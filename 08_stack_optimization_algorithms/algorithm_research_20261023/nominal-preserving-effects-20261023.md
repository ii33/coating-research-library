# 显式名义保留有限场景稳健优化：效果验证

日期：2026-10-23。本轮在 [coating-sim 17e0c4d公开基线](https://github.com/ii33/coating-sim/tree/17e0c4d8ecd38faf88f1793a4a935d683fa037fb)上使用独立开发中的核心实现。尚未正式发布或完成目标主机验收，不能据此称用户已可用；本次只同步研究报告和科学数据，不发布软件。未改原光学界限，未额外增加margin。

## 本轮新增的证据，不改写前轮

前轮[敏感性实效](sensitivity-results.md)与data目录保持原样。本轮显式启用nominal-preserving策略：用非线性有限场景云和解析Jacobian的SLSQP局部约束优化，在搜索/接受候选时保护原名义规格，不再仅靠敏感性目标本身碰巧保持名义。正式原运算符checker仍是最终依据，solver success与solver_acceptable不能取代它。此策略已在开发实现中完成本报告的小/大例与负例测试，但不等于发布版功能、全局最优或制造保证。

CVaR、更复杂工艺校准及监控反馈仍属先前研究建议，本报告未证明它们已实现或有效。这里的通过数只对应声明的厚度误差与固定理想材料模型。

## 设计与验收隔离

- AR/HR 使用先前归档的小例及其原名义网格/边界，只改显式假设误差档和新策略。训练24个独立有界均匀场景；最终独立/系统留出各64，种子与系数在预声明计划和请求中保存。
- 每档同时预声明 worst 与 expected 两种能力，全部结果一起报告；没有根据 holdout 选择超参数或重新优化。若今后据这些结果改方案，需要新 holdout。
- ±0.5%/1%/2% 是有界幅度，不是 sigma；1nm 为绝对有界幅度。这些是假设测试，不是用户设备实测精度。
- 训练 worst 是场景/条件加权最大违规；expected 是两级加权RMS，不是通过概率。有限样本通过数不是生产良率。
- 相同候选评价数不等于相同前向/Jacobian工作，不作时钟加速比声明。

## 全部小例结果

表内独立/系统为成对相同64场景；全部16组原名义均合格。

|案例|有界误差|目标|训练代理 初→末|独立通过 初→末|系统通过 初→末|cloud评价|终态|
|---|---|---|---|---|---|---|---|
|AR-local|±0.5%|worst|2.93981e-05→5.14808e-07|44→56|36→49|4|completed/constrained_tolerance|
|AR-local|±0.5%|expected|2.04773e-06→1.90174e-08|44→56|36→49|11|completed/constrained_tolerance|
|AR-local|±1%|worst|6.9672e-05→4.91958e-05|32→30|28→30|4|completed/constrained_tolerance|
|AR-local|±1%|expected|5.90103e-06→3.88871e-06|32→28|28→28|6|completed/constrained_tolerance|
|AR-local|±2%|worst|0.000156235→0.000156185|18→18|13→13|2|completed/constrained_tolerance|
|AR-local|±2%|expected|1.99921e-05→1.87697e-05|18→15|13→13|6|completed/constrained_tolerance|
|AR-local|±1nm|worst|6.06985e-05→3.84289e-05|34→35|29→32|4|completed/constrained_tolerance|
|AR-local|±1nm|expected|4.89767e-06→2.81371e-06|34→33|29→32|8|completed/constrained_tolerance|
|HR-8layer|±0.5%|worst|0→0|64→64|64→64|1|completed/constrained_tolerance|
|HR-8layer|±0.5%|expected|0→0|64→64|64→64|1|completed/constrained_tolerance|
|HR-8layer|±1%|worst|0→0|64→64|64→64|1|completed/constrained_tolerance|
|HR-8layer|±1%|expected|0→0|64→64|64→64|1|completed/constrained_tolerance|
|HR-8layer|±2%|worst|0→0|64→64|64→64|1|completed/constrained_tolerance|
|HR-8layer|±2%|expected|0→0|64→64|64→64|1|completed/constrained_tolerance|
|HR-8layer|±1nm|worst|0→0|64→64|64→64|1|completed/constrained_tolerance|
|HR-8layer|±1nm|expected|0→0|64→64|64→64|1|completed/constrained_tolerance|

小例结论：AR ±0.5% 有明显有限留出改善；1%/2% 时训练下降不能保证通过数改善，若干 expected/worst 结果反而下降，全部保留披露。HR 各档原已全过，两个有限目标本来为零，新法1次cloud评估保持设计不变；无可证通过率增益。

## 0nm退化负例

同原零厚度压力例采用[0,225]nm边界，±0.2%及±2%，新worst/expected四次真实求解均保留非零、原名义合格设计；未把0nm/4%反射率的低线性范数方案推荐。四次输入、处方与摘要见[零厚度压力例数据](nominal-preserving-data/zero-bound-summary.json)。
单测还强制SLSQP返回“success但0nm违规”的试探：该点不成为incumbent，最终partial/constrained_nominal_rejected而非假success。线性诊断/旧robustness_only仍保留，不被偷偷换成有限目标。

## 原89层四窗

保留原材料模型、89层、同六个预声明优化变量，全部89层扰动；训练12场景、±0.5%有界独立相对误差，预算25cloud/20迭代，最终21cloud因迭代上限返回partial。未用新holdout调参。
完整请求估计12,552,836,864字节，超过正式256MiB限制；已保存明确拒绝，未提高默认上限或隐式删点。本轮因此明确采用稀疏训练、单独全原名义与细网格流式验收，不冒充完整网格直接求解能力。

训练worst：0.00262701426→0.00103605605，下降约60.56%；partial/iteration_limit，21次cloud评价。cloud指一次完整场景云候选评分，不是单次光谱或完整优化器迭代。

|名义证据|初态|候选|条件数|
|---|---|---|---|
|原1nm×25角全四窗|True|True|184600|
|独立细网格：visible0.1nm、49角；IR1nm|True|True|529396|

所有IR仍按原R<0.03严格验收，visible仍R≥0.99，没有加安全余量。细网格通过也非连续域证明。

|成对留出模型|初态通过/16|候选通过/16|初态worst违规|候选worst违规|初态P95|候选P95|
|---|---|---|---|---|---|---|
|independent|0|0|0.00365712199|0.00374179596|0.0026591307|0.00290752716|
|common_mode|0|0|0.014608877|0.0127731199|0.0140131363|0.0121878518|

89层结论以全部模型和通过数一起判断。训练代理下降、原名义保持并不代表已提高独立有限误差通过概率，更不代表真实生产良率。16样本/模型不足以作精确统计收益判断。
candidate_passes_nominal_audits字段只表示本次原网格+细网格名义资格，manufacturing_improvement_established=False；不表示制造通过概率已够用。

## 公开数据、复现范围与适用域

- [公开数据导航](nominal-preserving-data/README.md)列出本次实际发布的汇总、CSV、预声明计划、请求、留出系数及候选处方。未复制开发源码、执行脚本、日志、内部路径或源码hash库存。冻结材料请求中必需的完整性字段保留。
- [全部小例汇总](nominal-preserving-data/small-matrix-summary.json)和[CSV](nominal-preserving-data/small-matrix-comparison.csv)包含所有16组，不仅最好者；[小例请求](nominal-preserving-data/small-experiments.json)和[独立留出系数](nominal-preserving-data/small-holdout-coefficients.json)提供数值输入。
- [89层汇总](nominal-preserving-data/large-summary.json)保存原网格/加密名义与两类逐样本留出；[训练请求](nominal-preserving-data/large-new-request.json)包含处方/冻结材料/12训练场景；[候选与工作量](nominal-preserving-data/large-candidate-and-work.json)提供可独立物理复算的最终处方、终态和调用计数。
- [重放摘要](nominal-preserving-data/physical-replay-summary.json)：开发实现中的22份最终结果（16矩阵、4零厚度负例、89层与CLI）通过冻结原请求身份、允许编辑范围与真实物理重放；这是开发测试记录，不是目标主机验收或生产认证。原始大体积逐条件result未在此复制，不能把汇总称为完整开发日志。
- 优化前计划和实际系数均保留。需要重新运行优化器时必须使用相应开发实现；仅公开17e0c4d基线尚不包含这次新策略，因此本研究资料不宣称目前可用公开软件一键重跑。固定处方及有限误差物理值可按保存的材料、原目标、系数独立复算。
- 与前轮±0.2%/256小例或±0.2%/16大例相比，本轮误差档、训练场景和求解策略已改变。两轮不是只变一项的匹配A/B，不能把跨轮数字直接归因为新算法优势。本轮内baseline/candidate使用成对固定留出。
- 本轮只有厚度误差、固定材料/层拓扑；未校准实际蒸发/监控相关性、n/k变化、空间非均匀或吸收。16样本/大例模型不能作为工程良率估计。
- 原始论文、实物/仿真/通用优化迁移边界沿用[方法研究](robust-methods-and-process-tolerances.md)与[来源索引](SOURCES.md)，不把文献参数当用户设备实测。
