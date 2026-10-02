# 氧化物镀膜材料工程数据卡

版本：首轮证据冻结 v1.0，2026-10-02。范围按原清单顺序为 Ta2O5、TiO2、SiO2、Al2O3、H4；其余材料由本专题其他分册承接。依据 `00_project/工程科研.txt` 第7行与本专题 README。此册是可追溯的选材、工艺迁移与故障诊断资料，不是量产工艺规程。**资料核对已完成本轮有限覆盖；本机仿真验收、实测验证、供应商批次确认均未完成。**

## 0 使用本册前应知道什么

五种材料的主要差别不是一列折射率高低，而是可获得的低吸收波段、允许的工件温度、成膜结构、应力与环境漂移之间的约束。源料密度、薄膜密度、QCM输入密度、颗粒堆装密度是四种不同量。数据库里出现同一化学式，不代表相态、氧含量、孔隙和热历史相同。

### 0.1 证据口径

- **P 原始实验**：原论文/作者机构公开原文、出版者正文或表格；受其设备、样品、拟合模型限制
- **M 厂商技术**：直接供应商资料；适合确认货号、源具候选、经验窗口，不是独立验证或无条件保证
- **S 官方SDS**：只对列出的产品、形态、地区和版本成立；“未分类为危险品”不代表没有粉尘、热源、高压或清腔风险
- **I 本册工程推导**：明确假设的计算、诊断逻辑、试验建议，不冒充生产实测
- **U 未知**：当前证据不足；未知不是零，也不是“与块材相同”

正文中的 OX 编号对应 [来源登记表](../data/oxide_sources.json) 及逐来源摘要。末尾给出直达原文链接。对于只取得摘要或检索索引的材料已降低使用范围，不把未读全文当作已核表。

### 0.2 单位与数据移植

n、k无量纲；λ须同时注明 nm 或 µm；本册采用复折射率 n+ik，光强衰减系数 α=4πk/λ，α的长度单位与λ一致。1 Å/s=0.1 nm/s；1 Torr≈133.322 Pa；1 mbar=100 Pa。气体流量 sccm 不能在未知抽速、导流和位置时换成某个氧分压。电源“350 V/350 mA”也不是基片上全部离子的能量与电流密度。

n(λ)应与k(λ)、膜厚、粗糙度/梯度模型一起保存。若拟合把k强制为零，只能写“透明模型假设”，不能写“已证明零吸收”。若仪器只给T/R，低T可能同时来自反射、吸收和散射。QCM中的z-ratio=1也可能只是未知值的占位，SiO2官方说明即如此 [OX-03]。

### 0.3 首轮可用性速览

| 材料 | 可作为工程起点的证据 | 首要约束 | 本轮不准直接填入设计库的量 |
|---|---|---|---|
| Ta2O5 | 550 nm IAD实测n、IBS密度示例、电子束经验窗口 | 氧亏、退火与应力；名义纯度与实测组成 | 未核组成样品的“纯Ta2O5”NIR n；未测MWIR k |
| TiO2 | 原料/温度对n的成组实验、n/k同时测量 | 高n不自动低k；相变与散射 | 单晶金红石n直接替代非晶膜；通用结晶温度 |
| SiO2 | 块材色散、IAD/IBS薄膜对照、吸水研究 | 水/OH、密度、真空空气漂移 | 石英晶体密度与FAQ n直接替代膜层数据 |
| Al2O3 | UV辅助蒸发n/k、电子束容器、IR实验入口 | 折射率反差较小；结构与密度不能仅由n判断 | 蓝宝石轴向n、硬度直接当非晶膜参数 |
| H4 | 明确厂商/货号的组成类别、条件n/k表 | 商标配方、源料与膜不等价、IAD应力窗口 | 通用H4化学式；5.9 g/cm³当实测膜密度 |

## 1 Ta2O5 五氧化二钽

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

## 2 TiO2 二氧化钛

### 2.1 必须先区分的身份

金红石、锐钛矿、板钛矿以及非晶TiO2不是同一光学模型。金红石单晶具有较大双折射和色散，紫端还存在吸收 [OX-28]；无取向非晶膜不能直接调用单晶普通光/非常光n。蒸发TiO2成膜可用Ti、TiO、Ti2O3、Ti3O5等不同源料，但“形成TiO2膜”不证明原始蒸气或最终O/Ti比相同 [OX-08]。

理论化学计量O/Ti=2；源料灰黑颜色与还原程度相关，不能仅以颜色判断源料失效。OX-02指出白料加热也会放氧、变黑。与SiO2或Al2O3的“变黑应警惕”经验不能机械互换。

### 2.2 薄膜数据和相态条件

| 对象/性质 | 数值与单位 | 条件、方法 | 来源/不确定度 |
|---|---|---|---|
| 商品源料密度、熔点 | 4.23 g/cm³；1830°C | 厂商TiO2条目，源料级 | M OX-02；无误差、晶型标注不足 |
| TiO2起始料→膜n | 2.06–2.08；2.41–2.42 | λ550 nm；基片25°C与250°C；沉积1周后透射法 | P OX-08 Table 2；范围不是±测量误差 |
| Ti3O5起始料→膜n | 2.08–2.12；2.38–2.43 | 同研究、同两种基片温度 | P OX-08；说明源料不能省略 |
| 电子束IAD膜n | EH 2.45；PS 2.36；CC 2.32 | λ550 nm，非加热玻璃 | P OX-05；误差未给 |
| EBE / IBAD S0A、S3A、S4A膜n | 1.99；2.06；2.14 | λ550 nm；Ti3O5源、基片<50°C；不同离子枪设定 | P OX-09 Table 4；拟合未给逐值误差 |
| 同三膜k | 2.12×10⁻³；2.71×10⁻³；4.64×10⁻³ | λ550 nm；Scout反演；Sellmeier与OJL模型 | P OX-09；不能解释成所有TiO2的吸收下限 |
| 同三膜相对填充度PD / 光学推算P | 0.79/40.8%；0.83/34.8%；0.87/28.6% | 分别按原文两种有效介质近似推算 | P OX-09；非XRR密度，P≠1−PD |
| 本机膜ρ、O/Ti、CTE、模量 | U | 须明确相态、膜厚、温度与辅助能量 | 不能从n独立唯一解出 |

2025研究选录条件：Mo坩埚，工作压约(1.2–1.7)×10⁻³ mbar，O2 100 sccm，离子枪3/4 A与80/90 V；这些是该实验设备设定，不是推荐配方。样品厚度随工艺约350/300/200 nm，故比较性质时还有厚度这个混杂量。800°C、空气2 h后均出现锐钛矿；这些实测结果反驳“高温处理必然改善所有光学与机械指标”的过度概括 [OX-09]。

### 2.3 蒸发与离子辅助

OX-02列W或Mo舟阻蒸以及FABMATE/Ta电子束衬埚；参考氧分压(1–2)×10⁻⁴ Torr（约0.0133–0.0267 Pa），其阻蒸经验速率0.3–0.5 nm/s。源料预熔放气关系到稳定性，但本册不从一个厂家网页推出允许的枪功率、炉温斜率或所有舟寿命。

TiO2是“n升高但综合指标可能变差”的典型。密实化、相结构、氧亏都可能改变n；晶粒长大会提高散射，离子辅助又可能改变应力和缺陷。必须同测n、k和散射，不能只最大化n。300°C反应电子束实验也显示，透明氧分压阈值和n/k取决于玻璃基片，并与基片组分及膜相态相关 [OX-29]；无论选玻璃还是晶体，应把真实基片与见证片同时放入验证矩阵，不能只用一块易测Si片代表全部产品。

### 2.4 故障诊断与适用边界

- **透明度下降而n升高**：先区分k增加与散射；对比积分球、椭偏残差和AFM，必要时看XRD。用k=0的模型强行解释会把吸收“搬到”膜厚和n上
- **源料放氧、压力冲高**：同时看源功率与气体供给；不能把源料放出的氧当作稳定可控的反应氧源
- **退火后乳白或雾度上升**：检查晶粒长大/晶相与表面，不因透射下降就直接判为化学吸收。OX-09的形貌和光谱提供一个有条件的失败实例
- **高反射膜开裂或脱层**：单层n达标不能代替多层应力验收；热基片沉积与后退火的热历史也不同
- **紫外选择**：接近材料吸收边时，必须实测短波k及缺陷吸收。不能从550 nm低k外推到355/266 nm
- **中红外选择**：OX-15提供室温反应溅射样品的IR测量入口，不能把其中SiO2/TiO2/Al2O3三套曲线统称为蒸发膜通用常数

### 2.5 选材算例

考虑550 nm四分之一波层，仅用OX-09同研究中n/k作损耗敏感性比较。S0A需要69.10 nm，S4A需要64.25 nm。若暂忽略界面反射和驻波，按单程体传播损失1−exp(−4πkd/λ)，两者约0.334%和0.679%。这不是实测膜系吸收，也不是激光损伤阈值；它说明即使较高n能让层变薄，较大的k仍可能使损耗增加。用于高功率滤光器时，先按允许吸收筛选工艺，再比较折射率反差。

### 2.6 SDS和冻结缺口

111771黑色片料SDS（MY，2024-10-29，v1.5）未列CLP危险分类，却明确要求避免粉尘吸入，并指出惰性粉尘也可影响呼吸功能 [OX-21]。这不适用于未经核对的纳米粉或清腔混合尘。缺口：目标波段k的独立量热验证、实际相态和体组成、同厚度条件下辅助效应、热/湿应力与可重复源耗变化。

## 3 SiO2 二氧化硅

### 3.1 三种相同化学式的不同对象

晶体石英、熔融石英/合成熔融硅石、沉积SiOx或SiO2薄膜必须拆开。块材低热膨胀、透明，并不证明沉积膜无孔、无OH。SDS中玻璃态硅石CAS60676-86-0也不应与晶体石英粉尘CAS等混用 [OX-22]。原料若为SiO反应蒸发，应单独记source_material=SiO，film_target=SiO2；不能回写成“SiO2直接蒸发”。

### 3.2 块材与膜数据

| 对象/性质 | 数值与单位 | 条件、方法 | 来源/限制 |
|---|---|---|---|
| AGC AQ块材ρ、E | 2.20 g/cm³；74 GPa | 合成熔融石英商品典型值 | M OX-25；温度/误差除特别注明者未给 |
| AQ块材CTE | 0.6×10⁻⁶ K⁻¹ | 50–200°C | M OX-25；不可当薄膜CTE |
| 熔融石英块材n | 1.459911@550 nm；1.457018@632.8 nm；1.449631@1064 nm；1.444024@1550 nm | 20°C，由Malitson式计算，原始实测0.21–3.71µm | P+I OX-11；计算小数位不是样品精度 |
| 电子束IAD薄膜n | 1.49（EH/PS）；1.47（CC） | 550 nm，非加热玻璃 | P OX-05；未报误差 |
| IBS SiO2配对n/ρ | Spector：1.474±0.005、2.34±0.01 g/cm³；Spector按GC条件：1.468±0.005、2.33±0.05 g/cm³ | n为1064 nm；非蒸发膜 | P OX-07 Table 1；逐行热历史未完全标注 |
| 电离气氛反应蒸发吸收 | α<40 cm⁻¹@190 nm | Heitmann研究；非晶膜 | P OX-10；上界不是零；适用该工艺 |
| 蒸发薄膜k(λ)、OH含量、开口孔隙率 | U | 必须实际测量 | 不能从块材n或“透明”反推 |
| 源料密度冲突 | 约2.65（OX-03）与2.32 g/cm³@20°C（OX-22 SDS） | 与AQ块材2.20又不同 | 未平均；材料形态、来源用途和数据质量不同 |

Malitson三项Sellmeier参数为B=(0.6961663,0.4079426,0.8974794)，C=(0.0684043²,0.1162414²,9.896161²) µm²，n²=1+ΣBᵢλ²/(λ²−Cᵢ)，λ用µm。来源报告的10.5×10⁻⁶拟合残差不是任意沉积膜的误差保证；本册不把拟合式外推至8–12µm，不据此指定k=0 [OX-11]。

**网页冲突。** Lesker FAQ写n=1.54–1.55 [OX-26]，当前主工艺页写1.44–1.55 [OX-03]，均缺波长及膜相态。不能挑较好看的一个作为默认薄膜n，也不能用平均值“解决”冲突。

### 3.3 电子束和阻蒸的实际边界

厂商主工艺页建议电子束，容器候选FABMATE、石墨、Ta或适配的铜坩埚/铜炉床；其参考源温约1200°C、速率0.2 nm/s、氧分压10⁻⁵ Torr（0.00133 Pa）、基片350°C。阻蒸困难，W舟或Ta挡板盒属于需另验的路线；网页对挡板盒给1500–1800°C并提示反应损坏风险，不能与“材料约1200°C”的段落当成同一个温度点 [OX-03]。

若工件只允许低温，350°C建议本身即不满足边界，不是调整一个监控系数就能照搬。应先建立低温IAD或其他已经许可路线的材料库。热源、反应氧、薄膜致密化是不同控制量；供氧充足也不自动消除孔隙。

### 3.4 水和OH为何是近红外到中红外的关键

Zeng等在电子束HfO2/SiO2高反膜上观察水吸附造成光学/应力不稳定，用致密PIAD SiO2封帽延缓吸水过程 [OX-27]。这给出“表面阻隔可改变时间尺度”的证据，不能证明封帽能永久消除全部入水，也不能把该多层数据直接变成单层孔隙率。

工程含义：空气中测得的n与刚出真空的n可能属于不同含水状态；窄带滤光片若未规定存放时间和湿度，即使重复测量也可能失去可比性。为3µm附近或更长波应用，应直接测FTIR；把可见n曲线延长不会自动产生OH或声子吸收。OX-15反应溅射IR研究覆盖1.54–14.29µm，但其制法不同，暂只作测试与建模参考。

建议把干燥态、实验室平衡态及再入真空后的光谱/应力作为同一试样的三个状态记录；各状态记录温湿度、等待时间和测量方式。此为验证方案I，不设未经证据支持的合格漂移阈值。

### 3.5 选材算例

1064 nm四分之一波层用块材n=1.449631得到183.49 nm；若真实膜接近OX-07的IBS示例n=1.474，应为180.46 nm，相差约3.03 nm。光学厚度误差来自材料库而非镀厚监控。

另设QCM按ρ_set=2.65 g/cm³报100 nm，而实际ρ_film仅为假设值2.20 g/cm³，在相同面密度且暂不考虑工具因子及声学修正时，真实厚度约120.45 nm。这里2.20是**教学假设**，不是声称实际膜必然等于AQ块材。这说明不能同时用错误密度和工具因子互相补偿后又跨材料迁移。

### 3.6 SDS和冻结缺口

115337的SG SDS已打开到2026-07-10 v1.3：玻璃态硅石、未列CLP危险分类，仍要求避免粉尘、干燥密闭并使用适当防护 [OX-22]。该SDS密度2.32 g/cm³是来源冲突记录，不用于裁决高精度膜厚。未知：本机低温SiO2孔隙和水含量、FTIR损耗、应力随湿度的符号/幅度、氧化程度与源料耗损寿命。

## 4 Al2O3 氧化铝

### 4.1 为什么它既不是“蓝宝石薄片”也不能只按中等n看待

Al2O3源料可为晶体/陶瓷；电子束得到的薄膜结构和密度不必等于α-Al2O3蓝宝石。单晶色散与光轴数据需要专用模型 [OX-12]，不可直接嫁接到无定形保护膜。对于氧化物组合，它常作为较低/中等折射率层、保护或界面候选；作用必须由目标波段、相邻材料和环境验证，不能把用途列表当作完成了耐久试验。

化学计量O/Al=1.5；实际膜含杂质、羟基与局部配位仍须检查。折射率较低也不自动证明膜多孔：这一点有原始辅助蒸发实验反例。

### 4.2 参数表

| 对象/性质 | 数值与单位 | 条件、方法 | 来源/限制 |
|---|---|---|---|
| 源料ρ、熔点 | 3.97 g/cm³；2072°C | 厂商Al2O3条目 | M OX-04；非实测膜物性 |
| 源料蒸气压参考点 | 10⁻⁴ Torr@1550°C | 厂商表值 | M OX-04；不等于某机达到规定nm/s所需源温 |
| 电子束薄膜n | 非辅助约1.61；辅助最高约1.70 | λ350 nm；腔温100°C；Ar和/或O2离子轰击 | P OX-13；无逐值误差，腔温不等于精确工件温度 |
| 同实验k | 约2×10⁻⁴ | λ350 nm；辅助前后基本不变 | P OX-13；不是k=0 |
| 同实验水吸附/真空空气漂移 | 未见明显3µm水带，低n非辅助膜也未见空气-真空漂移 | 原摘要的实验结果 | P OX-13；不是ρ绝对值或全体工艺的零孔隙证明 |
| 蒸发膜IR复介电函数 | 存在5–50µm实测研究 | T/R反演，KK一致性校验 | P OX-14；本轮未数字化，数值U |
| 膜ρ、热导率、CTE、杨氏模量、硬度 | U | 需非晶/晶相、厚度和方法 | 不借蓝宝石值填膜卡 |

**密度与n的反推限制。** n同时依赖电子极化、局部配位、组分和空隙。若先把蓝宝石n当无孔骨架，再用有效介质式反演非晶膜孔隙，结果可能将结构差异错算为孔隙。OX-13因此更适合提供一个反例，而不是给出所有Al2O3膜“密度一定接近1”的证明。

### 4.3 蒸发源选择和反应气体

OX-04认为高温使阻蒸很困难，W舟即便可用也存在反应与寿命问题；电子束候选为FABMATE、W衬埚或适配铜炉床。其经验源温约2100°C、速率0.2–0.5 nm/s、O2分压10⁻⁵ Torr（约0.00133 Pa）。源料发黑被列为更换信号。以上无完整设备热负荷资料，不给可直接执行的舟电流/电子枪功率。

1550°C蒸气压表与2100°C实际蒸发经验并非必然矛盾：平衡蒸气压参考、热源测温、熔池面积和目标沉积速率的定义不同。没有源到基片几何及测温方法时，不能用蒸气压单点反推通用源功率。

离子辅助应以目标指标定义：若n变高但k不下降，辅助并不保证吸收收益；若主目标是粘附或耐擦，需相应机械试验。界面层更薄也必须量化是否连续，厚度达到“名义若干nm”不等于无针孔屏障。

### 4.4 失效与测试

- **保护层透过下降**：测k和表面散射，检查是否有源颗粒/污染；不能借“Al2O3硬”排除膜裂纹
- **层间附着差**：分别检查基片清洁、界面反应与总应力；裸基片单层胶带测试不能证明复杂膜系寿命
- **中红外出现吸收**：应取实际膜FTIR n/k，不能以蓝宝石透过窗口代替薄膜窗口；参考OX-14/15的制法和测量覆盖
- **低n但耐湿好**：先检查局部结构与测量模型，不把低n作为唯一疏松指标
- **要求低损耗激光应用**：T/R的检出限常不是最终吸收预算，验收需要与实际波长、脉宽、重复频率、光斑和污染状态匹配

### 4.5 选材算例

350 nm四分之一波层：n=1.61时d=54.35 nm，n=1.70时d=51.47 nm。二者可见几何厚度以较薄层为基准相差约5.6%，即便都叫Al2O3也不可共用监控目标。用后者k≈2×10⁻⁴的实验值作无界面单程计算，损失约0.0370%（370 ppm）；这只是筛选量级，实际驻波膜系须另算、吸收须另测。若项目的吸收预算更严，应判为“待独立验证”，而不是因材料名符合UV用途即放行。

### 4.6 SDS与缺口

100840粒料IN SDS（2025-08-06，v1.5）列CAS1344-28-1，在所引CLP下未分类为危险物质；仍依其粉尘、眼部和操作防护条款处理 [OX-23]。这不覆盖含其它金属的腔体残渣。冻结缺口：实际批次可见/NIR/MWIR n/k全谱、非晶骨架密度、针孔/阻隔性能、热湿应力、与目标基片附着及激光验证。

## 5 H4 常见高折射率商品蒸发材料

### 5.1 名称问题已关闭，配方问题不能虚构关闭

本专题按用户确认，将H4作为常见高折射率镀膜材料研究。**H4不是IUPAC化学式，也不是所有供应商共同遵守的固定配方。** 本轮证据最完整的是Patinal商品族；若库存只标“H4”且无厂家/货号，以下数值只能作候选参照。

SUSONITY现行108332页面将组成写为La_xTi_yO_z [OX-16]；原厂2021技术PDF第1页描述钛氧化物/镧氧化物混合形成稳定LaTiO3相 [OX-17]。正确记录方式是“该厂家该产品族的源材料描述”；不能据此断言氧化气氛沉积的膜精确为LaTiO3，更不能把每个H4都赋予La:Ti=1:1。1992原厂会议摘要确认H4是混合高折射率蒸发材料 [OX-19]，不构成跨年代相同配方的保证。

### 5.2 牌号与物性分层

| 记录层 | 已核证据 | 不可推断 |
|---|---|---|
| 108332 H4粒料 | 1–4 mm；≥99.95%标称；La_xTi_yO_z | 纯度不等于主组分摩尔比或膜O含量 |
| 115591 H4 | 官方SDS为约0.1–2 mm；CAS66402-68-4 | 不能给其他厂家H4沿用该CAS |
| H4 HD | 厂商说明表观装料密度比普通H4明显提高 | HD不是“膜密度必然翻倍” |
| QCR密度设定 | 2021表给5.9 g/cm³、z=1 | 不是独立测量薄膜ρ；z=1未附校准不确定度 |
| 本机膜组成、ρ、孔隙率、热导率、CTE、弹性模量 | U | 不由商品缩写补齐 |

身份表分别依据OX-16、OX-17、OX-24。货号、供货粒级、COA与SDS应成为采购/来料核验键；不需要供应商回复才可研究，但缺牌号会阻止把候选数据用于最终放行。

### 5.3 有条件的n和k

选录2021资料（文件名含2022，内页发行12/2021）p2的少量数值，未重制整张厂商表 [OX-17]：

| 薄膜状态 | n@500 nm | k@500 nm | n@1000 nm | k@1000 nm | 不确定度 |
|---|---:|---:|---:|---:|---|
| 室温，常规蒸发 | 1.99 | 7.5×10⁻⁵ | 1.94 | 1.9×10⁻⁵ | 未给；厂商典型值 |
| 300°C，常规蒸发 | 2.05 | 2.4×10⁻⁴ | 2.00 | 5.1×10⁻⁵ | 同上 |
| 室温，IAD | 2.11 | 7.6×10⁻⁵ | 2.05 | 1.7×10⁻⁵ | 同上 |

独立1999研究的H4在非加热玻璃、550 nm，三类辅助源n=2.04/2.07/1.98 [OX-05]。不同波长、年代、辅助源与牌号状态不同，不能与500 nm表直接判“互相矛盾”。但2009旧H4 HD资料索引给500 nm无加热1.96、300°C约2.1，确实与2021表的条件标签和值不同 [OX-18]；旧文当前地区不可用，故保留版本差异而不强行统一Cauchy曲线。

透过窗口的“约至7µm”是厂家可用范围描述，不能当任意厚度和任意损耗预算下k=0。表中500 nm热沉积k反而较高，也说明“提高温度必然降低吸收”的简化不适用所有牌号/设备。

### 5.4 蒸发源和IAD边界

2021资料列源温2200–2300°C、速率0.2–0.8 nm/s、O2分压(0.8–2.0)×10⁻⁴ mbar（0.008–0.020 Pa）、基片30–300°C。正文优先Mo衬埚而非直接水冷铜炉床，另有Mo舟阻蒸路线。IAD示例为O2射频源350–700 mA、350–700 V；这些只是该源设定，不能变成通用入射离子能量，也不可据此指令用户设备运行。厂商指出过强辅助可能使吸收和损伤上升，并把H4作为拉应力补偿候选 [OX-17]。

工程建议I：若替换现有Ta2O5或TiO2，先比较H4的n/k是否满足目标，再检查多层曲率和老化，不应只因“可以补偿应力”就沿用原层厚。补偿的是层应力-厚度贡献与实际基片响应，而不是材料名称的正负号。相同材料在不同辅助、空气存放和厚度下可能不是同一应力状态。

### 5.5 容易混淆的失效与来料检查

1. **普通H4换HD后同体积装料**：实际装料质量/熔融形状会变；即便成膜n接近，源分布与耗料状态仍可能改变。须记录熔池初始高度、补料方式和批次，不把“高密度”当独立的膜光学参数
2. **只收到H4通称**：可先按本卡设计试片测量，但工艺数据库把manufacturer/grade/composition_status留空并设为未放行；不猜配方
3. **高n且应力小但吸收超标**：继续检测杂质、氧化状态和离子辅助损伤；从500 nm的n单值不能看出k
4. **多次补料后厚度分布改变**：在同一材料卡下增加source_state，而非假定修正板失效；本项给后续蒸发源模型接口，不提前开展下一专题模型研究
5. **“未检出吸收”的旧说明**：仪器检出限未知时不能转成零k；当前表中的非零k也不必与旧说明冲突

### 5.6 选材算例

500 nm单层目标：室温常规H4的n=1.99需62.81 nm；IAD状态n=2.11需59.24 nm。若常规流程的62.81 nm直接搬给IAD，光学厚度约增加6.0%，即使QCM厚度完全准确也会偏离设计。选择H4用于低温聚合物时，还必须确认实际表面温升、电子枪辐射与离子作用；“没有基片加热器”不等于聚合物未受热。

### 5.7 SDS和冻结缺口

115591 H4 MY SDS（2022-10-04，v1.3）所引CLP未列危险分类，要求避尘、干燥和密闭存放 [OX-24]。当前只核官方索引片段，完整打开失败；现场必须取得对应货号当前SDS。未知：用户实际H4的厂家/牌号/COA、完整配比、膜中La/Ti/O、MWIR k、同批次长周期光谱/应力和LIDT。**H4类别研究不等待供应商答复；配方与现场性能未核实也不会被写成已知。**

## 6 把材料卡变成可复用工程库

### 6.1 每次单层试验的最小记录模板

| 类别 | 必填字段 | 为什么必要 |
|---|---|---|
| 身份 | material_target、source_material、manufacturer、grade、lot、COA、SDS版本 | 把化学式、供货形态和膜分开 |
| 源状态 | 阻蒸/电子束、舟/衬埚、原料形态、预处理状态、补料和累计耗料 | 来源分布和反应可随熔池改变 |
| 真空和气氛 | 基础压、工艺压、分压测法、规管位置、O2流量、抽速/节流状态 | sccm不可无条件迁移 |
| 工件 | 基片材料/批次/清洁、实际表面温度、旋转与倾角、位置 | 界面与局部通量影响膜质 |
| 辅助 | 源类型、气体、源设定、可取得的基片电流密度和能谱 | IAD电源参数非材料常数 |
| 光学 | λ网格、n、k、d、拟合模型、粗糙/梯度、T/R/椭偏原始数据、残差 | 防止参数相关性产生假常数 |
| 物理与结构 | ρ测试法、组分测法、XRD、AFM、应力/面形、误差 | 密度与氧化/孔隙分开 |
| 历史 | 退火温度/时间/气氛、空气暴露时间、温湿度、真空循环 | 同片不同状态可能不同参数 |
| 判据 | 波段/角度/偏振、损耗与应力预算、测试阈值由项目定义 | “典型材料”不能代替合同指标 |

### 6.2 建议验证顺序和停止条件

先做身份与单位检查，拒绝缺波长/相态的n、缺材料状态的ρ进入默认库。随后获得独立d以及多波段n/k，检查是否能同时解释T、R与椭偏；再做结构/组成验证与干湿/真空前后对照。最后把单层库带入已批准的膜系验证，补充对应波长的吸收、散射与耐久试验。

本轮停止于“足以形成五卡、关键条件可追溯、冲突不隐藏”的资料冻结；不会为了填满未知列而无限找文献，更不擅自扩展到清单外材料。以下是后续实验入口，不表示已经安排或完成：

- Ta2O5：同批纯度/成分、n/k/ρ与退火状态联合验证
- TiO2：同厚度条件比较辅助效应，避免n和k混合优化
- SiO2：水/OH和应力/光谱的时间与真空空气敏感性
- Al2O3：结构极化与孔隙的可辨识性，实际IR吸收与界面连续性
- H4：实际厂家货号映射、非零k和长期应力，阻蒸/电子束各自建库

### 6.3 本次交付的一致性核验

2026-10-02本地核验通过：29个来源ID唯一且正文引用全部可回溯；29份逐来源摘要均存在；`data/oxide_property_records.json`含49条记录，五种材料均覆盖；所有null值带未知原因；名义Ta2O5但检出Ti的两条记录设独立sample_state与conflict_flag，并明确禁止进入纯材料默认库。五个算例的四分之一波厚度及单程衰减已按所列公式复算。此检查仅验证结构、来源映射和算术，**不等于光学模型、现场工艺或测量数据已验收**。

## 7 来源直达索引

所有来源访问日期均为2026-10-02；权利和逐来源读取范围见JSON登记及摘要，不再分发原PDF/图片。

- [OX-01 Kurt J. Lesker — Tantalum Pentoxide Evaporation Process Notes](https://www.lesker.com/newweb/deposition_materials/deposition-materials-notes.cfm?pgid=ta4)；Specifications; Thermal/E-beam Evaporation
- [OX-02 Kurt J. Lesker — Titanium Dioxide Evaporation Process Notes](https://www.lesker.com/newweb/deposition_materials/deposition-materials-notes.cfm?pgid=ti4w)；Specifications; Thermal/E-beam Evaporation
- [OX-03 Kurt J. Lesker — Silicon Dioxide Evaporation Process Notes](https://www.lesker.com/newweb/deposition_materials/deposition-materials-notes.cfm?pgid=si2)；Specifications; Thermal/E-beam Evaporation; Z-Factors
- [OX-04 Kurt J. Lesker — Aluminum Oxide Evaporation Process Notes](https://www.lesker.com/newweb/deposition_materials/deposition-materials-notes.cfm?pgid=al6)；Specifications; Thermal/E-beam Evaporation
- [OX-05 Niederwald et al. — Ion-assisted deposition of oxide materials at room temperature by use of different ion sources (1999)](https://opg.optica.org/ao/abstract.cfm?uri=ao-38-16-3610)；Applied Optics 38, 3610–3613; Tables 1–4; DOI 10.1364/AO.38.003610
- [OX-06 Durante et al. — Role of substrate and TiO2 content in TiO2:Ta2O5 coatings for gravitational wave detectors (2024)](https://inspirehep.net/files/3c4e23b65057a6e6b3a6ea500307f62e)；Classical and Quantum Gravity 41 025005; sections 2.1–2.5; Tables 1–2; DOI 10.1088/1361-6382/ad1613
- [OX-07 Amato et al. — High-Reflection Coatings for Gravitational-Wave Detectors: State of The Art and Future Developments (2018)](https://s3.cern.ch/inspire-prod-files-d/daf5e3587dbe1123c14e37ca01873897)；J. Phys.: Conf. Ser. 957 012006; Table 1; section 2.3; DOI 10.1088/1742-6596/957/1/012006
- [OX-08 Selhofer et al. — Properties of titanium dioxide films prepared by reactive electron-beam evaporation from various starting materials (2002)](https://opg.optica.org/ao/abstract.cfm?uri=ao-41-4-756)；Applied Optics 41, 756–762; Table 2; DOI 10.1364/AO.41.000756
- [OX-09 Obstarczyk and Wawrzaszek — Influence of ion beam current on TiO2 coatings (2025)](https://www.beilstein-journals.org/bjnano/articles/16/81)；Beilstein J. Nanotechnol. 16, 1097–1112; Tables 1,4; Experimental; DOI 10.3762/bjnano.16.81
- [OX-10 Heitmann — Properties of Evaporated SiO2, SiOxNy, and TiO2 Films (1971)](https://opg.optica.org/ao/abstract.cfm?uri=ao-10-12-2685)；Applied Optics 10, 2685–2689; DOI 10.1364/AO.10.002685
- [OX-11 Malitson — Interspecimen Comparison of the Refractive Index of Fused Silica (1965)](https://opg.optica.org/josa/abstract.cfm?uri=josa-55-10-1205)；JOSA 55, 1205–1209; abstract Sellmeier; DOI 10.1364/JOSA.55.001205
- [OX-12 Malitson — Refraction and Dispersion of Synthetic Sapphire (1962)](https://www.wip.osapublishing.org/josa/abstract.cfm?uri=josa-52-12-1377)；JOSA 52, 1377–1379; DOI 10.1364/JOSA.52.001377
- [OX-13 Targove, Messerly, Macleod — Ion-assisted deposition of Al2O3 thin films (1987)](https://opg.optica.org/abstract.cfm?uri=OAM-1987-THPO41)；OSA Annual Meeting THPO41; DOI 10.1364/OAM.1987.THPO41
- [OX-14 Eriksson et al. — Infrared optical properties of evaporated alumina films (1981)](https://opg.optica.org/ao/abstract.cfm?uri=ao-20-15-2742)；Applied Optics 20, 2742–2746; DOI 10.1364/AO.20.002742
- [OX-15 Kischkat et al. — Mid-infrared optical properties of thin films of aluminum oxide, titanium dioxide, silicon dioxide, aluminum nitride, and silicon nitride (2012)](https://opg.optica.org/ao/abstract.cfm?uri=ao-51-28-6789)；Applied Optics 51, 6789–6798; DOI 10.1364/AO.51.006789
- [OX-16 SUSONITY — Substance H4 product 108332](https://www.susonity.com/US/en/product/pm/108332)；Attributes; General information
- [OX-17 EMD Electronics — Substances H4 and H4 HD Patinal Product Information, issue 12/2021](https://www.emdgroup.com/Products/PM/us/SUB_H4_H4HD_EMD_2022.pdf)；pages 1–6, especially p2 n/k and p4 evaporation
- [OX-18 EMD Chemicals — Substance H4 HD Patinal Product Information, status 02/2009](https://www.sigmaaldrich.com/deepweb/assets/sigmaaldrich/product/documents/534/266/subh4hd-us-102437-ms.pdf)；Indexed thin-film optical section, Fig. 3 caption
- [OX-19 Friz et al. — New Materials for the Production of Optical Coatings (1992)](https://opg.optica.org/abstract.cfm?uri=OIC-1992-PD4)；Optical Interference Coatings PD4; DOI 10.1364/OIC.1992.PD4
- [OX-20 SUSONITY — Ta2O5 Patinal 108500 SDS SG, revision 2022-12-09](https://www.merckmillipore.com/Web-INTL-Site/en_US/-/USD/ShowDocument-File?Country=SG&DocumentId=108500_SDS_SG_EN.PDF&DocumentType=MSD&DocumentUID=362286534&Language=EN&Origin=SERP&ProductSKU=MDA_CHEM-108500)；sections 1–2; version 1.2; printed 2025-08-03
- [OX-21 Merck — TiO2 black tablets Patinal 111771 SDS MY, revision 2024-10-29](https://www.merckmillipore.com/Web-INTL-Site/en_US/-/USD/ShowDocument-File?Country=MY&DocumentId=111771_SDS_MY_EN.PDF&DocumentType=MSD&DocumentUID=16727255&Language=EN&Origin=SERP&ProductSKU=MDA_CHEM-111771)；sections 2,6,11,13; version 1.5
- [OX-22 SUSONITY — Silicon dioxide 115337 SDS SG, revision 2026-07-10](https://www.merckmillipore.com/Web-CL-Site/en_US/-/CLP/ShowDocument-File?Country=SG&DocumentId=115337_SDS_SG_EN.PDF&DocumentType=MSD&DocumentUID=294624148&Language=EN&Origin=SERP&ProductSKU=MDA_CHEM-115337)；sections 1–3,6–11; version 1.3
- [OX-23 SUSONITY — Aluminium oxide Patinal 100840 SDS IN, revision 2025-08-06](https://www.merckmillipore.com/Web-INTL-Site/en_US/-/USD/ShowDocument-File?Country=IN&DocumentId=100840_SDS_IN_EN.PDF&DocumentType=MSD&DocumentUID=46145806&Language=EN&Origin=SERP&ProductSKU=MDA_CHEM-100840)；sections 1–2,6–8; version 1.5; printed 2025-12-29
- [OX-24 SUSONITY — Substance H4 Patinal 115591 SDS MY, revision 2022-10-04](https://www.merckmillipore.com/Web-INTL-Site/en_US/-/USD/ShowDocument-File?Country=MY&DocumentId=115591_SDS_MY_EN.PDF&DocumentType=MSD&DocumentUID=17649993&Language=EN&Origin=SERP&ProductSKU=MDA_CHEM-115591)；sections 1–2,6–7; version 1.3; printed 2025-08-03
- [OX-25 AGC Electronics Taiwan — Synthetic Fused Silica Glass AQ series](https://www.agc-electronics.com.tw/semiconductor/14454488.html)；Technical properties table
- [OX-26 Kurt J. Lesker FAQ — How do I evaporate silicon dioxide?](https://www.lesker.com/newweb/faqs/question.cfm?id=353)；E-beam paragraph
- [OX-27 Zeng et al. — Effects of water adsorption on properties of electron-beam HfO2/SiO2 high-reflection coatings (2020)](https://api.creol.ucf.edu/Publications/14040.pdf)；Thin Solid Films 697, 137826; abstract and conclusions
- [OX-28 DeVore — Refractive Indices of Rutile and Sphalerite (1951)](https://opg.optica.org/josa/abstract.cfm?uri=josa-41-6-416)；JOSA 41, 416–419; DOI 10.1364/JOSA.41.000416
- [OX-29 Chen et al. — Substrate-dependent optical absorption characteristics of titanium dioxide thin films (1997)](https://opg.optica.org/ao/abstract.cfm?uri=ao-36-19-4403)；Applied Optics 36, 4403–4408; DOI 10.1364/AO.36.004403
