"""Read-only persisted-output and canonical Python identity verification."""
import hashlib
import json
from evaluator import HERE, source_hashes


def main():
    manifest = json.loads((HERE / "results/artifact_manifest.json").read_text())
    errors = []
    for name, digest in manifest["files"].items():
        path = (HERE / name).resolve()
        if not path.is_relative_to(HERE):
            errors.append(f"Escaping path: {name}")
        elif not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append(f"Missing or changed: {name}")
    baseline = json.loads((HERE / "results/baseline_manifest.json").read_text())
    if source_hashes() != baseline["product_python_sha256"]:
        errors.append("Canonical Python source hash mismatch")
    p = json.loads((HERE / "results/study_results.json").read_text())
    for o in p["optimizations"]:
        if o["counter"]["forward_calls"] != 240:
            errors.append("Training budget mismatch")
    for v in p["validations"]:
        if v["holdout_hash"] == v["train_hash"]:
            errors.append("Scenario partition collision")
        for res, expected in (("coarse", 130), ("refined", 34)):
            for method in ("nominal", "robust"):
                if v[res][method]["counter"]["forward_calls"] != expected:
                    errors.append("Validation call mismatch")
    print(json.dumps({"verified_study_files": len(manifest["files"]),
        "canonical_python_files": len(baseline["product_python_sha256"]),
        "errors": errors, "status": "passed" if not errors else "failed"}, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
