# 第二轮不确定性优化来源卡片

核查日期：2026-10-02 UTC。以下均为一手论文或标准组织原始记录；此卡片只作简短内容摘要，不转载原文。

## S01. 区间方法下的鲁棒多目标进化

**G. L. Soares, F. G. Guimarães, C. A. Maia, J. A. Vasconcelos, L. Jaulin.** “Interval Robust Multi-Objective Evolutionary Algorithm.” *2009 IEEE Congress on Evolutionary Computation*, 1637–1643, 2009. [DOI: 10.1109/CEC.2009.4983138](https://doi.org/10.1109/CEC.2009.4983138). [作者/实验室托管的论文PDF](https://webperso.ensta.fr/jaulin/paper_soares2009.pdf).

论文定义以有界不确定参数为输入的最坏情形多目标问题，并用区间包含函数、非重叠子区间细分和演化搜索近似鲁棒前沿。它支持“先明确不确定集合与 worst-case 语义，再做多目标比较”的设计选择；也讨论区间依赖可导致包络偏宽。

**限制：**算法用ZDT测试函数展示，进化前沿本身是近似；仅有限区间参数上的包含函数才继承其包络含义。它不证明本项目RayBundle、普通浮点求积差或T02全部物理误差已经被包含。

## S02. 近似解与不确定解之间的Pareto比较

**Miha Mlakar, Tea Tušar, Bogdan Filipič.** “Comparing Solutions under Uncertainty in Multiobjective Optimization.” *Mathematical Problems in Engineering*, 2014, Article 817964, 10 pages. [DOI: 10.1155/2014/817964](https://doi.org/10.1155/2014/817964). [期刊页面](https://onlinelibrary.wiley.com/doi/10.1155/2014/817964).

提出在目标 bounding boxes / confidence intervals 上扩展Pareto关系、纳入可行性状态；当区间重叠且关系难定时，文中讨论额外求值来缩窄不确定性。可用于支持“区间未分开时保留候选，触发有针对性的求值/加密”。

**限制：**文中示例主要按近似预测值与统计置信区间建模，并在三个二维基准问题与其代理设置上实证；统计置信区间不等同于已证明的数值误差界，也不保证覆盖所有未知输入。当前规格只借用比较思想，不声称复现该文关系或其数值效果。

## S03. 昂贵多目标黑盒的代理式采样

**Juliane Müller.** “SOCEMO: Surrogate Optimization of Computationally Expensive Multiobjective Problems.” *INFORMS Journal on Computing*, 29(4), 581–596, 2017. [DOI: 10.1287/ijoc.2017.0749](https://doi.org/10.1287/ijoc.2017.0749). [INFORMS原始论文页](https://pubsonline.informs.org/doi/10.1287/ijoc.2017.0749).

论文的序贯流程用代理近似昂贵黑盒目标，选择下一批需要真实高代价评估的位置。这支持本项目只用surrogate排序有限候选或提出下一次oracle调用。

**限制：**代理用于节省候选筛查成本，不是数学证书；该文并未赋予任一代理不确定带严格覆盖性质。当前项目的搜索代理不得单独淘汰潜在Pareto候选、判候选可行或替代有限RayOracle。

## S04. 估计型求积与自验证求积的区别

**George F. Corliss, L. B. Rall.** “Adaptive, Self-Validating Numerical Quadrature.” *SIAM Journal on Scientific and Statistical Computing*, 8(5), 831–847, 1987. [DOI: 10.1137/0908069](https://doi.org/10.1137/0908069). [SIAM原始期刊页](https://epubs.siam.org/doi/10.1137/0908069).

论文用区间计算捕获求积余项和舍入误差，按每个子区间“保证的”误差信息做自适应拆分。可支持本报告中“严格数值包络需要可验证余项和舍入传播；普通adaptive error估计、base/tight吻合或网格差不是同一证据等级”的划分。

**限制：**它是特定单变量算法/运算实现的数值分析论文，不证明T02的双重source-time积分、遮挡事件、binary64几何和真实材料响应已被认证；要获得相同保证，须实现并验证适用的区间/余项链。

## S05. 区间运算接口标准

**IEEE Standards Association.** *IEEE Std 1788-2015, IEEE Standard for Interval Arithmetic*. [IEEE SA原始标准记录](https://standards.ieee.org/ieee/1788/4431/).

标准组织说明该标准定义基础区间运算模型、浮点格式支持、异常条件及处理。它可作为区间实现接口、异常/空/无界语义与向外舍入审核的检查依据。IEEE网页同时标明1788-2015现为 inactive-reserved，页面列出简化版1788.1-2017；本引用记录标准曾规定什么，不把旧标准状态误说为当前激活版本。

**限制：**引用标准不代表当前代码已声明或验证符合标准。即使一个区间库实现标准运算，也不能自动证明输入区间涵盖实际物理不确定性，或模型将所有source/time/kernel/model误差都纳入。

## 与本项目的映射

- S01：有界不确定集、componentwise worst-case和区间加密语义。
- S02：重叠的不确定目标值应限制过早排序，必要时向影响排序的轴增加信息。
- S03：昂贵代理只决定搜索顺序或提案，真实冻结oracle评价才形成项目内证据。
- S04–S05：只有具备区间/余项/浮点包络链，才可把估计标签提升为可信上下界；来源差异本身不能当严格界。

S01–S05不能补全T02缺少的连续源支集、未知rate、空间连续极值、实机几何、材料响应、校准或生产容差。当前项目使用它们确定方法边界，不把论文中的保证直接移植到本项目模型。
