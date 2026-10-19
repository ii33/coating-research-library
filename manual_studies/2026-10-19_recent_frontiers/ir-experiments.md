# 多光谱红外选择性薄膜：原始实验核查

检索截止：2026-10-19。范围为2019年以来的原始期刊论文，优先实物光谱、温度和成像实验。以下并非穷尽目录。除特别注明外，数值为论文作者报告值，未作跨论文归一化。

## 核心判断

- “3–5/8–14 μm低发射 + 5–8 μm散热 + 可见/激光/微波兼容”至少在2021年已有实物集成证据，不能作为2026年首创叙述。
- 近年的实质结构进展在于：向SWIR扩展、增加第二散热窗口、700°C高温兼容、米级柔性低成本制造、加入超光谱与空间纹理控制。它们解决的是不同约束，并不存在一个所有指标均胜出的新结构。
- 新优化方法应单列：BO/TMM与NSGA-II/TMM主要改变搜索效率、目标表述和权衡方式；它们不能代替光谱、制备容差、实际热平衡和测量验证。
- 需严格区分微波透射、微波吸收、成像背景匹配三种功能；“透波”本身不是雷达吸收。需区分真实温度下降与热像仪表观温度下降。

## 五篇优先证据

### 1. 多波段集成实验基线，2021

Zhu et al., *Multispectral camouflage for infrared, visible, lasers and microwave with radiative cooling*, Nature Communications 12, 1805 (2021).

- DOI：[10.1038/s41467-021-22051-0](https://doi.org/10.1038/s41467-021-22051-0)
- 原文：[期刊全文](https://www.nature.com/articles/s41467-021-22051-0)
- 结构类别：Ge/ZnS平面选择性发射膜与Cu–ITO–Cu微波吸收超表面的分层集成，含可见结构色和激光吸收功能。
- 实验：光谱、MWIR/LWIR热像、恒功率温度和微波吸收等。报告ε3–5/8–14为0.11/0.12，ε5–8为0.61，8–12 GHz吸收>0.9；兼容1.55与10.6 μm激光。
- 热性能：2500 W/m²输入时，相比Cr对照，内部/表面真实温度降低8.4/5.9°C，MWIR/LWIR信号降低53.4%/13.0%。
- 限制：这是不同波段功能层的集成，不能称单一均匀薄膜覆盖全部波段。室内热像含反射环境辐射；实验不等于所有环境/距离下均不可探测。10.6 μm吸收峰与LWIR低发射本身有带宽权衡。

### 2. 全红外扩展与双散热窗，2023

Qin et al., *Whole-infrared-band camouflage with dual-band radiative heat dissipation*, Light: Science & Applications 12, 246 (2023), published 2023-10-04.

- DOI：[10.1038/s41377-023-01287-z](https://doi.org/10.1038/s41377-023-01287-z)
- 原文：[期刊](https://www.nature.com/articles/s41377-023-01287-z) / [PMC全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC10550919/)
- 结构创新：免光刻7层Al₂O₃/Ge/Al₂O₃/Ge/ZnS/GST/Ni；4英寸Si上制备，新增SWIR与2.5–3 μm热出口的联合管理。
- 实测：εSWIR/MWIR/LWIR=0.270/0.042/0.218；ε2.5–3/5–8=0.742/0.473；VIS/NIR平均反射率0.129/0.281。恒功率2000 W/m²下较Cr真实表面温度降低14.4°C。含太阳照射下的室外SWIR成像。
- 限制：同温200°C时LWIR表观温度实际上高于Cr约24°C，不能写成双IR窗口均优于Cr；低反射主要产生暗色，不等于任意背景颜色/超光谱匹配。没有同时验证微波吸收。

### 3. 700°C实物多红外/微波兼容，2025

Zhao et al., *High-Temperature Stealth Across Multi-Infrared and Microwave Bands with Efficient Radiative Thermal Management*, Nano-Micro Letters 17, 199 (2025), published 2025-03-24.

- DOI：[10.1007/s40820-025-01712-5](https://doi.org/10.1007/s40820-025-01712-5)
- 原文：[Springer全文](https://link.springer.com/article/10.1007/s40820-025-01712-5) / [期刊](https://www.nmlett.org/index.php/nml/article/view/1983)
- 结构创新：Mo/Si红外选择膜与TiB₂–Al₂O₃–TiB₂微波超表面集成，并通过激光分割使上层透微波。
- 实测：700°C时εMWIR/LWIR/SWIR=0.38/0.44/0.60，ε5–8=0.82；9.6–12 GHz反射损失低于−3 dB。高温光谱、三红外热像和微波暗室测试均有证据。
- 热性能：约17.3 kW/m²电加热下，相比Mo真实温降72.4°C；文中9.57 kW/m²为该温度的辐射散热量，不应当作所有环境下净制冷功率。
- 限制：−3 dB只是约一半功率反射阈值，弱于常见−10 dB吸收带标准。光谱随温度升高变化，750°C退化。“Mach 2.2”来自等效气动热输入，未进行真实飞行或风洞验证。主文不同位置出现17.3/17.4 kW/m²，引用宜写“约17 kW/m²”。

### 4. 米级Al/PA66柔性制造与宽角实验，2026

Jiang et al., *Hierarchical design and scalable production of radiative cooling film featuring multispectral camouflage*, Nature Communications 17, 2253 (2026), published 2026-02-02.

- DOI：[10.1038/s41467-026-69045-4](https://doi.org/10.1038/s41467-026-69045-4)
- 原文：[PMC全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC12966451/) / [作者机构PDF](https://light.nju.edu.cn/upload/file/20260309/s41467-026-69045-4_202603091107234969.pdf)
- 结构创新：以分子振动谱筛选PA66，卷对卷电纺随机纤维/Al双层，米级柔性成膜，低成本路线明显区别于精密多层干涉膜。散热窗为5–8和14–20 μm，可加颜料和PE封装。
- 实验：光谱、室内/室外真实温度、MWIR/LWIR热像、±60°观察角、10.6 μm激光背向信号、服装/假人演示。室内相对裸Al温降5–10°C，降温与PA66厚度及红外发射抑制存在权衡。
- 关键释义：论文的“indoor simulated experiment”是用量子级联激光及光功率计进行的实物回波实验，不能误列为“只有数值仿真”。
- 限制：厚度增加会降低窗口反射率，不能只引用冷却最强样品再配最低发射率样品。没有微波/雷达实验；激光实验没有证明实地全角度探测距离。

### 5. NSGA-II多目标逆设计与制备验证，2025；属于优化线

Shi et al., *Inverse design of visible-infrared multispectral camouflage with radiative cooling and microwave transmission*, Materials Today Physics 55, 101759 (2025).

- DOI：[10.1016/j.mtphys.2025.101759](https://doi.org/10.1016/j.mtphys.2025.101759)
- 原文：[ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2542529325001154) / [出版商摘要和方法片段](https://www.sciencedirect.com/science/article/abs/pii/S2542529325001154)
- 优化新意：NSGA-II+TMM寻找Ge/ZnS多层的多目标解，避免将所有目标预先固定为单一加权和；论文报告400次迭代。这个迭代数不是400次全部光学调用，也不能脱离种群/设计空间比较算法优劣。
- 实验：电子束蒸镀于Si和柔性PI。出版商摘要报告100°C下相对Si有显著MWIR/LWIR表观信号改善，以及约5°C额外实际温降。
- 限制：2–18 GHz功能为微波透射，不能直接称该薄膜完成雷达吸收。摘要对38.5%/33%描述为温度降低百分比，二手报道又称辐射强度降低；未取到对应完整图表前不应把这两个百分数写成确定的信号降幅。代码需向作者合理索取，未核到公开代码库。

## 可选扩展证据

### 2023 BO/TMM：优化方法而非全新材料物理

Xi et al., Nature Communications 14, 4694, published 2023-08-04. DOI [10.1038/s41467-023-40350-6](https://doi.org/10.1038/s41467-023-40350-6)，[PMC全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC10403604/)。BO/TMM优化Ge/ZnS的颜色、热平衡后的8–13 μm信号比及±2%膜厚敏感性；候选为60,416个离散配置，约1%采样找到较好解，并有8种颜色样品验证。限制：不是开放式任意材料/连续厚度的全局最优证明；MWIR、激光和雷达未同时验证。其温度耦合目标和制造容差惩罚，比单纯最小化窗口平均ε更值得借鉴。

### 2025 太空热边界：散热窗口应按工况改换

Qin et al., Light: Science & Applications 14, 137, published 2025-03-26. DOI [10.1038/s41377-025-01824-y](https://doi.org/10.1038/s41377-025-01824-y)，[原文](https://www.nature.com/articles/s41377-025-01824-y) / [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11947227/)。6层、总厚约4.25 μm，εMWIR/LWIR=0.132/0.142，ε13–25=0.798；H/K吸收0.839/0.633。真空腔+冷杜瓦模拟空间中，1200 W/m²时较金属降39.8°C。室外卫星模型成像为实物实验，轨道周期温度/探测信号则是计算。对近室温太空热管理，13–25 μm比仅5–8 μm更重要；不能把所有“隐身+冷却”固定为同一目标模板。

### 2025 超光谱/空间纹理：新目标维度，不是散热新纪录

Zhu et al., *Digital camouflage encompassing optical hyperspectra and thermal infrared-terahertz-microwave tri-bands*, Nature Communications 16, 8112, published 2025-08-30. DOI [10.1038/s41467-025-63563-3](https://doi.org/10.1038/s41467-025-63563-3)，[原文](https://www.nature.com/articles/s41467-025-63563-3)。柔性多层像素+激光蚀刻子像素+商用微波吸收底层，实际测得VIS–SWIR反射谱、MWIR/LWIR发射谱、THz/MW成像及热像。100°C目标的10 m红外成像接近背景；其要点是光谱/强度/纹理联合匹配。THz/X-band的0.1 m成像为实测，0.4 m结果为仿真，不能统称远距离实测。论文明确热IR/THz/MW图案尚未充分独立优化；未建立5–8 μm净散热优势。适合列在“背景与纹理匹配”，不宜混入选择性冷却性能排行。

### 2026 六层最简膜：有实物，精确数值待全图表复核

Li et al., *Scalable and minimalist multilayer films for visible-laser-infrared camouflage with thermal management*, Applied Thermal Engineering 300, 131455 (2026). DOI [10.1016/j.applthermaleng.2026.131455](https://doi.org/10.1016/j.applthermaleng.2026.131455)，[出版商](https://www.sciencedirect.com/science/article/pii/S1359431126017631)。Cr/ZnS/Ge/Pt/Ge/ZnS六层、PSO优化且电子束蒸镀，公开摘要报告双激光1.064/1.55 μm吸收约0.97及可见颜色调节。应列“实验候选”，不宜称优化算法创新。摘要的窗口ε=0.15/0.30，与公开Results片段的0.23/0.25不一致；尚不清楚是否模拟/实验、不同样品或平均方法差异。未获取完整对应图表前，不采用这一组精确值作仿真验收目标。

### 2026 多维偏振兼容：值得注意的新维度

Qin et al., *Multi-dimensional camouflage against VIS-NIR hyperspectral, MIR intensity, and MIR polarization imaging*, Light: Science & Applications 15, 63, published 2026-01-12. DOI [10.1038/s41377-025-02145-w](https://doi.org/10.1038/s41377-025-02145-w)，[期刊全文](https://www.nature.com/articles/s41377-025-02145-w)。粗糙PE/Ag纳米线/Cr₂O₃复合涂层，通过热压与刮涂制造；实测LWIR半球发射率约0.7、0°–85°线偏振度<1.5%、VIS–NIR植被谱相似度>96.9%，含实地强度及偏振成像。局限：并不是极低发射率膜或选择性5–8 μm散热纪录；偏振抑制、VIS–NIR透射和LWIR反射有权衡，MgCl₂潮解与WPU热稳定性也限制应用。DOI含2025不代表出版于2025。

### 2026 动态双窗口切换：不能写成双窗口同时低发射

Chen et al., *Broadband opto-thermal camouflage and infrared encrypted communication via inverse design*, Light: Science & Applications 15, 275, published 2026-06-22. DOI [10.1038/s41377-026-02370-x](https://doi.org/10.1038/s41377-026-02370-x)，[期刊全文](https://www.nature.com/articles/s41377-026-02370-x) / [PubMed](https://pubmed.ncbi.nlm.nih.gov/42331791/)。BO/TMM逆设计包含VO₂的七层结构，4英寸及柔性实物、0.38–2.5 μm光学伪装、结构色色域约66% CMYK；15个样品的MWIR/LWIR发射率由约0.41/0.90切换到0.93/0.45，采用各相态温度的Planck加权平均。它展示热窗口选择和光热解耦，两个IR窗口并非同时低发射，也未建立5–8 μm散热纪录。主动加热实现热通信会增加热辐亮度，作者明确承认热伪装/热通信权衡；没有雷达覆盖，高分辨/超光谱鲁棒性仍待验证。BO是现成方法，主要新意为结构与功能整合。

## 应明确排除出“已实验证明”名单的例子

- *Dual-dielectric Fabry-Perot film for visible-infrared compatible stealth and radiative heat dissipation*, Optics Communications 574, 131173 (2025), DOI [10.1016/j.optcom.2024.131173](https://doi.org/10.1016/j.optcom.2024.131173)。出版商摘要明确基于simulation；W/Ge/SiO₂/W/SiO₂及ε3–5=0.038、ε8–14=0.200、ε5–8=0.487不能标为实测。
- *Metamaterial structure design based on genetic algorithm and phase change material GST for multispectral camouflage*, DOI [10.1016/j.micrna.2024.207985](https://doi.org/10.1016/j.micrna.2024.207985)，[出版商](https://www.sciencedirect.com/science/article/abs/pii/S2773012324002346)。摘要明确“numerical analysis”，GA+GST不构成实验动态器件证据。
- *Multispectral Camouflage Photonic Structure for Visible–IR–LiDAR Bands with Radiative Cooling*, Photonics 13(1), 31 (2026), DOI [10.3390/photonics13010031](https://doi.org/10.3390/photonics13010031)，[原文](https://www.mdpi.com/2304-6732/13/1/31)。21层Ge/YbF₃+二维a-Si微结构的摘要以FDTD确认性能；不能因标题或“measurement”小节字样，就假定整个复合结构及所有波段均已制备实测。

## 研究项目可采用的证据分级和评价原则

1. 平面多层仿真优先用2023全红外7层与2021 Ge/ZnS做可复核的结构/光谱基线；高温必须加入温变n,k或实测ε(T)，不可沿用室温常数。
2. 分开记录结构创新、搜索算法、实测光谱、热平衡验证、环境成像。每个性能值均绑定样品、温度、入射角、波段平均方式与对照。
3. 发射率需要按任务定义加权：算术波段平均、Planck加权与探测器响应加权并不相同。反射环境辐射、太阳加载、非辐射换热和观察角都影响可见信号。
4. 5–8 μm高发射意味着可向较冷环境交换辐射热，不等于通过透明大气窗向太空实现亚环境温度冷却。净冷却与应用温度及环境边界有关。
5. 优化迁移重点应是Pareto前沿、制造容差与温度耦合目标，而不是把PSO换成另一个算法名称就声称取得新的光学机制。
