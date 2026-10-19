# Reproducible synthetic coating-search experiment

See **研究笔记.md** for the Chinese research note and qualifications.

This is a standalone cloud experiment, not a change to the optical simulation
application. All optical constants are synthetic and wavelength independent.
It must not be used to claim real infrared-material performance.

## Run

```sh
python -m unittest -v test_experiment.py
python run_experiment.py
python probe_templates.py
python audit_results.py --rerun-seed11
```

Use `--no-plot` to run without matplotlib. NumPy and SciPy are the only core
dependencies. The recorded versions are in `requirements.txt` and results.json.

## Deliverables

- `run_experiment.py`: normal-incidence TMM, physical checks, 18 fixed-seed runs,
  actual evaluation counting, independent dense-grid validation, JSON/CSV/plots
- `probe_templates.py`: separate exact-template basin/coverage experiment
- `test_experiment.py`: seven regression tests
- `audit_results.py`: stored-metric recomputation, disjoint-interior grid audit and optional six-run repeatability check
- `results/results.json`, `results/results.csv`: full per-run/per-window results
- `results/summary.json`, `results/summary.csv`: three-seed summaries
- `results/template_probe.json`, `.csv`: template experiment
- `results/reproducibility_check.json`: bitwise repeatability of seed 11 for both cases and all three methods
- `results/independent_review_audit.json`: disjoint-interior midpoint-grid cross-check for all final candidates
- `results/test_report.txt`: regression test report
- `results/spectra.png`, `spectra_target_zoom.png`: representative median-ranked runs
- `研究笔记.md`: Chinese analysis, limitations, sources, and next research questions

There is no needle-insertion implementation or claim of continuous-wavelength
certification. Dual-window AR leaves the intervening gap unconstrained; it is
not a two-passband filter with a rejection band.

Validation grids are independent of objective evaluation, not disjoint wavelength
holdouts: each 81/4097-point pair shares 17 points; 4097 is nested in 16385.
The additional midpoint audit uses 16384 disjoint interior points per window
plus boundary endpoints. All validation is excluded from objective-call counts;
the hybrid pre-local diagnostic is included in the recorded wall time.
