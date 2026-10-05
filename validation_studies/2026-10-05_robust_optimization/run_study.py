"""Bounded CPU proof comparison. All outputs stay beside this script."""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import argparse
import csv
import json
import os
import platform
import sys
import time

import numpy as np
from evaluator import (HERE, PRODUCT, Evaluator, objective, scenario_draws,
                       scenarios_hash, sha256, source_hashes)


def optimize(config, seed, level, mode):
    evaluator = Evaluator(config["resolution"], config["training_actual_forward_budget_per_method"])
    latent = np.zeros((1, 12))
    if mode == "robust":
        latent = np.vstack([latent, scenario_draws(seed, config["random_training_scenarios"], "train")])
    batch_cost = 2 * len(latent)
    candidates = config["training_actual_forward_budget_per_method"] // batch_cost
    bounds = np.array(config["bounds"])
    lo, span = bounds[:, 0], np.ptp(bounds, axis=1)
    rng = np.random.default_rng(seed)
    best_design = np.asarray(config["initial_design"])
    best_rank = (float("inf"), float("inf"))
    history = []
    start = time.perf_counter()
    for i in range(candidates):
        if i == 0:
            design = np.asarray(config["initial_design"])
        elif i <= 5:
            design = np.array([80. + 40. * (i - 1), 5., 5.])
        elif i % 4 == 0:
            design = rng.uniform(lo, bounds[:, 1])
        else:
            fraction = i / candidates
            step = (0.25 * (1. - fraction) + 0.025) * span
            design = np.clip(best_design + rng.normal(size=3) * step, lo, bounds[:, 1])
        rows = [evaluator.evaluate(design, z, level) for z in latent]
        rank = objective(rows, mode, config["constraints"], config["lambda_sd"])
        if rank < best_rank:
            best_rank, best_design = rank, design.copy()
        history.append({"candidate": i, "design": design.tolist(),
            "rank": list(rank), "incumbent_rank": list(best_rank),
            "actual_forward_calls": evaluator.counter.forward_calls,
            "scenario_rows": rows})
    return {"mode": mode, "seed": seed, "level": level,
        "design": best_design.tolist(), "training_rank": list(best_rank),
        "training_scenario_hash": scenarios_hash(latent),
        "counter": asdict(evaluator.counter), "wall_s": time.perf_counter() - start,
        "failures": evaluator.failures, "history": history}


def summarize(rows, constraints):
    valid = [r for r in rows if r["valid"]]
    cvs = np.array([r["cv_percent"] for r in valid])
    etas = np.array([r["throughput"] for r in valid])
    violations = sum(not r["valid"] or r["cv_percent"] > constraints["cv_max_percent"] or
                     r["throughput"] < constraints["throughput_min"] for r in rows)
    return {"n": len(rows), "valid_n": len(valid), "invalid_n": len(rows) - len(valid),
        "mean_cv_percent": float(cvs.mean()) if len(cvs) else None,
        "sd_cv_percent": float(cvs.std(ddof=1)) if len(cvs) > 1 else None,
        "p95_cv_percent": float(np.quantile(cvs, .95)) if len(cvs) else None,
        "mean_throughput": float(etas.mean()) if len(etas) else None,
        "min_throughput": float(etas.min()) if len(etas) else None,
        "violation_count": violations, "violation_fraction": violations / len(rows)}


def paired_bootstrap(nominal, robust, constraints, seed, resamples=2000):
    """Conditional uncertainty of method difference; robust minus nominal."""
    if any(not a["valid"] or not b["valid"] for a, b in zip(nominal, robust)):
        return {"status": "not_computed_due_to_invalid_pair"}
    x = np.array([r["cv_percent"] for r in nominal])
    y = np.array([r["cv_percent"] for r in robust])
    vx = np.array([r["cv_percent"] > constraints["cv_max_percent"] or r["throughput"] < constraints["throughput_min"] for r in nominal], dtype=float)
    vy = np.array([r["cv_percent"] > constraints["cv_max_percent"] or r["throughput"] < constraints["throughput_min"] for r in robust], dtype=float)
    ids = np.random.default_rng(seed + 300000).integers(0, len(x), (resamples, len(x)))
    metrics = {"mean_cv_delta_pp": ((y - x).mean(), (y[ids] - x[ids]).mean(axis=1)),
        "p95_cv_delta_pp": (np.quantile(y, .95) - np.quantile(x, .95),
                            np.quantile(y[ids], .95, axis=1) - np.quantile(x[ids], .95, axis=1)),
        "violation_fraction_delta": ((vy - vx).mean(), (vy[ids] - vx[ids]).mean(axis=1))}
    return {k: {"estimate": float(est), "percentile_95_interval": np.quantile(vals, [.025, .975]).tolist()}
            for k, (est, vals) in metrics.items()}


def evaluate_selected(config, pair, seed, level):
    # This function is called only after BOTH optimizers have returned their designs.
    holdout = scenario_draws(seed, config["holdout_scenarios"], "holdout")
    train = scenario_draws(seed, config["random_training_scenarios"], "train")
    assert not any(np.array_equal(a, b) for a in holdout for b in train)
    nominal_rows, refined_rows = {}, {}
    for resolution_key, storage, count in (("resolution", nominal_rows, len(holdout)),
            ("refined_resolution", refined_rows, config["refined_holdout_scenarios"])):
        for mode, result in pair.items():
            ev = Evaluator(config[resolution_key])
            nominal = ev.evaluate(result["design"])
            rows = [ev.evaluate(result["design"], z, level) for z in holdout[:count]]
            storage[mode] = {"nominal": nominal, "rows": rows,
                "summary": summarize(rows, config["constraints"]),
                "counter": asdict(ev.counter), "failures": ev.failures}
    return {"seed": seed, "level": level,
        "holdout_hash": scenarios_hash(holdout), "train_hash": scenarios_hash(train),
        "coarse": nominal_rows, "refined": refined_rows,
        "paired_coarse": paired_bootstrap(nominal_rows["nominal"]["rows"], nominal_rows["robust"]["rows"], config["constraints"], seed, config["bootstrap"]["resamples"]),
        "paired_refined": paired_bootstrap(refined_rows["nominal"]["rows"], refined_rows["robust"]["rows"], config["constraints"], seed, config["bootstrap"]["resamples"])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="results")
    args = ap.parse_args()
    output = (HERE / args.output).resolve()
    if not output.is_relative_to(HERE):
        raise ValueError("Outputs must remain inside this study")
    output.mkdir(parents=True, exist_ok=True)
    config = json.loads((HERE / "study_config.json").read_text())
    before = source_hashes()
    manifest = {"baseline_commit": config["baseline_commit"],
        "baseline_commit_evidence": "cub-integrated-review-20261005/CUB_CANONICAL_DEPLOYMENT.json; migrated product has no .git",
        "product_root_relative": str(PRODUCT.relative_to(HERE.parents[3])),
        "product_python_sha256": before, "config_sha256": sha256(HERE / "study_config.json"),
        "python": sys.version, "numpy": np.__version__, "platform": platform.platform(),
        "cpu": platform.processor(), "cpu_count": os.cpu_count(),
        "thread_environment": {k: os.environ.get(k) for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "PYTHONDONTWRITEBYTECODE")},
        "started_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()}
    (output / "baseline_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    start = time.perf_counter()
    optimizations, validations = [], []
    for level in config["uncertainty_levels"]:
        for seed in config["seeds"]:
            pair = {mode: optimize(config, seed, level, mode) for mode in ("nominal", "robust")}
            optimizations.extend(pair.values())
            validation = evaluate_selected(config, pair, seed, level)
            validations.append(validation)
            print(json.dumps({"level": level, "seed": seed,
                "designs": {k: v["design"] for k, v in pair.items()},
                "coarse": {k: v["summary"] for k, v in validation["coarse"].items()},
                "refined": {k: v["summary"] for k, v in validation["refined"].items()} }), flush=True)
            (output / "checkpoint.json").write_text(json.dumps({"optimizations": optimizations, "validations": validations}, indent=2, allow_nan=False) + "\n")
    convergence = []
    # A small nominal refinement check, one preselected repeat at each level.
    for level in config["uncertainty_levels"]:
        for mode in ("nominal", "robust"):
            opt = next(o for o in optimizations if o["seed"] == config["seeds"][0] and o["level"] == level and o["mode"] == mode)
            ev = Evaluator(config["convergence_resolution"])
            row = ev.evaluate(opt["design"])
            convergence.append({"seed": opt["seed"], "level": level, "mode": mode,
                "resolution": config["convergence_resolution"], "row": row,
                "counter": asdict(ev.counter)})
    after = source_hashes()
    if before != after:
        raise RuntimeError("Canonical Python source changed during the study")
    report = {"config": config, "optimizations": optimizations,
        "validations": validations, "nominal_convergence": convergence,
        "product_python_unchanged": before == after,
        "wall_s": time.perf_counter() - start,
        "status": "completed_synthetic_proof_study_not_engineering_validation"}
    (output / "study_results.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    with (output / "summary.csv").open("w") as f:
        fields = ["level", "seed", "resolution", "mode", "source_x_mm", "mask1_width_mm", "mask2_width_mm", "nominal_cv_percent", "mean_cv_percent", "p95_cv_percent", "sd_cv_percent", "mean_throughput", "violation_count", "n", "training_forward_calls", "validation_forward_calls"]
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader()
        for v in validations:
            for resolution in ("coarse", "refined"):
                for mode, data in v[resolution].items():
                    opt = next(o for o in optimizations if o["seed"] == v["seed"] and o["level"] == v["level"] and o["mode"] == mode)
                    writer.writerow({"level": v["level"], "seed": v["seed"], "resolution": resolution, "mode": mode,
                        **dict(zip(["source_x_mm", "mask1_width_mm", "mask2_width_mm"], opt["design"])),
                        "nominal_cv_percent": data["nominal"]["cv_percent"],
                        **{k: data["summary"][k] for k in ("mean_cv_percent", "p95_cv_percent", "sd_cv_percent", "mean_throughput", "violation_count", "n")},
                        "training_forward_calls": opt["counter"]["forward_calls"], "validation_forward_calls": data["counter"]["forward_calls"]})
    print(f"Completed in {report['wall_s']:.2f}s; product Python hashes unchanged", flush=True)


if __name__ == "__main__":
    main()
