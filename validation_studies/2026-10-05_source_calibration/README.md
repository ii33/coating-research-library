# 固定几何 QCM → 源 A/cosⁿ 标定研究

2026-10-05，既有 dot 云端 VM。状态：**可执行合成原型，真实物理验证未完成**。

重要结果：三枚覆盖不同源角的 QCM 可辨识 A,n；六枚同环传感器仍秩亏。小的训练残差无法保证片上通量正确。所有数值均为本研究构造的合成数据，未操作设备、未更改 cub、未 push、未安装依赖。

## 范围与实现

- 先固定已知几何，仅拟合非负总发射质量率 A[kg/s] 与非负角指数 n
- 前向核直接只读复用既有 T05 `Source/flux_kg_m2_s`，不是重新写一个未经标识的替代物理核
- `geometry_from_production_source` 只读调用安装版本 `coat_sim.core.source_profiles.source_samples`，将 mm 源节点转换为 SI m。当前安装源节点的法向为 +z
- cub 的 `simulator.py` 输出按工件均值归一的相对场，不含总发射质量率 A；其 `source_rate_nm_s` 不能直接当 A。此次只核查实际源几何适配，不声称验证完整 cub 有限源/行星运动/双掩模内核
- 固定超参数的轻量 RBF GP 先预测三枚 QCM 的质量通量，再拟合 A,n。它演示论文路径；没有主动学习、超参数优化或真实工况模型
- [算法说明及原创示意图](docs/algorithms.html)为单文件离线 HTML

## 复现

在本目录运行，已有 Python 3.12、NumPy 2.3.5、SciPy 1.17.0，无需安装：

    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python run_study.py --repetitions 20

单次 study 约 15 秒，单线程 CPU，无 GPU。`--repetitions` 只接受 1..100。重跑会替换本研究 results 下对应结果；保存另一份时指定 `--output-dir`，原源文件哈希基线不会重写。不同位置复现仍需已安装生产源几何接口和本库 T05 源参考接口，未称为完全独立可移植包。

## 结果入口

- [可读结果与边界](results/RESULTS.md)
- [完整机器可读结果](results/study_results.json)
- [180 次全部恢复试验](results/recovery_trials.csv)，不只保留最佳 seed
- [代表性完整 n profile](results/representative_profiles.json)
- [合成输入合同](results/synthetic_input_contract.json)
- [20 项小测试输出](results/test_output.txt)
- [生产/参考源文件哈希核查](results/runtime_source_check.json)
- [真实 unknown 输入模板](data/actual_unknown.json)

代码质量与数值一致性：20 项 unittest、180 次合成试验、解析归一化/独立点源公式/解析 Jacobian 差分核查、同环与零源反例、配置及工况域外拒绝。它们不能代替真实物理验证。20 次/格是小规模描述统计，不是准确覆盖率、成功率界或生产精度认证。

## 输入合同与未知值

1. 固定腔体坐标系，源节点位置[m]、单位法向、非负和为 1 的发射质量份额。固定配置标识应涵盖源/穴位/材料/料位/温度历史、传感器位置和姿态
2. 每枚 QCM 中心位置[m]、朝向蒸气的单位法向、明确有效面积[m²]、净捕集比例和其依据
3. 数据必须是面质量通量[kg m⁻² s⁻¹]，每枚已知独立 Gaussian 标准差同单位，另提供严格正的绝对噪声底。本研究 0% 噪声算例仍采用 1e-12 的计算噪声底
4. 若导出的是全晶体质量率[kg/s]，可用明确有效面积转换；已经是面质量率的 Sauerbrey/控制器导出不得再除面积。这里不擅自读取仪器频率、推断晶体常数、密度或 Z-ratio
5. 当前把晶体中心作为点接收器；面积用于识别量纲或总质量率换算，不进行有限晶体表面积积分。真实晶体过大、斜入射或边缘非均匀时需另作面积收敛/计量验证
6. 原始或减去漂移后的读数可为负，不将其裁成正值；物理幅度仍限制 A≥0，零源会明确报告无法辨识 n
7. `capture_fraction=None` 仅在程序化合成 fixture 中解释为已知 1；真实合同验证必须显式提供捕集率，未知值不能默认为 1

未知坐标、同环半径或测量误差继续保留 null。历史六个同环点且半径未知不能校准几何，也不能同时释放几何、密度、留存与 A,n。此模板在入口被拒绝，不借默认几何制造“实验标定”。

## 推断与使用约束

拟合最小化 Σ[(A Kᵢ(n)−jᵢ)/σᵢ]²，TRF 有界非线性最小二乘使用解析 Jacobian、五个固定起点和精确 n=0/n_max 端点。给定 n 的 A 另用非负线性闭式解精修。多起点不是全局最优证明。

- n 搜索上限 20 是本研究声明的计算域，不是测得的物理上限
- 对参数 [ln A,n] 的白化 Jacobian 作 SVD，1e-8 相对奇异值阈值为本研究约定；秩不足时阻止发布片上图
- 条件数>100、信号最大 SNR<3 是描述性项目告警，不能当普适计量门槛。窄角全秩仍可能严重病态
- 内点协方差条件化于给定噪声、几何、捕集与模型。已知绝对 σ 时不乘 reduced χ²。边界、秩亏时不发布普通无约束正态协方差
- 401 点 n profile 的 Δχ²=3.84146 区域只是常规内点渐近参照；网格端点、边界以及非线性小样本未证明精确 95% 覆盖。到达 cap 就记上端未闭合
- `predict_fitted` 只检查局部秩、信号及调用方维护的配置 ID 合同；返回值是科研预测，不是工程批准的空间图。它仍可能返回 cap-hit、病态或优化器未收敛的拟合。未来生产接口需更严格的收敛/不确定度门控与独立源身份校验，须另定范围和授权
- 三枚 QCM 内点拟合仅有 1 个残差自由度。拟合残差不能充分检出模型缺项
- GP 的整个功率/压力条件留出：20 条训练、5 条测试。训练均值/尺度/凸包均只由训练条件确定；测试真实值只作评估。固定长度尺度 0.65 未用测试调优
- GP 禁止超出训练凸包或变更配置后复用。处在凸包内也只说明没有数值外推，不证明整个域已物理验证
- GP 输出的标准差仅为给定固定超参数/独立输出假设下的潜在函数不确定度，不能覆盖模型偏差、QCM 共同漂移/交叉协方差、几何、膜密度、留存及批间差异

## 真实验证还缺什么

需要明确机台/源状态、QCM 原始频率或可追溯面质量通量与噪声、有效面积/姿态/坐标、源几何、遮挡/挡板状态、独立捕集率或明确复合幅度解释；随后用未参与拟合的二维样片质量/独立厚度测量，以及整组未参与训练的功率/压力/料位重复验证。

若读数是厚度率，则整体尺度通常只约束 A×捕集率/膜密度。这些量无独立证据时不能把拟合复合幅度发布为物理总发射率。研究保留三组同厚度尺度的反例。

真实 QCM、有限晶体面积收敛、源几何识别、finite-source planetary dual-mask kernel 物理验证、主动学习及完整指定 DeepSeek/Seed/Sol 审查链均未运行。本阶段仅有当前执行者的实现自检及另行安排的有界只读方法复核，不能标成完整指定模型审查验收。

## 来源及版本边界

- Jarl 等，2025，Machine learning for in-situ composition mapping in a self-driving magnetron sputtering system，[固定 v1 §2.1–2.4，尤其 Eq.2](https://arxiv.org/html/2506.05999v1)。本研究只借鉴三 QCM → GP → 点源 A/cosⁿ 反推的路径；该磁控溅射点源与实验成分验证不验证本项目的有限蒸发源、行星运动或双掩模。官方摘要页已有 v2（2026-01-09）；本次未把 v2 改动隐式混入固定 v1 范围
- [SciPy least_squares 官方说明](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.optimize.least_squares.html)：TRF 有界最小二乘；实际运行版本见 JSON
- [Rasmussen 与 Williams，Gaussian Processes for Machine Learning，第 2 章](https://gaussianprocess.org/gpml/chapters/RW2.pdf)：条件 Gaussian 后验。此处固定 RBF、独立输出与噪声底为简化实现约定，未复现 Jarl 的 Matérn 5/2 或完全 Bayesian 模型
- 本库既有 [T05 可辨识性与合同](../../05_evaporation_sources/reports/05_calibration_identifiability_and_interfaces.md)、[T05 SI 源接口](../../05_evaporation_sources/models/source_reference.py)只读复用

所有新增文件仅限此独立研究目录。186 个生产/参考源码文件运行前后 SHA-256 一致；运行前清单原样保留。生产基线名称由父任务提供为 cub 415635cf，当前可读工作副本不具可查询 git 元数据，因此本研究直接核查内容哈希，不伪称自己重新验证了 git commit。本包不修改生产算法文档；新算法说明在本目录 docs/algorithms.html。
