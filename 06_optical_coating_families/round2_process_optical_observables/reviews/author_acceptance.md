# 作者自审与需求追踪

状态：implementation_ready_validation_pending。本地实现与小数据验证足以交付此有界研究包；未声称指定模型完整阶段独审、真实材料或生产接受。

| 要求 | 文件/证据 | 本轮判定 |
|---|---|---|
| 仅新目录，不改上游/首轮/root STATE | verification/outside_before.json与outside_scope_check.json | 1097文件未变；7个根规划并行变更有明确归属与SHA256，保留原快照 |
| T05 arrival与T04 net/film state边界 | process_optics.film_inventory、报告01、未知fixture | 已实现，unknown阻断 |
| 四种厚度分开 | thickness输出、test_thickness_types_separate | 已检查 |
| 来源参数代表体系，不伪造实测 | Al派生121点、6来源登记/摘要、conditional fixture | 公共薄膜+合成工艺，限制显式 |
| 完整可运行前向光学 | vendor稳定核、process_optics.spectrum | 已实现，低维条件测试 |
| 测量合同与能量分账 | 报告02、finite substrate/scatter tests | 已检查声明模型 |
| n/d、R-only、漏吸收/散射、bulk误用 | diagnostics与报告03 | 有具体可证伪数值 |
| 批量/灵敏度/不确定度driver | batch_driver、inference、batch_plan_receipt | 全接口实现，完整计划not_run |
| 一次窄量纲/光学检查 | independent_optical_check.md、7独立测试 | 通过；修正reader兄弟目录依赖后重跑 |
| strict schema、机器实例、失败语义 | process_optics.schema.json、8个fixture、data_qa | 55小测试总通过 |
| 图与报告 | 5篇工程报告、3张原创PNG/SVG | 图已实际查看并修正布局 |
| 无ZIP/原文reader、精确允许列表 | reader、freeze manifest、integrity negative checks | 本地自校，非可信签名 |
| 不安排设备/生产标定 | stage_status、device_validation_plan | 均not_run |
| 停止本范围，交T07建议 | T07_ROUND2_HANDOFF.md | 仅建议，不启动 |

## 自审中的实际修正

- 独立窄测试最初读兄弟目录T08所存T07副本；发现会破坏隔离reader后，改用本包冻结核作为单程系数，保留独立Fresnel/往返公式；不把同核自比称独立
- Monte Carlo失效抽样最初仅捕获ValueError，schema负k会抛ValidationError；修正为明确记录该类域失败，并加2抽样负例，不静默丢失
- actual_unmeasured模板清除了继承的合成QCM、入射通量、温度/体吸收值，保持未知，不让模板数值被误读成用户样本
- 流程图框和长标题经过实际图像检查后重新排版；没有用渲染完成代替目视检查

55测试含作者48个小测试和独立7个点检。完整数值批量、设备性能/收敛、实测材料迁移、指定DeepSeek/Seed/Sol阶段审查没有运行。不把测试个数当证据覆盖率或生产门槛。
