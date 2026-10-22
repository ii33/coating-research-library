# Four-window IR structure comparison (2026-10-22)

## Finding

This was a bounded comparison of six cold-generated IR/HR layer architectures on the unchanged single-front-surface ZnS-substrate target. All six candidates fail the four-window requirements. The best new structure, a 51-layer ascending HR stack with an IR-scaled low-index end cap, has a 6.859606 percentage-point worst gap in the independent finite replay. It improves over the equal-budget HR-only control (9.105304 pp, a 24.664% gap reduction), but does not beat the earlier 300 s supplier candidate (6.300788 pp). These are failure diagnostics, not an acceptance result or proof of infeasibility.

The acceptance target is unpolarized R ≥ 99% at 580–920 nm and 1044–1084 nm, and strictly R < 3% at 3–5 μm and 7–12 μm, at 39–51° incidence. Search scoring used the original inclusive 1 nm wavelength grid and integer angles; separate final replays sampled 25 angles from 39° to 51° at 0.5° increments and 1 nm. That finite replay is not a continuous-angle, sub-nanometer or shifted-extrema certificate.

Six nontransferable 200 s search slices consumed 1200.464703 s total; six-family solver stages did not return convergence. Independent final-candidate replays were separately timed at 89.781334 s. The experiment used a 64-layer exploratory ceiling, not a user-specified manufacturing limit. No production code was changed.

## Model and interpretation caveats

The selected branch uses the complete supplier Merck YbF3 n/k pair with author-export deposited ZnS film data and bulk Querry ZnS substrate data. The source-level diagnosis corrects the frozen protocol's overly broad “more absorptive” rationale: supplier YbF3 is strongly dispersive, and neither source branch is uniformly more absorbing throughout the IR windows. Exported zero-k values remain model values, not measured zero-absorption bounds. The finite-stack/polarization and source-model limitations, plus the recommended next discriminating experiment, are detailed in `NEXT-GAP-DIAGNOSIS.md`.

## Files

- `REPORT.md`: outcomes, metrics, runtime and bounded interpretation.
- `NEXT-GAP-DIAGNOSIS.md`: source-level analysis and next experiment recommendation.
- `protocol.json`, `protocol-explained.md`, `families.json`: frozen protocol and exact cold starts.
- `prescriptions.json`, `comparison.json`, the six `*-result.json` files and six `*-replay.json` files: retained designs, aggregate results and finite failure diagnostics.
- `prior-evidence/`: selected material-source manifest, frozen requests and previous-candidate evidence used by this comparison.
- `SHA256SUMS.json`: SHA-256 hashes for every included payload except the checksum manifest itself.
- `README.txt`: source note preserved verbatim; this `README.md` is the publication index.

The source package’s `prior-evidence/source-identity.json` was intentionally omitted because it contains an extensive coating-sim source-file hash inventory. That inventory is neither published nor re-encoded here. The production commit identifier needed to identify the evaluator remains in `REPORT.md`. The original curated local file list is therefore not fully published.

Raw event/stdout/stderr logs, local scripts, ZIP archives, and private machine paths are also not included. Related source qualification and paired-retest results remain in their own existing research-library directories.
