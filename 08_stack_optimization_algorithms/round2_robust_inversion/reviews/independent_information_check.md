# Independent information-math check

- Reviewer role: GPT-6 Luna
- Scope: one narrow independent math/unit check only; no full review-chain signoff
- Files read: `models/design.py`, `models/inversion.py`, `models/scenarios.py`, `models/vendor/identifiability.py`, `models/vendor/measurement.py`, and `tests/test_reference.py`
- Files changed: this note only

## Derivation and findings

Let the existing and new observations have covariance

\[
C=\begin{bmatrix}C_0&C_{10}^{T}\\C_{10}&C_1\end{bmatrix},
\]

where `C10` is new-by-existing. The conditional mean of the new observations given the old ones has parameter derivative

\[
G=J_1-C_{10}C_0^{-1}J_0,
\]

and conditional covariance

\[
S=C_1-C_{10}C_0^{-1}C_{10}^{T}.
\]

These are the correct Gaussian conditional derivative and Schur-complement covariance. The block-Cholesky/conditional factorization gives the joint Fisher information as

\[
J^TC^{-1}J=J_0^TC_0^{-1}J_0+G^TS^{-1}G,
\]

which matches the returned `A0.T @ A0 + Ac.T @ Ac`. In the scenario construction, `C10=F1 @ F0.T` is the cross-covariance of the shared discrepancy features; the separately generated measurement noise has zero cross-covariance, as assumed.

`information_difference` appends the conditional whitened acquisition rows to the existing rows, then profiles the first three interest columns against the nuisance columns on both sides. Calibration/prior rows are present in the before and after matrices, so the nuisance parameter coordinates are the same; this is a same-space comparison, not a comparison against a different nuisance model.

`auxiliary_rows` gives a standardized calibration or prior residual the scaled-coordinate derivative `problem.scales[index] / sigma`, consistent with the Jacobian convention in `vendor/identifiability.py`, where columns are derivatives with respect to dimensionless scaled coordinates.

For the unknown-bias `d_geo` candidate, the added nuisance column is zero for old observations and `0.05` for the new thickness row. That is a row-local, uncalibrated bias direction; it has the same scaled-row derivative as the physical thickness parameter when `scale_d = 0.05 um`. With only this one new thickness row, nuisance projection removes its apparent thickness information, while retaining the information from existing rows. This matches the intended no-free-information result for an unknown-bias-only thickness reading.

## Checks run

With `PYTHONDONTWRITEBYTECODE=1`, four focused tests passed:

- `test_conditional_matches_joint_information`
- `test_correlated_repeat`
- `test_unknown_new_bias_zero_increment`
- `test_covariance_scale_rows`

An additional small SPD-matrix check compared the conditional-factor information against direct joint GLS information; maximum absolute difference was `8.9e-16`. A direct nuisance-projection check for the unknown-bias thickness reading returned exactly zero profiled interest-information increment. A calibration scale check with scale `0.1` and sigma `0.2` returned derivative `0.5`.

## Conclusion

No mathematical or unit inconsistency was found in the specifically scoped conditional-covariance formula, same-space nuisance projection, scaled calibration derivatives, or new uncalibrated thickness-bias handling. This is not a broader code review or review-chain signoff.
