# T05 independent source-physics and code check

Scope: independent mathematical/source-physics review of `models/source_reference.py`, `tests/test_source_reference.py`, and `benchmarks/run_benchmarks.py`, plus a compact source-evidence pack. This is not the mandated Seed/Sol review or stage sign-off. No model or benchmark code was edited; this review file is the only authored project file.

## Result

No blocking normalization, source-Q, aperture, or energy-balance error was found in the checked paths. The 41 unit tests and deterministic synthetic benchmark pass. Two interpretation issues should stay visible before any material/source fit is treated as calibrated: (1) the point-source log fit can be very misleading under misspecified source geometry, and (2) at a constrained boundary fit the reported degrees of freedom are still `N-2`. The latter is a small statistical-reporting defect, not a failure of the unconstrained fit path.

## Code and numerical checks

### Angular normalization and geometric transfer

`cosine_pdf` implements a per-solid-angle density on the front hemisphere. For `n >= 0`,

`Z = ∫hemisphere cos^n(θ) dΩ = 2π/(n+1)`, so `p_n = (n+1)/(2π) cos^n(θ)` integrates to one. At `n=1`, this is `cos(θ)/π`; for `n=0`, it is uniform over the forward hemisphere. The tests numerically integrate `n = 0, 1, 2, 7, 20`, verify the Lambertian case, and prevent back-emission at `n=0`.

`flux_kg_m2_s` multiplies this source angular density by the separate receiver projection `mu_i` and `1/r²`, then weights by normalized source fractions and visibility. This is the correct solid-angle-to-receiver-area mapping for the stated kernel. A source cosine and target cosine are both physically present for parallel planes; it is only double-counting if a fitted/empirical deposition kernel already includes the receiver projection. The analytic on-axis uniform disk check passes against `Q/[π(H²+a²)]` to the test tolerance.

`mass_rate_kg_s` is explicitly pre-occlusion total mass emitted into the source hemisphere, not a QCM nm/s value. Source fractions sum to one, and the aperture/visibility mask clips rays without renormalizing the surviving rays. That is correct for an absorbing, zero-thickness mask with no wall scattering or re-emission. `circular_aperture` documents those limits. The point log-fit has no aperture/visibility input, so it must not be applied as-is to an aperture-clipped/recessed source profile.

The updated `gaussian_footprint` variant was checked with zero-mass source nodes, including a highly concentrated footprint. It keeps finite, normalized weights; restricting the stabilization maximum to positive-weight nodes avoids the earlier zero-weight-node underflow failure mode.

### Log-fit identifiability and a counterexample

For the documented unobstructed point source, the fit transform is algebraically consistent: `log(J r² / mu_i) = [log Q + log(n+1) - log(2π)] + n log(mu_s)`. The implementation correctly recovers `Q,n` from exact synthetic point-source data and rejects a single-angle layout by rank. It returns a scaled design condition number and conditional covariance, which are useful diagnostics; narrow angle coverage is not rejected automatically.

The benchmark intentionally demonstrates the danger of geometry misspecification. A disk source of radius 0.10 m at a 0.20 m throw, with true `n=2.5`, fitted by the point-source model using only ±12° data, has just 0.023% maximum training residual. Yet the fit returns `n≈0.299` and `Q≈7.96e-6 kg/s` versus true `4e-6 kg/s`; the off-axis holdout reaches 191.3% maximum relative error. Wide-angle point-source synthetic holdout error is only 1.32%, illustrating that this result is model mismatch, not a failure of the exact point model.

The synthetic narrow-angle layout has design condition ≈1949 and standard errors ≈1.96 in `log Q` and ≈6.89 in `n`; the code returns these diagnostics. An on-axis monitor also cannot distinguish Q from angular shape: changing `(Q,n)` from `(4e-6,1)` to `(2e-6,3)` leaves the axial flux fixed while the 60° flux falls to one quarter. The fit covariance excludes geometry error, model discrepancy, sticking/density uncertainty, and correlated sensor drift, as the benchmark output records.

Concrete low-severity reporting issue: when an unconstrained slope is negative, `fit_point_logflux` sets `n=0`, marks `boundary_fit=True`, re-estimates the intercept, and suppresses covariance, but still reports `degrees_of_freedom = len(x)-2`. A six-observation synthetic negative-slope case returns a boundary fit with df 4. At a one-parameter active boundary, `N-2` is not the conventional residual df; moreover, boundary-constrained likelihood statistics are not ordinary interior chi-square cases. Safer options are to report df as null/qualified for boundary fits, or clearly label any active-parameter count as approximate. This does not affect the benchmark’s unconstrained cases.

### Aperture and source-rate convention

The recession benchmark keeps intrinsic Q fixed and applies a zero-thickness aperture transmission mask; it does not rescale Q to force the surviving downstream flux to sum to Q. This is the correct convention if Q denotes pre-aperture emitted mass. The generated recession profile shows increasing off-axis loss and complete clipping at some angles for the deepest synthetic source. Real hot/re-emitting walls would need a different transport model; the benchmark notes this.

The sweep/rate benchmark also handles linear averaging correctly for static geometry: independent averaging of footprint and Q gives 5.68% RMS error, while mass-weighting the footprint by Q recovers the exact time average to floating-point precision. Its static-aperture/geometry qualification is important; the same identity need not hold for moving geometry.

### Thermodynamic assumptions and limitations

`vapor_pressure_pa` uses a constant-enthalpy Clausius–Clapeyron approximation for one vapor species and requires a user-validated temperature interval. `hertz_knudsen_kg_m2_s` is the equal-temperature, one-species net evaporation form; the code rejects a condensation branch rather than clipping it. `lumped_history` is explicit Euler with fixed effective heat capacity, fixed source areas, lumped conductance/radiation losses, and a single-phase approximation. It has no phase-change enthalpy, evolving melt geometry, spatial temperature field, reactive/dissociative species, plume collision/recondensation, or material calibration. Those limits are stated in the docstrings and the benchmark identifies all numbers as synthetic.

One thermodynamic consistency check remains a user responsibility: for a pure single species on one equilibrium phase, the vaporization/sublimation enthalpy used in Clausius–Clapeyron should be compatible with the latent heat used in the energy balance (`ΔH_molar / M` in J/kg), unless the parameters explicitly represent different effective phenomena. The synthetic fixture is consistent (100 kJ/mol / 0.05 kg/mol = 2 MJ/kg), but the API does not enforce this. At a phase transition the equilibrium vapor pressure may be continuous while its temperature derivative changes; a single constant-enthalpy fit and fixed heat capacity should not span that transition. Restrict and document each fit interval by phase, or use a piecewise phase-aware model.

## Primary/open/manufacturer evidence pack

1. R. B. Darling, Caltech, “Physical Vapor Deposition” lecture notes, pp. 9–13 and 38. [PDF](https://mmrc.caltech.edu/PVD/manuals/PhysicalVaporDeposition.pdf). Derives the Knudsen-cell cosine law and the receiver-area projection; p. 38 distinguishes slow source-temperature response from shutter modulation. Teaching notes/idealized geometry, not an empirical e-beam kernel. Its p. 7 distinction between isotropic Langmuir free evaporation and Lambertian effusion should be read as a source-model convention, not generalized across all practical evaporators.

2. L. Holland and W. Steckelmacher, “The distribution of thin films condensed on surfaces by the vacuum evaporation method,” *Vacuum* 2(4), 346–364 (1952). [Publisher abstract](https://doi.org/10.1016/0042-207X(52)93784-6). Abstract recognizes Knudsen cosine as a baseline and treats point, strip, wire, and ring sources with experiments on ZnS/MgF₂ strip heaters and Al spiral filaments. The accessible evidence here is the abstract; it predates e-beam guns.

3. K. R. Carson, F. A. Wierum, and M. L. Rudee, “Departure from Free Molecular Flow During the Boat Evaporation of Permalloy,” *JVST* 7(2), 347–350 (1970). [AIP abstract](https://doi.org/10.1116/1.1315855). Resistance-heated tungsten-boat Ni–Fe experiments report non-cosine high-rate focusing normal to the boat and angle-dependent vapor composition. One alloy/source configuration, not a universal correction.

4. K. B. Thakur et al., “Spatial distribution function for vapour flow and its validation for a two-dimensional source generated using strip electron beam,” *Vacuum* 75(3), 283–292 (2004). [Publisher abstract](https://doi.org/10.1016/j.vacuum.2004.03.009). Cu strip-source measurements report source-temperature-dependent, anisotropic collimation along/across a 2D source and a ±5% fit over local Knudsen numbers 1.2–0.23. The result is specific to the reported strip source/material/range.

5. A. Powell, P. Minson, G. Trapaga, and U. Pal, “Mathematical modeling of vapor-plume focusing in electron-beam evaporation,” *Metallurgical and Materials Transactions A* 32, 1959–1966 (2001). [DOI](https://doi.org/10.1007/s11661-001-0008-y) · [author-uploaded full text](https://www.researchgate.net/publication/225267436_Mathematical_modeling_of_vapor-plume_focusing_in_electron-beam_evaporation). Sections II–III and V–VI model Ti disk/ring sources; collisional focusing and recondensation depend on effective local Kn, and a smaller/more intense source focuses more at fixed total rate. Caveats: hard-sphere/simple-source assumptions, uniform source temperature, no scan transient or background-gas transport.

6. N. Wang et al., “Experimental study of sweep control in e-beam evaporated optical coatings,” *Chinese Optics Letters* 8(6), 621–623 (2010). [Article/PDF](https://www.researching.cn/ArticlePdf/m00005/2010/8/6/COL08060621.pdf) · [publisher abstract](https://opg.optica.org/col/abstract.cfm?uri=col-8-6-621). Pre-melting/evaporation trials on Ti₃O₅, SiO₂, and HfO₂ connect sweep dwell and rate stabilization with source-surface depth/material thermal conductivity; a flatter source surface is associated with a more stable plume. Specific materials/controller, not a transferable sweep program.

7. A. Zehe, A. Ramírez, and B. W. Müller, “Thermal response of a Knudsen-type effusion source to sudden heating-power changes,” *Superficies y Vacío* 13, 72–76 (2001). [Open PDF](https://www.redalyc.org/pdf/942/94201319.pdf). Section 2.3 (around p. 73) and experiments report a delayed, approximately exponential small-step temperature response; heat capacity, finite conduction, and radiation contribute to the time constant. This is an MBE effusion cell, so use as qualitative thermal-lag evidence, not a boat/e-beam time constant.

8. Ferrotec/Temescal, “2PT and 3PT PopTop Electron Beam Turret Sources,” Rev. B manual. [Official PDF](https://e-beam.ferrotec.com/wp-content/uploads/sites/7/Temescal-2PT-3PT-Source-Manual-RevB.pdf). §1.2–1.3 pp. 1-3–1-6 describes magnetic beam deflection and spot concentration; §§1.4 and 2.5.1 give model-specific cooling/interlock requirements; front matter p. x warns of lethal residual HV and says not to bypass interlocks; §6.4–6.5 pp. 6-4–6-6 connects edge strikes/spot issues/inadequate cooling with contamination or source damage. Model-specific requirements are not generic operating guidance. The manual itself uses “water pressure” with a GPM unit in one interlock section and distinguishes flow/pressure in the spec table; its chamber-pressure interlock values also differ slightly between sections. A separate Temescal 1CK Rev. C manual gives a different flow-switch value. Quarantine these to the exact model/manual revision; publish no generic thresholds.

## Commands actually run

- `python -m unittest discover -s /workspace/scratch/d35c7d80562e/projects/coating-research-library/05_evaporation_sources/tests -v` — 41 tests passed.
- `python /workspace/scratch/d35c7d80562e/projects/coating-research-library/05_evaporation_sources/benchmarks/run_benchmarks.py` — exited successfully; all benchmark assertions passed. Synthetic outputs include wide-angle holdout max error 1.32%, geometry-mismatch holdout max error 191.3%, narrow-angle design condition 1949, and exact static-geometry mass-weighted footprint averaging.
- Manual zero-weight-node footprint probe (Python importing `source_reference.py`) — normalized finite weights for a concentrated Gaussian footprint; no error.
- Manual constrained-fit probe (six points with a negative apparent angular slope) — returns `boundary_fit=True`, `n=0`, `degrees_of_freedom=4`; this confirmed the boundary-df issue above.

### Supplemental inactive-node probe

After the initial review, a zero-mass source-node edge case was checked explicitly. `flux_kg_m2_s` computes every source-receiver distance and rejects zero distance before applying source fractions. A non-planar two-node `Source` with fractions `[0,1]`, receiver coincident with the inactive node, and the active node spatially separated raises `ValueError('receiver coincides with source')`. `circular_aperture` also checks every `dz`; with a valid aperture between the active node and receiver, it raises `ValueError('horizontal ray cannot use this aperture')` because the zero-mass node lies at receiver height. These are false failures: the inactive node emits no mass. Recommended handling is to validate visibility against the full `(Nreceiver, Nsource)` input shape, then calculate geometric rays and singularity/separation checks only for positive-weight nodes, while returning full-shape visibility/mask arrays (inactive columns can be zero). Coincidence with any positive-weight node should continue to raise. Add regression tests for both functions.

The benchmark was rerun after its later extension. It still passes. New synthetic results: rectangular-boat withheld y-plane maximum error is 17.41% after 1.22% maximum error in the x-plane training layout; ±2 mm source-height offsets produce roughly ±0.24% Q bias and ±0.036 bias in n for that geometry.
- Manual inactive-node coincidence probe (`Source` with fractions `[0,1]`) — both `flux_kg_m2_s` and `circular_aperture` reject inactive-node coincidence although the active node is separated; confirms the supplemental issue.

## Final regression check after fixes

The parent updated the implementation and added regression coverage after the findings above. Reran the complete T05 checks against that final code:

- `python -m unittest discover -s /workspace/scratch/d35c7d80562e/projects/coating-research-library/05_evaporation_sources/tests -v` — **51/51 passed**. New checks cover inactive-node coincidence in flux and aperture paths while retaining full mask dimensions, boundary-fit df reporting, single-species latent-heat consistency, invalid initial temperature even for empty histories, vapor-pressure overflow, equivalence with the T02 transfer kernel, spherical total-mass conservation, and aperture escape fraction.
- `python /workspace/scratch/d35c7d80562e/projects/coating-research-library/05_evaporation_sources/benchmarks/run_benchmarks.py` — **passed** (seed 20261002); point-source holdout max error 1.32%, rectangular-source withheld y-plane max error 17.41%, point-for-disk mismatch holdout max error 191.30%.

The inactive-node false errors are fixed by applying geometric checks/ray calculations to positive-weight nodes while preserving full visibility-array shape. Active-source coincidence remains rejected. Boundary-fit output now leaves df null with an explicit note instead of assigning ordinary interior-fit df. The single-phase, single-species history now checks `latent_heat_J_kg = delta_H_J_mol / molar_mass_kg_mol`; the synthetic fixture satisfies it. Vapor-pressure overflow is converted to a clear `ValueError`.

Final SHA-256 values:

- `models/source_reference.py`: `180fb1e9359c31855c0b9151d48071ec500627714c0ddd7095e91a903a65e842`
- `tests/test_source_reference.py`: `31ea61d5d2f18480df913f8ce29aeb149f1b6a43c4d34b7b96e82471e43e954d`
- `benchmarks/run_benchmarks.py`: `def990e1dbb977bb35f476ccecec246144b3f6551027fe1e4d5db69b13766ab9`

The earlier confirmed code findings are resolved in the tested version. The source-model assumptions and empirical-transfer limits described above remain applicable; this remains a bounded independent check, not a formal stage approval.
