# Four-window material-source qualification (2026-10-22)

Target: one coated face on ZnS, 39–51° AOI; HR 580–920 nm and 1044–1084 nm with ≥99% unpolarized reflectance; AR 3–5 µm and 7–12 µm with strict R<3%. No separate s/p minimum is specified.

This is an algorithm/source-model qualification package, not a measured n,k certification of the user's deposited films or a production qualification. Material identities and alternatives remain separated by film/substrate role and source/sample. Report s and p separately as well as the unpolarized response.

## Contents

- `qualification_report.md` — conclusions, limits, evidence and primary/source links.
- `source_catalog.json` — source/model metadata, intervals, cautions, and SHA-256 checksums.
- Seven CSV extracts — compact n/k screening data; no raw copyrighted PDFs are included.

## Critical interpretation

The Amotchkina numeric exports retain the authors' original exported k values, including exact zeros. Those zeros are source-model/export values, not measured absorption bounds. In the derived Amotchkina CSVs, blank `k_qualified_interval_only` cells are conservative qualification masking by this study; they do not mean the original author files lacked numeric data. Keep the original and qualification-masked columns distinct. Algorithm/model validation may proceed using labeled source-model branches; this cannot certify the actual process.

Merck YbF3, Amotchkina YbF3, and Mouchart ZnS are separate source-model scenarios, not values to average or mix. Bulk ZnS models are separate from deposited ZnS films. See the report and JSON catalog for source-specific intervals, provenance, uncertainties, unresolved material-threshold issues, and limitations.
