# 06 输入输出契约与复现操作

本库代码是小型、透明的数值参考，不是现有镀膜仿真产品的修改。它用Python与NumPy复现章节中的单位、解析极限、积分和失败反例，不需要GPU、商业求解器或大型安装。任何真实机台适配都应保留配置、来源、测量量和不确定度。

## 1 文件之间的对应

| 文件 | 用途 | 实现范围 |
|---|---|---|
| `models/deposition_reference.py` | 正向核、刚体链、时间求积、圆盘源/表面与矩形遮挡 | 章节01–03明确子集 |
| `models/run_case.py` | 从JSON配置计算并导出CSV/JSON | 点源/圆盘源，环/平面或球面盘，固定矩形遮挡，谐波速率 |
| `data/synthetic_case.json` | 可直接运行的最小合成例子 | 不是设备默认配置 |
| `data/measurement_template.json` | 实机参数和测量记录模板 | 未知值保留null，不可直接运行 |
| `verification/run_verification.py` | 硬断言解析/边界测试 | 失败返回非零退出码 |
| `benchmarks/run_benchmarks.py` | 光滑/阴影/扩展源/面积/混叠/齿比/可辨识演示 | CSV、JSON可独立检查 |
| `benchmarks/plot_results.py` | 对既有CSV画图 | 可选，需要已安装matplotlib |
| `verification/check_release.py` | 交付完整性、来源、JSON和本地链接检查 | 不等于物理验证 |

## 2 运行步骤

从`02_machine_modeling`目录运行：

```bash
python verification/run_verification.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python benchmarks/run_benchmarks.py
python models/run_case.py data/synthetic_case.json --output benchmarks/results/example
python verification/check_release.py
# 可选图示，核心计算不依赖matplotlib
MPLCONFIGDIR=/tmp/t02-mpl XDG_CACHE_HOME=/tmp/t02-cache python benchmarks/plot_results.py
```

冻结结果记录Python 3.12.14、NumPy 2.3.5及本次平台信息。没有随机采样，因此核心脚本无需随机种子。未来加入随机不确定度传播或Monte Carlo射线时，必须同时记录生成器类型、种子、样本数和停止准则。运行时间依赖硬件负载，不应要求不同机器的计时CSV逐字节相同；数值结果按已注明容差比较。

## 3 最小输入协议

`schema_version=T02-case-0.1`表示本轮有限协议，不能默默接收未来语义变化。配置包含：

- `units`：严格SI契约；唯一明确例外为字段名自带单位的`carrier_rpm`，在位姿内部转换
- `value_status`：合成例子为`synthetic_assumption`；实机值需逐量记录测量/估计状态与来源
- `pose`：轨道半径、高度、载架速度、平面绝对自转比、载架/相对初相位、倾斜
- `surface`：`ring`指定环半径与点数；`disk`指定径向阶次、角向点数和可选曲率半径
- `source`：`point`含位置/单位法向；`disk`还含半径、正交姿态矩阵与源面分辨率
- `rate`：总发射质量率及正弦调制，频率Hz、相位rad；示例输入限制调制幅值绝对值总和≤1以保证整段非负
- `material`：有效薄膜密度与常数留存比例
- `masks`：矩形板中心、正交局部基、半宽、半高、厚度；空数组明确表示没有建模遮挡
- `time`：开始/结束s、已知事件时刻s
- `numerics`：面板数、每面板Gauss阶次、时间分块数
- `engineering_target`：真实产品目标未知时为null，不能从算法测试阈值自动填入

源法向和接收法向均需明确朝向。高层构造器归一化法向，但低层`transfer_kernel`要求调用者传入有效单位接收法向；它是高效数值内核，不是完整的通用输入验证器。零质量权重源节点在构造时移除，以免无贡献节点引发虚假奇异点。

对于倾斜轴，字段`spin_ratio_absolute_planar`只定义平面情况下的绝对转速比；代码实际把`ratio−1`作为载架局部倾斜轴相对旋转比。不要在三维中把它解释成对实验室z轴的完整矢量角速度。

### 不能省略的状态信息

`null`不是0，“没有测量”不是“没有误差”。测量模板中的每一量应包含value、unit、frame、value_status、source、standard_uncertainty或明确的区间说明。配置版本应随源穴、材料批次、夹具、掩模位置和传动结构改变。既有标定参数只在明确允许的配置域内复用。

## 4 输出协议

每个工件采样点输出局部坐标、法向膜厚m、留存面密度kg/m²及可用时的实际表面积权重m²。JSON输出模型版本、输入与模型SHA-256、软件版本、时间和源节点数、发射总质量kg、指标口径与验证状态。

对环形采样，`actual_surface_integrated_mass_kg=null`：一条圆周不能代表整个工件面积。对面积求积节点，才计算`Σ A_i m_A,i`。该值是当前工件有效面的捕获质量，通常小于总发射质量；腔壁与夹具损失未逐项求解，不能声称实现了整个腔体闭合质量账本。

`mean_m`等字段存SI数值；显示nm时乘10⁹。报告的PV/CV/MAD为比例，例如0.01表示1%，不可在界面再次按百分比错误转换。平均厚度、空间归一化形状、留存总量应同时保留，避免优化器在“均匀但几乎没有沉积”的解上虚假成功。

## 5 适配实际设备的操作顺序

1. 以T01参数模板确认真实传动和坐标；通过标记点/法向轨迹核验位姿模块
2. 填完整层的源、挡板与运动时序，核对单位及时间延迟
3. 从无掩模最简单源核开始，先核验绝对尺度与形状，再按残差升级源和留存模型
4. 同一配置跑解析回归与时间/源/空间分项加密，记录数值预算
5. 加入观测算子，区分参数拟合数据和独立验证数据
6. 用经过验证的适用域、误差预算和目标指标约束T03修正板优化

本轮不读取旧测光原始数据，不据历史转述填实机校准，不更改产品代码，不产生可直接加工的修正板图纸。这些边界确保理论成果可以继续推进，而不会把合成样例伪装成设备证明。
