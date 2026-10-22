# Frozen IR structure experiment

This isolated research does not modify coating-sim production code. Its only optical engine is the byte-unchanged production source at 68835133025ffc1e74df2fe00921e4961f691efb. It is not a manufacturing acceptance run or an infeasibility proof.

## Scope and frozen inputs

The selected first branch is supplier_ybf3, the lower prior worst-gap branch, with the full independent Merck YbF3 n/k pair. Deposited ZnS is the author-export film model; bulk ZnS remains Querry substrate material. Exported source zeros are model values, not measured zero absorption bounds. No cross-source n/k splicing, extrapolation, extra material, backside coating, relaxed threshold, or relaxed sampling is introduced.

Every search trial uses the complete joint four-window optics: unpolarized R >= 99% at 580–920 and 1044–1084 nm, strictly R < 3% at 3000–5000 and 7000–12000 nm, 1 nm inclusive wavelengths and 13 integer angles 39–51 degrees. 95,992 wavelength-angle values per trial. Maximum 64 layers and minimum 5 nm; no user maximum layer/total thickness. Search boxes below are explicit experimental search limitations, not manufacturing constraints.

## Cold-generated structures

All families start from the same source-derived separated-HR prior, five pairs at each of five source-derived centers, 50 HR layers. The descending case reverses the HR center/window sequence, not a prior optimized answer. The six starting prescriptions are archived before any scoring. They never borrow thicknesses from a previous failed candidate.

Incident-to-substrate schematic (the stored file reverses this order):

1. Air | HR ascending | ZnS substrate.
2. Air | L(6000 nm, quarter-wave) | HR ascending | substrate.
3. Air | L(4000 nm, half-quarter) H(6000 nm, quarter-quarter) L(9000 nm, half-quarter) | HR ascending | substrate.
4. Air | L(4000 nm, half-quarter) | HR first window | L(6000 nm, quarter-quarter) | HR second window | L(9000 nm, half-quarter) | substrate.
5. Family 3 with descending HR order.
6. Family 4 with descending HR order.

L is the complete supplier YbF3 model, H is the deposited ZnS film model. Each initial physical thickness is fraction*lambda/(4*Re(sqrt((n+ik)^2-sin(45deg)^2))). These seed fractions and IR reference wavelengths are project conventions, not externally validated AR solutions. Full coherent complex-index calculations resolve their actual behavior; the seed phase formula alone makes no performance claim.

## Bounded scheduler and local stages

There are six nontransferable 200 s family slices, sequential single-process CPU execution with all math-library thread counts set to one. Optical search total is at most approximately 1200 s plus one in-flight kernel-call cancellation latency per expired slice. Setup, independent replay and reporting are measured separately. A family cannot consume another family's slice.

Each family has four nontransferable 50 s stages: shared architecture beta=64, shared architecture beta=256, all-layer beta=512, all-layer beta=2048. Every stage has L-BFGS-B maximum 40 iterations and maximum eight line-search steps. If it returns early, unused time is not reassigned. A time-sliced stage is honestly labelled incomplete; no claim is made that its continuation stages converged.

Architecture coordinates share one HR multiplier for each HR center and material, giving ten HR variables, plus independent IR layers. HR scale bounds are 0.65–1.45 relative to the cold seed; IR thickness bounds are 5 nm to 2.5 times cold thickness. All-layer stages recenter a finite +/- half-quarter-wave trust interval at the best complete candidate, using 550 nm HR phase scales and 6000 nm IR phase scales, clipped to the 5 nm minimum. A cancelled partial candidate never replaces a complete candidate.

## Search guide and unchanged acceptance

For each original sampled condition, signed violation v is 0.99-R for HR or R-0.03 for AR. The guide is log(sum_i mean_j exp(beta*v_ij)/4)/beta, with an analytic chain-rule thickness derivative from the unchanged production helper. Equal window mass is a search-guide convention, not averaging acceptance. A numerically stable log-sum-exp implementation is used.

Every complete candidate is archived by the original maximum positive violation first, with equal-window positive hinge-square loss only as tie-break. Thus average improvement cannot replace a bad worst condition. Strict AR equality remains a failure, although the positive-gap archive metric is zero at equality.

## Independent verification

The final retained candidate from every family is replayed through a separately constructed normal production prepared evaluator. Its 95,992 training values must exactly match the direct kernel array reduction. Failure diagnostics then use 25 discrete angles every 0.5 degree at the same 1 nm wavelengths, with separate s/p outputs only as diagnostics. A candidate still failing this finite diagnostic is not sent through a huge passing audit.

Any apparent passing candidate requires the production 0.1 nm/shifted/extrema audit and an independent 25-angle check before an acceptance claim. Finite 25-angle testing is not continuous angular certification. No failed experiment establishes global infeasibility.

## Implementation boundary

Only experiment.py and replay.py in this research directory implement scheduling and vectorized reductions. Production code and all prior requests/results stay untouched. The optical recurrence, source interpolation, absorption treatment, polarization average and physical definitions are imported unchanged. The frozen JSON protocol and cold prescriptions have SHA256 identities; runtime/source hashes and actual stage logs are retained for handoff.
