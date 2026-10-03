# 主来源摘要及采用边界

访问日期2026-10-02 UTC。以下均为原作者、期刊开放原文或官方技术资料。报告的有限厚板投影、事件积分和合成数字由本包独立推导；未复制第三方图、长段原文或代码。全文本地留档与公开分发严格分开。

## S01 可见性导数的边界贡献

Tzu-Mao Li, Miika Aittala, Frédo Durand, Jaakko Lehtinen. Differentiable Monte Carlo Ray Tracing through Edge Sampling. ACM TOG 37(6), 2018。

[作者项目页](https://people.csail.mit.edu/tzumao/diffrt/)；[论文原文](https://people.csail.mit.edu/tzumao/diffrt/diffrt.pdf)；[作者勘误页](https://people.csail.mit.edu/tzumao/diffrt/errata.html)。核读第3节、式6–7及Fig.2–3：光滑区域求导与不连续边界贡献分开，普通区域采样无法自动捕获后者。采用的是这个结构性结论。本研究不是其算法复现，且该论文场景/光源假设不同；不把其无偏渲染结论套给本包的有限源求积。勘误页已查，本包未抄录其中被修正的投影公式。原文可公开访问，本地研究保存；不假定再分发授权，全文排除读者包。

## S02 事件时序、横截条件和共同事件

Nathan J. Kong, J. Joe Payne, James Zhu, Aaron M. Johnson. Saltation Matrices: The Essential Tool for Linearizing Hybrid Dynamical Systems. Proceedings of the IEEE 112(6), 585–608, 2024，DOI 10.1109/JPROC.2024.3440211。

[arXiv v3原文](https://arxiv.org/html/2306.06862v3)；[PDF](https://arxiv.org/pdf/2306.06862)。核读III-A/B及其横截假设、联合guard讨论：事件时间的变化不能仅靠reset Jacobian表达，多事件同时触发会超出单一普通转移公式。本包累计沉积量没有机械冲击reset，使用独立的Leibniz推导，不直接移植机器人碰撞模型。arXiv页显示CC BY 4.0且正文另有IEEE使用声明；保守地只本地存档全文，读者包仅此短摘要与公开链接。

## S03 编码几何的稳健谓词

Jonathan Richard Shewchuk. Adaptive Precision Floating-Point Arithmetic and Fast Robust Geometric Predicates. Discrete & Computational Geometry 18, 305–363, 1997。

[作者技术页面](https://www.cs.cmu.edu/~quake/robust.html)。本轮读取官方作者页面而非重新下载/复核全文。采用点：接近退化位置时，浮点符号误判可改变几何拓扑，稳健谓词与普通epsilon分支应区分。本文使用此前T02已冻结的标准库有理slab参考，并非Shewchuk源码；不会宣称其对已编码几何的结果认证了未测实物。页面本地归档，全文/网页均不进reader。

## S04 联合分布传播的适用条件

JCGM 101:2008. Evaluation of measurement data — Supplement 1 to the GUM — Propagation of distributions using a Monte Carlo method。

[BIPM官方原文](https://www.bipm.org/documents/20126/2071204/JCGM_101_2008_E.pdf)。核读5.10、7–8，特别是联合输入、输出分布和有效性条件。本报告将相关性传播与几何分支变化分开；没有执行该标准的正式Monte Carlo程序或作覆盖概率认证。该官方文档可自由读取但有保留权利标识，合法本地研究副本被排除发布。

## S05 镀膜角核不是统一材料常数

Lichao Zhang, Xikun Cai. Uniformity Masks Design Method Based on the Shadow Matrix for Coating Materials with Different Condensation Characteristics. The Scientific World Journal, 2013:160792，DOI 10.1155/2013/160792。

[PMC开放原文](https://pmc.ncbi.nlm.nih.gov/articles/PMC3817662/)。核读式1及理论/实验讨论：发射与凝结角因子的选择影响板形响应；经验凝结指数必须在明确工艺下解释。引用用于标明本包cosine/cosine模型的条件性，不借用其实验数字作为用户机器精度。原文为CC BY开放文章，首轮已有合法本地副本，本轮原字节复制归档但仍不纳入读者分发。

## 未采用的外推

没有引用论坛经验作为事件算法证明，没有以第三方蒙特卡洛图形性能估计当前设备速度，没有把文献的实验均匀度写成此次机器的合格结果。主来源提供方法脉络；合成公式、程序和误差判定以本包明确合同为准。
