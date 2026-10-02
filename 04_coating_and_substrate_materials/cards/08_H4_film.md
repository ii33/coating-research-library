# 08 H4 商品高折射率镀膜材料

T04第一轮，2026-10-02。独立卡片由[证据分册](../reports/oxide_material_cards.md)提取；修改分册后运行 `python models/build_material_package.py` 同步。此卡是公开资料与工程推导，不是本机实测或量产配方。

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

## 本卡证据入口

- [OX-05 Niederwald et al. — Ion-assisted deposition of oxide materials at room temperature by use of different ion sources (1999)](https://opg.optica.org/ao/abstract.cfm?uri=ao-38-16-3610)
- [OX-16 SUSONITY — Substance H4 product 108332](https://www.susonity.com/US/en/product/pm/108332)
- [OX-17 EMD Electronics — Substances H4 and H4 HD Patinal Product Information, issue 12/2021](https://www.emdgroup.com/Products/PM/us/SUB_H4_H4HD_EMD_2022.pdf)
- [OX-18 EMD Chemicals — Substance H4 HD Patinal Product Information, status 02/2009](https://www.sigmaaldrich.com/deepweb/assets/sigmaaldrich/product/documents/534/266/subh4hd-us-102437-ms.pdf)
- [OX-19 Friz et al. — New Materials for the Production of Optical Coatings (1992)](https://opg.optica.org/abstract.cfm?uri=OIC-1992-PD4)
- [OX-24 SUSONITY — Substance H4 Patinal 115591 SDS MY, revision 2022-10-04](https://www.merckmillipore.com/Web-INTL-Site/en_US/-/USD/ShowDocument-File?Country=MY&DocumentId=115591_SDS_MY_EN.PDF&DocumentType=MSD&DocumentUID=17649993&Language=EN&Origin=SERP&ProductSKU=MDA_CHEM-115591)
