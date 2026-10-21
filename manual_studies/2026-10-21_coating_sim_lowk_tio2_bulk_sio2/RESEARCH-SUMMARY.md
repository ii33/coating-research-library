# MgF2/TiO2 薄膜＋块材 SiO2：400–700 nm 宽带高反研究

日期：2026-10-21。代码只读基线：0a631b7428486ab08fe0f27aa8938c50783f5280。未修改或发布软件；旧 ZnS 和旧基准证据保留，不改写为新材料结果。

## 结论

在保留来源 n,k、块材熔融石英基底、400–700 nm、0°/30°各 s/p、每层10–500 nm、总厚<=5000 nm、层数<=32的条件下：

| 层数 | 独立稠密/极值审计最小 R | 最差位置 | 总厚 nm | 结论 |
|---|---:|---|---:|---|
|32|98.7354944%|402.505092 nm，30°p|2569.646687|通过，裕量0.73549个百分点|
|30|98.2672721%|401.499234 nm，30°p|2438.449547|通过，裕量0.26727个百分点|
|28|98.0591853%|407.499213 nm，30°p|2458.396123|通过，但裕量仅0.05919个百分点|
|26|97.5229052%|407.501105 nm，30°p|2244.734123|本轮失败，不是不可行性证明|

28层是本轮预先限定26/28/30/32比较中找到的最少合格层数，不是全局最少层数证明。层数更少不保证总厚更薄。30/32层有更大数值裕量；这些数值不包含制造误差、散射、膜应力、界面粗糙度或工艺偏差资格验证。

32层最差点 R/T/A=98.7354944%/1.1524933%/0.1120123%。28层最差点 R/T/A=98.0591853%/1.8565218%/0.0842929%。这些是谱线最小反射率，不是平均反射率。

## 材料与来源

所有原始文件钉住 refractiveindex.info 数据库 commit c5c2f188e848453def5970e347399d653df2ffc2，数据许可CC0-1.0，论文版权独立。完整链接、SHA256、来源表范围、工艺和k状态见 sources/lowk_tio2_source_provenance.json。

- H：Franta2015 TiO2，99.6 nm电子束蒸发膜，c-Si上，来源表述为amorphous (very fine polycrystalline)。不是把各向异性块材金红石当作各向同性薄膜。室温为表征信息，沉积温度未核实。作者拟合nk原样保留。400/550/700 nm处k分别7.15045e-4、1.44267e-7、5.02983e-10。原表范围0.114114–125.124 µm，不把整张模型表等同测量窗；本轮仅用400–700 nm。
  - 原始论文 https://doi.org/10.1117/12.2190104
  - 来源页 https://refractiveindex.info/?shelf=main&book=TiO2&page=Franta
- L：Franta2017 MgF2，134.2 nm电子束蒸发多晶膜，c-Si上；保留作者模型非零k。400/550/700 nm处k约1.52e-15、5.42e-18、1.76e-19。不能将这些模型尾部数值称为直接测得同等灵敏度的超低吸收，也不能称为实测零。原表范围0.0275043–125.141 µm，本轮仅用400–700 nm。
  - 原始论文 https://doi.org/10.1016/j.apsusc.2016.09.149
  - 来源页 https://refractiveindex.info/?shelf=main&book=MgF2&page=Franta
- S：Malitson1965块材熔融石英，20°C，n-only Sellmeier；原始适用范围0.21–3.71 µm。基底k=0是明确的透明半无限出射介质假设，不是来源给出的实测零，也不将薄膜SiO2重标为块材。没有背面反射或有限基底相干干涉。
  - 原始论文 https://doi.org/10.1364/JOSA.55.001205
  - 来源页 https://refractiveindex.info/?shelf=main&book=SiO2&page=Malitson

备选TiO2 Siefke和Zhukovsky的原始表仅用于来源对照，未替换本轮基线；其工艺不同。详见 sources/TiO2-film-visible-comparison.csv。

## 方法与可复现性

从两个重叠QW子堆栈的物理先验开始：32层8+8对，研究输入中心440/625 nm，参考相位角15°，不是从已知优化答案开始。初始谱线最小R约29.57%，所有32层厚度经解析梯度平滑minimax和SLSQP精确采样minimax优化，最后训练最小98.7418%，独立审计最小98.7355%。每nm训练，独立0.1nm及0.05nm错位网格并集、来源内插节点和全部括住的谱极值细化；另用现有生产求解器/冻结审计交叉验证。有限网格加极值细化不是区间证明，也不声称覆盖0°与30°之间的全部角度。

首次运行主程序5.83秒，其中优化4.63秒。新Python子进程冷重放（包括导入、材料加载、先验构造、梯度检查、优化与独立审计，不含来源下载）7.15秒。硬件/负载相关，不是软件耗时承诺。见 cold-replay-timing.json。

重要：440/625是这次研究的显式先验参数，不是已存在于软件中的通用生成器输出；禁止把这两个中心或最终处方硬编码为目标答案。通用停止带分块/连续中心参数化及解析梯度minimax最小集成方案见 SOFTWARE-HANDOFF.md，通用自动中心默认策略仍需无答案种子的生产验收。冻结答案seed成功只证明光学与格式可移植性。

## 审计与交付

- 32层完整首个通过证据冻结于 frozen-32layer-first-pass/，后续减层不覆盖它。
- review-production-frozen-request.json、review-production-optical-snapshot.json、review-production-candidate-design.json是可离线解析的生产冻结请求/材料快照/32层设计；不依赖修改活动材料库。
- review-production-frozen-audit.json：现有生产审计32层通过，最小R=0.9873549442083828，402.505092514nm/30°p；24754个唯一条件点，36/36极值细化，753次物理求值。独立矩阵与生产稠密谱最大|ΔR|1.36e-14。只对未知k的Malitson基底应用显式k=0，已知薄膜k不变、禁止外推。
- layers-{32,30,28,26}-incident-to-substrate.csv提供全部厚度。生产front_layers顺序相反，必须同时反转材料与厚度；详见 review-PORTABILITY-PLAN.md。
- 精确研究候选：32 retained-best.json；30 candidate-B-economy30_two_stack.json；28 lowest-qualified.json；26 candidate-B-economy26_two_stack.json。
- 减层独立审计：audit-B-economy30_two_stack.json、audit-B-economy28_linear_chirp.json、audit-B-best-26layers.json。

没有把旧材料已知k归零，未伪称直接测得超低吸收，未使用平均R替代最低R，未向软件仓库发布。换材料同时改变n、k及优化处方，因此不能把新旧性能差异全部归结于某一个k的改变。

28/30层另经现有生产冻结审计均通过：分别0.9805918532201829和0.9826727210906502；各31/31极值细化。层数专用文件为 review-production-{28,30,32}layer-{candidate-design,frozen-request,optical-snapshot,frozen-audit}.json。与独立矩阵最大|ΔR|<=1.50e-14。
