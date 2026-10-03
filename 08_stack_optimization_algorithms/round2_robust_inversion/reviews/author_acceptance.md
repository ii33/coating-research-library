# T08作者自查与本地冻结边界

状态：implementation_ready_validation_pending。不是生产acceptance或完整模型审核链。

## 验收映射

| 要求 | 证据 | 结论 |
|---|---|---|
| 数据、校准/先验、候选模型分账 | inversion.py、报告02、test_penalty_not_robustified | 小型正确性通过 |
| 硬调用预算、多解、失败保留 | Ledger/fit_one/multistart；diagnostics两别名；tiny_final | 小型正确性/路由通过，有限搜索无全局证书 |
| 剖面重拟合 | profile、test_profile_refits_free_parameter | 正确执行路径；tiny低端达到局部ftol/xtol，高端预算耗尽未收敛保留 |
| 留出相关误差/参数不确定度声明 | heldout、报告04 | 固定参数高斯plugin，覆盖未验 |
| 条件信息与nuisance | design、focused tests、独立窄核查 | 公式/单位小检查通过 |
| 相关噪声/精确偏置/色散失配负例 | diagnostics.json、两幅原创图 | 合成反例已执行 |
| 高算量先写driver且plan_only默认 | batch_plan_receipt；163584启动/196391832调用上限 | 完整代码已备，重型执行未跑 |
| 上游不改、独立reader | frozen_dependencies、outside、manifest、隔离receipt | 最终以receipt逐字节结果为准 |
| 原始资料合法本地隔离 | source_registry、local_originals_manifest、allowlist | 2份官方预印本PDF+派生提取文本不进入reader |
| 可读性 | PNG已直接查看；HTML静态链接检查 | PNG清晰；Chromium受本地IPC限制，两次尝试均未完成，未声称桌面/移动浏览器验收 |

## 自查更正与限制

初始通用线性单元测试把记录写成空字典，触发观测计账的kind要求；修正测试fixture为非光学d_geo坐标后通过。此问题没有改变光学核。完整driver训练角从预开发0°调整为10°，使允许±0.5°偏差始终在冻结核域内；未用角度裁切掩盖拒绝。加入synthetic-only输入护栏后用新tiny_final目录复测，不覆盖初始tiny_driver历史。

18项模型/算法小测试加4项清单负例构成最终22项测试；单位测试控制台与隔离回执为实际结果。一次GPT-6 Luna只查相关条件信息及nuisance/尺度，没有扩展成多轮形式审核。作者负责其余实现/理论自查；DeepSeek执行、Seed Pro、Sol完整链未运行。

核心限制：真实材料、用户仪器、噪声、校准与重型设备验证未知/not_run；局部Gaussian设计不等于Huber统计信息或完整EIG；先验不能冒充数据；模型差异不自动恢复物理参数；有限簇/剖面无唯一性和覆盖证书。额外厂家手册由独立任务处理，本轮不吸收未审读结论。

止于本地freeze，无push、上传、部署、外部分享、硬件实验或用户电脑改变。
