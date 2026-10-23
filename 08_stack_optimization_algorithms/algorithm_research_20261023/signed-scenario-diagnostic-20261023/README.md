# 固定场景signed-V：网格低估与过零率错配

日期：2026-10-23。先读[诊断报告](REPORT.zh.md)。本批只对原baseline/control/exchange做固定输入的纯前向诊断，无优化、无Jacobian、无新候选选择；既有研究结果一字不改。

## 发现与不能推断的事

- 32个原训练场景×3设计，各完成96次稀疏600点与96次完整184600点前向。共享600点R差为0；baseline/control/exchange被稀疏低估的场景为24/26/28。
- control和exchange在稀疏训练各有1个假通过，完整训练均0/32。worst优势从稀疏34.3%缩至完整8.1%，但不反转，完整32场景中27个exchange更优。
- 历史共模control的5个通过样本，在exchange均失败。其中4个小负共模扰动在IR4046–4047nm/51°轻微越界，与exchange名义IR活跃点的极小余量相容；另1个由HR1044nm/39°主导。
- 因而波长欠采样确实存在，但不能独自解释“尾部严重度下降、通过数不升”。该诊断不隔离场景模型、零阈值目标及余量分配的因果贡献，不证明物理不可达或真实工艺机制。

signed V保留负值：取所有原HR点的0.99−R、IR点的R−0.03之最大值。通过仍按每条原运算符逐点判定，V=0不是一概通过；共享点审计阈值不是验收容差。

## 三幅诊断图

- [共模系数与signed V，包括五个丢失通过点](common-mode-coefficient-vs-signed-V.png)
- [零附近历史经验CDF](signed-V-near-zero-ecdf.png)
- [同一32场景的稀疏/完整V与配对差](training-sparse-vs-full-V.png)

曲线连线仅为视觉引导，非新增前向或连续证书。图中历史64场景不是新的确认集。

## 结果导航

| 文件 | 科学内容 |
|---|---|
| training-grid-diagnostic.json / training-grid-summary.csv | 96对前向的汇总、分位数、欠采样及配对诊断 |
| training-grid-scenarios.csv | 96组稀疏/完整signed V、原判定、主导点、共享R差 |
| training-grid-window-gaps.csv / training-window-gap-summary.csv | 逐窗欠采样与分布摘要，不等于只检查全场景主导点 |
| training-exchange-control-pairs.csv | 32场景的两网格配对差及排序变化 |
| existing-diagnostic.json / historical-validation-summary.csv | 三设计两历史误差模型的signed分布及过零率 |
| historical-validation-signed-scenarios.csv | 历史384个设计样本输出；完整系数列不在此复制 |
| historical-validation-signed-windows.csv | 1536个历史窗输出与严格通过标志 |
| historical-validation-near-zero-cdf.csv | 零附近ECDF结果，不是新物理采样 |
| five-control-pass-exchange-fail.csv / nominal-active-windows.csv | 五个翻转样本的标量共模位置、主导点与对应名义活跃点 |
| verification.json | 421项历史完整性核查、768个新窗极值/判定复核、无新优化或最终确认 |

本批排除完整训练请求、嵌入材料、32×89训练输入系数快照、执行脚本、源码/封存文件清单与原ZIP。五个例证中的标量共模坐标只为诊断，不是完整输入快照。本目录不能单独完整重跑全部原实验。

## 后续使用边界

历史holdout现已用于理解现象，不可再充当后续算法/候选的独立最终确认。训练分布是独立层误差，历史共模为不同相关结构；样本相关和共享代数项不构成因果证据。任何CVaR、yield目标或三臂实验均须另行决定与验证，本批未实施。

采用[公开fa987833数值基线](https://github.com/ii33/coating-sim/tree/fa9878336a597dc6df1db5b584bda3be4423cbca)及同一理想zero-k材料模型。没有生产良率、连续域、全局可达或GPU效果声明。


## 当前产品阶段方向（与历史研究分开）

本期敏感度优化先仅针对明确的理想假设，并保持原名义规格。用户参数表提供的预期误差分析是独立入口，不自动变成真实工艺/生产yield优化目标；暂不引入预置工艺误差模型。上述独立、共模或漂移等历史制造模型探索保留为研究假设，不是当前产品默认或已验证的用户生产模型。此处记录阶段方向，不宣称对应产品改造已经交付。
