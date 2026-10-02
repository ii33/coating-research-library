# 03 TiO2 镀膜材料

T04第一轮，2026-10-02。独立卡片由[证据分册](../reports/oxide_material_cards.md)提取；修改分册后运行 `python models/build_material_package.py` 同步。此卡是公开资料与工程推导，不是本机实测或量产配方。

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

## 本卡证据入口

- [OX-02 Kurt J. Lesker — Titanium Dioxide Evaporation Process Notes](https://www.lesker.com/newweb/deposition_materials/deposition-materials-notes.cfm?pgid=ti4w)
- [OX-05 Niederwald et al. — Ion-assisted deposition of oxide materials at room temperature by use of different ion sources (1999)](https://opg.optica.org/ao/abstract.cfm?uri=ao-38-16-3610)
- [OX-08 Selhofer et al. — Properties of titanium dioxide films prepared by reactive electron-beam evaporation from various starting materials (2002)](https://opg.optica.org/ao/abstract.cfm?uri=ao-41-4-756)
- [OX-09 Obstarczyk and Wawrzaszek — Influence of ion beam current on TiO2 coatings (2025)](https://www.beilstein-journals.org/bjnano/articles/16/81)
- [OX-15 Kischkat et al. — Mid-infrared optical properties of thin films of aluminum oxide, titanium dioxide, silicon dioxide, aluminum nitride, and silicon nitride (2012)](https://opg.optica.org/ao/abstract.cfm?uri=ao-51-28-6789)
- [OX-21 Merck — TiO2 black tablets Patinal 111771 SDS MY, revision 2024-10-29](https://www.merckmillipore.com/Web-INTL-Site/en_US/-/USD/ShowDocument-File?Country=MY&DocumentId=111771_SDS_MY_EN.PDF&DocumentType=MSD&DocumentUID=16727255&Language=EN&Origin=SERP&ProductSKU=MDA_CHEM-111771)
- [OX-28 DeVore — Refractive Indices of Rutile and Sphalerite (1951)](https://opg.optica.org/josa/abstract.cfm?uri=josa-41-6-416)
- [OX-29 Chen et al. — Substrate-dependent optical absorption characteristics of titanium dioxide thin films (1997)](https://opg.optica.org/ao/abstract.cfm?uri=ao-36-19-4403)
