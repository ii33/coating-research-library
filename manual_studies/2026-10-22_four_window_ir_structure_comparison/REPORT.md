# Bounded IR matching structure experiment

## Result

All six newly cold-generated families fail the unchanged four-window requirements. This experiment improves the equal-budget HR-only control, but does not improve the earlier best supplier candidate. It is an explicit bounded negative, not a feasibility or manufacturing conclusion.

The best new structure is the 51-layer ascending HR stack with an IR-scaled low-index end cap. Independent 25-angle, 1 nm worst gap: 6.859606 percentage points; equal-budget HR-only control: 9.105304 pp, a 24.664% reduction. The prior 300 s supplier candidate remains better at 6.300788 pp. The new six-family protocol differs in solver/architecture and per-family time, so this is not a controlled regression test against the prior search.

## Unchanged physical and source scope

Single front coating, bulk Querry ZnS substrate; unpolarized HR >=99% at 580–920 and 1044–1084 nm, strictly R<3% at 3000–5000 and 7000–12000 nm; 39–51 degrees; original 1 nm inclusive wavelength grid. All search trials evaluate all 95,992 original wavelength-angle conditions. Minimum 5 nm; our declared exploratory ceiling is 64 layers, not a user-specified manufacturing limit. No user thickness caps were introduced. The selected first branch uses the complete supplier Merck YbF3 n/k pair and author-export deposited ZnS model. Author-export zeros are model values, not measured no-absorption bounds. Other source branch not searched in this experiment.

## Independent finite diagnostic

Each final candidate was replayed by a new normal production evaluator at 25 discrete angles 39–51 degrees every 0.5 degree, 1 nm wavelengths, unpolarized plus separate s/p diagnostics. Every final candidate exactly reproduces all 95,992 original training values, and direct kernel reduction agrees exactly with normal scoring. This is not a 0.1 nm/shift/extremum or continuous-angular certificate. All candidates fail, so no expensive passing audit was run. Separate s/p numbers are diagnostics, not new constraints.

| Cold family | Layers | HR 580–920 min R% | HR 1044–1084 min R% | AR 3–5 μm max R% | AR 7–12 μm max R% | Worst gap pp |
|---|---:|---:|---:|---:|---:|---:|
| cold_hr_ascending | 50 | 90.467119 | 90.378918 | 12.105304 | 11.755803 | 9.105304 |
| cold_ir_cap_ascending | 51 | 92.483074 | 92.308866 | 9.765307 | 9.859606 | 6.859606 |
| cold_ir_triad_ascending | 53 | 88.837698 | 88.972298 | 13.152993 | 4.637865 | 10.162302 |
| cold_ir_end_connection_ascending | 53 | 84.045461 | 83.528004 | 18.375686 | 18.503974 | 15.503974 |
| cold_ir_triad_descending | 53 | 84.258307 | 84.998676 | 16.941166 | 7.181890 | 14.741693 |
| cold_ir_end_connection_descending | 53 | 79.608483 | 83.887974 | 24.079114 | 24.000496 | 21.079114 |

For HR, worst means minimum R; for AR, maximum R. Worst-condition locations and all s/p extrema are in comparison.json and per-family replay files.

## Interpretation

The ascending triad improves its own long-wave AR maximum to 4.637865%, but HR minima 88.837698% / 88.972298% and short-wave AR maximum 13.152993% are much worse. It is not a passing broadband-AR design, and it is not an improvement to the full joint problem. End/connection and reversed-order prescriptions are worse under these bounded slices. This rejects only these concrete seeds and local search boxes, not the general existence of useful IR matching structures.

The new single-cap candidate retains large s-polarized IR peaks (17.173036% / 18.242962%), so this experiment has not resolved the polarization-impedance difficulty diagnosed earlier. s/p global extrema can occur at different conditions and must not be averaged to reconstruct unpolarized extrema.

The half-degree replay detects a visible-HR dip at 580 nm / 48.5 degrees in the ascending triad: 88.837698%, compared with its 13-angle training minimum 89.080199%. Its overall gap rises from 10.152993 pp to 10.162302 pp. The other five families' overall worst gaps are unchanged.

## Runtime and completed stages

Six nontransferable 200 s slices consumed 1200.464703 s total; 0.464703 s over the nominal 1200 s is cancellation-boundary latency. Independent final-candidate failure replays consumed 89.781334 s, separately timed. 342 complete joint trial candidates, 18,557 completed objective-angle kernel calls, and 33,704,197 completed wavelength-angle points were recorded; 22 cancelled partial trials are excluded from the archive.

All 24 planned stages were entered, but none returned solver convergence before its time slice. They are not described as completed/converged beta continuation. No epigraph stage was run. Every family received architecture beta 64, architecture beta 256, all-layer beta 512 and all-layer beta 2048 work. The original maximum per-condition violation, not average guide loss, selected complete candidates.

Runtime: Python 3.12.15; NumPy 2.5.4; SciPy 1.18.1. Serial CPU, all math thread counts 1. Analytic optical derivative finite-difference discrepancy at sampled verification points <=1.3e-11/nm; log-sum-exp chain-rule discrepancy <=2.05e-12. These are code diagnostics, not optical acceptance.

## Source-level next-gap diagnosis

The existing prior already has four visible-band centers and one narrow-band center. It includes the sampled worst 51-degree p admittance contrast in its width/pair proxies, but not a finite coherent coverage guarantee; layer phases are initialized at 45 degrees. Its cold seed uses five pairs per center versus a heuristic ten-pair demand. Those estimates are not physical lower bounds. See NEXT-GAP-DIAGNOSIS.md for exact source lines, material-model differences and a better finite-stack tiling/chirp plus IR-admittance matching comparison.

The frozen protocol phrase “more absorptive stress branch” is corrected: neither source branch is uniformly more absorbing across both IR windows. Supplier YbF3 is strongly dispersive, while author-export k is greater at 12 μm. The justified branch-selection reasons are the smaller prior worst gap and independent complete supplier n/k. Sources and frozen protocol remain unchanged.

## Minimal generic implementation recommendation

1. Make global structural-family scheduling fair before long refinement: reserve a bounded first quantum for each eligible end/connection/order family, then resume retained continuations. Preserve full-grid feasibility-first ranking and only audit physically passing candidates.
2. Add explicit IR phase-scaled matching candidates separately from visible-HR half-quarter end layers. Derive phase from captured complex source n/k and all original material domains. Keep family provenance, source hashes and declared search boxes in results.
3. Keep HR-center/material shared coordinates as an optional inexpensive architecture guide, followed by bounded all-layer stages. Do not elevate this experiment’s seed wavelengths, beta ladder, trust boxes or equal-window smooth-max into validated defaults.
4. Preserve cancellation-safe complete-candidate archives and report which stages actually returned. Add a controlled matching-vs-no-matching regression test at equal resources; no exact passing prescription is established here.

This is a research prescription, not a published software change. Production source is unchanged at 68835133025ffc1e74df2fe00921e4961f691efb; all 365 runtime hashes match and the checkout remains clean. Original source requests/results were preserved.

## Reuse and audit trail

protocol.json was frozen before search, SHA256 a49057eaf560be2c88ebec79dfb12ad83e6ab73cc17fa5dd90cf209f394b3d43. families.json contains the exact six cold seeds. prescriptions.json contains every final retained physical design and physical SHA256. Original full frozen requests and prior prescriptions/diagnostics remain in prior-evidence/. The original experimental scripts are retained verbatim and contain executor-local import/data constants; to rerun elsewhere, point those constants at an exact clean source checkout and the included prior-evidence directory. No production code is bundled or overwritten.
