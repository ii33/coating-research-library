# 几何光追到波前偏振光瞳及衍射成像的成熟化路线

研究日期：2026-10-10。对象：顺序平面／球面几何光追、位置相关逐层沉积厚度、局部薄膜 TMM 已存在的光学仿真 MVP。目标硬件：CPU、RTX 4070 Ti Super 16 GB 显存、32 GB 内存。本稿给出物理边界、数据接口、开源选型和验证门槛；没有在目标机器上运行基准测试，不给速度承诺。所列软件功能依据官方仓库及公开文档核实，开发版文档与稳定发布版必须分别锁定。

## 1 结论与优先路线

建议保留已有几何和沉积模型，在其后建立独立的“复振幅出口”，首先完成单条主透射路径的 OPD、振幅和 Jones pupil，再用可替换的波动传播器产生衍射 PSF，最后进行源积分、成像和探测器转换。第一条成熟链应是：

光源及相干状态 → 带光程、局部基底与功率权重的几何光追 → 每次命中的局部复数 TMM 系数 → 出瞳／参考面上的复振幅或 Jones pupil → 波动传播 → 场／波长／相干模加权 → 像素积分与电子数。

核心决定如下。

1. **现有探测器直方图应命名为几何辐照度图或加权点列图。** 它没有跨孔径相位干涉，不能称衍射 PSF。几何 MTF 也应单列，不能替代包含衍射的 OTF／MTF。
2. **先做局部波动与几何传播混合，不把整个器件空间离散成 Maxwell 网格。** 普通宏观成像系统可在几何有效区域用光追，在出瞳、光阑邻域、焦面及需要衍射的子系统传播复振幅。后续按误差预算增加近场段、Gaussian beamlets 或矢量衍射。
3. **推荐 Prysm 为首个可切换 CPU／CuPy 的衍射与探测器后端，HCIPy 为偏振和多平面物理光学的独立参考，Optiland 为几何／波前／PSF 的对照实现。** Poke 很适合学习和复用几何到 Jones pupil／beamlet 的接口思想，但其现成取数工作流仍主要依赖 Zemax／CODE V。此选型是工程判断，不等于这些库已经替本项目通过精度验证。
4. **不要承诺 HCIPy 全流程 GPU 已成熟。** 官方 dev 的 NewStyleField／Array API 支持 CuPy 等后端，但明确处于实验阶段，且许多 OpticalElement 尚不兼容。[HCIPy Performance](https://docs.hcipy.org/dev/performance.html)
5. **相位、采样面积、波长权重和绝对辐射量必须写进接口。** 只有“每条光线功率＋位置”无法唯一重建相干波前；几何形状、入瞳照明和光源相干模型同样必需。

## 2 当前 MVP 的物理边界

本路线承认现有 MVP 不具备宏观反射分支、体吸收和相干面间传播。因此第一阶段的结果仅表示规定顺序下的主透射像及其衍射，不包含鬼像、杂散反射、多路径干涉、体散射或完整热损耗预算。

还需区分“从几何结果构造最后一个复光瞳”和“在每个需要的位置传播复场”。前者不能恢复此前已被几何近似漏掉的中间光阑 Fresnel 衍射、面间振幅起伏或多次裁切的相干耦合。如果这些效应影响目标指标，应从第一个相关平面开始插入波动子链；末端加一个 FFT 不会追溯补全整条光路的波动历史。

局部 TMM 能包含一个薄膜堆内的多重反射干涉；这不等于已经模拟不同宏观光学表面之间的反射往返。两个层级应分别记录：

- 层内／堆内：由同一次 TMM 调用处理复数反射、透射与堆内相位。
- 表面之间：由几何分支或场传播图处理路径、传播相位和相干关系，不能靠重复乘局部强度透过率代替。

局部平面堆近似要求涂层厚度、材料和表面法向在相关横向尺度内足够缓变，曲率半径远大于波长及膜厚，并且所研究效应不依赖显著横向耦合。若膜厚图出现波长尺度台阶、光栅或超表面，逐点 TMM 会漏掉衍射级次及横向耦合；需专门的局部 RCWA／FDTD／FEM 散射算子，再接回宏观光路。软件的“局部 TMM 图”不能因此被标为完整全波解。

当口径远大于波长、介质分段均匀、表面光滑、出瞳映射单值、没有未处理的焦散和强非局域散射时，光追生成的 eikonal／Jones pupil 是有效的渐近桥梁。接近焦散、边缘阴影过渡、高 NA 或强矢量耦合时，应增加更合适的波动段，而不是仅加密几何光线。

## 3 开源实现核实

### 3.1 实际开放能力及建议用途

| 项目 | 已核实开放能力 | GPU 情况及边界 | 建议用途 |
|---|---|---|---|
| HCIPy | Fraunhofer／Fresnel、标量／Jones 波前、部分偏振、光阑和波片等 | dev 的 Array API／NewStyleField 可用 CuPy；官方明确实验性，光学元件支持尚不完整 | CPU 偏振及多平面参考，逐模块试验 GPU |
| Prysm | FFT、矩阵 DFT／CZT、角谱、像差、多波长示例、像素及噪声模型 | 官方说明可替换 NumPy／SciPy shim 为 CuPy；不代表所有可选依赖和外部数据 IO 都无缝留在 GPU | 首选可控波动后端；先验证所用调用子集 |
| Optiland | 几何光追、OPD／参考球面、Jones pupil、标量与矢量 FFT／Huygens PSF，另有标量角谱接口 | NumPy CPU 与 PyTorch GPU／autograd；具体模块、精度和版本仍需测试 | 与 MVP 对照，参考出瞳及 OPD 实现，不必整体替换现有系统 |
| Poke | Polarization Ray Tracing、Gaussian Beamlet Decomposition、TMM、Rayfront 保存及 HCIPy／POPPY 接口示例 | 论文说明可切 CuPy／JAX；仓库自称早期开发。不能把外部商业光追器自动视为可微或 GPU | 研究桥接方式和局部 beamlet；自有光追输入需适配器 |
| POPPY | 标量 Fraunhofer／Fresnel、单色及多色 PSF | 有 NVIDIA GPU 加速路径；当前 GPU 文档较简略，仍须针对工作流验证 | 独立标量基准；不作为原生偏振或探测器噪声引擎 |

能力证据：[HCIPy 官方仓库](https://github.com/ehpor/hcipy)、[HCIPy 偏振教程](https://docs.hcipy.org/dev/tutorials/PolarizationIntro/PolarizationIntro.html)、[Prysm propagation API](https://prysm.readthedocs.io/en/latest/api/propagation.html)、[Prysm GPU 文档](https://prysm.readthedocs.io/en/latest/how-tos/GPU%20and%20Exascale%20Computing.html)、[Optiland 波前 API 索引](https://www.optiland.org/docs/api/api_wavefront.html)、[Optiland 标量物理光学 API](https://optiland.readthedocs.io/en/latest/api/api_physical_optics.html)、[Poke 文档](https://poke.readthedocs.io/en/latest/)、[POPPY 能力与限制](https://poppy-optics.readthedocs.io/en/latest/)、[POPPY GPU 文档](https://poppy-optics.readthedocs.io/en/latest/gpu_acceleration.html)。

几个容易误读之处：

- HCIPy 的“部分偏振”并不自动解决任意部分空间相干源的传播。
- Prysm 的偏振扩展位于 `prysm.x.polarization`；文档存在标为 experimental 的辅助实现。可把四个 Jones 元素分别当复数通道传播，但不能对任意入射偏振都简单把四通道强度相加，必须再与输入相干矩阵组合。[Prysm polarization API](https://prysm.readthedocs.io/en/latest/api/x/polarization.html)
- Optiland 文档中的矢量 PSF 是真实开放的实现，不宜再把项目归类为“只有几何光追”。但是函数名含 vectorial 或 Huygens 并不自动证明它符合本项目全部高 NA、曲面探测器及绝对通量需求。[VectorialHuygensPSF](https://www.optiland.org/docs/api/psf/psf.vectorial_huygens.html)
- Poke 的官方快速工作流要求有人取得 Zemax／CODE V 光线数据。其开放物理内核及保存后的 Rayfront 不等于免费开放的完整商业光追器；自建 Rayfront 适配必须验证字段、单位和基底。[Poke 接口说明](https://poke.readthedocs.io/en/latest/notebooks/jonespupils.html)
- POPPY 官方明确不提供完整 Rayleigh–Sommerfeld／矢量电磁传播或探测器缺陷噪声模型。分别用 POPPY 传播 Jones 通道是外层组合方法，不应描述为 POPPY 原生矢量求解。

### 3.2 许可证和版本

核实到的项目许可证为：HCIPy MIT、Prysm MIT、Optiland MIT、Poke BSD-3-Clause、POPPY BSD-3-Clause。直接证据分别是 [HCIPy LICENSE](https://github.com/ehpor/hcipy/blob/master/LICENSE)、[Prysm LICENSE](https://github.com/brandondube/prysm/blob/master/LICENSE.md)、[Optiland LICENSE](https://github.com/optiland/optiland/blob/master/LICENSE)、[Poke LICENSE](https://github.com/Jashcraf/poke/blob/main/LICENSE.md)、[POPPY LICENSE](https://github.com/spacetelescope/poppy/blob/develop/LICENSE.md)。打包时仍应保留相应版权和许可声明，并另查材料数据库、第三方数据文件及商业 API 的条件；主项目许可证不覆盖所有外部内容。

检索时 HCIPy dev 页面已到 0.7.1 开发序列，Prysm stable 与 latest 页面分别显示 0.21.1／0.22，Optiland 部分页面显示 0.6.2 开发提交，也能检索到较旧 stable 页面。不要混用不同版本的代码片段。实施时应记录 release／commit、Python、NumPy／SciPy、CuPy／PyTorch、CUDA／驱动版本及许可证快照；本稿的在线链接是定位资料，不是依赖锁文件。

## 4 光源不能只剩随机光线

### 4.1 辐亮度与几何通量

统一内部 SI：位置与真空波长用 m，方向单位向量，角度 rad，功率 W。谱辐亮度定义为

\[
L_\lambda(\mathbf r,\hat{\mathbf k})\quad[\mathrm{W\,m^{-2}\,sr^{-1}\,m^{-1}}],\qquad
d\Phi_\lambda=L_\lambda\cos\theta\,dA\,d\Omega.
\]

这里 `per m wavelength` 与常见 `per nm` 差 \(10^9\)，必须明确。Monte Carlo 光线权重需要除以实际采样 PDF，且包含面积、方向、波长采样的积分测度；不能用“每条线一样亮”掩盖不同采样策略。[PBRT 作者官方 Radiometry 第 4.1 节](https://pbr-book.org/4ed/Radiometry%2C_Spectra%2C_and_Color/Radiometry)

无损几何传输中，约化辐亮度 \(L/n^2\) 与 étendue \(dG=n^2\cos\theta\,dA\,d\Omega\) 的关系是有用的校验。透过率和孔径截断降低通量；折射引起的方向空间压缩不能被误认为辐亮度无成本增加。[PBRT 官方折射与辐亮度推导](https://www.pbr-book.org/3ed-2018/Reflection_Models/Specular_Reflection_and_Transmission)

### 4.2 独立的相干状态

源接口应分别提供：

- 几何／辐射部分：发光面积、方向分布、谱密度、绝对功率、时间依赖。
- 场部分：单个相干模的复振幅／初相位、参考面、偏振状态。
- 统计部分：互不相干模式及非负权重，或者交叉谱密度的显式模型。

辐亮度不包含完整的相位与互相干信息，因此不存在一般性的“把任意随机几何射线开平方就得到正确波前”。例如，一个热光物点在某窄波长分量上的跨入瞳场应作为一个空间相干响应计算，不应把采样它的每条射线当作互不相干光源。不同不相干物点的像再加强度。

对单模激光，应从 Gaussian／实测复场出发；不能独立任意指定腰斑和发散角，再以为随机位置与方向采样已经保留了单模相干性。理想近轴 Gaussian 的腰斑与远场发散满足衍射约束；有 M² 或多模时应明确源模型及适用范围。

## 5 最小可审计数学接口

### 5.1 每条主路径与每个命中点

至少保存以下信息，而非只保存末端落点。

| 字段 | 含义与约束 |
|---|---|
| `field_id, wavelength_m, mode_id, branch_id` | 物点／视场、真空波长、相干模和宏观路径身份；mode 不能等同 ray |
| `r_global_m, k_hat, normal_hat` | 全局位置、传播方向和界面法向，均注明正向约定 |
| `surface_uv, surface_id, material_id` | 局部表面参数及材料索引；用于同一物理位置读取逐层厚度 |
| `basis_in, basis_out` | 每条光线的有向正交横向基；记录局部 s／p 与全局输出基的变换 |
| `opl_bulk_m` 或稳定的差分 OPL | 所有传播段 \(\sum n'\ell\)，使用 float64；与涂层相位分开 |
| `J_surface_complex` | 复数 Jones 系数及坐标基，不能只输出 T、R |
| `area_weight, sample_pdf, validity` | 孔径求积权重／几何采样 PDF、遮挡和失效掩膜；两种权重用途不可混用 |
| `power_weight_W` | 几何能量记账；注明已包含哪些膜损耗、体损耗及源谱权重 |

未来加入宏观反射分支时，同一相干模的各分支仍应保留相对光程；反射路径不应无条件强度相加。若源相干时间／带宽使相对延时去相干，可由谱积分或互相干函数给出交叉项衰减。

### 5.2 相位与符号

可选一套明确约定：时谐场 \(\mathrm{Re}\{E e^{-i\omega t}\}\)，前向传播 \(e^{+i k_0\tilde n\ell}\)，被动材料 \(\tilde n=n+i\kappa\)、\(\kappa\ge0\)。则振幅吸收因子为 \(e^{-k_0\kappa\ell}\)，功率吸收为 \(e^{-2k_0\kappa\ell}\)。这只是本项目建议约定；库适配必须转换其自身符号。

总体相位使用

\[
\phi_{\rm bulk}(\mathbf u,\lambda)=\frac{2\pi}{\lambda_0}\,W_{\rm bulk}(\mathbf u,\lambda),\qquad
W=S_{\rm actual}-S_{\rm reference}.
\]

涂层的复透射／反射相位留在 Jones 矩阵中。若导出的商业 OPD 已包括涂层相位，必须写 `opd_includes_coating_phase`，避免再乘一次而双计。只乘 \(\sqrt T\) 会丢失薄膜相位，不能用于可靠的波前像差。

同样，前端库的“phase”可能实际表示 OPD nm。Prysm `Wavefront.from_amp_and_phase` 文档明确要求该参数为 nm，波长为 µm、入瞳间距为 mm；它不是 rad 数组。Optiland 常规几何为 mm、波长为 µm、角度为 degree。适配边界必须显式转换。[Prysm Wavefront API](https://prysm.readthedocs.io/en/latest/api/propagation.html#prysm.propagation.Wavefront.from_amp_and_phase)、[Optiland conventions](https://www.optiland.org/docs/conventions.html)

### 5.3 参考面与 Jones pupil

每份场数据须含：参考面的原点、基向量、法向、参考球面中心和半径（若有）、波长、介质折射率、网格坐标、面积权重、相位符号、焦距／像距、删去了哪些 piston／tilt／defocus。参考面不是随手选一个 z 值。

- 成像系统通常相对一个指定像点的参考球面定义 WFE。
- 无焦系统通常相对参考平面。
- 计算实物像面时不能为了“更好看”自动删除 defocus；这相当于改变焦面。
- 为比较形状去 tilt 可以，但必须另保存实际质心／像点位移。多波长 PSF 不可各自居中后再叠加，否则横向色差会被抹掉。
- 单一模的全局 piston 不改变它的强度 PSF，但不同相干分支之间的 piston、或脉冲频谱相位不能随意删除。

Optiland 已把平面与球面参考抽成独立几何类，可用于接口对照。[ReferenceGeometry API](https://www.optiland.org/docs/api/wavefront/optiland.wavefront.reference_geometry.html)

在固定输出横向坐标中定义复光瞳

\[
\mathbf P_\lambda(\mathbf u)=M(\mathbf u)\,a_{\rm geom}(\mathbf u)\,
\widetilde{\mathbf J}_\lambda(\mathbf u)\,
e^{i2\pi W_{\rm bulk}(\mathbf u)/\lambda_0}.
\]

\(M\) 为孔径及遮挡，\(a_{\rm geom}\) 表示入射照明和光线管映射，\(\widetilde J\) 是约定好功率归一化的偏振传递。对于固定相干输入 Jones 向量 \(\mathbf e\)，场为 \(\mathbf P\mathbf e\)。

**不能把功率归一化 Jones 与原始电场 Fresnel 系数混用。** 对无损、实折射率的同一平面界面，原始电场透射系数满足 \(T_{s,p}=\frac{n_t\cos\theta_t}{n_i\cos\theta_i}|t_{s,p}|^2\)；只有吸收进这个功率因子后的系数才可直接按模平方解释为该通道功率透过率。对于复折射率／吸收介质，要采用相应 Poynting／光学导纳定义，不能机械套实数公式。

建议分为两种明确的接口模式，不能同时重复修正：

1. 物理电场模式：保留原始复电场、局部介质／传播方向，并从 Poynting 向量算穿过参考面的通量。
2. 近轴功率归一化模式：用 \(u\,[\sqrt{\mathrm W}/\mathrm m]\)，使 \(\int u^\dagger u\,dA=P\)；Jones 传递和参考面映射均遵循此归一化。标准 FFT 成像优先使用此模式。

固定视场下，几何映射 \(\mathbf u_{in}\mapsto\mathbf u_{out}\) 改变光线管截面积。只考虑该映射时，振幅因子包含 \(\sqrt{dA_{in}/dA_{out}}\)，即 Jacobian 的逆平方根。损耗若已在 Jones 中，不再乘进同一振幅。更实用的验算是对每个输入偏振模验证 \(\int|u_{out}|^2dA=\sum dP_{out}\)。若映射 Jacobian 接近零、翻折或多值，普通单张插值光瞳不再可靠，需分支／波动处理。

单个 Jones 传递还假定确定性的非退偏响应。粗糙表面散射、随机结构平均或器件本身的退偏若必须建模，应使用合适的场系综／相干矩阵／Mueller 统计描述；不能用任意一个 2×2 复矩阵声称覆盖所有退偏机制。

## 6 曲面到波动网格的映射

每个面上厚度 \(d_j(u_s,v_s)\) 应按真实命中点读取，角度由该处法向决定。膜厚地图若位于基底参数域，不能直接把相机像素坐标或入瞳坐标当成厚度图索引。

从曲面导出场时至少包含三步：

1. 从曲面命中点延伸到明确参考面／参考球面，加入带符号的光程修正，保持同一相位基准。
2. 将每个局部 s／p 横向基运输到一致的输出基。法向入射附近 s／p 不唯一，应采用连续基或双极基等稳定方法，不能让数值奇点产生假偏振像差。Poke 的 PRT 文档明确采用相应局部坐标转换。[Poke PRT 教程](https://poke.readthedocs.io/en/stable/notebooks/introtopolarization.html)
3. 保留光线管面积／求积权重，对非均匀出瞳点进行守恒重采样，或直接在非规则点上求积。曲面面积元 \(dA=|\partial_u\mathbf r\times\partial_v\mathbf r|du\,dv\)，投影面积和斜入射余弦必须一致。

不能只插值落点而不改相位，不能把非均匀射线密度直接解释为场振幅，也不能在跨遮挡缺口／不同路径的区域无条件平滑 Jones 元素。相位宜保留未包裹 OPD并在目标点重新构造 phasor；有真实相位跳变／涡旋时必须分区。也可插值复场，但仍须做功率和收敛验证。

倾斜／曲面探测器可在真实表面采样并用其法向 Poynting 通量积分，或者使用验证过的平面到倾斜面场变换。仅对平面强度图做图像几何扭曲，通常不是等效的场传播。

## 7 PSF OTF MTF 与偏振的定义

### 7.1 从复光瞳到振幅响应

近轴、适当参考球面已提取、固定共轭的情形，可把各 Jones 分量送入 Fourier 成像算子。均匀像方介质中记 \(\lambda_m=\lambda_0/n_{img}\)：

\[
\mathbf H_\lambda(\mathbf x)=
\frac{e^{ikf}}{i\lambda_m f}\int
\mathbf P_\lambda(\mathbf u)
\exp\left[-i\frac{2\pi}{\lambda_m f}\mathbf u\cdot\mathbf x\right]d^2u.
\]

这里忽略的全局／已知二次相位是否可忽略，取决于后续是否还要相干传播；不能在需要下一平面的复场时只保留强度。有限共轭、强畸变／瞳像差或高 NA 时，坐标映射、有效焦距和核应改用对应模型，不能只把上述 f 换成某个几何距离就宣称精确。

### 7.2 偏振状态必须进入 PSF 定义

令输入偏振相干矩阵 \(\mathbf C=\langle\mathbf e\mathbf e^\dagger\rangle\)，对偏振不分辨、近轴的探测器：

\[
g_\lambda(\mathbf x)=\mathrm{Tr}\,[\mathbf H_\lambda(\mathbf x)\mathbf C\mathbf H_\lambda^\dagger(\mathbf x)].
\]

若输入非偏振且总强度归一到 1，则 \(C=I_2/2\)，响应是两种正交入射态响应的等权强度和。若是 +45° 线偏振，两个输入分量相干，必须保留交叉项。加分析器时先在场／相干矩阵上应用分析器，再求探测量。Stokes V 和圆偏振手性的符号须跨库专门测试。

因此，通常的 Mueller pupil 不能直接 FFT 得到正确偏振 PSF：应先传播复 Jones／矢量场，再构造像面 Mueller 响应。高 NA 时会出现重要纵向电场，需包含矢量旋转和相应聚焦积分；真正穿过探测器的量是其法向 Poynting 通量。简单相加 \(|E_x|^2+|E_y|^2\) 的近轴公式不能无条件推广。

### 7.3 三种归一化分开保存

- `absolute_response`：例如每 1 W 入射对应的像面 W/m²，即数值单位 m⁻²，积分给出实际吞吐率 \(\eta_\lambda\)。
- `unit_integral_psf`：\(h_\lambda=g_\lambda/\eta_\lambda\)，积分为 1，用于描述已透过能量的空间分布。
- `peak_normalized_display`：仅供显示，不能用来加宽带、预测电子数或判断总能量。

有限 ROI 捕获的能量也必须另记。不要裁掉 PSF 尾部后重新归一到 1，再假称没有损失。Optiland FFTPSF 文档的默认标度可使等效衍射极限峰值为 100，这并不是 W/m²，导入绝对成像前必须转换。[Optiland FFTPSF API](https://www.optiland.org/docs/api/psf/psf.fft.html)

对单位积分的非相干强度 PSF：

\[
\mathrm{OTF}(\boldsymbol\nu)=\int h(\mathbf x)e^{-i2\pi\boldsymbol\nu\cdot\mathbf x}d^2x,
\quad\mathrm{OTF}(0)=1,
\quad\mathrm{MTF}=|\mathrm{OTF}|.
\]

PTF 为 OTF 相位。频率用 cycles/m 或明确换算为 cycles/mm。相干系统的振幅传递函数与上述非相干 OTF 不同。强像差点列可以给出几何近似，但“几何点列卷积 Airy”不是一般正确的替代；波前中已经包含几何像差时再卷积几何点列还可能双计像差。

Strehl 应比较相同通量归一化、相同口径／振幅条件下的像差峰值与明确的无像差参考。膜损耗、振幅 apodization 与相位像差的变化应分开报告；一个峰值数字不能同时代替吞吐率和像质。

## 8 相干 部分相干 与宽带积分

### 8.1 三种不同相加规则

1. 同一波长、同一相干模内：先加复振幅，再取模平方。孔径点、beamlets 或同源相干路径皆如此。
2. 互不相干的源点／模式：各自完整相干传播后，加非负加权强度。
3. 一般稳态宽带源配普通长曝光探测器：各频率分量的强度按光谱与响应积分，不是把不同波长复场直接相加。

脉冲、拍频／外差或超快门控若保留不同频率间可观测交叉项，应转为时域／互谱模型，保存频谱相位及探测器时间响应；“宽带一律非相干”仅对相应测量条件成立。

### 8.2 部分空间相干

一般情形需要交叉谱密度矩阵 \(W(\mathbf r_1,\mathbf r_2;\lambda)\)，局部 Stokes 场只给同一点的偏振二阶统计，不能给出不同位置的相关性。可用相干模分解：

\[
W(\mathbf r_1,\mathbf r_2;\lambda)
=\sum_m \mu_m(\lambda)\,\psi_m(\mathbf r_1;\lambda)\psi_m^\dagger(\mathbf r_2;\lambda),\quad\mu_m\ge0,
\]

\[
I_\lambda(\mathbf x)=\sum_m\mu_m(\lambda)\left|\mathcal P_\lambda[\psi_m](\mathbf x)\right|^2.
\]

模式可逐个传播并累加强度，适合 16 GB 显存。模截断需记录剩余权重和对指定 ROI／MTF 的影响；仅“总功率遗漏很小”未必保证高对比暗区相对误差很小。理论基础见 Wolf 1982 的空间频率相干模论文，出版者摘要已核实；全文访问受限，不能声称本稿逐式审计了全文。[Wolf 原论文](https://opg.optica.org/josa/abstract.cfm?uri=josa-72-3-343)

### 8.3 宽带 PSF 与电子权重

所有波长必须落到同一个**物理像面坐标网格**。普通 FFT 的像面间距随波长变化，不可直接按相同数组索引相加。可使用矩阵 DFT／CZT 指定共同输出采样，或做带面积因子的守恒重采样。[Prysm 多波长教程](https://prysm.readthedocs.io/en/v0.21/how-tos/Polychromatic%20Propagation.html)

若 \(S_\lambda\) 是入射谱功率密度、\(h_\lambda\) 单位积分、\(\eta_\lambda\) 为已单独分离的光学吞吐率，则辐射型宽带核的非归一化权重为

\[
w^{rad}_k=S_{\lambda_k}\eta_{\lambda_k}\Delta\lambda_k.
\]

光电子型有效 PSF 权重为

\[
w^e_k=S_{\lambda_k}\eta_{\lambda_k}\mathrm{QE}(\lambda_k)
\frac{\lambda_k}{hc}\Delta\lambda_k.
\]

如果输入已经是 photons/s/nm，不能再乘 \(\lambda/hc\)；如果绝对响应已经包含吞吐率，不能再乘 \(\eta\)。光谱以频率密度给出时需同时变换积分测度，不能把 per Hz 数值当成 per nm。

宽带有效 PSF 为 \(h_{eff}=\sum w_kh_k/\sum w_k\)。宽带 MTF 要先加复 OTF 再取绝对值：\(\mathrm{MTF}_{eff}=|\sum w_k\mathrm{OTF}_k/\sum w_k|\)，一般不等于单色 MTF 的加权平均。若各波段有不同像移或 OTF 相位，这一区别尤其重要。

## 9 从 PSF 到真实成像和探测器

平移不变／等晕小视场可用物体强度与 PSF 卷积。大视场、畸变、渐晕、横向色差或厚度图引入明显场依赖时，应计算 \(h(\mathbf x;\mathbf r_{obj},\lambda)\) 的 PSF 场库，在物点积分或分块近似中使用，保留每个物点的真实像移和通量。不能用中心 PSF 卷整张图后称为完整成像。

对像素 p，理想光电子均值为

\[
\bar N_{e,p}=\int_{t_0}^{t_0+T}\int d\lambda\,
\mathrm{QE}_p(\lambda)\frac{\lambda}{hc}
\int_{A_p}\!E_\lambda(\mathbf x,t)\,R_p(\mathbf x,\lambda)\,dA\,dt.
\]

\(E_\lambda\) 为像面谱辐照度，\(R_p\) 为声明好归一化的像素响应／填充率，QE 与 R 中不能重复包含同一损耗。之后才考虑光子散粒噪声、暗电流、读出噪声、PRNU／DSNU、满阱／饱和、转换增益和 ADC。增益要注明 e⁻/DN 还是 DN/e⁻。Poisson 是常用光电计数假设，不包含所有热光聚束、EM 增益或器件相关噪声情形。

EMVA 1288 Linear 4.0 可用于参数定义和线性传感器验收，尤其是 QE、系统增益、暗噪声、饱和和线性响应；本模型并不会因采用这些名词而自动“符合 EMVA”。[EMVA 官方标准及下载](https://www.emva.org/standards-technology/emva-1288/emva-standard-1288-downloads-2/)、[EMVA Linear 4.0，第 6 与第 9 节](https://www.emva.org/wp-content/uploads/EMVA1288Linear_4.0Release.pdf)

Prysm 的 `Detector.expose` 接收 **e⁻/s** 的 aerial image，QE 应已体现在其标度中；输出 DN。它不能直接接收一张峰值归一 PSF。[Prysm detector API](https://prysm.readthedocs.io/en/latest/api/detector.html)

像素积分先于离散采样。矩形像素的 presampling MTF 是相应 sinc 因子；在平移不变前提下可与光学 OTF 相乘。但离散图像还受 Nyquist 和 alias 影响，不能把“光学 MTF × 像素 MTF”无条件当成完整数字图像的唯一 MTF。

## 10 传播算法选择

| 方法 | 适用场景 | 主要边界及验证 |
|---|---|---|
| FFT Fraunhofer／瞳到焦 | 规则采样出瞳、近轴成像、许多视场和波长的基准 PSF | 必须正确去除参考载波；输出间距受输入网格约束；大瞳像差和高 NA 要另评估 |
| 矩阵 DFT／CZT | 共同物理像素网格、多波长、只需焦面小 ROI | 仍是所选衍射模型；不能因采样灵活就修复错误近似；ROI 外能量另计 |
| Fresnel | 近轴多平面、离焦、光阑之间有限距离传播 | 需验证近轴展开误差及输入／输出采样；Fresnel 数本身不能替代角度／相位误差判断 |
| 角谱 ASM | 均匀介质中平行平面的局部自由传播，需超出 Fresnel 的传播角度精度时 | 精确标量核不等于全 Maxwell 系统；FFT 周期边界、传递函数采样和倏逝波策略都要指定 |
| Huygens／Rayleigh–Sommerfeld 求积 | 非规则出瞳、指定像面位置、曲面／离轴验证、小 ROI 的高精度参考 | 核、倾斜因子、面积权重、矢量或标量必须明确；计算量约为源采样点数乘目标点数 |
| 矢量聚焦积分 | 高 NA、纵向场和显著偏振耦合 | 使用正确的 aplanatic／实际光线映射及 apodization；不是把标量场改成数组最后一维 3 即可 |
| Gaussian beamlet | 曲折／离轴系统、局部光束沿几何路径运输、部分需要越过焦散的混合模型 | 每个 beamlet 仍有局部近似、分解宽度／重叠和边缘误差；相干重构及分块收敛需验证 |

角谱传播的典型核为

\[
H(f_x,f_y;z)=\exp\left[i2\pi z\sqrt{(n/\lambda_0)^2-f_x^2-f_y^2}\right].
\]

必须选对复平方根／传播方向，说明倏逝项保留、衰减还是滤除；反向传播可能放大倏逝或噪声分量。除了零填充，还要控制传递函数的离散采样误差。Matsushima 与 Shimobaba 的 band-limited ASM 原论文专门讨论该问题，不应把“用了 FFT 角谱”视为自动无 alias。[原论文 DOI](https://doi.org/10.1364/OE.17.019662)、[作者机构存档](https://kansai-u.repo.nii.ac.jp/record/11127/files/KU-1100-20091015-50.pdf)

Poke 的论文给出 Rayfront、PRT 和 beamlet 的整体架构以及分块计算思路；这可作为本路线的 primary 设计依据。不同于一次性整场 FFT，beamlet 或直接 Huygens 大数组应按源点及目标点分块，不能为向量化而生成不可承受的全连接张量。[Ashcraft 等 2023，§2、§3、§4.2](https://arxiv.org/html/2309.04649v1)

## 11 采样收敛及能量验证

### 11.1 分开控制四种采样

1. **几何／厚度采样**：覆盖局部膜厚变化、入射角、遮挡边界和 Jacobian；仅增加 FFT padding 无法补回漏掉的膜厚细节。
2. **光瞳复场采样**：解析最短波长及最大的残余相位梯度。相邻相位变化小于 π 是基本警示线，更保守的 π/2 可作初始设计条件，但仍需收敛测试。未解析的硬边缘和周期结构不能靠此单指标保证准确。
3. **像面采样／视场范围**：规则 FFT 有 \(\Delta x=\lambda_m f/(N_{FFT}\Delta u)\)。零填充使像面采样更密，并不提高原始光瞳信息分辨率；增大真实光瞳采样与增大 padding 是两种不同实验。
4. **谱／视场／相干模采样**：按涂层窄带结构、材料色散、PSF 变化和探测器 QE 加密；不能一律固定三色或九个波长。

非相干无像差成像的光学截止频率为 \(2\mathrm{NA}/\lambda_0\)。要无 alias 地采样其完整带宽，像面间距应满足 \(\Delta x\le\lambda_0/(4\mathrm{NA})\)，空气近轴下约为 \(\lambda_0F\#/2\)。最短波长通常给出最严格采样。实际传感器可故意欠采样，但模拟必须显示其 alias，而不是把粗网格生成的假 MTF 当成器件性质。

### 11.2 必须建立的基准

| 基准 | 必查结果 |
|---|---|
| 均匀圆孔无像差 | Airy 第一暗环与包围能量，圆孔解析非相干 MTF，频率尺度 |
| 纯 piston／tilt | piston 不变 PSF；tilt 仅按符号和尺度位移，不改变固有像质 |
| 已知 defocus／astigmatism | 符号、轴方向、焦前焦后对称关系及跨传播器一致性 |
| 无涂层单界面 | s／p 透反系数、Brewster／全反射边界、正确功率因子 |
| 均匀膜与空间变化膜 | 均匀极限一致，厚度导致的振幅及相位都生效，无双计 |
| x／y／45°／圆偏振及非偏振 | 基底旋转不变性，交叉项，V 符号，正交态平均 |
| 不同谱表示 | W/nm 与 photons/s/nm 转换后相同电子数，Δλ 不重复／不遗漏 |
| Fourier 与 Huygens 小模型 | 同一参考、单位、孔径、归一化下，允许近似范围内结果收敛 |
| 曲面映射／离轴 | 光线管功率与网格积分一致，孔径遮挡和实际像移保存 |
| 无损局部传播 | Parseval／总通量守恒；加遮挡后丢失量可解释 |
| 探测器 | 曝光倍增使均值倍增，Poisson 方差／读噪声叠加、增益与饱和定义正确 |

每次分别把光瞳采样加倍、padding 加倍、ROI 扩大、波长节点加密、相干模数增加。比较峰值、包围能量、指定频点 MTF、总通量、像移及必要的暗区绝对误差。可先设“关键指标变化 <1%”作为普通成像项目的初始工程门槛，再由用途调整；高对比、相位测量或严苛公差任务需更严且不同形式的误差预算。这里的 1% 是建议，不是论文背书或本项目已通过结果。

应独立记账：输入、孔径截断、已计算的反射／透射、体吸收、输出窗口外泄和数值残差。当前无反射分支／体吸收时，账本要明确未建模项，不能靠末端归一化掩盖。

## 12 16 GB 显存与 32 GB 内存的离线方案

本硬件的合理策略是逐视场、逐波长、逐相干模处理并缓存必要中间结果，而非同时驻留整个四维／五维数据集。

- float64 生成几何差分光程、参考面和膜系计算基准，避免用 float32 从米级总 OPL 相减获取纳米级 WFE。最终复场是否可降为 complex64，需按指标验证。
- 单个 2048² complex64 数组约 32 MiB，complex128 约 64 MiB；四个 Jones 通道分别约 128／256 MiB。4096² 时单通道约 128／256 MiB，四通道约 512 MiB／1 GiB。这里只算数组本体，FFT workspace、补零、临时矩阵、缓存和自动微分图都会增加占用。
- 8192² 的四个 complex128 通道已约 4 GiB；再加两倍线性 padding 会乘四，不能按裸数组大小规划 16 GB GPU。
- 初期一次只放一个视场和波长，按必要的 1／2／4 复通道执行，立即累积到共同物理网格的强度／电子率。只有确认显存余量后再小批量并行。
- 生产正向推演无须保留 autograd 图。需要优化时单独预算 checkpoint、梯度与优化器状态。
- 保存未包裹 OPD、复 Jones pupil、mask、坐标、归一化、吞吐率、配置哈希和收敛摘要。完整面间场仅对选定诊断工况保存；避免保留所有波长的全部大阵列。
- 将 CPU double 结果作为回归参考；GPU 功能逐调用测试，不以库宣称的后端能力推定本模型正确。
- 初始 grid 可从 256／512 入瞳、适当 padding 和小焦面 ROI 起步，按物理细节和收敛门槛增长至 1024／2048 等。不存在适合所有光学系统的固定“成熟版网格”。

几何／TMM、光瞳重采样、传播、谱与模式积分、探测器应独立计时并报告峰值显存和误差。对 4070 Ti Super 的速度只能由该流程实测；其他 GPU、论文仪器或不同光学问题的速度不可迁移成承诺。

## 13 分阶段交付与验收

### 阶段 A 单色标量主透射成像

新增差分 OPL、输入相干模、参考面、复振幅和孔径面积权重。接通 CPU Fourier／DFT PSF，完成圆孔、tilt、defocus、能量和采样基准。产物命名清楚区分 geometric irradiance 与 diffraction PSF。

### 阶段 B 空间涂层与偏振成像

将位置相关 TMM 的复系数、局部偏振基和路径相位接入 Jones pupil，完成正交／斜线／圆偏振、均匀膜与非均匀膜验证。交付 polarization-conditioned PSF 和吞吐率，不只交付 T／R 热图。

### 阶段 C 宽带非相干物体与探测器

共同物理网格上的谱积分，场依赖 PSF 库，像素积分及电子数链。明确物光谱、QE、色差与通量权重。用真实单位检验曝光、增益和噪声，形成可离线重跑的配置及结果包。

### 阶段 D 经验证的 GPU 与局部波动扩展

先让通过的 CPU 模型逐模块转到 CuPy／PyTorch，做精度与显存回归；再按具体失效工况增加 ASM、Huygens 或 beamlet 子系统。不要为了“全波”标签把全部系统替换成昂贵且未验证的网格求解。

### 阶段 E 有明确需求再加入多路径与部分相干

增加可审计反射分支、体吸收、相干路径图、谱相干处理和相干模分解。分支数量、截断阈值、相干假设及遗漏功率都必须进入误差预算。此阶段需要新增物理，不应从现有 TMM 推导出已实现的错觉。

## 14 可直接引用的 primary 资料清单

以下均为论文出版者／作者存档或项目官方资料，按用途定位：

1. [Ashcraft 等，Poke: an open-source ray-based physical optics platform，2023](https://arxiv.org/html/2309.04649v1)：§2 Rayfront 数据，§3.1 GBD，§3.2 PRT，§4.2 CuPy／JAX。与几何—波动桥直接相关；软件开源，但示例光追来源含商业 API。
2. [Poke Jones pupil → HCIPy／POPPY 官方 notebook](https://poke.readthedocs.io/en/latest/notebooks/jonespupils.html)：局部坐标转换和复 Jones pupil 传播实例。
3. [HCIPy Performance](https://docs.hcipy.org/dev/performance.html)：NewStyleField／Array API GPU 明确实验性；应引用这个限定，而不是只引用“支持 GPU”。
4. [HCIPy Wavefront API](https://docs.hcipy.org/dev/api/hcipy.optics.Wavefront.html)：标量、Jones 向量、两组 Jones 场加输入 Stokes，以及 intensity／power 的区别。
5. [Prysm GPU and Exascale Computing](https://prysm.readthedocs.io/en/latest/how-tos/GPU%20and%20Exascale%20Computing.html)：后端替换和精度设置，本文不转用其中速度宣传作为本机预测。
6. [Prysm Polychromatic Propagation](https://prysm.readthedocs.io/en/v0.21/how-tos/Polychromatic%20Propagation.html)：不同波长的共同物理输出网格及强度积分。旧版本示例，应配合目标版本 API 与归一化测试。
7. [Prysm Radiometrically Correct Modeling](https://prysm.readthedocs.io/en/stable/how-tos/Radiometrically-Correct-Modeling.html)：Parseval、积分／峰值归一化和裁剪导致的能量变化；不直接照抄其特定二值孔径缩放到一般复场。
8. [Optiland Wavefront Analysis](https://www.optiland.org/docs/api/api_wavefront.html) 与 [ReferenceGeometry](https://www.optiland.org/docs/api/wavefront/optiland.wavefront.reference_geometry.html)：公开 OPD、平面／球面参考、标量／矢量 PSF 分类。
9. [Matsushima 与 Shimobaba，Optics Express 17，19662–19673，2009](https://doi.org/10.1364/OE.17.019662)：band-limited angular spectrum 的采样问题；[作者机构副本](https://kansai-u.repo.nii.ac.jp/record/11127/files/KU-1100-20091015-50.pdf)。本次机构 PDF 访问出现限流，结论由可检索的论文摘要与书目信息核实，不声称完成全文数值复现。
10. [Wolf，JOSA 72，343–351，1982](https://opg.optica.org/josa/abstract.cfm?uri=josa-72-3-343)：交叉谱密度的相干模表示；出版者摘要可读，全文本次未获开放访问。
11. [PBRT 4e Radiometry](https://pbr-book.org/4ed/Radiometry%2C_Spectra%2C_and_Color/Radiometry)：作者官方教材／实现文档，谱辐亮度、通量、辐照度与积分单位。
12. [EMVA 1288 Linear 4.0](https://www.emva.org/wp-content/uploads/EMVA1288Linear_4.0Release.pdf)：光子、光电子、QE、增益与相机噪声参数的官方定义。

最终验收重点不是“同时集成了几个库”，而是同一输入物理问题在相同参考、单位、权重、相干假设和采样精度下，几何功率账、波动通量账和探测器电子数账能够闭合，并且对所需像质指标收敛。
