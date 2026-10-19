# Finite protective-layer-pack experiment

See [中文研究报告](研究报告.md) for protocol, complete paired outcomes, failure
interpretation, actual/charged costs, and limits.

## Main result

40 paired runs (two fixed six-layer starts × five methods × four seeds).
No two-window 1% reflectance success. Starting with an already compliant
3–5 um window, no method preserved that window and improved 8–12 um.
Single-anchor half-wave neutrality was verified, but it demonstrably failed
to preserve the complete window. This is a constrained small-budget negative
result, not a general rejection of protective layer packs.

## Replay

From this directory, with Python 3.12 and requirements.txt installed:

    python mechanism_check.py
    python run_layer_packs.py
    python -m unittest -v test_layer_packs.py
    python analyze_results.py

Optional figures:

    python plot_results.py

No cloud-specific paths, credentials or production software are required.
The verified research kernel is bundled unchanged with provenance. Its source
is a pre-existing synthetic thin-film research experiment, not the production
simulation repository. All numerical data here are synthetic.

## Files

- mechanism_check.py and mechanism_checks.json: one-point analytic mechanism
  and full-window/absorption counterexamples, all seven insertion positions
- run_layer_packs.py: fixed candidate-pool and actual spectral-budget experiment
- test_layer_packs.py and test_report.txt: nine consistency/replay checks
- analyze_results.py: rebuild the Chinese report and detailed cost diagnostics
- plot_results.py and figures/: optional reproducible illustrations
- verified_kernel/: byte-identical original research kernel with provenance
- results/config.json: frozen target, materials, budgets, starts, kernel hash
- results/results.csv: all 40 run outcomes, no best-seed selection
- results/refinements.csv: all 240 selected finite-pack repair outcomes
- results/results.json: full candidate pools, thicknesses, best-improvement
  traces, independent dense/offset/extremum audits and optical cost accounting
- results/summary.json, summary.csv, diagnostics.json: aggregate results and
  actual versus charged costs, with final auditing and helper matrices separate
- MANIFEST.json: publication inventory after excluding transient logs and caches

No main software files were changed. This package publishes research scripts and synthetic results only.
