# 09 Ge 镀膜材料

T04第一轮，2026-10-02。独立卡片由[证据分册](../reports/metal_ge_material_cards.md)提取；修改分册后运行 `python models/build_material_package.py` 同步。此卡是公开资料与工程推导，不是本机实测或量产配方。

### 材料身份和适用问题

Ge 是元素锗；源料与沉积膜有不同状态。KJLC 示例产品是 Sb 掺杂 n 型源料，电阻率5–40 Ω·cm，不代表一切光学 Ge。沉积结果可能是非晶、部分结晶或多晶，须把相态、基片温度、离子辅助、氧污染和退火历史编入样品身份。[M01](https://www.lesker.com/newweb/deposition_materials/depositionmaterials_evaporationmaterials_1.cfm?pgid=ge1)

Ge 膜适合红外高折射率层候选；透明区不能按基片宣传的透过范围直接给膜设计。2018年原研究针对熔石英上电子束非晶Ge，用R/T联合和Cody–Lorentz模型关联吸收区与透明区，专门讨论膜折射率高于块材的原因。[M13](https://doi.org/10.1016/j.mssp.2018.04.019) 该文全文参数未取得，不能凭摘要还原配方或色散系数。

### 有条件参数表

| 参数 | 数值/状态 | 对象与条件 | 不确定度及用途 |
|---|---|---|---|
| 源料理论密度 | 5.32 g/cm³ | M01规格表；正文另写5.35 | 来源内部差异未消解；仅初估装料，膜密度未知 |
| 熔点 | 937°C | M01块料 | 未给误差；不是源工作温度 |
| 块料热导率 | 60 W/(m·K) | M01；温度未说明 | 不代替非晶膜热导率 |
| 块料线膨胀系数 | 6×10⁻⁶ K⁻¹ | M01；温区未说明 | 仅材料筛选，膜应力不直接反算 |
| 平衡蒸气压10⁻⁴ Torr对应温度 | 1167°C | M01源料参考表 | 平衡值，不是腔体基压或基片温度 |
| 历史蒸镀膜n | 约4.3，λ>6 μm | M15，40 nm–1 μm膜，玻璃/石英/CaF2承载 | 历史工艺；不默认现代机器相同 |
| 本机n(λ)、k(λ)、ρ、σ、α_T | 未知 | 需同批见证片 | 不以块材补空值 |

### 蒸发与成膜判断

M01支持W/Ta舟热蒸发以及石墨/FABMATE电子束衬里。其给出的1400°C、基压≤10⁻⁶ Torr及1–5 Å/s是其设备经验示例；**本轮不把它们转成用户机台设定**。应先区分源温度、基片温度和测量温度。Ge在该工作情形由熔体蒸发，液体与衬里机械结合及热膨胀差可在冷却/复热时导致开裂。[M01](https://www.lesker.com/newweb/deposition_materials/depositionmaterials_evaporationmaterials_1.cfm?pgid=ge1)

工程推论：T05不能只给Ge一个固定点源和常数速率；至少要记录预熔前后几何、液位和衬里循环次数。速率突然改变时，分别排查真实蒸发通量、熔池移动/喷溅、QCM热漂移与膜密度，不把所有偏差塞进tooling factor。

测量时升温与沉积后退火也必须分开。IBAD Ge/CVD ZnS 的2–5 μm研究在室温至773 K测得n、k随测量温度增加；这是温变光学证据。[M12](https://doi.org/10.1016/j.tsf.2015.06.029) 另有350–500°C退火系列报告晶化与粗糙度变化，趋势不等于“退火越高越透明”。该条只核实摘要，不能作为工艺窗口。[M14](https://rmme.ijournals.cn/rmme/article/html/E20200054?st=search)

### 工程算例和验收

只用来说明状态误配：在10 μm做理想四分之一波光学厚度，n=4.0时d=0.625 μm；历史膜n=4.3时d=0.5814 μm，相差约7.0%。这两个数不是本机上下限，也没有含吸收/色散。实际决策应先测Ge单层n,k，再决定是否用更高n降低层厚；不能以同样物理厚度直接比较两种膜系。

最小证据包：R/T/椭偏联合、独立台阶厚度、FTIR覆盖实际IR带、退火前后XRD和AFM、同载具中心/边缘见证片；对漂移分别估计n与d而非仅拟合nd。对高温应用在使用温度测k，不能只记录室温n。

### 安全和未决项

KJLC2017 Ge粉/块SDS供应态未分类，但明确加工和沉积会生成粉尘/烟粒；清腔时按真实残渣控制粉尘、通风和收集，不把“未分类”等同可直接吸尘吹扫。[M16](https://www.lesker.com/msds/pdfs/0F73F3913DF080C980E5D3A5F823C7924D71421021348335582F774CD8C026D2.pdf) 未决：用户源料的掺杂、纯度证书、膜氧含量、附着/应力和有效密度；均是后续校准项，不阻断T05资料研究。

## 本卡证据入口

- [M01 KJLC Germanium pieces and evaporation notes](https://www.lesker.com/newweb/deposition_materials/depositionmaterials_evaporationmaterials_1.cfm?pgid=ge1)
- [M12 Liu et al 2015 Temperature dependence of infrared optical constants of Ge films](https://doi.org/10.1016/j.tsf.2015.06.029)
- [M13 Study on optical constants of amorphous Ge films 2018](https://doi.org/10.1016/j.mssp.2018.04.019)
- [M14 Effect of annealing temperature on Ge thin films](https://rmme.ijournals.cn/rmme/article/html/E20200054?st=search)
- [M15 Brattain and Briggs 1949 Optical constants of Ge](https://doi.org/10.1103/PhysRev.75.1705)
- [M16 KJLC Germanium powder and pieces SDS revision 6 2017-06-13](https://www.lesker.com/msds/pdfs/0F73F3913DF080C980E5D3A5F823C7924D71421021348335582F774CD8C026D2.pdf)
