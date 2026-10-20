# Optical-constant data attribution

The CSV files are cropped, precision-preserving numerical extracts from the
CC0 refractiveindex.info database snapshot
c5c2f188e848453def5970e347399d653df2ffc2. Public domain dedication:
https://creativecommons.org/publicdomain/zero/1.0/

Original YAML SHA256, original and stored ranges, full references, preparation
comments and conditions are in provenance.json. The data represent the cited
measurements and fitted dispersion models, not measurements of the optimized
stacks or arbitrary deposited layers. Numerical interpolation does not improve
source accuracy. No missing k values were filled.

- MgF2, Franta et al. (2017), 134.2 nm e-beam evaporated polycrystalline film.
  https://refractiveindex.info/?shelf=main&book=MgF2&page=Franta
  https://doi.org/10.1016/j.apsusc.2016.09.149
- ZnSe, Querry (1987), optical-constants compilation.
  https://refractiveindex.info/?shelf=main&book=ZnSe&page=Querry
  https://apps.dtic.mil/sti/citations/ADA192210
- Float-zone crystalline Si, Franta et al., fitted 300 K data.
  https://refractiveindex.info/?shelf=main&book=Si&page=Franta-300K
  https://doi.org/10.1063/1.5026195

Online dataset pages were checked on 2026-10-20 against the pinned offline
coverage. The original publisher DOI for the MgF2 paper was not readable through
this research browser; the dataset supplied by its author remains fully
attributed. These are disparate processes and specimens, not one qualified
coating production recipe. Scalar effective-isotropic modeling is used here.
