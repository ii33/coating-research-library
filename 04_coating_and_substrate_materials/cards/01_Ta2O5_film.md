# 01 Ta2O5 镀膜材料

T04第一轮，2026-10-02。独立卡片由[证据分册](../reports/oxide_material_cards.md)提取；修改分册后运行 `python models/build_material_package.py` 同步。此卡是公开资料与工程推导，不是本机实测或量产配方。

### 1.1 身份与功能

目标膜为钽氧化物高折射率层；原料常以Ta2O5标称。CAS 1314-61-0可用于核对所引Patinal粒料 [OX-20]。化学计量Ta2O5对应O/Ta=2.5，这是化学式定义，实际膜应以XPS、RBS/EBS或其他适用方法确认；表面XPS氧/钽比不能不加说明地替代体平均。结晶块材、非晶电子束膜、IAD膜、IBS膜必须分开记录。

它可进入可见/近红外高折射率候选集，但是否适用于指定激光器或中红外滤光片，须由目标波段k、散射、膜应力、环境稳定性共同决定。本册不授予一个设备无关的“Ta2O5损伤阈值”。

### 1.2 参数表与禁混项

| 对象/性质 | 数值与单位 | 条件、方法 | 来源与不确定度 |
|---|---|---|---|
| 源料理论密度 | 8.2 g/cm³ | 厂商Ta2O5条目；晶型/测温未完整给出 | M OX-01；无误差，不能当ρ_film |
| 源料熔点 | 1872 °C | 厂商标称 | M OX-01；无误差，不等于有效蒸发温度 |
| 薄膜n | EH 2.15；PS 2.13；CC 2.01 | λ=550 nm，非加热玻璃，电子束+三类离子/等离子源 | P OX-05 Table 2；未给n误差 |
| IBS薄膜n及密度 | GC：2.03±0.02、7.34±0.07 g/cm³；Spector：2.08±0.02、7.5±0.1 g/cm³；DIBS：2.014±0.005、6.9±0.2 g/cm³ | n在1064 nm；同论文Table 1配对数值，非蒸发膜；逐行退火状态未单独明示 | P OX-07；保留原±，置信水平未在表中标明 |
| 可见/近红外k、膜孔隙率 | U | 尚无一套同时满足本机材料、厚度和工况的核定数据 | 禁止填0；与密度不足不能直接换算开口孔隙 |
| CTE、弹性模量、导热率、附着临界载荷 | U | 薄膜/基片组合，测试方向、温度与方法待定 | 不从块材数据库补齐 |

**名义纯样品隔离记录。** Durante 2024把零名义Ti一行标成Ta2O5，但Table 1的EDS Ti/(Ta+Ti)=7.1±0.6%；该行在1064 nm的n从2.062变为2.046，1550 nm退火后2.033 [OX-06]。这些值只能描述这组名义Ta2O5 IBS样品。Si上光学样品使用空气退火、500°C相关状态；方法段列12 h平台，而SiO2样品列10 h，两种记录不能合并成单一退火配方。此证据可证明“成分和退火标签要核”，不能为纯Ta2O5提供无歧义默认常数。

### 1.3 蒸发路线和迁移边界

OX-01给出的厂商经验为：电子束优于阻蒸；FABMATE或Ta衬埚可作为候选；参考源温约2000°C、速率0.2–0.5 nm/s、氧分压10⁻⁴ Torr（约0.0133 Pa），并倾向IAD。阻蒸只在设备允许时考虑Ta舟。其400°C空气4 h处理为特定经验，不可写成所有膜的消吸收保证。该来源没有给出完整温度校准、膜组成、热应力或机型外推误差。

工程上必须把三个位置分开：源热点温度决定蒸发/放氧，工件表面温度决定热预算与结构，真空计位置影响氧分压读数。只照抄速率、炉温或氧流量，会遗漏单位面积到达通量及氧化机会。若比较IAD与非IAD，应保持膜厚和入射几何可比，另记录基片上的离子通量/能谱；仅记录离子源电源电流不足以复现。

### 1.4 失效机制与排查顺序

| 现象 | 候选机制而非直接诊断 | 最小区分证据 | 可控下一步 |
|---|---|---|---|
| 光谱有吸收尾或激光发热 | 氧亏、污染、缺陷，亦可能粗糙散射被拟合成k | R/T+积分球或量热；XPS/RBS；空白基片对照 | 在批准的工艺试验内区分氧化状态和污染，先验证而非盲目加氧 |
| 升温后n变动 | 致密化、结构松弛、组分或厚度变化 | 退火前后同片椭偏+独立膜厚+XRD | 重新建退火状态光学库 |
| 开裂、起皮、面形变化 | 总膜应力与基片/膜热膨胀约束；颗粒和界面污染 | 曲率/面形、截面和缺陷位置、冷热循环 | 先定位界面、厚度和热预算，不用“加厚粘接层”作通用补救 |
| 蒸发速率跳动/喷点 | 源料放气、局部钻孔、熔池几何变化 | 压力/功率/速率同步日志、见证片颗粒计数 | 恢复经设备认可的源预处理和相同初始料位 |

这些是因果候选和试验设计I，不是已证明的现场事故归因。OX-07提示退火必须兼顾结晶导致的光损失；它的样品结晶状态不能定义所有Ta2O5膜的温度上限。

### 1.5 选材算例

设550 nm正入射、忽略色散的一阶四分之一波层。若选OX-05的PS膜n=2.13，几何厚度为64.55 nm；换成CC膜n=2.01则应为68.41 nm。若沿用64.55 nm而真实n为2.01，单层的四分之一波相位中心约变成519.0 nm。**这是工艺迁移敏感性算例，不是整膜系通带预测。** 因此选Ta2O5后仍须选定工艺状态；厚度均匀并不消除n不均匀。

### 1.6 SDS和冻结缺口

所引108500粒料SDS（2022-12-09，SG，v1.2）在其引用CLP下未列为危险物质/混合物，同时有P260防尘要求 [OX-20]。本轮该文可核官方索引片段、完整打开失败，现场应取同批/同地区完整现行SDS。未解决：本机蒸发k(λ)、应力随厚度和湿度的变化、真正同批膜ρ与O/Ta、MWIR吸收和激光条件下LIDT。上述未知不阻止资料首轮冻结，但阻止量产放行。

## 本卡证据入口

- [OX-01 Kurt J. Lesker — Tantalum Pentoxide Evaporation Process Notes](https://www.lesker.com/newweb/deposition_materials/deposition-materials-notes.cfm?pgid=ta4)
- [OX-05 Niederwald et al. — Ion-assisted deposition of oxide materials at room temperature by use of different ion sources (1999)](https://opg.optica.org/ao/abstract.cfm?uri=ao-38-16-3610)
- [OX-06 Durante et al. — Role of substrate and TiO2 content in TiO2:Ta2O5 coatings for gravitational wave detectors (2024)](https://inspirehep.net/files/3c4e23b65057a6e6b3a6ea500307f62e)
- [OX-07 Amato et al. — High-Reflection Coatings for Gravitational-Wave Detectors: State of The Art and Future Developments (2018)](https://s3.cern.ch/inspire-prod-files-d/daf5e3587dbe1123c14e37ca01873897)
- [OX-20 SUSONITY — Ta2O5 Patinal 108500 SDS SG, revision 2022-12-09](https://www.merckmillipore.com/Web-INTL-Site/en_US/-/USD/ShowDocument-File?Country=SG&DocumentId=108500_SDS_SG_EN.PDF&DocumentType=MSD&DocumentUID=362286534&Language=EN&Origin=SERP&ProductSKU=MDA_CHEM-108500)
