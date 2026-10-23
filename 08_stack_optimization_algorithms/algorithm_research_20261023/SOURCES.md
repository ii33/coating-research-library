# 原始来源索引：光学薄膜稳健设计与制造容差

核查日期：2026-10-23。证据等级描述的是本文所用证据，不是期刊质量排名。

## 薄膜稳健优化

1. Birge, J. R.; Kärtner, F. X.; Nohadani, O. (2011). *Improving thin-film manufacturing yield with robust optimization*. Applied Optics 50, C36–C40. DOI 10.1364/AO.50.000C36。
   - [机构开放全文](https://bib-pubdb1.desy.de/record/97205/files/32DE6A27-C2C7-A869-C92E4A7D3539AB91_206412.pdf)
   - 证据：薄膜数值试验；明确区分 minimax、nominal 与 yield。
2. Pervak, V.; Trubetskov, M. K.; Tikhonravov, A. V. (2011). *Robust synthesis of dispersive mirrors*. Optics Express 19, 2371–2380. DOI 10.1364/OE.19.002371。
   - [作者机构开放全文](https://attoworld.de/fileadmin/user_upload/tx_attoworld/publications/paper_OptExpr_Y2011_M01_D31_V19_P2371.pdf)
   - 证据：场景云、绝对/相对误差、解析导数；磁控溅射实物对照及两次 robust 制造。
3. Poitras, D.; Ma, P. (2025). *Surrogate sensitivity analysis of facet optical coatings produced without and with in situ design reoptimization*. Scientific Reports 15, 5692. DOI 10.1038/s41598-025-89625-6。
   - [期刊原文](https://www.nature.com/articles/s41598-025-89625-6)
   - [NRC 机构存档](https://nrc-publications.canada.ca/eng/view/object/?id=a9867a0a-07b0-4c40-bafe-709512c4e41f)
   - 证据：数值试验；PCE/Sobol、层交互、顺序再优化；不是实物工艺精度标定。
4. Tikhonravov, A. V. et al. (2018). *Correlation of errors in optical coating production with broad band monitoring*. Numerical Methods and Programming 19. DOI 10.26089/NumMet.v19r439。
   - [期刊原始入口](https://en.num-meth.ru/index.php/journal/article/view/986)
   - 证据：光学监控误差相关模型及高效模拟器。
5. Tikhonravov, A. et al. (2019). *Strategies of Broadband Monitoring Aimed at Minimizing Deposition Errors*. Coatings 9, 809. DOI 10.3390/coatings9120809。
   - [期刊原文](https://www.mdpi.com/2079-6412/9/12/809)
   - 证据：数值比较监控芯片策略，自补偿与误差积累并存。

## 制造与材料

6. Sokolov, V. I. et al. (2015). *Investigation of optical properties of multilayer dielectric structures using prism-coupling technique*. Quantum Electronics 45(9), 868–872. DOI 10.1070/QE2015v045n09ABEH015852。
   - [期刊开放全文](https://quantum-electronics.ru/wp-content/uploads/2015/en/15852.pdf)
   - 证据：ZnS/MgBaF4 电阻蒸发实物；速率和厚度终止精度定义见 p.870，不是 Gaussian σ。
7. INFICON. *SQC-310 Operating Manual*, 074-550-P1-H。
   - [官方手册](https://www.inficon.com/media/11922/download/SQC-310-Operating-Manual-.pdf?inline=true&language=de&v=2)
   - 证据：p.16 仪器 accuracy/resolution；pp.136–139 density/tooling/Z 校准。
8. INFICON. *Guide to INFICON Quartz Monitor Crystals*。
   - [官方应用说明](https://www.inficon.com/media/9160/download/Guide-to-INFICON-Quartz-Monitor-Crystals.pdf?language=ko&v=1)
   - 证据：shutter 热冲击、薄层终止尖峰，不能以分辨率替代真实成膜准确度。
9. INFICON. *Multi-layer Compensation System*。
   - [厂商原始说明](https://www.inficon.com/en/academy/webinar/inficon-multi-layer-compensation-system)
   - 证据：同晶体多材料 Z-ratio 累积误差机制；不是某一用户设备的量测。
10. OptiLayer. *Statistical error analysis*；*Systematic Errors*。
    - [统计误差官方文档](https://optilayer.com/optilayer-tools/error-analysis/statistical-error-analysis/)
    - [系统误差官方文档](https://optilayer.com/optire-module-of-optilayer-thin-film-software/systematic-errors/)
    - 证据：绝对/相对、材料共模、n/k 与系统/随机误差分解的工业建模功能。
11. Wu, X. et al. (2008). *Optical inhomogeneity of ZnS films deposited by thermal evaporation*. Applied Surface Science 254, 6455–6460. DOI 10.1016/j.apsusc.2008.04.023。
    - [期刊摘要与实验片段](https://www.sciencedirect.com/science/article/pii/S0169433208007058)
    - 证据：热蒸发 ZnS 实物的折射率、致密度与厚度相关非均匀；本文没有依赖付费全文中的未读数据。
12. Lemarquis, F.; Marchand, G.; Amra, C. (1998). *Design and manufacture of low-absorption ZnS–YF3 antireflection coatings in the 3.5–16-μm spectral range*. Applied Optics 37, 4239–4244. DOI 10.1364/AO.37.004239。
    - [原始期刊摘要](https://opg.optica.org/ao/abstract.cfm?uri=ao-37-19-4239)
    - 证据：电子束 ZnS/YF3 实物设计必须考虑复折射率、色散和水吸收。
13. Matsuoka, Y. et al. (2018). *Broadband multilayer anti-reflection coating for mid-infrared range from 7 μm to 12 μm*. Applied Optics 57, 1645–1649. DOI 10.1364/AO.57.001645。
    - [原始期刊摘要与表格](https://opg.optica.org/ao/abstract.cfm?uri=ao-57-7-1645)
    - 证据：电子束 ZnS/YF3/Ge 具体工艺及设计厚度；速率不是误差精度。

## 通用优化与统计

14. Rockafellar, R. T.; Uryasev, S. (2000). *Optimization of Conditional Value-at-Risk*. Journal of Risk 2(3), 21–41。
    - [作者开放全文](https://sites.math.washington.edu/~rtr/papers/rtr179-CVaR1.pdf)
    - 证据：CVaR 优化表达式；不是光学薄膜制造实验。
15. SciPy. *minimize(method='SLSQP')*；*Optimization tutorial*。
    - [SLSQP 官方文档](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html)
    - [约束优化官方说明](https://docs.scipy.org/doc/scipy/tutorial/optimize.html)
    - 证据：解析目标/约束 Jacobian、约束优化与求解器选择；需独立最终可行性检查。
16. NIST/SEMATECH. *Confidence intervals for proportions*, e-Handbook §7.2.4.1。
    - [官方统计手册](https://itl.nist.gov/div898/handbook/prc/section2/prc241.htm)
    - 证据：binomial proportion 的 Wilson/exact 区间方法，不证明误差分布模型正确。

## 读取边界

DESY、AttoWorld、Quantum Electronics、INFICON、Rockafellar 全文及 OptiLayer 官方文档可完整读取。Nature/NRC 与 MDPI 本次部分直接访问受到 cookie/限流影响，但原始期刊/机构检索全文片段可核实研究所引细节。Optica 与 ScienceDirect 某些论文仅公开摘要/表格/片段，本报告只使用可核实的公开部分。未用第三方聚合页代替原始证据。
