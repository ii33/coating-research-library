# T02 来源摘要：高精度镀膜机建模与仿真

本页只记录可核实的来源事实与证据边界。T02本地来源ID写作 `M01`–`M08`（引用时用 `T02:Mxx`）。逐项摘要都区分论文报告与本项目推断；本文不是用户设备模型，也不代表精度验证。

## M01 · Holland & Steckelmacher (1952)
**The distribution of thin films condensed on surfaces by the vacuum evaporation method**

- 作者：L. Holland、W. Steckelmacher；Vacuum 2(4), 1952, pp. 346–364
- DOI及来源：[10.1016/0042-207X(52)93784-6 · 出版社页面](https://doi.org/10.1016/0042-207X(52)93784-6)
- 阅读状态：只读出版社书目与摘要，未读全文/公式；无本地原文。全文访问受限。
- 许可：出版社摘要可读不等于全文开放；未核实存档或再分发授权。仅保留链接。
- 摘要明示：以Knudsen余弦定律作为基本律，计算范围包括点源、长条源、线源和环形源，以及平面/球面接收面；摘要提到ZnS、MgF₂、Al等实验和适用范围讨论。
- T02可用处：为有限面积源/线状源不能一概等同点源、需对发射区域积分或验证简化条件，提供历史文献入口。
- 边界：摘要没有公开推导细节。本记录不引用任何未读公式、不据摘要声称已完成扩展源数值积分。

## M02 · Musset & Stevenson (1988)
**Thickness Distribution of Evaporated Films**

- 作者：Anthony Musset、Ian Stevenson；Optical Interference Coatings 1988, Technical Digest Series, paper ThE3
- DOI及出版信息：[10.1364/OIC.1988.ThE3 · Optica页面](https://doi.org/10.1364/OIC.1988.ThE3)；[Denton Vacuum官方技术页](https://info.dentonvacuum.com/thickness-distribution-of-evaporated-films)
- 阅读状态：Optica只核书目与短摘要；读了Denton官方技术页公开的技术摘录，未读Optica全文。没有存档原文。
- 许可：全文未开放给本次读取；未核实复制/再分发许可。
- 摘录精确支持：先在单转平面架上、已知径向位置测量测试片厚度；用程序寻找最贴合测量值的源发射函数 `cos^Q φ`；再用已知函数选择源偏置与calotte曲率以改善直径方向均匀性。
- T02可用处：实测源函数校准的例子。测量空间位置、装夹几何与拟合参数应同批保存；校准参数须在新几何/工艺另验。
- 边界：只覆盖网页披露的摘录，未核对原论文算法、拟合残差或不确定度。该例不能证明 `Q` 在其他几何/测点设计下可辨识。

## M03 · Schmidt, Parlak & Brinkman (2008)
**Control of the thickness distribution of evaporated functional electroceramic NTC thermistor thin films**

- 作者：Rainer Schmidt、Mehmet Parlak、A. W. Brinkman；Journal of Materials Processing Technology 199, pp. 412–416
- DOI及来源：[10.1016/j.jmatprotec.2007.08.014 · METU AVESIS机构记录](https://avesis.metu.edu.tr/yayin/8210cab0-907c-4aab-a923-28ccff0ef0a9/control-of-the-thickness-distribution-of-evaporated-functional-electroceramic-ntc-thermistor-thin-films)
- 阅读状态：仅读作者机构库书目与摘要，未取得/存档全文。
- 许可：全文版权未核实；未存档。
- 摘要报告：0.8 nm/s低速电子束蒸发的NTC薄膜；在宏观膜面用Alpha Step触针轮廓仪测厚；用基于Hertz–Knudsen方程与改进余弦发射律的几何模型拟合；由该模型估计蒸汽对基底的黏附系数为80 ± 1.5%。
- T02可用处：支持把实测厚度地图与来源/凝结模型共同拟合，并显式记下材料、速率、几何和测量仪器。
- 边界：只读摘要，未核对“±1.5%”含义、仪器校准、拟合残差与参数相关性；这一材料/工况的值不能移植至用户机。

## M04 · Zhang & Cai (2013) · 完整开放全文
**Uniformity Masks Design Method Based on the Shadow Matrix for Coating Materials with Different Condensation Characteristics**

- 作者：Lichao Zhang、Xikun Cai；The Scientific World Journal 2013, article 160792
- DOI/原文：[10.1155/2013/160792 · PMC全文HTML](https://pmc.ncbi.nlm.nih.gov/articles/PMC3817662/)
- 阅读状态：PMC官方HTML全文已读，含Theory and Experiment、Results、Conclusion；已存单份官方HTML研究档案。
- 许可：文中明示Creative Commons Attribution License（要求正确署名）；正文网页未写明具体版本号。完整HTML抓取文件还含网站导航/标识，读者包只给原文链接；不能把正文许可直接覆盖整个网页。第三方图像的权利需单独检查。
- 精确支持：§2式(1)使用点源厚度核 `t_p = K cos^n(α) cos^m(β) / r_p²`，其中n、m分别描述源发射和材料凝结的角响应；式(2)–(5)建立分区shadow matrix并求掩模形状。§3的Fig. 2及相邻段落称用无掩模实测厚度分布拟合 n、m，文中获得MgF₂的n=2、m=1及LaF₃的n=2、m=0.5。注意式(2)本身是shadow matrix关系，不是n/m拟合公式；shadow matrix与掩模逆解由§2式(2)–(5)描述。
- 实验条件：SYRUSpro 1110 DUV；1100 mm腔体、四个基片架、行星半径300 mm；凸球面半径200 mm/直径280 mm；MgF₂、LaF₃单层，源到架垂距700 mm。摘要及§3报告两材料均匀度优于98%。
- T02可用处：点源角分布、材料相关凝结项、参数由基线测量拟合、遮挡离散化和模型/实测闭环验证的全文公式与示范。
- 物理解读警告（由式(1)推导）：文中m是经验凝结角响应指数，不能直接解释成概率型黏附系数。若把 `cos^m(β)` 分解为基础 `cos(β)` 投影项乘角度因子 `c(β)`，则 `c=cos^(m−1)(β)`；m<1时c在掠入射发散，说明这种分解不应被解释为物理概率。M03摘要里的特定模型黏附系数80 ± 1.5%来自另一项拟合，不能与M04的m混淆。
- 边界：上述n/m、98%及设备参数只属于该文几何/材料/测量。式(1)是文中简化点源模型，不直接证明用户机扩展源积分、散射、具体遮挡或时间依赖已验证。T01相同来源为S06；T02:M04是便于本专题引用的交叉登记。

## M05 · Oliver (2016) · T01全稿交叉引用
**Impact of deposition-rate fluctuations on thin-film thickness and uniformity**

- 作者：J. B. Oliver；Optics Letters 41(22), pp. 5182–5185
- DOI及出版页：[10.1364/OL.41.005182 · Optica](https://opg.optica.org/ol/abstract.cfm?uri=ol-41-22-5182)；[OSTI作者稿](https://www.osti.gov/servlets/purl/1342091)
- 阅读状态：已读T01登记的OSTI开放作者稿（T01:S12；本地 `01_machine_structures/sources/originals/S12_Oliver_2016_Rate_Fluctuations_Accepted.pdf`），Optica/PubMed出版元数据另核。T02不复制文件。
- 许可：OSTI可公开阅读作者稿；未核实再分发许可，读者包不含原文。
- 精确支持：作者稿式(1)给出随源点/工件点坐标与羽流余弦幂指数变化的微分厚度贡献；式(2)在行星运动逐步求和中乘以归一化、显式随时间变化的速率 `R_N(t)`。按行星公转转速w rpm、每圈U步，时间步为 `60/(wU)` s。作者说明运动相位与源速率波动应在同一时间基准上关联。
- 模拟工况/限制：1.37 m腔体、4个533 mm行星盘、双源；用完整轨迹周期遍历来隔离速率波动，比较齿比171/53、237/70和多组正弦/噪声速率。论文摘要所称最高约3%是该模型与条件结果，不能作为用户机误差上界。作者稿页首的DOI/日期有占位符，正式书目信息以出版社记录为准。
- T02可用处：指出平均速率和齿数不足以表述动态沉积；需要逐时速率/挡板/位姿同步积分，并将有限单层时长与完整周期假设分开。

## M06 · JCGM 100:2008 + Amendment 1:2026
**Evaluation of measurement data — Guide to the expression of uncertainty in measurement; Amendment 1: Nonlinearity in measurement models**

- 机构：Joint Committee for Guides in Metrology (JCGM)
- 官方入口及DOI：[BIPM Guides in Metrology](https://www.bipm.org/en/committees/jc/jcgm/publications)；GUM 100:2008 DOI `10.59161/JCGM100-2008E`；Amd.1:2026 DOI `10.59161/PPDI3267`
- 阅读状态：读BIPM提供的JCGM 100英文PDF相关条款及Amd.1:2026正式PDF相关条款；并未逐页研读基础指南全文。BIPM官方目录在2026-10-01列有2026修订。
- 许可：BIPM/JCGM免费提供访问但版权由成员组织共有；未获许可，未存档/再分发。
- 精确支持：GUM §4.1描述输入/输出测量模型，§5.1.2–5.1.3给出灵敏度/合成不确定度传播；Amd.1:2026修订§4.1.4与Annex H.1.7，说明非线性显著时应使用JCGM 101蒙特卡洛或计入符合条件的高阶Taylor项。
- T02可用处：把测厚、几何位置、倾角、转速、源速率及模型系数的不确定度传递至厚度/均匀度输出；参数协方差不可默认忽略。
- 边界：通用测量不确定度指南，不为镀膜模型提供输入分布、测量精度或参数先验。需由实测/校准证据决定。

## M07 · JCGM 101:2008
**Evaluation of measurement data — Supplement 1 to the GUM: Propagation of distributions using a Monte Carlo method**

- 机构：JCGM
- 官方入口/DOI：[BIPM Guides in Metrology](https://www.bipm.org/en/committees/jc/jcgm/publications)；[10.59161/JCGM101-2008](https://doi.org/10.59161/JCGM101-2008)
- 阅读状态：在BIPM官方英文PDF中读§5.9.6及§7.1–7.2相关章节；并未逐页研读其余全文；未存档。
- 许可：官方免费阅读不等于自由再分发；版权受JCGM成员组织保护，不存档。
- 精确支持：§5.9.6、§7.1给出将输入分布经模型传播的Monte Carlo流程；§7.2.1–7.2.3说明试验数要按输出分布形状、目标覆盖概率和数值容差选择，不能假设任意预定样本数必然足够，并给出自适应选择的指引。
- T02可用处：厚度几何模型呈非线性、遮挡不连续或输出分布偏离正态时，作为不确定度传播方案候选；记录随机种子、样本数、停止准则和覆盖区间。
- 边界：Monte Carlo只能传播输入不确定度，不能修复错误几何、系统偏差或不可辨识参数；计算结果本身仍需收敛检查。

## M08 · NASA-STD-7009B Change 1 (2024)
**Standard for Models and Simulations**

- 机构/正式状态：NASA Office of the Chief Engineer；官方登记页标为ACTIVE，文档日期2024-03-05
- 官方页/原文：[NASA标准登记页](https://standards.nasa.gov/standard/NASA/NASA-STD-7009)；[官方PDF](https://standards.nasa.gov/sites/default/files/standards/NASA/B/1/NASA-STD-7009B-Final-3-5-2024.pdf)
- 阅读状态：已读官方登记页和PDF上述相关章节§4.3.3.1、§4.3.5、§4.3.8、附录E.3.3–E.3.4；未逐页研读其余全文；未存档。
- 许可：NASA登记为Internet Public并可在线阅读；复制/再分发权未另行核实，不保存文件。
- 精确支持：附录E.3.3解释solution verification应识别数值误差并评估精度影响，包括迭代收敛容差及模型离散/分辨率误差；§4.3.3.1要求记录输入、输出及派生量的不确定度表征过程和理由；§4.3.5要求记录敏感性分析；§4.3.8要求报告最佳估计、不确定度、可信度评价和适用限制。
- T02可用处：作为验收记录检查表的参考，支持解析极限/单位守恒、时间步收敛、敏感性、实测对照、版本与失败边界都留档。
- 边界：这是一项跨领域NASA M&S标准，T02引用为自愿工程参考，不表示属于NASA项目或已获得NASA标准合规认证；项目仍需自行定容差。

## 主题交叉索引与证据缺口

- 源角分布/源型：M01为历史摘要入口（只读摘要）；M04给出已读完整点源角核；M02/M03为测厚图拟合源项的校准实例，但原文读取不完整。
- 行星运动及速率时间耦合：M05是全文动力积分/速率波动基线；适用工况有限。不能将其数值误差直接套至新机型。
- 校准/参数可辨识：M02和M04报告对角响应参数进行拟合；尚无来源证明对本项目未知设备配置的参数可辨识。正式校准应检查灵敏度/Jacobian秩、参数相关性、设计点覆盖与独立留出测点；这是本项目应做的验证事项，不是上述文献已替项目完成的结论。
- 数值/测量不确定度：M06、M07提供通用传播框架，M08提供V&V报告结构；均不提供用户设备的输入不确定度或容差。
- 扩展源积分：M01摘要提示点/条/线/环源属于不同计算几何，但不能代替本项目推导；当前证据组合没有已全文核读且覆盖用户具体蒸发源尺寸/羽流的验证论文。需把扩展源面积积分作为待验证模块，用点源极限、数值求积收敛及独立厚度地图测量验证。
