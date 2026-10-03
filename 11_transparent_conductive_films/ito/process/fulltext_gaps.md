# ITO蒸镀第一版：精确全文缺口与不可由文献填补的参数

更新：2026-10-03。当前已有6篇可用原始研究全文支撑阶段一；下列缺口不阻断当前报告。没有付费、绕过限制或联系作者索取。Undermind的PDF X仅作入口状态，已另查出版社/官方机构库。

## 优先级高

### ITO-P09：源料非一致蒸发与电阻热蒸发

- S.-W. Jan、S.-C. Lee，1987，Preparation and Characterization of Indium-Tin-Oxide Deposited by Direct Thermal Evaporation of Metal Indium and Tin，Journal of The Electrochemical Society 134(8):2056–2061
- 正确原始论文DOI：[10.1149/1.2100819](https://doi.org/10.1149/1.2100819)
- 已查：[台大机构库](https://scholars.lib.ntu.edu.tw/entities/publication/139b88db-b09b-48e0-8451-d900a08ea417)只有书目/摘要，DOI入口本次读取失败；未获原始PDF
- 需要全文回答：摘要Sn:In=3:1金属质量比如何设定；投料质量、Mo舟/源温、基片温度/距离、氧分压、初始与末期蒸气组成、膜中Sn/In实测及只蒸发少量源料的量化范围
- 防误引：10.1002/CHIN.198748384为ChemInform摘要条目，不替代ECS原论文；机构摘要的ρ数学式丢失，不从二手资料补写成该摘要直接证据

### ITO-P10：PIAD室温成膜基准

- S. Laux、N. Kaiser、A. Zöller、R. Götzelmann、H. Lauth、H. Bernitzki，1998，Room-temperature deposition of indium tin oxide thin films with plasma ion-assisted evaporation，Thin Solid Films 335(1–2):1–5
- DOI：[10.1016/S0040-6090(98)00861-X](https://doi.org/10.1016/S0040-6090(98)00861-X)
- 已查：[ScienceDirect出版社页](https://www.sciencedirect.com/science/article/abs/pii/S004060909800861X)可取得摘要；限定题名/DOI/PDF及Fraunhofer机构检索未找到可读完整原文，Undermind无PDF
- 需要全文回答：APS源电压/电流/实际平均能量、O₂分压和活化份额、蒸发速率、源料成分、基片实测温升、ρ/吸收/Drude参数配对与误差
- 目前仅可使用：摘要的室温、300nm、ρ=5×10⁻⁶ Ωm、550nm吸收<5%；没有权利和完整条件依据，不保存/发布原文

### ITO-P11：低温PIAD和光学—电学桥接

- Kevin Füchsel、Ulrike Schulz、Norbert Kaiser、Andreas Tünnermann，2008，Low temperature deposition of indium tin oxide films by plasma ion-assisted evaporation，Applied Optics 47:C297–C302
- DOI：[10.1364/AO.47.00C297](https://doi.org/10.1364/AO.47.00C297)
- 已查：[Optica出版社页](https://opg.optica.org/ao/abstract.cfm?uri=ao-47-13-c297)明确Not Accessible/无订阅；[Fraunhofer PUBLICA记录](https://publica.fraunhofer.de/entities/publication/2216f467-aa66-4551-9422-80a233a1ece2)打开为bot检查页；Undermind无PDF
- [Fraunhofer官方2008年报pp.74–75](https://www.iof.fraunhofer.de/content/dam/iof/en/documents/publications/annual-report/2008/iof_jahresbericht_2008_10_fuechsel.pdf)完整可读，直接援引该期刊文章，但只有概述，不能冒充论文全文
- 需要全文回答：平均离子能量和混合气体、真实Ts<100°C窗口、Drude电阻率与四探针偏差、模型频段、结构/厚度/热历史、重复性

## 优先级中

### ITO-P12：离子能量扫描

- J. W. Bae等，Effects of oxygen ion beam plasma conditions on the properties of Indium tin oxide thin films，Vacuum 56(1):77–81 (2000)
- DOI：[10.1016/S0042-207X(99)00169-4](https://doi.org/10.1016/S0042-207X(99)00169-4)
- [SKKU机构页](https://pure.skku.edu/en/publications/effects-of-oxygen-ion-beam-plasma-conditions-on-the-properties-of/)验证题名/作者/DOI/摘要；未取得完整PDF
- 需要：900 V的电极/栅级定义、离子到片能谱/流密、蒸发速率、厚度与能量效应和氧供给效应的解耦。摘要900 V不能直接成为本模型的900 eV单能束边界

### ITO-P13：Sn价态、气氛与离子照射

- Mika Yamaguchi等，Characteristics of indium tin oxide thin films prepared using electron beam evaporation，Thin Solid Films 447–448:115–118 (2004)
- DOI：[10.1016/j.tsf.2003.09.033](https://doi.org/10.1016/j.tsf.2003.09.033)
- [出版社](https://www.sciencedirect.com/science/article/abs/pii/S004060900301304X)仅公开摘要、方法/结论片段，Undermind无PDF
- 需要：完整实验表、基片温度、ECR源条件、氧/氩压力扫描、总Sn/In与Sn⁴⁺占比的不同定义、XPS拟合/校正和表面—体相差别

## 已读全文中必须核实的疑点

1. Korneluk2023，DOI10.1038/s41598-023-45651-w：Methods的底压5×10⁻⁵ Torr与“压力升至2×10⁻⁵ Torr”冲突。需要勘误或原始设备日志，不能改写指数。当前保留精确原值，工压/氧分压不作校准输入
2. Far文章，DOI10.31185/jwsm.180：正文2012与线上2022年份、氧化物/金属源、Table1与摘要ρ数值、ρ=Rs·d不一致。隔离出定量模型，不选择其中任一数值充当纠正
3. Berkeley热蒸发报告：摘要pO₂=0.32mTorr、Table1=0.25mTorr，ρ与两种厚度的对应关系不明确；保留C级工程线索
4. Kojima2012：Table1未明示源SnO₂ wt%；“不预热”系列的真实末端Ts未给；不要从邻图/其他样品补齐

## 实测才能补齐的工程缺口

- 原料批次/纯度、源面温度/束斑/装料量/消耗比例、预蒸与复用历史
- 片位温度随时间、压力计气种修正、实际氧分压与有效抽速、残余水及氢
- 分时/深度膜Sn/In/O、In/Sn氧化态和活性缺陷；避免将单个O1s分峰直接当氧空位计数
- 到片离子物种、f(E)、j_i(x,t)、活性中性氧、能量与粒子剂量
- 厚度工具因子与误差、Hall几何/接触、T/R基底归一化、雾度、应力/附着和空气稳定性

## 包内边界

本目录JSON/CSV为固化证据数据，无须运行生成器。唯一合法本地原件是CC BY 4.0的Korneluk PDF，SHA-256已登记；父任务发布包须排除全部`sources/originals/`。本版不含依赖原件的用户复算入口，数据复核可以直接读取CSV并用ρ=Rs·d与ρ≈1/(e n μ)检查，不能把原始图中的估读点升级为精确测量。
