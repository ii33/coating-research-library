# 05 SiO2 镀膜材料

T04第一轮，2026-10-02。独立卡片由[证据分册](../reports/oxide_material_cards.md)提取；修改分册后运行 `python models/build_material_package.py` 同步。此卡是公开资料与工程推导，不是本机实测或量产配方。

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

## 本卡证据入口

- [OX-03 Kurt J. Lesker — Silicon Dioxide Evaporation Process Notes](https://www.lesker.com/newweb/deposition_materials/deposition-materials-notes.cfm?pgid=si2)
- [OX-05 Niederwald et al. — Ion-assisted deposition of oxide materials at room temperature by use of different ion sources (1999)](https://opg.optica.org/ao/abstract.cfm?uri=ao-38-16-3610)
- [OX-07 Amato et al. — High-Reflection Coatings for Gravitational-Wave Detectors: State of The Art and Future Developments (2018)](https://s3.cern.ch/inspire-prod-files-d/daf5e3587dbe1123c14e37ca01873897)
- [OX-10 Heitmann — Properties of Evaporated SiO2, SiOxNy, and TiO2 Films (1971)](https://opg.optica.org/ao/abstract.cfm?uri=ao-10-12-2685)
- [OX-11 Malitson — Interspecimen Comparison of the Refractive Index of Fused Silica (1965)](https://opg.optica.org/josa/abstract.cfm?uri=josa-55-10-1205)
- [OX-15 Kischkat et al. — Mid-infrared optical properties of thin films of aluminum oxide, titanium dioxide, silicon dioxide, aluminum nitride, and silicon nitride (2012)](https://opg.optica.org/ao/abstract.cfm?uri=ao-51-28-6789)
- [OX-22 SUSONITY — Silicon dioxide 115337 SDS SG, revision 2026-07-10](https://www.merckmillipore.com/Web-CL-Site/en_US/-/CLP/ShowDocument-File?Country=SG&DocumentId=115337_SDS_SG_EN.PDF&DocumentType=MSD&DocumentUID=294624148&Language=EN&Origin=SERP&ProductSKU=MDA_CHEM-115337)
- [OX-25 AGC Electronics Taiwan — Synthetic Fused Silica Glass AQ series](https://www.agc-electronics.com.tw/semiconductor/14454488.html)
- [OX-26 Kurt J. Lesker FAQ — How do I evaporate silicon dioxide?](https://www.lesker.com/newweb/faqs/question.cfm?id=353)
- [OX-27 Zeng et al. — Effects of water adsorption on properties of electron-beam HfO2/SiO2 high-reflection coatings (2020)](https://api.creol.ucf.edu/Publications/14040.pdf)
