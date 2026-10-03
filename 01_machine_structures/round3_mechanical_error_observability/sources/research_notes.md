# 机械误差与可观测校准：主来源核验

核验日：2026-10-02。6项正文来源；以下均为原创短摘要，非标准替代品。固定太阳轮120齿、行星36/37齿但拓扑未知，来源不证明实际传动符号、转速比或设备性能。除明确获许可的NASA报告外，不保存原文、不上传。

1. **Lion Precision，Spindle Error Analyzer 9.0 Manual，M017-8900.002**
   URL：https://www.lionprecision.com/user-manual-spindle-error-analyzer-90/
   已读位置：网页 GLOSSARY（Axial/Radial/Tilt/Face error motion、Runout）；Tilt: Fixed Sensitive Direction；Donaldson Reversal。
   摘要/支持：径向、轴向、倾斜须按参考轴及测点位置定义；端面误差运动含指定半径的轴向与倾斜投影。表面跳动混含定心和形状，不能当轴误差。轴向分隔的两径向测点用于倾斜；Donaldson两次反转分离检具形状与同步径向误差。
   不支持：单探头直接辨出上述各项；把手册检具对心的一倍频处理规则直接用于删除载片真实轨迹的一倍频。

2. **Renishaw，The accuracy of rotary encoders（技术白皮书网页）**
   URL：https://www.renishaw.com/en/the-accuracy-of-rotary-encoders--47130
   已读位置：Effect of scale swash；Error compensation techniques → Multiple readheads / Error maps。
   摘要/支持：对径双读头可消偏心及重复误差奇次谐波；角度与极坐标定位对轴漂移的要求不同。映射须最终装配后以独立参考校准；倾斜、轴向相对运动和读头位置会耦合进角度读数。
   不支持：双头消尽所有误差；静态映射消除轴漂移、扭转等时变误差；引用厂商示例数作为本机精度。

3. **KHK，Gear Technical Reference，Gear Backlash**
   URL：https://khkgears.net/new/gear_knowledge/gear_technical_reference/gear_backlash.html
   已读位置：6.1、6.3、6.4、6.5。网页gzip经内存解压读取正文，无原文落盘。
   摘要/支持：角齿隙是固定另一轮时可自由转动的角区间；中心距、齿厚及齿轮串级影响齿隙，预紧/消隙有接触与润滑约束。
   不支持：齿隙等于单向传动误差；未知拓扑下直接套两级定轴累积公式或保证零齿隙设计可用。

4. **Houser、Bassett，NASA-CR-176163（1985）**
   题名：The design and analysis of single flank transmission error testor for loaded gears
   身份/许可：https://ntrs.nasa.gov/citations/19850026091
   原文：https://ntrs.nasa.gov/api/citations/19850026091/downloads/19850026091.pdf
   已读位置：§1.1印刷p1（PDF11）；§2.5印刷pp21–22（PDF31–32）。
   摘要/支持：TE是随转角变化的齿轮副量，含几何与有限刚度/载荷效应；均值滞后与交变量须区分。转向、中心距、转速、接触齿对会改变TE；未满足分离条件，齿对曲线不能定位到某一轮。
   不支持：无载TE代表工况TE；仅凭120/36或120/37便识别误差来源。
   本地许可归档：originals/NASA-CR-176163_1985_loaded_transmission_error.pdf；39,424,061字节；SHA256 ff022b201cba6ff54b2d5ec1cc1cd0e76bd657c8babba9bd2327e1cc0e9512af。依据：NTRS条目Distribution Limits为Public，Copyright为“Work of the US Gov. Public Use Permitted.”；未上传。

5. **NIST TN1297，Appendix A**
   URL：https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-appendix-law-propagation-uncertainty
   已读位置：A.1–A.3，式(A-1)–(A-3)。
   摘要/支持：测量模型须涵盖重要修正和变异源；一阶不确定度传播含灵敏度及协方差，相关输入不能默认独立平方和。
   不支持：将公差上限当标准差；不经检验用于强非线性、大扰动或多峰模型。

6. **Cintrón-Arias等，A Sensitivity Matrix Based Methodology for Inverse Problem Formulation，arXiv:2004.06831v1**
   URL：https://arxiv.org/html/2004.06831
   已读位置：§3.3式(44)–(49)；§4；§6。
   摘要/支持：灵敏度矩阵小奇异值放大观测噪声；满秩仍可能病态，近共线参数响应可相互补偿。参数子集选择须同时看秩、条件及估计不确定度。
   不支持：以满秩宣称全局唯一辨识；跨量纲直接比较未经尺度处理的条件数；将该文其他领域的示例阈值移作本机验收值。
