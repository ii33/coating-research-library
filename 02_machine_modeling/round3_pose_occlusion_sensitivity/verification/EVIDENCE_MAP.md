# 要求与证据映射

| 要求 | 主要文件 | 可重放入口/资格 |
|---|---|---|
| 位姿与法向同时变化 | report01、event_reference、冻结T01模块 | test_rotation_normal_and_point |
| 光滑段与事件项分开 | report02/03、algebraic_results | test_event_primitive_jacobian、test_event_signs |
| 正厚度与活动面 | report03、shadow_limits | test_far_source_active_face、独核Fraction投影 |
| 相切/端点/近合并拒绝梯度 | report02、event_map、oracle | test_grazing、test_endpoint_rejected、test_oracle_close_events_rejected |
| UNKNOWN不可静默透明 | 原字节robust_mask、report04 | test_rational_near_boundary_unknown、test_unknown_no_gradient |
| 输入不确定性与数值误差分开 | report04、conditional_unknown_envelope | 小型边界位移见证；不是严格区间认证 |
| 运动/源/时间混淆 | report04、algebraic_results | test_clock_null、test_translation_gauge |
| 朴素FD反例 | run_examples、figure03 | 16节点阶跃解析导数−1与伪零对照 |
| 完整高算量算法先写 | device_driver、device_validation_plan | 默认plan_only，--run拒绝；heavy路径not_run |
| 旧点12/点2状态不提升 | inherited_point2_point12_reference、stage_status | 原字节hash；未执行旧重算 |
| 只必要小验证与一次独核 | unit_tests日志、independent_results、repair_replay | 31测试；初始独核11/12；作者修复3条件 |
| 单包可复制依赖 | frozen_dependencies、reader_manifest、release_receipt | 独立解压五条轻量命令及两条负向CLI |
| 合法原文隔离 | source_notes、local_originals_excluded、allowlist | 五项主来源；原文/抽取文本全排除 |
| 图片和阅读版 | 三PNG、reader.html | PNG像素已查；HTML布局未验证 |
| 不启动下一题/上传 | T03_ROUND3_HANDOFF、stage_status | local freeze，候选未启动 |

正式指定模型链未实际执行，不存在将以上有界证据换算为DeepSeek/Seed/Sol接受签署的步骤。
