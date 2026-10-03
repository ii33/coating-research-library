# 独立窄核查：初始结果与单次静态补充

日期：2026-10-02 UTC  
范围：本轮唯一一次、12 项小公式/接口检查；不修复作者代码、不复审、不运行高算量 driver，不作外部调查。  
结论：**11 项通过，1 项失败。** 初始失败证据完整保存在 `independent_results.json`，该文件未因后续静态补充而改写。  
正式指定的 DeepSeek / Seed / Sol 链：**pending**。本核查不替代、不冒充该链。

## 1. 发现：解析 oracle 缺少近合并事件的梯度门控

级别：中等，接口准入契约不一致；不是已证明的普通光滑分支导数符号错误。

- 位置：初始版本 `models/analytic_oracle.py:22–43`，尤其排序与端点检查后的 `32–34` 行
- 对照：`models/event_reference.py:153` 对事件间距 `<= 2 * event_guard_s` 标为 `event_order_unresolved`；`185–196` 行不返回梯度
- 解析 oracle 已拒绝速度不足、未知几何、投影面并列和端点事件，但初始版本没有事件间距检查

精确输入：默认 `Scene`，只将 `half_width_m` 改为 `1e-11`；源节点为 `0.0`。等价调用为：

```python
sc = Scene(half_width_m=1e-11)
reference = evaluate(0.0, sc)
oracle_value, oracle_gradient = exact_value_gradient(sc)
```

初始结果：

- 两事件时间：`0.9249999999374999`、`0.9250000000624999` 秒
- 时间间距：`1.2500001034254637e-10` 秒
- 所需最小分离门槛：`2e-10` 秒
- `evaluate`：`event_order_unresolved`，`gradient=None`
- oracle：仍返回值 `2.3469959022365128` 和七维梯度
- oracle 梯度：`[-0.44341920732206297, 0.44341920755643827, -0.17736768292882488, 2.3469959022365128, -2.3437518592572815e-10, -15.968749999999996, -4.254317086974336]`

影响：调用方若将 oracle 视为与 reference 使用同一可微准入门槛的校验器，可能在 reference 已声明事件顺序未解析时仍拿到未经相同门控的梯度。这不表示正宽度的理想数学模型不存在分支导数；问题是声明的数值护栏没有统一。

建议作者在独立排序后的事件时间上直接增加相同间距拒绝条件，保留 oracle 的独立公式计算。修复及作者定点重放不属于本次独立复核，不能把初始 11/12 改写为独立全通过。

## 2. 通过项及证据

1. **有限厚板投影**：用标准库 `Fraction` 独立算出源坐标 `0, +3/10, -3/10` 的区间分别为 `[-1/5,1/5]`、`[-13/20,-1/15]`、`[1/15,13/20]`。远侧源需要 near/far 混合活动面，实现一致
2. **正速度事件项**：跳变顺序为入遮挡 `-1`、出遮挡 `+1`；独立公式 `-jump_V * kernel * time_derivative` 与全部七列事件项一致
3. **负速度事件项**：设置 `velocity_m_s=-0.4, x0_m=0.4` 后事件顺序和所有事件项一致；宽度事件项始终负
4. **值和七列梯度**：以标准库标量闭式积分作独立重算，四阶中心差分只作用于已解析的分段积分值；两速度分支均与 reference 和 oracle 相符，容差 `2e-8`
5. **静止**：reference 不发梯度，oracle 拒绝
6. **相切**：`grazing_duration(0)` 的导数为 `None`
7. **精确端点**：`x0_m=-0.23` 时不发梯度，oracle 拒绝
8. **近端点**：`x0_m=-0.23000000002`，首事件距离端点约 `5.000007352595759e-11` 秒，小于 `1e-10` 护栏，双方拒绝梯度
9. **活动面并列**：`source_shift_m=0.08` 时双方拒绝梯度
10. **未知几何**：`shadow_boundary_uncertainty_m=1e-4` 时 reference 为 `geometry_unknown` 且无梯度，oracle 拒绝
11. **时钟与平移混淆**：时钟偏移 `0.13 s` 与目标平移由 `0.03 m` 改为 `0.082 m` 得到相同值和事件；`J_clock = v * J_target`。在当前固定参考时钟源速率 `q(t)` 的模型下，这两参数列无法独立辨识

完整数值见 `independent_results.json`。此处的“通过”只适用于上述有界案例及指定族，不是连续源、任意 CAD、真实设备或严格区间证明。

## 3. 追加授权后的静态核实

父任务随后明确允许读取五个额外文件。本段只读核实，没有调用入口、导入 driver 或启动计算。

- `models/device_driver.py:99–104`：无 `--run` 时只打印 `plan_only_no_execution`、估算与 `not_run`
- `models/device_driver.py:56–59`：即使给出 `--run`，实际执行还须 plan 同时为 `execution_authorized=true`、`execution_mode=explicit_authorized_run` 且有设备标签；输出目录须在冻结包外
- `data/device_validation_plan.json:3–5`：当前为 `plan_only`、`false`、`null`。因此当前默认计划不允许高算量执行
- `models/device_driver.py:1–2,35,96`：明确只属新 affine 族，历史点 2/12 未重跑；receipt 仍保留 `point12_still_partial=true`、`point2_not_strictly_certified=true`、`physical_certification=false`
- `data/inherited_point2_point12_reference.json:15–21`：点 2 基线仍是 `reference_estimated_not_strict_bound`，tight 为 `not_completed_interrupted`，点 12 ion 为 `not_run_awaiting_device`
- `models/run_examples.py:20–26`：输出明确为合成解析样例，点 12 `partial_not_rerun`，点 2 `conditional_envelope_not_strict_certification`，设备 `not_run`
- `models/offline_read.py:7–18,24–25`：仅显式允许的 synthetic 合同可读，不推测真实测量参数，且不宣称连续源收敛

在这些指定文件中，**未发现假称已闭合旧点 12 / 点 2**。没有检查其他报告、旧源或父任务文件，不能将此结论扩大为整库审计。

初始 `independent_results.json` 的 `not_verified` 字段准确记录了计算完成时尚未获准检查 driver / 旧状态文件的情况；本节是稍后获准的静态补充，特意保留初始 JSON 而不覆写历史。

## 4. 执行与独立性说明

- 实际只执行一次 `independent_checks.py`，12 个顶层小检查，耗时约 0.12 秒
- 运行时冻结 mask / rigid 依赖使用惰性占位模块，避免读取未授权源；因此没有验证 `classify_ray` 或冻结几何判定实现
- 独立预期值使用标准库 `Fraction` / `math`；调用被测接口所需的 NumPy 运算保留。值核查仍基于相同物理族的闭式积分，并非完全不同的物理模型
- 初始结果中保存了三个被测源文件的 SHA-256，可区分作者后续修订
- 生成结果后，只把检查脚本的输出模式改为独占新建，防止未来覆盖初始证据，并让近合并检查在 oracle 正确抛出 `ValueError` 时可通过；没有重跑
- 未修改任何作者模型、数据合同、计划、旧状态、父源或报告；只写入本 `reviews/` 下三个获准文件
