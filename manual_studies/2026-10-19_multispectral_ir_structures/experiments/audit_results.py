#!/usr/bin/env python3
"""Review stored final candidates on a disjoint-interior grid.

Use --rerun-seed11 to additionally repeat both cases and all three optimizers.
No stored candidate or optimization result is replaced by this audit.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from run_experiment import (ROOT, CASES, LAYER_N, TARGET_R, metrics,
                            reflection_recursion, run_one, tmm_normal)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rerun-seed11", action="store_true")
    args = parser.parse_args()
    output = ROOT / "results"
    data = json.loads((output / "results.json").read_text())
    audit = {
        "scope": "Independent review of recorded final candidates only; no optimization, main application edits or real-material validation.",
        "offset_grid_interior_points_per_window": 16384,
        "offset_grid_note": "Midpoints of the 16385-point audit grid; all interior points are disjoint from training, 4097-point validation and 16385-point audit grids. Boundary endpoints are additionally included when comparing worst R.",
        "original_train_validation_shared_points_per_window": 17,
        "original_validation_grid_is_subset_of_audit": True,
        "run_count": len(data["runs"]),
        "rows": [],
    }
    stored_metric_max_error = 0.0
    for result in data["runs"]:
        windows = CASES[result["case"]]
        thickness = result["thickness_um_from_air_to_substrate"]
        for field, points in (("independent_dense_metrics", 4097),
                              ("higher_density_audit_metrics", 16385)):
            for actual, stored in zip(metrics(thickness, windows, points), result[field]):
                stored_metric_max_error = max(stored_metric_max_error, abs(actual["max_R"] - stored["max_R"]))
        for (lo, hi), stored in zip(windows, result["higher_density_audit_metrics"]):
            edges = np.linspace(lo, hi, 16385)
            interior = (edges[:-1] + edges[1:]) / 2
            training = np.linspace(lo, hi, 81)
            validation = np.linspace(lo, hi, 4097)
            assert len(np.intersect1d(training, validation)) == 17
            assert len(np.intersect1d(validation, edges)) == 4097
            assert all(np.intersect1d(interior, grid).size == 0
                       for grid in (training, validation, edges))
            wl = np.concatenate(([lo], interior, [hi]))
            rr, tt = tmm_normal(wl, thickness, LAYER_N)
            independent_r = reflection_recursion(wl, thickness, LAYER_N)
            audit["rows"].append({
                "case": result["case"], "method": result["method"], "seed": result["seed"],
                "window_um": [lo, hi],
                "max_R_offset_plus_boundaries": float(rr.max()),
                "max_R_original_audit": stored["max_R"],
                "max_R_absolute_difference": float(abs(rr.max() - stored["max_R"])),
                "same_pass_classification": bool((rr.max() <= TARGET_R) == (stored["max_R"] <= TARGET_R)),
                "max_energy_error": float(abs(rr + tt - 1).max()),
                "max_abs_matrix_recursion_R_difference": float(abs(rr - independent_r).max()),
            })
    audit["recomputed_stored_max_R_max_abs_error"] = stored_metric_max_error
    audit["max_abs_R_difference_offset_vs_original_audit"] = max(row["max_R_absolute_difference"] for row in audit["rows"])
    audit["all_window_pass_classifications_unchanged"] = all(row["same_pass_classification"] for row in audit["rows"])
    for field in ("max_energy_error", "max_abs_matrix_recursion_R_difference"):
        audit[field] = max(row[field] for row in audit["rows"])
    (output / "independent_review_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: value for key, value in audit.items() if key != "rows"}, indent=2))
    if args.rerun_seed11:
        repeats = []
        for case, windows in CASES.items():
            for method in ("classic_local", "classic_de", "de_local"):
                fresh = run_one(case, windows, method, 11)
                old = next(row for row in data["runs"] if row["case"] == case and row["method"] == method and row["seed"] == 11)
                repeats.append({
                    "case": case, "method": method, "seed": 11,
                    "same_thickness_bitwise": fresh["thickness_um_from_air_to_substrate"] == old["thickness_um_from_air_to_substrate"],
                    "same_training_objective": fresh["training_objective"] == old["training_objective"],
                    "same_actual_calls": fresh["actual_stack_evaluations_including_fd"] == old["actual_stack_evaluations_including_fd"],
                })
        (output / "reproducibility_check.json").write_text(json.dumps(repeats, ensure_ascii=False, indent=2) + "\n")
        assert all(row[key] for row in repeats for key in ("same_thickness_bitwise", "same_training_objective", "same_actual_calls"))
        print("All six seed-11 repetitions reproduced thickness, objective and call count exactly.")
    assert stored_metric_max_error < 1e-12
    assert audit["all_window_pass_classifications_unchanged"]


if __name__ == "__main__":
    main()
