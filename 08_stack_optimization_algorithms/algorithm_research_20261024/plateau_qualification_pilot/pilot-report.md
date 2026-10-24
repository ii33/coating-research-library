# Plateau qualification pilot: bounded inconclusive result

Date: 2026-10-24. Source SHA: `7e43ebf845d82e50e7bf38bbcc227671fbc68b04`.

## Finding

No operational plateau was admitted within the predeclared warm-up bound. **The three comparison arms were not launched.** This does not establish a local minimum or show that deletion lookahead succeeds or fails after a plateau. It records continued local progress on one difficult case while declining to run an inapplicable escape experiment.

The warm-up used 256 admitted full-grid FJ calls, 256 completed calls, 487.870 seconds, and 149,597,184 FJ point-layers. F calls: 0. Stop: `call_limit`. The ceiling was 256 FJ or 600 s, whichever first, with no extension.

## Purpose and frozen protocol

The falsifiable conditional hypothesis was that, **after a measured plateau**, a deterministic deletion-child/refinement competition improves original spectral constraints more efficiently than both uninterrupted local continuation and a restart-only control. Without the condition, no three-arm conclusion is available.

The seed is the prior negative pilot's saved A57 strict champion, not a fresh seed, a recovered historical design, or a seed selected during this run. Its exact bytes are frozen in `inputs/warm-start-a57.json`. Both mean and pointwise strict original goals remain enabled: R > 0.97 at 580–920 nm; R > 0.99 at 1039–1089 nm; T > 0.98 at 3650–5000 and 7650–10550 nm. Unpolarized angles 40–50 degrees at 1-degree steps; maximum wavelength step 5 nm, 10,252 wavelength-angle pairs. No goals, margins, constraints, scorer, or production source changed.

Materials remain the explicitly derived k=0 mathematical ZnS-substrate/ZnS/YbF3 model from the first pilot, with original n dispersion and source grids unchanged and new derived material IDs. This is not a measured engineering lossless-material claim. `inputs/derived-k0-pilot-manifest.json` preserves source/derived provenance. No independent denser/extremum audit was run; all metrics are screening-grid results.

Operational plateau required at least 64 FJ calls and two consecutive, non-overlapping windows of 16 accepted-iterate transitions each. In **each** window: relative best SSE improvement <=0.001 (0.1%), and strict-best original maximum-violation improvement <=0.0001 absolute. This is a disclosed project research criterion, not a convergence or local-optimum theorem. The exact comparisons use no epsilon relaxation.

Had it triggered, A would retain the same live L-BFGS-B invocation via normal callback return; B would restart the identical raw topology from the same complete cached checkpoint; C would give four deterministic diverse positive-row deletions 8 FJ calls each, then continue the best refined child, charging its refresh. Every arm would have 64 times checkpoint-row-count times10,252 FJ point-layers and 180 s; no new F-only calls. This all-FJ policy differs from the first pilot and is declared before execution. A/B would preserve raw topology to keep the optimizer-history control; C would clean exact zeros/equal optical neighbors after row deletion. These planned arms are **untested here**.

## Plateau and convergence evidence

Accepted progress callbacks: 231; solver-committed accepted iterations: 232; SciPy objective invocations: 256; objective cache hits: 1; aborted objective invocations: 0. Physical and objective calls are not interchangeable. A complete cached initial Jacobian avoids an uncharged refresh; the initial warm-up FJ is counted.

There were 171 eligible admitted plateau checks and zero passes. The last observed windows were:

| Accepted-iterate range | Relative best SSE gain | Strict-best max-violation gain | Meets both thresholds |
|---|---:|---:|---|
| 199–215 | 0.0113862334 | 0.000231308607 | False |
| 215–231 | 0.00534486408 | 2.90082235e-05 | False |

The smallest observed maximum relative SSE gain across any pair of eligible windows was 0.0113862334, compared with the required 0.001. All windows are preserved in `plateau-checks.json`; these are not thresholds retuned after seeing results.

The final projected-gradient diagnostic is r = x - project_bounds(x - gradient_x F), with x_i = d_i /100 nm, lower and upper bounds transformed identically, exact bound comparisons and no epsilon. Its infinity norm is 1.52623811e-07; raw coordinate-gradient infinity norm is 1.52623812e-07. It is a diagnostic for the original canonical SSE, not a certificate that all nominal constraints pass or that a global/local optimum has been found.

The production callback commits an accepted iterate before checking the budget, then emits progress. Thus a plateau first reached exactly at the terminal admission cannot be admitted for branching. Callback counts and the separately returned actual endpoint are both retained; do not interpret a missing final callback as an unevaluated endpoint.

Post-run recorded-data arithmetic also included the final committed endpoint at call 256 / accepted iteration 232. Its two windows pass both thresholds: False. This boundary check launches no arms and dispatches no optics; its exact values are in `compact-result.json`.

## Optical metrics and physical counts

Max violation is dimensionless; here 0.01 corresponds to a one-percentage-point deficit. SSE is the unchanged canonical equal-window/user-weighted guide. Strict champion, best explored SSE, and actual optimizer endpoint remain distinct roles.

| Candidate | Raw / exact-cleaned physical layers | Total nm | Original max violation | Weighted SSE | Original-grid nominal pass |
|---|---:|---:|---:|---:|---|
| Saved A57 starting design | 57 / 57 | 8227.234750 | 0.023018759 | 2.04280055e-06 | False |
| Warm-up strict champion | 57 / 57 | 8055.165809 | 0.012623299 | 4.78539274e-07 | False |
| Best explored SSE | 57 / 57 | 8049.439329 | 0.012669302 | 4.76541656e-07 | False |
| Actual accepted endpoint | 57 / 57 | 8049.439329 | 0.012669302 | 4.76541656e-07 | False |

Each band cell below is sampled minimum / minimum over angle-specific complete-band wavelength means. Values are fractions, not percentages.

| Band | Metric, wavelength nm | Starting design | Strict champion | Actual endpoint |
|---|---|---|---|---|
| 1 | R, 580–920 | 0.958675468 / 0.979172183 | 0.961158027 / 0.974685137 | 0.961049307 / 0.974764433 |
| 2 | R, 1039–1089 | 0.985780270 / 0.989447442 | 0.986993511 / 0.989609494 | 0.987129592 / 0.989562749 |
| 3 | T, 3650–5000 | 0.965544519 / 0.979471290 | 0.967410644 / 0.979229355 | 0.967339316 / 0.979208555 |
| 4 | T, 7650–10550 | 0.956981241 / 0.977744347 | 0.967376701 / 0.978815044 | 0.967330698 / 0.978837832 |

Layer cleanup is algebraic bookkeeping only: exact-zero removal and equal material/optical-set neighbor merge, no positive near-zero deletion or extra physics. The raw optimized variables are not silently changed. This is spectral refinement, not the separate feasible total-thickness-reduction operator.

## Limits and next hypothesis

One deliberately warm-started case, one serial run, both criteria enabled, synthetic k=0 materials and a coarse screening grid provide no cross-family, switch-mode, statistical-repeat, or dense-audit generalization. Work is a point-layer proxy, not FLOPs; memory enforcement is a declared production-workspace plus retained-checkpoint-array plus 128 MiB record allowance, not measured RSS. The frozen cap is 512 MiB; no low layer-count cap, GPU or user computer was used.

The supported lesson is narrow: this checkpoint still allowed substantial ordinary local descent within the bound, so a short previous budget was not evidence of being trapped. A possible next isolated hypothesis is whether progress-adaptive longer local service and retained optimizer history outperform repeated short restarts at equal work. That comparison has **not** been run here. Do not extend this same run until a plateau appears or report an escape result from the missing arms.

## Reproduction and versioned data

`protocol.json` was written before the first physical dispatch and records constants and exact input hashes. `run_plateau_pilot.py` is the executed experimental wrapper; it calls the unchanged production evaluator/refiner. `record_helpers.py` derives from the prior record/selection helpers, excluding zero-row and physically unchanged deletion proposals. `warmup-calls.jsonl` and `warmup-accepted.jsonl` are distinct physical-call and accepted-iterate histories. `warmup-summary.json`, saved designs, `result.json`, and `compact-result.json` preserve outcomes. `summarize_plateau.py` performs only recorded-data arithmetic and algebraic count checks.

Numerical environment: Python 3.12.14, NumPy 2.5.4, SciPy 1.18.1; numerical thread environment variables were all 1. Use a separate copied directory with its relative `inputs/`, the source SHA above on PYTHONPATH, and recorded dependencies. The harness overwrites outputs. `artifact-manifest.json` supplies hashes. No production files or remote software releases are changed by this experiment.
