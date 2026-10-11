# TFCalc 针插与隧穿的公开方法及项目落地路线

检索与复核日期：2026-10-11 UTC。范围是云端公开文献研究、现有实现状态对照与小型独立数值复算；本轮没有修改产品代码、安装 TFCalc、访问专有源码或运行付费服务。

## 结论

建议把“针插 + 生长层逃逸 + 局部精修”作为联合合成主线，先做可验证的单针和单层生长，再扩多针。TFCalc 已公开的是操作流程和功能边界，尚不足以原样复刻内部选址、选层、步长或隧穿评分。

- **TFCalc 的插入种子是零厚度层。** 在选定位置加层后，由 Gradient 或 Variable Metric 局部优化让它长出。程序可找不到可长的针；此时的“optimal”只是针插/局部精修意义下的局部终点。[产品方针法说明](https://www.hulinks.co.jp/en/tfcalc/special-features/needle-optimization/)
- **TFCalc 的 tunneling 是生长已有层以换谷。** 到达一个针插局部终点后，尝试另一目标函数谷底，局部精修，再做针插。公开文字没有提供目标变换公式。不能把差分进化、模拟退火或普通随机重启叫作 TFCalc 隧穿。[产品方针插与隧穿说明](https://www.hulinks.co.jp/en/tfcalc/special-features/needle-tunneling/)
- **最新 Windows 项目仍是有限厚度界面试插。** 已有实际 Python API 和测试，但经典零厚度敏感度、tunneling 及二者组合尚未实现，GUI 不能提交这类任务。见第 4 节的证据范围。
- **隧穿启动门限不等于硬厚度约束。** 官方示例设 10000 nm 隧穿启动门限，公开最终层表合计却为 10263.39 nm。独立复算其谱结果约为 max R=0.898%。本项目若承诺总厚度不超标，应显式约束并独立回证，不能只模仿这一启动门限。

## 1 证据如何使用

以下将三类内容分开：① TFCalc 产品方明确公开；② 经典作者论文或教材公开的一般方法；③ 本报告原创推导、实验设计与实现建议。第二类不能证明 TFCalc 内部采用同样的公式，第三类也不代表产品已实现。

- Hulinks 是 TFCalc 当前所有方；旧 Software Spectra 官网公告其于 2022-06-17 转让。Hulinks 当前产品页列最新版本 3.6.2。本轮逐页阅读相关 HTML，不将旧 3.4/3.5.15 手册当成当前版本完整规格。[旧官网公告](https://www.sspectra.com/)，[当前产品页](https://www.hulinks.co.jp/en/tfcalc/)
- Software Spectra 原版 **Mac 3.4** 手册由俄勒冈州立大学机构镜像托管，版权页署名原厂；相关 Section 2 pp.36–38、43–44、Appendix B pp.61–62 已逐页核读。手册页面编号不同于 PDF 索引，第 61 页是 PDF 第 71 页。[原厂手册机构镜像](https://sites.science.oregonstate.edu/~tatej/TateLabWiki/lib/exe/fetch.php?media=manuals%3Atfcalc_manual.pdf)
- 原厂 **Windows 3.5.15** 官方 URL 本次直接打开返回 404；其 pp.51–52、68–69 等只能核搜索索引的页码摘录，不宣称 PDF 全文已读。[Windows 手册原 URL](https://www.sspectra.com/files/win_demo/manual.pdf)
- 1982 原论文、1992 作者教材和 1996/2007 作者上传论文的阅读范围与定位列在第 8 节。Optica 出版方能核书目/摘要，收费正文未被绕过；作者主动上传的原论文副本与期刊正式版的托管来源分别注明。

## 2 TFCalc 公开行为与未知内部实现

### 2.1 针插与精修

公开参数包括材料候选、逐层是否允许针插、重复到无可长新层、同时加多根零厚层、先局部优化再加针，以及手动停止后的恢复。Mac 3.4 Appendix B p.61 给出至少 2、最多 8 种针材料；已有层可用其它材料。不能与 Simplex、group 或 sensitivity optimization 联合。很薄残留层可置零、Consolidate，再关闭针法精修。这些是公开操作契约，不能推出内部用解析零厚导数还是有限差分来找位置。[原厂手册相关页](https://sites.science.oregonstate.edu/~tatej/TateLabWiki/lib/exe/fetch.php?media=manuals%3Atfcalc_manual.pdf)

3.0 明确最佳针值并列位置都可插，多材料“add many”同位置仅取最佳材料，并修正非正入射平均偏振问题；该文还说明厚度上下界兼容针法但不推荐这种组合。[3.0 变更的 Needle Optimization 和 Optimization 节](https://www.hulinks.co.jp/en/tfcalc/30-changes/)

### 2.2 隧穿与循环

公开状态顺序可以写为：当前设计 → 局部精修 → 针插及再次精修 → 针插局部终点 → 保存候选 → 若仍未达标且允许生长则尝试生长层换谷 → 新谷局部精修 → 再针插。原厂手册称会考察可能的 tunnel 并按某种意义挑较好者，同时明确没有通用规则说明长哪一层。没有披露：候选 tunnel 的数学定义、评分、扫描范围、步长、临时目标重标定或是否使用专门的 transformed objective。

以下沿革支持联合流程，但不证明历代内部实现不变：

| 版本 | 本轮可核的公开变化 | 一级来源定位 |
|---|---|---|
| 2.9 与 2.9.6 | 引入针法；后续列针法改进 | [2.9 变更](https://www.hulinks.co.jp/en/tfcalc/29-changes/) |
| 3.0 | 8 材料、并列位置、多针同位冲突和平均偏振修正 | [Needle Optimization 节](https://www.hulinks.co.jp/en/tfcalc/30-changes/) |
| 3.1 | tunneling 扩展针法，生成总厚度递增的局部最优设计序列 | [Automatic Synthesis 节](https://www.hulinks.co.jp/en/tfcalc/31-changes/) |
| 3.2 | 修“不能决定长哪层”的失败；连续目标贯通 local、needle、tunnel | [Optimization 节](https://www.hulinks.co.jp/en/tfcalc/32-changes/) |
| 3.3 | 可在当前局部精修结束后延迟退出 | [Delayed quit 节](https://www.hulinks.co.jp/en/tfcalc/33-changes/) |
| 3.4 | 背面层也可针插与隧穿；逐层许可；先优化再针插 | [Optimization 节](https://www.hulinks.co.jp/en/tfcalc/34-changes/) |

### 2.3 目标 约束 停止

公开目标支持不同波长、角度、P/S/平均偏振、多环境、等式或不等式。merit 由归一化偏差与 tolerance 缩放，幂可选 1、2、4、8、16、Max；大幂偏重大偏差，Max 只配 Simplex，故不能将其直接套到针法。连续目标会转为内部采样，公开资料没有足够细节复刻自动网格。[优化总览](https://www.hulinks.co.jp/en/tfcalc/special-features/optimization-overview/)，[3.2 连续目标](https://www.hulinks.co.jp/en/tfcalc/32-changes/)，[原厂手册 pp.36–38](https://sites.science.oregonstate.edu/~tatej/TateLabWiki/lib/exe/fetch.php?media=manuals%3Atfcalc_manual.pdf)

手册 p.44 的 tunneling 触发需同时满足：开启 Grow、当前总厚度低于设定值、当前 deviation 高于设定值；可保存每个针插终点。Appendix B p.62 说明所有不等式达成时停止。零厚层停止优化开关与工艺最小厚度删层不是同一功能；停止时的局部目标值也不是全局最优或连续谱达标证明。[原厂手册参数与 Appendix B](https://sites.science.oregonstate.edu/~tatej/TateLabWiki/lib/exe/fetch.php?media=manuals%3Atfcalc_manual.pdf)

## 3 经典公开针法怎样复现

### 3.1 一阶结构敏感度

1992 作者教材在无吸收、正入射、二材料的最简设定下定义宿主折射率 n(z)、新针折射率 n̂，并得到：

δF = P(ẑ) [n̂² − n²(ẑ)] Δz + 高阶项。

P 由前向导纳与反向伴随方程构造；低指数中换高指数要 P<0，高指数中换低指数要 P>0。此处是固定位置小段“替换”变分，有限宽度必须实际复算。公式符号已同时核提取文本和 p.121 渲染页。教材循环包括针变分、厚度精修和薄层降维，删层可能抬高目标值。[作者教材 §2.2，pp.115–127，式 2.2.17–2.2.22](https://optilayer.com/content/book_Furm_Tikh.pdf)

1996 原论文用 ΔF=P₁(z,n)d+P₂(z,n)d²+…，在预选材料和层内位置中寻找负的一阶插入系数，可单针或多针，然后厚度精修。其 P(z)=min材料 P₁ 的符号定义不能和教材伴随 P 混用。论文明说没有严格全局收敛证明。[1996 正式书目与摘要](https://opg.optica.org/ao/abstract.cfm?uri=ao-35-28-5493)，[作者上传原论文 §2 pp.5494–5495，结论 p.5506](https://www.researchgate.net/publication/49654448_Application_of_the_needle_optimization_technique_to_the_design_of_optical_coatings)

2007 的 gradual evolution 每轮强制增加总光学厚度，再以针优化补偿目标变差，保留不同层数/厚度的设计；它是可公开参考的另一策略，不应命名为 TFCalc 的已核实隧穿内部实现。[2007 正式书目](https://opg.optica.org/ao/abstract.cfm?uri=ao-46-5-704)，[作者上传原论文 §2 pp.704–707](https://www.researchgate.net/publication/6525952_Optical_coating_design_approaches_based_on_the_needle_optimization_technique)

补充：数值选址本身并不排除“needle”名称。Sullivan 与 Dobrowolski 的 1996 原始论文摘要明确介绍以数值方式代替解析选址的变体，支持一根或多根针。当前项目与成熟经典方法的差距是搜索范围、连续层内结构敏感度、循环与工程回证，而不能仅以“数值”二字判定。本文只读该文出版方摘要，未取得其正文公式。[原始论文摘要 Applied Optics 35,5484–5492](https://opg.optica.org/ao/abstract.cfm?uri=ao-35-28-5484)

### 3.2 本报告独立推导的实现接口

对项目现有稳定正演和目标函数，可定义 g(m,z)=∂F/∂w|w=0+，只沿非负新层厚度计算单侧方向。

1. 将宿主 h 分为同材左段、零厚候选 m、同材右段。零厚候选两界面必须数值上抵消，F(0) 等于原设计。
2. 由候选传播矩阵的厚度切线，经 prefix/suffix 或稳定 S 合成，得到 ∂r/∂w、∂t/∂w；例如 ∂R/∂w=2 Re(conj(r)∂r/∂w)。再按同一目标权重/不等式激活逻辑合成 g。不能把对波长的导数目标当成插针导数。
3. 先扫描允许层内位置和材料，再细化负谷。w=0 时位置移动不改变光谱，位置梯度本身为零；仅把位置丢给常规厚度精修器无法代替结构选址。
4. 在 enlarged topology 上检查新针列 Jacobian 和原宿主列，临时变量采用固定正长度尺度，不能以零厚种子作尺度。此为新接口设计要求，不是在断言今日 Windows 代码已有该缺陷。

**add 与 replace 不同。** 令原宿主厚度 d、位置比例 f：

- add：左 fd、针 w、右 (1−f)d，物理厚度增加 w。
- 对称 replace：左 fd−w/2、针 w、右 (1−f)d−w/2，物理厚度不变。

在 w=0，两个同材段的厚度梯度都等于原宿主 g_h，所以 g_replace = g_add − g_h。只有该宿主为无活动约束的厚度驻点、g_h≈0，两动作才一阶近似一致。在盒界、固定总厚度或未精修起点，它们不应混评分。这是链式法则的原创推导，可作为单元测试，不是 TFCalc 已公开公式。

## 4 项目现状对照

### 4.1 2026 年 10 月 11 日 Windows 实现

来源是当日 Windows 只读复核回执；本轮云端未直接重新读取该 Windows 源码。项目尚无对应提交版本，未取得精确内容哈希数值。回执说核心源码与当日验收版哈希一致，不能据此虚构 commit。

| 项目 | 已核回执内容 | 证据定位 |
|---|---|---|
| 当前针插服务 | 有限厚度界面试插 + 局部精修；仅原指标严格改善才接受；零厚度经典敏感度未实现 | `coat_sim/core/film_optimization_needle.py:616` |
| 针插专门测试 | 原 6 项 + 新 7 项边界通过；74 是整体优化断言总数 | `tests/test_film_optimization_needle.py`；验收见下 |
| 成功例 | 550 nm、正入射非偏振 R 的正演合成目标，成功插 20 nm 层、归一化误差为 0 | `tests/test_film_optimization_needle.py:95` |
| 异常回退 | 注入异常下 2 次试插失败/总 3 次评估；是恢复测试 | 同测试文件；不是宽带工程达标反例 |
| 可调用入口 | Python 核心 API；GUI 只有说明按钮，队列不能提交，未有专用 MCP/CLI | `FilmOptimizationWindow.qml:789` |
| 联合算法 | tunneling 和 needle+tunneling 尚无实现 | 同日只读复核回执 |
| 对外说明 | 称项目启发式、性能未外部验证；未直写“实验性” | `docs/algorithms.html:2394` |

验收证据相对路径：`artifacts/film-optimization/takeover-final-20261011T143159Z-4cbc60f4/FINAL_ACCEPTANCE.md`。不附用户电脑绝对路径或私有任务链接。

解析 Jacobian + TRF/L-BFGS-B 可作为固定结构精修基础；单侧厚度导数正确、多起点或 DE 的可运行性，都不能单独证明结构敏感度、换谷或宽带制造约束已经成熟。尤其“误差 0”的单波长构造例，只证明该构造的 API 路径。

### 4.2 旧 T08 研究参考

本轮直接读过旧 T08 的 `models/optimization_core.py`、`models/run_benchmarks.py`、拓扑测试与 `data/benchmark_results.json`。它枚举 2 宿主×3 位置×add/replace，用 ε=10⁻⁶ µm 的有限差斜率及 30/100 nm 回算，再做约束精修；不是今天 Windows 服务。

旧 B01 插层候选回证未被接受：原结构留出 cost=0.03726527，插层精修后=0.04156061；因此保存原设计是合理行为。旧 B03 在限定评估预算中失败，不能转写成“今天的 needle 失败”。这些旧例仅用于组织失败基准和预算记账。

## 5 有限阶段落地路线

下面是研究建议，不是本轮实施结果。初版只承诺冻结材料/目标/约束和有限预算下的可重复候选；不给全局最优或商业软件等效性保证。

### 第一阶段 补齐结构导数与单针生长

- 冻结层序、材料 n/k、角度偏振、波长权重、目标尺度、允许宿主、制造厚度和层数上限。先以二材料、无吸收、正入射回归，再扩当前核已验证的吸收与斜入射范围。
- 实现上节 g(m,z)，先每个允许宿主做有限位置网格并括区细化；输出已覆盖位置和未覆盖范围。找不到负 g 只能说“本次扫描无下降候选”。
- 新针起于 0，已有层与新层联合有界精修；结构变化后重置 quasi-Newton 历史。若库在零厚边界作内部扰动，要记录实际起点与单侧导数。
- 每个候选需真实模型接受，独立网格审计，失败回滚。暂不多针并行，避免同时生长的交叉高阶项掩盖错误。
- 验收：零厚等谱、新针导数、多位置覆盖、单针实际改善、无可行针和回滚均有可复算证据。

### 第二阶段 加单层生长逃逸并串联针插

采用明确命名的“公开流程启发的生长层逃逸”，不要声称复制 TFCalc 专有 tunneling。

- 在一个已精修且单针搜索不能改进的候选上，保存当前和历史最佳解。
- 按合法已有层逐个生成有限正厚度增长候选，在有界增长区间做一维采样和括区搜索。可用参考波长的相位厚度定尺度，但具体区间/采样数写入协议；不能让默认参数假冒原厂算法。
- 允许试探路径暂时高于原目标，否则无法越过局部障碍；对路径候选做局部精修，并用原目标、同一约束、同一审计网格比较终点。小扰动若精修回原谷，要报告重复谷，不说成功隧穿。
- 新谷终点经验证后再做单针循环；保存每轮 F、层数、物理与光学厚度、增长层、增长量、预算及退出原因。未改善时保持历史最好解和明确失败记录。
- 验收必须同时出现：从针插停点到另一有效候选、回同谷的失败、硬 Dmax 阻止增长、目标达成停止，以及失败后原解完整保留。

这和“换个随机起点再跑”不同：逃逸候选明确从当前局部解的层生长路径产生，联合流程也要显示随后针插的贡献。若以后采用数学 transformed tunneling objective，应另立方法名、公式来源与验证，不能称该公式为 TFCalc 已披露实现。

### 第三阶段 制造化清理与多针

- 工艺下限是离散条件：层不存在，或 d≥dmin。允许新针暂时 0≤d<dmin 是合成松弛；最终必须在“删层”和“保留且约束长到 dmin”两分支中回证。对裂开的宿主两段也要检查，不能只检查新针。
- 删除零层、只合并完全同材同模型且无独立界面效应的相邻层，再精修；删异材薄层、舍入厚度或改变材料都重算光谱与约束。清理可使 F 变差，应保存前后权衡。
- 单针通过后，比较逐针重算与批量多针；每批数量、最小位置间隔、同位置冲突和并列处理写清。有限批量总变化不保证等于各个负导数的相加。
- 多起点与 DE 留作独立对照，不混入 tunneling 名称。多环境/偏振/鲁棒情景应使用同一冻结目标和真实预算。

## 6 验证基准与反例

| 基准 | 想证伪的问题 | 最小验收证据 |
|---|---|---|
| 零厚针与宿主同材针 | 人造界面未抵消、层序或振幅约定错 | R/T/A 等谱；同材 add 等于宿主增厚，replace 等于原谱 |
| 单侧 g 与差分步长序列 | 错符号、单位或灾难性消差 | 用一组递减正 h 对 [F(h)−F(0)]/h，比 g 的误差下降区；另核幅度导数 |
| add/replace 链式关系 | 把不同物理动作混为一谈 | g_replace≈g_add−g_h；含宿主活动下界和未精修起点 |
| 连续层内位置 | 只枚举界面漏有效候选 | 存在界面皆无改善而内点 g<0 的冻结反例；位置网格细化可重现 |
| P/S/平均与多角度 | 错误平均或偏振导数 | 分别对 R_s、R_p 和加权平均的 g 对照；不要平均振幅 |
| 宽度反转 | 负微分不能保证有限 20/30/100 nm 改善 | 至少一例小 h 下降、大 h 上升；记录实际接受门 |
| 无针可用/耗尽预算 | 把局部停止写成全局完成 | 明确 no_candidate/budget/user_stop 与 specification_met 分开 |
| 生长回原谷 | 普通厚度扰动被误称成功换谷 | polished 厚度/结构/谱重复检查及失败状态 |
| 生长跨谷后再针插 | 两步只是名义串联 | 记录生长前、精修后、针后各 F 和调用量；做 needle-only/growth-only 联合消融 |
| dmin、Dmax、Lmax | 生长或裂层绕过约束 | 不可行初态、剩余厚度为0、裂宿主太薄、候选超层数；外部复算违例为0 |
| 薄层删除与合并 | 清理后光谱悄悄恶化 | 前后独立网格、公差情景及降层代价；失败回滚 |
| 窄带/粗网格伪合格 | 训练点遗漏峰或角度失效 | 留出细网格与额外角度，报告最坏采样违例位置；不冒称连续上界 |
| 异常/取消/恢复 | 中途失败污染当前设计 | 失败候选隔离、原解哈希保持、恢复前重新精修、计数不重置掩盖成本 |

比较路径：固定拓扑 TRF/L-BFGS-B、多起点/DE、现有有限试插、经典单针、单针+生长逃逸。相同主 nfev 不等于相同成本；记录正演次数、Jacobian 次数、候选次数、局部精修总调用量、波长×角度×偏振×层工作代理及墙钟。限定阶段预算应事先写入，不能失败后无限加预算直到看起来成功。

教学基准合格后才进入材料实测 n/k、厚度公差、工艺可沉积性和设备验证；任何合成测试都不能替代这些。

## 7 官方 Ge 宽带 AR 示例的独立复算

官方示例使用空气、Ge 基底 n=4.0，膜料 H=4.2、L=2.2；目标 7700–12300 nm 的 R<1%。网页用 R<0.9% 和 power=16 留清理余量，最初 L 单层约 2300 nm，针插/隧穿得到 15 层，再删一个很薄内层并重新精修得到公开 13 层。[官方示例完整参数与最终层表](https://www.hulinks.co.jp/en/tfcalc/examples/list-of-coating-design/growing-antireflection/)

本目录 `reproduce_official_ar.py` 用独立正常入射 Airy 递推复算最终表，依赖 Python/NumPy，不用产品软件或项目光学内核。运行：

```bash
OPENBLAS_NUM_THREADS=1 python reproduce_official_ar.py
```

结果在 `official_ar_reproduction.json`：

- 13 层总物理厚度 10263.39 nm，比网页所设 10000 nm 隧穿启动门限高 263.39 nm。
- 20001 个等间距点，最大采样 R=0.00897930613，即 0.897930613%；位于 11369.19 nm。
- 波长积分平均 R=0.00801023721；裸 Ge 和任意零厚中间层控制 R=0.36。

这只核最终层表和示范材料假设。没有复现 TFCalc 的合成路径、选层策略、15→13 层清理过程或运行时间。稠密采样仍不是连续谱严格上界，常数无吸收 n 也不是材料实测。门限超出是表上可复算事实；其产生原因与内部最大厚度语义并未进一步披露，应避免猜测。

## 8 原始文献与阅读记录

检索日期统一为 2026-10-11 UTC；官方网页已在正文具体链接。文献最小定位如下：

1. Tikhonravov，1982，*A Method of Synthesis of Optical Coverings Which Uses the Necessary Optimality Conditions*，Moscow University Physics Bulletin 37(6),108–110。必要条件与点变分在刊页109，构造建议109–110。[MSU 官方条目](https://vmu.phys.msu.ru/en/abstract/1982/6/82-6-91/)，[原始 PDF](https://vmu.phys.msu.ru/file/1982/6/en-82-37-6-108.pdf)。本轮文献核查读取三页原文；主报告复核环境对同 URL 返回不可访问，因此不以个人全页二次读取作保证。
2. Furman 与 Tikhonravov，1992，*Basics of Optics of Multilayer Systems*，§2.2.1–2.2.3，pp.115–127；本轮逐页读取相关节，主报告亲核公式、正文与 p.121 渲染；没有声称整本全读。[作者方公开 PDF](https://optilayer.com/content/book_Furm_Tikh.pdf)
3. Tikhonravov、Trubetskov、DeBell，1996，Applied Optics 35,5493–5508，DOI 10.1364/AO.35.005493。出版方仅书目/摘要；作者上传原论文相关 §2 和结论已阅读全文摘录核对，不复制其图文。[出版方](https://opg.optica.org/ao/abstract.cfm?uri=ao-35-28-5493)，[作者原文副本](https://www.researchgate.net/publication/49654448_Application_of_the_needle_optimization_technique_to_the_design_of_optical_coatings)
4. Tikhonravov、Trubetskov、DeBell，2007，Applied Optics 46,704–710，DOI 10.1364/AO.46.000704。出版方仅书目/摘要；作者上传原论文 §2 的渐进生长与清理相关全文已核读。其总光学厚度不能和物理总厚度互换。[出版方](https://opg.optica.org/ao/abstract.cfm?uri=ao-46-5-704)，[作者原文副本](https://www.researchgate.net/publication/6525952_Optical_coating_design_approaches_based_on_the_needle_optimization_technique)
5. 原厂手册引用的 Tikhonravov 1993，Applied Optics 32,5417–5426，DOI 10.1364/AO.32.005417；本轮只核摘要和书目，不能据此称读过其完整针法证明。[出版方](https://opg.optica.org/ao/abstract.cfm?uri=ao-32-28-5417)
6. Baskakov–Tikhonravov 1984、Sveshnikov 等 1986 与 1987 章节，本轮仅从作者教材书目核得，未取得原文；没有据其题名补造算法步骤。

公开包只需本报告、独立复算脚本和结果，以及来源/内容哈希清单。第三方原 PDF、提取文本和截图不随研究成果再分发；无 GPL 源码引入。研究库同步是研究交付，不是软件仓库发布。
