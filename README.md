# 镀膜工程科研长期研究库

本库保存用户原始清单，并落实为可延续、可追溯的工程研究项目。T01–T10首轮、第二轮与第三轮有界研究范围均已本地收口。本批统一发布第二轮尾批、第三轮十个完整reader载荷与MXC原创派生；第四轮未启动。正式模型审查、实机校准、完整数值验证和生产资格仍未完成。

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
2. 第二轮与第三轮已按原顺序完成有界本地研究。阶段收口不提升证据等级；第四轮未启动。
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

[十专题成熟度地图](00_project/FIRST_SWEEP_REVIEW_DRAFT.md)保留首轮有限复核边界。第二轮增补入口：

- [T02v03](02_machine_modeling/round2_dual_coverage_error_budget/quadrature_control_v0_3/README.md)
- [T03R2](03_correction_plate_optimization/round2_dual_coverage_optimizer/README.md)
- [T04R2](04_coating_and_substrate_materials/round2_material_response_contract/README.md)
- [T05R2](05_evaporation_sources/round2_qcm_flux_transfer/README.md)

## 计算验证与发布准则

有界离线算法与批量driver已写出，重型精度、性能和资源验证待用户安排设备；T10实时硬件通信适配因协议和授权缺失未实现。当前小测试和合成结果只用于实现核查，不代表生产验收。完整与未运行任务分开记录，真实输入unknown及partial状态不掩盖。

先在云端积累并冻结成果，攒成有实质进展的批次再统一上传；不逐个小修订提交。T06–T10已本地冻结，后续发布另行进行。T10公开完整包因私有依赖及全库审计耦合阻塞，原冻结包不回写。

## 第二轮本地收口入口

- [综合结论与成熟度](00_project/SECOND_SWEEP_SYNTHESIS.md)
- [冻结证据、复现范围与设备计划索引](00_project/ROUND2_EVIDENCE_INDEX.json)
- [37条历史配方交叉引用](00_project/PRIOR_RESEARCH_CROSS_REFERENCE.md)，不重复导入旧配方
- [第三轮优先级草案](00_project/ROUND3_PRIORITY_DRAFT.md)，未执行
- [候选发布计划](00_project/ROUND2_PUBLICATION_PLAN.md)，无上传且不等于发布批准

T06–T10入口分别为[工艺光学](06_optical_coating_families/round2_process_optical_observables/README.md)、[可辨识性](07_thin_film_design_theory/round2_measurement_identifiability/README.md)、[稳健反演](08_stack_optimization_algorithms/round2_robust_inversion/README.md)、[证据合同](09_standards_and_qualification/round2_traceable_validation_contracts/README.md)、[离子观测](10_ion_sources/round2_observable_material_response/README.md)。


## 第三轮完整入口与本批发布

[第三轮综合](00_project/THIRD_SWEEP_SYNTHESIS.md) · [精确证据索引](00_project/ROUND3_EVIDENCE_INDEX.json) · [批次发布说明](00_project/CONSOLIDATED_PUBLICATION.md)

- [T01R3](01_machine_structures/round3_mechanical_error_observability/README.md)
- [T02R3](02_machine_modeling/round3_pose_occlusion_sensitivity/README.md)
- [T03R3](03_correction_plate_optimization/round3_event_aware_trust_region/README.md)
- [T04R3](04_coating_and_substrate_materials/round3_bounded_material_response/README.md)
- [T05R3](05_evaporation_sources/round3_source_retention_identifiability/README.md)
- [T06R3](06_optical_coating_families/round3_bounded_stack_response/README.md)
- [T07R3](07_thin_film_design_theory/round3_observation_set_exclusion/README.md)
- [T08R3](08_stack_optimization_algorithms/round3_budgeted_candidate_sets/README.md)
- [T09R3](09_standards_and_qualification/round3_unresolved_evidence_acceptance/README.md)
- [T10R3](10_ion_sources/round3_ion_state_evidence_gate/README.md)

[T10R2独立portable派生](publication_packages/t10_round2_portable_v1/README.md)不沿用原冻结包身份。历史文件中的未发布/候选/下一题未启动是当时记录，当前状态以根STATE为准。

## 2026-10-03 文献增量与当前同步范围

[当前证据索引](00_project/CURRENT_EVIDENCE_2026-10-03.md)：Oliver全文已核验，新增Shakoury辅助证据，Lehan正文仍待补；CPU/GPU主机复现包待取得当前文件读取授权后另批同步。
