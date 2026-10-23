# 名义保护稳健优化 · 公开科学数据

配套[效果报告](../nominal-preserving-effects-20261023.md)。这批资料来自独立开发实现的测试，不代表软件已正式发布、用户已可用、目标主机验收或制造资格。

## 数据地图

| 文件 | 用途 |
|---|---|
| predeclared-plan.json | 小例24训练/64留出、误差档、两目标、种子与预算 |
| small-experiments.json | 全16组小例的正式请求；每组含原处方/目标/变量/冻结材料/训练场景 |
| small-holdout-coefficients.json | AR/HR两案例各自独立与共模64样本系数；同案例八组系数核对相同，去重保存 |
| small-matrix-summary.json / small-matrix-comparison.csv | 全16组训练、名义、留出统计与最终厚度，不筛掉恶化或无增益 |
| zero-bound-summary.json | 四次零厚压力例的请求、最终处方、名义和训练结果 |
| large-predeclared-plan.json | 89层预声明计划：12训练、每模型16留出、6变量、25评价/20迭代上限 |
| large-new-request.json | 89层稀疏训练请求、全部89层误差、冻结材料、系数与原名义策略 |
| large-candidate-and-work.json | 候选真实处方/厚度、终态、完整前向及Jacobian调用等计数 |
| large-summary.json | 原1nm与529396条件加密名义审计；两种误差的逐样本留出违规、worst/P95与通过数 |
| large-holdout-independent/common_mode-coefficients.json | 两类各16个全89层留出系数，固定baseline/candidate配对 |
| large-full-grid-resource-rejection.json | 正式256MiB护栏下的完整请求明确拒绝；未静默删点/场景 |
| physical-replay-summary.json | 开发实现22结果的真实物理重放摘要；case_label是实验标签，不表示此目录含其原始大体积result |

## 复算方法与限制

1. 小例读取small-experiments.experiments中的request；按experiment的AR-local/HR-8layer前缀匹配独立留出系数。它是多案例研究封装，不能把整个文件直接传给单请求CLI。
2. 大例使用large-new-request中的冻结材料和初始设计，candidate-and-work中best_design为优化候选。不要从实时目录更换材料或调整层/目标/厚度；原1nm与加密网格定义在计划/报告中分别保存。
3. 相对误差幅度随当前候选厚度定义，绝对nm为有界幅值。用保存系数分别生成相同潜变量的baseline/candidate；不用重新随机抽样替代。最终R/T按每条原运算符逐条件AND，严格R<0.03在相等时失败。
4. 新策略依赖尚未正式发布的开发实现，公开基线17e0c4d本身不能直接重跑该优化器。数据支持固定处方和误差物理值的独立核查，不是当前公开软件的自包含可执行包。
5. cloud evaluation是一次候选的完整场景云评分；不等于一次TMM调用或一轮优化，也不是端到端速度。历史耗时不用于宣称加速。

原报告及小例/大例摘要原数值保留。此批没有发布开发源代码、脚本、运行日志、内部目录或源码文件hash清单；冻结材料sha256为请求校验所必需，非源码库存。前轮data目录和原始结果不作改写。

所有误差是假设压力测试，不是实际工艺精度。大例名义保持、训练worst下降但两类0/16不变，独立尾部略差；不能据此推荐替换原设计或声称制造良率改善。
