# 06 MgF2 镀膜材料

T04第一轮，2026-10-02。独立卡片由[证据分册](../reports/fluoride_sulfide_substrate_cards.md)提取；修改分册后运行 `python models/build_material_package.py` 同步。此卡是公开资料与工程推导，不是本机实测或量产配方。

### 3.1 身份与选型

CAS 7783-40-6；常用UV–NIR低折射率膜。应区分光学单晶的双折射、蒸发膜的织构/孔隙和IBS膜。单晶nₒ/nₑ不是薄膜两个“可任选”的设计值；只有已测织构和偏振响应时才能使用各向异性膜模型。[IR10,IR12]

### 3.2 光学及物理卡

| 状态 | λ | n / k | 条件/限制 |
|---|---:|---|---|
| Merck蒸发薄膜 [IR10] | 120 nm | 1.612 / 3.5×10⁻³ | 目录示例；未知膜厚、误差 |
| 同上 | 250 nm | 1.396 / 1.5×10⁻⁴ | 不外推到VUV更短端 |
| 同上 | 500 nm | 1.383 / 3.4×10⁻⁵ | 同上 |
| 同上 | 1500 nm | 1.375 / <2×10⁻⁵ | “小于”是边界，不等于零 |
| 单晶 [IR12] | 0.546 µm | nₒ1.379 / nₑ1.390；k未列 | 晶轴条件；仅作材料差异参考 |
| 单晶 [IR12] | 4.0 µm | nₒ1.349 / nₑ1.359；k未列 | 不作为蒸发膜常数 |
| IBS约200 nm膜 [IR13] | 1550 nm | n=1.401±0.005 | 工艺相关；椭偏k检测能力不足以保证低ppm吸收 |

Merck典型薄膜窗口120 nm–7 µm；然而超过约4 µm时四分之一波层变厚、拉应力及开裂风险使常规蒸发MgF₂不适合直接当LWIR低折射率主材料。[IR10] 晶体的“透到7 µm”也不能证明8–12 µm厚层系统可用。

| 参数 | 值 | 状态与条件 |
|---|---|---|
| QCM密度 / z-ratio | 3.18 g/cm³ / 0.637 | Merck设置 [IR10] |
| Packing density | 0.72@20°C沉积；0.98@300°C沉积 | 目录典型比值，测量方法/误差未列 [IR10] |
| 单晶导热率 | 平行21、垂直33.6 W/(m·K) | 300 K、相对晶轴 [IR12] |
| 单晶CTE | 平行13.7、垂直8.9×10⁻⁶ K⁻¹ | 温区未明 [IR12] |
| 单晶E / ν / Knoop | 138 GPa / 0.276 / 415 | Knoop载荷未明，不能与不同载荷直接比 [IR12] |
| 单晶密度 / 比热 | 3.18 g/cm³ / 1003 J/(kg·K) | 温度未明 [IR12] |
| IBS膜E / ν | 115±3 GPa；两片ν=0.28±0.02、0.26±0.02 | 约206 nm膜，机械共振反演 [IR13] |
| IBS膜密度 | 2.7±0.2 g/cm³ | 质量/厚度法；论文RBS另约2.96，测法不可混用 [IR13] |
| 蒸发膜CTE、导热、比热、硬度 | 未获得完整定量数据 | 不用单晶表直接计算膜应力/热传导 |

### 3.3 设备与工艺：必须保留坩埚相容性差异

- [IR10] 提供阻蒸/电子束；W/Mo/Ta/Pt舟及铜坩埚类别，温度1300–1600°C，速率0.5–5 nm/s，基片200–300°C（倾向300°C）。预熔/更新料有助于控制喷溅；低氧牌号≤0.02% O，对比标准≤0.06% O。Ta舟可能损害光学表现，特别是UV。
- [IR11] KJLC 推荐Mo/Ta舟及石墨/FABMATE/Mo电子束衬套，同时标注与W反应；示例约950°C、10⁻⁶ Torr、最高约20 Å/s=2 nm/s。其设备说明建议低功率扫束，避免打孔、局部解离及低料位击穿衬套。
- **冲突处理**：不把Merck的“W可列入”转换为所有W舟安全；也不把950°C与1300–1600°C平均。装料、几何、热电偶/辐射测温位置和牌号不同是待验证变量，不是已经证明的解释。
- 此组来源没有可迁移的通氧/通氟反应气参数；IAD参数也不能拿YbF₃的一组替用。气氛改变需独立小样和尾气安全评估。

### 3.4 密度、退火与环境可靠性

低温蒸发膜可能疏松、附着差；高温工艺改善致密度不意味着所有基片都应加热到300°C。[IR10] 对温敏基片或已镀多层，先在允许温度内做密度/吸水与应力矩阵。

原始IBS研究[IR13]在其样品上发现退火对吸收与机械损耗的最佳点不同；200°C处理降低吸收，后续更高温处理反而增加；约373°C处理出现裂纹。**IBS后退火结果不能作为阻蒸生产处方**。其价值在于证明“退火越热越好”不成立，并提示氧污染、失氟、结晶、热失配必须一起检查。

### 3.5 选型算例

假定500 nm、基片nₛ=1.519、MgF₂ n=1.383，四分之一波厚约90.4 nm，理想单面R≈1.32%，而裸面约4.25%。这是简单可见减反的合理量级；若目标R<0.2%，单层本身折射率匹配不足，应采用多层或重新评估目标。把此层缩放到10 µm会变成微米级厚层，且超出常规材料透明/应力适用范围，不能只按比例放大。

### 3.6 安全

Crystran MgF₂晶体SDS（2026-07-06）指出粉尘、皮肤/眼刺激与吸入风险、强酸不相容及HF分解产物。[IR14] 对Patinal颗粒另已定位Merck105834的专属官方SDS入口。[IR24] 装料和清腔应防尘、密闭收集残料；玻璃/金属清洗残留物的相容性先评估。块材SDS不替代颗粒或纳米粉的实际版本。

## 本卡证据入口

- [IR10 Merck/EMD Magnesium Fluoride Patinal Product Information](https://www.emdgroup.com/Products/PM/us/MgF2_EMD_2022.pdf)
- [IR11 Kurt J. Lesker Magnesium Fluoride MgF2 Evaporation Process Notes](https://www.lesker.com/newweb/deposition_materials/deposition-materials-notes.cfm?pgid=mg2)
- [IR12 Crystran Magnesium Fluoride MgF2 optical material data](https://www.crystran.com/optical-materials/magnesium-fluoride-mgf2/)
- [IR13 Granata et al., Optical and mechanical properties of ion-beam-sputtered MgF2 thin films for gravitational-wave interferometers](https://arxiv.org/abs/2111.01646)
- [IR14 Crystran Magnesium Fluoride Optical Crystal SDS](https://www.crystran.com/wp-content/uploads/2025/09/magnesium-fluoride-mgf2-msds.pdf)
- [IR24 Merck Magnesium fluoride 105834 Patinal SDS official entry](https://www.merckmillipore.com/INTL/en/product/msds/MDA_CHEM-105834)
