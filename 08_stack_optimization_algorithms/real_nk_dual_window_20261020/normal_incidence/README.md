# Dual-window real-material AR research — locally finalized research archive

**Status: original fixed-source normal-incidence results passed separate independent review; locally finalized.**
This package has not been uploaded, pushed or published. It preserves
the two already successful research prescriptions; no search was rerun.

Both normal-incidence, air-to-coated-ZnS-half-space routes pass the unchanged
3–5um and8–12um research guards R<=0.0099 and T>=0.9001, tolerance1e-6.
The gap is unconstrained. T means flux entering the ZnS half-space, not total
transmission through a1mm ZnS plate. Material data are source-specific film or
bulk proxies and do not establish project-process manufacturing validity.

| Route | Origin | Layers | Total nm | Max R,3–5um | Max R,8–12um | Min T,3–5um | Min T,8–12um |
|---|---|---:|---:|---:|---:|---:|---:|
| A | Genuine N=0 beam growth |10|4248.806764|0.968903233%|0.968259500%|98.342720348%|98.218998583%|
| B | Prior seven-layer start plus grouped structural jumps |10|3268.558512|0.924476489%|0.923568887%|98.155465216%|97.459988848%|

The original B search produced11rows, with adjacent identical ZnS rows; merging
those into one218.260068nm ZnS layer gives the equivalent archived10-layer form.
The final tables are rounded to six decimal nm and were re-audited after merging
and rounding. This numerical precision is not a fabrication tolerance claim.

## Files

- `prescriptions/A.csv`, `B.csv`, and corresponding JSON: complete layer tables,
  ordered **substrate outward**; physical incident order is reversed.
- `targets.json`: exact objective guards, tolerance, medium and geometry boundary.
- `materials/sources.json` and five `*_nk.csv`: full explicit source n/k tables,
  original source links/hashes, processes, data domains and per-CSV checksums.
  Numeric RII source tables are recorded as CC0-1.0; original YAML/PDF papers and
  unpublished product code are not included.
- `trajectories/`: empty-stack evidence, actual seven-layer B start, compacted
  successful event logs and every independently audited improvement. The event
  projection removes repetitive incumbent payloads and preserves timestamps,
  evaluated work, branch stages, solver status and archived improvements.
- `results/final_metrics.json`, `search_work.json`: final per-window metrics and
  actual completed search counters. A/B counts are not product logical-evaluation
  counts. A's153424 initial calls were a redundant bare-stack plateau audit.
- `spectra/*_plot_reference.csv`:408-point/window-pair illustrative subsets of
  the original dense spectra; they are not the final audit grid. Recompute the
  dense audit with the script below.
- `scripts/verify_prescriptions.py`: independent characteristic-matrix audit,
  raw n/k interpolation and dimensionless golden-section extrema; Python standard
  library only. No unpublished core, NumPy, SciPy, network or installation.
- `METHODS.html`: offline formulas, diagrams, units, defaults and approximations.
- `search/REPRODUCTION_LIMITS.md`: full search still depends on unpublished v3;
  this package independently reproduces final physical checks, not full search.
- `next_round/PLAN.md`: proposed start-stability, angle/polarization and finite
  double-surface research. No new target silently replaces the original benchmark.
- `provenance/`: hashes and sanitized evidence; no local absolute paths or keys.
- `MANIFEST.sha256.json`: checksum of each packaged file except itself.

## Independent check

From the package root, with any compatible existing Python3:

```powershell
python -B scripts/verify_prescriptions.py --output verification/recheck.json
```

Default10001 uniform+10000 shifted+all source knots per window, plus local extrema.
Each prescription is checked against the original audited metrics to2e-9 power
fraction, and against the original guarded goals. Exit0 means both match and pass.
The original audit's recurrence-vs-independent-matrix R/T difference was below
7e-15. This is a finite numerical audit; continuous_certificate=false.

The bundled `verification/standalone_recheck.json` records the packaging check;
the separate review also passed and its portable evidence is in `independent_review/`.

The original350 product Python files and62 named frozen entries were unchanged.
Two static-analysis files differed from the larger951-file historical snapshot;
this research did not modify/run them. Exact original artifact hashes are included,
but full raw logs and workstation paths stay outside the shared package.

## Independent review included

See `independent_review/REPORT.html`, `accepted_conclusion.json`, per-route audits,
extrema, boundary-flux checks, original review hashes and sanitized QA. No original
production code, workstation paths or paper PDFs were added. Angle/finite-plate
stress diagnostics completed as a separate research item and do not alter this
original half-space acceptance. Candidatev1 is preserved unchanged.
