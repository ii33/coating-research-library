# T07 第二轮 · 条件测量算子与有限参数可辨识性

状态：implementation_ready_validation_pending；本地冻结，不发布。用户实际硬件未知，全部数值为明示合成条件。生产、设备与完整批量未运行。

先打开`index.html`阅读全文，再按第06章运行`models/reader.py`作离线隔离自校。reader不含版权原文、ZIP或外部依赖目录；无网站部署。另有一份CC Attribution原始论文仅本地存档，严格排除于reader。

## 本轮可复用内容

- 测量合同：独立几何d、R/T、角/谱功率平均、单射线复椭偏比、偏振相干矩阵混合；未实现背面/散射/硬件明确拒绝
- 数学链：单位尺度与协方差白化、SVD及null方向、干扰参数投影、局部/全局区别与明确厚度别名
- 代码：有限参数有界多起点、每点重拟的厚度剖面、固定seed合成Monte Carlo和完整失败记录；默认plan_only
- 证据：精确哈希、一次独立相位/量纲核查、小测试和保留的rank阈值初次失败

## 阅读顺序

1. reports/01_conditional_measurement_operator.md
2. reports/02_phase_polarization_and_coordinates.md
3. reports/03_jacobian_scaling_and_nuisance.md
4. reports/04_local_global_ambiguity.md
5. reports/05_conditional_comparisons_and_design.md
6. reports/06_provenance_uncertainty_and_reproduction.md

一个关键反例：局部满秩的单波长透明膜仍可有完全相同R/T与反射椭偏比的另一厚度；精确d周期别名不能靠局部SVD消除。一个关键实现边界：切向p振幅到另一反射p基矢会带负号，不能只比较不同软件的Delta字符串。

所有T06材料来源、净留存、散射、背面、七误差轴及上游partial/not_run限制继续有效。详见第06章，不将任何小测试解释为生产资格。
