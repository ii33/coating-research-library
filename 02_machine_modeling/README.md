# T02 高精度镀膜机建模与仿真

首轮v0.1已完成并冻结：三维正向模型规范、可复用NumPy参考实现、解析/数值验证、误差预算和实机标定协议。34项解析与边界检查通过；有时间、源面积、工件面积、遮挡、混叠、36/37齿归因和可辨识性基准。当前成果适用于理论/公开证据/合成验证范围，尚未证明用户机器的物理预测精度。

这是十专题串行研究的第二阶段，原文要求见`00_project/工程科研.txt`第5行。T01的行星结构和运动学基线为前置；本轮完成后可进入T03修正板自动设计，实机识别、材料标定和真实数据验证按明确接口后续适配，不暗中填默认值。

## 先读哪些文件

1. [物理边界与保真度层级](chapters/01_physics_and_fidelity.md)：质量率、密度、角分布、扩展源、视因子及适用域
2. [三维运动和遮挡](chapters/02_geometry_kinematics_visibility.md)：精确刚体链、法向、真实掩模平面、厚板、36/37中心距混淆
3. [数值积分](chapters/03_numerical_integration.md)：时间/源/面积求积、事件分段、混叠、空间极值和复杂度
4. [标定与不确定度](chapters/04_calibration_uncertainty.md)：观测模型、结构不可辨识、留出验证及误差预算
5. [验证与基准结果](chapters/05_validation_and_benchmark_results.md)：实际执行数字、速度—精度、负例及接受边界
6. [输入输出与复现](chapters/06_reproducibility_and_interfaces.md)：配置协议、命令、文件及设备适配顺序

来源见[8项来源登记](sources/source_registry.json)和[逐来源摘要](sources/summaries/source_summaries.md)。全文、摘要及官方条款读取范围分别注明，合法原文存档与公开分发权限分开记录。

## 直接复现

在本目录运行，核心仅需Python 3和NumPy，无需安装商业模拟器：

```bash
python verification/run_verification.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python benchmarks/run_benchmarks.py
python models/run_case.py data/synthetic_case.json --output benchmarks/results/example
python verification/check_release.py
```

图示可选，用既有matplotlib执行`benchmarks/plot_results.py`。CSV与JSON是可重复计算的主结果，图片仅帮助阅读。参考实现不是现有镀膜软件产品代码。

## 验收状态

- 理论模型与公开来源：首轮范围完成
- 解析/合成数值检查：34/34通过；参考解自身残余差明确记录
- 窄范围独立数学复核：核心公式一致，1项低严重度输入边界问题已修复复测
- 用户实机标定/实验验证：未执行，所需数据和容差留空
- 指定但未实际运行的模型审核：未执行，不虚构签署；本次冻结依据为实际证据

详见[阶段验收](reviews/ROUND1_ACCEPTANCE.md)、[已知缺口](reviews/OPEN_ISSUES.md)、[机器可读状态](stage_status.json)和[T03移交](T03_HANDOFF.md)。项目总状态由主协调工作统一更新，本专题不同时改写根目录。

## 使用底线

合成例子不是实机默认参数；法向几何膜厚不是光学性能或微结构；数值积分收敛不是物理模型已被验证。任何优化器须继承误差与适用域，不能用未标定模型直接输出加工或生产合格保证。所有十个专题首轮结束后，再返回补充本专题更广泛的机理和通用求解器扩展。
