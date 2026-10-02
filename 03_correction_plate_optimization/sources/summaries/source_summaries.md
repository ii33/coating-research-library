# T03 来源摘要与使用范围

以下为项目原创摘要。检索/核读日期2026-10-02，研究对象是修正板算法的有界方法基线，不声称穷尽文献。全文、摘录、摘要、仅书目分别标记。来源报道的性能只属于其论文试验；本项目算例的数字全部另行计算。

## P01 Zhang and Cai 2013

- 原文：Lichao Zhang, Xikun Cai, Uniformity Masks Design Method Based on the Shadow Matrix for Coating Materials with Different Condensation Characteristics, The Scientific World Journal, 2013, Article 160792
- DOI：[10.1155/2013/160792](https://doi.org/10.1155/2013/160792)；[PMC全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC3817662/)
- 读取：PMC正文、式(1)–(5)、图题和实验段；HTML原档继承自T02，并在本轮在线复核正文
- 摘要：通过分区建立形状参数与遮挡损失间的矩阵关系，并在特定球面工件/材料组合上验证互补板思想
- 关键定位：第2节式(2)–(4)是影矩阵/双材料方程；第3节为无板数据拟合与实验结果
- 限制：角度单位、近似线性区域和可制造约束需另外检查；公开HTML式(5)按字面不是式(4)一般解，详见报告03的标量反例，不能据此否定特殊实验结果
- 本项目使用：方法入口、材料响应不能混用、原方程应回代；不照抄未经核验的逆矩阵表达式
- 权利：文章明示Creative Commons Attribution，页面未指明版本；保存单份HTML作为本地研究原档，保留作者/来源。整页含网站内容，原档不进入对外读者包

## P02 Sun et al 2014

- 原文：Jian Sun, Weili Zhang, Kui Yi, Jianda Shao, Optimization of thickness uniformity of coatings on spherical substrates using shadow masks in a planetary rotation system, Chinese Optics Letters 12(5), 053101
- [出版社摘要](https://opg.optica.org/col/abstract.cfm?uri=col-12-5-053101)
- 读取：出版社元数据和摘要；未据未读全文作公式断言
- 摘要：将基本沉积、自遮挡和板遮挡结合，研究固定板轮廓数值优化及凹凸球面的实验
- 使用：提醒曲面工件有自遮挡及参数化选择；本轮平面工件不能直接外推到球面
- 限制/权利：摘要中性能数值不等于本项目误差定义；未核实再分发权，未存档全文

## P03 Coatings 2021 11 140

- 原文：Optimization of Thickness Uniformity Distribution on a Large-Aperture Concave Reflective Mirror and Shadow Mask Design in a Planetary Rotation System, Coatings 11(2), 140 (2021)
- DOI：[10.3390/coatings11020140](https://doi.org/10.3390/coatings11020140)；[出版社](https://www.mdpi.com/2079-6412/11/2/140)
- 读取：检索引擎提供的出版社正文摘录，包括摘要、第4节及结论；直接全文请求返回429，故未标为完整阅读
- 摘要：几何、源位与行星运动共同影响膜厚，固定板设计同时涉及安装位置与形状
- 使用：板位与形状共同建模的文献背景；结论指出扩展源及准确遮挡计算仍需研究
- 限制/权利：未完整核对公式与许可页面，不保存原文，不用其实验值标定本算例

## P04 Boyd and Vandenberghe 2004

- 原文：Stephen Boyd, Lieven Vandenberghe, Convex Optimization, Cambridge University Press (2004)
- [作者官方教材页](https://web.stanford.edu/~boyd/cvxbook/)
- 读取：教材官方入口、版权说明；本轮PDF请求失败，因此不冒称本轮重读具体章节
- 摘要：作为凸优化、二次规划和对偶理论的后续教材入口。T03具体Hessian、KKT投影和块求解由本项目直接推导与测试
- 权利：作者页称出版社允许其在网页提供教材；这不自动授权本研究库重新分发，未保存或打包教材

## P05 Parikh and Boyd 2014

- 原文：Neal Parikh, Stephen Boyd, Proximal Algorithms, Foundations and Trends in Optimization, 1(3), 123–231，作者页面书目为2014
- [作者官方论文页](https://web.stanford.edu/~boyd/papers/prox_algs.html)；[作者PDF](https://web.stanford.edu/~boyd/papers/pdf/prox_algs.pdf)
- 读取：PDF第1.1、1.2和4.2节，尤其正文148–151页；作者PDF封面仍标2013/DOI占位符，登记保留版本差异
- 摘要：投影是约束指示函数的近端算子，光滑凸目标加闭凸约束可用近端/投影梯度迭代
- 使用：支持步长1/L和凸固定模型的收敛条件；不能将其扩展为二值板形非凸问题的保证
- 权利：作者官方公开阅读；未核实再分发许可，不存档PDF

## P06 JCGM 101 2008

- 原文：Evaluation of measurement data, Supplement 1 to the Guide to the expression of uncertainty in measurement, Propagation of distributions using a Monte Carlo method
- DOI：[10.59161/JCGM101-2008](https://doi.org/10.59161/JCGM101-2008)；[BIPM官方页](https://www.bipm.org/en/doi/10.59161/jcgm101-2008)
- 读取：官方出版页面与摘要；本轮不声称完整重读规范
- 摘要：针对测量模型中输入分布向输出分布的传播给出蒙特卡洛框架
- 使用：区分有依据的概率传播与本项目任意幅度情景测试；没有输入概率分布就不输出覆盖概率
- 权利：官方可读不等于可再分发；未在本专题存档原文

## P07 Long et al 2022

- 原文：Guoyun Long, Yaoping Zhang, Junqi Fan, Chunlin Guan, Optimization of coating uniformity in a simple rotation system by using a rotating shadow mask, Applied Optics 61(1), 188–195
- DOI：[10.1364/AO.441444](https://doi.org/10.1364/AO.441444)；[出版社页面](https://opg.optica.org/ao/abstract.cfm?uri=ao-61-1-188)
- 读取：出版社摘要、元数据、数据可用性说明；未复现全文模型
- 摘要：研究旋转板与固定板组合改善简单旋转工件的膜厚分布
- 使用：可动板属于后续扩展，不能把固定板限制误当作整个设计问题的物理极限
- 限制/权利：原始数据需向作者合理请求；本轮未获取，不宣称重复其实验，也不存档全文
