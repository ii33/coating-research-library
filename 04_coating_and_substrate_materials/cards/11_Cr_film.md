# 11 Cr 镀膜材料

T04第一轮，2026-10-02。独立卡片由[证据分册](../reports/metal_ge_material_cards.md)提取；修改分册后运行 `python models/build_material_package.py` 同步。此卡是公开资料与工程推导，不是本机实测或量产配方。

### 数据与光学代价

Cr常被选为附着层候选，但即使很薄，其光学损耗也必须计入。是否允许3、5或10 nm取决于产品和基片，不能把经验厚度当通用规范。

| 参数 | 数值 | 条件与来源 | 不确定度/边界 |
|---|---|---|---|
| 块料密度 | 7.2 g/cm³ | M03目录 | 膜ρ未测 |
| 熔点 | 1857°C | M03目录 | 文献温标/纯度差异本轮未展开 |
| 热导率 | 94 W/(m·K) | M03；温度未给 | 不是纳米膜有效值 |
| 线膨胀系数 | 4.9×10⁻⁶ K⁻¹ | M03；温区未给 | 不能单独保证应力匹配 |
| QCM Z ratio | 0.305 | M03 | 起始参数，非校准结果 |
| n,k@0.6328 μm | 3.13990，3.31505 | J&C1974数字化插值 | 原文大部分谱域估计<±2%，不是本点认证误差 |
| n,k@1.55 μm | 3.66829，4.18005 | 同一室温多晶蒸镀数据 | 文件上限1.937 μm |

J&C1974透过测试膜厚20–50 nm，一些易氧化样品在N2中测量。[M06](https://doi.org/10.1103/PhysRevB.9.5056) 这与空气暴露、岛状3 nm附着层不是同一对象；小于连续成膜尺度时，应改用形貌/有效介质模型或直接测复合结构。

### 蒸发行为

Cr在KJLC讨论的约1400°C工况低于其目录熔点，主要升华；颗粒与舟的热接触使源温不能简单等于加热舟温。镀Cr钨棒可用于薄附着层，料量有限；W舟也是其示例。电子束可采用FABMATE、石墨、W或其允许的裸铜水冷炉床结构。[M03](https://www.lesker.com/newweb/deposition_materials/deposition-materials-notes.cfm?pgid=cr1)

工程推论：把Cr和Al都写成“液面高度随消耗下降”会误配源模型。Cr应先识别升华表面、活跃面积和热接触演化；不依据通用网页的“熔池”措辞强行假定熔融。实际电子束局部可能与热蒸发相态不同，需测量/源观察支持。

### 工程算例

632.8 nm下由J&C数据算强度1/e衰减长度δ_I=λ/(4πk)=15.19 nm。理想均匀体内单程传播5 nm，因吸收强度乘因子exp(−5/15.19)=0.7195。**这不是空气/Cr/基片结构的透过率或“28%附着层损失”**；真实场在界面多次反射，超薄层可能不连续。其意义是警告不能把Cr视作光学零厚度。选型应对有/无Cr、不同实测厚度的同批样品比较附着与R/T，并用完整膜系模型计算局部吸收。

### 安全与缺口

Cr金属块料SDS2022-07-18未将供应态分类为危害品，同时明确沉积/机械加工产生烟尘风险。[M18](https://www.lesker.com/msds/pdfs/108B5F3A508AF1C1AD5A1C80CE7D64FAC9A7938CBA21919BF203EC809BDF2FFF.pdf) 不能把Cr金属直接当Cr(VI)；也不能反过来保证腔内所有混合残渣均为金属Cr。清腔要先核对历史工艺和残渣组分。缺口：超薄膜氧化/连续性、残余应力、实际附着破坏模式、IR k及离子辅助窗口；不填猜测值。

## 本卡证据入口

- [M03 KJLC Chromium evaporation notes](https://www.lesker.com/newweb/deposition_materials/deposition-materials-notes.cfm?pgid=cr1)
- [M06 Johnson and Christy 1974 Optical constants of transition metals](https://doi.org/10.1103/PhysRevB.9.5056)
- [M18 KJLC Chromium pieces SDS revision5 2022-07-18](https://www.lesker.com/msds/pdfs/108B5F3A508AF1C1AD5A1C80CE7D64FAC9A7938CBA21919BF203EC809BDF2FFF.pdf)
