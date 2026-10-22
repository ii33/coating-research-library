# Engineering literature benchmark: one-sided ZnS four-window coating

## Bottom line

I found no primary source demonstrating the complete requested combination: ZnS substrate, one coated face, nonpolarized R ≥ 99% over both 580–920 nm and 1044–1084 nm, R < 3% over both 3–5 µm and 7–12 µm, and AOI 39–51°. The closest four-function demonstrator is on Ge and measured much lower reflection than the requested HR threshold. The strongest ZnS-substrate recipes are partial-spectrum analogues and use material sets beyond ZnS/YbF3.

The table values below retain each source's own metric. Mean reflectance/transmittance, a single-wavelength reflectance, and a minimum-over-band requirement are not interchangeable. No source below specifies a full 39–51° angle sweep or a nonpolarized (both s and p pass) minimum across all requested bands.

## Five relevant primary sources

1. **Shi et al., “Design and Deposition of Ultra-Broadband Beam-Splitting Coatings,” Coatings 15(6), 695 (2025).** [Primary full text and tables](https://www.mdpi.com/2079-6412/15/6/695)
   - Closest four-window function: designed at 45° for HR 0.5–0.8 and 0.9–1.7 µm, AR/transmission 3–5 and 8–12 µm. Not the requested HR windows, and Ge substrate rather than ZnS.
   - Finite graded-block designs at λ0 = 1800 nm, H=Ge, M=ZnS, L=YbF3; the authors report 14.02 µm S1 and 13.16 µm S2. Table 2 stacks:
     - S1: `Ge/(0.5HM0.5H)^8 0.8(0.5ML0.5M)^8 0.63(0.5ML0.5M)^8 0.5(0.5ML0.5M)^8 0.4(0.5ML0.5M)^8 0.3(0.5ML0.5M)^8/Air`
     - S2: `Ge/(0.5HM0.5H)^9 2M 0.8(0.5ML0.5M)^8 0.63(0.5ML0.5M)^8 0.49(0.5ML0.5M)^8 0.39(0.5ML0.5M)^9 0.31(0.5ML0.5M)^9/Air`
   - At 45°, measured average R was 86.6% in 0.5–0.8 µm and 93.7% in 0.9–1.7 µm. Measured component (front splitter plus rear AR) average T was 91.4% in 3–5 µm and 91.3% in 8–12 µm; rear-AR-only T values 98.5% and 97% are inferred, not direct single-face measurements. These are means, not minimum R.
   - Process lesson: the authors associate IR transmission loss with Ge absorption, ZnS degradation at high-temperature deposition, and contamination/cross-contamination; lowering the bake temperature to 100 °C improved the result. This paper is a useful architecture/process analogy, not proof the user’s limits are feasible on ZnS.

2. **Rahmlow et al., “Filters for Dual Band Infrared Imagers,” Proc. SPIE 7298, 72982J (2009).** [Primary paper PDF](https://www.corning.com/content/dam/corning/media/worldwide/csm/documents/Filters_for_Dual__Rahmlow.pdf)
   - At 45° on Ge, compares visible HR 0.45–0.8 µm with MWIR AR 3.5–5 µm and FIR AR 7–10.5 µm. It does not include the target 1044–1084-nm HR band or the full 7–12-µm pass window.
   - Model candidate table gives *band means*, not minima: a 59-layer / 8.73-µm design has mean visible R 98.1%, MWIR reflectance 1.43%, FIR reflectance 1.35%. The fabricated 53-layer / 6.5-µm design measured mean visible R 94.5%, and mean IR reflectances 1.2% / 0.9% at 45°.
   - E-beam evaporation, QCM thickness monitoring; no finite layer recipe or material pair is disclosed. The authors identify thickness/stress-induced distortion and cosmetic defects as practical tradeoffs; moving the short-wavelength reflector nearer the top helps reduce absorption loss. This is a measured manufacturing benchmark, not a 99%-minimum demonstration.

3. **CN105842857A/B, ZnS-substrate visible/NIR HR / MWIR-pass patent.** [Primary patent record and claims](https://patents.google.com/patent/CN105842857A/en), [PDF](https://patentimages.storage.googleapis.com/12/97/cc/6363bbbc3807de/CN105842857A.pdf)
   - Most useful exact ZnS-substrate finite prescription: 51 layers, ZrO2 end layers with an aperiodic alternating YbF3/ZnS interior. Table 2 embodiment 1 was visually checked and transcribed to `CN105842857A_embodiment1_table2.csv`.
   - At 45°, the patent reports tested mean T=1.674% over 0.5–0.8 µm, T=0.771% at 1064 nm, and mean T=95.747% over 3.7–4.8 µm. Claims also state <2%, <1%, and >95% criteria, respectively. No minimum band R, p/s or nonpolarization criterion, or LWIR window is reported; these are T measurements and are not R limits.
   - Reported stack lesson: aperiodic thicknesses and ZrO2 transition/protective end layers are chosen for stress matching, passband ripple control and durability. This is not directly transferable if the working model lacks validated ZrO2 constants.

4. **CN106443841A/B, “Ultralow residual reflectance ZnS substrate long wave antireflection film.”** [Primary patent record](https://patents.google.com/patent/CN106443841A/en), [PDF](https://patentimages.storage.googleapis.com/7b/57/47/96b8395f03152d/CN106443841A.pdf)
   - Exact six-layer ZnS-substrate recipe, visually verified on PDF p.6; λ0=8 µm, QWOT reference unit λ0/4: `ZnS substrate | 0.5298 Ge, 0.1411 YF3, 1.0932 Ge, 0.5478 ZnS, 0.2883 YF3, 0.3019 ZnS | air`. Physical thicknesses from substrate out are 264.5, 191.6, 545.7, 492.9, 391.5 and 271.6 nm.
   - Patent reports max residual R <0.5% and average R <0.1% over 7.5–9.7 µm; however, I found no explicit AOI or measurement protocol in the patent text, so treat as a patent performance claim/design, not verified 39–51° measured evidence. It is not the whole 7–12 µm target.
   - Useful manufacturability lesson: limit the high-stress YF3 layer to <0.4 µm; the final YF3 layer is 391.5 nm. Note YF3 is yttrium fluoride, not YbF3, and the design also needs Ge.

5. **Amotchkina et al., “Comparative study of NIR-MIR beamsplitters based on ZnS/YbF3 and Ge/YbF3,” Optics Express 27(4), 5557–5572 (2019).** [Primary paper PDF](https://pure.mpg.de/rest/items/item_3035434_1/component/file_3039131/content), [DOI](https://doi.org/10.1364/OE.27.005557)
   - Manufactured ZnS/YbF3 dichroic on ZnSe, optimized at the ZnSe Brewster angle 67.9° for HR around 770–830 and 860–1050 nm, with 4–8 µm transmission; measured spectra at 45° and 67.9°. This is outside the user’s AOI and spectral specification, but is useful primary evidence on polarization: for the 14-layer ZnS/YbF3 design, central R_s=99% and R_p=87.5% at 67.9°. A 20-layer modeled design reaches central R_p=98.5%, but adds thickness/stress/deposition-error risk; paper's analysis states the p-polarized HR width for this pair is limited at that large angle.
   - E-beam deposition at 120 °C; reported ZnS and YbF3 film stresses have opposite signs and partially cancel in the stack. This warns not to extrapolate a single polarization's peak R to an unpolarized band minimum.

## Machine-readable prescriptions

- `research/CN105842857A_embodiment1_table2.csv`: 51-layer ZnS/ZrO2/YbF3 embodiment, visually checked against PDF pp.3–4.
- `research/CN114236661B_22layer.csv`: 22-layer Ge-substrate alternating YbF3/ZnS prescription, visually checked against patent PDF p.2. Its patent reports at 45° a tested R=98.25% at 1.064 µm and *average* T=98.71% over 7.7–10.3 µm. This is a useful exact YbF3/ZnS fabrication example, but it misses the user’s 99% minimum, uses Ge substrate and does not establish nonpolarized performance.
- `research/CN106443841A_6layer.csv`: six-layer Ge/YF3/ZnS ZnS-substrate recipe above, visually checked against PDF p.6.

## Design implications for the present target

- No close source supports relaxing the target. Simulate and judge the exact one-face ZnS interface over the full four bands, both s and p and all angles 39–51°, reporting worst-case minima/maxima separately from band means. Keep a clear/bare backside or a back-reflection correction consistent with the requested single-face metric.
- Finite graded / aperiodic blocks and terminal impedance transitions are better literature-supported starting structures than merely concatenating quarter-wave HR stacks and caps. However, none of the cited recipes is a drop-in stack for the current material dataset; use only materials with validated film n,k over the full 0.58–12 µm range.
- Reference wavelength is stated for the 2025 graded-block design (1.8 µm) and the six-layer LWIR AR design (8 µm). It is not specified in the retrieved Rahmlow report or the CN105842857A embodiment table; do not infer one from thicknesses. The CN114236661B patent also gives physical thicknesses rather than a design λ0.
