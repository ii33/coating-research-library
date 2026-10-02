# 07 Al2O3 镀膜材料

T04第一轮，2026-10-02。独立卡片由[证据分册](../reports/oxide_material_cards.md)提取；修改分册后运行 `python models/build_material_package.py` 同步。此卡是公开资料与工程推导，不是本机实测或量产配方。

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

## 本卡证据入口

- [OX-04 Kurt J. Lesker — Aluminum Oxide Evaporation Process Notes](https://www.lesker.com/newweb/deposition_materials/deposition-materials-notes.cfm?pgid=al6)
- [OX-12 Malitson — Refraction and Dispersion of Synthetic Sapphire (1962)](https://www.wip.osapublishing.org/josa/abstract.cfm?uri=josa-52-12-1377)
- [OX-13 Targove, Messerly, Macleod — Ion-assisted deposition of Al2O3 thin films (1987)](https://opg.optica.org/abstract.cfm?uri=OAM-1987-THPO41)
- [OX-14 Eriksson et al. — Infrared optical properties of evaporated alumina films (1981)](https://opg.optica.org/ao/abstract.cfm?uri=ao-20-15-2742)
- [OX-23 SUSONITY — Aluminium oxide Patinal 100840 SDS IN, revision 2025-08-06](https://www.merckmillipore.com/Web-INTL-Site/en_US/-/USD/ShowDocument-File?Country=IN&DocumentId=100840_SDS_IN_EN.PDF&DocumentType=MSD&DocumentUID=46145806&Language=EN&Origin=SERP&ProductSKU=MDA_CHEM-100840)
