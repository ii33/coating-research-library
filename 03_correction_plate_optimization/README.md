# T03 修正板自动设计优化

首轮v0.1已形成理论、参考算法、合成基准和实测闭环方法。核心结果是把“灰度线性解”和“真正实体板”分开验证：一个40 s合成案例改善明显，一个17.3 s案例反而恶化。这里没有用户机器数据，输出不是可直接切割安装的加工图。

## 从这里阅读

1. [物理正向算子](reports/01_forward_operator.md)：真实板平面、扩展源、有限厚度与射线缓存
2. [均匀性和制造约束](reports/02_objectives_and_constraints.md)：径向/角向分解、吞吐、可行性、几何屏障
3. [算法与线性代数](reports/03_algorithms_and_linear_algebra.md)：受约束凸松弛、实体转换、局部搜索、文献逆式核验
4. [稳健性与校准](reports/04_robustness_and_calibration.md)：有限情景、测量协议、加工偏差与闭环
5. [数值研究结果](reports/05_benchmark_results.md)：同预算比较、密集留出、加密和负例
6. [复现与使用边界](reports/06_reproducibility_and_limits.md)：运行方式、单位、证据层级和停止条件

## 结果摘要

40 s固定速率合成算例，144个错开验证点、4096个时间节点、48个扩展源节点，1 mm厚实体板：

- CV由1.375%降至0.320%，PV/mean由4.442%降至1.127%
- 面积平均厚度保留90.18%；仅几何筛查通过，未作机械/工艺放行
- 17.3 s带速率波动反例的CV由1.439%升至2.268%，说明径向变平不等于二维变均匀
- 同预算三情景稳健搜索在本例没有优于名义方案，不做普遍优越性宣传

以上均为合成数值结果。47项硬断言检查、一次有界独立数学复核和加密研究不等于实机验证。完整数值以[结果JSON](benchmarks/results/benchmark_summary.json)和[对照CSV](benchmarks/results/comparison.csv)为准。

## 复现和可复用文件

从研究库根目录运行：

    PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 python 03_correction_plate_optimization/verification/run_verification.py
    PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 python 03_correction_plate_optimization/benchmarks/run_benchmarks.py
    python 03_correction_plate_optimization/benchmarks/plot_results.py
    python 03_correction_plate_optimization/verification/check_release.py

离线读者包不含原文HTML，运行最后一条完整性检查时追加 `--reader`，明确跳过未打包原文的哈希复查。

核心验证和基准只需NumPy；可选绘图使用已有Matplotlib。冻结T02模型是只读同级依赖，不改动其物理内核。

- [合成输入](data/synthetic_case.json)与[真实测量模板](data/measurement_template.json)
- [板形与闭合多边形](benchmarks/results/designs.json)，长度单位m，非加工放行
- [来源摘要](sources/summaries/source_summaries.md)、[登记](sources/source_registry.json)与[权利说明](sources/RIGHTS_AND_ACCESS.md)
- [范围验收](reviews/ROUND1_ACCEPTANCE.md)、[独立数学检查](reviews/independent_math_check.md)、[未决问题](reviews/OPEN_ISSUES.md)
- [下一专题T04移交](T04_HANDOFF.md)

指定DeepSeek/Seed/完整Sol审查链的缺口如实保留；一次实际Sol数学检查不冒充完整阶段签署。按原顺序完成有界优先研究后移交下题，全部十个大项目首轮结束后再扩展更多板族、实机闭环和多材料实际互补板。
