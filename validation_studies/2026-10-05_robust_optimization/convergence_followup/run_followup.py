"""Axis-separated, bounded numerical follow-up. First-round files are read-only."""
from __future__ import annotations
from dataclasses import asdict, replace
from pathlib import Path
import argparse
import hashlib
import json
import math
import sys
import time

import numpy as np

HERE = Path(__file__).resolve().parent
FIRST = HERE.parent
sys.path.insert(0, str(FIRST))
from evaluator import Evaluator, source_hashes, scenario_draws, scenarios_hash, weighted_metrics
from run_study import summarize


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def first_round_identity():
    m = json.loads((FIRST / "results/artifact_manifest.json").read_text())
    expected = dict(m["files"])
    expected["results/artifact_manifest.json"] = digest(FIRST / "results/artifact_manifest.json")
    actual = {n: digest(FIRST / n) for n in expected}
    if any(n != "results/artifact_manifest.json" and d != m["files"][n] for n, d in actual.items()):
        raise RuntimeError("First-round artifact verification failed")
    return actual


def roi_weights(axis, valid, radius):
    """A fixed 90-mm physical ROI fully represented by the 100-mm product grid.

    Cells centred slightly outside the ROI can contribute their clipped area.
    No product-outside sample is invented; the 10-mm inset exceeds half the
    coarsest cell diagonal. Domain coverage therefore remains ~100% at all grids.
    """
    full = float(np.max(axis))
    edges = np.r_[-full, (axis[:-1] + axis[1:]) / 2, full]
    nodes, wg = np.polynomial.legendre.leggauss(64)
    weights = np.zeros(valid.shape)
    for iy, ix in zip(*np.where(valid)):
        lo, hi = max(edges[ix], -radius), min(edges[ix + 1], radius)
        if hi <= lo:
            continue
        x = (lo + hi) / 2 + (hi - lo) / 2 * nodes
        top = np.sqrt(np.maximum(0., radius ** 2 - x ** 2))
        height = np.maximum(0., np.minimum(edges[iy + 1], top) - np.maximum(edges[iy], -top))
        weights[iy, ix] = (hi - lo) / 2 * np.dot(wg, height)
    area = weights.sum()
    return weights / area, float(area / (math.pi * radius ** 2))


class FollowupEvaluator(Evaluator):
    def __init__(self, resolution, alpha=.5, roi_radius=90.):
        super().__init__(resolution)
        self.alpha, self.roi_radius = alpha, roi_radius
        self.original_settings = self.settings
        self.results = []
        self.roi_w = None
        self.roi_coverage = None

    def _call(self, settings, mask, source):
        row = super()._call(settings, mask, source)
        self.results.append(row)
        return row

    def evaluate(self, design, latent=None, level=0.):
        z = np.zeros(12) if latent is None else np.asarray(latent)
        rpm = self.original_settings.carrier_rpm * (1. + level * z[11])
        shift_s = (self.alpha - .5) * self.original_settings.duration_s / self.original_settings.time_steps
        self.settings = replace(self.original_settings,
            carrier_phase_deg=6. * rpm * shift_s,
            planet_phase_deg=6. * rpm * (1. + 120. / 36.) * shift_s)
        self.results = []
        row = super().evaluate(design, latent, level)
        if row["valid"]:
            masked, bare = self.results
            if self.roi_w is None:
                self.roi_w, self.roi_coverage = roi_weights(masked["x"], np.isfinite(masked["field"]), self.roi_radius)
            amp = 1. + level * z[9]
            m = weighted_metrics(masked, self.roi_w, amp)
            u = weighted_metrics(bare, self.roi_w, amp)
            row.update({"interior90_cv_percent": m["cv_percent"],
                "interior90_throughput": m["area_mean_raw"] / u["area_mean_raw"],
                "interior90_area_fraction": self.roi_coverage,
                "quadrature_alpha": self.alpha})
        return row


def get_cases(config, first):
    cases = []
    for case in config["cases"]:
        seed, level = case["seed"], case["level"]
        designs = {o["mode"]: o["design"] for o in first["optimizations"]
                   if o["seed"] == seed and o["level"] == level}
        holdout = scenario_draws(seed, config["holdout_count"], "holdout")
        cases.append({**case, "designs": designs, "holdout": holdout,
                      "holdout_sha256": scenarios_hash(holdout)})
    return cases


def run_level(resolution, alpha, cases):
    start = time.perf_counter()
    output = []
    for case in cases:
        methods = {}
        for mode in ("nominal", "robust"):
            ev = FollowupEvaluator(resolution, alpha)
            nominal = ev.evaluate(case["designs"][mode])
            rows = [ev.evaluate(case["designs"][mode], z, case["level"]) for z in case["holdout"]]
            methods[mode] = {"nominal": nominal, "rows": rows,
                "mean_cv_percent": float(np.mean([r["cv_percent"] for r in rows])) if all(r["valid"] for r in rows) else None,
                "mean_interior90_cv_percent": float(np.mean([r["interior90_cv_percent"] for r in rows])) if all(r["valid"] for r in rows) else None,
                "counter": asdict(ev.counter), "failures": ev.failures}
        output.append({"seed": case["seed"], "level": case["level"],
            "holdout_sha256": case["holdout_sha256"], "methods": methods})
    calls = sum(m["counter"]["forward_calls"] for c in output for m in c["methods"].values())
    return {"resolution": resolution, "alpha": alpha, "cases": output,
            "actual_forward_calls": calls, "wall_s": time.perf_counter() - start}


def run_pilot(config):
    identity = first_round_identity(); sources = source_hashes()
    first = json.loads((FIRST / "results/study_results.json").read_text())
    cases = get_cases(config, first)
    out = []
    for res in config["pilot"]:
        ev = FollowupEvaluator(res)
        start = time.perf_counter()
        row = ev.evaluate(cases[1]["designs"]["nominal"])
        out.append({"resolution": res, "row": row, "counter": asdict(ev.counter),
                    "wall_s": time.perf_counter() - start})
    assert first_round_identity() == identity and source_hashes() == sources
    pilot = {"rows": out, "actual_forward_calls": sum(r["counter"]["forward_calls"] for r in out),
             "first_round_identity": identity, "product_python_identity": sources,
             "config_sha256": digest(HERE / "config.json")}
    (HERE / "pilot_results.json").write_text(json.dumps(pilot, indent=2) + "\n")
    print(json.dumps({"pilot_actual_calls": pilot["actual_forward_calls"],
        "rows": [{"resolution": r["resolution"], "wall_s": r["wall_s"], "kernel_s": r["counter"]["elapsed_s"]} for r in out]}, indent=2), flush=True)


def main(config):
    pilot = json.loads((HERE / "pilot_results.json").read_text())
    identity = first_round_identity(); sources = source_hashes()
    if identity != pilot["first_round_identity"] or sources != pilot["product_python_identity"]:
        raise RuntimeError("Inputs changed after pilot")
    first = json.loads((FIRST / "results/study_results.json").read_text())
    cases = get_cases(config, first)
    # Measured pilot informs a ray-work cost model. It is a planning estimate,
    # not a hardware benchmark or a prediction interval.
    samples = [(r["wall_s"] / (r["resolution"]["grid_size"] ** 2 * r["resolution"]["time_steps"] * r["resolution"]["source_order"] ** 2)) for r in pilot["rows"]]
    coefficient = max(samples)
    def estimate(res):
        return coefficient * res["grid_size"] ** 2 * res["time_steps"] * res["source_order"] ** 2 * len(cases) * 2 * (config["holdout_count"] + 1)
    axes = {"time": [(dict(grid_size=41, time_steps=n, source_order=5), .5) for n in config["planned_time_steps"]],
        "grid": [(dict(grid_size=g, time_steps=768, source_order=5), .5) for g in config["planned_grid_sizes"]],
        "source": [(dict(grid_size=41, time_steps=768, source_order=q), .5) for q in config["planned_source_orders"]],
        "phase": [(dict(grid_size=41, time_steps=n, source_order=5), alpha) for n in config["phase_test_time_steps"] for alpha in config["phase_offsets"]]}
    unique = {json.dumps([r, a], sort_keys=True): (r, a) for requests in axes.values() for r, a in requests}
    plan = {"unique_levels": len(unique), "planned_actual_forward_calls": len(unique) * len(cases) * 2 * (config["holdout_count"] + 1) * 2,
            "estimated_wall_s": sum(estimate(r) for r, _ in unique.values()), "cost_model": "max measured pilot wall/(grid_size^2*time_steps*source_order^2), extrapolated to 20 scenarios per level; conservative planning only"}
    (HERE / "execution_plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    print(json.dumps({"plan": plan}), flush=True)
    start = time.perf_counter(); levels = {}; skips = []; axis_keys = {}; actual_calls = 0
    for axis, requests in axes.items():
        axis_keys[axis] = []
        for res, alpha in requests:
            key = json.dumps([res, alpha], sort_keys=True)
            if key in levels:
                axis_keys[axis].append(key); continue
            estimate_s = estimate(res)
            remaining = config["resource_limits"]["main_wall_cap_s"] - (time.perf_counter() - start)
            expected_calls = len(cases) * 2 * (config["holdout_count"] + 1) * 2
            if estimate_s > remaining or actual_calls + expected_calls > config["resource_limits"]["main_actual_forward_call_cap"]:
                skips.append({"axis": axis, "resolution": res, "alpha": alpha,
                    "estimated_wall_s": estimate_s, "remaining_wall_s": remaining,
                    "reason": "Predefined resource cap would be exceeded"})
                continue
            level = run_level(res, alpha, cases)
            levels[key] = level; axis_keys[axis].append(key)
            actual_calls += level["actual_forward_calls"]
            print(json.dumps({"axis": axis, "resolution": res, "alpha": alpha,
                "calls": level["actual_forward_calls"], "wall_s": level["wall_s"],
                "case_mean_gaps": [{"level": c["level"], "seed": c["seed"],
                    "cv_gap_pp": c["methods"]["robust"]["mean_cv_percent"] - c["methods"]["nominal"]["mean_cv_percent"]} for c in level["cases"]]}), flush=True)
            checkpoint = {"config": config, "plan": plan, "levels": levels, "axis_keys": axis_keys,
                "skips": skips, "actual_forward_calls": actual_calls, "wall_s": time.perf_counter() - start,
                "first_round_unchanged": first_round_identity() == identity,
                "product_python_unchanged": source_hashes() == sources}
            (HERE / "followup_results.json").write_text(json.dumps(checkpoint, indent=2, allow_nan=False) + "\n")
    assert first_round_identity() == identity and source_hashes() == sources
    checkpoint.update({"skips": skips, "wall_s": time.perf_counter() - start, "status": "bounded_axis_study_completed"})
    (HERE / "followup_results.json").write_text(json.dumps(checkpoint, indent=2, allow_nan=False) + "\n")
    print(f"Completed {actual_calls} counted main calls in {checkpoint['wall_s']:.2f}s", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--pilot", action="store_true")
    args = ap.parse_args(); config = json.loads((HERE / "config.json").read_text())
    run_pilot(config) if args.pilot else main(config)
