# Narrow optical and units check — T06 round 3

Scope: reviewed `models/exact_intervals.py`, `models/bounded_optics.py`, `data/case.json`, and the selected record in `data/legacy_selection.json`; compared five isolated points to the frozen round-2 vendor scalar Airy kernel. This is not the formal review chain or a physical/material certification.

## Findings

- No material units or optical-recursion bug found. The legacy order is explicitly substrate-to-incident; reversing its layer list produces incident-to-substrate order, aligned with the refractive-index and thickness arrays. Physical thickness is converted from nm to µm by dividing by 1000.
- The normal-incidence lossless Airy recursion is consistent with the scalar reference: it starts from the last film/substrate interface and applies `(r_j + r_tail exp(4π i n d/λ)) / (1 + r_j r_tail exp(4π i n d/λ))` while walking toward air. The phase matches the reference's squared one-way propagation factor. R is formed from complex amplitude magnitude squared; with real positive indices, no absorption, and a semi-infinite exit substrate, `T=1-R` is the stated flux-into-substrate complement.
- The interval path uses exact rational/Fraction arithmetic on encoded inputs, outward rounding to the 80-bit dyadic grid, an alternating-series enclosure for Machin π, Taylor polynomials with Lagrange remainder plus a Lipschitz radius allowance, and conservative complex rectangular intervals. The reviewed operations preserve enclosure; dependency overestimation may widen or fail closed when a denominator interval includes zero.
- The latent thickness mapping is shared: `z=h/h_ref` is one interval, and every film thickness is multiplied by the same `z` and the variant scalar. The paired-difference routine evaluates A and B on the same latent subcells, consistent with its same-run claim.

## Five isolated point comparisons

The table compares interval midpoints at baseline and two variant scales with the copied NumPy scalar recursion at individual wavelengths. The vendor kernel is floating-point reference evidence, not a certificate; the small differences are compatible with its binary64 rounding and are much larger than the tight point-enclosure widths.

| scale | wavelength (µm) | copied-kernel R | interval midpoint | midpoint − kernel | interval width |
|---:|---:|---:|---:|---:|---:|
| 1 | 4.25 | 0.010274678484132868 | 0.010274678484132793 | −7.63e−17 | 1.73e−18 |
| 1 | 4.26 | 0.011575601709474892 | 0.011575601709474859 | −3.30e−17 | 1.73e−18 |
| 1 | 4.27 | 0.012910002901725736 | 0.012910002901725693 | −4.16e−17 | 1.73e−18 |
| 1.25 | 4.26 | 0.18718469322819384 | 0.18718469322819424 | +4.16e−16 | 2.78e−17 |
| 1.002 | 4.26 | 0.010466814804679861 | 0.010466814804679887 | +2.60e−17 | 1.73e−18 |

The author-reported precision-test issue at a zero-reflectance point is an assertion tighter than the dyadic rounding floor (about 1.65e−24 versus 1e−35); that is a test threshold issue, not evidence of a numerical-code defect. No sweeps, Monte Carlo, device actions, or writes outside this package were performed.
