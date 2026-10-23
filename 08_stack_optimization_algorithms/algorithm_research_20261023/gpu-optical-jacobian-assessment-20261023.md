# GPU光学与解析厚度Jacobian：只读评估摘要

日期：2026-10-23。依据[公开软件数值基线fa987833](https://github.com/ii33/coating-sim/tree/fa9878336a597dc6df1db5b584bda3be4423cbca)及官方技术资料整理。本次未运行GPU、未实现新后端、未改源码或环境；不含当前主机配置、运行目录或私人信息。以下实现建议均为待验证提案，不是89层任务已加速的证据。

## 1. 不是从零新增GPU forward

该公开基线已有FP64/complex128 Torch批量相干前向，可供部分自动合成纯forward阶段使用；不能因此称整个合成或敏感性流程已在GPU上。

现敏感性评价仍直接使用CPU解析厚度Jacobian，没有GPU/backend请求入口。固定拓扑DE、通用性能后端、合成forward和敏感性是不同接线，不能把一个入口的GPU能力移植为另一个入口已实现。代码依据为同提交的[GPU前向](https://github.com/ii33/coating-sim/blob/fa9878336a597dc6df1db5b584bda3be4423cbca/coat_sim/core/film_optics_gpu.py)、[敏感性评价](https://github.com/ii33/coating-sim/blob/fa9878336a597dc6df1db5b584bda3be4423cbca/coat_sim/core/film_sensitivity.py)与[解析导数](https://github.com/ii33/coating-sim/blob/fa9878336a597dc6df1db5b584bda3be4423cbca/coat_sim/core/film_optimization_derivatives.py)。这是代码状态，不是本次硬件验收。

建议分工是GPU执行同公式物理forward与解析Jac，CPU保留冻结问题、层ID/变量映射、优化调度、目标聚合、取消/预算及严格最终验收。若显式GPU链路实际回落CPU，必须如实标示或拒绝，不能将fallback计为GPU成功。

## 2. 复用解析双sweep，而非替换物理问题

现解析核具有约O(P×(L+V))的双sweep结构，P为条件点、L为层数、V为求导变量列。可复用冻结q、Fresnel接口和flux不变量，GPU并行条件/波长/角度/同拓扑场景；每层递推仍有真实顺序依赖，不把89层误拆成独立线程。

优先迁移同一complex128/float64运算和分支，保持被动复折射率、s/p功率平均、层序及临界/奇异域错误语义。理想k=0仍有复传播相位，不能据此换成实数近似。解析GPU路径不以autograd或有限差分替代；有限差分只作独立导数核查。

原型A建议先扩展现Torch冻结buffer/forward，禁用梯度图，按场景与条件分块。若剖面确认逐层eager launch和临时数组是瓶颈，再考虑原型B的CuPy RawKernel融合。B新增手工dtype、stride、错误flag、JIT及跨设备风险，不能仅将NumPy数组替换就称验收；[CuPy官方文档](https://docs.cupy.dev/en/stable/user_guide/kernel.html#kernel-arguments)明确内核参数类型/数量需调用方负责。

## 3. FP64与显存约束，不承诺10倍

[NVIDIA Ada白皮书](https://images.nvidia.cn/aem-dam/Solutions/Data-Center/l4/nvidia-ada-gpu-architecture-whitepaper-v2.1.pdf)第7页对AD102列出的FP64吞吐约为FP32的1/64。此类complex128的sqrt/exp/div与逐层递推不能由营销FP32或Tensor峰值推得任务速度。保持双精度，不用TF32/FP32/混精度或fast-math制造收益。

对P=184600、L=89、S=32，若保留三组每层complex128系数，仅48×P×S×L就约23.50GiB。两个float64功率Jac输出另需16×P×S×V：V=89约7.83GiB，V=6约0.528GiB。以上是明确数组的公式预算，不含全部临时、context、allocator、缓存或驱动；更不是实测峰值。

因此必须按条件与场景分块、复用不变量和工作区，主机也分块消费。减块可以，暗减原光学网格/场景不可以。应同时报告框架allocated/reserved、设备整体使用基线/峰值及主机RAM；数组估算不能替代这些实测。

## 4. 历史60层结果只限原实验

[正式仓库历史报告](https://github.com/ii33/coating-sim/blob/fa9878336a597dc6df1db5b584bda3be4423cbca/docs/film-synthesis-gpu-forward-report-20261020.md)记录60层Ge/BaF2与ZnS、64固定候选、CPU局部精修和CPU留出的CPU8/CUDA反序对照：中位76.898/45.948秒，比值1.6736；全观测最大CPU/CUDA绝差3.3085e-14，最终目标未达。

这只是历史固定60层评价/精修流程，并非从零长到60层，也不是本次89层、184600条件、32场景的敏感性GPU Jac结果。resident微计时不代表整个流程，历史三项GPU回归也不构成当前89层性能验证。本次没有重跑这些实验，不外推10倍或线性加速。

## 5. 建议先验数值，再做公平计时

- 固定同处方、冻结材料/理想假设、原网格、场景、变量列及优化预算，分别核forward-only和forward+Jac，先S=1再扩大。不能改采样、权重或物理模型来制造更快。
- 全列/子集/重排、s/p/非偏振、零厚/正厚/吸收/近临界及奇异拒绝分别核GPU与原CPU；再独立有限差分核Jac。具体新Jac容差是实施时待确认的数值门，不自动放宽原验收。
- 原严格R/T不等号仍按真实值判定；allclose数值门不使IR等号变通过，不添加隐性margin。最终候选使用原CPU完整回放/独审。
- cold计入导入/context、准备/上传、数值门、JIT、计算/回传、评分和清理；warm预热后AB/BA交替，分别报告kernel-only与端到端。CPU提交异步操作的时间不是GPU完成时间；[PyTorch官方CUDA说明](https://docs.pytorch.org/docs/2.10/notes/cuda.html#asynchronous-execution)要求同步或CUDA Event准确计时。
- 对照实际现用CPU敏感性链路，不把其他合成入口的19worker能力冒充敏感性已有并行。记录取消、OOM、非有限、dtype/设备身份错误与fallback，不发布半Jac结果。

以上是受控原型与验收建议，尚未形成新GPU实现或任务性能结论。[PyTorch复数文档](https://docs.pytorch.org/docs/2.10/complex_numbers.html)支持cdouble/complex128，但不能代替具体后端与全算子实机核查。

## 6. 与当前产品方向的关系

本期敏感度优化先针对明确理想假设并保持原名义规格；参数表驱动的预期误差分析独立提供，暂不预置真实工艺模型或生产yield目标。GPU只改变执行后端，不扩展这些物理/产品承诺。历史制造误差探索继续保留为研究，不作为当前生产默认。

本摘要不含软件源码、脚本、完整请求、材料数据、场景系数、主机路径或执行元信息。引用公开源是为了区分实现、历史证据和提案，并不重新发布软件。
