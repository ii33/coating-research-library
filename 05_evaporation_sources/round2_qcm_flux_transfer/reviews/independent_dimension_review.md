# Narrow independent dimensional review

Date: 2026-10-02 (UTC)

## Scope and method

One narrow review of `models/qcm_flux.py` and `sources/summaries/T05-R2-S01.md`. Focus: Sauerbrey and Z-match SI units/sign, the selected finite-load branch and nonempty initial load, point-kernel units and receiving projection, Al/Al2/O2 particle-to-nucleus/mass conservation, and rank separation of source Q from capture `eta`. No implementation files were changed; no hardware, external service, production data, or API was used. Seven self-authored lightweight numerical checks are in `tests/test_independent_dimensions.py`.

This is not a general code review or a claim that any designated Seed/Sol independent-review chain has completed. The numerical checks exercise the current implementation with synthetic inputs only.

## Result

No dimensional, sign, or conservation defect was found in the requested scope.

- INFICON's SQM-160 manual defines added mass as a frequency reduction and `DF = Fq − Fc`, with `dq = 2.649 g/cm3` and `Nat = 166100 Hz·cm`. Converting to SI gives `rho_q = 2649 kg/m3` and `Nq = 1661 Hz·m`, matching the model constants. `rho_q*Nq*(f0−f)/f0²` has kg/m² units and positive sign for added mass. The model's Z-match expression likewise has kg/m² units and positive sign on its admitted branch; its `z_ratio` is dimensionless.
- The code accepts only `f0/2 < f <= f0` for the principal mathematical branch, excluding the singular endpoint, and explicitly says this is not a physical validation threshold. The summary appropriately reports the manual's empirical statements as material-specific test/limits, not a guarantee. A synthetic nonzero baseline load followed by a known additional rate recovered the added rate without treating the initial load as zero.
- `point_kernel` evaluates angular source emission times receiving incidence cosine divided by squared range, so its output is m^-2 for total emitted kg/s. Equal-range isotropic examples gave the expected inverse-square value and the expected receiving-projection cosine. The QCM/workpiece transfer uses `Q_incident * k_w / k_q` consistently.
- Explicit stoichiometry gave Al nuclei flux `3 + 2·4 = 11`, O nuclei flux `2·5 = 10`, and mass `(11 M_Al + 10 M_O)/N_A`; the calculated mass matched exactly in the check. Reconstructing a mixed incident mass from Al, Al2, and O2 number fractions returned its specified input mass.
- For QCM-only measurements with fitted common capture, the log-Q and log-eta design columns are identical and rank deficient. The appended independent-source-Q row is `[1, 0, 0, 0]` for `(logQ, n, a, logeta)` and restores full rank, consistent with the residual equation in `fit_source`.

## Verification

Command: `PYTHONDONTWRITEBYTECODE=1 python -m unittest projects/coating-research-library/05_evaporation_sources/round2_qcm_flux_transfer/tests/test_independent_dimensions.py -v`

Result: 7 tests passed. I did not run the full project suite, inspect unrelated modules, or validate any actual deposition measurement.

Reference checked: [INFICON SQM-160 Operating Manual, §§10–11](https://www.inficon.com/media/4271/download/SQM-160-Operating-Manual.pdf?language=en&v=4).
