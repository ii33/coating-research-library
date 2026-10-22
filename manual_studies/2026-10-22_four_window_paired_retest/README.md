# Four-window paired optimizer failure comparison (2026-10-22)

## Conclusion

Both bounded source-model optimizer runs failed the four-window acceptance targets. The 1051fd6 baseline timed out before starting a joint minimax trial (zero such trials in either branch); the 6883513 paired retest produced substantially better candidates and reductions in the training maximum-error score of 53.0% (author-export model) and 64.6% (supplier YbF3 model), but still failed all four windows. These are bounded research outcomes, not feasibility proofs, manufacturing acceptance, or an achieved coating design.

The branch-wise minima/maxima below are unpolarized reflectance from the finite 25-angle replay (39–51° inclusive, 0.5° spacing; 1 nm wavelength step). For the two HR windows, entries are minimum R; for the two AR windows, entries are maximum R. Window order is HR 580–920 nm, HR 1044–1084 nm, AR 3–5 µm, AR 7–12 µm. Acceptance is HR R ≥ 99% and strict AR R < 3%.

| Model branch | Run | Layers | Thickness (nm) | HR1 min R | HR2 min R | AR1 max R | AR2 max R | Result |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Author-export | Baseline | 28 | 3566.172 | 0.844504 | 0.918210 | 0.182571 | 0.153766 | All four fail |
| Author-export | Retest | 46 | 5590.405 | 0.918347 | 0.956343 | 0.094912 | 0.097853 | All four fail |
| Supplier YbF3 | Baseline | 28 | 3476.164 | 0.811836 | 0.894000 | 0.180524 | 0.158291 | All four fail |
| Supplier YbF3 | Retest | 50 | 5875.141 | 0.926992 | 0.941173 | 0.069239 | 0.078703 | All four fail |

## Protocol and qualification boundary

- One coated face, ZnS substrate (grade unspecified), incidence 39–51°. HR 580–920 nm and 1044–1084 nm at unpolarized R ≥ 0.99; strict AR 3–5 µm and 7–12 µm at unpolarized R < 0.03. No separate s/p acceptance minimum was added.
- Same frozen request payloads in both runs (SHA-256 recorded in `protocol/manifest.json` and exact files in `inputs/`). Exploratory limits were 300 seconds, 6000 logical evaluations and 64 layers; 1 nm training grid at integer angles 39–51°. No silent material extrapolation; unknown k was not set to zero. These are research budgets, not manufacturing constraints or a proof of infeasibility.
- The baseline proposal sweep enumerated 234 classic-reflector structures per branch before the multispectral stage. The paired retest changed schedule/algorithm execution under the same requests: it started 52 author-export and 50 supplier-YbF3 complete joint-minimax trials, but still hit the time limit. Exact counts, stages and further diagnostics are preserved in the JSON/JSONL files.
- The 25-angle, 1 nm replay is a finite failure diagnostic, not a production certificate. Full acceptance still requires dense/offset/extremum checks and any specified production tolerance/validation procedure. No returned candidate had a complete production audit. Do not infer infeasibility from these bounded timeouts.
- The source branches and material tables are documented in the [four-window material source qualification package](../2026-10-22_four_window_material_qualification/qualification_report.md). Original Amotchkina exported zero values remain source-model numbers, not measured absorption bounds; blank conservative masked-k cells in the derived CSV are our qualification masking, not missing values in the original numerical export. Source-model algorithm validation is separate from actual-process qualification.

## Reproducibility and contents

- `protocol/manifest.json`: frozen material/protocol/request hashes.
- `inputs/`: the two exact frozen request JSON files, shared by both runs.
- `protocol/preflight-*.json` and `protocol/source-identity-*.json`: per-run dependency, material/input, commit and source-file hash evidence. One absolute local interpreter path is omitted; hash values are unchanged.
- `paired-comparison.json`: exact paired run comparison, time limits, grid, per-window values, and failure/audit classification.
- `baseline/` and `retest/`: candidate layer designs and numerical scores, analysis records and bounded replays. Candidate results are a projection of the original candidate output; numeric scientific values and design stacks are copied unchanged. Process command/cwd records, local filesystem paths, raw event/progress logs and raw checkpoint artifacts are excluded.

The material CSVs referenced by their SHA-256 checksums are preserved in the linked qualification package. No raw/copyrighted source PDFs, giant raw checkpoints, or private local paths are included here.
