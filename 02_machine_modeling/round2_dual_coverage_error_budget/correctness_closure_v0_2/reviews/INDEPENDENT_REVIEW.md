# Independent bounded review of the v0.2 mask predicate

## Result

**Initial review: FAIL on two public-API validation defects; no geometric or numerical counterexample found in the bounded checks.** This is a reference implementation review for the represented input coefficients. It does not certify physical geometry, production performance, source/time integration, continuous extrema, or the full forward model.

Reviewed only `models/robust_mask.py` and `verification/PRE_REGISTERED_PROTOCOL.md`. No prior implementation, other report, copyrighted original, or source/time grid was read. Only the three permitted `reviews/` artifacts were created. The two defects below were reported to the parent immediately after the run; the reviewer did not change the implementation.

## Findings that require correction

### R1: malformed public `HitResult` can silently become transparent

`HitResult` is a public dataclass without runtime validation. `combine_masks` verifies the outer instance type, then checks enum members with `is`. Therefore all these inputs are accepted and their opaque union becomes `CLEAR`:

- `HitResult('blocked', 'public_constructor')`
- `HitResult('unknown', 'public_constructor')`
- `HitResult('nonsense', 'public_constructor')`
- `HitResult(None, 'public_constructor')`

For the first two, the string-valued enum also makes `transmission_interval` work by dictionary equality, while union classification uses identity. This inconsistent behavior is an especially plausible trap after serialization. The minimal reproduction is `combine_masks([HitResult('unknown', 'x')]).verdict`, which returns `Verdict.CLEAR` on the audited version.

This is an API contract failure, not a counterexample to the geometry returned by `RectangleMask.classify`: classifier-produced values use actual enum members and passed the complete finite union truth table. It nevertheless violates the intended failure-safe propagation boundary when public results are constructed or decoded. Recommended correction: reject non-`Verdict` values at construction, or deliberately normalize recognized strings and reject everything else; keep the chosen policy consistent across all consumers. Strict rejection is simplest.

### R2: an empty batch skips margin validation

`classify_many([], local_margin_m=-1)` returns `()` instead of rejecting the negative margin. The same structural issue applies to other invalid margin values because validation happens only inside the element loop. It does not misclassify a ray in an empty batch, but it violates the protocol's unconditional invalid-domain rejection contract. Validate the shared margin before the loop, including for an empty sequence.

## Independent method and bounded evidence

Run: `python reviews/independent_review.py` from this package directory. Fixed seed: `2718281828`. One initial run, 1.471 seconds, well below the 180-second limit.

- 3,299 admitted predicate evaluations and 8,099 independent oracle evaluations, total **11,398**
- 801 aggregate enclosure checks, 10,138 assertions, 22 invalid-input checks
- Five failed assertions, all belonging to R1 (four invalid representations) and R2 (one empty-batch margin)
- The invalid-input checks that stop before geometric classification are not counted as admitted predicate evaluations; including all attempted calls still leaves ample margin below 20,000
- 51 explicit boundary/convention cases
- 244 power-of-two scale, all 24 proper signed-axis frame permutations, reversal and encoded-translation cases
- 1,800 ordinary fixed-seed cases, including 500 ideal thin masks and rounded proper rotations
- 800 fixed-seed adjacent-representable sidewall/near-parallel cases, including 200 thin masks
- Four numerical-domain extreme cases
- 400 positive-margin cases, with 4,800 independently selected endpoint/boundary perturbation witnesses
- Margin verdicts: 103 blocked, 215 clear, 82 unknown

The independent oracle is **world-coordinate halfspace boundary-parameter enumeration**, not slab clipping. It constructs exact rational affine plane coefficients directly in laboratory coordinates, evaluates all face parameters strictly inside `(0,1)`, and also evaluates the midpoint. For a nonempty intersection with a closed convex solid, either a feasible interval boundary is at an interior face parameter, or the segment remains inside and the midpoint is feasible. Endpoint-only intersections are excluded. The thin reference separately solves its unique plane crossing and explicitly excludes coplanar/parallel rays. This is algebraically independent of the implementation's running enter/leave interval, but both intentionally use `Fraction` to define the same stored-input model. It is not an independently calibrated physical reference.

Translations are checked against the newly encoded world coordinates rather than assumed to preserve a sub-ulp perturbation; large translations can erase that perturbation at input encoding. The fixed old-sidewall example is blocked at all tested scales, reversals and proper signed-axis permutations.

## Mathematical assessment and applicability boundary

### Open parameter segment, closed solid, zero thickness

The solid predicate correctly tests intersection of `{a+t(b-a): 0<t<1}` with the closed box. `enter <= leave` retains a one-point interior edge/corner tangent; `leave > 0` and `enter < 1` discard contact only at an endpoint. Exact zero direction components are handled without a nonzero parallel cutoff. A degenerate source-equals-target ray is blocked in or on a finite solid because the protocol specifies an open *parameter* interval, whose constant image still contains that point. This is a convention, not an assertion that every definition of an “open degenerate geometric segment” is nonempty.

For zero thickness, exact coplanarity is transparent even for a point or path lying within the rectangle. A nonparallel plane crossing is blocked only at an interior parameter and within the closed rectangle. Hence the zero-thickness branch is deliberately discontinuous from the positive-thickness limit for coplanar rays. It agrees with the explicit protocol, and should not be sold as a universal thin-sheet contact rule.

### Fraction inputs and numeric range

`Fraction(float)` retains the exact rational value of the binary64 number supplied, not the intended decimal measurement or an ideal rotation. Integer inputs are also represented exactly. Coordinate subtraction, dot products and parameter division are then rational operations without intermediate floating cancellation or overflow. The tiny nonzero direction in the reported sidewall counterexample remains nonzero.

The accepted ranges are materially narrower than all finite binary64 values: nonzero coordinates/frame entries/margins/contributions below `2^-200` are rejected, coordinates/sizes/contributions over `2^80` are rejected, and positive widths/heights/thickness below `2^-80` are rejected. Zero thickness is special; positive thickness is halved rationally. The frame Gram check is itself exact for the supplied coefficients, with the encoded binary64 value of `1e-12` as its threshold. The frame is not repaired. Near-orthogonal coefficients still define the six nominal halfspaces, not an exactly rigid Euclidean box in some unrounded ideal frame. Proper handedness and the near-identity Gram check preclude the singular/reflected frames tested.

Intermediate local values are not independently rejected for exceeding an input limit: these are bounds on inputs, and `Fraction` safely carries derived values. The strict input magnitudes and bounded 4,096-element batch constrain this reference path but do not establish a production throughput target. The sum bound is at most `4096 * 2^80 = 2^92`, safely within finite binary64; its smallest admitted positive contribution is far above binary64 underflow.

### Supplied margin: sufficient enclosure, not an estimator

Under the required coordinatewise assumption, the logic is sound. Let each actual local endpoint differ from its nominal endpoint by at most `e_p,j`, and each actual halfspace boundary differ by at most `e_h,j`, with `e_p,j + e_h,j <= m`. At every fixed segment parameter, the endpoint interpolation error is bounded by `e_p,j` because interpolation is convex. Therefore:

1. If an actual point lies inside the actual solid, its nominal point lies inside every nominal halfspace expanded by `m`. No nominal hit in the expanded closed solid certifies clear
2. If a nominal interior-parameter point lies in every halfspace eroded by `m`, the corresponding actual point remains inside the actual solid. The eroded witness certifies blocked

Equality is safe because the solid boundary is closed. A zero eroded extent is allowed and can still be a valid closed-set witness. If an extent becomes negative, no blocked certificate is issued. Any remaining case is unknown. This proof covers joint endpoint/halfspace errors only when the user's scalar margin actually bounds their sum in the encoded local coordinates. It is **not** enough to bound endpoint error and boundary error separately by the entire margin, which could require twice that budget. Changes of frame/center must also be converted into the stated endpoint-local/plane-error budget; the implementation does not estimate them.

For a thin mask and positive margin, the implementation intentionally never certifies blocked; it can certify clear outside the expanded 3-D set and otherwise returns unknown. This is conservative and potentially very loose, including robust through-crossings. The 4,800 witnesses are finite supporting evidence; the set-inclusion argument supplies the general justification under the stated model. The witness tests used exact dyadic error budgets, spending half the margin on endpoint perturbation and half on boundary/plane displacement, to avoid accidentally testing a rounded perturbation outside the assumed set.

### Three-state propagation and outward float outputs

For actual enum-valued results, all union combinations of lengths 0 through 4 passed: a certain blocker dominates, unknown dominates otherwise, and an empty union is clear. Boolean coercion of an unknown result raises. The explicit conservative block choice is appropriate only for a lower bound on a nonnegative transmitted sum, not for arbitrary signed metrics or nonlinear quantities. R1 is the remaining public-construction failure in this chain.

The aggregate sums admitted contributions exactly as rationals. A single `nextafter` step corrects a nearest binary64 output only when it lies on the wrong side of the exact endpoint. The tests verified both enclosure and tight directed rounding over mixed scales, empty sums, all three states, and the maximum 4,096-element sum. This encloses the stated finite nonnegative weighted sum's visibility uncertainty. It does not enclose errors in the weights, source/time quadrature, calibration, model form, continuous extrema or downstream nonlinear metrics.

## Initial audited file hashes

- `models/robust_mask.py`: `d94aea185190f2339ee175335442216f0c65b9ff749d12f71c03787627c09f33`
- `verification/PRE_REGISTERED_PROTOCOL.md`: `5f6282d8558e6f1f8e7f7148bca33242fa520a709db55d641f7eb599ba240925`
- `reviews/independent_review.py`: `4b2fa709df0d1583fda8f01980307db36accd58bdc6679f5cd47651322fb6adc`

The machine-readable initial result preserves the failures and these hashes in `reviews/independent_results.json`. Any authorized targeted review after a real correction should be recorded separately without erasing the initial failed run.

## Final targeted correction review — 2026-10-02

**PASS: both initial API defects are resolved in the final reviewed version.** The original failed run, its five failed assertions, and original hashes remain preserved above and in the machine-readable result.

The reviewer read the changed implementation and verified by SHA256 reconstruction that deleting exactly the added `HitResult.__post_init__` validation block and the added eager batch-margin validation block reproduces the original audited source. No geometry, margin certificate, sum or rounding algorithm changed.

The finite targeted recheck passed all 185 assertions: seven malformed verdicts are rejected; three proper enum instances and intervals are preserved; all 121 union state combinations through length four work; all three Boolean coercions raise; ten invalid margins are rejected for an empty batch; four valid empty margins return an empty tuple; three nonempty margin settings match individual classification; an oversized batch is rejected; and 27 state combinations retain exact nonnegative-sum enclosure.

Additional geometric predicate calls: 24; additional oracle calls: 0. Total initial plus targeted predicate/oracle evaluations: 11422. Targeted elapsed time: 0.020820 seconds. No second random-suite run was performed. The targeted check covers ordinary public construction and API use; it does not claim protection against deliberate Python object mutation bypassing a frozen dataclass.

Final `models/robust_mask.py` SHA256: `2c6006636c2728d226fafcb854d5ef45a96ddbbcc3e4e57cc90f31f52c17464c`

Protocol and independent review script remain byte-identical to their initial recorded hashes. Final applicability limits and the distinction between represented-geometry arithmetic and physical/integration certification are unchanged.
