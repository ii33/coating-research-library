# 作者范围自查与停止说明

日期2026-10-02；版本T07-r2-v0.1.0。结论implementation_ready_validation_pending，不标accepted或production-qualified。

| 范围 | 证据 | 结果 |
|---|---|---|
| 条件测量算子与硬件未知 | reports/01、data/measurement_contract.json、measurement.py | 已实现受限单层synthetic算子，拒绝未支持合同 |
| 相位基矢与数据坐标 | reports/02、test_reference、独立窄核查 | 明确p负号、法向极限、圆周差、ρ协方差与混合C矩阵 |
| 尺度化白化、SVD与nuisance | reports/03、identifiability.py、小算术检查 | 成立于报告固定Σ/局部条件；不提供秩亏伪协方差 |
| 局部/全局反例 | reports/04、diagnostics.json | 局部rank2仍有精确厚度别名；合成留出可区分该对 |
| 条件观测比较 | reports/05、保存的9个小场景 | 不同噪声/行数/成本明确，未声称设备排名 |
| 完整批量算法 | batch_driver.py、batch_plan_receipt.json | 默认plan_only；339,552启动任务not_run_awaiting_device |
| 必要小测试 | verification/unit_tests.txt | 19项通过；其中6项为reader拒绝/完整性分支 |
| 最小driver路由 | verification/tiny_driver | 4启动任务，只核路径、不核覆盖/性能 |
| 一次独立窄核查 | independent_phase_dimensional_check.md | GPT-6 Luna相位/量纲核对，非完整指定链 |
| 来源/合法原件 | 6原始来源、local_source_archive_manifest | 已读范围有限如实记载；1份明确CC Attribution PDF仅本地 |
| 图与reader | 2组原创PNG/SVG、index.html | 图已逐张视觉检查；HTML资源/链接由脚本检查 |
| 外部范围 | 原始outside_before及freeze时复查 | 只接受零变化或明确逐hash归因，不能重设baseline |

## 保留的失败与修订

初始rank绝对阈值10⁻¹⁰误把法向ρ浮点差分噪声判为rank1。原始失败日志不删；在公开h/2、2h检查与数学法向极限下，将默认绝对阈值修至10⁻⁸，所有结果、测试与报告更新。它是数值诊断阈值，不是普适精度标准。

窄核查发现circular_delta文档的半开端点不完全符合np.angle有符号零行为。实现物理相位正确；作者仅把docstring改为±π同一圆周端点，独立原始核查记录保留，不启动新审核循环。

## 未完成

真实设备/测量硬件接口、材料状态和工艺校准、真实协方差、背面/散射完整反演、多层/各向异性、真实CI覆盖率、完整批量运行和性能均未验证。DeepSeek执行、Seed Pro完整独审、Sol完整算法复核未实际完成，其机器角色状态pending/not_run。不会因一次窄查或19个小测试提升生产资格。

停止在本地freeze与精确receipt，不修改根规划，不发布/上传/push/deploy，不启动下一手交或用户电脑。
