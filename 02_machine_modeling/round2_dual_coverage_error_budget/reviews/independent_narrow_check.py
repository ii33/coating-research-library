#!/usr/bin/env python3
"""Bounded review of three approved files and two authorized T01 functions.

No main-model edits, device data, optimization, or global convergence claim.
Ray count conservatively includes BOTH implementations of every comparison.
"""
from pathlib import Path
import ast
import hashlib
import importlib.util
import json
import math
import sys
import time
from types import SimpleNamespace
import warnings

import numpy as np

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
APPROVED = (
    "models/dual_finite.py",
    "models/frozen/t02_deposition_reference.py",
    "verification/PRE_REGISTERED_PROTOCOL.md",
)
LIMIT = 3_000_000
# Prior runs: first serialization met a concurrently added status string; second
# completed before the final metrics coverage-label update. Count both honestly.
PRIOR_ATTEMPT_RAYS = 297_444
START = time.monotonic()
RAYS = 0
COUNTS = {}


def charge(name, count):
    global RAYS
    count = int(count)
    if PRIOR_ATTEMPT_RAYS + RAYS + count > LIMIT:
        raise RuntimeError("independent review ray budget exceeded")
    RAYS += count
    COUNTS[name] = COUNTS.get(name, 0) + count


def load_reference():
    name = "narrow_check_t02"
    spec = importlib.util.spec_from_file_location(name, ROOT / APPROVED[1])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_comparators():
    """Avoid importing the adapter's unapproved dependency/configuration files."""
    tree = ast.parse((ROOT / APPROVED[0]).read_text())
    selected = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                and n.name in {"compare", "stats_compare", "metrics"}]
    namespace = {"np": np}
    exec(compile(ast.Module(body=selected, type_ignores=[]), APPROVED[0], "exec"), namespace)
    return namespace


def load_ratio_functions():
    # Parent specifically expanded the read scope to these TWO functions only.
    path = ROOT / "models/frozen/t01_dual_coverage.py"
    source = path.read_text()
    tree = ast.parse(source)
    selected = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                and n.name in {"output_values", "statistics"}]
    snippets = "\n".join(ast.get_source_segment(source, n) for n in selected)
    namespace = {"np": np, "math": math}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), "exec"), namespace)
    return namespace, hashlib.sha256(snippets.encode()).hexdigest()


def face_enumeration(mask, sources, targets):
    """Open segment vs SIX CLOSED FACES, with an interior midpoint witness.

    Independent of slab interval clipping: enumerate plane intersections and
    test face rectangles. Parallel means EXACT zero here, not a length epsilon.
    The midpoint covers segments contained in the closed solid or a face.
    """
    a, b = np.broadcast_arrays(np.asarray(sources, float), np.asarray(targets, float))
    shape = a.shape[:-1]
    a, b = a.reshape(-1, 3), b.reshape(-1, 3)
    d = b - a
    q = mask.orientation
    center = mask.center_m
    half = np.array([mask.half_width_m, mask.half_height_m, mask.thickness_m / 2])
    midpoint = 0.5 * (a + b) - center
    hit = np.ones(len(a), bool)
    for j in range(3):
        hit &= np.abs(midpoint @ q[:, j]) <= half[j]
    for j in range(3):
        normal = q[:, j]
        denom = d @ normal
        valid = denom != 0.0
        for sign in (-1, 1):
            face_center = center + sign * half[j] * normal
            lam = np.divide((face_center - a) @ normal, denom,
                            out=np.full(len(a), np.nan), where=valid)
            crossing = a + lam[:, None] * d - face_center
            on_face = valid & (lam > 0.0) & (lam < 1.0)
            for k in range(3):
                if k != j:
                    on_face &= np.abs(crossing @ q[:, k]) <= half[k]
            hit |= on_face
    return hit.reshape(shape)


def geometry_checks(t02):
    rng = np.random.default_rng(2601002)
    random_sets = []
    for i in range(6):
        q, _ = np.linalg.qr(rng.normal(size=(3, 3)))
        if np.linalg.det(q) < 0:
            q[:, 0] *= -1
        center = rng.uniform(-0.6, 0.6, 3)
        half = rng.uniform([0.04, 0.025, 0.005], [0.2, 0.15, 0.06])
        m = t02.RectangleMask(center, q, half[0], half[1], 2 * half[2])
        n = 10_000
        a = rng.uniform(-4, 4, (n, 3)) * half
        b = rng.uniform(-4, 4, (n, 3)) * half
        # Include contained endpoints and crossing families, beyond uniform misses.
        a[:n//5] = rng.uniform(-0.99, 0.99, (n//5, 3)) * half
        b[n//5:2*n//5] = -a[n//5:2*n//5] + rng.normal(0, 0.15, (n//5, 3)) * half
        a, b = a @ q.T + center, b @ q.T + center
        charge("random_geometry_both_algorithms", 2 * n)
        actual, reference = m.blocked(a, b), face_enumeration(m, a, b)
        bad = np.flatnonzero(actual != reference)
        random_sets.append({"set": i, "rays_each_algorithm": n,
                            "blocked": int(actual.sum()), "mismatches": len(bad),
                            "first_mismatches": bad[:5].tolist()})

    m = t02.RectangleMask(np.zeros(3), np.eye(3), 0.1, 0.2, 0.04)
    cases = [
        ("through_front_back", [0, 0, -0.1], [0, 0, 0.1], True),
        ("sidewall_only", [-0.3, 0, 0], [0.3, 0, 0], True),
        ("parallel_outside", [-0.3, 0.21, 0], [0.3, 0.21, 0], False),
        ("contained", [-0.01, 0, 0], [0.01, 0, 0], True),
        ("source_inside", [0, 0, 0], [0.3, 0, 0], True),
        ("target_inside", [-0.3, 0, 0], [0, 0, 0], True),
        ("source_boundary_outward", [0.1, 0, 0], [0.3, 0, 0], False),
        ("target_boundary_only", [-0.3, 0, 0], [-0.1, 0, 0], False),
        ("source_boundary_inward", [-0.1, 0, 0], [0.3, 0, 0], True),
        ("target_boundary_from_inside", [0, 0, 0], [0.1, 0, 0], True),
        ("coplanar_face_crossing", [-0.3, 0.2, 0], [0.3, 0.2, 0], True),
        ("edge_tangent", [0.1, 0.2, -0.1], [0.1, 0.2, 0.1], True),
        ("corner_contact_in_open_segment", [-0.3, 0, 0], [0.1, 0.4, 0], True),
        ("grazing_inside_1e_minus_12", [-0.3, 0.2-1e-12, 0], [0.3, 0.2-1e-12, 0], True),
        ("grazing_outside_1e_minus_12", [-0.3, 0.2+1e-12, 0], [0.3, 0.2+1e-12, 0], False),
    ]
    deterministic = []
    for name, a, b, expected in cases:
        charge("deterministic_geometry_both_algorithms", 2)
        actual, reference = bool(m.blocked(a, b)), bool(face_enumeration(m, a, b))
        deterministic.append({"case": name, "slab": actual, "six_faces": reference,
                              "expected": expected, "pass": actual == reference == expected})
    # Deliberate representational edge case: not a failure of nondegenerate gate.
    a, b = [0.1+4e-15, 0, -0.1], [0.1-4e-15, 0, 0.1]
    charge("sub_epsilon_geometry_both_algorithms", 2)
    epsilon_case = {"source": a, "target": b, "delta_x_m": b[0]-a[0],
                    "slab": bool(m.blocked(a, b)), "six_faces": bool(face_enumeration(m, a, b)),
                    "classification": "documented_numeric_scale_caveat"}
    thin = t02.RectangleMask(np.zeros(3), np.eye(3), 0.1, 0.2, 0.0)
    thin_cases = [
        ("transverse", [0, 0, -1], [0, 0, 1], True),
        ("source_endpoint_only", [0, 0, 0], [0, 0, 1], False),
        ("target_endpoint_only", [0, 0, -1], [0, 0, 0], False),
        ("coplanar_excluded", [-1, 0, 0], [1, 0, 0], False),
    ]
    thin_results = []
    for name, a, b, expected in thin_cases:
        charge("thin_mask_conventions", 1)
        actual = bool(thin.blocked(a, b))
        thin_results.append({"case": name, "actual": actual, "expected": expected,
                             "pass": actual == expected})
    return {"random": random_sets, "deterministic": deterministic,
            "sub_epsilon_example": epsilon_case, "thin_mask_conventions": thin_results,
            "nondegenerate_pass": all(x["mismatches"] == 0 for x in random_sets)
                and all(x["pass"] for x in deterministic)}


def normalization_checks(t02):
    q, w = np.polynomial.legendre.leggauss(64)
    mu, wm = (q+1)/2, w/2
    hemispheres = [{"p": p, "integral": float((p+1)*np.sum(wm*mu**p))}
                   for p in (0, 1, 12)]
    a, h, total_rate = 0.15, 0.3, 7.3e18
    axial = []
    for p in (0, 1, 12):
        src = t02.disk_source(a, 32, 67, exponent=p)
        charge("axis_kernel", len(src.fractions))
        actual = float(t02.transfer_kernel(np.array([[0, 0, h]]),
                                           np.array([[0, 0, -1]]), src)[0])
        exact = -np.expm1(-(p+1)/2 * np.log1p(a*a/(h*h))) / (np.pi*a*a)
        axial.append({"p": p, "source_fraction_sum": float(src.fractions.sum()),
                      "kernel_actual_m_minus_2": actual, "kernel_exact_m_minus_2": float(exact),
                      "relative_error": float(abs(actual/exact-1)),
                      "total_rate_particles_s": total_rate,
                      "flux_particles_m_minus_2_s_minus_1": total_rate*actual})
    projection = []
    src = t02.disk_source(0.035, 16, 37, exponent=1)
    base = None
    for degrees in (0, 35, 70):
        beta = np.deg2rad(degrees)
        n = np.array([[np.sin(beta), 0, -np.cos(beta)]])
        charge("projection_once_kernel", len(src.fractions))
        value = float(t02.transfer_kernel(np.array([[0, 0, 0.6]]), n, src)[0])
        if base is None:
            base = value
        ratio = value/base
        projection.append({"tilt_degrees": degrees, "ratio": ratio,
                           "expected_cosine": float(np.cos(beta)),
                           "absolute_error": float(abs(ratio-np.cos(beta)))})
    return {"hemisphere_normalization": hemispheres, "axis": axial,
            "projection_once": projection,
            "pass": all(abs(v["integral"]-1) < 1e-12 for v in hemispheres)
                and all(v["relative_error"] < 1e-8 for v in axial)
                and all(v["absolute_error"] < 1e-12 for v in projection)}


def cartesian_source_integral(points, normals, radius, exponent, order):
    """Independent disk cubature and flux, no Source/transfer_kernel helpers.

    x=a sin(chi), y=a cos(chi) v, chi in [-pi/2,pi/2], v in [-1,1].
    Jacobian a^2 cos(chi)^2; divide by disk area pi*a^2 for RATE fractions.
    Different coordinates, weights, azimuth behavior, and kernel implementation
    from the reference's Gauss in r^2 times uniform azimuth.
    """
    z, w = np.polynomial.legendre.leggauss(order)
    chi, v = z*np.pi/2, z
    x = np.broadcast_to(radius*np.sin(chi)[:, None], (order, order))
    y = radius*np.cos(chi)[:, None]*v[None, :]
    nodes = np.column_stack([x.ravel(), y.ravel(), np.zeros(order*order)])
    fractions = ((w*np.pi/2)[:, None]*w[None, :]
                 *np.cos(chi)[:, None]**2/np.pi).ravel()
    out = []
    for point, normal in zip(points, normals):
        charge("independent_cartesian_source_kernel", len(nodes))
        delta = point - nodes
        rr = np.linalg.norm(delta, axis=1)
        emission = np.maximum(delta[:, 2]/rr, 0)**exponent
        incidence = np.maximum(-(delta @ normal)/rr, 0)
        flux = (exponent+1)/(2*np.pi)*emission*incidence/(rr*rr)
        out.append(fractions @ flux)
    return np.array(out), float(fractions.sum())


def source_checks(t02):
    # At most three fixed synthetic receiver points; no masking discontinuity,
    # no moving pose/time or continuum uniformity inference.
    points = np.array([[0, 0, .30], [.11, .06, .29], [-.09, .14, .35]])
    normals = np.array([[0, 0, -1], [.12, -.07, -1], [-.16, .1, -1]], float)
    normals /= np.linalg.norm(normals, axis=1)[:, None]
    radius, exponent = .15, 1
    low, low_sum = cartesian_source_integral(points, normals, radius, exponent, 31)
    high, high_sum = cartesian_source_integral(points, normals, radius, exponent, 61)
    src = t02.disk_source(radius, 32, 67, exponent=exponent)
    charge("reference_polar_source_kernel", len(points)*len(src.fractions))
    actual = t02.transfer_kernel(points, normals, src)
    relative = np.abs(actual-high)/np.abs(high)
    change = np.abs(low-high)/np.abs(high)
    return {"scope": "three static unmasked points only; independent source quadrature, not time holdout",
            "points_m": points.tolist(), "normals": normals.tolist(),
            "radius_m": radius, "p": exponent, "cartesian_orders": [31, 61],
            "cartesian_fraction_sums": [low_sum, high_sum],
            "independent_values": high.tolist(), "reference_values": actual.tolist(),
            "reference_vs_independent_relative": relative.tolist(),
            "independent_order_change_relative": change.tolist(),
            "observed_agreement_under_1e_minus_8": bool(np.max(relative) < 1e-8),
            "is_global_convergence_proof": False,
            "moving_mask_time_nonresonance_check": "NOT_RUN: outside approved input/configuration read scope"}


def safe_float(value):
    if isinstance(value, str) or value is None:
        return value
    value = float(value)
    return value if np.isfinite(value) else str(value)


def denominator_checks():
    namespace = load_comparators()
    compare = namespace["compare"]
    cases = []
    for name, a, b in [
        ("all_zero", np.zeros((3, 4)), np.zeros((3, 4))),
        ("one_zero_channel_hides_finite_difference", np.array([[0, 2, 2, 0]]*3, float),
         np.array([[0, 1, 1, 0]]*3, float)),
        ("nonzero_difference_zero_reference", np.array([[1, 2, 2, 0]]*3, float),
         np.array([[0, 1, 1, 0]]*3, float)),
        ("positive_tiny_reference", np.array([[2e-300, 2e-300, 2e-300, 0]]*3),
         np.array([[1e-300, 1e-300, 1e-300, 0]]*3)),
    ]:
        with warnings.catch_warnings(record=True) as seen:
            warnings.simplefilter("always")
            result = compare(a, b)
        cases.append({"case": name, "result": {k: safe_float(v) for k, v in result.items()},
                      "warnings": [str(w.message) for w in seen],
                      "gt_0_003_threshold": bool(result["max_relative_integral_difference"] > .003)})
    ratio_functions, selected_hash = load_ratio_functions()
    namespace["t01"] = SimpleNamespace(**{k: ratio_functions[k] for k in ("output_values", "statistics")})
    config = {"vapor": {"net_atomic_density_m3": 1e28}, "ion": {"energy_per_ion_eV": 100.0}}
    integrals = np.array([[-1, 1, 1, 0], [0, 1, 1, 0], [1e-16, 1, 1, 0], [1, 1, 1, 0]], float)
    values = ratio_functions["output_values"](config, integrals)
    stats = ratio_functions["statistics"](values["ion_to_net_atom_ratio"], np.ones(4))
    adapter_metrics = namespace["metrics"](config, integrals, np.ones(4))
    zero_stats = ratio_functions["statistics"](np.zeros(3), np.ones(3))
    fake_metrics = {k: zero_stats for k in ["h_nm", "ion_fluence_m2", "incident_energy_J_m2"]}
    try:
        out = namespace["stats_compare"](fake_metrics, fake_metrics)
        stats_edge = {"returns": {k: safe_float(v) for k, v in out.items()}}
    except (ZeroDivisionError, TypeError, ValueError) as exc:
        stats_edge = {"exception_type": type(exc).__name__, "exception": str(exc)}
    return {"adapter_compare_cases": cases,
            "selected_t01_functions_sha256": selected_hash,
            "actual_R_epsilon_implementation": "only output_values and statistics inspected; authorized narrow scope extension",
            "synthetic_N": integrals[:, 0].tolist(),
            "actual_ratio": [safe_float(v) for v in values["ion_to_net_atom_ratio"]],
            "actual_eV_per_atom": [safe_float(v) for v in values["eV_per_net_atom"]],
            "ratio_statistics_over_finite_subset": stats,
            "adapter_ratio_metrics_with_coverage": adapter_metrics["ion_to_net_atom_ratio"],
            "finite_positive_area_fraction_in_this_test": 0.5,
            "statistics_zero_mean": zero_stats,
            "stats_compare_zero_mean_case": stats_edge,
            "protocol_conditioning": "N>0; estimated numerical error/abs(N)>=0.1 => ill_conditioned",
            "recommended_required_statuses": ["undefined when N<=0", "ill_conditioned when estimate/abs(N)>=0.1",
                                               "unassessed when no credible absolute N-error estimate exists"],
            "conditioning_note": "near-zero net N can amplify gross deposition/erosion errors; passing h,D,U relative changes alone is not an N-error bound",
            "error_budget_wording": "protocol distinguishes numerical components, scenarios, unknown calibration, model discrepancy; empirical mesh difference is not a rigorous bound"}


def main():
    fingerprints = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in APPROVED}
    t02 = load_reference()
    result = {"scope": "one bounded independent narrow mathematical review; D conditional baseline only; C/I unsupported; all synthetic",
              "input_sha256": fingerprints,
              "geometry": geometry_checks(t02),
              "normalization": normalization_checks(t02),
              "source_quadrature": source_checks(t02),
              "denominators_and_wording": denominator_checks(),
              "limitations": ["random ray agreement is not exhaustive geometry certification",
                              "three smooth static source checks are not motion/mask/time convergence",
                              "no empirical pair of grids is treated as a rigorous discretization bound",
                              "no T01 inspection beyond two specifically approved functions; no t05, real data, or other library work"]}
    result["budget"] = {"ray_evaluations": RAYS, "ray_limit": LIMIT,
                        "prior_review_runs_rays": PRIOR_ATTEMPT_RAYS,
                        "review_cumulative_rays": PRIOR_ATTEMPT_RAYS+RAYS,
                        "counting": "both reference and independent evaluations counted separately",
                        "breakdown": COUNTS, "wall_seconds": time.monotonic()-START}
    result["approved_inputs_unchanged_during_run"] = all(
        hashlib.sha256((ROOT/p).read_bytes()).hexdigest() == h for p, h in fingerprints.items())
    out = ROOT/"reviews/independent_narrow_results.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)+"\n")
    print(json.dumps({"result": str(out.relative_to(ROOT)), "geometry_pass": result["geometry"]["nondegenerate_pass"],
                      "normalization_pass": result["normalization"]["pass"],
                      "source_agreement_pass": result["source_quadrature"]["observed_agreement_under_1e_minus_8"],
                      "ray_evaluations": RAYS, "seconds": result["budget"]["wall_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
