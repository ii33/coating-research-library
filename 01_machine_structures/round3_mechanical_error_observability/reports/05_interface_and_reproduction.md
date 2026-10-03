# 离线接口 复算与正式计算边界

## 1 代码职责与非职责

`models/reference.py`提供SI单位刚体位姿、点/法向、局部Jacobian、有初态的play算子、小矩阵去干扰可辨识诊断和严格离线CSV读入。它不是设备驱动、控制器解码器、完整参数反演器或生产性能软件。对未知拓扑，理想直接外啮合比例函数拒绝调用；对未知模数，中心距函数拒绝补值。

`models/offline_read.py`只从一个JSON合同及其所在目录内CSV读取，没有网络、账户、设备或父研究库依赖。每个CSV必须恰有`time_device_s,value`两列，每行恰有两字段，数值有限、时间严格递增；映射到共同时间后再次检查有限和严格递增，避免大绝对时间吞掉细小采样间隔。读者传入的JSON目录就是准许读取的边界，绝对路径、上跳路径和逃逸符号链接被拒绝。原文件SHA-256匹配后才解析，但hash只是内容身份，不证明仪器真实性或校准有效性。

量类型与标准单位：carrier_angle/output_angle用rad；axial_displacement/radial_displacement/thickness用m；source_monitor为经过声明归一化的无量纲1，不能把电流或QCM原计数不转换就塞入该字段。图像原帧与像素特征本轮仅定义需求，没有声称实现通用视觉姿态提取器。

每个通道另需sensor_id、安装描述、角度解缠约定、时间单位、时钟比例a与偏置b及其证据、原文件路径与hash、校准状态/证据。测量模板故意没有虚构数值，`dataset_kind=template`会被拒绝。合成fixture必须显式`--allow-synthetic`才进入。程序只作接口准入；之后的传感器响应、相关协方差、拓扑/基准和留出数据仍决定能否拟合。

CSV设计故意很小，原始厂家日志应保留独立版本化转换和字段映射，不要求真实仪器改为这种输出格式。真实数据缺失、单位转换或时钟关系不明确时，应返回incomplete/unknown，不能借通用模板填零。

## 2 公开函数契约

| 函数 | 输入/输出 | 重要约束 |
|---|---|---|
| exp_so3(v) | 3分量rad → 3×3旋转 | 有限数，保留零角稳定级数 |
| pose(...) | 单时刻几何、角度、平移/倾斜 → c,Q | bC含名义高度；两类倾斜均无z自由度 |
| point_normal(c,Q,u,n,e) | 位置m、单位法向 → 世界点/法向 | Q必须正交且det=+1，n必须单位长 |
| rigid_jacobians(c,x,n) | 世界点/法向 → 3×6矩阵各一 | 列为世界平移3＋关于c的左小旋转3 |
| play_backlash(x,b,y0) | 解缠角序列、半宽/初态 → 输出角 | b为rad，实际接触动力学另行处理 |
| local_observability(Jm,Jn,Σ,s) | 任意同一观测顺序矩阵 → rank/奇异值/null/条件协方差 | Σ须SPD；确定约束另处理；s>0；病态干扰子空间返回未决而非识别 |
| load_observation_dataset(path) | JSON及已hash CSV → 共同时间坐标记录 | 默认拒绝合成和模板，无实测认证 |

观测顺序是联合协方差的关键。多通道拼接、删点和重采样都必须同步变换Σ；不能只切Jacobian。SVD结果的null_physical是参数实际单位方向（若干扰子空间未决，该向量也仅条件于数值截断），不是置信区域；其向量长度没有概率含义。

## 3 正式反演完整计划保留精度

`data/formal_calibration_plan.json`列出完整参数块、误差轴、干扰条件、优化/剖面/留出/传播步骤以及停止状态。`models/prepare_calibration_plan.py`默认仅打印plan_only；`--execute`明确拒绝，不冒充已实现完整求解或启动设备任务。

正式算法应先冻结测量算子和基准，再构造SO(3)联合残差与可靠导数，按已校准相关噪声白化；在有依据的接触/拓扑候选间检查全局别解，沿弱方向作剖面或可行区间，最后用独立运行验证。连接到沉积预测时，要分别验证时间、源求积、遮挡事件、基片空间、优化停止和统计抽样误差；不能用本轮小矩阵通过替代这些轴。

真实目标、计算设备、wall/内存/前向调用/重启和profile预算目前均为null，正式执行前须明确。当前执行资源受限时不降低正式问题精度、不改小网格宣称完成，只保留未运行状态。此包没有隐藏重任务入口。

## 4 无父目录的复算

把读者ZIP解压到任意新目录，进入该目录。需要Python 3.10+与NumPy 1.24至2.x；本次实际为Python3.12.14、NumPy2.3.5。只校验manifest需要Python标准库；完整轻量复算需要NumPy。以下默认不覆盖冻结数据：

```
python -B verification/reader_check.py --check
python -B -m unittest discover -s verification -v
python -B models/run_examples.py
python -B models/offline_read.py data/synthetic_observations.json --allow-synthetic
python -B models/prepare_calibration_plan.py
python -B reviews/independent_checks.py
```

`run_examples.py --write`只供作者在新版本构建时写结果，不用于证明收到的文件未变；reader_check的build同理。归档内不会递归加载前两轮、不联网取原文、不要求全库存在，也不自动重新拟合实机数据。

## 5 版本与输出身份

公开清单是逐项允许列表；manifest记录允许列表中除manifest自身外每个文件的SHA-256和字节数，并明确自引用例外。外部receipt记录ZIP本身和manifest摘要，receipt不在ZIP内，避免循环。引用的前轮和原始需求只登记来源身份与内容hash；当前代码不是那些文件的修改版或新发布。第三方原文另存本地，永不被reader递归收集。

完整性校验不是数字签名；它只证明读到的文件与给定manifest一致。重新build会创建新的声明，不能作为旧包未改的证据。独立核查的输入hash与最终版之间如有修改，必须记录明确差异和复测范围。
