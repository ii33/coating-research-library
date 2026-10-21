# Minimal generic integration handoff

Baseline used read-only: `0a631b7428486ab08fe0f27aa8938c50783f5280`. Implement only on the then-current latest software; do not overwrite newer files from this research checkout. No software has been changed or published here. Keep old benchmarks frozen; add a separately named sourced-film/bulk-SiO2 case.

## What is and is not proved

The 32-layer cold-start experiment used a generic two-substack *parameterization*, but its research input centers were explicitly 440 and 625 nm, eight pairs each. These are not a production generator output and must not become hardcoded default answers. No optimized thickness vector was used as the initial seed. Full independent thickness refinement produced the passing prescription. Runtime from a fresh Python subprocess through source loading, prior construction, gradient check, optimization and independent audit was 7.15 s here (source downloads excluded; timing is not guaranteed elsewhere).

Current `film_synthesis_global.iter_reflector_proposals` already contains periodic, two-section and chirped QW families. Its two-section centers currently sit at the requested band endpoints; this exact research interior-center seed is not currently generated. Existing production local optimization supports analytic Jacobians but its squared range-violation objective is not the direct staged minimum-reflectance recipe below. A frozen successful answer-seed replay proves optical portability, not cold-start optimizer/generator capability.

## Generic prior API, no target-special casing

Inputs: wavelength bounds, requested angle/polarization set, incident medium, ordered candidate material pair, layer/thickness budget, optional user-selected architecture. Output: physical layer seed plus complete provenance.

Represent a two-substack prior by continuous centers `(c1,c2)`, pair allocation `(m1,m2)`, orientation HL/LH, wavelength direction, reference angle, and optional end/junction matching fractions. A chirped prior uses linear/geometric center interpolation instead. For every layer use

`d(label,c) = c / [4 Re sqrt((n(label,c)+i k(label,c))^2 - n0^2 sin(theta_ref)^2)]`.

Use the midpoint of requested angle extrema as an initial phase angle; rescore every requested angle/polarization. Here theta_ref=15 degrees. Do not replace complex-index phase with n*cos(theta) using an incorrectly shared refracted angle. Every layer and every matching layer counts against the budget.

For reusable automatic scheduling, derive interior-center search bounds from the requested band and the source-dependent QW stopband width, then tile/overlap local bands or optimize a small continuous normalized-center vector before full thickness matching. One *proposed, not yet independently cold-start validated* default is interior padding based on a fraction of the minimum local QW stopband width, with multiple ordered placements and log-band tilings. Keep this as a project search convention, not an engineering theorem. Do not simply install 440/625 nm or the final prescription as a hidden target lookup. A production acceptance test must start from a generated prior with no answer seed and demonstrate an audited pass under the declared wall/evaluation budget.

## Verified refinement recipe

All internal arrays are incident-to-substrate, wavelength and thickness nm, material convention n+ik. Train on 301 wavelengths from 400 through 700 nm, all four 0/30-degree s/p conditions. Duplicate normal-incidence polarizations are harmless; preserve the requested semantics.

1. Scale optimizer variables x=d/100 nm. Enforce 10<=d<=500 nm, sum(d)<=5000 nm, and <=32 layers. Keep an archive of the best *legal spectral minimum*, not the mean and not simply the final solver iterate.
2. Compute amplitudes by passive Fresnel recursion. For interface amplitude a, accumulated next-interface amplitude r, z=exp(4*pi*i*q*d/lambda): F=(a+r*z)/(1+a*r*z). The local thickness derivative is `(1-a*a)*r*z*(4*pi*i*q/lambda)/(1+a*r*z)^2`; transfer derivative is `(1-a*a)*z/(1+a*r*z)^2`. Chain these and use dR/dd=2Re(conj(r_total)*dr_total/dd). Prefer existing `simulate_with_thickness_jacobian` in production; do not copy an isolated second solver without justification.
3. Minimize `logsumexp(-beta*R)/beta`, with analytic gradient `-sum(softmax(-beta*R)*dR/dd)`, beta=100,400,1500. Each L-BFGS-B stage max180 iterations, ftol2e-13, gtol1e-9,maxls25. Intermediate iteration-limit status means a bounded nonconverged stage, not final success. Preserve best legal candidate and continue the declared schedule when budget remains.
4. Finish with exact sampled-minimum epigraph refinement: minimize -t subject to R_i(d)-t>=0 for every training condition and all physical constraints. SLSQP, analytic constraint Jacobians, max180 iterations, ftol1e-11. The successful32-layer run converged in130 SLSQP iterations after753 total optical/Jacobian evaluations in the researcher. Its all-thickness optimization took4.63 s, full main routine including independent audit5.83 s.
5. Independently audit fixed candidates on0.1nm mesh plus0.05nm shift, include material interpolation knots, refine all bracketed spectral minima and check endpoints. If a narrow missed dip changes qualification, reject it and optionally use a bounded point-exchange refinement; never report the training minimum as the audited minimum. Re-audit after any thickness/source change. This finite audit is not interval arithmetic and does not cover unrequested intermediate angles.
6. Existing production `audit_frozen_synthesis_candidate` successfully audits the exported exact32-layer candidate. Use its condition errors to compute the minimum *actual R*, not a tie-dependent worst zero-violation status field.

## Material and frozen-payload handling

- Keep `use_k=True`. The explicit source-unknown zero assumption applies ONLY to bulk Malitson substrate. It must not erase known Franta film k. Keep extrapolation=error.
- Existing TiO2 Franta dataset `builtin_research_TiO2_film` / `rii_tio2_franta` exactly matches the selected source. Add a distinct MgF2-Franta source identity rather than changing existing Rodriguez MgF2 records. The supplied frozen snapshot already does this.
- Film source nk values are fitted dispersion-model values, not independently measured ultra-low absorption. These are process/sample-specific models, not manufacturing qualification.
- Production front_layers storage is substrate_outward. Reverse BOTH research labels and thicknesses on export; preserve units. Single-sided bulk substrate resolves to semi-infinite, no back-face contribution.
- See `review-PORTABILITY-PLAN.md` for exact canonical frozen-schema replay and digest/assumption checks.
- If implementing/refactoring algorithms, update `docs/algorithms.html` in the same software change and add numerical/contract tests, cancel and budget checks, monotonic source semantics, no-seed cold-start regression, and independent dense-audit regression. An existing source record/import alone is not permission to overwrite user material data.


## Supplemental one-case generated-prior bridge (2026-10-21)

A bounded companion run subsequently tested a source-derived interior-center prior without loading the retained answer or optimized thickness vector as its seed. It computed the minimum real-admittance ratio C=1.5791937 across the requested band/conditions and applied the lossless-QW scheduling approximation only to prior placement: Δ=4/π·asin((C−1)/(C+1))=0.288383; with dimensionless f=1/3 the generated centers were 438.4511 and 638.6117 nm for an 8+8-pair allocation. Full optimization started from an initial minimum R≈6.1505%; the independent audit then passed at R=0.9873549441 (402.5051 nm, 30° p). A separately frozen production audit passed at R=0.9873549441 over 24,776 points with 36 bracketed extrema refined.

This is evidence for that single sourced-material/target/32-layer case only. It does not prove the schedule universally feasible, validate arbitrary materials/bands/architectures, establish continuous-band or manufacturing qualification, or mean this generator has been integrated into production software. The centers are computed outputs, not defaults or lookup values. Broader automatic anchor scheduling remains a proposal pending broader cold-start acceptance tests. The 7.15-second measurement above belongs specifically to the earlier 440/625 nm research prior and is not a generic synthesis runtime claim. See `generic-prior-bridge/` for frozen request, generated prior, result and audits.
