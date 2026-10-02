# T10 独立来源核查：Kaufman 栅控离子源及四类材料的证据边界

核查日期：2026-10-02（UTC）。范围限于文献与厂商资料；未操作设备、未改产品代码、未推送。以下不是设备操作规程或可直接执行的沉积配方。

## 1. 可立即纳入主文档的结论

1. **分源型**：Kaufman 热阴极/DC 栅控源、RF 栅控源、gridless End-Hall 应分开。KRI 是厂商名，不能据此认定所有 KRI 资料都是 Kaufman 栅控源。尤其 Kennedy 1998 MgF2/YbF3 论文明确使用 End-Hall；Dumas 2001 实验片段同样写 End-Hall。
2. **双/三栅不是优劣排名**：双栅 screen/accelerator 常见；三栅添加下游、通常接地的 decelerator。三栅可改善某些低净/总加速电压比下的聚束，但有栅截流、返流阈值、工作窗口与维护折衷，不能写成“能量、通量完全解耦”或“三栅必然更好”。[S1, S5]
3. **束电流不等于基片局部通量**：总束电流、放电电流、栅截流与基片面电流密度是不同量。发散、源距、角度、遮挡与运动改变局部剂量；加大负加速电压即便提高提取电流，也可能因发散减少到靶电流。[S1, S4]
4. **中和不等于把离子全部变为中性原子**：space-charge neutralization 是体积电荷近似平衡；current neutralization 是相应电流平衡。低压下电子-快离子复合不构成主要快中性化机制。荷交换却会生成快中性原子与慢离子，普通电探针无法等价计量其处理效应。[S2, S3]
5. **水冷须按型号/组件核实**：KRI 官方 KDC160 产品页明说源本体无需水冷。这足以否定“所有 Kaufman 源都须水冷”的写法。基片台、射频部件、腔体等是否水冷是另一个问题。[S7]
6. **化学风险须分材料与波段**：MgF2 的失氟、氧掺入及光学损耗有原始证据，但氧辅助可同时降低某些可见/IR损耗并带来其他代价。YbF3 的特定氧化相、ZnS 的普遍“优先失硫”、Ge 在任意低能 O2-IAD 下的氧化速率，均不应被写成此次已经证明的定量结论。[M1–M8]

## 2. 仪器物理与安全来源卡

### S1 — KRI TN-01：Broad-Beam Industrial Ion Sources
- 原始 URL：https://ionsources.com/wp-content/uploads/2024/01/TN-01_Broad-Beam-Industrial-Ion-Source-Resource.pdf
- 访问等级：厂商官方 PDF 全文，4页；正文第1页，PDF第2页，Gridded Ion Sources。
- 可支持：双栅最常见；负 accelerator 抑制中和电子反向进入；正确工作且近似单电荷、靶近地时，离子 eV 近似对应 beam supply 的 V；提高总栅间电压会改变可提取束流；三栅仅部分缓解大负加速电压下的发散。
- 限定/未知：文中 gridded 同时涵盖 DC 与 RF；End-Hall 的放电电压/平均能量比例属于另一源型，不移植为 Kaufman 换算。单电荷和近地靶是假设，非任意电荷态、基片电位和碰撞条件下的恒等式。

### S2 — KRI TN-02：Ion-Beam Neutralization
- URL：https://ionsources.com/wp-content/uploads/2024/01/TN-02_Ion-Beam-Neutralization-Resource.pdf
- 访问等级：厂商官方 PDF 全文，4页；正文第1–2页。
- 可支持：区分复合、空间电荷中和、电流中和；栅控源中中和器发射电流与束电流关联，gridless 则与放电电流关联。绝缘靶和已被介质镀覆的腔壁会改变电荷泄放。中和不足可能发散或放电并损伤工件；须在实际靶位检查电位及瞬态。
- 限定/未知：图2的量化实验是 End-Hall，不是 Kaufman。厂商针对不同接地/绝缘场景给不同建议，不能摘一个发射/束流比例作为普遍设置。中和器发射读数也不直接证明基片已无电荷。

### S3 — KRI TN-03：Charge and Momentum Exchange in an Ion Beam
- URL：https://ionsources.com/wp-content/uploads/2024/01/TN-03_Charge-and-Momentum-Exchange-in-an-Ion-Beam-Resource.pdf
- 访问等级：厂商官方 PDF 全文，3页；正文第1页。
- 可支持：荷交换可产生保留较大动能的中性粒子与低能离子；简单电探针漏计前者而可能收集后者。因此电流衰减不等价于全部能量通量消失。
- 限定/未知：平均自由程依赖气体、能量、背景数密度与具体碰撞截面。不得把室温气体动量碰撞平均自由程直接作为数百 eV 束的能量损失尺度；不得把 Ar 的曲线直接搬给 O2 混合束。

### S4 — KRI TN-05：Ion-Assist Doses
- URL：https://ionsources.com/wp-content/uploads/2024/01/TN-05_Ion-Assist-Doses-Resource.pdf
- 访问等级：厂商官方 PDF 全文，4页；正文第1–2页。
- 可支持：剂量应联系沉积到达率与每沉积原子获得的能量；基片平均电流密度要经过几何和接收比例换算；MgF2 有易挥发元素耗损问题。表内括号值是估算，MgF2 的括号值不是该表直接实测。
- 限定/未知：装置示例为 EH1000 End-Hall；表中“100 eV、1 Å/s”是假定的比较基准。原文明确数值只是试验起点。不得升级为 Kaufman 的最佳束压、材料通用窗口或安全阈值。

### S5 — Kaufman & Robinson, NASA-CR-165334 (1981)
- 题名：Ion Source Design for Industrial Applications。
- 官方记录：https://ntrs.nasa.gov/citations/19810016343
- 全文：https://ntrs.nasa.gov/api/citations/19810016343/downloads/19810016343.pdf
- 访问等级：NASA 官方原始技术报告全文，92页；Double Ion Production 纸页14–15，Three-Grid Optics 纸页31–35。
- 可支持：第三栅在 accelerator 下游接地；低净/总加速电压比可获得较好聚束，但工作窗口受限。Ar 多电荷比例依放电条件、气体供给与源尺寸变化，不能一概视为纯 Ar+。
- 限定/未知：历史设计研究不是现代具体型号的验收参数；OCR 的百分号/公式易错。本文不转录多电荷比例或栅孔设计数值，也不把历史比例当新设备规格。

### S6 — KRI KDC10 + KSC1202 原厂手册 (2012)
- URL：https://engineering.purdue.edu/CMUXE/Manuals/Ion%20guns/Ion%20gun%20KDC-10%20Manual.pdf
- 访问等级：高校托管的原厂手册全文，120页；KDC10 §1、§2、§4.2/4.5/4.6；KSC1202 §3.4.1。
- 可支持：KDC10 为 DC 双石墨栅、可配热丝中和器；电子返流会使束流指示出现假贡献；最大束流受栅光学或热限制。维护需先隔离电源并确保不能再加电。控制器明确警告联锁不是人身安全保护，维修前需切断 AC。
- 限定/未知：这不是待研究设备的型号手册；不引用其引脚或操作顺序作为建议。没有从该手册证明普适水冷要求。现代控制器的储能放电、接地、门/真空/水流联锁须依本机最新版手册及单位规程核定。

### S7 — KRI KDC160 官方规格
- URL：https://ionsources.com/products/kdc160/
- 访问等级：厂商官方产品页全文，访问2026-10-02。
- 可支持：该 DC 栅控源明确无需水冷源本体。
- 限定/未知：仅为该产品配置的反例；不能据此认定整套镀膜机无需冷却，也不能反推出其他源的流量/温度设定。

## 3. 材料化学风险来源卡

### M1 — Gibson & Kennemore, 1985：MgF2 / Ar
- 题名：Ion-assisted deposition of MgF2 at ambient temperatures；DOI：https://doi.org/10.1016/0040-6090(85)90024-0
- 出版社页：https://www.sciencedirect.com/science/article/pii/0040609085900240/pdf?md5=5e6304c1f62d77b8705511d4076a3994&pid=1-s2.0-0040609085900240-main.pdf
- 访问等级：出版社元数据与摘要，未核全文；URL 名称含 PDF 不等于已取到全文。
- 精确支持：未加热基片、低于250 eV的 Ar 辅助下，耐磨/附着改善；RBS 显示一定失氟；UV边红移，但未见显著额外可见吸收。
- 边界：摘要不足以确认源型、离/原子比与均匀性；这是“风险与收益共存”的证据，不是所有 Ar-IAD 都有高可见吸收。

### M2 — Martin et al., 1987：MgF2 / O2 与 Ar
- 题名：Influence of ion assistance on the optical properties of MgF2；DOI：https://doi.org/10.1364/AO.26.001235
- 摘要：https://pubmed.ncbi.nlm.nih.gov/20454308/
- 访问等级：原始论文的 PubMed 元数据/摘要；未核全文。
- 精确支持：氧离子辅助提高小于180 nm波长处消光系数；作者由RBS推断MgO存在并将其提出为VUV损耗主要因素。
- 边界：“由RBS推断/提出”不能升级为直接相鉴定；不可外推到所有可见光、MWIR/LWIR范围，更不能据此断言O2总是使吸收上升。

### M3 — Kennedy, Ristau & Niederwald, 1998：MgF2、YbF3 / 气体比较
- DOI：https://doi.org/10.1016/S0040-6090(98)00847-5
- 出版社页：https://www.sciencedirect.com/science/article/pii/S0040609098008475
- 访问等级：原始论文摘要及出版社部分正文片段，全文付费未核。
- 精确支持：**gridless End-Hall MarkII**；室温沉积；比较Xe、Ar、Ar–O2，优化后Xe表现优于后两者；优化YbF3耐久性改善，vis无显著吸收。片段给沉积率0.7–1 nm/s、约250 nm膜厚。
- 边界：不能将Xe优势表述成Kaufman已验证规律；可见片段未足以证明Yb2O3/YbOF等特定产物，也未取得可复现的YbF3剂量–成分相图。

### M4 — Dumas et al., 2001：MgF2 / Ar
- 题名：Characterization of magnesium fluoride thin films produced by argon ion beam-assisted deposition；DOI：https://doi.org/10.1016/S0040-6090(00)01414-0
- 出版社页：https://www.sciencedirect.com/science/article/abs/pii/S0040609000014140
- 访问等级：原始论文摘要和部分正文片段，未核全文。
- 精确支持：结构/组分/密度/应力受Ar通量、能量与沉积率合成的归一化动量影响；实验片段注明**End-Hall**。
- 边界：论文的约55归一化动量转折不是通用能量阈值，更不是55 eV。仅做跨设备趋势参考，不照搬为Kaufman配方。2002后续论文DOI 10.1116/1.1424276此次只取得第三方文本，不提升为已核全文主证据。

### M5 — Zhang et al., 2019：MgF2 / O2，明确称 Kaufman
- 题名：Influences of Oxygen Ion Beam on the Properties of Magnesium Fluoride Thin Film Deposited Using Electron Beam Evaporation Deposition；DOI：https://doi.org/10.3390/coatings9120834
- 出版社：https://www.mdpi.com/2079-6412/9/12/834
- 作者机构存档：https://research-portal.uws.ac.uk/files/53268625/2019_12_03_Zhang_et_al_Influences_final.pdf
- 官方重印本：https://mdpi-res.com/bookfiles/book/3800/Current_Research_in_Thin_Film_Deposition.pdf （书页100为实验，书页110为该篇参考文献和CC BY 4.0声明）。
- 访问等级：出版社/机构搜索索引可见实验片段，官方重印本可见结论片段；单篇PDF直接获取403，整书打开因约31.5 MB超过web大小限制失败；**未核全文**。CC BY声明已在官方重印本索引核实，但本文没有存档原文。
- 可直接核实的实验限定：Kaufman、300°C、0.8 nm/s、名义0/50/80 mA、700 nm膜厚；名义束电流不能转成局部基片通量。
- 官方重印本结论可支持：作者报告可见/中红外吸收随氧辅助降低，而Si上附着恶化；提出先沉积无辅助薄预层再辅助的办法。MgO/色心和界面键合解释须保留为作者解释，不升级成独立验证。实际束能、局部通量、电荷态、图表与统计仍待全文核查。

### M6 — ZnS：证据分层，避免“必然失硫”
- 直接IAD论文：Ruffner et al., 1989，DOI https://doi.org/10.1364/AO.28.005209；出版社 https://opg.optica.org/ao/abstract.cfm?uri=ao-28-24-5209；访问等级为元数据/摘要，未核全文。
- 摘要仅支持：−120至50°C、比较有/无IAD、考察组分/应力/光学损耗；不足以确认Ar/O2、源型或选择性移除方向。
- 氧化化学的旁证：Grimm et al., 2011，DOI https://doi.org/10.1016/j.tsf.2011.04.150；出版社 https://www.sciencedirect.com/science/article/abs/pii/S0040609011009916；摘要/实验片段支持由ZnS靶在Ar+O2反应RF磁控溅射中得到Zn(O,S)，组成随氧分压改变（200°C、60 W、9 μbar、至2.5%O2）。
- 边界：后者证明氧不是化学惰性稀释气，却不是Kaufman辅助蒸发的定量损伤证据；此次不足以写普遍的“Ar优先溅射S”或确定ZnO/硫酸盐产率。

### M7 — Ge / Ar：保留收益与缺口
- 原始论文：Broadband AR coatings on germanium substrates using ion-assisted deposition，1988；DOI https://doi.org/10.1364/AO.27.004255；出版社 https://opg.optica.org/ao/abstract.cfm?uri=ao-27-20-4255。
- 访问等级：元数据/摘要；未核全文。
- 精确支持：220°C制备的AR系统中，Ge层同步Ar轰击提高耐久性及10.6 μm、0.1 μs脉冲条件下的激光损伤阈值。
- 边界：不能据此排除Ar俘获、位移损伤、再溅射或应力风险；摘要不提供普遍可移植的能量窗口。Yehoda等 DOI 10.1116/1.575341 的15–110 eV/0–25%此次仅第三方摘要检索到，未获出版社/作者机构核实，保持待核，不作定量主证据。

### M8 — Ge / O：有氧化证据，缺同条件IAD验证
- 原始论文：Germanium implanted with high dose oxygen and its optical properties (1990)，DOI https://doi.org/10.1016/0168-583X(90)90755-J；出版社 https://www.sciencedirect.com/science/article/abs/pii/0168583X9090755J。
- 访问等级：原始论文元数据/摘要，未核全文。
- 精确支持：45 keV、高剂量氧注入Ge，IR/RBS显示GeO2形成。
- 边界：这是高能注入而非低能Kaufman-IAD，不可据其剂量、厚度或光学结果给薄膜工艺设阈值。对本项目应标“氧化风险需验证”，而非“已证实在任意O2辅助下必然严重吸收”。

## 4. 建议统一的量纲与术语（解析关系，不是新增实验数据）

- 电场加速的单粒子能量近似为 E = z e (V_plasma − V_surface)，需明确电位参考、初始能量、碰撞和电荷态；E[eV]≈V_beam[V]只是适用假设下的简化。
- 基片面离子电荷电流密度 j = e Σ(z_s Γ_s)。纯单电荷束才有 Γ_i = j/e；混合电荷态不能只用j/e获得离子个数。分子离子还须区别每离子、每分子和每原子的能量及到达率。
- 离/沉积原子到达比为 Γ_i/Γ_dep；注量是对时间积分；能量通量需按各物种的 Γ_s E_s 求和，并说明快中性成分是否计入。
- 薄膜“每沉积原子剂量”与束能不是同一量。沉积速率换算原子到达率还需密度、化学计量与净沉积/再溅射定义。
- 探针读数需注明收集面积、法向、位置、偏压/二次电子抑制、电子/慢离子排除方式及空载/实际转架条件；电流数字不完整时把基片通量记为未知。

## 5. 接受前检查清单

- [ ] 所有阈值/经验电压旁有源型、气体、能量定义、剂量、沉积率、温度、基片、几何、指标波段和访问等级；未给出的字段明确为未知。
- [ ] 不把End-Hall放电压写为Kaufman束能；不把总束流或放电流写为基片通量。
- [ ] 不把Ar+假设写成实测电荷态；O+、O2+、多电荷/碎片比例未测时不填数。
- [ ] 不把中和器等流读数当成空间电荷、表面电位、启动/关机瞬态均已验证。
- [ ] 高压/联锁条目要求本机规程；“水冷检查”注明适用组件，不统一套到所有源。
- [ ] 材料风险把“已观测”“作者推断”“跨方法旁证”“待验证”分开；不通过不同文献拼接成从未实测的统一配方。

未找到/未充分核实不意味着文献不存在或风险不存在；表示当前来源不能支持更强的结论。
