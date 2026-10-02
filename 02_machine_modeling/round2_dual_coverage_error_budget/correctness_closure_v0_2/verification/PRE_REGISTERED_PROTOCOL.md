# T02 v0.2 correctness closure: bounded protocol

Recorded 2026-10-02 05:06 UTC, before implementation or numerical test runs.

## Scope and stop

Only the deterministic rectangle / finite rectangular-solid open-segment predicate is changed in a new standalone reference module. v0.1 code, result files, its source/time quadrature and root STATE remain untouched. No third-party original is read or copied. No T03 work, optimization, product work or device claim.

The old near-sidewall false-clear example must be reproduced with a small, attributed transcription of the relevant legacy predicate. The replacement has no nonzero direction cutoff. Algebra over the encoded binary64 input values is evaluated with Python standard-library Fraction, with a strict admitted numeric domain and bounded batch size; this is a reference correctness path, not a production vectorized replacement. It must not call its result exact physical geometry. Boundary uncertainty is separately represented as a supplied local-coordinate margin, with unknown never coerced to clear.

## Fixed numerical domain and conventions

- SI metres; point coordinates and centers: zero or absolute value in [2^-200, 2^80]
- Widths/heights and positive thickness: [2^-80, 2^80] m; zero thickness is an explicit ideal-plane convention
- Frame coefficients: zero or absolute value in [2^-200, 2]; proper-frame encoded Gram residual <= 1e-12. No silent orthogonalization. The represented inequalities, not an unrounded ideal rotation, define nominal geometry
- Local uncertainty margin: zero or [2^-200, 2^80] m. It must enclose endpoint-coordinate plus plane/boundary error; no automatic physical/calibration uncertainty is invented
- Open parameter interval 0 < lambda < 1; closed solid boundary contacts block. The ideal thin plane excludes exactly coplanar segments and endpoint-only contact, matching the legacy convention
- Out-of-domain or invalid inputs raise, and may not be cast to transparent
- Strict nominal classification requires exact agreement, no Boolean tolerance. Positive uncertainty may widen to unknown; its interval must enclose the nominal and checked perturbed results

## Fixed test set and acceptance

1. At least 20 deterministic cases: known sidewall miss, true parallel, below-cutoff crossings, interior/exterior, front/back, endpoint-only, edge/corner/face contact, thin coplanar and near-plane cases, degenerate segment
2. Known counterexample under powers-of-two scale factors 2^k, k=-40,-20,0,20,40, direction reversal, signed axis permutations with a proper frame, and translated coordinates where original encoded perturbations remain resolvable
3. 6,000 seeded ordinary rays plus 2,000 seeded adversarial sidewall/near-parallel/thin-plane rays. Independent exact-rational face-plane enumeration is the oracle, not a second slab implementation. Both nominal solid and thin semantics must agree on all samples
4. Positive-margin tests: input perturbation witness checks and conservative unknown / transmission-interval propagation. Pointwise supplied uncertainty is not a claim about integration, continuous extrema or physical calibration
5. Invalid-domain tests, anti-Boolean coercion, and package-only verification in a copied allowlisted tree without a ZIP or parent files

Hard stop: <= 40,000 predicate/oracle evaluations per main-suite run; <= 160,000 accumulated across correction reruns; <= 180 s per run. One independent focused review, separately <= 20,000 predicate/oracle evaluations and <= 180 s. Stop at the fixed tests or these caps; no source/time mesh increases and no random-seed search to improve a result. Failed checks remain failures. Re-running after a real code correction is allowed within the cumulative cap.

## Success does not upgrade earlier findings

The v0.1 best-source-family discrepancy around 0.203% and ion-only duration discrepancy around 14.3 ms remain the recorded results, including the unmet 10 ms condition. Passing this predicate closure does not convert empirical grid differences to error bounds, settle source/time integration, validate real machines, or qualify the full T02 forward model as a certified T03 oracle.
