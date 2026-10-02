# Independent narrow check: shadow integral math

Status: **independent_narrow_check_complete_not_certified**. This is a narrow check of the frozen synthetic D case only. It does not rerun the main quadrature, does not validate device-scale execution, and is not physical or interval certification.

This records the actual Luna narrow mathematical check; it does not replace a Seed or Sol sign-off.

## Projection and geometric mask

The two emitted source planes and their corresponding thick boxes satisfy `0 < dv < dX` at every box vertex: the vapor geometry has `dX=0.6 m`, `dv∈[0.19,0.21] m`; for the ion geometry, `dX∈[0.5584,1.1536] m` and `dv∈[0.155,0.269] m`. With positive projective denominators, the image of each convex box is exactly the convex hull of its projected vertices. This supports the eight-corner convex-hull construction, not just a thin-plate approximation.

An independent hull and ray classification were compared with `frozen/robust_mask_v02.py` on 256 non-boundary rays (within its batch limit): vapor 0 mismatches/128, ion 0 mismatches/128. These samples check implementation consistency, not exhaustive proof.

## Analytic y antiderivative

For 63808 smooth Gauss nodes (32-point Gauss-Legendre, at most 200,000), using independently constructed projected hulls and vertical cross-sections:

- exponent 1: max absolute difference 8.88e-16, max relative 7e-15
- exponent 12: max absolute difference 2.93e-14, max relative 1.89e-13

Both formulas agree with independent smooth quadrature on these finite samples. This does not bound outer x/time quadrature error.

## Cross-source plates and duration event

The ignored plate has an all-time coordinate separation for each source, including finite source-disk extents. Vapor rays at the ion-plate z slab have x ≥ 0.062 m, while the ion plate ends at x=-0.370 m. Ion rays at the vapor-plate z slab have x ≤ -0.220 m, while the vapor plate begins at x=0.175 m. Thus omitting the *other* source's plate is supported for these frozen bounded geometries. Separately, the ion disk contains the interior point `u=-0.044 m, v=0` whose rays remain x≤-0.503 m at the ion plate, below its x-minimum -0.490 m. An open neighborhood is also clear, so ion flux is positive for every time.

For diagnostic point #2, an independent direct projection, convex hull, point-to-edge distance, and bisection locate vapor full-cover roots at 3.971115124 s and 4.034107212 s, a 62.992 ms cover interval. Adding the 1.300 s vapor gate-off time gives 1.362992088 s. The open ion-source patch above establishes positive ion transmission throughout. Root sign checks at ±2 μs are {'left_before_m': -2.290518854239365e-07, 'left_after_m': 2.2904943756951734e-07, 'right_before_m': 9.10155019476222e-08, 'right_after_m': -9.101394499166915e-08}; this independently supports the changed duration magnitude versus frozen discrete estimates, but remains a binary64 event-root estimate, not a certified endpoint.

## Lipschitz and floating point

The global target speed bound is 0.898495 m/s. A projection-derivative bound gives vapor vertex speed ≤0.483805 m/s, below the configured 0.5 m/s. For ion, `dX-dv ≥0.2894 m`; a conservative derivative bound gives projected vertex speed ≤3.199 m/s, below the configured 6 m/s. Since a hull cannot move faster in Hausdorff distance than its corresponding vertices, and signed distance is 1-Lipschitz in that distance, both slopes are conservative under the stated geometry.

The `1e-11 m` floating guard in `support_intervals` is **not validated as a floating-point error bound**. Therefore support intervals and duration remain conditional numerical enclosures, not strict certified bounds. No change to main code is indicated by this narrow check.
