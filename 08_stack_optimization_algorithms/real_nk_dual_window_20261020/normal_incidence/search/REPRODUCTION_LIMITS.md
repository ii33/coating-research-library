# Search reproduction boundary

The archived final prescriptions and spectra can be independently checked with
`python scripts/verify_prescriptions.py`. That script imports no `coat_sim` code.

The completed A/B structure search used the unpublished frozen v3 core for power,
analytic thickness derivatives and synthesis audit. Its original driver and the
production core are not bundled. The hashes, settings, actual seven-layer start,
empty-stack origin, events and every audited improvement identify the completed
research; they do not make the full search independently executable without v3.

Route A retained five distinct material-order branches and refined up to thirty
new orders per growth depth. Finite births used3500/9500nm reference wavelengths,
quarter-wave fractions0.25/0.75/1.5; it reached the goal at growth depth10.
Route B started from the supplied seven-layer recipe. It used paired insertions,
material/order changes and thickness perturbations; it reached the goal on the
157th grouped structure trial. The local solver was SLSQP epigraph minimax, with
frozen analytic derivatives, not the product's original SSE acceptance rule.
Both used81 training points/window; every effective improvement was independently
audited with dense/shifted/source-knot/local-extremum samples. Thin layers at or
below0.101nm were removed and the resulting physical structure rescored; this was
a research numerical convention, not a manufacturing minimum thickness.

Two initial preparation attempts failed before searching and were not included in
successful-run counters: dataclass serialization failure, plus premature relocation
of an active A output directory. Raw local failure evidence stays outside this
minimal shared package; its original artifact hashes are retained as provenance.
All successful search and verification sessions terminated normally.
