# Four-window paired acceptance evidence

Exact retest source: 68835133025ffc1e74df2fe00921e4961f691efb. Baseline: 1051fd612170c90a1d09939168f2444c3b0056b5.

## Decision

Both branches ended not_found / time_limit. All four original windows still fail. This is bounded source-model research, not an infeasibility proof or manufacturing qualification.

The requests are byte-identical to baseline: 300 s, 6000 logical evaluations, at most 64 layers, minimum 5 nm, no per-layer or total-thickness cap, no answer seed, 1 nm training and 13 angles 39–51 degrees. The audit, physical forward and minimax kernels are byte-identical; only scheduling changed.

The independent failure replay uses 25 discrete angles every 0.5 degree and 1 nm wavelengths. It reproduces all 95,992 original training values exactly for each returned candidate. It is not a dense/offset/extremum or continuous certificate. Because every candidate already fails, no large passing-certificate run was made. Separate s/p are diagnostics, not additional constraints.

## Source and request identity

- Author request SHA256: 4f9ce18e5ad34d3d20e223d55286d2c456a0c39c55bc7c0ee927e9bbde4f38c5.
- Supplier request SHA256: 573a8c616456fe28fd31979981f2270da6718819717d3de345bc6989111b26b6.
- Material source commit: 78fb88a9610ba2cdc3da26480dc70424b6cbf337. All four CSV SHA256 match the manifest.
- Author export zeros remain explicit model data, not measured no-absorption bounds. Supplier YbF3 uses its complete independent n/k pair. Querry bulk ZnS is distinct from deposited films. No extrapolation or unknown-k-zero assumption was introduced.
- See preflight.json and source-identity.json for complete data and runtime hashes. The baseline evidence ZIP was independently rehashed and is unchanged.

## Author export

- Returned candidate: 46 layers, 5590.405461 nm; baseline 28 layers, 3566.171918 nm. Actual layer-count change: +18.
- Wall time: 303.689 s; logical evaluations: 56; failures: 0. CPU time: 303.641 s; peak RSS: 904508 KiB.
- First complete joint trial at 13.687 s after first freezing progress; 52 complete joint trial candidates. Stage-labeled joint-trial interval: 286.316 s. These are progress intervals, not a profiler attribution.
- Original training max violation: 0.1525706996 -> 0.0716534228, a 53.036% reduction. The result is still not a pass.
- Known completed training physical calls: 2860; known wavelength-angle points: 5279560. One cancelled callback leaves exact totals unknown. Audit work is zero. Cleanup completed; serial worker count 1 and IPC work 0.
- Candidate physical SHA256: 590f4c06411dee37eda8bc27e7b1b66e0e722bfce69b8a2749078538cc4d7659. No matching complete production audit and no audited checkpoint exists. The complete legal returned training candidate is retained, explicitly unaudited. The old bare-substrate checkpoint is a different candidate and is not reused.

| Window nm | Unpolarized R min–max % | Worst condition nm / deg | Remaining gap pp | Improvement vs baseline pp | s worst % | p worst % |
|---|---:|---|---:|---:|---:|---:|
| 580–920 | 91.834658–99.758020 | 588 / 51 | 7.165342 | 7.384244 | 95.045166 | 83.780107 |
| 1044–1084 | 95.634300–98.585971 | 1084 / 51 | 3.365700 | 3.813272 | 97.323885 | 92.168255 |
| 3000–5000 | 0.534506–9.491199 | 3000 / 39 | 6.491199 | 8.765871 | 14.207959 | 4.774439 |
| 7000–12000 | 2.856754–9.785301 | 7000 / 39 | 6.785301 | 5.591258 | 15.171134 | 4.459134 |

For HR, worst means minimum R; for AR, worst means maximum R. s/p extrema may occur at different conditions and must not be averaged to reconstruct unpolarized values. Positive improvement means HR increased or AR decreased. All gaps are to the original thresholds, not averages.

## Supplier YbF3

- Returned candidate: 50 layers, 5875.141111 nm; baseline 28 layers, 3476.163646 nm. Actual layer-count change: +22.
- Wall time: 303.467 s; logical evaluations: 54; failures: 0. CPU time: 303.472 s; peak RSS: 942256 KiB.
- First complete joint trial at 13.007 s after first freezing progress; 50 complete joint trial candidates. Stage-labeled joint-trial interval: 286.893 s. These are progress intervals, not a profiler attribution.
- Original training max violation: 0.1781636861 -> 0.0630078839, a 64.635% reduction. The result is still not a pass.
- Known completed training physical calls: 2756; known wavelength-angle points: 5087576. One cancelled callback leaves exact totals unknown. Audit work is zero. Cleanup completed; serial worker count 1 and IPC work 0.
- Candidate physical SHA256: 7a6a9b6c45af58d4f45e01d3b981471474a24c43c72ec6ba6e56f0a074442d6c. No matching complete production audit and no audited checkpoint exists. The complete legal returned training candidate is retained, explicitly unaudited. The old bare-substrate checkpoint is a different candidate and is not reused.

| Window nm | Unpolarized R min–max % | Worst condition nm / deg | Remaining gap pp | Improvement vs baseline pp | s worst % | p worst % |
|---|---:|---|---:|---:|---:|---:|
| 580–920 | 92.699212–99.325594 | 920 / 51 | 6.300788 | 11.515580 | 93.155515 | 85.716423 |
| 1044–1084 | 94.117266–98.325665 | 1044 / 39 | 4.882734 | 4.717240 | 93.578367 | 91.115425 |
| 3000–5000 | 1.312368–6.923914 | 3000 / 41 | 3.923914 | 11.128456 | 12.191211 | 3.206361 |
| 7000–12000 | 1.773778–7.870284 | 12000 / 51 | 4.870284 | 7.958833 | 13.703199 | 3.283663 |

For HR, worst means minimum R; for AR, worst means maximum R. s/p extrema may occur at different conditions and must not be averaged to reconstruct unpolarized values. Positive improvement means HR increased or AR decreased. All gaps are to the original thresholds, not averages.

## Most evidence-supported next comparison

Keep the joint optimizer and original acceptance unchanged, but compare a small, fairly scheduled set of structural families that includes explicit IR matching/connection layers and stack order, within the same 64-layer and parent resource bounds. Both retests screened only one source-derived HR topology, with no optional matching or connection layers, and spent the remainder inside its first refinement invocation. The logs therefore do not evaluate the remaining structural families or establish a local/global infeasibility claim.

IR diagnostics specifically show much larger s reflectance peaks than p peaks, especially in the supplier branch: s worst 12.1912% / 13.7032% versus p worst 3.2064% / 3.2837%. This supports investigating polarization-aware IR impedance matching, while still accepting only the user’s unpolarized R. HR p minima also remain lower than s minima. The evidence does not support merely raising layer count or wall time, or claiming that later optimizer continuation/epigraph stages are ineffective: the invocation had not returned before timeout.

## Bundle contents

- Exact frozen requests and original manifest.
- Full original returned CLI results in author_export-result.json.gz and supplier_ybf3-result.json.gz; decompression is verified against raw SHA256.
- Exact returned candidate prescriptions, result/identity summaries, complete raw progress logs, 25-angle and s/p failure diagnostics, paired comparison and source hashes.
- raw-artifact-index.json records absent audited checkpoints honestly and hashes all preserved raw results.
- Machine-local executable, working-directory and output paths are normalized in portable process metadata. No credentials, private user data or source code are included.
