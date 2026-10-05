"""Standard-library integrity audit; never starts a deposition evaluation."""
from pathlib import Path
import argparse
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", action="store_true", help="Also check original historical and product identities in the authorized workspace")
    args = parser.parse_args()
    m = json.loads((HERE / "handoff_manifest.json").read_text())
    errors = []
    for name, sha in m["files"].items():
        p = (HERE / name).resolve()
        if not p.is_relative_to(HERE) or not p.is_file() or digest(p) != sha:
            errors.append(name)
    status = json.loads((HERE / "CURRENT_STATUS.json").read_text())
    if status["resource_accounting"]["actual_core_calls"] != 130 or status["engineering_ranking_allowed"]:
        errors.append("call total or ranking guard")
    if not status["time_stability_at_grid21_legacy_source"]["shape_pass"] or status["same_step_finite_periodic_direct_agreement"]["shape_pass"]:
        errors.append("separate time/periodic guards")
    if status["finer_periodic_reference"]["accepted_requested_dt_s"] != .0015625 or status["joint_final_resolution_direct_agreement"] != "not run":
        errors.append("qualification scope")
    result_count = 0
    for name in m["files"]:
        if not name.endswith(".json"):
            continue
        d = json.loads((HERE / name).read_text())
        # Flat saved forward result records; enclosing reports contain copies.
        if not isinstance(d, dict) or "mode" not in d or "core_audits" not in d:
            continue
        result_count += 1
        if not math.isclose(d["total_duration_s"], 10888.888888888889, abs_tol=1e-9):
            errors.append(name + ": incomplete recipe")
        if not math.isclose(sum(s["duration_s"] for s in d["step_results"]), d["total_duration_s"], abs_tol=1e-9):
            errors.append(name + ": layer durations")
        for a in d["core_audits"]:
            if a["status"] != "completed" or not a.get("all_steps_observed") or a["actual_time_steps"] != a["requested_time_steps"] or a["actual_dt_s"] > .05:
                errors.append(name + ": core node audit")
    historical = product = 0
    if args.workspace:
        identity = json.loads((HERE / "NUMERIC_IDENTITY.json").read_text())
        first = HERE.parent
        product_dir = HERE.parents[4] / "projects/deposition_sim"
        for name, sha in identity["historical_identity"].items():
            prefix, rel = name.split("/", 1)
            root = {"first": first, "followup": first / "convergence_followup", "gate": first / "engineeringgate"}[prefix]
            p = root / (("results/artifact_manifest.json" if prefix == "first" else "artifact_manifest.json") if rel == "manifest" else rel)
            historical += 1
            if not p.is_file() or digest(p) != sha:
                errors.append("historical:" + name)
        for name, sha in identity["product_python_identity"].items():
            p = product_dir / name
            product += 1
            if not p.is_file() or digest(p) != sha:
                errors.append("product:" + name)
    print(json.dumps({"status": "passed" if not errors else "failed", "bundle_files_checked": len(m["files"]), "flat_forward_results_node_audited": result_count, "historical_files_preserved": historical, "product_python_files_preserved": product, "actual_cpu_calls": 130, "errors": errors}, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
