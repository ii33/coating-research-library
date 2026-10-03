# 第二轮复现范围与设备计划

2026-10-02 UTC。本文件的命令是后续复现说明，本次未执行其中任何测试、reader、driver、审查或重任务。现有记录见[证据索引](ROUND2_EVIDENCE_INDEX.json)。先做工作副本，所有生成输出写新目录；不要在冻结源目录重建数据、图片、清单或收据。

## 共同合同

- 每项工作目录为证据索引all_topic_stage_paths中的对应目录；使用各verification/environment.json记录的依赖版本。Python版本要求/库以原README为准，不擅自安装
- 固定输入/代码/配置哈希、种子、单位、层序、测量算子与拟合/留出角色；记录失败和资源，不删失败样本
- 小测试、哈希、独立窄核查、全量数值、实际校准、生产资格是六种不同证据。复现以前的tiny结果不提升后三者状态
- 下列完整设备计划均not_run；其预算是配置或估计，不是实测耗时/内存/加速比。需要另行确定输入、资源和执行授权
- T02 partial、T03净侵蚀不支持、点12参考未运行、tau非严格条件包络、QCM温度/声学/tooling及材料响应缺口原样传递

## T01–T05

| 阶段 | 原有入口及当前有限证据 | 未运行计划及进入条件 |
|---|---|---|
| T01 | README、verification/PRE_REGISTERED_PROTOCOL.md；24项既有测试 | C/I原图门槛、完整网格时间加密与连续极值仍缺；未设新一轮执行任务 |
| T02 v0.3 | python -B models/device_driver.py 默认仅计划；verification/device_validation_plan.json | 默认2点8个reference jobs，固定网格估计2450612480射线。selected/diagnostic_13/area_236各域不可混称。每点work cap 1e11、wall 86400 s；QUADPACK警告/未知速率/未解支集/预算触发须保留unresolved |
| T03 | python -B models/device_runner.py 默认仅计划；verification/device_validation_plan.json | training/independent_holdout/area_validation合计2100409824射线。补齐真实输入SHA、device_ready和目标；按点分块保留完整source/time，内存/GPU性能未测 |
| T04 | python models/calibration_driver.py --mode plan；verification/device_validation_plan.json | 100000次八行加权拟合重采样。实际工艺/温度/光谱/历史匹配与完整协方差未补齐；默认合成输入不能产出物理校准 |
| T05 | python models/validation_driver.py 默认plan；reports/04_results_reproduction_and_limits.md | 1000重复×120窗口×4情景=480000拟合、约63360000频率样本。现有light只有12窗口；单重复分位不能称95%覆盖。resume要求配置/代码哈希相同 |

T02已记录的显式设备命令：OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -B models/device_driver.py --run --workers 2 --output <new-device-results>。本次不运行。

T03高保真入口需--execute、新输出目录及具备真实输入哈希的配置；恢复用相同版本/配置与--resume，取消用--cancel-file。并行另需--workers与--allow-parallel，不推定当前设备性能。

T05 heavy分支要求同时--mode heavy、--execute、--acknowledge-synthetic-only和新输出目录；设备/实际校准状态仍独立于heavy合成状态。

## T06–T10

小测试通用形式为：PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=models python -m unittest discover -s tests -v。T10数值命令另可固定OPENBLAS_NUM_THREADS=1。它们不是本次执行记录。

### T06 工艺到光学

- 默认：python models/batch_driver.py；reader：python models/reader.py --directory .；数据QA：python models/data_qa.py
- 全计划显式入口：python models/batch_driver.py --execute --output <new-local-json>
- 441个独立光谱点×15角度/偏振条件，1000次MC；估计6674535 wavelength evaluations，额外求解/求积不在该估计内
- 输入/计划：data/batch_plan.json、verification/device_validation_plan.json。需真实膜/仪器与协方差；当前只有给定合成输入不确定度
- 注意：最终61项载荷继承55项tiny证据，早期59项隔离回执不冒充最终重跑；本次只核对最终载荷哈希

### T07 可辨识性

- 默认：python models/batch_driver.py；reader：python models/reader.py --directory .
- 全计划显式入口：python models/batch_driver.py --execute --max-jobs 339552 --output <new-directory>
- 27真值×4观测模式、12起点、61 profile点、200 MC；339552起点任务、135820800估计nfev。有限差分Jacobian增加光学调用，nfev并非精确call计数
- 计划：verification/batch_plan_receipt.json。现有tiny只4 starts；实际协方差、零偏与全局别解均需单独验收

### T08 稳健反演

- 默认：python models/batch_driver.py；独立reader：python models/reader.py --directory . --isolated
- 原tiny路线：python models/batch_driver.py --tiny --execute --max-jobs 3 --max-forward-calls 191 --output <new-directory>
- 全计划：python models/batch_driver.py --execute --max-jobs 163584 --max-forward-calls 196391832 --output <new-directory>
- 163584起点任务，拟合196300800次+诊断91032次=196391832观测向量预测调用上限；一次call为整组观测向量，不是一条光学波长计算
- 计划：verification/batch_plan_receipt.json。原tiny最终176次调用，主拟合收敛、高端profile耗尽45次预算；不可引用all_attempts_converged替代端点/整个profile验收
- 无并行/长程可靠性/重试恢复验收；拒绝覆盖已有输出。真实偏差/失配、留出与统计覆盖未验证

### T09 证据合同

- 例子入口：python models/evidence_contract.py --examples；原包核对：python models/freeze_package.py --verify
- 84项冻结包、81项独立reader范围分开；无重型设备driver或实际规范符合性执行的声明
- 真实使用需仪器/协议、受控校准、原始样本、合法方法正文、不确定度/相关结构、独立验证及已确定决策规则。浏览器视觉/交互未验证

### T10 离子观测与材料响应

- 默认：python models/validation_driver.py；tiny：python models/validation_driver.py --mode tiny_synthetic
- 离线记录：python models/validation_driver.py --mode offline_packet --input <packet.json> --raw-root <raw-directory> --out <new-result.json>
- 全合成：python models/validation_driver.py --mode full_synthetic --execute-deferred-synthetic --wall-budget-s 1800 --out <new-result.json>
- 216条件×200重复，最多43200逆解、每次最多100迭代；1800 s预算在求解之间检查，可超出一个正在运行的solve，不是硬实时截止
- 计划：verification/deferred_plan.json；实际协议/局部电位/荷态/快中性/杯校正/膜响应均待数据。没有实时hardware adapter，不能向真实设备下发命令
- **完整包审计不是独立reader验证**：python models/audit_package.py --verify需原ZIP、外置freeze receipt、21个上游兄弟文件及全库outside baseline。ZIP83项不含外置receipt；复制后直接在孤立目录运行此命令并不具备它的依赖合同
- 静态核查还发现一个冻结MXC来源依赖含私有身份。原ZIP不允许公开，删掉该依赖也会破坏原清单及可能触发缺文件异常。HTML/图形可读投影与完整可复現审计必须分开；此次不生成新派生发布包

## 设备执行前的最低交接

1. 选定目标输出、精度/性能容差及设备资源，不以玩具阈值替代用户指标
2. 明确合成验证、实际数据验证和实机动作的不同授权；离线driver存在不授权硬件操作
3. 锁定输入/版本/预算/停止规则并使用新输出位置，保存实际CPU/库/峰值内存/耗时
4. 按原计划保留未运行、预算耗尽、告警、歧义和失败，不据结果方便而追加预算或删除bad cases
5. 完成之后另形成执行收据；任何新结论不回写旧freeze。当前没有上述执行正在运行
