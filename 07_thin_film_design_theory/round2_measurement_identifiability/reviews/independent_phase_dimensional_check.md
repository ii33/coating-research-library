# Independent phase and dimensional check

Date: 2026-10-02  
Scope: only `models/measurement.py` phase-basis mapping and `models/identifiability.py` scaled-Jacobian/covariance units; independently checked against the frozen `models/vendor/optics_kernel.py`. No implementation changes or batch run.

## Phase convention

The kernel declares `exp(-iωt)` and tangential-E amplitudes (`optics_kernel.py:4-6`). Its interface admittance variables are `q_s=kz` and `q_p=n²/kz` (`:26-32`), giving tangential-E reflection `r_t=(q_left-q_right)/(q_left+q_right)` (`:41-49`). Independently, with the incidence plane x-z, choose `e_p,i=(cosθ,0,-sinθ)` and the explicitly opposed reflected basis `e_p,r=(-cosθ,0,-sinθ)`. The reflected tangential field is then `E_x,r=-cosθ·r_p,basis`, while the kernel's tangential coefficient gives `E_x,r=+cosθ·r_p,t`; therefore `r_p,basis=-r_p,t`. Thus `ratio_from_amplitudes`'s default `rho=-rp_t/rs` is consistent with that basis (`measurement.py:63-72`); its `same_tangential_p` option instead reports `+rp_t/rs`.

At normal incidence `q_s=q_p=n`, so a bare air-to-real-glass boundary has `r_s=r_p,t=(1-n)/(1+n)`. The opposed-basis ratio is therefore `rho=-1` and `Delta=arg(rho)=π mod 2π`; the same-tangential ratio is `+1`. Tiny direct check using the frozen kernel and the naked-interface formulas, for n=1.52 at λ=0.55 µm:

| AOI | `r_s` | `r_p,t` | opposed-basis `rho` | `Delta` |
|---:|---:|---:|---:|---:|
| 0° | −0.206349206349 | −0.206349206349 | −1 | ±π (mod 2π) |
| 60° | −0.428296918826 | +0.0390788935963 | +0.091242527972 | 0 |

The two bare Fresnel expressions and kernel amplitudes agreed within `5.6e-17` at both angles. NumPy can display the normal-incidence phase as `−π` because of signed zero; this is physically the same point as `+π`. Minor endpoint note: `circular_delta` documents `(-π,π]` (`measurement.py:75-77`), but `np.angle` may return `−π` exactly on the branch cut. This is only a representative-value/documentation edge, not a rho sign error.

## Scaling and whitening dimensions

`theta=theta0+diag(scales) z` makes `z` dimensionless (`identifiability.py:18-22`); with `(n,k,d_um)`, the thickness scale and finite-difference step are in µm (`:23-35`). Therefore `J=∂y/∂z` has the observation-coordinate units in each row. A Cholesky factor `L` of observation covariance `C` has those row units, so `B=L⁻¹J` is dimensionless and `covariance_scaled_local_if_full_rank=(BᵀB)⁻¹` is covariance of dimensionless `z` (`:41-55`). To express local covariance in physical parameters, apply `diag(scales)·cov_z·diag(scales)`; the field name correctly says the returned covariance is scaled.

For an actual unit conversion, both dependent quantities must follow: if a thickness observation changes from µm to nm, transform its Jacobian row by 1000 and covariance by `C' = D C Dᵀ` with `D=diag(...,1000,...)`. If parameter `d` changes from µm to nm, change the function's input mapping, `d` scale, and bounds by 1000 together. A tiny two-row fixture doing both transformations yielded maximum absolute difference `4.8e-11` in `L⁻¹J`; rank and singular values were unchanged. This verifies the intended invariance under consistent unit conversion. No implementation or test file was added; no heavy computation was run.
