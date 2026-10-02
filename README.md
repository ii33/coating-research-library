# 镀膜工程科研长期研究库

本库保存用户原始清单，并把它落实为可延续、可追溯、分阶段验收的工程研究项目。最终报告以工程手册与教材级知识库为目标；T01–T10已覆盖第一轮优先公共资料、理论和合成基础，T01第二轮有限拓扑接口已移交，T02第二轮双覆盖误差预算以部分数值接受状态冻结，独立v0.2求交正确性已有限收口，当前推进三个限定阴影不连续求积案例。正式完整审查、实机校准与生产资格仍未完成。

## 从这里开始

- 原始要求：[00_project/工程科研.txt](00_project/工程科研.txt)；按原始字节保存，校验见 [original_manifest.json](00_project/original_manifest.json)
- 执行顺序：[ROADMAP.md](ROADMAP.md)
- 当前状态：[STATE.md](STATE.md) / [STATE.json](STATE.json)
- T01阶段范围与验收：[00_project/T01_STAGE_PLAN.md](00_project/T01_STAGE_PLAN.md)
- 可机读任务：[00_project/research_tasks.json](00_project/research_tasks.json)
- 需求追踪：[00_project/requirements_traceability.json](00_project/requirements_traceability.json)
- 证据规则：[90_methods/EVIDENCE_AND_CITATIONS.md](90_methods/EVIDENCE_AND_CITATIONS.md)
- 版本与阶段验收：[90_methods/VERSIONING_AND_ACCEPTANCE.md](90_methods/VERSIONING_AND_ACCEPTANCE.md)
- 可复现、实验与算法评测：[90_methods/REPRODUCIBILITY.md](90_methods/REPRODUCIBILITY.md)
- 未决问题：[00_project/clarifications.json](00_project/clarifications.json)

## 十个专题

1. [主流镀膜机结构](01_machine_structures/README.md)；首轮重点：行星盘机器
2. [高精度镀膜机建模与仿真](02_machine_modeling/README.md)；原文未指定子优先项，先完成本专题首轮核心范围
3. [修正板自动设计优化](03_correction_plate_optimization/README.md)；原文未指定子优先项，先完成本专题首轮核心范围
4. [镀膜材料与基片材料](04_coating_and_substrate_materials/README.md)；首轮重点：ta2o5、zns、tio2、ybf3、sio2、mgf2、al2o3、h4、ge、cu、cr、al、基片zns、基片ge、基片k9、基片znse
5. [蒸发源特性与材料耦合建模](05_evaporation_sources/README.md)；首轮重点：阻蒸、电子枪
6. [各类光学薄膜与应用](06_optical_coating_families/README.md)；首轮重点：近红外、中红外、多光谱
7. [薄膜设计理论](07_thin_film_design_theory/README.md)；原文未指定子优先项，先完成本专题首轮核心范围
8. [膜系设计优化算法](08_stack_optimization_algorithms/README.md)；首轮重点：高精度的高性能优化算法、快速求解的近似算法、方便不停迭代的算法
9. [生产标准、环境与损伤试验](09_standards_and_qualification/README.md)；原文未指定子优先项，先完成本专题首轮核心范围
10. [离子源特性与生产参数优化](10_ion_sources/README.md)；首轮重点：考夫曼离子源

## 执行原则

1. 按原文大项目顺序推进。每个大项目先完成明确优先项，验收后进入下一个；所有大项目首轮完成后，才回头补充扩展。
2. T01–T10第一轮优先公共资料、理论和合成基础已覆盖；当前为T02第二轮源/时间求积误差控制进行中；已交付增量仍为frozen_bounded_partial。第一轮基线保留不变，实机与产品资格需独立证据。
3. 每个阶段产出可复用报告、来源摘要、数据/模型接口及未决问题，不以无限穷尽文献作为完成标准。
4. 工程结论必须注明证据、条件、单位、不确定度和验证状态。概念推导、仿真和实测不是同一层面的证明。
5. 合法存档公开许可允许保存的原文；受限、付费或权利不明内容仅存元数据、链接及合规摘要，不绕过付费墙。
6. 用户已确认H4是常见的高折射率材料，YbF3是氟化镱。H4的具体配方/牌号按资料核验，不擅自指定化学式，也不把供应商回复设为研究前置条件；原文ybf3保留，不能改成YF3。单独“研究”一行只作为待澄清项。
7. 当前建库和研究不等于后台永久运行；每次推进以本库的当前状态、证据和验收记录为准。

## 共享资产

- `91_templates/`：研究报告、来源摘要、实验、校准、算法评测、失败案例、阶段验收模板
- `92_glossary/`：术语、原始标记、别名与身份核对
- `93_parameters/`：参数、单位、条件、误差和来源
- `94_experiments/`：实验与校准索引
- `95_benchmarks/`：算法评测索引
- `96_failure_cases/`：失败和反例索引
- `99_sources/`：跨专题来源登记、来源身份和版权状态

研究产物就近放在专题目录内，共享索引链接到它们；不要复制出无法追踪版本的多份证据。

## 首轮复核与第二轮入口

[十专题成熟度地图及有限复核](00_project/FIRST_SWEEP_REVIEW_DRAFT.md)说明现有资产、实用化证据缺口与第二轮停止条件。[T01第二轮冻结增量](01_machine_structures/round2_topology_alignment/README.md)已可带缺口移交；C/I原图准入、最终全网格时间再加密和连续极值仍未完成。[T02第二轮冻结部分结果](02_machine_modeling/round2_dual_coverage_error_budget/README.md)保留侧壁漏挡、源/时间数值未达与混叠反例；[独立v0.2求交修复](02_machine_modeling/round2_dual_coverage_error_budget/correctness_closure_v0_2/README.md)已冻结，保留初次FAIL与修复后局部PASS；原v0.1部分数值状态和求积误差不变，尚不进入T03。

## GitHub发布范围与复核

本私有仓库包括原创研究和合规引用，不包含第三方原文PDF/HTML或完整原始光谱。发布边界、冻结包校验和复算命令见[发布说明](00_project/GITHUB_PUBLICATION.md)。
