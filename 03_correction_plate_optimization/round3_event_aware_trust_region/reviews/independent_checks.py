#!/usr/bin/env python3
"""One-pass narrow independent checks for T03 round 3.

Run from this round's root with:
  PYTHONDONTWRITEBYTECODE=1 python reviews/independent_checks.py
Only the three scoped implementation/reference/test files are hashed. The independent
Darboux calculation below is deliberately small and uses Fraction arithmetic directly.
"""
from dataclasses import asdict, replace
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "models"))
from trust_region import (  # noqa: E402
    Scene, Interval, certify_segment, clipped_candidate, compare,
    full_forward, objective_interval, rational_forward_interval,
    reduction_ratio,
)
from event_reference import evaluate  # noqa: E402


def q(x):
    return x if isinstance(x, F) else F(float(x))


def project_boundary(sc, node, sign, z):
    p = {k: q(v) for k, v in asdict(sc).items()}
    s = q(node) + p["source_shift_m"]
    edge = p["plate_shift_m"] + sign * p["half_width_m"]
    return s + (edge - s) * p["height_m"] / p[z]


def independent_exact_darboux(sc, nodes, weights, panels):
    """Return exact Fraction lower/upper bounds without calling trust_region helpers."""
    if len(nodes) != len(weights) or not nodes or len(nodes) > 65:
        raise ValueError("invalid finite source")
    p = {k: q(v) for k, v in asdict(sc).items()}
    lower = F(0)
    upper = F(0)
    count = 0
    for raw_node, raw_weight in zip(nodes, weights):
        node, weight = q(raw_node), q(raw_weight)
        if weight < 0:
            raise ValueError("negative weight")
        s = node + p["source_shift_m"]
        # Independent geometric projection: lower is the minimum projected left edge;
        # upper is the maximum projected right edge, each attained at a slab endpoint.
        lo_x = min(project_boundary(sc, node, -1, "z_near_m"),
                   project_boundary(sc, node, -1, "z_far_m"))
        hi_x = max(project_boundary(sc, node, +1, "z_near_m"),
                   project_boundary(sc, node, +1, "z_far_m"))
        v = p["velocity_m_s"]
        if v == 0:
            raise ValueError("this check covers transverse events only")
        tlo = (lo_x - p["x0_m"] - p["target_shift_m"]) / v - p["clock_offset_s"]
        thi = (hi_x - p["x0_m"] - p["target_shift_m"]) / v - p["clock_offset_s"]
        blocked_a, blocked_b = sorted((tlo, thi))
        visible = []
        if p["t0"] < min(blocked_a, p["t1"]):
            visible.append((p["t0"], min(blocked_a, p["t1"])))
        if max(blocked_b, p["t0"]) < p["t1"]:
            visible.append((max(blocked_b, p["t0"]), p["t1"]))
        d = (p["x0_m"] + p["target_shift_m"] + v * p["clock_offset_s"] - s)
        h2 = p["height_m"] ** 2
        for a, b in visible:
            dt = (b - a) / panels
            for j in range(panels):
                ta = a + j * dt
                tb = ta + dt
                qa = p["q0"] + p["q1_per_s"] * ta
                qb = p["q0"] + p["q1_per_s"] * tb
                ya = d + v * ta
                yb = d + v * tb
                ymin2 = F(0) if ya * yb <= 0 else min(ya * ya, yb * yb)
                ymax2 = max(ya * ya, yb * yb)
                panel_lo = p["amplitude"] * min(qa, qb) * h2 / (h2 + ymax2) ** 2
                panel_hi = p["amplitude"] * max(qa, qb) * h2 / (h2 + ymin2) ** 2
                lower += weight * dt * panel_lo
                upper += weight * dt * panel_hi
                count += 1
    return lower, upper, count


def outward(x, lower):
    f = float(x)
    if lower and F(f) > x:
        return math.nextafter(f, -math.inf)
    if not lower and F(f) < x:
        return math.nextafter(f, math.inf)
    return f


def finite_source_estimate(sc, nodes, weights):
    return math.fsum(float(w) * evaluate(float(n), sc)["value_s_m2"]
                     for n, w in zip(nodes, weights))


def run():
    selected = ["models/trust_region.py", "models/event_reference.py", "verification/test_small.py"]
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in selected}
    s = Scene()
    findings = {}

    # Necessary minimal topology counterexamples: each is a one-node, one-design-axis
    # affine segment. Check expected geometry independently, then check certificate.
    near0 = project_boundary(s, 0., -1, "z_near_m")
    far0 = project_boundary(s, 0., -1, "z_far_m")
    face_candidate = replace(s, plate_shift_m=.09)
    near1 = project_boundary(face_candidate, 0., -1, "z_near_m")
    far1 = project_boundary(face_candidate, 0., -1, "z_far_m")
    face_tie = project_boundary(replace(s, plate_shift_m=.08), 0., -1, "z_near_m")
    face_cert = certify_segment(s, face_candidate, [0.])
    failed_face_ids = [g["id"] for g in face_cert["guards"] if not g["positive"]]
    assert near0 < far0 and far1 < near1 and face_tie == 0
    assert face_cert["status"] == "reject_topology_crossing_or_guard"
    assert any(x.endswith(":lower") and x.startswith("face:") for x in failed_face_ids)
    findings["face_switch_minimal_counterexample"] = {
        "one_source_node": 0., "design_change": {"plate_shift_m": [0., .09], "half_width_m": .08},
        "projected_lower_edge_at_base_m": {"near": float(near0), "far": float(far0)},
        "projected_lower_edge_at_candidate_m": {"near": float(near1), "far": float(far1)},
        "exact_tie_at_plate_shift_m": .08,
        "certificate_status": face_cert["status"],
        "negative_guard_ids": failed_face_ids,
        "assessment": "required active-face branch flip is detected; segment is rejected",
    }

    end_candidate = replace(s, plate_shift_m=-.07)
    end_cert = certify_segment(s, end_candidate, [0.])
    candidate_lower = project_boundary(end_candidate, 0., -1, "z_near_m")
    t0_x = q(s.x0_m) + q(s.target_shift_m) + q(s.velocity_m_s) * q(s.clock_offset_s)
    end_event = (candidate_lower - q(s.x0_m) - q(s.target_shift_m)) / q(s.velocity_m_s) - q(s.clock_offset_s)
    failed_endpoint_ids = [g["id"] for g in end_cert["guards"] if not g["positive"]]
    assert candidate_lower < t0_x and end_event < 0
    assert end_cert["status"] == "reject_topology_crossing_or_guard"
    assert any(x.startswith("endpoint:") and x.endswith(":t0") for x in failed_endpoint_ids)
    findings["endpoint_crossing_minimal_counterexample"] = {
        "one_source_node": 0., "design_change": {"plate_shift_m": [0., -.07], "half_width_m": .08},
        "candidate_lower_near_projected_edge_m": float(candidate_lower),
        "target_x_at_t0_m": float(t0_x), "candidate_event_time_s": float(end_event),
        "certificate_status": end_cert["status"],
        "negative_guard_ids": failed_endpoint_ids,
        "assessment": "same active face, but event crosses t0; endpoint guard rejects",
    }

    clipped, clipped_info = clipped_candidate(s, [0.], [.2, 0.])
    assert clipped_info["certificate"]["status"] == "encoded_affine_segment_certified"
    assert all(g["positive"] for g in clipped_info["certificate"]["guards"])
    findings["safe_clipped_segment"] = {
        "alpha": clipped_info["alpha"], "encoded_plate_shift_m": clipped.plate_shift_m,
        "status": clipped_info["certificate"]["status"],
        "all_exact_guard_minima_positive": True,
    }

    # Independent Fraction Darboux implementation vs the production enclosure and the
    # frozen reference's closed-primitive estimate, including negative velocity and
    # a two-node weighted finite source.
    cases = [
        ("default_one_node", s, [0.], [1.], 16),
        ("default_one_node_refined", s, [0.], [1.], 64),
        ("reverse_velocity", replace(s, x0_m=.4, velocity_m_s=-.4), [0.], [1.], 32),
        ("two_node_weighted_source", s, [0., .1], [.25, .75], 32),
    ]
    enclosure_records = {}
    for name, scene, nodes, weights, panels in cases:
        exact_lo, exact_hi, expected_count = independent_exact_darboux(scene, nodes, weights, panels)
        module_iv, module_count = rational_forward_interval(scene, nodes, weights, panels)
        estimate = finite_source_estimate(scene, nodes, weights)
        assert module_count == expected_count
        assert module_iv.lo == outward(exact_lo, True)
        assert module_iv.hi == outward(exact_hi, False)
        assert module_iv.lo <= estimate <= module_iv.hi
        oi = objective_interval(module_iv, 1.)
        objective_estimate = .5 * ((estimate - 1.) ** 2)
        assert oi.lo <= objective_estimate <= oi.hi
        enclosure_records[name] = {
            "panels_per_visible_segment": panels, "panel_count": module_count,
            "independent_exact_lower_as_float": float(exact_lo),
            "independent_exact_upper_as_float": float(exact_hi),
            "exact_bound_numerator_denominator_bit_lengths": {
                "lower": [abs(exact_lo.numerator).bit_length(), exact_lo.denominator.bit_length()],
                "upper": [abs(exact_hi.numerator).bit_length(), exact_hi.denominator.bit_length()],
            },
            "outward_float_interval": module_iv.to_dict(),
            "frozen_reference_estimate_s_m2": estimate,
            "value_enclosed": True,
            "target_1_objective_interval": oi.to_dict(),
            "reference_objective_estimate": objective_estimate,
            "objective_enclosed": True,
        }
    findings["rational_darboux_checks"] = enclosure_records

    baseline = full_forward(s)
    uncertain = full_forward(replace(s, shadow_boundary_uncertainty_m=1e-4))
    overlap = compare(baseline, baseline)
    unknown_comparison = compare(uncertain, uncertain)
    contract_mismatch_refusal = None
    try:
        compare(baseline, uncertain)
    except ValueError as exc:
        contract_mismatch_refusal = str(exc)
    valid_but_overlapping_ratio = reduction_ratio(baseline, baseline, Interval(.001, .002).to_dict())
    pathological = {}
    for name, p in {
        "zero": Interval(0., 0.),
        "negative_or_crossing_zero": Interval(-.1, .1),
        "below_floor": Interval(1e-15, 1e-15),
        "unknown": Interval.unknown(),
    }.items():
        pathological[name] = reduction_ratio(baseline, baseline, p.to_dict())
        assert pathological[name]["decision"] == "reject"
    assert overlap["relation"] == "unresolved"
    assert unknown_comparison["relation"] == "unresolved"
    assert valid_but_overlapping_ratio["decision"] == "unresolved"
    findings["refusal_checks"] = {
        "same_objective_interval_comparison": overlap,
        "same_contract_input_uncertainty_comparison": unknown_comparison,
        "different_contract_comparison_refused": contract_mismatch_refusal,
        "positive_denominator_but_overlapping_actuals": valid_but_overlapping_ratio,
        "pathological_predicted_denominators": pathological,
        "assessment": "unknown/overlapping outcomes are unresolved; nonpositive, unknown, or <=1e-12 predictions reject",
    }

    return {
        "review_kind": "one narrow independent math/code check; not Seed/Sol sign-off",
        "project": "T03 round 3 event-aware trust region",
        "model_version": "T03-r3-affine-trust-1",
        "scope": selected,
        "sha256": hashes,
        "findings": findings,
        "limitations": [
            "This checks only the encoded finite discrete-source slab model and the requested three files.",
            "It does not certify input uncertainty, a continuous source, CAD/device behavior, or global optimization.",
            "The reference estimates are float closed-primitive evaluations; enclosure validity rests on the exact positive-kernel Darboux argument recorded in the review note.",
        ],
        "result": "no_blocking_defect_observed_in_scoped_checks",
    }


if __name__ == "__main__":
    result = run()
    out = ROOT / "reviews" / "independent_results.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
