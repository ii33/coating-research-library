# 一维光学多层膜：可微、离散材料与稳健逆设计核查

核查截至 2026-10-19。范围以平面分层、TMM可求解的光学薄膜为主；不把横向图案化超表面、拓扑能带态、机械/声学一维结构混入同一进展。以下把论文自述、代码可核事实与本次审查判断分开。未运行作者代码，未做独立数值性能复现。

## 可直接用于主稿的结论

1. 近年的真实增量主要是把快速物理梯度接入新的搜索表示、离散材料选择、制造误差目标和系统级损失。可微TMM、梯度厚度优化、非周期堆栈和一维拓扑设计本身并不是2025/2026才出现。
2. GLOnet有一维薄膜原论文与官方代码，可作为“无预生成训练集的生成式全局搜索”强案例。它在特定基准上找到已知最优附近的解，不构成任意薄膜问题的全局最优保证。
3. tmm-fast、TMMax是可直接采用的开源可微求解基础设施；其百倍级数字主要指对串行Python/NumPy参考实现的求解加速，不能写成优化质量或整个设计流程同倍数提升。
4. Ma等SAGD正式发表于2026-06-23，并有器件制备与成像实验。关键创新是把平坦极小值/局部对抗扰动用于薄膜制造容差；公开仓库目前不足以完整复现论文全部比较和实验。
5. Yesilyurt等2023年已把制造误差放入可微薄膜优化，但论文明确其“fabrication-in-loop”生长与测量均由模拟代替。不能称其已完成真实沉积闭环。

## 1. GLOnet：材料类别松弛与种群式可微搜索

### 论文与证据

- Jiang, J.; Fan, J. A., *Multiobjective and categorical global optimization of photonic structures based on ResNet generative neural networks*, Nanophotonics 10(1), 361–369 (2021)。首次在线为2020-09-22；不要因卷期为2021或网页抓取时间而误标新近2025成果。
- 正式论文：[DOI 10.1515/nanoph-2020-0407](https://doi.org/10.1515/nanoph-2020-0407)；[可读出版社全文](https://onlinelibrary.wiley.com/doi/10.1515/nanoph-2020-0407)。
- 原论文并非先训练代理物理模型：ResNet生成器输出材料概率与厚度，PyTorch TMM直接计算光谱和梯度；softmax逐步锐化，最终选择材料库中的类别。演示包含三层减反膜和多材料白炽灯滤波器，属于计算设计。
- 三层例中，作者给出7秒单GPU、4000组计算，平均反射率约1.81%；多起点局部梯度最好约1.82%。与19 CPU日的branch-and-bound比较必须保留“对方同时给出全局性认证、硬件不同”的背景。
- 灯滤波例报告45层光效增强17.2，对比文献memetic 14.8、RL 16.6；成本段落写GLOnet 50万次模拟，但训练描述又写batch=1000、1000轮，存在需解释的计数不一致。

### 对公平性与“新”的判断

- 对齐目标、材料库、角度、厚度边界，比只与随机堆栈比较更有价值；但论文未建立同硬件、同墙钟、同重启次数下对成熟needle+局部优化的全面优势。
- “找到认证基准的同等值”与“自己认证全局最优”是两种不同结果。GLOnet属于启发式全局搜索，应报告成功率和多次独立运行分布。
- 不应沿用原文引言把needle与memetic一概说成无梯度：原文自己的灯滤波综述就说明needle流程配合厚度局部梯度，memetic也包含梯度精修。
- 材料概率加权得到的中间折射率只是优化松弛，不自动对应能制备的混合材料。最终必须硬离散化，再重新计算与局部精修。

### 官方代码实查

- 官方仓库：[jiaqi-jiang/GLOnet_for_thin_film](https://github.com/jiaqi-jiang/GLOnet_for_thin_film)。核查版本：[01ff041f2d731bfc22cd48e2af44461bbca4654d，2022-06-30](https://github.com/jiaqi-jiang/GLOnet_for_thin_film/commit/01ff041f2d731bfc22cd48e2af44461bbca4654d)。
- [GLOnet_thinfilm.py](https://github.com/jiaqi-jiang/GLOnet_for_thin_film/blob/01ff041f2d731bfc22cd48e2af44461bbca4654d/GLOnet_thinfilm.py)有完整在线训练、TMM调用和类别后处理。evaluate默认grayscale=True；复现实物材料结果应显式采用grayscale=False，避免把松弛材料的光谱当成最终类别结果。
- 同文件虽有global_loss_function_robust，但train实际调用普通global_loss_function，且robust_coeff不在该类初始化。因此不能根据函数名就把这个公开示例称为已经启用稳健训练。
- 仓库包含TMM、网络、材料数据库、LightBulbFilter.ipynb，提供有用起点；根目录树未见依赖锁定、基线实现或独立重复试验脚本。不能把“有官方源码”写成“所有比较已一键复现”。

## 2. tmm-fast / TMMax：物理与梯度基础设施

### tmm-fast

- Luce, A.; Mahdavi, A.; Marquardt, F.; Wankerl, H., *TMM-Fast, a transfer matrix computation package for multilayer thin-film optimization: tutorial*, JOSA A 39, 1007–1013 (2022)。正式在线2022-05-11；[DOI 10.1364/JOSAA.450928](https://doi.org/10.1364/JOSAA.450928)；[作者机构存档PDF](https://pure.mpg.de/rest/items/item_3401594_4/component/file_3401970/content)；[预印本](https://arxiv.org/abs/2111.13667)。
- 贡献是批量波长/角度TMM、PyTorch自动微分及强化学习环境，不是新的麦克斯韦物理定律。原始基准：10个21层堆栈、100波长×20角度，串行参考约17.5秒、向量化约0.168秒，约100倍；百万个9层样本在8核机器约40分钟。以上为作者报告，未独立复跑。
- 官方MIT许可源码：[MLResearchAtOSRAM/tmm_fast](https://github.com/MLResearchAtOSRAM/tmm_fast)。当前main核查提交：[7e3895b39a29919374a68231776b2817bc5862e4，2026-08-21](https://github.com/MLResearchAtOSRAM/tmm_fast/commit/7e3895b39a29919374a68231776b2817bc5862e4)。此版本含重要修复，不能用当前包性能反向代替2022论文版本。

### TMMax

- Danis, B. S.; Zayim, E., *TMMax: High-performance modeling of multilayer thin-film structures using transfer matrix method with JAX*, JOSS 10(114), 9088；正式发表于2025-10-27。[DOI 10.21105/joss.09088](https://doi.org/10.21105/joss.09088)；[正式文章页与review/archive入口](https://joss.theoj.org/papers/10.21105/joss.09088)；[论文全文](https://arxiv.org/html/2507.11341v2)。
- JAX向量化/JIT/lax.scan、自动微分、跨CPU/GPU/TPU、材料数据库，是其主要工程价值。论文以同一Intel Core i9单核和Byrnes tmm比较，报告2–400层约18–700倍；小2×2波长角度网格可被低开销NumPy反超。不能从该实验推断始终更快，也未证明比所有批量TMM实现都快。
- 官方仓库：[bahremsd/tmmax](https://github.com/bahremsd/tmmax)；核查master提交：[dc4b90438dffeafd420a7b90c63539813881bedb，2026-10-16](https://github.com/bahremsd/tmmax/commit/dc4b90438dffeafd420a7b90c63539813881bedb)。JOSS给出归档[Zenodo DOI 10.5281/zenodo.17361547](https://doi.org/10.5281/zenodo.17361547)，本次未取得归档内容，不能宣称其与最新master完全相同。

### TMMax计时细节：直接可核的重要限制

- [benchmarks/layer_size_benchmark.py](https://github.com/bahremsd/tmmax/blob/dc4b90438dffeafd420a7b90c63539813881bedb/benchmarks/layer_size_benchmark.py)同时列出tmm、vtmm、tmm-fast、tmmax；但论文与[说明文档](https://github.com/bahremsd/tmmax/blob/dc4b90438dffeafd420a7b90c63539813881bedb/docs/source/user_guide/benchmarks.rst)正文主要讲tmm对照。
- 脚本timeit(number=50)返回累计时间，存储/打印前未除以50；文档称平均值。相同重复数下速比不因此失效，但文中绝对秒数不应未经核对当成单次调用延迟。
- [绘图notebook](https://github.com/bahremsd/tmmax/blob/dc4b90438dffeafd420a7b90c63539813881bedb/benchmarks/tmmax_benchmark_figures.ipynb)也直接加载计时数组绘制秒数，未见除以50的步骤。该观察针对核查提交，不等于已经复核论文归档版本全部原始计时。
- JAX计时用了block_until_ready，避免简单的异步发射假加速；然而脚本未显式把JIT冷启动与稳态分别计时。不同shape触发编译会影响结果。
- 仓库存在tests和benchmark结果数组，这是比只有一个演示脚本更好的复现基础；正数计时测试不能代替物理准确性与梯度验证。

### 对项目的采用判断

优先把二者用作可信候选求解后端和交叉验证器。优化算法应共享同一个后端、相同采样网格和复数精度，再比较结果。把“向量化后端加速”与“新优化算法减少搜索次数”分开统计，避免给算法记上实现语言与GPU的功劳。

## 3. SAGD：可微TMM上的局部平坦性稳健目标

### 正式论文可以确认的内容

- Ma, Yuchen; Hu, Guangwei; Cao, Liangcai, *Sharpness-Aware Minimization for Robust Inverse Design of Nonlocal Thin Films*, Laser & Photonics Reviews, e71366 (2026)。正式首次在线2026-06-23，不是2025。[DOI 10.1002/lpor.71366](https://doi.org/10.1002/lpor.71366)；[出版社页](https://onlinelibrary.wiley.com/doi/10.1002/lpor.71366)。
- 作者把SAM式sharpness-aware策略与可微TMM结合，目标是对厚度和折射率变化更稳健；摘要明确双通道空间频率滤波器已设计、制备，并演示明场/暗场切换。属于具有真实器件实验的强案例。
- 出版社数据声明直接链接官方GitHub。摘要仅说优于conventional techniques，本次全文/补充PDF入口未成功获取，因此不能确认全部基线、误差分布、样本数、显著性和算力公平性；不填造倍数或容差数字。

### 官方代码实查：只覆盖部分复现链

官方MIT许可仓库：[THUHoloLab/SAGD](https://github.com/THUHoloLab/SAGD)。核查main提交：[1c4ebd2debf9c277025e86a71da93a3f2aa8d1d0，2026-07-11](https://github.com/THUHoloLab/SAGD/commit/1c4ebd2debf9c277025e86a71da93a3f2aa8d1d0)。

- [SAGD_main.py](https://github.com/THUHoloLab/SAGD/blob/1c4ebd2debf9c277025e86a71da93a3f2aa8d1d0/SAGD_main.py)：固定35层TiO2/SiO2交替，仅训练连续厚度；默认CPU、200轮、SGD+momentum=0.9；训练6个波长620–630nm×10个角度0–约36.9°，同时优化s/p；后评估200×200网格600–650nm、0–45°。这是角度响应设计，不是任意材料拓扑搜索。
- 每轮先求原参数梯度，再沿归一化梯度施加L2厚度扰动，随后在扰动点求第二次梯度，回到原点更新；默认rho=0.05（脚本厚度单位μm）。它是整条厚度向量的L2球半径50nm，不能称为“每一层±50nm独立容差”。
- 两次梯度使其单轮成本高于普通SGD；不能只对齐轮数宣称更高效，应对齐前向/反向次数和墙钟。
- 只有负厚度惩罚，未见硬性最小厚度、沉积量化、最大总厚度或层间过渡约束；最初厚度在0–0.5μm随机采样，未固定随机种子。
- 仓库树只有主示例、TMM、插值绘图工具、两个nk CSV与结果图；未见needle/PSO/多起点基线、Monte Carlo厚度和折射率扰动评估、论文成像原始图/光谱测量数据、冻结环境或论文各图复现脚本。因此准确标签是“官方核心算法示例开源，完整论文复现未核实”。
- [src/tmm_layer.py](https://github.com/THUHoloLab/SAGD/blob/1c4ebd2debf9c277025e86a71da93a3f2aa8d1d0/src/tmm_layer.py)使用complex64和相干TMM。[src/utils.py](https://github.com/THUHoloLab/SAGD/blob/1c4ebd2debf9c277025e86a71da93a3f2aa8d1d0/src/utils.py)把CSV正k返回为n−ik，且缺数据文件时退回n=1.5而非硬报错。将来用于吸收膜前，必须核查时间/相位符号、forward波分支、被动性R+T≤1以及有限差分梯度。这里只标为风险点，未运行测试，不能直接定性作者求解器有错。

### 对稳健性的准确解释

本次判断：局部sharpness目标很适合增加厚度容差，但其有效性受参数尺度和误差几何影响。实际沉积误差往往同时包含材料相关系统偏差、逐层随机误差、时间漂移和厚度–折射率相关性。未经这些分布上的外部测试，平坦损失不等价于量产良率保证，也不自动覆盖粗糙、散射、应力、非均匀性、材料色散变化或制造设备可达性。

## 4. 2023制造意识逆设计：值得纳入的前驱对照

- Yesilyurt等，*Fabrication-conscious neural network based inverse design of single-material variable-index multilayer films*, Nanophotonics 12, 993–1006 (2023)，首次在线2023-01-30。[DOI 10.1515/nanoph-2022-0537](https://doi.org/10.1515/nanoph-2022-0537)；[正式可读全文](https://onlinelibrary.wiley.com/doi/10.1515/nanoph-2022-0537)。
- 在线神经参数化+解析可微求解器，不需预生成训练集；单材料Si_xN_y以可变折射率实现分层设计，并减少冗余层，第二阶段引入制造误差补偿。
- 最重要限定：第4.3节与结论明确，生长和椭偏测量由模拟误差替代；真实实验数据留作未来工作。并非已经验证的自动镀膜闭环。
- 随机误差比较用1000组扰动：对非零均值能补偿谱移，对零均值±1%/±5%的随机波动优势有限。说明“学习系统偏差”和“对随机制造误差本身免疫”必须分开。
- 本次未核到官方完整代码/原始实验数据入口，不应标注完整开源复现。

## 5. 经典基线和措辞边界

### 必须保留的历史锚点

- 一维薄膜时域拓扑优化至少已有Yang等2009年Si/SiO2脉冲整形设计：[DOI 10.1063/1.3278595](https://doi.org/10.1063/1.3278595)，[作者机构条目](https://orbit.dtu.dk/en/publications/design-of-one-dimensional-optical-pulse-shaping-filters-by-time-d/)。因此不要把一维拓扑优化本身列为近年首创。
- Needle插层/删层与连续厚度精修具有成熟历史：[Tikhonravov等1996，DOI 10.1364/AO.35.005493](https://doi.org/10.1364/AO.35.005493)。其时域扩展显式涉及梯度与解析导数：[Trubetskov等2008，DOI 10.1364/OE.16.020637](https://doi.org/10.1364/OE.16.020637)。不宜用“经典方法都是无梯度”作论证前提。
- Azunre等2019的Taylor-model branch-and-bound提供指定容差内的全局认证，并有三层减反膜制备：[DOI 10.1088/1367-2630/ab2e19](https://doi.org/10.1088/1367-2630/ab2e19)，[MIT正式稿存档](https://dspace.mit.edu/entities/publication/97c01ec7-771f-458c-aee6-2866851a0b68)。高成本部分是在证明不存在更优解；与7秒启发式寻优不能作同任务耗时解释。

### 建议项目采用的公平比较协议（本次审查建议）

1. 分三个问题分别比较：固定材料顺序的连续厚度；固定层数的离散材料+厚度；允许插层/删层/变层数的拓扑搜索。每个方法必须承担相同自由度与约束。
2. 最小基线包括多起点L-BFGS-B/LM或适用局部法、needle+局部精修、DE/PSO+局部混合；小规模另设branch-and-bound认证校验。不能只有单起点SGD和随机搜索。
3. 锁定材料nk来源、插值、采样波长/角度/偏振、厚度界、量化、最小层厚和总层数。最终硬离散堆栈一律交由独立TMM实现高密网格复算。
4. 分别报告无训练数据方法的完整优化成本，以及预训练方法的数据生成、训练、推理与后精修成本；统一wall-clock、硬件、精度、前向/反向调用数和内存。把JIT冷启动与稳态计时分列。
5. 至少多随机种子重复，报告最优、中位数、分位数、达标成功率，避免挑一个最好结构；所有方法共享测试目标集合。
6. 对稳健设计，锁定真实或保守的误差模型，以未用于优化的扰动样本评估期望、尾部/CVaR、最坏值和规格良率；分别测试系统厚度比例误差、逐层随机误差、材料相关n偏差与相关漂移。
7. 对SAGD做同预算消融：普通梯度、多点随机扰动训练、显式灵敏度惩罚、SAM。考察rho与参数单位/归一化的依赖；不能把μm数值上的平坦直接当成物理尺度不变性质。
8. 复现包应含版本固定、环境锁、目标定义、优化和制造约束、完整基线、种子、最终层表、所有测量与扰动统计。源码公开只证明可以检查部分实现。

## 6. 取舍建议

- 近期最值得复现的是：可信可微TMM后端+多起点强局部/needle基线，再加入SAGD与真实沉积误差模型。研究问题应是“在同预算和同制造约束下，良率能提高多少”。
- 如需联合材料选择，再以GLOnet/softmax作离散松弛候选；先验证硬离散化损失与局部精修，再讨论生成器的收益。
- 目前证据支持“可微与稳健优化正在让复杂一维镀膜更容易系统化搜索”，不支持“AI新算法已全面取代经典薄膜优化”或“非周期/局部梯度/一维拓扑是新近发现”。
