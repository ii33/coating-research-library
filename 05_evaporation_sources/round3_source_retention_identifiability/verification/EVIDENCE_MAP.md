# 证据对应表

- 第一二轮不重复：reports/01、dependencies/context/03_identifiability_and_uncertainty.md
- 单QCM加平行见证片全局等效：reports/03 §2、data/tiny_results.json/exact_global_ambiguity、对应3项测试
- 方向与尺度的条件诊断：reports/03 §3–5、log_jacobian/rank_report、paired_retention_a
- 归一化/单位/不重复投影：reports/01 §2、KernelTests、一次13项独核结果
- 原始设备与工艺经验：reports/02、sources/source_registry.json及6张来源卡
- 完整T04与哈希依赖：reports/04 §1–2、bridge_t04、data/frozen_dependencies.json、full_forward完整对象相等测试
- unknown、负净沉积、零分母：ContractTests与继承T04 guards
- 双时钟与MXC测量来源：two_clocks、qualify_observation及对应拒绝测试
- 默认计划而非重运行：verification/plan_only_output.json、执行权限拒绝测试
- 轻量无噪声拟合：IdentificationTests.test_fit_noiseless；不等于噪声统计验证
- PNG像素：verification/visual_check.json；HTML布局未验证
- 本地freeze：manifest与release_receipt；ZIP内部不含receipt以免自引用
- 完整模型链、实机资格、连续源认证：全部未完成，不由以上证据推出
