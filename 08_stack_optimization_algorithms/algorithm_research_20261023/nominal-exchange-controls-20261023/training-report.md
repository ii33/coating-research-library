# Fixed-budget nominal constraint exchange: completed training comparison

Date: 2026-10-23. This is a bounded optical research experiment, not a production-software release. The subsequent fixed-candidate validation is now complete and is reported separately in [validation-report.md](validation-report.md).

Formal optical core: fa9878336a597dc6df1db5b584bda3be4423cbca. Ten small physical/logic/outer-budget tests passed. Both experiments completed their five rounds and 100-cloud budgets, without claiming convergence. The fixed numerical and scientific inputs passed the recorded consistency checks; source-file inventories are not published here. The first 20 complete clouds were bit-for-bit identical between groups.

## Usable, exact-full-nominal-passing candidates

- Baseline training worst: 0.0040641672536294235.
- Exchange: 0.00070361844379063232, retained at cloud 88; all original 184600 nominal points pass strictly. Candidate digest: f0ae421704a5739c79be0211d15d222f6a82a642d0a967b936ac27962febaaf7.
- Fixed-760 control: 0.0010706379975689018, retained at cloud 13; all original 184600 nominal points pass strictly. Candidate digest: 5ffcb1ecb9b82bafff29ee1f6d5e49e5393231bdd3813a09d7f9fe0c4819961f.
- Exchange's usable training worst is 34.280% lower than the control's, and 82.687% below the original baseline. This is the fixed 32×600 finite-scene training loss, not manufacturing yield.

Two forward-only independent replays of the saved usable designs exactly reproduced all saved window minima/maxima and strict full nominal passes. They consumed 450 additional nominal forward chunks and no training clouds; these are separate from optimization budgets.

## Raw trials are not usable candidates

- Exchange's final raw worst: 0.00067692446465188183; 4 original nominal points fail, maximum signed violation 1.6176940769233039e-07. Rejected.
- Control's final raw worst: 0.00066977327367881423; 109 original nominal points fail, maximum signed violation 8.7209890619652231e-05. Rejected.

The control raw number is slightly lower, but comparison of rejected raw states is not a usable-design result.

## Work and observed costs

- Exchange: 100 complete clouds, 96783 forward calls, 74283 Jacobian calls, 1694.20 s. Nominal work set grew 760→782→782→842→842→846. The last four additions were recorded after the final budget and were not re-solved; the largest actually solved nominal work set was 842.
- Control: 100 complete clouds, 96500 forward calls, 74000 Jacobian calls, 1576.67 s. Nominal work set remained 760.
- Both: 66000 original training forward calls and 22500 full-nominal scan chunks. Actual total cost is reported, without a speedup claim under shared-resource contention.
- Conservative resource preflight: 213075112 bytes, below unchanged 268435456-byte gate. This is a resource estimate, not a measured process peak.

## Training scope and separate subsequent validation

Only one training seed, one assumed bounded ±0.5% independent relative-error model and the original ±1% local nominal thickness domain have been tested. No new holdout was read in choosing candidates. Full unperturbed 1 nm sampled feasibility does not prove continuous-domain or real-process feasibility. Subsequent fixed dense diagnostics and a new independent/common-mode holdout are complete. They are reported separately, without changing or selecting these candidates. In particular, the exchange candidate loses five common-mode passes versus control, despite lower tail severity; see [validation-report.md](validation-report.md).

See [training-summary.json](training-summary.json), [verification-summary.json](verification-summary.json), the two usable candidate files, and [README.md](README.md) for the compact method definition and publication scope. Complete requests, material payloads, scene coefficients, drivers and source/hash inventories are not included; this directory alone is not a complete replay package.
