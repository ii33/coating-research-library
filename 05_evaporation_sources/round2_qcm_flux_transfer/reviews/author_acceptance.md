# 作者自检与冻结接受范围

本轮为algorithmic有界实现，状态implementation_ready_validation_pending。没有真实机台数据，不签署生产接受。用户限定仅一次窄量纲核查，已由GPT-6 Luna完成7个自造小测；没有冒充Seed Pro或指定Sol完整算法审查。

| 请求 | 实现/证据 | 结果 |
|---|---|---|
| 频率/面质量/有限负载单位与漂移 | qcm_flux.mass_areal、mass_frequency_derivative、rate_from_frequency；报告01 | 已实现，小测通过；实际声学适用域未验证 |
| density/Z/tooling/capture分开 | strict schema、actual_unknown、报告01/02 | 无未知值静默默认或生产tooling |
| 归一化源、工件实际面积、各向参数 | point_kernel、geometry_terms；解析积分与投影测试 | 点源有限参数族实现；有限源/碰撞未实现 |
| 原子/分子/团簇/反应气守恒 | species_elements、mixture_from_mass、retained_elements、gas_impingement | Al/Al₂/O₂合成守恒通过 |
| 总率/空间形状/η的不可辨识 | design_matrix、rank_report、fit_source；diagnostics | 秩亏硬拒绝，独立Q行可破尺度退化 |
| 稳健有界拟合/不确定度 | soft_l1有界拟合、conditional covariance、correlated propagation | 已知真值/离群合成通过；不声称覆盖未建模偏差 |
| 反例与数据QA | 60个小测、diagnostics、data_qa | 通过；温漂/遮挡/低信号/unknown反例可复现 |
| 高计算量算法/计划/断点 | validation_driver，heavy_plan，light_driver | 完整实现；heavy与设备验证未运行 |
| 原始来源核查与访问分级 | sources登记、摘要、官方手册视觉核对 | 7条；缺失全文明确标记 |
| 精确manifest/无ZIP reader | freeze_package、reader、freeze_receipt | 在最终冻结时复核完整树与独立临时目录 |
| 不改冻结上游/产品，不push | outside_before/outside_scope_check | 最终按路径/大小/哈希核查，不做Git写入 |

界限：α/ηQ、源形、温漂和z的外部校准不能被本模型拟合成功取代；实际膜密度/n/k/应力、T02 oracle闭合和T03净侵蚀输入仍未解决。没有迭代调用评审去把同一证据刷成通过。读者可检验的通过仅限本包实现与合成检查。
