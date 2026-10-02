# 十二种材料与蒸发源耦合

下面的候选容器和机制继承T04逐材料卡，并在本轮复核主要原厂页面。候选不等于批准组合；任何几何、温度、功率、气体流量或扫描参数都没有直接转为本机生产设定。所有材料的本机角指数、蒸气压模型、污染阈值和允许源寿命目前均为未知，机器可读表以null保留。

## 1 先确认输入材料身份

每个源实例要同时有source_material与film_target：源为Ti3O5而目标TiO2，或源为SiO而目标SiO2，不能共用一个名字掩盖化学反应。颗粒、压片、预制料块、纯度、粘结剂、潮气、已用残料和COA是必要字段。H4须厂家/货号；YbF3是镱氟化物，不得替换为YF3；Ge掺杂/电阻率不能由元素符号猜。

同一材料在热蒸发、电子束、反应氧、IAD等条件下膜n/k与ρ不同。源模型负责到达物质及角向/时间历史；材料模型负责这些条件下的膜状态。没有实测时，不能用T04的块材光学常数为源模型“补齐精度”。

## 2 候选源与需要区别的机制

| 材料 | 电阻源候选 | 电子束源候选 | 必须进入状态的机制 | 证据入口 |
|---|---|---|---|---|
| Ta2O5 | Ta舟，适用性另验 | FABMATE/Ta | 放氧/还原、热点、源面与膜O/Ta | T04-OX-01 |
| ZnS | Mo/Ta/Pt舟按牌号 | Mo/Ta/玻璃碳类别按原厂 | 解离/复合、S/Zn与残气、温度定义冲突 | T04-IR01/02 |
| TiO2 | W/Mo舟 | FABMATE/Ta | 原始氧化态、放氧变黑、Ta相关还原 | T04-OX-02 |
| YbF3 | Mo/Ta舟 | Mo衬里 | 局部过热、解离/失氟、牌号身份 | T04-IR05 |
| SiO2 | W舟/Ta挡板盒为困难路线 | FABMATE/石墨/Ta/适配铜 | 源料与目标膜区分、钻孔、OH/缺氧 | T04-OX-03 |
| MgF2 | Mo/Ta；W有来源冲突 | 石墨/FABMATE/Mo/适配铜类别 | 含氧牌号、喷点、容器污染/失氟 | T04-IR10/11 |
| Al2O3 | 困难，无通用舟方案 | FABMATE/W/适配铜 | 高热负荷、污染、源面结壳/形状 | T04-OX-04 |
| H4 | 仅所引Patinal可研究Mo舟 | 所引Patinal优先Mo衬里 | 商品牌号、致密粒料、初始料位、熔面 | T04-OX-17 |
| Ge | W/Ta凹舟 | 石墨/FABMATE/适配铜 | 熔体与衬里机械结合、冷热循环 | T04-M01 |
| Cu | W/Mo舟、W篮、间接Al2O3 | 石墨/Mo | 实际相态、润湿/氧化、活跃区 | T04-M02 |
| Cr | 镀Cr W棒/W舟 | 石墨/FABMATE/W/适配铜 | 常见升华面、颗粒接触与耗料 | T04-M03 |
| Al | 难熔金属舟有反应/寿命限制 | TiB2–BN等候选，石墨需防碳 | 合金化、润湿外溢、碳/氧污染 | T04-M04 |

完整来源链接、核读范围和限制在[sources/source_registry.json](../sources/source_registry.json)，原始材料卡由[data/material_source_matrix.json](../data/material_source_matrix.json)逐项连接。商品FABMATE并非任意石墨的同义词；上述同列候选也不表示热导、润湿或污染等价。

## 3 氧化物不是一套通氧模型

Ta2O5的源放氧、膜氧不足与污染可能共同影响吸收；应把源功率/压力峰、O/Ta、k和颗粒关联。TiO2的白料加热可放氧变黑，所以“黑色必报废”不能从SiO2经验照搬。Ta被列为TiO2容器候选，但同一页面又提示Ta的还原作用，必须记录为有条件组合，不能删掉冲突。[Ta2O5原厂](https://www.lesker.com/newweb/deposition_materials/deposition-materials-notes.cfm?pgid=ta4)、[TiO2原厂](https://www.lesker.com/newweb/deposition_materials/deposition-materials-notes.cfm?pgid=ti4w)

SiO2页面同时有源料温度、挡板盒温度和不同供氧经验，这些不是同一个测温位置/源结构，不能作一条通用蒸气压拟合。若使用SiO反应源，要以Si与O的元素质量平衡解释成膜。Al2O3的高温使热源/容器耦合特别重要；有效膜密度与蓝宝石密度不同的问题仍由同批膜计量解决。[SiO2原厂](https://www.lesker.com/newweb/deposition_materials/deposition-materials-notes.cfm?pgid=si2)、[Al2O3原厂](https://www.lesker.com/newweb/deposition_materials/deposition-materials-notes.cfm?pgid=al6)

本轮不设置“氧化物统一氧分压”。气体进入位置、有效抽速、真空计位置、基片热预算与反应概率会改变相同压力数字的意义；增加氧还可能改变传播散射。T02弹道模型若用在反应蒸发，必须重新检验传播条件。

## 4 ZnS与氟化物的组分和容器边界

ZnS资料允许阻蒸/电子束，并说明可能解离后在基片重组。两个厂家给出的源温表差异大，T04已隔离，T05不平均、不用其差值反推蒸发焓。看见QCM稳定时，仍需用膜S/Zn与FTIR确认关键波段吸收；稳定总质量不意味着硫比例稳定。[ZnS资料](https://www.emdgroup.com/Products/PM/us/ZnS_tcm2080-us.pdf)

YbF3的电子束建议强调局部能量密度；本轮不据此发明电流/斑径阈值。MgF2厂商对W舟相容性和源温的表述不同，且热舟污染对UV尤其值得核查。源材料的含氧规格、形态与更新历史须保留到源状态记录。不能从“KJLC概览写分子蒸发”推出所有氟化物在所有束流下都严格守恒。[YbF3资料](https://www.emdgroup.com/Products/PM/us/101601_YbF3_tcm2080_127462-us.pdf)、[MgF2 Patinal](https://www.emdgroup.com/Products/PM/us/MgF2_EMD_2022.pdf)、[MgF2 KJLC](https://www.lesker.com/newweb/deposition_materials/deposition-materials-notes.cfm?pgid=mg2)

IAD失氟属于到达后作用，不能反推为源端唯一故障。若n上升同时k上升，需同时考虑密实化、组成变化与缺陷；不把所有光学变化用源强标量解释。

## 5 H4的身份和历史条件

所引Patinal H4是商品混合氧化物家族，H4与H4 HD的装料热行为不应相同处理。原厂将反复装料的初始高度与分布重复性联系起来，支持把源高度作为校准条件。每层速率相同但起始料位不同，应至少进入不同源状态版本，不能自动继承同一修正板算子。[原厂资料pp4–5](https://www.emdgroup.com/Products/PM/us/SUB_H4_H4HD_EMD_2022.pdf)

未取得用户厂家/COA前，本册不把源料的La/Ti比例、膜组成、发射率或蒸气物种写成已知。资料研究可继续，但没有这些信息就不能建立带真实单位的热预测或膜光学放行标准。

## 6 Ge与金属源的不同失效路径

Ge熔体与衬里的机械结合使热循环次数具有物理意义；每次复热不是“全新相同源”。热裂纹或料块脱离可能同时改变接触热阻和足迹。Cu舟/篮与间接坩埚路线的热惯性不同，应按结构分开拟合；高热导块材不保证任意装料均温。[Ge](https://www.lesker.com/newweb/deposition_materials/depositionmaterials_evaporationmaterials_1.cfm?pgid=ge1)、[Cu](https://www.lesker.com/newweb/deposition_materials/deposition-materials-notes.cfm?pgid=cu1)

Cr在一些常见热蒸发情景主要升华。其Q随接触面积和活跃表面改变，不能由液体体积—高度关系强行求h(t)。电子束局部状态仍须另验。Al则需要把舟合金化、衬里选择、碳污染与残气历史纳入记录；提高功率可能补偿瞬时Q，却加速容器失效或改变污染。[Cr](https://www.lesker.com/newweb/deposition_materials/deposition-materials-notes.cfm?pgid=cr1)、[Al](https://www.lesker.com/newweb/deposition_materials/deposition-materials-notes.cfm?pgid=al1)

## 7 每个组合如何由候选升级为本机证据

先做身份/相容性审查，再按设备批准条件取得源状态、无掩模多位置膜厚与QCM同步日志；区分新装料、稳定料和耗料阶段。对候选容器评估污染、颗粒、膜n/k、应力和重复性；只满足蒸发速率不够。带掩模验证留在源模型冻结之后，并留出不同方位/角度/料位。没有用户设备与样片数据，本轮不报告“某材料源已校准”。
