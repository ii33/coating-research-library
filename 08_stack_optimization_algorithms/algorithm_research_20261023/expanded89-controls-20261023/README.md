# 全89变量、32场景的四组有限稳健控制

日期：2026-10-23。先读[完整报告](controls-report.md)，再看[质量曲线PNG](quality-vs-cloud-work.png) / [SVG](quality-vs-cloud-work.svg)。本批只同步已完成光学研究，不发布软件，不包括进行中的后续constraint exchange/100预算控制或GPU效果。

## 结论与负结果

- 两个固定训练seed各测试±0.5%/±1%独立均匀误差，32训练场景、全部89厚度变量，设计搜索边界为原厚±1%。工艺误差幅度与设计域是两种不同设置。
- 四组均21次cloud评价、20次迭代，partial。四个raw稀疏训练最佳解都未通过完整184600条件名义；外部只保留之前完整名义合格的候选。较低raw loss不是资格。
- 全新完整原网格留出：每幅度的原设计与该幅度两个冻结候选均为独立0/16、系统1/16。四候选逐样本gain/loss全0，未证明yield改善；±1%还保留尾部恶化。
- 192个固定样本的双扰动表达式全网格复核，逐点及联合判定翻转为0，最大R差约4.57e-14。真实四工作线程只验证四个固定场景的串并数值一致，不是速度基准。
- 有限预算、理想k=0材料、固定层数/材料、局部搜索和16样本不能构成收敛、全局/物理不可行、连续域或生产良率证书。

## 公开数据地图

| 文件 | 解释 |
|---|---|
| predeclared-plan.json | 两seed×两幅度、32训练/89变量、原厚±1%、25评价/20迭代上限与新留出计划 |
| compact-study-settings.json | 四组紧凑科学设置：种子/误差幅度/场景数/变量数/设计边界/预算；不是完整可执行请求，无材料数组或场景系数 |
| seed-…-candidate-and-work.json，四份 | 最终外部完整名义合格处方及训练/调用计数；不是raw稀疏冠军 |
| training-controls-summary.json / comparison.csv | 四组全部训练、raw/full资格、停止状态与拒收数；summary不重复候选层表 |
| quality-and-qualification-traces.json | 四组真实质量进度与61次完整资格检查，包括25次拒收；未复制中间候选处方 |
| 原规格与材料 | 沿用既有公开研究基线；本批不新增完整材料/请求载荷，原1nm×25角184600条件与严格运算符见报告和紧凑设置 |
| baseline-full-original-nominal.json | 原设计完整名义前向验收 |
| fresh-holdout-summary.json | 两误差档的12行统计、逐样本通过标志/最大违规；无holdout选seed |
| 留出设置 | 新seed2026102351/52、每模型16样本；本批只发布汇总，不发布完整系数数组 |
| core-expression-holdout-summary.json | 双表达式逐点/联合翻转、ULP和绝对差摘要 |
| verification-summary.json | 192样本完整重放及四worker数值等价摘要，不含源码清单或模块路径 |
| constraint-rejection-diagnostics.json | 稀疏路径漏掉的完整原约束诊断，不是已实现constraint exchange的结果 |
| fixed-candidate-descriptive-diagnostics.json | 冻结候选的配对gain/loss、显式边界与厚度改动诊断，不用于事后挑选 |
| work-accounting.json | 训练/资格/留出/算术重放工作量分开；非完整CPU/wall或公平加速比 |

CSV实际文件名为training-controls-comparison.csv。表中省略号只指四个明确seed/幅度文件前缀，不表示有未公开软件入口。

## 复现口径

软件基线为[公开fa987833提交](https://github.com/ii33/coating-sim/tree/fa9878336a597dc6df1db5b584bda3be4423cbca)。研究runner未公开，因此本目录是科学配置/处方/结果载荷，不冒充一条命令自包含复跑包；本批未包含完整请求、场景系数数组和嵌入材料，不能只凭这些摘要精确重跑全部实验；它支持方法/结果审查及最终处方核对，不冒充完整可执行复现包。

每个cloud评价含名义与32场景；其计数不是单个波长点、TMM子核调用或总CPU成本。完整原网格外部资格检查另计，不能把它描述为已在稀疏求解器内部施加全部原约束。

IR物理上界使用0.03及显式严格[2,3]，避免在历史nextafter阈值上再收紧一ULP。真实core扰动表达式与原始等价表达式均完整检查，未选择有利浮点路径。原始名义/扰动指标和误差系数不变，无额外margin。

公开范围排除完整优化请求、嵌入材料数据和场景系数数组，以及源码hash/模块manifest、脚本/运行日志、原ZIP、384份逐样本大证据和中间层表。设计/材料/响应身份digest是科学完整性字段。前轮研究与数据一字不改；后续提案和未完成工作必须另报，不因本轮质量曲线下降就记作已成功。
