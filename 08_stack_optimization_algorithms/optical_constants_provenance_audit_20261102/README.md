# 光学常数来源审计：显式零值、缺失域与样品边界

**数据库页面中没有某段 k，不等于作者原始数表中没有该段；作者表写出的 `k = 0` 也不等于已经证明该样品完全无吸收。** 区分这两类情况，保留源头、模型与数值域，才能判断何时可用作参考模型，何时必须标为未知。本文只说明通用资料审计方法，不导入材料数据、不修改软件内置材料库。

## 作者数表与精简页面：三个示例

Amotchkina 等报告电子束蒸发薄膜在 **0.4–12 µm** 的表征，作者补充文件区分 ZnS/YbF₃ 薄膜与 ZnSe 基片，并列出色散及非参数模型。论文的表征范围与随附表格的数字范围不是同一个声明；表格超出 12 µm 的数值不能自动当成有同等实测支撑的外延。[论文摘要](https://pubmed.ncbi.nlm.nih.gov/32225351/)；[作者补充说明](https://refractiveindex.info/download/data/2020/Amotchkina/Summary_for_RefractiveIndexINFO.pdf)。

下表为本次逐行核读作者工作簿的**节点**结果，不是对节点之间连续光谱的额外测量。精简页面列出的是其选用的 k 范围，不能将页面未列范围一律反推为原表未知；尤其 ZnSe 的页面选域还可能未涵盖原表零段之后的数值，应逐项核对而非假定仅删零。

| 来源及物态 | 原作者表的波长范围 | 原表显式零 k 节点段 | 数据库页面所列 k 范围 |
|---|---|---|---|
| [ZnS 薄膜](https://refractiveindex.info/download/data/2020/Amotchkina/ZnS_nk.xlsx) | 400–14000 nm | 1000–14000 nm | [0.4–1.0 µm](https://refractiveindex.info/?shelf=main&book=ZnS&page=Amotchkina) |
| [YbF₃ 薄膜](https://refractiveindex.info/download/data/2020/Amotchkina/YbF3_nk.xlsx) | 400–13974.951 nm | 400–9016.795 nm | [9.0–14 µm](https://refractiveindex.info/?shelf=main&book=YbF3&page=Amotchkina) |
| [ZnSe 基片](https://refractiveindex.info/download/data/2020/Amotchkina/ZnSe_nk.xlsx) | 400–13888.9 nm | 888–4201.7 nm | [0.4–0.888 µm](https://refractiveindex.info/?shelf=main&book=ZnSe&page=Amotchkina) |

以上表格中的零是**作者所提供的表值／模型值**：不是缺失值，也不是对真实 k 精确为零或低于特定检出限的证明。未在可核对资料中确认对应零值的检出限与误差时，应注明不确定，而非发明精度。ZnS 补充说明给出指数 k 模型，但工作簿后续节点有显式零值；不要悄悄用一个连续公式替换作者原表并声称仍为原表数据。表内两节点之间的插值是使用者的数值选择，不是新增实验点。

## 可追溯使用原则

1. **先锁样品再锁域。** 记录原始 n、k、单位、光谱域、样品形态、沉积／制备条件、来源与模型类型。优先使用同一来源、同一样品的完整 n/k 对；不要将不同样品的 n 与 k 无标识混拼，也不要把薄膜参数冒充块材或把不同玻璃牌号视为同一实测样本。
2. **把三类状态分开。** 作者明确零、来源未提供或超域、使用者为计算而假设零，必须分别标记。后者是条件性假设，不能被重标为作者测量值；缺域不因插值、拼表或外推而自动获得验证。
3. **核查波段与分辨率。** 逐段说明拟用区间落在数表域和论文表征域的哪里。稀疏表的插值、数值舍入、温度／批次、厚度及工艺差异应作为不确定性来源；不将模型节点密度当成测量光谱分辨率。
4. **敏感性而非虚假精度。** 对 k 很小或未知的区域，按来源约束报告有界假设和敏感性；不能因为模拟通过就倒推实际材料无损或实际工艺达标。

## 内透过率不是完整器件透过率

[SCHOTT N-BK7 资料表](https://media.schott.com/api/public/content/41e799d0bf874807a0bb8e702fbb75b5?v=54856406)给出不同厚度的**内部透过率** τᵢ；它不是含两表面反射的外部透过率。仅在样品均匀、适用 Beer–Lambert 衰减并把内损耗视为吸收等条件下，可按同一长度单位换算

`α = −ln(τᵢ)/d`，`k_ext = α λ/(4π)`。

这里 `k_ext` 为无量纲复折射率消光系数，不应与某些厂家以相同符号表示的单位长度吸收系数混淆。τᵢ 接近 1 时，表中舍入可显著影响推算的微小 k；若散射或其他内损耗不可忽略，推算结果也不能直接称为纯吸收。SCHOTT 的[技术说明](https://media.schott.com/api/public/content/110b56518128431b9f3134627d7f4c4e?v=613962ef)指出，标准资料表在 700 nm 以上仅有少数波长，并讨论约 1.45 µm 和 2.9–4.2 µm 的 OH 吸收；稀疏锚点插值不能保证重建这些特征。

## 低精度表与材料形态

[Querry 1987 报告](https://lweb.cfa.harvard.edu/HITRAN/HITRAN2012/Aerosols/papers/querry_minerals_1987.pdf)区分 CVD ZnS/ZnSe 块材与薄膜，并描述反射／透射与反演过程。[数据库的 ZnS 表](https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/master/database/data/main/ZnS/nk/Querry.yml)中 k 按三位小数列示，含 `0.000`；这类精度不能支持高精度微弱吸收或物理绝对零损耗结论。该块材不能不加说明地替代另一来源的薄膜。

可用来源、工作簿摘要和边界见[来源链接清单](sources.md)。上述资料仅可作为明确标注工艺、来源、模型和适用域的文献参考，不意味着软件已更新内置材料，也不代表实际器件材料经过独立测量或制造验证。
