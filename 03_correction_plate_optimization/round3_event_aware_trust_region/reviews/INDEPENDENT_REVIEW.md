# T03 round 3: narrow independent math/code check

**Conclusion:** No blocking defect was observed in this narrow check. This is not an informal Seed/Sol sign-off and does not establish that a wider model chain passes.

## Checked scope and source identity

Only the requested implementation/reference/test files were treated as the review scope:

- `models/trust_region.py` — SHA-256 `cde28a258e00fafe578bae7dbdf4443db6d7b8546e8bdb11cf03c9bbe3037373`
- `models/event_reference.py` — SHA-256 `c82ebcd1ee2820a8cae6c4cb5c921a96eaa2aedc6af5b76b52ed183a41a3b354`
- `verification/test_small.py` — SHA-256 `9a8fdde3edbf21f3a0bc3ef6d690a118336dbee3f9f831b3dc4d7dea3fcb999b`

The implementation identifies itself as `T03-r3-affine-trust-1`. The checks cover its encoded SI slab scene and finite discrete-source objective. They do not establish input-uncertainty or continuous-source certification, CAD/device behavior, or global optimization.

## Findings

1. **The affine topology guards are sufficient for the stated two-variable segment.** With the other scene data fixed, each target-plane projection of a slab edge is
   `x_{sign,z} = s + (plate_shift + sign * half_width - s) * H / z`.
   It is affine in `(plate_shift, half_width)`. Lower/upper active-face selection can change only when the corresponding near/far projected coordinates meet; `face_guard_m` keeps the selected branch strictly separated. On a fixed face, each event time is that affine coordinate transformed by fixed nonzero velocity and fixed clock/target offsets, so it is affine too. The event-to-endpoint guard has a fixed sign as long as its exact guarded margin stays positive; the adjacent event-order gaps are affine. Therefore their minima on the whole segment occur at one of its endpoints. The implementation computes those endpoint minima with exact `Fraction` values from the encoded binary-float inputs and accepts only when every exact lower margin is positive. Positive half-width, fixed transversality, and fixed positive angular cosines complete the stated topology conditions.

2. **Minimal active-face challenge case (one source node, one design coordinate).** For the default scene and source node `0`, moving only `plate_shift_m` from `0` to `0.09 m` moves the lower-edge projection from near/far `−0.2/−0.133333… m` to `0.025/0.016666… m`. They tie at `plate_shift_m = 0.08 m`, and the active lower face switches near-to-far. `certify_segment` rejects this segment on `face:0x0.0p+0:lower`; the reported exact minimum guard is negative. This is the smallest useful adversarial case for the necessity of the active-face guard. It is a challenge example that is safely rejected, not a defect in the current implementation.

3. **Minimal event-endpoint challenge case.** For the same single node, moving only `plate_shift_m` from `0` to `−0.07 m` retains the lower near face but moves that event past `t0`; at the candidate its event time is about `−0.0125 s` (`x_event = −0.375 m`, while target `x(t0) = −0.37 m`). The segment is rejected on `endpoint:0x0.0p+0:lower:z_near_m:t0`. Thus the endpoint condition catches a topology change not dependent on a face switch.

4. **Rational Darboux enclosure matches an independently coded exact-rational check.** The review script independently derives projected slab limits, exact event times, visible intervals, and panel bounds. On each panel, the source rate is affine and nonnegative, the ray offset is affine, and the positive kernel is `A q(t) H²/(H²+y(t)²)²`. Endpoint extrema bound the affine rate; endpoint extrema and any zero crossing bound `y²`. Combining minimum rate with maximum `y²` gives a lower kernel bound, and maximum rate with minimum `y²` gives an upper bound. Summing with nonnegative weights encloses the same encoded finite-node integral. The production interval endpoints matched the independent exact calculations after outward float rounding in all four checks: the default one-node case at 16 and 64 panels, reverse velocity at 32 panels, and a two-node weighted source at 32 panels. The frozen reference value estimate lay inside each enclosure, as did its mapped objective interval for target `1`.

5. **Unknown/overlapping outcomes do not authorize acceptance.** Equal objective intervals return `unresolved`; identical unknown-geometry contracts return `unresolved`; a positive predicted-reduction interval with overlapping actual outcomes remains `unresolved`. Predicted reduction intervals that are zero, negative or cross zero, unknown, or below the `1e-12` default floor return `reject` with a pathological-denominator reason. Different objective/source contracts are refused with `incompatible_objective_source_or_code_contract` rather than compared.

6. **A safe clipped example also remains guarded.** The default scene with the proposed shift direction `[0.2, 0]` clips to an encoded plate shift of about `0.064 m`; all exact guard minima are positive and `certify_segment` returns `encoded_affine_segment_certified` for that encoded segment.

## Reproduction

From the round root, run:

`PYTHONDONTWRITEBYTECODE=1 python reviews/independent_checks.py`

The command recreates `reviews/independent_results.json`, including the reviewed file hashes, exact-check details, counterexample guard IDs, and enclosure outputs. No production source was edited.

## Limits

`heuristic_limit` is explicitly only a first-order screen; its output is not the topology proof. The safety claim checked here comes from `certify_segment` and its exact affine guards. The reference point estimates are floating closed-primitive evaluations, not the enclosure proof. The proof applies to the declared finite discrete-source model and exact encoded inputs only.
