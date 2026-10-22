# Source-level diagnosis and next discriminating experiment

No further optimization was run for this diagnosis. It uses the frozen source, original optical tables, saved source-derived prior provenance, and the completed finite diagnostics.

## What the current HR prior actually covers

The supplier branch does not treat the broad visible HR band as one quarter-wave stack. It creates four substack centers inside 580–920 nm:

- 614.430793 nm
- 689.545504 nm
- 773.843056 nm
- 868.446058 nm

It creates one additional center, 1063.812013 nm, for the separate 1044–1084 nm HR window. The cold 50-layer prior gives each center five H/L pairs. The same source allocator at the 64-layer no-extra-layer boundary would distribute 32 pairs as [7, 7, 6, 6, 6], in ascending center order.

Source: [multispectral prior, exact production commit](https://github.com/ii33/coating-sim/blob/68835133025ffc1e74df2fe00921e4961f691efb/coat_sim/core/film_synthesis_multispectral_priors.py#L159-L250); allocation tie-break is at lines 63–72.

## Does it account for 39–51 degree p polarization?

Partly, but only through a static proxy. For each HR window, the code samples both s and p at every requested angle and three wavelengths (lower endpoint, geometric center, upper endpoint). It takes the weakest admittance contrast across these witnesses. In this source branch the minima are:

- Broad HR: contrast ratio 1.372501784, at 920 nm / 51 degrees / p.
- Narrow HR: ratio 1.367760757, at 1084 nm / 51 degrees / p.

Those contrasts feed an infinite-periodic-style stopband-width proxy, approximately 0.20074 and 0.19856, and a quarter-wave mirror threshold proxy that estimates ten pairs per center. The center count and logarithmic spacing use a project-convention three-quarter proxy-width overlap.

However, each actual layer thickness is initialized using its center wavelength at 45 degrees. There is no independent finite-substack calculation proving that the resulting centers, pair counts and terminations maintain 99% across every band edge and angle. Concatenated blocks interact coherently, their angular phase shifts are not resolved by the static width estimate, and the budget allocation does not learn from the actual worst spectral condition. The full joint evaluator catches those failures later.

The ten-pair estimate is a heuristic demand, not a physical minimum. Five centers times ten pairs suggests 100 HR layers only within that proxy. It does not prove 100 layers are necessary, or that 64 layers are insufficient. The proxy even uses the limiting p contrast with a 99% single-polarization-style threshold, whereas the user's acceptance is unpolarized. The actual requirement is neither a separate 99% p threshold nor the heuristic pair count.

The 64-layer ceiling is our declared exploration budget, not a manufacturing constraint specified by the user. This new experiment used 50–53 layers, so it also does not exhaust architectures available within that ceiling.

## What the new diagnostics add

The best new cap candidate still has a broad-HR unpolarized minimum of 92.483074% at 894 nm / 51 degrees and a narrow-HR minimum of 92.308866% at 1084 nm / 51 degrees. Its p minima are lower, 86.241231% and 86.541276%, though their extrema need not occur at the unpolarized worst conditions. This supports treating finite-stack tiling/termination and the weak-p angular response jointly, not merely attaching a generic IR cap to a fixed HR seed.

The ascending IR triad obtains a 4.637865% long-wave AR maximum, but damages the joint HR and short-wave AR requirements. The half-degree replay additionally finds an HR dip at 580 nm / 48.5 degrees. A good IR-only plot is not an acceptable optimization result.

## Source-model choice is a real optical variable, not a free splice

Values sampled directly from the separate frozen n/k pairs:

| Wavelength | Supplier YbF3 n | Supplier k | Author-export YbF3 n | Author-export k |
|---|---:|---:|---:|---:|
| 3 μm | 1.522333 | 0.000833 | 1.485100 | 0 |
| 5 μm | 1.509000 | 0.001500 | 1.484709 | 0 |
| 7 μm | 1.475000 | 0.001800 | 1.484601 | 0 |
| 12 μm | 1.254400 | 0.002880 | 1.484527 | 0.032853 |

Supplier YbF3 is strongly dispersive in the long-wave IR; author-export YbF3 is almost index-flat over these samples but has greater k at 12 μm. Neither branch is uniformly the more absorbing one. Author-export zero values remain explicit model values, not measured zero-absorption bounds.

Correction to the preserved frozen protocol: its phrase “more absorptive stress branch” was too broad and is not supported across the full IR range. The valid selection rationale is the smaller previous worst gap and use of an independent complete supplier n/k model. This correction changes no source, search setting, candidate or result. The original protocol remains unchanged for auditability.

The source manifest in prior-evidence/manifest.json identifies the exact independent material files and source hashes. A favorable constant index or n/k splice must not replace these branches. Actual deposited-film/process measurement remains a separate qualification issue.

## Recommended next step, in priority order

1. Replace fixed equal-demand concatenated HR blocks with a small finite-stack-aware tiling/chirp comparison. Optimize visible center placement, overlap, pair allocation/phase profile and terminations against the actual full-stack 39–51 degree response, including the narrow HR window. A smoothly chirped or apodized pair profile is a research candidate, not a validated solution. Retain both s/p diagnostics, but accept only the user's unpolarized constraints.
2. Design the IR match against the complete dispersive HR stack's complex input response/admittance, with explicit field and layer-order conventions, not against an isolated bare ZnS interface or arbitrary 4/6/9 μm quarter-wave fractions. Then jointly refine HR and IR variables on all four original windows. This tests the interaction identified by the triad tradeoff rather than repeating the same unhelpful end/connection seeds.
3. Compare these generic architectures separately on both complete material-source branches. Do not select the model only because its dispersion or absorption makes a target easier, and do not combine favorable n and k from different sources.
4. Keep fair first-stage family coverage and resumable bounded local stages. Longer refinement may help because none of the 24 local slices reached a solver return, but this experiment does not establish that more time alone will overcome the topology/model mismatch. Give extra continuation time only after a finite coherent tiling/matching candidate is shown to have a better joint worst-gap trajectory.

The minimum generic production change worth reviewing first is therefore fair family coverage plus finite-stack-derived IR/HR structure proposals and honest stage reporting. The present seed fractions, beta ladder, search boxes and smooth-max normalization should not be promoted as validated defaults. No software implementation or publication is made by this experiment.
