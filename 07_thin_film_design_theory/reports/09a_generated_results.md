# 自动生成算例指标
全部为理论合成场景，不是实测。完整条件见 example_results.json。

## W01_AR
```json
{
  "n_substrate": 1.52,
  "n_ideal": 1.2328828005937953,
  "d_ideal_um": 0.3041651646201798,
  "assumed_MgF2_n": 1.375,
  "R_at_center_ideal": 1.1501154714002845e-33,
  "R_at_center_available_index": 0.01180868340478841,
  "note": "Independent synthetic substrate=1.52. T06 E01 actual proxy is 1.50106, not silently replaced."
}
```

## W02_Bragg
```json
{
  "nH": 2.1,
  "nL": 1.45,
  "pairs": 8,
  "center_um": 1.0,
  "center_R": 0.99300042325767,
  "infinite_period_relative_frequency_gap": 0.23445102861949743,
  "infinite_period_wavelength_edges_um": [
    0.895074438590696,
    1.1327921413792208
  ],
  "finite_8pair_R_at_gap_edges": [
    0.9190250043749382,
    0.9190250043749371
  ]
}
```

## W04_incoherence
```json
{
  "interface_R": 0.04,
  "analytic_incoherent_T": 0.923076923076923,
  "phase_ensemble_T": 0.923076923076923,
  "incorrect_average_amplitude_power": 7.703719777548943e-34,
  "coherent_T_min": 0.8520710059171595,
  "coherent_T_max": 1.0,
  "phase_samples": 4096,
  "assumptions": "uniform one-way phase ensemble, no bulk loss, all reflected orders collected"
}
```

## W05_cavity
```json
{
  "n": 1.5,
  "d_um": 5.0,
  "resonance_wavelength_um": 1.5,
  "interface_R": 0.04,
  "center_T": 1.0000000000000004,
  "center_GD_fs": 27.102082695736247,
  "analytic_center_GD_fs": 27.102082734849855,
  "FSR_frequency_Hz": 19986163866666.668,
  "reference_planes": "two physical slab faces; no added external propagation"
}
```

## W05_layer_absorption
```json
{
  "finite_layer_A": 0.5977193829638812,
  "density_integral": 0.5977194050552848,
  "parameters": {
    "lambda_um": 1,
    "N": "2+.15i",
    "d_um": 0.5,
    "AOI_deg": 35,
    "pol": "p"
  }
}
```

## W07_gradient
```json
{
  "profile": "n(z)=1+0.52(3u^2-2u^3); u=z/(2 um)",
  "rows": [
    {
      "slices": 20,
      "max_absolute_R_error_vs_640": 5.021250877299219e-06
    },
    {
      "slices": 40,
      "max_absolute_R_error_vs_640": 1.3449381305865937e-06
    },
    {
      "slices": 80,
      "max_absolute_R_error_vs_640": 3.380200488280991e-07
    },
    {
      "slices": 160,
      "max_absolute_R_error_vs_640": 8.082202500127636e-08
    },
    {
      "slices": 320,
      "max_absolute_R_error_vs_640": 1.618144987267252e-08
    }
  ],
  "max_R_640_on_0p7_to_2um": 0.00010900017205041197,
  "not_manufacturing_recipe": true
}
```

## W08_sensitivity
```json
{
  "wavelength_um": 1.01,
  "center_design_um": 1,
  "nominal_T": 0.21103347772631306,
  "sigma_fractional_thickness": 0.001,
  "J_per_um": [
    1.6616190154888908,
    1.952453543775656,
    4.436893804873887,
    4.633713599697109,
    9.962943592013717,
    10.10926857407668,
    21.38950935866024,
    21.50007846687951,
    45.22955055947381,
    21.500078466894777,
    21.38950935868522,
    10.109268574065577,
    9.962943592017881,
    4.6337135997193135,
    4.4368938048808255,
    1.9524535437742683,
    1.6616190154930541
  ],
  "d_um": [
    0.11904761904761904,
    0.1724137931034483,
    0.11904761904761904,
    0.1724137931034483,
    0.11904761904761904,
    0.1724137931034483,
    0.11904761904761904,
    0.1724137931034483,
    0.23809523809523808,
    0.1724137931034483,
    0.11904761904761904,
    0.1724137931034483,
    0.11904761904761904,
    0.1724137931034483,
    0.11904761904761904,
    0.1724137931034483,
    0.11904761904761904
  ],
  "J_step_halving_max_abs_change": 5.759817207007245e-05,
  "linear_sigma_T_independent": 0.012940220783422456,
  "linear_sigma_T_common": 0.03285670418170714,
  "MC_std_T_independent": 0.012977909240232947,
  "MC_std_T_common": 0.03300082507080856,
  "MC_samples": 3000,
  "seed": 708,
  "distribution": "illustrative Gaussian scenarios, no estimated production yield"
}
```

## W08_stationary_counterexample
```json
{
  "dR_dd_center": 3.4304730966222595e-17,
  "R_at_1percent_thicker": 1.0972418840410035e-05,
  "message": "Vanishing first derivative at nominal perfect AR does not mean zero tolerance loss."
}
```

## W03 稳定性
| d / µm | Imδ | R(S) | T(S) | |det M−1| | naive finite |
|---:|---:|---:|---:|---:|---|
| 0 | 0 | 0.04 | 0.96 | 0 | True |
| 0.01 | 0.377 | 0.486111097 | 0.465 | 2.22e-16 | True |
| 0.03 | 1.131 | 0.896412169 | 0.07 | 1.19e-16 | True |
| 0.1 | 3.77 | 0.978168946 | 0.000316 | 3.38e-14 | True |
| 0.3 | 11.31 | 0.978632478 | 8.92e-11 | 9.81e-07 | True |
| 0.5 | 18.85 | 0.978632479 | 2.52e-17 | 1 | True |
| 1 | 37.7 | 0.978632479 | 1.07e-33 | 1 | True |
| 3 | 113.1 | 0.978632479 | 3.46e-99 | 6.38e+81 | True |
| 10 | 377 | 0.978632479 | 0 | inf | True |
| 20 | 754 | 0.978632479 | 0 | nan | False |
| 100 | 3770 | 0.978632479 | 0 | nan | False |

## T06 数值对照
28组条件，最大复反射振幅绝对差 7.458e-15；最大透过功率绝对差 1.688e-14。
