# T05 首轮范围验收

2026-10-02。结论：优先资料与参考模型包可冻结移交T06；实机资格未验证，正式指定模型审查链未完成，不能写成形式阶段accepted。

## 目标与实际证据

| 原目标 | 交付及定位 | 结果 |
|---|---|---|
| 阻蒸优先研究 | reports/02；结构、热平衡、滞后、容器、速率观测 | 本轮范围完成 |
| 电子枪优先研究 | reports/03；扫束/活跃面/液位/炉床与原厂安全依据 | 本轮范围完成 |
| 十二材料源耦合 | reports/04；data/material_source_matrix.json共12条 | 条件化候选完成，实机参数未填 |
| 分布和质量归一化 | reports/01；models/source_reference.py | 解析与合成检查通过 |
| 拟合/可辨识/留出 | reports/05–06；benchmarks/results | 三类角向/方位留出，负例明确 |
| 不确定度/数值误差 | 400次噪声重复、几何敏感性、面积/口沿加密 | 条件范围通过，不等于物理验证 |
| T02/T03接口 | reports/05；同节点T02核对测试 | 静态核一致；时变API明确未集成 |
| 来源/原文 | 27条登记+逐条摘要；1份CC署名原文本地排除 | 来源范围与权利分开 |
| 图示/复现 | 3幅原创PNG/SVG；脚本和输出文件 | 已生成并逐图目视检查 |
| 异常/下一阶段 | reports/07；OPEN_ISSUES；T06_HANDOFF | 失效与未知未隐去 |

## 执行记录

- 核心单元/不变量：51/51通过，reviews/test_output.txt
- 合成基准：run_benchmarks.py成功，固定种子20261002，全部硬断言通过
- 加密研究：run_resolution_study.py成功；圆盘/舟主案例离散差远小于模型误配，口沿非单调误差如实记录
- 独立窄范围数学/证据核查：GPT-6 Luna xhigh，见independent_source_physics_check.md；两项具体边界问题修复后重跑51项与主基准
- 后续新增的源面积加密脚本是执行方自检，不冒称包含在先前独立源码哈希内
- 发布结构/权利/哈希检查：tests/check_release.py，日志另存；--reader模式不要求原文存在
- 设备连接/实验/真实改机/采购：均未执行

## 形式审查状态

本任务要求的DeepSeek、Seed Pro和完整Sol串联流程不能由当前窄审冒名完成。各未执行项在stage_status.json保持pending，formal_status=awaiting_seed。当前冻结仅表示理论/公开证据/合成实现的有界优先范围完成，适用边界与未决项已足够清楚，可以继续原顺序的资料研究。

## 基线

模型代码SHA256由独立窄审记录；全部交付内容的SHA256见release_manifest.json。根README/ROADMAP/STATE/全局索引由协调者统一更新，本专题仅修改05_evaporation_sources。
