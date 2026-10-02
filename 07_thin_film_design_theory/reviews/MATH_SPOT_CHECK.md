# Thin-film design theory: independent math spot check

**Date:** 2026-10-02  
**Scope.** Narrow derivation/check only; this is not a review of the whole project or a substitute for a full implementation review. No calculation code was present in this subfolder when inspected, so I did not wait on or assess code. I checked the stated equations directly and ran a small independent complex-arithmetic calculation. Actual execution was a **GPT-6 Luna mathematical spot check**, not a user-requested Seed or Sol review.

## Conventions and characteristic matrix

Use the `exp(-iωt)` convention, passive refractive index `N=n+ik` (`k≥0`), and forward waves with `exp(+ik_z z)`. Let `k0=ω/c`, `β=k_parallel/k0`, and choose the outgoing/attenuating square-root branch for `qz=sqrt(N²-β²)`. In a dimensionless tangential state `[E_t, Z0 H_t]^T`, the optical admittances are

- s / TE: `q_s=qz=sqrt(N²-β²)`
- p / TM: `q_p=N²/qz`

The phase is `δ=k0 d qz` for either polarization. With the state defined as fields on a layer's left face equal to its matrix times fields on its right face, the layer matrix is

`M=[[cosδ, -i sinδ/q], [-i q sinδ, cosδ]]`.

This sign is consistent with `exp(-iωt)`: for `E(z)=E+ exp(+ik_z z)+E- exp(-ik_z z)` and the corresponding signed tangential magnetic field, propagation from right face to left face gives the displayed matrix. Its determinant is `cos²δ-(-i sinδ/q)(-i q sinδ)=cos²δ+sin²δ=1`, including complex `q,δ`. A left-to-right state map uses `M⁻¹`, so matrix multiplication order should be made explicit. Here a stack in physical order `1,2,…,m` has `Mstack=M1 M2 … Mm`.

## Quarter-wave `(HL)^m` center admittance

At the design frequency, if both layers have `δH=δL=π/2`,

`MH ML = diag(-qL/qH, -qH/qL)`.

Thus `(MH ML)^m` is diagonal with entries `(-qL/qH)^m` and `(-qH/qL)^m`. With a substrate outgoing wave `[E,H]=E[1,qsub]`, the input admittance is `Yin=(C+D qsub)/(A+B qsub)`, hence

`Yin = qsub (qH/qL)^(2m)`.

This assumes the stack is ordered H then L in each pair and the phase thicknesses are exactly quarter-wave. Reversing the pair order inverts the admittance ratio. For a real physical thickness and a lossy layer, `δ=π/2` cannot generally hold as a complex equality; the expression is the exact matrix result under the quarter-wave-phase condition, normally used for lossless design layers.

## Lossless binary-period first stop-band width

At normal incidence, for nondispersive, lossless layers with quarter-wave optical thicknesses at `ω0`, a period's half-trace is

`cos(KΛ)=cos²x - ½(nH/nL+nL/nH) sin²x`, with `x=πω/(2ω0)`.

The first-gap edges satisfy `cos(KΛ)=-1`. Solving gives `|cos(xedge)|=|nH-nL|/(nH+nL)`; the lower edge has positive cosine and the upper edge negative cosine, and the two edge frequencies are symmetric about `ω0`. Therefore

`Δω/ω0 = (4/π) asin(|nH-nL|/(nH+nL))`.

So the quoted result checks out for the stated idealization: first gap, lossless and nondispersive, normal incidence, and exact quarter-wave optical thickness at the reference frequency. At fixed oblique incidence in nondispersive media, the same algebra uses the polarization's layer admittances `qH,qL` in place of `nH,nL`, provided both phases scale linearly with frequency. With material dispersion or a frequency-dependent incidence condition, calculate the edges from `|½ tr(Mperiod)|=1` instead of applying the closed form blindly.

As a numeric check, `nH=2.30, nL=1.45` gives `Δω/ω0=0.29113119` from the formula.

## Symmetric stack as an equivalent layer

For a reciprocal isotropic stack, each layer matrix has unit determinant and equal diagonal entries. Reversing the physical layer order gives `Mrev=J M⁻¹ J`, `J=diag(1,-1)`. A mirror-symmetric (palindromic) stack equals its reverse, so its total matrix has `A=D` and `AD-BC=1`:

`M=[[A,B],[C,A]]`.

For generic `B,C≠0`, it has the exact formal homogeneous-layer representation `cosδeff=A`, `qeff²=C/B`, choosing compatible complex branches so that `B=-i sinδeff/qeff` and `C=-i qeff sinδeff`. This is an algebraic transfer-matrix equivalence, not a claim that the stack is a physical uniform material. In a lossless stop band, `|A|>1`; therefore `arccos(A)` is complex, and `C/B` may be negative, making `qeff` imaginary/complex. Degenerate cases such as `B=C=0` need a limiting representation rather than division by `B`.

## Scattering-matrix cascade and reciprocal transmission

Using scalar wave-amplitude ports and defining `b=S a`, cascading a left block `A` followed by a right block `B` gives the 1-D Redheffer composition (`D=1-A22 B11`):

`S11=A11+A12 B11 A21/D`

`S12=A12 B12/D`

`S21=B21 A21/D`

`S22=B22+B21 A22 B12/D`.

For a bare interface between real propagating admittances `q1,q2`, using tangential-E wave amplitudes, `r1=(q1-q2)/(q1+q2)`, `r2=-r1`, `t12=2q1/(q1+q2)`, and `t21=2q2/(q1+q2)`. These port amplitudes must be kept in a consistent normalization during the cascade; do not multiply ordinary S matrices as if they were transfer matrices.

For the above characteristic-matrix convention, let `Mstack=[[A,B],[C,D]]` and let `qin,qout` be the exterior admittances. Solving the two boundary conditions gives the common denominator

`den=qin(A+B qout)+C+D qout`,

`tforward=2 qin/den`, `treverse=2 qout/den`.

Hence `qout tforward = qin treverse` for reciprocal layers at the same `β`, when `t` is the tangential-E amplitude ratio. With flux-normalized ports in lossless exterior media, the equivalent statement is equality of the forward and reverse transmission amplitudes. It is not a statement that the two reflection amplitudes have equal magnitude in an absorbing asymmetric stack.

For a direct lossy counterexample, I multiplied the stated characteristic matrices at normal incidence for a stack between air on both sides, with left-to-right layers `(N,d/λ)=(2+0.25i,0.11)` then `(1.4,0.17)`. From the boundary equations, `Rleft=0.14735776` while `Rright=0.06347099`. Reversing the layer order gives the same right-incidence result. This verifies that reciprocity of transmission does not force equal reflectances when the stack absorbs.

## Online spot check: arXiv:1809.07708v1, Eqs. 30–34

I checked the v1 PDF itself, specifically Eqs. 21–23 and 30–34 (PDF pp. 3–4). Eq. 11a defines the s-wave interface matrix `Γs=[[1,1],[s,-s]]` (Eq. 11b gives the p-wave form); Eq. 21 is the interference matrix `Φ`. Eq. 22 states `Ω=Γ0⁻¹ Ψ ΓM+1`; Eq. 23 identifies `Ψ` as the tangential-field transfer matrix. Eq. 30a–d, as printed, gives each `ωij` as `½` times the corresponding numerator, without division by `s0`. Direct multiplication of Eq. 22 instead gives `1/(2s0)` times those four numerators for this s-wave convention. Thus, when the numerator terms are read as intended, Eq. 30's four entries are all `s0` times the Eq. 22 matrix entries.

There is also a literal typesetting issue in the v1 text of Eq. 30b: its third term reads `−s0 sM+1 ω1,2` rather than the corresponding `−s0 sM+1 ψ1,2`. Read literally, this makes the equation self-referential. I do not infer the authors' intended correction.

The scalar mismatch is visible without any film. Take a bare normal-incidence interface `n0=s0=1.3`, `nsub=sM+1=1.7`, so `Ψ=I`. From Eq. 22 and the displayed Γ matrices,

`Ω11=(1+sM+1/s0)/2=1.15384615`, giving the conventional tangential-E Fresnel transmission `tE=1/Ω11=0.86666667`.

Using Eq. 30a as printed instead gives `ω11=(s0+sM+1)/2=1.5`; Eq. 32 then gives `t̃+=2/(s0+sM+1)=0.66666667`, exactly `tE/s0`, not `tE`. The interface reflectance from Eq. 31 is `R=|(1.3−1.7)/(1.3+1.7)|²=0.01777778`. Eq. 34 with its printed `s0 sM+1 |t̃+|²` gives `T=0.98222222`, which happens to equal the physical `T=(nsub/n0)|tE|²`; `R+T=1`. This shows that Eq. 32's amplitude is scalar-rescaled relative to the conventional tangential-E amplitude while Eq. 34 compensates for that scale in this example. It is inconsistent with treating both the Eq. 26 field-amplitude definition and Eq. 32 as the same unscaled transmission coefficient unless an extra normalization is specified. This is a report of the algebraic inconsistency, not a guess about author intent; do not copy Eq. 30/32 as a standard formula without independently fixing the normalization and checking a bare interface.

## Recalculation recipe

1. Choose the square-root branch for `qz` that represents an outgoing/attenuating passive wave; form `q_s` or `q_p` and `δ=k0 d qz`.
2. Build each `M_j` from the displayed convention and multiply in physical order (right-to-left state map: `M1 M2 …`).
3. For left incidence, use `t=2qin/[qin(A+B qout)+C+Dqout]` and `r=[qin(A+Bqout)−(C+Dqout)]/[qin(A+Bqout)+C+Dqout]`. For right incidence, reverse the physical layer list and repeat, or solve the right-boundary conditions directly.
4. For lossless exterior media, check `R=|r|²`, `T=(qout/qin)|t|²`, and energy balance for lossless layers. For lossy external media, use the appropriate real normal Poynting flux rather than assuming this simplified `T` expression.
5. For the arXiv example, use `Ψ=I` and multiply the two displayed Γ matrices by hand; this immediately distinguishes `Ω11=1.15384615` from the Eq. 30/32 value `1.5` / `0.66666667`.

## Sources

- L. N. Acquaroli, [“Matrix method for thin film optics,” arXiv:1809.07708v1](https://arxiv.org/pdf/1809.07708v1), especially Eqs. 11a–b, 17, 21–23, 25–34, 45, and 49–53. The paper's own v1 PDF is the source checked for the Eq. 30 transcription and normalization comparison.
- [arXiv abstract/metadata](https://arxiv.org/abs/1809.07708).

