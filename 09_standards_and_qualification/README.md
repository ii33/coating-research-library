# T09 光学镀膜标准与检验规划

版本：T09-r1-v0.1.0；目录查询日：2026-10-02；状态：ready_for_review。首轮通用资料研究、原创规划与合成数值自检完成，未作真实产品测试、认证或完整标准符合性评定。原始要求定位：00_project/工程科研.txt第13行；承接T08，保持原项目顺序。

## 先看结论

“按某标准测试”不足以形成可放行结论：必须把版本/方法、严酷度、产品阈值、抽样和不确定度决策规则分别写清。目录已核验不表示付费全文已读；实验室认可也要匹配具体方法和能力范围。

本轮发现的关键版本变化包括ISO21254-1:2025、ISO11551:2026、ISO2859-1:2026、ASTM B117-26a及GB/T26332.4-2026。GB/T26332.2/.3-2026已发布但2027-01-01才实施；查询日2015版仍现行。MIL-C-675/14806/48497的所获官方证据为Inactive for New Design，不能泛称现行、取消或被ISO正式替代。缓存/来源冲突均保留，具体见第2章和来源摘要。

## 手册导航

1. [范围与合同基线](reports/01_scope_and_contract.md)
2. [标准目录与版本过渡](reports/02_standards_lifecycle_and_mapping.md)
3. [光学与薄膜计量](reports/03_optical_metrology_and_uncertainty.md)
4. [环境鉴定规划](reports/04_environmental_qualification_plan.md)
5. [附着 耐磨 清洗](reports/05_adhesion_abrasion_cleaning.md)
6. [激光损伤条件与统计](reports/06_laser_damage_test_contract.md)
7. [判定 抽样与合成演示](reports/07_decision_rules_sampling_and_demo.md)
8. [根因与工艺验证](reports/08_root_cause_and_process_validation.md)
9. [执行门槛与证据闭合](reports/09_execution_gates_and_evidence.md)

## 数据与复用

- [62条标准/指导文件映射](data/standards_map.json)：发布、修改/采用、现行/待实施状态，未知条款与阈值保持null
- [66条来源索引](reports/00_source_index.md)；[来源登记JSON](data/source_registry.json)
- [MIL与GB独立目录核对](sources/summaries/official_status_mil_gb.md)；[10项目录冲突](reviews/source_conflicts.json)
- [15项试验矩阵](templates/test_matrix.csv)；[检验计划模板](templates/qualification_plan.json)
- [测试记录](templates/test_record.json)；[条款证据表](templates/clause_evidence_map.csv)；[不确定度预算](templates/uncertainty_budget.csv)
- [12类根因验证矩阵](templates/failure_process_matrix.csv)
- [合成结果](data/demo_results.json)；[合成测量CSV](data/synthetic_measurements.csv)；[粗网格漏谷示意](figures/synthetic_spectral_sampling.svg)
- [自查和限制](reviews/SELF_REVIEW.md)；[验收记录](reviews/acceptance.json)；[T10移交](T10_HANDOFF.md)

## 离线复现

在本专题目录，使用Python标准库：

    python models/qualification_demo.py
    python -m unittest discover -s tests -v
    python models/check_package.py

28项单元/数据检查通过只证明演示与结构按已写规则运行，不能证明标准完整实现。当前模板故意缺少产品和授权方法输入，会阻止结构检查通过；模板不得直接作为执行批准。

需要从已人工核对的来源数据重建目录时，依次运行build_research_assets.py、merge_source_assets.py、enrich_metadata.py；重建空模板运行build_templates.py。这些是离线排版/结构脚本，不会联网更新标准状态，不会操作设备。重新生成后须再次执行演示、自检及哈希生成。

## 边界

本库覆盖一般光学制造质量，未涉及特定武器系统的设计、适配或性能优化。GJB未能获得足够公开官方目录证据，不猜编号，也不据此声称不存在。标准全文、客户合同、真实样品、设备校准和实验室方法能力尚未获得；实际生产和放行需另行闭合。

所有数值示例是合成数据或明确数学定义，非标准严酷度/阈值。无第三方全文存档；不购买、外部咨询、设备操作、产品代码改动或push。原创摘要和报告可分享，第三方原文不得随包分发。全局状态与下一阶段由协调者维护。
