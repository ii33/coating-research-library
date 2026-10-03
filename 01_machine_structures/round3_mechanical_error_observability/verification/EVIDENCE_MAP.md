# 本轮命题与证据

| 命题 | 状态 | 证据与范围 |
|---|---|---|
| C1 实际表面跳动不能直接当轴误差 | primary_reported + engineering_synthesis | M01 Glossary；报告01，不声称标准符合 |
| C2 SO(3)姿态必须同步更新点和法向 | derived + light_verified | 报告02；reference.py；独立四元数及六列差分 |
| C3 play有历史且b为半宽 | derived + light_verified | 报告02；手算路径；不含动力学 |
| C4 TE不能无条件归因单个齿轮 | primary_reported | M04 §2.5；有载荷/方向/中心距条件 |
| C5 高度和源幅度存在严格等效族 | derived + light_verified | 报告03反例A；独立不变式；仅轴线上点源反例 |
| C6 恒速时钟和零相位不可分 | derived + light_verified | 报告03反例B；两列严格线性依赖 |
| C7 非共线已校准高度点方可拆平面位姿 | derived + light_verified | 报告03反例C；斜共线零向量及未知零点反例 |
| C8 相关校准不随样本数独立平均 | primary_basis + derived_example | M05 Appendix A；合成均值方差0.25/0.85，不是实测噪声 |
| C9 病态干扰SVD可能制造虚假信息 | independently_counterexampled + conservative_guard | 独立R3、初次失败与作者重放；当前返回未决，不称严格秩认证 |
| C10 reader不需要父目录/原文 | packaging_verified | 临时仅46允许项的隔离解压和完整轻量复算；以最终receipt计数为准 |
| C11 实机误差/厚度改善解释 | not_measured_not_claimed | 无实机日志；不从合成例推断 |

来源身份与合法原件hash在sources/access_registry.json；先前研究身份与hash在data/input_provenance.json。独立原始失败与最终重放拥有不同内容身份，未覆盖。付费ISO/ASME正文未获得，不作为任何通过判据。
