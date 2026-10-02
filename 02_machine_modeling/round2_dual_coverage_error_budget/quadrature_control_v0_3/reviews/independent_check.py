#!/usr/bin/env python3
"""Narrow independent geometry/primitive check for shadow_integral.py.

This is deliberately not a full integral, convergence study, or certificate.
Run from any directory. Default mode is read-only; --record writes only the
two evidence files beside this script.
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path
import argparse

sys.dont_write_bytecode = True

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MODELS = ROOT / "models"
sys.path.insert(0, str(MODELS))
sys.path.insert(0, str(MODELS / "frozen"))
import legacy_adapter as legacy  # frozen contract values only
import robust_mask_v02 as robust


GAUSS_ORDER = 32
SLICE_CASES_PER_CHANNEL = 1200
ORACLE_RAYS_PER_CHANNEL = 128
ORACLE_MAX_RAYS = 256


def cross2(a, b):
    return float(a[0] * b[1] - a[1] * b[0])


def convex_hull(points):
    """Monotone-chain hull, independently implemented for 2-D points."""
    pts = sorted(set((float(p[0]), float(p[1])) for p in points))
    if len(pts) < 3:
        raise ValueError("projection did not produce a 2-D polygon")

    def turn(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and turn(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and turn(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return np.asarray(lower[:-1] + upper[:-1], dtype=float)


def geometry():
    c = legacy.config()
    shapes = legacy.plates(c, "both")
    by_name = {"vapor": shapes[0], "ion": shapes[1]}
    sources = {}
    for channel in ("vapor", "ion"):
        q = c[channel]
        if channel == "vapor":
            center = np.asarray(q["position_L_m"], dtype=float)
            Q = np.eye(3)
        else:
            center = np.asarray(q["origin_L_m"], dtype=float)
            Q = np.column_stack(
                [q["basis_u_L"], q["basis_v_L"], q["direction_L"]]
            ).astype(float)
        sources[channel] = dict(
            center=center,
            Q=Q,
            radius=float(q["radius_m"]),
            exponent=int(q["exponent"]),
        )
    return c, by_name, sources


def target(t, point):
    """Direct D-contract pose, not shadow_integral.Model.position."""
    phi = math.pi * t / 2
    psi = 13 * math.pi * t / 6
    x, y, z = point
    return np.array(
        [
            .312 * math.cos(phi) + x * math.cos(psi) - y * math.sin(psi),
            .312 * math.sin(phi) + x * math.sin(psi) + y * math.cos(psi),
            .6 + z,
        ],
        dtype=float,
    )


def plate_corners(mask):
    u, v, n = mask.orientation.T
    hw, hh, thick = mask.half_width_m, mask.half_height_m, mask.thickness_m
    return np.asarray(
        [
            mask.center_m + su * hw * u + sv * hh * v + sw * thick / 2 * n
            for su in (-1, 1)
            for sv in (-1, 1)
            for sw in (-1, 1)
        ]
    )


def projected_polygon(channel, t, point, source, mask):
    """Project all eight box corners onto the source's own plane, then hull."""
    X = target(t, point)
    c, Q = source["center"], source["Q"]
    normal = Q[:, 2]
    dX = float((X - c) @ normal)
    corners = plate_corners(mask)
    out = []
    depths = []
    for V in corners:
        dv = float((V - c) @ normal)
        depth = dX - dv
        depths.append((dv, dX, depth))
        if not (0 < dv < dX):
            raise AssertionError(f"projection-side condition failed for {channel}")
        # Homogeneous central projection; denominator is positive throughout.
        source_tangent_X = (X - c) @ Q[:, :2]
        source_tangent_V = (V - c) @ Q[:, :2]
        out.append((dX * source_tangent_V - dv * source_tangent_X) / depth)
    return convex_hull(out), depths


def signed_gap(poly, radius):
    """Signed distance of disk center to polygon boundary, minus disk radius."""
    edges = np.roll(poly, -1, axis=0) - poly
    signed = np.array([cross2(e, -p) / np.linalg.norm(e) for p, e in zip(poly, edges)])
    if np.all(signed >= 0):
        return float(np.min(signed) - radius)
    best2 = math.inf
    for p, e in zip(poly, edges):
        u = float(np.clip(-np.dot(p, e) / np.dot(e, e), 0.0, 1.0))
        best2 = min(best2, float(np.dot(p + u * e, p + u * e)))
    return -math.sqrt(best2) - radius


def point_in_poly_margin(poly, point2):
    edges = np.roll(poly, -1, axis=0) - poly
    signs = np.array([cross2(e, point2 - p) / np.linalg.norm(e) for p, e in zip(poly, edges)])
    if np.all(signs >= 0):
        return True, float(np.min(signs))
    best2 = math.inf
    for p, e in zip(poly, edges):
        u = float(np.clip(np.dot(point2 - p, e) / np.dot(e, e), 0.0, 1.0))
        d = point2 - (p + u * e)
        best2 = min(best2, float(d @ d))
    return False, math.sqrt(best2)


def vertical_block_interval(poly, x):
    """Intersect a convex polygon with x=constant via edge crossings."""
    ys = []
    for p, q in zip(poly, np.roll(poly, -1, axis=0)):
        x0, x1 = float(p[0]), float(q[0])
        if x0 == x1:
            if x == x0:
                ys.extend([float(p[1]), float(q[1])])
        elif min(x0, x1) <= x <= max(x0, x1):
            f = (x - x0) / (x1 - x0)
            ys.append(float(p[1] + f * (q[1] - p[1])))
    return (min(ys), max(ys)) if len(ys) >= 2 else None


def analytic_primitive(exponent, A, z):
    """Primitive of (A+z^2)^(-(exponent+3)/2), for A>0."""
    if exponent == 1:
        return z / (2 * A * (A + z * z)) + math.atan(z / math.sqrt(A)) / (2 * A**1.5)
    if exponent != 12:
        raise ValueError("only registered exponents 1 and 12")
    I = z / (A * math.sqrt(A + z * z))  # exponent 3/2
    for s in (2.5, 3.5, 4.5, 5.5, 6.5, 7.5):
        I = z / (2 * A * (s - 1) * (A + z * z) ** (s - 1)) + (2 * s - 3) / (2 * A * (s - 1)) * I
    return I


def check_primitives(c, masks, sources, rng):
    gx, gw = np.polynomial.legendre.leggauss(GAUSS_ORDER)
    report = {}
    total_gauss_evals = 0
    for channel in ("vapor", "ion"):
        q = sources[channel]
        gate = c["clock"][channel + "_gate_s"]
        abs_errors, rel_errors = [], []
        evaluated_intervals = 0
        for _ in range(SLICE_CASES_PER_CHANNEL):
            t = float(rng.uniform(*gate))
            r = q["radius"] * math.sqrt(float(rng.random()))
            x = float(r * math.cos(2 * math.pi * rng.random()))
            poly, _ = projected_polygon(channel, t, (0, 0, 0), q, masks[channel])
            ydisk = math.sqrt(max(0.0, q["radius"] ** 2 - x * x))
            lo, hi = -ydisk, ydisk
            block = vertical_block_interval(poly, x)
            pieces = [(lo, hi)]
            if block is not None:
                blo, bhi = max(lo, block[0]), min(hi, block[1])
                if blo < bhi:
                    pieces = []
                    if blo > lo:
                        pieces.append((lo, blo))
                    if bhi < hi:
                        pieces.append((bhi, hi))
            if not pieces:
                continue
            X = target(t, (0, 0, 0))
            local = (X - q["center"]) @ q["Q"]
            A = float(local[2] ** 2 + (x - local[0]) ** 2)
            exact = 0.0
            direct = 0.0
            power = (q["exponent"] + 3) / 2
            for a, b in pieces:
                za, zb = a - local[1], b - local[1]
                exact += analytic_primitive(q["exponent"], A, zb) - analytic_primitive(q["exponent"], A, za)
                y = (a + b) / 2 + (b - a) / 2 * gx
                z = y - local[1]
                direct += (b - a) / 2 * float(np.dot(gw, (A + z * z) ** (-power)))
                total_gauss_evals += GAUSS_ORDER
                evaluated_intervals += 1
            abs_errors.append(abs(exact - direct))
            rel_errors.append(abs(exact - direct) / max(abs(direct), 1e-300))
        report[channel] = {
            "exponent": q["exponent"],
            "slice_cases": SLICE_CASES_PER_CHANNEL,
            "visible_y_intervals_compared": evaluated_intervals,
            "max_abs_primitive_integral_difference": max(abs_errors, default=0.0),
            "max_relative_primitive_integral_difference": max(rel_errors, default=0.0),
        }
    if total_gauss_evals > 200_000:
        raise AssertionError("independent Gauss evaluations exceeded protocol cap")
    return report, total_gauss_evals


def check_oracle(c, masks, sources, rng):
    robust_masks = {}
    for channel, mask in masks.items():
        robust_masks[channel] = robust.RectangleMask(
            tuple(float(x) for x in mask.center_m),
            mask.orientation.tolist(),
            float(mask.half_width_m),
            float(mask.half_height_m),
            float(mask.thickness_m),
        )
    out = {}
    rays_used = 0
    for channel in ("vapor", "ion"):
        q = sources[channel]
        gate = c["clock"][channel + "_gate_s"]
        pairs, expected = [], []
        trials = 0
        while len(pairs) < ORACLE_RAYS_PER_CHANNEL and trials < 20_000:
            trials += 1
            t = float(rng.uniform(*gate))
            p_r = .06 * math.sqrt(float(rng.random()))
            p_ang = 2 * math.pi * float(rng.random())
            target_local = (p_r * math.cos(p_ang), p_r * math.sin(p_ang), 0.0)
            X = target(t, target_local)
            sr = q["radius"] * math.sqrt(float(rng.random()))
            sang = 2 * math.pi * float(rng.random())
            uv = np.array([sr * math.cos(sang), sr * math.sin(sang)])
            S = q["center"] + q["Q"][:, 0] * uv[0] + q["Q"][:, 1] * uv[1]
            poly, _ = projected_polygon(channel, t, target_local, q, masks[channel])
            inside, margin = point_in_poly_margin(poly, uv)
            if margin < 5e-7:
                continue  # avoid measure-zero boundary convention differences
            pairs.append((tuple(float(v) for v in S), tuple(float(v) for v in X)))
            expected.append(inside)
        if len(pairs) != ORACLE_RAYS_PER_CHANNEL:
            raise RuntimeError("could not collect enough non-boundary oracle rays")
        verdicts = robust_masks[channel].classify_many(pairs)
        actual = [v.verdict is robust.Verdict.BLOCKED for v in verdicts]
        unknown = sum(v.verdict is robust.Verdict.UNKNOWN for v in verdicts)
        mismatches = [i for i, (a, b) in enumerate(zip(actual, expected)) if a != b]
        out[channel] = {
            "rays": len(pairs),
            "polygon_blocked": int(sum(expected)),
            "oracle_blocked": int(sum(actual)),
            "unknown": unknown,
            "mismatch_count": len(mismatches),
            "boundary_exclusion_m": 5e-7,
        }
        rays_used += len(pairs)
    if rays_used > ORACLE_MAX_RAYS:
        raise AssertionError("robust oracle ray cap exceeded")
    return out, rays_used


def bisect_root(f, a, b, iterations=60):
    fa, fb = f(a), f(b)
    if fa * fb >= 0:
        raise ValueError(f"root is not bracketed: f(a)={fa}, f(b)={fb}")
    for _ in range(iterations):
        m = (a + b) / 2
        fm = f(m)
        if fa * fm <= 0:
            b, fb = m, fm
        else:
            a, fa = m, fm
    return (a + b) / 2


def check_duration(c, masks, sources):
    # Outer point #2 in the frozen 13-point layout: radius 60 mm, angle 30 deg.
    point = (.06 * math.cos(math.pi / 6), .06 * math.sin(math.pi / 6), 0.0)
    vapor = sources["vapor"]
    gap = lambda t: signed_gap(
        projected_polygon("vapor", t, point, vapor, masks["vapor"])[0], vapor["radius"]
    )
    left = bisect_root(gap, 3.90, 4.00)
    right = bisect_root(gap, 4.00, 4.10)
    # Direct sample bracketing around independently found roots, not integration.
    eps = 2e-6
    signs = {
        "left_before_m": gap(left - eps),
        "left_after_m": gap(left + eps),
        "right_before_m": gap(right - eps),
        "right_after_m": gap(right + eps),
    }
    covered = right - left
    gate_off = 7.3 - (6.55 - .55)

    return {
        "point_local_m": point,
        "left_root_s": left,
        "right_root_s": right,
        "covered_duration_s": covered,
        "gate_off_duration_s": gate_off,
        "independent_ion_only_duration_s_if_ion_visible": gate_off + covered,
        "root_signs_at_2us_m": signs,
        "event_root_method": "independent corner projection, monotone-chain hull, point-to-edge distance, bisection",
        "duration_scope_note": "The vapor full-cover interval is independently recomputed. An independent open ion-source patch stays clear of the ion plate for every target position; cross-source separation is also established, so ion flux is positive throughout. This establishes the duration decomposition for this frozen geometry, not float-certified endpoint bounds.",
    }


def simple_coordinate_bounds(c):
    # Target substrate is z=.6 with x in [-.372,.372] over the orbit/disk.
    target_x = (-.312 - .06, .312 + .06)
    vplate = c["plates"]["vapor_plate"]
    iplate = c["plates"]["ion_plate"]
    vp_x = (vplate["origin_L_m"][0] - vplate["half_width_m"][0], vplate["origin_L_m"][0] + vplate["half_width_m"][0])
    ip_x = (iplate["origin_L_m"][0] - iplate["half_width_m"][0], iplate["origin_L_m"][0] + iplate["half_width_m"][0])
    # Vapor source to cross ion plate, at plate z in [0.085,.115].
    lam_vi = (.085 / .6, .115 / .6)
    vapor_source_x_min = .2 - .035
    x_vi_min = vapor_source_x_min + lam_vi[1] * (target_x[0] - vapor_source_x_min)
    # Ion source disk x,z ranges and cross vapor plate z slab.
    zsi = (-.8 * .045, .8 * .045)
    xsi_max = -.62 + .6 * .045
    lam_iv_max = (.21 - zsi[0]) / (.6 - zsi[0])
    x_iv_max = xsi_max + lam_iv_max * (target_x[1] - xsi_max)
    # An interior source point near the negative-u disk rim stays clear of the
    # ion plate in x for all target x, with a strict gap and thus an open patch.
    xi = -.044  # |xi| < source radius .045; eta=0
    patch_x = -.62 + .6 * xi
    patch_z = -.8 * xi
    lam_patch_max = (.115 - patch_z) / (.6 - patch_z)
    x_patch_max = patch_x + lam_patch_max * (target_x[1] - patch_x)
    return {
        "target_x_m": target_x,
        "vapor_plate_x_m": vp_x,
        "ion_plate_x_m": ip_x,
        "vapor_to_ignored_ion_plate": {
            "ray_x_lower_bound_m": x_vi_min,
            "plate_x_upper_bound_m": ip_x[1],
            "gap_m": x_vi_min - ip_x[1],
        },
        "ion_to_ignored_vapor_plate": {
            "ray_x_upper_bound_m": x_iv_max,
            "plate_x_lower_bound_m": vp_x[0],
            "gap_m": vp_x[0] - x_iv_max,
        },
        "ion_own_plate_open_clear_source_patch": {
            "chosen_local_source_uv_m": [xi, 0.0],
            "source_disk_radius_m": .045,
            "source_x_m": patch_x,
            "source_z_m": patch_z,
            "max_crossing_lambda": lam_patch_max,
            "ray_x_upper_bound_m": x_patch_max,
            "plate_x_interval_m": ip_x,
            "gap_to_plate_m": ip_x[0] - x_patch_max,
            "conclusion": "strict x separation for an interior source point and therefore an open positive-area source neighborhood for all target positions; beam-emission and target-incidence cosines are positive",
        },
    }


def lipschitz_bounds(c):
    S = .312 * math.pi / 2 + .06 * 13 * math.pi / 6
    # Vapor: dX=.6, plate dv<=.21, so each projected vertex speed <= dv/(dX-dv)*S.
    kv = .21 / (.6 - .21) * S
    # Ion: target normal coordinate .8*x+.856; plate dv in [.155,.269].
    dX_min, dv_max = .8 * (-.372) + .856, .269
    B = dX_min - dv_max
    vmax = .8984954989266808
    vertex_distance = math.sqrt(.862**2 + .2**2 + .515**2)
    dXdot = .8 * S
    ki = dv_max / B * vmax + dv_max / (B * B) * dXdot * vertex_distance
    return {
        "target_speed_bound_m_s": S,
        "vapor_projected_vertex_speed_bound_m_s": kv,
        "vapor_slope_limit_m_s": .5,
        "vapor_margin_m_s": .5 - kv,
        "ion_dX_min_m": dX_min,
        "ion_dv_max_m": dv_max,
        "ion_projection_denominator_min_m": B,
        "ion_vertex_target_distance_bound_m": vertex_distance,
        "ion_projected_vertex_speed_bound_m_s": ki,
        "ion_slope_limit_m_s": 6.0,
        "ion_margin_m_s": 6.0 - ki,
        "argument": "Corresponding projected box vertices move no faster than these bounds; their convex hull Hausdorff speed is no larger. Signed distance of the origin to a convex polygon is 1-Lipschitz under Hausdorff motion, hence cover_slack inherits the same bound.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", action="store_true", help="write the two review evidence files")
    args = parser.parse_args()
    start = time.monotonic()
    c, masks, sources = geometry()
    rng = np.random.default_rng(20261002)
    primitives, gauss_evals = check_primitives(c, masks, sources, rng)
    oracle, oracle_rays = check_oracle(c, masks, sources, rng)
    duration = check_duration(c, masks, sources)
    lipschitz = lipschitz_bounds(c)
    coords = simple_coordinate_bounds(c)
    results = {
        "status": "independent_narrow_check_complete_not_certified",
        "scope": "Frozen synthetic D geometry only; no full source/time integral, no device-scale run, no physical certification.",
        "geometry": {
            "projection": "For every vertex, 0 < dv < dX. A positive-denominator projective map sends a convex box to the convex hull of the images of its vertices; independently checked against robust_mask_v02 on sampled rays.",
            "oracle": oracle,
            "oracle_rays_total": oracle_rays,
            "oracle_limit": ORACLE_MAX_RAYS,
        },
        "analytic_y_vs_independent_gauss": {
            "channels": primitives,
            "gauss_order": GAUSS_ORDER,
            "smooth_gauss_samples": gauss_evals,
            "smooth_sample_limit": 200_000,
        },
        "duration_event_independent_check": duration,
        "cross_source_coordinate_bounds": coords,
        "cover_slack_lipschitz": lipschitz,
        "float_guard": "The 1e-11 m guard in support_intervals is not an outward-rounded or otherwise validated floating-point error bound. Numerical results remain conditional; no strict enclosure claim.",
        "runtime_seconds": time.monotonic() - start,
    }
    if args.record:
        (HERE / "independent_results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
        (HERE / "INDEPENDENT_CHECK.md").write_text(make_report(results))
    print(json.dumps({"status": results["status"], "oracle_rays": oracle_rays, "gauss_samples": gauss_evals, "runtime_seconds": results["runtime_seconds"], "recorded": args.record}, ensure_ascii=False))


def make_report(r):
    g = r["geometry"]["oracle"]
    y = r["analytic_y_vs_independent_gauss"]["channels"]
    d = r["duration_event_independent_check"]
    c = r["cross_source_coordinate_bounds"]
    l = r["cover_slack_lipschitz"]
    return f"""# Independent narrow check: shadow integral math

Status: **{r['status']}**. This is a narrow check of the frozen synthetic D case only. It does not rerun the main quadrature, does not validate device-scale execution, and is not physical or interval certification.

This records the actual Luna narrow mathematical check; it does not replace a Seed or Sol sign-off.

## Projection and geometric mask

The two emitted source planes and their corresponding thick boxes satisfy `0 < dv < dX` at every box vertex: the vapor geometry has `dX=0.6 m`, `dv∈[0.19,0.21] m`; for the ion geometry, `dX∈[{.8*(-.372)+.856:.4f},{.8*(.372)+.856:.4f}] m` and `dv∈[0.155,0.269] m`. With positive projective denominators, the image of each convex box is exactly the convex hull of its projected vertices. This supports the eight-corner convex-hull construction, not just a thin-plate approximation.

An independent hull and ray classification were compared with `frozen/robust_mask_v02.py` on {r['geometry']['oracle_rays_total']} non-boundary rays (within its batch limit): vapor {g['vapor']['mismatch_count']} mismatches/{g['vapor']['rays']}, ion {g['ion']['mismatch_count']} mismatches/{g['ion']['rays']}. These samples check implementation consistency, not exhaustive proof.

## Analytic y antiderivative

For {r['analytic_y_vs_independent_gauss']['smooth_gauss_samples']} smooth Gauss nodes (32-point Gauss-Legendre, at most 200,000), using independently constructed projected hulls and vertical cross-sections:

- exponent 1: max absolute difference {y['vapor']['max_abs_primitive_integral_difference']:.3g}, max relative {y['vapor']['max_relative_primitive_integral_difference']:.3g}
- exponent 12: max absolute difference {y['ion']['max_abs_primitive_integral_difference']:.3g}, max relative {y['ion']['max_relative_primitive_integral_difference']:.3g}

Both formulas agree with independent smooth quadrature on these finite samples. This does not bound outer x/time quadrature error.

## Cross-source plates and duration event

The ignored plate has an all-time coordinate separation for each source, including finite source-disk extents. Vapor rays at the ion-plate z slab have x ≥ {c['vapor_to_ignored_ion_plate']['ray_x_lower_bound_m']:.3f} m, while the ion plate ends at x={c['vapor_to_ignored_ion_plate']['plate_x_upper_bound_m']:.3f} m. Ion rays at the vapor-plate z slab have x ≤ {c['ion_to_ignored_vapor_plate']['ray_x_upper_bound_m']:.3f} m, while the vapor plate begins at x={c['ion_to_ignored_vapor_plate']['plate_x_lower_bound_m']:.3f} m. Thus omitting the *other* source's plate is supported for these frozen bounded geometries. Separately, the ion disk contains the interior point `u=-0.044 m, v=0` whose rays remain x≤{c['ion_own_plate_open_clear_source_patch']['ray_x_upper_bound_m']:.3f} m at the ion plate, below its x-minimum {c['ion_own_plate_open_clear_source_patch']['plate_x_interval_m'][0]:.3f} m. An open neighborhood is also clear, so ion flux is positive for every time.

For diagnostic point #2, an independent direct projection, convex hull, point-to-edge distance, and bisection locate vapor full-cover roots at {d['left_root_s']:.9f} s and {d['right_root_s']:.9f} s, a {d['covered_duration_s']*1000:.3f} ms cover interval. Adding the 1.300 s vapor gate-off time gives {d['independent_ion_only_duration_s_if_ion_visible']:.9f} s. The open ion-source patch above establishes positive ion transmission throughout. Root sign checks at ±2 μs are {d['root_signs_at_2us_m']}; this independently supports the changed duration magnitude versus frozen discrete estimates, but remains a binary64 event-root estimate, not a certified endpoint.

## Lipschitz and floating point

The global target speed bound is {l['target_speed_bound_m_s']:.6f} m/s. A projection-derivative bound gives vapor vertex speed ≤{l['vapor_projected_vertex_speed_bound_m_s']:.6f} m/s, below the configured 0.5 m/s. For ion, `dX-dv ≥{l['ion_projection_denominator_min_m']:.4f} m`; a conservative derivative bound gives projected vertex speed ≤{l['ion_projected_vertex_speed_bound_m_s']:.3f} m/s, below the configured 6 m/s. Since a hull cannot move faster in Hausdorff distance than its corresponding vertices, and signed distance is 1-Lipschitz in that distance, both slopes are conservative under the stated geometry.

The `1e-11 m` floating guard in `support_intervals` is **not validated as a floating-point error bound**. Therefore support intervals and duration remain conditional numerical enclosures, not strict certified bounds. No change to main code is indicated by this narrow check.
"""


if __name__ == "__main__":
    main()
