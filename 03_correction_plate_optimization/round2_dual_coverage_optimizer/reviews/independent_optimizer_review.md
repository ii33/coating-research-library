# T03 dual-coverage optimizer: independent counterexample review

Reviewer: GPT-6 Luna, narrow independent counterexample review. This is not the user-requested Seed/Sol formal sign-off.

Scope: read the current `models/intervals.py`, `contracts.py`, `geometry.py`, `oracle.py`, `optimizer.py`, plus the frozen mask predicate; add/run only small standard-library synthetic tests. No T02 reevaluation, no network/source downloads, no device run, and no push. The review does not establish a physical coating-performance certificate or continuous-space optimum.

## Result

The tested counterexamples pass on the current implementation. During review, three fail-closed issues were reproduced and the owner agent patched them; the corresponding regression cases now pass:

1. **Empty decision schema could be called resolved.** A one-candidate `Search` with an oracle returning empty objective and constraint dictionaries yielded `resolved_on_evaluated_candidates` and put the candidate in the certified archive. `validate_evaluation` now rejects an empty objective schema (an empty constraint dictionary remains an explicit unconstrained problem), and summary logic leaves a feasible candidate with estimated/unknown objectives unresolved and out of the archive.
2. **Out-of-range uncertainty point could be filtered away.** For one valid area point (ID 0), an unknown `N` error with `points=(1,)` passed bundle validation, was skipped by the point filter, and produced bounded objective/throughput fields. `RayBundle` now rejects invalid error point IDs and requires all seven error axes for every physical `N`/`D` point.
3. **Mutable input aliases could invalidate a validated bundle.** A caller-owned `points=[0]` list could be changed to `[1]` after construction; separately, clearing a caller-owned `errors` list after bundle validation removed an unknown `N` qualification. The result could then be marked bounded. Current dataclasses normalize tuple fields, the oracle deep-copies its bundle and checks its frozen digest on evaluation, and fixture data is guarded. Both alias regressions now pass.

Additional contract hardening observed and tested: a bounded measure cannot conceal an estimated/unknown attached error source; empty objectives are refused; comparisons reject unit/definition drift before feasibility shortcuts; and a lone feasible candidate with estimated objectives is unresolved, not archived.

## Independently tested counterexamples

The 15-test suite is `test_optimizer_counterexamples.py`. Run from this directory:

`python -m unittest -v test_optimizer_counterexamples.py`

Current result: **15 tests passed**. Cases cover unknown/estimated qualification, single-candidate estimated objectives, objective/constraint unit mismatch before feasibility dominance, overlapping noise intervals, denominator intervals crossing/touching zero, two-plate envelope overlap, disconnected support from `xmin`, invalid and mutable uncertainty locations, per-point physical error-axis coverage, geometry-unknown witness location and no double widening, geometric cache reuse versus changed rates and changed geometry, and cancel/checkpoint/resume budget retention. The model modules also passed `python -m py_compile` during this review.

The cache check confirms that changing rates preserves the pure geometry key while changing the weighted-data key and reusing visibility; changing design geometry produces a different geometry key and a cache miss. Review files live outside `models/`; current code hashing covers only runtime model files.

## Boundaries

The implementation remains an explicitly qualified finite-ray research adapter. Its quadrature, calibration, physics/model assumptions, and spatial/time witness coverage are caller supplied; the mask is a reference predicate, not a production geometry certification. The archive is only the set of evaluated, qualified feasible candidates not eliminated by certified interval dominance; overlapping interval survivors are not proven true Pareto members. The separate chunked-oracle/device-runner path was not independently re-audited here; its results remain subject to the project’s own validation plan.
