# 16 ZnSe 基片

T04第一轮，2026-10-02。独立卡片由[证据分册](../reports/fluoride_sulfide_substrate_cards.md)提取；修改分册后运行 `python models/build_material_package.py` 同步。此卡是公开资料与工程推导，不是本机实测或量产配方。

### 6.1 身份及等级

ZnSe，CAS1315-09-9；本卡以CVD多晶光学级为主，不能与掺杂激光晶体或蒸发ZnSe膜互换。Coherent区分常规光学料和折射率均匀性受控的prism grade；高功率用途必须同时控制体吸收、内缺陷、加工损伤与薄膜吸收。[IR21,IR22]

### 6.2 光学、温度与厚度

| λ (µm) | n | α (cm⁻¹)及条件 |
|---:|---:|---|
| 0.62 | 2.5994 | 未给；可见短波边缘不能外推 |
| 1.3 | 未摘录 | 0.005，Crystran典型 |
| 3.8 | 未摘录 | 0.0004，Crystran典型 |
| 5.0 | 2.4295 | 5.25 µm另列0.0004，不能标成同波长 |
| 10.6 | 2.4028 | Coherent<0.0005；Crystran0.0005 |
| 15.0 | 2.3665 | 未给 |

n与Crystran α来自[IR21]，Coherent上限来自[IR22]；目录误差未给。10.6 µm、α=0.0005 cm⁻¹对应k≈4.22×10⁻⁸，是α的派生等价值，不是独立高精度测量。目录典型窗口0.6–21 µm未给固定阈值；Coherent附6.3 mm透过谱及3 mm、25–400°C温变曲线，因此带宽和长波端不能脱离温度/厚度。[IR21,IR22]

### 6.3 热力参数表

| 参数 | 数值 | 条件/来源 |
|---|---|---|
| 密度 | 5.27 g/cm³ | Coherent20°C [IR22] |
| 导热率 | 18 W/(m·K) | Coherent20°C（0.18 W/cm/°C换算） [IR22] |
| 比热 | 356 J/(kg·K) | Coherent20°C [IR22]；Crystran339，未给同一温点，不平均 |
| CTE | 7.57×10⁻⁶ K⁻¹ | Coherent20°C [IR22]；Crystran7.1×10⁻⁶@273 K，条件不同 |
| dn/dT | 6.1×10⁻⁵ K⁻¹ | 10.6 µm，20°C [IR22]；Crystran298 K一致量级 |
| E / ν | 67.2 GPa / 0.28 | Coherent20°C [IR22] |
| 破坏模量 | 55.1 MPa | Coherent20°C；试样统计未明，不是许用应力 |
| Knoop | 105–120 kgf/mm² | Coherent载荷未明；Crystran120、500 g [IR21,IR22] |
| 断裂韧性 | 0.5 MPa·m^½ | Coherent原单位0.5×10⁶ N/m^1.5换算 [IR22] |
| 相变/分解温度 | 不作设计上限 | SDS与物性表针对不同气氛/判据；正常空气应用遵守厂商温度限制 |

### 6.4 加工、成膜、可靠性

- 高功率CO₂系统不能仅验总透过率：AR后T接近满量程仍可能掩盖足以引起热透镜的ppm级吸收。Coherent用CO₂真空量热测体吸收。[IR22] 需分别指定体、两面膜和表面污染吸收。
- 软而脆、低韧性：擦拭颗粒可能造成划伤，边缘缺陷和过约束装夹可降低有效强度。强度须以加工后成品/统计试样验证，不能因材料不吸湿就免除机械和污染检查。
- 温升影响n和厚度；用dn/dT单项无法完整预测焦漂，应加几何热膨胀、温度场、安装架和应力光学。若采用保护膜，检验其与光学膜的界面及自身10.6 µm吸收。
- Crystran提示空气正常应用不超过250°C；SDS另外给出火灾分解条件，二者不是同一“耐温”。[IR21,IR23] 不把Coherent高温透过率研究曲线解释成长期操作许可。
- 本卡没有为ZnSe基片编写阻蒸/电子束蒸发处方：这里是承膜块材；其清洗和预处理不得无条件继承ZnS、玻璃或Ge的方案。

### 6.5 选型算例

10.6 µm、5 mm ZnSe窗、n=2.4028、取α=0.0005 cm⁻¹：内部透过率99.975%；裸双面非相干总T≈70.93%，主要损失来自反射而非体吸收。若有1 kW的**单程体内入射功率**，体吸收估计约0.25 W；这是单程近似，未含膜吸收、表面污染、反射驻波和热反馈。比较ZnS同厚10.6 µm的α=0.2可见，材料体吸收选择对热设计的重要性远超过仅比较目录n。

### 6.6 安全

Crystran 2026-07-06官方ZnSe SDS列吞咽/吸入毒性和水生环境危害，特别强调加工粉尘、酸接触可释放高毒H₂Se、火灾分解烟气。[IR23] 完整窗口正常受控使用与切削、破裂、烧损、清腔是不同暴露情景。破损/烧损光学件先隔离，由EHS制定收集与废弃流程；不以日常普通垃圾处理，不干扫或使用无适当过滤的吸尘设备。

## 本卡证据入口

- [IR21 Crystran Zinc Selenide ZnSe optical material data](https://www.crystran.co.uk/optical-materials/zinc-selenide-znse/)
- [IR22 Coherent Optical Materials — ZnSe](https://www.coherent.com/content/dam/coherent/site/en/resources/datasheet/optics/optical-materials-ds.pdf)
- [IR23 Crystran Zinc Selenide Optical Crystal SDS](https://www.crystran.com/wp-content/uploads/2025/09/zinc-selenide-znse-msds.pdf)
