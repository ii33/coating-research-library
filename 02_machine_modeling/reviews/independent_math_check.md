# T02 reference: narrow independent math/numerical check

Date: 2026-10-01 (UTC)  
Scope: independently inspected `models/deposition_reference.py` and `verification/run_verification.py`; no model or test files changed. This is a narrow worker review of the stated mathematical reference, not a designated-model review and not an experimental/physical-machine validation.

## Bottom line

The central ballistic transfer equation, its source/receiver incidence signs, angular normalization, the documented tilted-pose composition, disk quadrature measure, and conversion to normal thickness are internally consistent under the stated SI and incoming-facing-normal conventions. I found one low-severity edge case in the public `Source` input: a zero-mass source node coincident with a target raises even though that node contributes no source mass. I found no central-formula defect in this narrow review.

## Independent derivation and spot checks

For source-to-target unit direction `u`, range `R`, source outward normal `ns`, and receiver normal `n` pointing toward the incident hemisphere, the implementation uses `mu_s=max(u·ns,0)` and `mu_i=max(-u·n,0)`. Its directional mass-rate density is

`f_p=(p+1)/(2π) * mu_s^p` on the source hemisphere and zero on the back side.

Since `dΩ/dA=mu_i/R²`, each source node contributes `fraction * f_p * mu_i/R²` [m^-2] to mass capture per target area. The hemisphere integral is `(p+1)∫₀¹ μ^p dμ = 1` for `p≥0`. Thus `p=1` is Lambertian angular emission for fixed emitted mass rate; the receiver cosine is separate from the source angular law. `disk_source` fractions sum source-node mass rates (projected-area quadrature weights), rather than supplying radiance directly. With constant emitted mass per projected source area, those weights and the per-node cosine law give the corresponding constant-radiance Lambert disk; no extra source-area factor should be added to the kernel.

Independent computations made against the implementation:

- Oblique receiving-plane check: point source at the origin, target `(x,y,h)`, Lambert exponent `p=1`, receiver normal `(sin θ,0,-cos θ)`. Analytic kernel is `max(h cos θ - x sin θ,0) h / [π(h²+x²+y²)²]`. At `h=0.73 m`, `θ=0.29 rad`, and three on-/off-axis targets, maximum absolute difference was `1.67e-16 m^-2`; this independently checks both incidence signs and receiver cosine.
- Projected-area disk quadrature: `disk_source(a=.37 m, radial_order=10, azimuth_nodes=24)` returned total weight `1.0`, weighted `E[r²]=0.06844999999999998 m²` versus uniform-disk analytic `a²/2=0.06845 m²`, and weighted `(E[x],E[y])` within `1.8e-17 m` of zero.
- Extended disk on-axis limit: for a uniform Lambert disk of radius `a`, height `h`, and fixed total emitted rate, each area element contributes `dK = (dA/(πa²)) h²/[π(h²+r²)²]`. Radial integration gives `K=(1/a²)∫₀ᵃ 2r h²/[π(h²+r²)²]dr = 1/[π(h²+a²)]`, matching the verification's formula. This is a finite-source area integral, not a point-source inverse-square result evaluated at the disk center.
- Tilted kinematics: independently constructed scalar `Rz(phi) @ Ry(tilt) @ Rz(alpha) @ local_point + carrier_center` using hand-written rotation matrices for the documented phase equations; two nonzero-time positions agreed with `PlanetaryPose.evaluate` within `7e-17 m`.
- Finite mask geometry: after transforming segment endpoints to mask-local coordinates, a zero-thickness mask blocks only for the interior segment parameter `λ=-a_w/(b_w-a_w)` when it crosses the plane inside the finite u/v rectangle. A finite-thickness rectangular solid instead clips the segment's λ interval against all three local slabs, so side entry can block even when the mid-plane intersection misses the rectangle. This matches the code's plane-hit and slab-clipping branches. In the verification's `(-.4,0,0)→(.6,0,1)` ray, a zero-thickness `|x|≤.05` mask at `z=.5` is missed because `x=.1` there, while the .2 m-thick box reaches from `z=.4` to `.6` and the ray intersects the box near its side at `z=.4` to `.45`; this is a useful non-projected-clip distinction.
- Normal-thickness units: `transfer_kernel` is [m^-2]; integrating `kernel * (kg/s) * seconds` yields kg/m², and division by density [kg/m³] yields m along the local receiving normal. Receiver cosine correctly converts ray flow to area perpendicular to that local normal. Curved-surface area weights are a separate area-integration concern; the implemented spherical-graph Jacobian `R/sqrt(R²-r²)` and downward normal are geometrically consistent for the documented `z=R-sqrt(R²-r²)` graph.

The saved synthetic verification artifact was already present and reports 33/33 checks passing (`verification/verification_results.json`, model SHA-256 `06b8ac82901f88176c1c0252de820141f4ab59d71210c130ced8502c038b3619`). Its hemisphere, parallel-plane, capture, extended-disk on-axis, mask, pose closure, SI rate/density, and spherical-cap checks are consistent with the derivation above. That report explicitly covers synthetic analytical/code verification only, not physical-machine data. This review did not infer engineering accuracy or endorse a phase gate.

## Finding

**Low severity — zero-fraction coincident source node is rejected unnecessarily.** `Source` explicitly accepts nonnegative fractions, including zero. `transfer_kernel` checks `r²<=0` over *all* source nodes before applying fractions. Therefore a zero-emission node at the target raises, although its mass-rate contribution is mathematically zero and the other nodes produce a finite answer.

Exact reproducer:

```python
mixed = Source([[0, 0, 1], [0, 0, 0]],
               [[0, 0, -1], [0, 0, 1]], [1.0, 0.0])
transfer_kernel([[0, 0, 0]], [[0, 0, 1]], mixed)
# ValueError: Target coincides with source node

reduced = Source([[0, 0, 1]], [[0, 0, -1]], [1.0])
transfer_kernel([[0, 0, 0]], [[0, 0, 1]], reduced)
# array([0.31830989])  # 1/π m^-2
```

The same target/source configuration with only the positive-weight node gives `1/π m^-2`. Suggested repair if zero-weight nodes are meant to remain valid API inputs: omit zero-weight nodes from the singularity check and safely zero their kernel contributions before summation (or compact zero-weight nodes at construction). If zero-weight nodes are intentionally unsupported in coincident geometry, document that narrower restriction. The normal disk quadrature generates strictly positive weights, so this does not affect the shipped `disk_source` default path.

## Disposition

No blocker to the central mathematical reference was found within this narrow scope. The noted zero-weight-node edge case was corrected and checked below; analytical verification, later numerical convergence, and real-machine calibration/validation remain distinct evidence categories.

## Closure after zero-weight-node fix

Rechecked the prior exact reproducer against the updated model: the mixed source `[1.0, 0.0]` now returns `[0.31830989] m^-2`, equal to the reduced source `[1.0]`, rather than raising. Reran `verification/run_verification.py`: all 34/34 checks pass, including `zero_weight_source_node_ignored`. The recorded model SHA-256 matches the current file: `26a022105b0a0147e8c651bbc014d380afe45a403e6c8adf7e812b1a611e91bb`. This closes the single low-severity finding above; no expanded review was performed.
