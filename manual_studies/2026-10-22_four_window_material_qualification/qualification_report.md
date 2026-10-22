# Four-window material/model source recommendation

Scope and acceptance: single coated surface on a ZnS substrate, HR 580–920nm and1044–1084nm, AR3–5um and7–12um, incidence39–51degrees. AR is strict R<3% in both windows at the specified angles; HR is ≥99% unpolarized in both windows. No separate s/p minimum criterion is specified; retain s and p outputs alongside the unpolarized result.

## Decision

Algorithm/model-level validation can proceed now using named, reproducible source-model branches. A complete same-process measured n,k spectrum is not a prerequisite for testing algorithms. It is necessary to avoid claiming that these source-model results certify the actual manufacturing process.

1. Amotchkina2020 original numeric exports give a complete, reproducible modeled n,k branch over the target bands, including exported zeros. Those zeros are explicit source-model values, not measured absorption upper bounds. Keep the original values and identify the branch as modeled. Do not silently equate them with measured k=0.
2. Use the Merck YbF3 sparse n,k table as an independent supplier-model scenario. Its full10-node n,k data spans0.25–12.5um. The sparse grid does not resolve moisture features near3um. It differs strongly from Amotchkina in LWIR n and k.
3. Use the paired Mouchart1992 ZnS n,k table on3–11um as an independent film-loss sensitivity scenario, not as an unlabelled patch onto another process. It cannot independently characterize11–12um or1064nm. Merck ZnS is n-only and does not close those absorption-characterization gaps.
4. Keep bulk ZnS distinct from film ZnS. Use a named bulk boundary model: Li1984 n-only; manufacturer Hellma bulk n-only; or Querry1987 full modeled n,k as a separate CVD-bulk screening branch with its uncertainty. The user's ZnS grade is unspecified. Do not relabel a deposited film as a substrate or assume Cleartran grade.

Derived Amotchkina CSVs have both the original numerical k and a conservative qualification-masked k column. Blank masked entries reflect our conservative qualification policy, not an absence of numerical author data. The original author files have n,k numbers across the export range.

## Key source-model discrepancies

- ZnS author export: k is positive at400–990nm and exactly0 from1000–14000nm. The author description also provides an exponential model, k=0.03970exp(-0.080715/lambda_um-7.074209lambda_um). This predicts about1.98e-5 at1064nm, rather than the export's0. Retain the model choice and difference explicitly. A visible absorption exponential cannot establish the magnitude of long-wave phonon loss.
- YbF3 author export at roughly10/11/12um has k≈0.00477/0.01635/0.03278; Merck has k=0.0024 at10um and0.003 at12.5um. These are materially different absorption scenarios.
- YbF3 author model has n≈1.48454 at10um; Merck has n=1.372 at10um. Do not combine n from one source and k from another under one calibrated material identity.
- Querry bulk CVD ZnS is explicitly optically isotropic, measured as a thick Raytheon sample and KK-inverted from reflectance. Low-loss k has large uncertainty: original Table6 has DK≈K at many target wavelengths, including1.06um and10um. The CC0 database transcription omits DN/DK, so keep this limitation.

## Implementation policy

- Separate material roles, source/sample/process identity, n and k domains, and modeled versus measured/characterized status.
- Make source-model branches reproducible by pinning source URL, retrieval date, interpolation method, units and data hash.
- Do not silently extrapolate. An explicit extrapolated/model-continuation research branch is permissible if labeled and compared with alternatives.
- Linear or shape-preserving interpolation of sparse data is a numerical assumption, not evidence that unresolved absorption features are absent.
- Run all specified angle and wavelength windows with s,p reported separately and the explicitly chosen polarization acceptance rule. None of these sources by itself establishes the actual film's tensor optical constants at39–51degrees. Scalar effective-isotropic TMM is an assumption to state.
- For a single surface, report flux into the ZnS boundary as single-surface T; do not equate low R with high T when film absorption is nonzero. No rear-face or substrate-thickness transmission acceptance is required by the user's current instruction.
- Model-level acceptance should identify material branch and assumptions. Manufacturing/process acceptance remains conditional on matching measured film and substrate data, tolerances and deposition process.

## Verified primary/source URLs

Merck ZnS, n-only table, page2:
https://www.emdgroup.com/Products/PM/us/Zinc%20sulfide_Patinal_EMD.pdf

Merck YbF3, n,k table, page2:
https://www.emdgroup.com/Products/PM/us/101601_YbF3_tcm2080_127462-us.pdf

Mouchart, Begel andClement1992, TableII, DOI10.1364/AO.31.000885:
https://opg.optica.org/ao/abstract.cfm?uri=ao-31-7-885

Amotchkina etal2020, DOI10.1364/AO.59.000A40:
https://opg.optica.org/ao/abstract.cfm?uri=ao-59-5-A40
https://refractiveindex.info/download/data/2020/Amotchkina/ZnS_nk.xlsx
https://refractiveindex.info/download/data/2020/Amotchkina/YbF3_nk.xlsx
https://refractiveindex.info/download/data/2020/Amotchkina/Summary_for_RefractiveIndexINFO.pdf

Hellma, bulk ZnS andCleartran manufacturer data:
https://www.hellma-materials.com/en/optical-materials/ceramics-for-optics/zinc-sulfide-and-cleartran-2/
https://www.hellma-materials.com/wp-content/uploads/2024/11/ZincSulfide_Cleartran.pdf

Li1984, bulk n, DOI10.1063/1.555705:
https://srd.nist.gov/JPCRD/jpcrd240.pdf

Querry1987, primary report section4.6,p71,Table6pp74–80; full PDF downloaded and checked:
https://hitran.org/data/Aerosols/Aerosols%20data%20from%20previous%20HITRAN/Aerosols-2016/papers/querry_minerals_1987.pdf
CC0 numeric transcription:
https://refractiveindex.info/database/data/main/ZnS/nk/Querry.yml

## Primary leads not yet imported as numeric models

- Zheng etal2021, DOI10.3788/IRLA20210371: YbF3/YF3 films on multispectral ZnS, claimed n,k0.4–14um. Primary abstract verified. PDF request returned420, so numerical model/table not extracted.
- Sun etal2022, DOI10.3390/coatings12111693: YbF3 IAD, n,k190–12000nm figures; moisture features near2.9 and6.1um. No verified portable numeric table yet; full page returned429 and official PDF403.
- Liu etal2017, DOI10.3788/OPE.20172508.2038: e-beam/IAD ZnS, annealing variants, IR n,k figures through14um and long-wave phonon absorption. Primary PDF available but font encoding corrupts numeric text. No reproducible numeric fit extracted.
- Harris etal2008, DOI10.1117/1.3006123 anderratum10.1117/1.3223355: Cleartran bulk n,k8–14um atseveraltemperatures. Primary article/erratum not fully retrieved; no unverified numeric table imported.

Rahmlow/Corning2009 is an architecture precedent, not a material-data certification:45degree visible reflection plus dual-IR passbands. Public text does not identify a film pair and does not prove the present39–51degree,7–12um or99percentHR specification.
https://www.corning.com/media/worldwide/csm/documents/Filters_for_Dual__Rahmlow.pdf

No user data, source repository or external publication was modified during this research.
