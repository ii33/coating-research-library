# 05 参考算法、完整验证计划及接口合同

## 1 新代码的接口层级

| 接口 | 已实现输入 | 返回与失败行为 |
|---|---|---|
| flux_directional | x,n,s,n_s及各方向导数、指数与幅度 | 光滑前侧导数；角边界null；严格背面0 |
| shadow_limits / event_map | 固定y=0正厚slab、仿射轨迹 | 全部两边事件、活动面、时间Jacobian、分支状态 |
| evaluate | 单一源节点、Scene、平滑求积阶数 | I、7列光滑/事件/总Jacobian；未决状态梯度null |
| classify_ray | 同族单一时刻和板局部不确定界 | 原字节有理求交器的blocked/clear/unknown |
| exact_value_gradient | 条件光滑分支 | 闭式原函数Dual求导；拓扑/近合并/unknown拒绝 |
| offline_read | 严格合成合同及显式允许标志 | 正权离散源积分；不推断连续源收敛，不接纳测量模板 |
| device_driver | 冻结计划或外部显式授权计划 | 默认只打印计划；高算量路径从未执行 |

七列量纲随参数表声明。将总Jacobian传入T01去干扰可观测性诊断前，需要堆叠多个真实观测、正确单位、噪声协方差及干扰参数；这里不重新执行T01反演。

## 2 算法步骤与停止条件

对本固定族：

1. 完整检查SI数值、源/板/目标z的严格顺序、正半宽、正幅度、窗口内非负仿射源率和所有门槛
2. 在near/far两面计算左右影边投影，选择min/max；并列即标topology_switch_unresolved
3. 解析计算候选时刻并排序；检查横截速度、端点距离、两事件间隔及外部几何不确定界
4. 从窗口减去遮挡区间；原函数计算名义可见积分
5. 仅在所有门控通过时，在可见开段内积光滑导数，加每个窗口内部事件的 [f⁻−f⁺]t_p；两类分开存储
6. 未决时返回null梯度。若给影边包络，另求非负积分条件上下界；不把区间中心变成“最可信”梯度
7. 连续源、空间见证、参数扰动和硬网格诊断在显式driver中进行，保留每个节点/分支失败，不自动放宽门槛

复杂度：每源节点的解析事件发现O(1)；分段Jacobian约O(N_q P)，P=7。N_s源节点、N_x见证点、N_case参数情景的完整计划相乘。硬网格值与朴素FD仅用于展示数值风险，不作为梯度真值，其成本O(N_s N_x N_case N_t)。流式time_chunk限制内存，不假装消除总工作量。

## 3 为什么没有通用事件扫描器

任意周期c(t),Q(t)及多个厚板需要完整候选guard、可靠根隔离和有效约束判断。一个初步工程方案必须满足：

- 每个时间区间有可验证的几何/guard范围，只有整区间排除零时才能安全丢弃
- 若区间含零，利用导数包络、单调性或区间Newton隔离根；普通端点同号不能排除两个内根
- 保留根簇、面交会、共面、角度截断及速率门控的事件身份，按总可见性左右极限确定跳变
- 遇到无法分离的根簇、相切或预算耗尽就返回unresolved；不增大epsilon掩盖问题
- 对每个已隔离根给时刻区间及几何状态，积分上下界要随该区间传播

这些是后续接口要求，**本包没有实现任意刚体/CAD的严格区间根隔离**。本族之所以可靠枚举事件，是代数结构允许直接列出两个边界，不是因为任何固定时间网格“足够密”。

## 4 已写完整、但未执行的高算量计划

`data/device_validation_plan.json` 默认execution_mode=plan_only，execution_authorized=false，device_label=null。线源半宽0.12 m固定，65个横移见证，源节点32/128/512，Gauss-Legendre与等距中点两族，光滑分段32/64阶；硬时间网格4096/8191/32749点，基线及七轴正负扰动共15情景。

代码已包含循环、参数扰动、分块硬积分、完整事件梯度、源级比较、平滑阶数比较、两源族比较、分支状态、预算停机、检查点、输入hash和结果receipt。预估约59,031,947,520次核求值，**这是静态工作量估算，不是已跑射线数或耗时承诺**。当前设备授权未恢复，不执行。没有缩小原精度计划后假称高精度替代验证。

差异分别用于值和按参数尺度缩放后的Jacobian；满足请求容差仅标comparison_within_requested_tolerance，不能当作严格误差界。朴素硬网格FD单独标trusted_gradient=false。任何节点未决，相关聚合梯度保持null。上游真实数据、完整物理资格仍不由此验证计划授予。

恢复设备授权之后，需复制计划到独立位置，明确新的执行授权、设备标识、工作预算和输出目录，再使用显式 `--run`。冻结默认计划不被自动改写；输出路径必须在包外且全新。工具中的授权字段是执行声明和防误启动开关，不代替对用户实际授权的核实。当前包内所有说明均为未来步骤，没有发起远程控制或更换设备。

本driver只算**本轮新仿射族**。旧点12及点2的完整二维源计划以原字节 `data/inherited_reexecution_plan.json` 保存作追溯，未接线为这里的运行后端，也未重算。

## 5 离线读者命令

Python3.10+、NumPy1.24–2.x。在ZIP解压后的根目录执行：

```sh
python -B verification/reader_check.py --check
python -B -m unittest discover -s verification -p 'test_small.py' -v
python -B models/run_examples.py
python -B models/offline_read.py data/synthetic_contract.json --allow-synthetic
python -B models/device_driver.py
python -B reviews/author_replay.py
```

均默认只读；不运行高算量driver，不覆写冻结证据。故意拒绝的两个命令是 `python -B models/offline_read.py data/measurement_template.json` 与 `python -B models/device_driver.py --run`，退出码应为2。`run_examples --output` 是明确的作者写出模式，不用于读者完整性校验。

`reviews/independent_checks.py` 保存唯一初始审查的可追溯脚本，默认独占新建结果文件，已有初始证据时拒绝写出；如需重放必须在临时副本安排独立输出，不要在冻结包执行。修复后的读者入口为author_replay与unittest。

## 6 包边界和结果含义

运行时只导入包内models和frozen副本。依赖复制hash逐项验证；provenance中的原项目相对位置仅用于溯源，不是运行依赖。公开reader包含原创报告、合成数字、图及参考代码；第三方全文只本地独立留档，不在允许列表。

离线HTML内嵌CSS和PNG，不需要服务器、远程字体或JavaScript。结构/内链/资源检查与浏览器排版检查分开：本轮三张PNG实际查看，HTML浏览器layout未验证，不重试已拒绝的socket权限。SHA-256证明相对完整性，不是作者身份数字签名。
