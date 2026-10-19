# T08 · 膜系设计优化算法（首轮工程手册与可复算参考）

原文：`00_project/工程科研.txt` 第12行。范围：高精度/高性能、快速近似、持续迭代。9章报告、16条来源卡、3个T06起始膜系、参考代码、36项测试与失败反例。没有修改T06/T07或产品程序，没有推送。

## 先读结论

- 稳定S核配合prefix/suffix解析厚度Jacobian，层数复杂度O(M L)；与全方向切线及独立Airy差分对照
- 有界TRF/L-BFGS-B精修、粗网格快解、粗到细继续、多起点/有限枚举、显式总厚度约束及有限minimax均可复跑
- 结构插入必须经过有限厚度与制造约束回证；本轮needle候选退化，保留原设计
- B03窄带滤波精修在设定预算内未收敛且未达教学规格，未隐藏失败或继续无限调参
- 材料都是冻结proxy，所有光谱/公差为合成计算；没有材料实测、设备或量产资格证明，无全局最优保证

## 阅读路线

1. [设计契约与目标](reports/01_design_contract_and_objectives.md)
2. [稳定正问题与导数](reports/02_stable_forward_model_and_derivatives.md)
3. [局部精修与约束](reports/03_local_refinement_and_constraints.md)
4. [全局探索与needle](reports/04_global_search_needle_and_topology.md)
5. [快速近似与代理控制](reports/05_fast_approximations_and_surrogate_control.md)
6. [鲁棒性与不可辨识性](reports/06_robustness_and_identifiability.md)
7. [持续迭代工程结构](reports/07_incremental_iterations_and_engineering_architecture.md)
8. [基准与复现](reports/08_reproducible_benchmarks.md)
9. [失败与验收](reports/09_failure_modes_and_acceptance.md)
10. [自动结果表](reports/09a_generated_results.md)

## 一次离线复跑

```bash
cd 08_stack_optimization_algorithms
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
export MPLCONFIGDIR=/tmp/t08-matplotlib
python -m unittest discover -s tests -v
python models/run_benchmarks.py
python models/run_extensions.py
python models/render_results.py
python models/check_package.py
```

运行依赖Python3.12 / NumPy2.3.5 / SciPy1.17.0 / Matplotlib3.10.8已安装可信环境；兼容范围见requirements，其他版本未全面测。数值不依赖联网或原文PDF。本专题复制出去可以独立运行，因为T06材料/层表和T07核已冻结成逐字快照并标记来源；既不导入上游目录，也不修改它们。

## 数据与代码导航

- `models/optimization_core.py`：导数、目标、求解器、插层/合并、局部代理、minimax
- `models/vendor/t07_optics_kernel.py`：T07冻结稳定核（自有项目源码）
- `data/benchmark_config.json` / `optimization_contract.json`：可重复协议与未知输入
- `data/benchmark_results.json` / `extension_results.json`：全部预算/误差/失败
- `data/checkpoints.json`：继续迭代的厚度和上下文标识
- `data/spectra/`：独立谱审计CSV
- `figures/`：4张原创SVG；reviews内预览
- [来源说明](sources/README.md)、[来源注册表](data/source_registry.json)
- [首轮验收](reviews/ROUND1_ACCEPTANCE.md)、[未决问题](reviews/OPEN_ISSUES.md)、[T09移交](T09_HANDOFF.md)

指定完整模型审查链缺席仅在阶段schema中保持pending，不影响阅读工程方法；不得将本轮窄核查冒称完整独审通过。第三方原文仅本地排除存档，公开包只保留摘要和来源链接。


## 2026-10-19 近期前沿补充

[近期逆设计方法与公平成本核查](../manual_studies/2026-10-19_recent_frontiers/README.md)：OptoGPT/OptoLlama/IrisFlow、可微求解、主动学习与制造稳健性；版本、开放状态、训练/推理/求解成本和基线范围均单独列明。未运行作者代码或独立复现其性能。
