# coating-sim 敏感性/稳健优化研究建议

调研日期：2026-10-23。本文为研究与实施建议。来源限原始论文、作者/研究机构存档与厂商技术文档。文中“建议/推导”不是文献中已经验证的项目成果。

## 1. 最重要的结论

1. 当前不能把“训练 worst 下降 77.88%”称为制造稳健性改善。已有独立场景 pass 6/16→4/16、系统误差 1/16→1/16，且 nominal 在细网格不合格，恰好暴露目标不一致、训练场景过拟合和规格采样不足。16 个样本也不足以判断良率差异是否真实。
2. 第一优先级不是加 margin，而是把原始规格逐条保留为 nominal 硬约束；先修复细网格原规格可行性，再在可行域内优化制造误差下的尾部损失。输入原指标中已有的 margin 必须原样保留，不叠加隐形 safety margin。
3. 误差不能只有 ±0.2% 独立均匀分布。应区分：独立终止误差、绝对 nm 项、按材料共模的晶控校准偏差、逐层漂移、空间通量非均匀、n/k 与真空到空气变化；有光学监控时另建“顺序反馈/自补偿”模型，不能简单假定所有相关性都有害。
4. 可落地算法是“非线性场景云 + 全层解析 Jacobian + 显式 nominal 约束 + CVaR 或 epigraph minimax + 独立验收”。薄膜实物文献支持场景云/解析导数路线；CVaR 和 constraint exchange 是本项目的通用优化迁移，不应写成已有该 89 层/该蒸发工艺的实证。
5. 固定材料/层数、局部优化、有限样本均不能保证全局可行或保证真实生产良率。若较大误差下所有可行候选良率都低，应报告此边界，不能改验收指标来制造改善。

## 2. 原始方法证据与适用边界

### A. 最坏情形与良率不是同一个目标

Birge, Kärtner & Nohadani, *Improving thin-film manufacturing yield with robust optimization*, Applied Optics 50, C36–C40 (2011), DOI 10.1364/AO.50.000C36。[开放全文，DESY 机构存档](https://bib-pubdb1.desy.de/record/97205/files/32DE6A27-C2C7-A869-C92E4A7D3539AB91_206412.pdf)。

原文 pp. C37–C40：先在有界误差集合内做局部内层 ascent 找坏场景，再向避开这些场景的方向更新；最后沿 robust→nominal 优化轨迹，以固定验收 cutoff 搜最高 Monte Carlo yield。作者明确指出，最坏 merit/方差改善不必然改善 yield，极少见尖峰会迫使 nominal 过度退化。21 层 AR 数值例中，2.5 nm RMS 误差、平均 R≤1% cutoff 下，yield 从 36% 到 74%；作者把实物制造验证列为后续必要工作。本文也不支持直接照搬其人为去除 DC/限制 Fourier 相关误差的假设到项目实际蒸发工艺。

本项目推论：保持“原规格是否全部合格”的 joint pass/yield 为最终指标；worst、RMS、Jacobian 范数只能是优化代理或诊断。可尝试用原规格可行候选间的短轨迹做 yield 筛选，但不能允许路径上的 nominal 失败方案成为最终推荐。

### B. 非线性场景云有真实薄膜制造对照

Pervak, Trubetskov & Tikhonravov, *Robust synthesis of dispersive mirrors*, Optics Express 19, 2371–2380 (2011), DOI 10.1364/OE.19.002371。[作者机构开放全文](https://attoworld.de/fileadmin/user_upload/tx_attoworld/publications/paper_OptExpr_Y2011_M01_D31_V19_P2371.pdf)。

方法：同时优化 pivotal design 邻域的 design cloud，而不是只惩罚一阶敏感度；绝对和相对 Gaussian 厚度误差相加，支持解析 gradient/Hessian。文中实例用 50 场景、σ_abs=0.5 nm、σ_rel=0；实验为 Helios 磁控溅射、690–890 nm 高色散镜，对照 conventional 与 robust 设计，robust 第二次独立镀膜亦得到可接受 GDD。作者也承认真实制造扰动不全包含在简化误差模型中。

边界：该文支持场景云思想与实际制造价值，不支持把磁控 0.5 nm 精度作为 ZnS/氟化物蒸发默认值；其完整 synthesis 可改层结构，不能等同于固定 89 层局部微调能力。

### C. 全局层交互与顺序再优化有价值，但 PCE 不宜第一版全维移植

Poitras & Ma, *Surrogate sensitivity analysis of facet optical coatings produced without and with in situ design reoptimization*, Scientific Reports 15, 5692 (2025), DOI 10.1038/s41598-025-89625-6。[期刊全文](https://www.nature.com/articles/s41598-025-89625-6)，[加拿大 NRC 存档页](https://nrc-publications.canada.ca/eng/view/object/?id=a9867a0a-07b0-4c40-bafe-709512c4e41f)。

作者用 PCE 代理、Sobol 一阶/总阶/交互指标分析 facet AR，并模拟逐层完成后再优化剩余层。其误差假设为 Gaussian σ=min(1 nm, 1%·d)，不是绝对 nm 底限实测。6 层数值例按所设 criterion 的 PoS 从 75% 到 100%，敏感性转移至最后层；代理在未参与拟合的样本上校验。这不是实际镀膜验证。

本项目推论：不能仅凭单层线性排名固定 6 个优化变量。需考虑全层/交互与相关因子。89 维全二阶 PCE 已有 C(91,2)=4095 系数，三阶更多；TMM 便宜时优先直接场景评估和导数，后续才考虑稀疏/低秩代理。若使用相关误差，经典独立变量 Sobol 层归因不宜直接套用，可先归因于独立 latent process factors。

### D. 光学监控产生的相关性同时包含补偿与累积放大

Tikhonravov et al., *Correlation of errors in optical coating production with broad band monitoring*, Numerical Methods and Programming 19 (2018), DOI 10.26089/NumMet.v19r439。[期刊原文入口](https://en.num-meth.ru/index.php/journal/article/view/986)。

Tikhonravov et al., *Strategies of Broadband Monitoring Aimed at Minimizing Deposition Errors*, Coatings 9, 809 (2019), DOI 10.3390/coatings9120809。[期刊全文](https://www.mdpi.com/2079-6412/9/12/809)。

这组研究在 50 层 non-polarizing edge filter 上比较单片、多片与 returning monitor-chip 策略：当前终止拟合受此前层的实际厚度影响，因而误差相关；相关性可能产生自补偿，也可能导致厚度误差累积。故“独立同分布扰动”和“所有层同号共模”都不是完整监控模拟，正相关也不能自动等同于差制造。

最小顺序模型（本文推导，不是上述论文的逐字算法）：令本层谱对厚度导数为 h_j，之前层导数矩阵为 J_prev，信号噪声 ε_j，则局部 least-squares 终止近似给出 δd_j = −h_jᵀ(J_prev δd_prev+ε_j)/(h_jᵀh_j)。由此得到下三角反馈与协方差。只有已知监控波段、信噪比、芯片切换、终止规则、n 模型后才可校准；厚层、非线性或多局部终止点时应做真实顺序模拟。

### E. CVaR 与约束求解器：通用方法，不冒充薄膜实证

Rockafellar & Uryasev, *Optimization of Conditional Value-at-Risk*, Journal of Risk 2(3), 21–41 (2000)。[作者开放全文](https://sites.math.washington.edu/~rtr/papers/rtr179-CVaR1.pdf)。CVaR 可用辅助阈值和正部期望表示，便于基于样本优化。这里把它应用到光谱 joint violation，是本项目的工程构造。

[SciPy SLSQP 官方文档](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html)、[官方约束优化说明](https://docs.scipy.org/doc/scipy/tutorial/optimize.html)支持提供目标/约束解析 Jacobian；trust-constr 还可利用稀疏性。这些是可靠的离线参考解基线，不要求前端直接引入 SciPy。有限精度 solver success 不等于光谱全规格最终认证。

## 3. 制造误差的工程证据，数字须保留定义

### 3.1 接近项目材料的蒸发实物证据

Sokolov et al., *Investigation of optical properties of multilayer dielectric structures using prism-coupling technique*, Quantum Electronics 45(9), 868–872 (2015), DOI 10.1070/QE2015v045n09ABEH015852。[期刊开放全文](https://quantum-electronics.ru/wp-content/uploads/2015/en/15852.pdf)。

第 870 页：11 层 ZnS/MgBaF4，VTC-900 PO 电阻蒸发、150°C、7×10^-6 mbar、自动晶控。作者报告凝结速率控制精度优于 1%，每层厚度终止精度优于 2%；约 55–57 nm 层厚。其后 TE/TM 反演层厚结果相差小于约 ±1%，这是表征一致性，不是独立层生产随机误差 σ。该证据说明 ±0.2% 不宜作为通用实际工艺代表，但不能据此断言项目实际设备误差恰为 2%，也不能把“优于2%”擅自换成 Gaussian σ=2%。

### 3.2 晶控分辨率不是膜厚准确度

INFICON *SQC-310 Operating Manual*, 074-550-P1-H。[官方手册](https://www.inficon.com/media/11922/download/SQC-310-Operating-Manual-.pdf?inline=true&language=de&v=2)。

§4.5.1/p.16：厚度与速率 accuracy 为 0.5% typical；厚度/速率 resolution 为 ±0.015 Å，后者带 tooling/density/Z=100/1/1、6 MHz、0.25 s 等条件。§10/pp.136–139 要求 density、tooling、Z-ratio 校准；晶体测的是质量，换算物理厚度需要密度，基片/晶体的非均匀通量需要 tooling，晶体负载与多材料又改变声学修正。规格不是整套设备/所有材料的 substrate 成膜保证，更不是 nm 绝对误差底限。

[INFICON 晶体应用说明](https://www.inficon.com/media/9160/download/Guide-to-INFICON-Quartz-Monitor-Crystals.pdf?language=ko&v=1)特别指出小于 50 nm 薄光学层会受开 shutter 的热冲击造成速率/厚度尖峰，可能误终止或使控制环不稳定。[官方 multilayer compensation 说明](https://www.inficon.com/en/academy/webinar/inficon-multi-layer-compensation-system)指出多种 Z-ratio 的材料累积在同一晶体上会使传统单材料修正出现累积误差。

### 3.3 同材料共模、绝对/相对、折射率误差均是现成工业分析项

[OptiLayer Statistical error analysis 官方文档](https://optilayer.com/optilayer-tools/error-analysis/statistical-error-analysis/)分别提供绝对 nm 和相对 % 厚度误差，以及 n/k 扰动、per-material 一致偏移。[OptiRE Systematic Errors 官方文档](https://optilayer.com/optire-module-of-optilayer-thin-film-software/systematic-errors/)列出仪器漂移、监控校准、真空 shift、witness tooling 等系统因素，并支持按高/低材料分离系统成分与零均值残差。这支持“分量模型”而非单一逐层 iid 百分比；它不提供该项目实际参数值。

### 3.4 ZnS/氟化物不是只存在几何厚度误差

Wu et al., *Optical inhomogeneity of ZnS films deposited by thermal evaporation*, Applied Surface Science 254, 6455–6460 (2008), DOI 10.1016/j.apsusc.2008.04.023。[期刊摘要和实验片段](https://www.sciencedirect.com/science/article/pii/S0169433208007058)。室温热蒸发 ZnS，石英基片，参考 620 nm 的光学厚度 310–1240 nm；实测随膜增长 n、packing density、粗糙度等改变，存在折射率非均匀。不能把这种误差全部解释为同一个 d 偏差。

Lemarquis, Marchand & Amra, *Design and manufacture of low-absorption ZnS–YF3 antireflection coatings in the 3.5–16-μm spectral range*, Applied Optics 37, 4239–4244 (1998), DOI 10.1364/AO.37.004239。[期刊原始摘要](https://opg.optica.org/ao/abstract.cfm?uri=ao-37-19-4239)。其 ZnSe 基片、电子束 ZnS/YF3 实物设计强调准确测定复折射率、色散和膜内水吸收，才改善长波性能。

Matsuoka et al., *Broadband multilayer anti-reflection coating for mid-infrared range from 7 μm to 12 μm*, Applied Optics 57, 1645–1649 (2018), DOI 10.1364/AO.57.001645。[期刊原文摘要及工艺表](https://opg.optica.org/ao/abstract.cfm?uri=ao-57-7-1645)。ZnS/YF3/Ge 电子束蒸发示范使用材料不同速率（ZnS 6.5 Å/s、YF3 12 Å/s、Ge 2 Å/s）和很不同的膜厚。这些是特定工艺配方，不是误差百分比，也不应当作推荐项目改变速率的依据。

空间非均匀应另作位置场/孔径模型：晶控点终止误差不能代表所有基片半径。当前没有该项目基片尺寸、夹具、均匀性扫描，不能给通用 spatial % 或实际 nm 底限。

## 4. 最小数学实现，严格保持原指标

### 4.1 单一原规格解释器

把所有区间、角度、偏振、上下界分别转成 g_j(d)≤0。举例：R≥R_min 则 g=R_min−R；R≤R_max 则 g=R−R_max。输入已经给的 margin 属于原规格，不另加。为混合 R/T/GDD 设正的单位尺度 w_j，仅用于数值归一化 g_j/w_j，不改变 g_j 的零界。

保存两套明确对象：`spec.original`（不可变来源）与 `evaluation.grid`（可细化采样）。若一条约束是 average，而不是 pointwise，必须保留 average 语义，不能悄悄换成每点硬阈值。

场景 s 的 signed joint loss：l_s(d)=max_j g_j(d_actual,s)/w_j。所有约束为非严格不等式时，yield=mean[ l_s≤0 ]；若原规格含严格上/下界，最终每个样本须按原运算符逐条件判定，边界相等不能由这个简写记为通过。保留 signed loss 比只用 max(0,l_s) 更能在全训练场景恰好通过后继续区分尾部接近失败的设计；它不改变验收零界。

### 4.2 目标二选一，均有独立 nominal 硬门

CVaR：最小化 t + Σ_s max(0,l_s−t)/[(1−α)N]，subject to g_j(d)≤0、原有制造上下界。建议先比较 α=.90 和 .95，透明记录为尾部偏好，不称为需求指定的 yield 目标。α=.95、N=64 时只有约3个尾样本，不稳定；须增大训练云或先用.90。

Epigraph minimax：最小化 z，subject to g_j(d_actual,s)/w_j≤z 对所有 s,j，另有 nominal g_j(d)≤0。最大有限样本不是真实全误差最坏值，更不是 2^89 个 box 顶点证明。

CVaR 与 yield 不完全等价：CVaR 优化严重度/尾部，最终仍按原 joint pass/yield 比较；不能把 CVaR 降低自动宣称 yield 上升。Chance constraint P(l≤0)≥p 需要明确分布与 p，需求未给目标时不要擅自承诺 99% yield。

### 4.3 可校准的分量制造模型

建议误差接口输出 actual_d、actual_n/k、latent_factors、definition、unit、distribution、seed、source。一个可解释起点：

δd_i = a_i z_abs,i + r_i d_i z_rel,i + b_material(i)d_i + b_batch d_i + drift_i d_i + spatial_i(x)d_i。

各分量若独立 Gaussian，则方差相加；iid 绝对+相对项标准差为 sqrt(a_i²+(r_i d_i)²)，不是随意取某一个百分比。b_material 是同材料全层共享一次抽样，不是每层另抽。drift 可以先以 AR(1) 模拟，参数只是压力测试假设，后续由生产时间序列估计。

须分清均匀 bound a 与 Gaussian σ：Uniform[-a,a] 的 σ=a/√3。±0.2% uniform 实际 σ约0.1155%，不是 σ=.2%。不要默默截断/clip 负厚度；应设正物理厚度的受限分布或明确拒绝策略，并报告其影响。导出厚度量化/终止 overshoot 可另设确定性 round/offset 测试。

线性诊断：每条约束 Var[g_j]≈J_j Σ_d J_jᵀ；全响应 covariance≈JΣ_dJᵀ。独立 box 的一阶最坏扰动为 Σ_i |J_ji|a_i，而不是 L2 norm；Gaussian/椭球才对应相应二次型。解析指标只用于快速诊断/预条件，最终靠非线性完整场景。

### 4.4 从坐标搜索升级的最小路径

1. 每个场景一次 TMM 同时返回所有可优化层导数。用 prefix/suffix 矩阵积或等效递推得到全层 Jacobian，避免为每层做一遍完整 finite difference。先与中央差分逐层、随机方向对比，测试角度/偏振/吸收层和相位分支。
2. 场景重用 common random numbers：固定底层 z 与训练种子，设计改变时按模型变换 actual_d；若相对项依赖 d，gradient 要包含 ∂actual_d/∂d，不能当固定 additive offset。每次刷新云属于新训练阶段，不与前一阶段目标数值直接比较。
3. 初始 active constraints 包含所有 nominal 近边界点、每个规格段端点、当前 extrema、每个训练场景最坏点。SQP/active-set 或外层 augmented-Lagrangian + L-BFGS 更新全层；若只有前端实现，先做带 bounds/feasibility filter 的梯度方向与回溯也比 17 点逐轴试探高效，但别称其提供硬约束收敛证明。
4. 每次候选定期回扫全 nominal/场景网格；发现遗漏点就加入 active set，再优化。所有最终接受方案必须单独过完整 nominal checker，solver 的 success flag 不足。用数值求解容差处理浮点误差，不用“容差”吞掉真实规格超限。
5. 选择变量与扰动维度分开：即便只优化6层，也须扰动全部89层；但应优先让全部允许层参与梯度优化。若资源不足，用 JΣ^(1/2) 低秩方向或分组厚度变量开局，再全层 polish；不能永久把一阶低排名层当不相关。
6. 离线做一份同目标/同约束的 SLSQP 或 trust-constr 参考解，以区分“目标有问题”与“前端求解器弱”。相同预算比较要记录 TMM实际次数/场景数/光谱点评估数/时间，不能只比较外层 evaluation counter。

## 5. 分阶段最小交付

P0，可信规格：锁定原始输入；验证 89 层在 0.1 nm+局部 extrema/角度细化下是否可行。若不行，先 nominal feasibility restoration，明确报告修复前后的最坏点及超限，不进入“已可制造”结论。

P1，可信误差：实现 absolute nm + relative % 两独立项与 material/batch 共模；保留旧±.2%作为 regression。每种分布参数、σ/bound、单位和数据来源必须出现在报告元数据。没有实测则标记 hypothetical_stress_not_process_data。

P2，可信优化：场景云64→128→256逐级、固定种子、解析梯度、nominal约束；比较CVaR与有限minimax，保留最佳可行 incumbent，不能因目标变好覆盖 nominal 失败的基线。严重误差可做 continuation，但最终仍在指定误差档验收。

P3，可信评价：候选选择用validation；最终另留从未用于调参/选解的test。独立场景建议至少512起，最终2048或更多，按精度/预算增加。相同test潜变量成对比较baseline与candidate。输出每规格失败率、joint yield、Wilson或exact binomial CI、signed worst/quantile/CVaR、R/T原单位、失败波长/角度/偏振。95%CI方法可参见[NIST原始技术手册](https://itl.nist.gov/div898/handbook/prc/section2/prc241.htm)。

P4，工艺闭环：收集按材料的单层 n/k、晶控实际/基片实测厚度、沉积速率和时间、晶体寿命、tooling、批次/半径、监控模式；拟合bias/variance/correlation。若有真实光学监控，再做顺序补偿模拟；不把事后任意调整所有层当成现实可执行补偿。

## 6. 最小验证矩阵

以下数值全部是建议的假设压力测试，不是项目实际工艺估计，也不是引用论文的统一精度结论。

| 轴 | 最小测试 | 必须回答 |
|---|---|---|
| 设计 | 小AR；89层原始；修复nominal后的89层；高敏感合成回归例 | 改善是否仅小问题有效？ |
| 相对iid uniform | bound ±.2%、±.5%、±1%、±2%；可另加±5%极端诊断 | 大误差下是否仍有收益，还是全失败？ |
| 绝对+相对Gaussian | (σ_abs nm,σ_rel)=(.25,.5%)、(.5,1%)、(1,2%)、(2,3%) | 薄层绝对项是否被忽略？明确这些是σ不是bound。 |
| 相关因子 | 单独及混合：按材料共模bound±.5/1/2%；batch共模；AR(1)ρ=.8/.95，保持已声明边际尺度 | iid训练是否只会保护不现实方向？ |
| n与空间 | material n偏移±.5/1%诊断；位置厚度场±.5/1/2%诊断；k绝对偏差需材料实测后设 | 几何d改善是否被材料模型/孔径误差抵消？ |
| 光谱网格 | 原网格、0.1nm、失败点局部更细；角度端点+interior extrema；两偏振 | 采样之间是否漏峰？细网格仍不构成连续域证明。 |
| 泛化 | 固定train；独立validation选解；未触碰test；多个优化seed | 有没有训练过拟合/挑seed？ |
| 消融 | 原算法；nominal硬门；+误差模型；+梯度；CVaR vs minimax | 真正改善来自何处？ |
| 成本 | 6变量 vs 全89变量，同TMM预算；active与全网格对照 | 梯度路线是否真的更快而非偷减验收？ |

验收措辞分级：
- nominal不合格：不发布为满足原指标的稳健方案。
- nominal合格、test tail改善但yield差异不确定：只能称“在该假设误差模型下尾部违规减轻，良率改善尚无足够证据”。
- nominal合格、独立test yield及区间支持改善：称“仿真制造良率在所声明模型下改善”；不能升级为实物生产保证。
- 只有实测批次与工艺模型校准后，才谈与实际工艺相关的量产收益。

## 7. 来源核查与可访问性备注

本次已完整读取：DESY 2011 AR论文PDF、AttoWorld 2011 robust synthesis论文PDF、Quantum Electronics 2015 ZnS/MgBaF4论文PDF、INFICON手册/应用说明、Rockafellar作者PDF、OptiLayer官方文档。Nature/NRC和MDPI部分直接打开受站点cookie/限流影响，但原期刊/机构的检索全文片段可读并核实所述细节。部分Optica论文只公开摘要/表格，本文未把未读全文内容当成已核实事实。ResearchGate及第三方聚合页只用于找原始入口，没有作为最终技术证据。
