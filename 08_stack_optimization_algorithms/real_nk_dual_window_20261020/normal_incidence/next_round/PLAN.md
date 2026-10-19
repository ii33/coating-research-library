# Next round: metric-first research plan (not started)

This plan does not change acceptance of the archived normal-incidence half-space
results:3–5um and8–12um, R<=0.0099, T>=0.9001, tolerance1e-6. No long batch is
authorized by this plan document alone; the present task only prepared the plan.

## 1. Stability across genuinely different starts

Keep the same five source datasets, target guards and initial design domain
(<=16layers, <=20um total,0.1–10000nm/layer). Compare at least ten distinct start
families per route, recording each family before execution. For B, use independent
mutation seeds, the original seven-layer start, perturbations of each final
ten-layer start, and distinct material orders. Merely changing the current A RNG
seed would do nothing: its beam generation is deterministic. Independent A trials
must actually change prescreen admissions, finite-birth reference wavelengths or
retained order branches, while always beginning at N=0 and keeping physical goals
unchanged. Record the exact resulting starting/growth choices.

Use success fraction, independently audited worst R/T distributions, layer count,
total thickness and starting-family sensitivity as primary outcomes. Work/time
counts are evidence, not optimization objectives. Audit every effective improvement;
stop each successful run immediately. For a plateau, document repeated geometric
basins and switch a predeclared structural family, instead of increasing identical
local restarts. Preserve cancellation files, five-second heartbeats and best/basin
checkpoints. Search reproduction still requires unpublished v3 unless a separately
validated external research search kernel is prepared later.

## 2. Angle and polarization stress audit before reoptimization

First hold the exact archived A/B prescriptions fixed. Separately audit0,5,10,15,
20,30 and45degrees for s and p polarization in each window. This is a new stress
matrix, not a silent expansion of the original accepted objective. Report Rmax,
Tmin and Amax by angle/polarization/window, using dense/shifted/source-knot and
dimensionless local-extremum audit. Retain the zero-degree benchmark unchanged.
Only after these diagnostics should the user choose an angular design target.

The present sources cover all3–12um wavelengths needed at all listed incidence
angles, since angle changes do not change the vacuum wavelength domain. However,
the current n/k models are scalar effective isotropic data; MgF2 source-film
microstructure and actual deposited-film anisotropy are not thereby validated.
No fabrication/roughness/stress/temperature uncertainty is included.

## 3. Real finite ZnS plate and both surfaces

Confirm actual substrate thickness, wedge/parallelism, back coating, intended
coherence/measurement resolution and source match before a device-level claim.
The old design stores1mm, but that thickness was inactive in the half-space task
and has not been independently physically verified here.

Use the same Querry bulk/crystal ZnS dataset for the first diagnosis, retaining k.
The supplied1mm propagation estimate already shows potentially dominant absorption
at several source points. It is only exp(-4*pi*k*L/lambda), not a complete plate
calculation. Do not trade that loss for zero k or replace bulk ZnS with a thin-film
dataset. If the intended real ZnS plate is known to have very different absorption,
require an appropriate measured or original sourced bulk dataset and register the
data/model change as a separate experiment.

Compare bare plate, A/front-only, B/front-only, matching coatings on both sides,
and independently designed rear coatings. Begin with an incoherent intensity
model if the physical measurement justifies it; separately examine coherent
parallel-plate fringes and spectral averaging if justified. Report total plate
R/T, bulk absorption and each coating's absorption separately. Check reciprocity,
energy balance and an independent finite-slab formulation. The original accepted
half-space result remains an archived reference whatever these new device results.

## Source coverage for all proposed diagnostics

ZnS/BaF2/NaCl Querry:220–166666.7nm, bulk/crystal/mineral proxies.
MgF2 Franta thin film:27.5043–125141nm, e-beam134.2nm film on c-Si, not project matched.
Ge Amotchkina thin film:400–15000nm, source-specific e-beam film, not project matched.
All five sources have explicit full n/k tables and cover both windows. No broad
angular manufacturing validity, alternate substrate absorption or whole-device
90% transmission guarantee follows from domain coverage alone.

The separate independent review passed and is now attached. The fixed-angle and
finite-plate first-stage diagnostics were subsequently completed in a separate
result set, without changing these baseline goals or optimizing structures. This
file preserves the originally proposed follow-up scope. No push or upload occurred.
