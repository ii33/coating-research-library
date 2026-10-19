# 近期前沿：确缺资料与复算缺口清单

核查日期 2026年10月19日

前三区分为最能改变近期研究判断的优先项；后三项主要影响材料与器件的数值复算。已有可用公开版本的OptoGPT、OptoLlama，以及大部分红外实验原文无需重复寻找。SAGD已有官方代码，缺的是论文正文与补充材料。这里列的是确实尚缺的细节，不要求用户代替检索已公开的内容。

## 1 GNA刚正式在线论文的正文与补充材料

- 准确题名：Interpretable inverse design of optical multilayer thin films based on global neural adjoint
- 作者：Sungjun Kim and Jungho Kim
- DOI：10.1038/s41598-026-75220-w
- 原文：https://www.nature.com/articles/s41598-026-75220-w
- 已有：出版社完整摘要、2026年10月12日同行评审早期在线状态、作者与刊载信息。摘要已说明对部分目标的峰值准确率、多样性收益，以及某些工艺约束任务的更高计算代价。
- 确缺：正文PDF和Supplementary Information的可读内容；若正文另列正式代码、数据或权重链接，也需据此核实。目前没有确认它们已公开，不能说只缺下载。
- 用途：核查训练集/材料范围、GA与OptoGPT公平预算、连续材料松弛与离散化误差、每epoch时间是否能转化为总任务收益。网页在本轮工具路径被Nature身份跳转阻断，不等于论文付费或用户无权访问。

## 2 SAGD稳健可微薄膜论文的正文与补充材料

- 准确题名：Sharpness-Aware Minimization for Robust Inverse Design of Nonlocal Thin Films
- 作者：Yuchen Ma, Guangwei Hu and Liangcai Cao
- DOI：10.1002/lpor.71366
- 原文：https://onlinelibrary.wiley.com/doi/10.1002/lpor.71366
- 已有：出版社摘要、2026年6月23日正式在线信息、数据声明，以及官方仓库 https://github.com/THUHoloLab/SAGD 的完整核心示例源码。
- 确缺：论文正文与Supplementary Information的可读PDF（期刊补充文件名 lpor71366-sup-0001-SuppMat.pdf）；实验光谱/成像的原始数据、完整经典优化基线与制造扰动评估脚本尚未在公开库核到。用户找正文和SI会有帮助，缺失代码/原始数据则需看作者是否另有附件或提供。
- 用途：核实所称制造容差究竟用什么厚度和n,k误差分布、各基线是否相同预算、多少独立运行、真实器件与模拟预测的偏差。现有示例的50nm是整个厚度向量L2扰动半径，不能替代论文里的逐层制造容差定义。

## 3 2025 NSGA II多光谱红外实验全文与复现细节

- 准确题名：Inverse design of visible-infrared multispectral camouflage with radiative cooling and microwave transmission
- 作者：Shi et al.
- DOI：10.1016/j.mtphys.2025.101759
- 原文：https://www.sciencedirect.com/science/article/pii/S2542529325001154
- 已有：出版社摘要、样品制备方法片段、NSGA-II/TMM与400次迭代描述、Si和柔性PI基底及真实制备证据。
- 确缺：全文对应图表与Supplementary Information中的完整层序/厚度/n,k、各样品性能对应关系、种群规模和全部求解预算、实验原始光谱与优化代码。代码属于向作者合理索取，未核到现成公开仓库。
- 用途：厘清摘要38.5%/33%究竟对应温度量还是辐射信号，防止误当作确定信号降幅；建立实际可复现的多目标IR实验基准。微波功能已可确定是透射，不能写成自身吸波。

## 4 金属玻璃与ENZ薄膜的全文及补充材料

- 标题：Epsilon-near-zero thin films in a dual-functional system for thermal infrared camouflage and thermal management within the atmospheric window
- DOI：10.1039/D4MH00711E
- [期刊页面](https://pubs.rsc.org/et/content/articlelanding/2024/mh/d4mh00711e)
- 已有：作者、出版时间、摘要、器件机制、角域、性能概述；期刊上的补充入口已核到。
- 真正缺少：金属玻璃的准确合金组成与制程、各层厚度、材料光常数的测量/引用出处、温度与热实验细节。当前补充入口指向d4mh00711e1.pdf但返回404；全文加载也未成功。这是三项中最需要全文的一项。

## 5 2026 IST器件的Supporting Information S1

- 标题：Non-Volatile In3SbTe2 Multispectral Responsive Emitter With Visible Color and Infrared Display-Erasure Function
- DOI：10.1002/nap2.70084
- [已读完整正文](https://onlinelibrary.wiley.com/doi/10.1002/nap2.70084)
- 需要的文件：nap270084-sup-0001-suppl-data.docx，期刊页面的Supporting Information S1入口。
- 已有：完整层序/厚度、沉积和300°C退火工艺、测量谱与角度热像、仪器及材料表征。
- 真正缺少：S1中的IST两相光常数、S6的温度稳定范围和S13的角谱细节，以及是否附原始数值表。正文没有本器件再非晶化或循环数据，需确认补充材料有无补证；若没有，就保留缺口，不需寻找不存在的数据。

## 6 2023 非周期Ge与ZnS器件的补充结构信息

- 标题：Ultrahigh-efficient material informatics inverse design of thermal metamaterials for visible-infrared-compatible camouflage
- DOI：10.1038/s41467-023-40350-6
- [已读完整正文](https://pmc.ncbi.nlm.nih.gov/articles/PMC10403604/)
- 需要的文件：Supplementary Information，41467_2023_40350_MOESM1_ESM.pdf；如方便，连同Supplementary Dataset 1的XLSX。
- 已有：主文结构规则、八个样品的测量与角度/温度实验、材料手册来源和数据声明。
- 真正缺少：逐样品实际合并后层序/厚度表与基片说明，以澄清主文quartz和Methods中Si的矛盾；XLSX用于取得实测曲线数值。不是缺整个论文，也不是声称论文提供了同批温变n/k。本轮补充PDF访问遇到检索端验证码；未尝试绕过。


## IrisFlow无需重复找PDF

IrisFlow最新v2正文与64页含补充PDF已读到：https://arxiv.org/abs/2607.08392v2 。目前真正缺的是作者尚未公开的完整实现、训练/测试数据与权重；官方仓库https://github.com/z-one-l/IrisFlow只有说明等文件，注明发表后发布。这需要等待作者发布或获得作者授权材料，用户再找一份PDF不会解决。搜索结果仍缓存v1实验表述，使用时应以v2为准。


本清单不重复前轮经典文献全文缺件。上述“未取得”描述本次访问状态，不推断付费、无权访问或原论文不存在数据；原始数据和代码是否存在应以正式附件、数据声明或作者提供为准。
