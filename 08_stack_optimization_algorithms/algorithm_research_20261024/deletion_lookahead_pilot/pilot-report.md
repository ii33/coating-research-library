# Negative pilot: independent deletion-child refinement

Date: 2026-10-24. Production source: `7e43ebf845d82e50e7bf38bbcc227671fbc68b04`.

## Result and falsifiable hypothesis

Hypothesis: under a bounded shared optical budget, refining four deletion children before selecting one can choose a better basin than selecting by their immediate weighted SSE. The decision metrics are unchanged original maximum constraint violation, each-band measurements, and strict nominal pass, not SSE alone.

**This schedule did not help this case.** Both arms chose child 3. The lookahead arm spent calls on losing branches but did not reverse the winning choice. Baseline A is better at the matched 43-completed-call prefix and also at a conservative 42-call prefix using less point-layer work than B. Neither arm satisfies all original targets. Do not add this lookahead schedule to default production on this evidence.

## Frozen case, materials, and controls

- ZnS substrate; alternating ZnS/YbF3 films. Four strict lower targets: R > 0.97 at 580–920 nm; R > 0.99 at 1039–1089 nm; T > 0.98 at 3650–5000 and 7650–10550 nm. Both independent mean and pointwise criteria enabled. Unpolarized angles 40–50 degrees inclusive at 1-degree spacing.
- Material model is an explicitly derived **k = 0 mathematical hypothesis**, not measured lossless engineering data. Original source n dispersion and sample grids are unchanged; all three datasets use new derived material IDs and explicit zero k. Original source material snapshot remains separately archived. Unknown-k opt-in is false. See `inputs/derived-k0-pilot-manifest.json`.
- Training grid: at most 5 nm spacing, 932 wavelengths across four bands and 11 angles, 10,252 sample pairs. This is screening only. **No independent denser/extremum audit was run.** No tolerance, hidden margin, target, or scorer was changed.
- Fresh deterministic 62-layer, three-quarter-demand prior, not a recovered historical 67/87-layer film and not selected by scored outcome. Shared bounded warm-up freezes one identical actual local-refinement endpoint for both arms. Existing exact-zero removal and exact same-material/optical-set merge are applied identically before branching and after each deletion. Substrate-outward ordering is preserved.
- CPU-only, requested one numerical thread; Python 3.12.14, NumPy 2.5.4, SciPy 1.18.1. Frozen 512 MiB working-set guard; no manufacturing or low layer-count cap. One serial trial, A then B, no randomized repeats or held-out case. No scorer performance optimization mixed into the comparison.

## Predeclared schedule and actual resource use

Shared warm-up: 24 physical full-grid evaluations including the initial Jacobian refresh. Each arm: at most 64 physical calls and a fixed 90-second cooperative admission deadline. First evaluate the shared parent and four identical raw deletion children (5 forward calls). A selects raw minimum SSE and refines only it. B gives each child 8 independent all-layer refit calls, then restarts refinement from the lowest-SSE endpoint for remaining calls. All raw and Jacobian refresh calls are counted; parent remains eligible as immutable fallback. Local optimization is the unchanged production all-layer L-BFGS-B refiner.

| Phase | F calls | FJ calls | Completed | Wall return (s) | Stop |
|---|---:|---:|---:|---:|---|
| Shared warm-up | 0 | 24 | 24 | 61.764 | Call limit |
| A raw selection | 5 | 45 | 50 | 90.395 | Wall limit |
| B independent refits | 5 | 38 | 43 | 91.167 | Wall limit |

Both arms stopped before 64 calls, without extending the deadline. These are **not equal-64-call endpoints**. The final completed calls ended at 89.235 s (A) and 89.984 s (B); existing scoring/optimizer bookkeeping caused return after 90 s, with no subsequent new optical dispatch. No incomplete physical calls occurred. F and FJ have different costs, so they are reported separately.

The shared warm-up changed max violation from 0.150033087 to 0.044898333 and weighted SSE from 0.00378340749 to 7.52372842e-6. Its last six SSEs continued falling, ending 1.01234e-5, 9.63027e-6, 8.92988e-6, 8.39408e-6, 7.98115e-6, 7.52373e-6. **Stationarity was not established; this is a branch-selection test, not evidence of escaping a local optimum.** Its strict-best point differed from its actual endpoint; the latter was deliberately frozen, as recorded in `shared-parent.json`.

## Deterministic children and branch ranks

Selection uses first the thickest physical layer, then maximin Euclidean distance over exact material/optical-set one-hot identity, normalized log thickness, and normalized physical stack center. Stable layer ID then index breaks ties. No wavelength or layer index was tuned. Full IDs, features, hashes, and merge maps are in `deletion-children.json`.

The warm-up endpoint had 62 raw rows but **58 physical layers**: two exact-zero rows were removed, followed by two equivalent neighbor merges. Thus every deletion starts from the same 58-layer physical parent, not from an artificially claimed 62-layer stack.

| Child | Removed material / frozen index | Removed nm | Raw / physical rows after deletion | Raw SSE | SSE after 8 calls | Max violation after 8 calls |
|---|---|---:|---:|---:|---:|---:|
| 0 | YbF3 / 56 | 697.146510 | 57 / 56 | 3.60994353e-3 | 1.57611559e-3 | 0.481075795 |
| 1 | ZnS / 3 | 123.112859 | 57 / 56 | 1.40075598e-4 | 2.42147368e-5 | 0.052397288 |
| 2 | YbF3 / 0 | 197.291830 | 57 / 57 | 1.03180597e-4 | 3.40361424e-5 | 0.094937406 |
| 3 | ZnS / 57 | 37.618733 | 57 / 57 | 4.70449074e-5 | 8.55480489e-6 | 0.037740873 |

Raw SSE rank: 3, 2, 1, 0. Refined rank: 3, 1, 2, 0. Only the middle ranks reverse. Some children reduce SSE while worsening original maximum violation; they are exploration endpoints, not automatically accepted strict champions. B uses 24 FJ calls on losing branches and restarts the selected optimizer, whereas A retains a continuous chosen-branch trajectory. This pilot does not separate those two overhead mechanisms.

## Matched completed-call and work-prefix evidence

Original max violation is dimensionless; here 0.01 equals a one-percentage-point deficit because each active criterion's normalizing scale is 1. SSE is the canonical equal-window/user-weighted guide. Strict champion and minimum-SSE explored point are explicitly separate.

| Prefix | Calls F / FJ | F point-layers | FJ point-layers | Strict-best max violation | SSE at strict best | Minimum explored SSE |
|---|---:|---:|---:|---:|---:|---:|
| A at 43 | 5 / 38 | 2,911,568 | 22,205,832 | 0.023301731 | 2.72538420e-6 | 2.20762290e-6 |
| B at 43 | 5 / 38 | 2,911,568 | 22,041,800 | 0.035015040 | 6.42334503e-6 | 6.42334503e-6 |
| A at 42, lower work | 5 / 37 | 2,911,568 | 21,621,468 | 0.023301731 | 2.72538420e-6 | 2.26179557e-6 |

A43 uses 0.66% more total point-layer proxy than B43. A42 uses less than B43 and remains better on both recorded criteria. Point-layers are a work proxy, **not exact FLOPs, equal wall time, or memory use**. A43 completed at 76.048 s; B43 at 89.984 s. One serial run is insufficient for a robust timing claim.

## Actual wall-endpoint results

| Candidate | Raw / physical layers | Total nm | Max violation | Weighted SSE | Original-grid pass |
|---|---:|---:|---:|---:|---|
| Frozen shared parent | 62 / 58 | 8089.302798 | 0.044898333 | 7.52372842e-6 | No |
| A strict champion, 50 calls | 57 / 57 | 8227.234750 | 0.023018759 | 2.04280055e-6 | No |
| B strict champion, 43 calls | 57 / 57 | 8163.906039 | 0.035015040 | 6.42334503e-6 | No |

At each actual wall endpoint, strict champion and best explored SSE happen to be the same evaluated candidate. A's last accepted optimizer endpoint is different (max violation 0.023517483, SSE 2.04531408e-6); it is preserved separately in the raw summary rather than silently substituted. Final algebraic count checks found no additional zeros or equivalent neighbors. No new optics were dispatched for that bookkeeping. Thickness rises during this spectral-search pilot; it is **not** the separate feasible thinning algorithm.

Each cell below is sampled minimum / minimum over angle-specific complete-band wavelength means. Values are fractions, not percentages.

| Band | Shared parent | A wall champion | B wall champion |
|---|---|---|---|
| R, 580–920 nm | 0.946757689 / 0.980576701 | 0.958675468 / 0.979172183 | 0.940257458 / 0.980856246 |
| R, 1039–1089 nm | 0.986266329 / 0.990375400 | 0.985780270 / 0.989447442 | 0.983073925 / 0.989869364 |
| T, 3650–5000 nm | 0.935101667 / 0.977129210 | 0.965544519 / 0.979471290 | 0.944984960 / 0.978508456 |
| T, 7650–10550 nm | 0.949229395 / 0.974982380 | 0.956981241 / 0.977744347 | 0.946005144 / 0.975356943 |

## Interpretation, limits, and next hypothesis

This is a useful negative result for one predeclared four-child/eight-call schedule: diversification consumed most of a short budget without changing the winning branch while the parent still benefited from ordinary descent. It is not a general rejection of topology lookahead, proof of global optimization, or evidence that the engineering target is feasible/infeasible. There is no held-out, alternate switch-mode, statistical uncertainty, or denser-audit evidence.

Possible next hypothesis, **not tested here**: only admit alternative-child competition after a measured local-progress plateau, and test the admission rule against an equal-budget continuation-only control while separating optimizer restarts from branch competition. Do not tune this same case until a favorable result appears. A parent-controlled further protocol and distinct cases would be needed before any general claim or default change.

## Reproduction and artifact index

`request-v3.json` is the exact executed current-format request. The incoming v2 fixture was explicitly re-authored as v3 with the experimental thinning flag disabled; production has no v2 decoder. `inputs/` contains exact original and derived requests, the initial parent, and provenance manifests. `protocol.json` records the predeclared constants. `*-calls.jsonl` records every evaluation, timing, metrics, and cumulative work. `*-summary.json`, `result.json`, and saved champion/best-explored designs retain full results. `compact-comparison.json` is the machine-readable prefix comparison; `summarize_pilot.py` recomputes it without optical dispatch.

Use the source SHA above with the recorded numerical dependencies. Run a **separate copy** of `run_pilot.py` with its sibling `inputs/`, with numerical thread environment variables `OPENBLAS_NUM_THREADS`, `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS` all set to 1 and the source checkout on `PYTHONPATH`. It overwrites output files. Its input-directory binding alone was made relative after execution; both executed and portable hashes are in `portable-harness-provenance.json`. Input/output hashes and the relative reproduction command are in `artifact-manifest.json`. No production file was changed by this experiment, and no additional physical run was performed during reporting.
