#!/usr/bin/env python3
"""Audit exact, unperturbed heuristic seeds separately from optimizer ranking."""
import csv
import json
import time
from pathlib import Path
import numpy as np
from run_experiment import (ROOT, CASES, Objective, classical_templates, run_local,
                            metrics, AUDIT_POINTS)

def main():
    rows = []
    full = []
    for case, windows in CASES.items():
        for name, ds in classical_templates(windows):
            obj = Objective(windows, 1200)
            started = time.perf_counter()
            details = run_local(obj, ds, 1200)
            elapsed = time.perf_counter() - started
            pre, post = metrics(ds, windows, AUDIT_POINTS), metrics(obj.best_x, windows, AUDIT_POINTS)
            entry = {"case": case, "template": name, "actual_calls": obj.calls,
                     "wall_seconds": elapsed, "before": pre, "after": post,
                     "best_thickness_um": obj.best_x.tolist(), "solver": details}
            full.append(entry)
            for b, a in zip(pre, post):
                rows.append({"case": case, "template": name,
                             "window_um": "-".join(map(str, a["window_um"])),
                             "before_max_R_percent": 100*b["max_R"],
                             "after_max_R_percent": 100*a["max_R"],
                             "after_worst_violation_percentage_points": 100*a["worst_violation_absolute"],
                             "actual_calls": obj.calls, "wall_seconds": elapsed})
            print(case, name, "before", [round(100*m["max_R"], 4) for m in pre],
                  "after", [round(100*m["max_R"], 4) for m in post], "calls", obj.calls, flush=True)
    out = ROOT / "results"
    (out / "template_probe.json").write_text(json.dumps(full, ensure_ascii=False, indent=2), encoding="utf-8")
    with (out / "template_probe.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)

if __name__ == "__main__":
    main()
