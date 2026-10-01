# 主流镀膜机结构研究

首批专题：行星盘光学蒸发镀膜机  
版本：0.2 首轮资料基线，2026-10-01（UTC）  
状态：首轮理论资料与接口已齐备，建议移交T02；用户实机识别、校准和生产验收未执行

## 本批已形成的结论

1. “行星盘”描述工件运动，不唯一决定沉积方法、齿轮拓扑、离子源类别或控制方式。必须同时画出物料路径、机械传动链、离子束路径和测量路径。
2. 固定外齿太阳轮、直接外啮合、工件与行星轮直连时，绝对自转角速度为 `ωp = ωc + (Zs/Zp)(ωc−ωs)`。太阳轮固定后是加号，不可漏掉载架角速度。
3. 历史案例的120/36、120/37齿及15 rpm仅作待核实示例：对应绝对自转65与约63.64865 rpm；完整位姿闭合分别需要3与37圈公转，即12与148秒。该结果不等于已证明实际膜厚差异的原因。
4. 长闭合周期不能替代有限层时间、启停相位、真实源分布、遮挡、装夹倾斜和时间速率记录。径向平均曲线不能诊断同半径角向不均匀。
5. 进入高精度仿真之前，应先得到可复核的传动拓扑、统一坐标、几何尺寸与逐层时间日志。

## 阅读顺序

- [01 设备分类与典型架构](chapters/01_architectures.md)
- [02 行星盘机器的子系统与工程接口](chapters/02_subsystems.md)
- [03 坐标与运动学](chapters/03_kinematics.md)
- [04 实机识别 参数字典与验证计划](chapters/04_identification_and_validation.md)
- [05 工程选型与维护复标](chapters/05_selection_and_error_control.md)
- [06 结构与坐标示意](chapters/06_structure_and_coordinate_diagrams.md)
- [术语索引](glossary.md)
- [T02移交建议](T02_HANDOFF.md)
- [首轮验收边界](ROUND1_ACCEPTANCE_GAPS.md)
- [证据地图](evidence_map.md)
- [资料登记表](sources/source_registry.json) 与 [可读资料摘要](sources/abstracts/source_summaries.md)
- [待确认案例参数](data/historical_case_unverified.json)
- [运动学独立检查](reviews/kinematics_independent_check.md)
- [阶段缺口与后续工作](stage_gaps.md)

## 使用边界

这是一套可继续累积的首轮理论手册，不是覆盖全部设备的完整教材、设备操作规程或已校准的数字样机。厂家资料用于证明结构与选项存在，不视为独立验证的性能保证；专利用于认识实施结构，不构成可自由实施的法律意见；公开论文的结果限于其试验条件。正文中“建议”“应采集”“待验证”是本研究提出的工程工作项，不是来源已证实的用户设备事实。

资料访问日统一为2026-10-01。下载成功的原始PDF保留在 sources/originals/，仅作本研究存档，不据此假定允许公开再分发。读取或下载失败的资料如实登记，不绕过付费、验证码或访问限制。标准与教材仅登记已核对的官方元数据，不伪称取得全文。

## 读者包验证

运行`python verification/check_initial_release.py --reader`检查本包引用与理想运动学。第三方原始PDF被有意排除，相应本地字节检查明确跳过，登记表仍保留来源与存档校验值。运行复算仅需Python标准库；schema附加检查需要jsonschema。
