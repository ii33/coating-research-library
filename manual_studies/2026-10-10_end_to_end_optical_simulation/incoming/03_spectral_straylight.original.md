# 光学生产仿真成熟版：非顺序光谱、偏振、鬼像与杂散光研究

核验日期：2026-10-10。研究范围：公开官方文档、固定提交源码与原始论文；未安装运行这些引擎，未对 4070 Ti SUPER 做性能测试，未修改用户 Windows、远程服务或发布任何内容。

## 一、结论先行

建议保留现有“沉积逐层厚度场 d_i(x,y) → 局部薄膜求解”的资产，把成熟版分成三个相互校验的物理层：

1. **局部相干散射算子**：由膜层求解器返回位置、入射方向、波长、入射侧相关的复振幅 r_s、r_p、t_s、t_p，必要时完整 Jones 矩阵。薄膜内干涉在这里求解，不把几十层膜转换成几何光追的几十次可见界面。
2. **全机非相干光谱/偏振输运**：用非顺序几何求交、Stokes/Mueller、体吸收、表面散射及统计估计处理源、镀膜镜片、镜筒、光阑、传感器反射和鬼像。首选考察 Mitsuba 3/Dr.Jit 为底座，但膜层 BSDF、色散折射、光学曲面和工程探测器仍需定制。
3. **选定相干通道的波动成像**：从主像或指定鬼像路径的复瞳函数计算 PSF/MTF。激光、相干鬼像和干涉仪不能靠相互独立的 Stokes 路径强度相加。只对有需要的区域与路径升级为波动/全波计算。

**四个不能混淆的产品事实**：

- Mitsuba 的 `thindielectric` 不是多层干涉薄膜；其固定提交源码以强度几何级数得到等效反射，传输方向不变，并输出去偏振量。[固定源码](https://github.com/mitsuba-renderer/mitsuba3/blob/ab3e3b18445963707d83f2b31d3db0c1f5b7688f/src/bsdfs/thindielectric.cpp)
- Mitsuba 的普通 `dielectric` 使用标量折射率；“光谱渲染”不等于该现成 BSDF 已有色散 Snell 追迹。[固定源码](https://github.com/mitsuba-renderer/mitsuba3/blob/ab3e3b18445963707d83f2b31d3db0c1f5b7688f/src/bsdfs/dielectric.cpp)
- PBRT-v4 默认四个 `SampledSpectrum` 分量是四个采样波长，不是 I/Q/U/V；现成核心是标量光谱输运。[固定源码](https://github.com/mmp/pbrt-v4/blob/b4ce9687e6c695f5582997c61b0c66cf064bdb4a/src/pbrt/util/spectrum.h)
- Optiland NSQ 的开发文档已存在，但明确尚未进入任何 tagged release；此实现没有偏振、体散射或 BVH。顺序引擎有偏振/薄膜模块，不意味着 NSQ 已支持。[固定状态说明](https://github.com/optiland/optiland/blob/4e893f53aee1312f2d091680b93dd2279711e197/docs/gallery/nonsequential/limitations_and_roadmap.rst)

以下“可复用”表示已有公开接口或实现，不表示未经验证即可用于生产验收。“建议”及预算均是工程推断。

## 二、四个候选底座的实际边界

### 2.1 Mitsuba 3 / Dr.Jit：优先的可扩展输运底座

**已核验可复用**：非顺序场景求交、GPU/CPU 后端、光谱变体、路径采样、部分偏振 BSDF、Stokes 输出、可自定义 Python/C++ BSDF、传感器和积分器。Python 自定义 BSDF 的关键接口为 sample/eval/pdf，JIT 变体可对数组编译，而非每条光线跑 Python。[自定义插件教程](https://mitsuba.readthedocs.io/en/latest/src/others/custom_plugin.html)

**偏振边界**：官方列出光滑介质、光滑/粗糙导体、偏振器/延迟器及 measured_polarized 等；其余未覆盖 BSDF 会去偏振。现成发光体为非偏振发射，偏振体散射没有实现。`volpath` 可处理表面偏振，并不等价于偏振介质散射。[偏振文档：Feature list](https://mitsuba.readthedocs.io/en/latest/src/key_topics/polarization.html#feature-list)

**薄膜边界**：`thindielectric` 无逐层 d/n/k 参数，无膜厚相位；代码采用 r_eff=2r/(1+r)、t_eff=1-r_eff。它用于几何厚度忽略的玻璃片，不能代替 AR/HR/窄带滤光片。`specular_reflectance` 纹理也只是现有模型的乘子，不是替换 Fresnel 的完整膜层算子。直接把 R_TMM 填入会有重复乘 Fresnel、错误透射或偏振相位丢失的风险。[源码](https://github.com/mitsuba-renderer/mitsuba3/blob/ab3e3b18445963707d83f2b31d3db0c1f5b7688f/src/bsdfs/thindielectric.cpp)

**必须自定义**：多层膜复振幅替换、每波长折射方向、解析非球面/自由曲面、绝对辐射度探测器及路径来源标签。使用已有玻璃几何时，前后表面的介质侧和涂层顺序必须独立处理。粗糙介质偏振、任意偏振源、偏振体散射不能当现成功能承诺。

**逆向优化限制**：官方 `prb`、`prb_projective`、`prbvolpath` 等明确不支持跟踪偏振的变体；基础 PRB 的 detached sampling 对理想镜面 IOR 优化另有局限。因此“偏振＋端到端可微＋PRB恒定路径内存”不是现成可叠加开关。[积分器文档：PRB](https://mitsuba.readthedocs.io/en/latest/src/generated/plugins_integrators.html#path-replay-backpropagation-prb)

### 2.2 PBRT-v4：标量光谱参考与采样实现来源

**已核验可复用**：C++ CPU/GPU 光谱路径/体输运、微表面和实测 BRDF、重要性采样及物理相机。官方仓库说明 GPU 路径依赖 CUDA/OptiX，支持 Linux/Windows。[仓库 Features / Using pbrt on GPU](https://github.com/mmp/pbrt-v4)

**薄层限制**：`ThinDielectricBxDF` 对理想薄介质成对界面内部反射作强度求和，并非多层电磁 TMM；“layered material random walk”也不能直接解读为相干干涉层。[PBRT §9.5 Dielectric BSDF](https://pbr-book.org/4ed/Reflection_Models/Dielectric_BSDF)

**需要自定义的工作量**：现成 `SampledSpectrum` 为实值逐波长能量，偏振要改 throughput、BSDF、坐标框架和积分器契约，不能只替换一个 Fresnel 函数。故当偏振是产品核心要求时，Mitsuba 起点更合适；PBRT 适合非偏振独立结果对照、学习波前队列/采样/数值鲁棒性，或团队已有较强 C++ 基础的路线。[光谱核心源码](https://github.com/mmp/pbrt-v4/blob/b4ce9687e6c695f5582997c61b0c66cf064bdb4a/src/pbrt/util/spectrum.h)

### 2.3 Raysect：辐射度与观测器参考

**已核验可复用**：科学射线追踪、光谱材料、辐射度观测器、像素/功率/光谱流水线与统计误差。它把 observer 的谱采样转成 power/radiance，并提供 mean/error，适合构建小型独立标量验算器。[Sampling and Observers](https://www.raysect.org/observers.html)、[Pipeline API](https://www.raysect.org/api_reference/optical/pipelines.html)

**偏振不应宣称已有**：检查其 dielectric 源码，Fresnel 为 s/p 反射强度平均，再按分支概率追迹；本次未发现现成端到端 Stokes/Mueller 输运，不能因“scientific optics”就视为支持相干偏振。[固定 dielectric.pyx，第305行附近](https://github.com/raysect/source/blob/5ed9a21b5f6ec10b71e187d51da2b430bdc65e20/raysect/optical/material/dielectric.pyx)

**部署边界**：官方 README 仍写 Linux only；不应承诺原生 Windows 现成安装或 CUDA 加速。对用户本机，优先作为将来经授权的 Linux/远程参考实现，不作为必须新增的服务端项目。[官方仓库](https://github.com/raysect/source)

### 2.4 Optiland 非顺序：值得跟踪，但不能用顺序功能代替 NSQ 核验

**已核验开发实现**：NSQScene、NumPy 分批前向引擎、Torch 梯度引擎；有 Lambertian、Harvey-Shack、tabulated BSDF；有反射/折射重要性偏置、NumPy 有界分裂、俄轮盘、Beer–Lambert 体吸收及通量诊断。[开发文档](https://optiland.readthedocs.io/en/latest/developers_guide/nonsequential_raytracing.html)

**明确缺口**：无 NSQ 偏振/体散射/BVH；每反弹求交为 rays×surfaces；Torch 为完整 autograd 图，内存随 rays×depth 增长；可见性梯度缺失；Dr.Jit/Mitsuba/OptiX 后端仍在 roadmap。官方写的射线数量适用范围不是该用户显卡性能测试，不在本报告中转换成预计速度。[固定限制源码](https://github.com/optiland/optiland/blob/4e893f53aee1312f2d091680b93dd2279711e197/docs/gallery/nonsequential/limitations_and_roadmap.rst)

**进一步源码发现**：RefractiveComponent 显式拒绝 BaseCoatingPolarized，因为 NSQ rays 没有偏振态；接入 SimpleCoating 时将 reflectance/transmittance 转为 float 常数。不能认为现成 NSQ 已能计算 d_i(x,y)、角度和 λ 联动的 ThinFilmCoating。反射面支持随波长 callable 的能力也不能外推成折射镀膜面完整能力。[固定 refractive.py](https://github.com/optiland/optiland/blob/4e893f53aee1312f2d091680b93dd2279711e197/optiland/nonsequential/components/refractive.py)

**定位建议**：继续用 Optiland 支撑顺序设计、OPD/PSF 等适合的环节；NSQ 用作小场景算法参考或未来替代后端评估，先不要作为成熟偏振杂散光唯一计算核。

## 三、薄膜算子如何接入，哪些物理量不能丢

### 3.1 建议的接口契约

CoatingResponse(surface_id, uv, λ_vacuum, incident_direction, incident_medium, outgoing_medium, temperature_or_process_state)

返回：

- local_basis：入射与出射 s/p 基底；明确法向、传播方向及圆偏振符号约定
- r_s、r_p、t_s、t_p 的实部与虚部；各向异性时返回完整 2×2 Jones R/T
- 功率归一化 R/T/A，或者可重建它们的端口导纳；单位、膜层顺序及适用域
- 对应反射/透射方向、体介质 ID；散射模型另用明确能量预算连接
- 有效性标志：插值出界、TIR、无实传播端口、异常材料、数据来源版本

这不是某库现成 API，是为项目建议的边界。现有 TMM 可继续使用；强吸收/厚层/多层场景宜用数值稳定的散射矩阵或稳定递推验算，不要求全机求解 Maxwell 方程。

### 3.2 从复振幅到 Mueller

对各向同性平面膜，在相容基底下 J_R=diag(r_s,r_p)。透射需要先按电场定义和端口导纳作通量归一化：T_q=Re(Y_out,q)/Re(Y_in,q)×|t_q|²（q=s,p；Y 与采用的切向场振幅定义配套）。不能普遍用 |t|² 当功率，也不能在吸收性入射介质中生搬非吸收公式。

有了归一化 Jones J，可用 M_ij=½ Tr(σ_i J σ_j J†) 转换 Mueller（σ 的排列与 V 符号必须固定）。例如相对相位 arg(r_p)−arg(r_s) 决定 U/V 的耦合，只保留 R_s、R_p 会丢失这一项。局部矩阵还须旋转到引擎路径使用的入射/出射参考框架。Mitsuba 的 mueller.h 提供基底旋转及复 Fresnel 构建的参考实现。[固定 mueller.h](https://github.com/mitsuba-renderer/mitsuba3/blob/ab3e3b18445963707d83f2b31d3db0c1f5b7688f/include/mitsuba/render/mueller.h)

工程接口要区分“通量光子包”与“辐亮度 BSDF”。前者透射分支乘 T；后者还遵守折射的立体角雅可比与 radiance/importance 模式约定，可能含 η² 因子。应沿用宿主引擎 transport mode，不额外重复乘或漏乘。反向追迹还须处理反向涂层顺序、正确邻接介质和伴随偏振约定。[Mitsuba dielectric 源码](https://github.com/mitsuba-renderer/mitsuba3/blob/ab3e3b18445963707d83f2b31d3db0c1f5b7688f/src/bsdfs/dielectric.cpp)

### 3.3 色散与空间膜厚

- 每次命中从同一曲面的材料坐标 uv 查 d_i(uv)，而不是世界坐标直接插值；旋转、去心与非球面必须保持沉积场到光学面的映射。
- 若 n(λ) 改变折射方向，不能把多个不同波长绑在同一几何射线而忽略方向差异。最小正确实现可按单波长批次运行；成熟采样可用有正确 PDF 补偿的 hero wavelength/分束策略。
- 复振幅插值与插值后守恒需做误差测试；直接线性插相位会遇到 ±π 跳变。可插实虚部并检查物理性，或解包相位，但零点附近仍需加密。
- R/T 谱的窄峰、截止边、临界角及 Brewster 附近要自适应加密，不能以 RGB 或少数固定波长判定窄带滤光性能。
- 局部平膜假设要求横向变化相对波长及相关传播尺度足够慢。周期结构、陡峭厚度梯度、亚波长图案、衍射光栅、强近场耦合需要局部 RCWA/FDTD/FEM 或衍射算子，再把散射结果接回全机。
- 已由局部 TMM 合并的薄膜内反射不能再次生成显式几何分支；厚基底与空气隙则要按相干长度决定保留几何非相干反射，还是进入相干腔模型。

这些是工程推断，应通过局部相干模型和整机能量预算交叉验证。

## 四、Stokes/Mueller 与 Jones 的相干边界

Stokes 可描述非偏振、部分偏振、全偏振光；每条路径由 Mueller 作用，独立路径在同一探测器基底下加 Stokes。该操作保留单路径内部的偏振相对相位，但已不保留不同几何路径间的共同载波相位和互相干项。

因此：

- 宽谱照明、路径光程差显著超过相干长度、时间/空间平均足够充分的普通鬼像和杂散光，可按强度相加。
- 激光照明、窄线宽源、等光程多反射、平行板 etalon、干涉仪与相干散斑，必须保留各相干组的 E 场、OPL、源相干信息，并在探测器按 |ΣE|² 求强度；部分相干则需相干模态或互相干表示。
- 不同 λ 的非相干光谱贡献通常在探测后积分；不能把所有波长 E 直接混加。
- Jones 处理确定性完全偏振场，本身也不会自动生成衍射 PSF。必须有瞳面采样、传播积分、空间相位与足够带宽；宏观几何光追里仅记录 Jones 矩阵还不够。

这里不是要求全机全波：可用几何光追找主路径与重要鬼像，用局部复膜层系数修正复瞳，再对选定通道用标量/矢量衍射。高NA或强偏振耦合时需矢量传播。Mitsuba 2 论文中的 coherent MCMC 是计算中光线路径束的一致性采样，不应仅凭名称误读为电磁相干干涉求解。[原论文项目页](https://rgl.epfl.ch/publications/NimierDavidVicini2019Mitsuba2)

## 五、反射分支爆炸、罕见路径与采样策略

### 5.1 不全展开，不无声截断

每面保留反射和透射会在 k 个事件后产生最多 2^k 个分支；反弹/回访使路径组合更大。建议混合：

1. 对主像与最重要的低阶鬼像，枚举/约束表面序列，并作有限分裂，获得低噪声可审计结果。
2. 对剩余高阶、多散射、镜筒漫反射路径，用蒙特卡罗单分支和重要性采样。
3. 对关键低反射路径，提升选中概率 q，同时将反射权重乘 R/q、透射权重乘 T/(1−q)。对 Mueller 使用 M_R/q 与 M_T/(1−q)，q 必须非负并覆盖非零贡献，不能把带符号的 Q/U/V 当概率。
4. 低权重路径使用俄轮盘：存活概率 p 后将存活贡献除以 p。全扔掉小贡献是有偏阈值截断；俄轮盘无偏只在估计器补偿正确时成立。
5. 任何最大深度、最大队列、贡献夹紧都要报告截断或偏差。队列满时不可静默丢射线；用额外批次或有权重补偿的抽样。

重要性采样/分裂/俄轮盘的理论参考为 PBRT §2.2 与 Veach 的 MIS/BDPT 路径空间框架。[PBRT Improving Efficiency](https://pbr-book.org/4ed/Monte_Carlo_Integration/Improving_Efficiency)、[Veach thesis](https://graphics.stanford.edu/papers/veach_thesis/)

### 5.2 常规路径追踪并非对所有光学系统都高效

从像素逆追只看得到有效口径的一小部分光源；纯镜面链、小光源、窄角源和 SDS 路径可能极难随机命中。普通下一事件估计不能穿过折射面，把光源与当前点直线相连也不满足 Snell。渲染几乎全黑不代表杂散光不存在。

工程优先顺序：

- 光源正向发射适合算整体通量、照明均匀性和部分离轴源杂散光；探测器反向适合限定 ROI/像素。
- 对已知镜片组、低阶鬼像表面序列，定向采样入口瞳/出口瞳、限制事件类型，准确乘回序列概率与采样雅可比。
- 漫反射/散射连接用 BSDF 与源/探测器重要性多策略组合，明确 MIS 的测度；delta 镜面分布不可直接当普通连续 PDF。
- 高阶镜面链再考虑 manifold sampling 或其引导方案。它们是可研究/移植的算法，不能声称当前 Mitsuba 3 一键成熟支持全部镜片鬼像。
- 按路径类别分别积累：主像、反射次数/表面组合、镜筒散射、镜片散射、传感器回反，防止总通量稳定掩盖很弱但关键的鬼像。

相关原始研究专门解决纯镜面/近镜面连接难题：[Specular Manifold Sampling, 2020](https://rgl.epfl.ch/publications/Zeltner2020Specular)、[Slope-Space Integrals, 2020](https://rgl.epfl.ch/publications/Loubet2020Slope)。本项目是否值得移植，取决于基准场景的方差和维护成本。

### 5.3 罕见路径的“未发现”不是上界

若某等权 Bernoulli 事件概率为 p，普通采样相对误差量级约 1/√(Np)；p=10⁻⁸ 而想达约10%相对误差，需要约10¹⁰个独立试验这一量级。它只是统计示意，不是本机速度预测。零次命中在适用的独立 Bernoulli 条件下可给约3/N的95%概率上界；对重要性加权、高相关分裂样本或高尾权重，不能直接套这个公式。

建议对弱鬼像做强制路径/分层采样，独立种子批次估方差，保存每路径类别贡献、最大权重和有效样本量，并与小场景确定性分裂结果对照。必要时报告“在当前采样方案下尚未建立足够低的检测上限”。

## 六、粗糙度、实测 BRDF/BSDF 与体效应

### 6.1 输入应是光学数据，而非视觉粗糙度旋钮

BRDF 的单位为 sr⁻¹，半球反射比例为 ∫f_r cosθ_o dΩ_o；BTDF 也需与采用的通量/辐亮度测度一致。实测表要记录 λ、θ_i/φ_i、θ_o/φ_o、位置、偏振基底、是否包含镜面峰、角分辨率、检测下限和校准不确定度。[NIST MIST 定义](https://pages.nist.gov/ScatterMIST/docs/Introduction.htm)、[NIST SP250-101](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.250-101.pdf)

只有一个 RMS 粗糙度 σ 不能唯一确定散射尾部；还需要相关长度/PSD/各向异性或实测散射分布。GGX/Beckmann 的 α 是模型参数，不能无条件等于 nm 级 RMS。生产镜面的低角散射和宽角尾部应优先用实测 BRDF/BTDF；缺数据时可按适用条件使用 PSD/Rayleigh–Rice/Harvey–Shack 等，并把模型误差显式列出。[Harvey–Krywonos 原始工作](https://opg.optica.org/abstract.cfm?uri=oic-2007-ThA4)

Mitsuba/PBRT 可借用实测材质表示与采样框架；Dupuy–Jakob 的工作把实测光谱 BRDF 的存储和重要性采样统一，是方法来源，而不是用户镀膜材料的自动数据库。[2018论文与代码/数据入口](https://rgl.epfl.ch/publications/Dupuy2018Adaptive)

偏振散射应输入 Mueller BRDF 或经校验的 pBSDF，不能先拟合标量 BRDF 再假定偏振保持。Mitsuba `measured_polarized` 对接的原始研究提供偏振反射测量/建模参考，但实际工业镀膜仍需自己的材料数据。[Baek 等，2020](https://rgl.epfl.ch/publications/Baek2020Image)

### 6.2 能量记账避免重复

若 TMM 假设光滑界面，而另加散射瓣，必须重新分配 specular、diffuse/scatter 与 absorption 的能量，不能在完整 R+T 后额外加散射能量。若实测 BSDF 已含镜面峰，也不能再加一份 Fresnel delta。每个入射条件要验算 R_spec+R_scatter+T_spec+T_scatter+A≈1。

Belcour–Barla 的薄膜微表面论文说明局部干涉可以嵌入微表面模型；其目的含实时彩色外观和频谱抗混叠，不可不经验证就替代工业任意多层膜设计与相位误差预算。[原始论文](https://belcour.github.io/blog/research/publication/2017/05/01/brdf-thin-film.html)

### 6.3 体吸收先做，体散射按需求扩展

基底体吸收为 exp(−α(λ)ℓ)，在常见复折射率约定下 α=4πκ/λ。ℓ 和 λ 必须同单位；玻璃 n、κ 的批次/温度/波段来源要保存。常规非二向色吸收可等比例缩放所有 Stokes 分量。

体散射需要 σ_s、σ_a 与相函数，不是把透射减少就算完成。Henyey–Greenstein 是标量方向模型，不能自动代表偏振 Mie/Rayleigh 散射。需要偏振时，体散射 Mueller 相函数、参考系与估计器均要定制；二向色吸收/双折射体传播也不能简化为单一 Beer–Lambert 系数。

## 七、光源到探测器的绝对单位与统计

以下是建议统一的数据契约与验算公式，不直接采用渲染器 RGB 输出当工程通量。

- 几何统一米；存储接口可用 mm，但只在边界转换。λ统一真空 nm 或 m，字段显式标注。Raysect 的约定为长度 m、波长 nm、谱辐亮度 W·m⁻²·sr⁻¹·nm⁻¹；Optiland NSQ 则为长度 mm、λ μm、通量 W，两者不可无转换混用。[Raysect Conventions](https://www.raysect.org/conventions.html)、[Optiland Units convention](https://optiland.readthedocs.io/en/latest/developers_guide/nonsequential_raytracing.html#units-convention)
- 光源输入选 L_e,λ(x,ω) [W·m⁻²·sr⁻¹·nm⁻¹]、I_e,λ [W·sr⁻¹·nm⁻¹] 或 Φ_e,λ [W·nm⁻¹]，不要混为“强度”。面源要有面积和角分布；远场 LED 曲线不能直接代表近场源的空间-角度相关性。[PBRT Radiometry](https://pbr-book.org/4ed/Radiometry%2C_Spectra%2C_and_Color/Radiometry)
- 对面源从联合 PDF p_A,Ω,λ 采样，单样本无1/N的功率贡献为 X=L_e,λ cosθ_e/p_A,Ω,λ，最终用 (1/N)ΣX×路径权重×命中指示。若光子包初始权重已包含1/N，最后不能再除一次。联合分布可分解为条件 PDF，不能把相关的源错误当独立。
- 正向“携带功率”的包命中探测器后，把它的 W 累加即可；不要又乘入射 cosθ。其几何投影已由采样/相交含入。反向辐亮度积分则需要 ∫L_i,λ cosθ_d dΩ dA dλ。
- 像素平均辐照度 E=Φ_pixel/A_pixel，单位 W/m²；谱箱若保存每箱积分为 W，就不能又乘 Δλ；若保存 W/nm，积分时必须乘 Δλ。
- 光子/电子计数：N_e=t_exp∫Φ_pixel,λ·QE(λ)·λ/(hc)dλ。若使用响应度 A/W，则计算光电流后乘曝光时间再除电子电荷；不能与 QE 同时重复套用。λ/(hc) 中 λ 用 m。
- 偏振敏感探测器要以自身分析 Mueller/响应矩阵作用后取 I；所有路径先对齐探测器的公共基底。

**Mitsuba 输出注意**：`hdrfilm` 把光谱转换为颜色；`specfilm` 支持定义光谱响应带，但仍须核对带响应与归一化。Stokes 默认输出还可能经过颜色转换，精密光谱可采用固定 λ 或自定义原始谱/通量 accumulator，避免 RGB 上采样及人眼响应改变结果。[Film插件](https://mitsuba.readthedocs.io/en/latest/src/generated/plugins_films.html)、[偏振 Rendering output](https://mitsuba.readthedocs.io/en/latest/src/key_topics/polarization.html#rendering-output)

**最少统计字段**：每独立批次的 Φ、样本数、ΣX、ΣX²或Welford均值/M2、种子、λ箱、路径类别、被截断通量/概率信息。分裂子路径共享父样本，误差条应按独立父样本或独立批次估计，不能把所有子射线当独立样本。物理光子 shot noise 与计算的 Monte Carlo 方差分开报告。Q/U/V 可以为负，不能做正值夹紧。

**通量账本**：发出→探测器吸收/累计→结构吸收→基底吸收→逃逸→尚未结束/深度截断。非吸收探测器可多次观察同一个包，这些观测量不能一并当作“消耗通量”去闭账。重要性采样/RR 的闭账在统计期望上成立，不要求每随机批次机械相等。

## 八、16GB VRAM + 32GB RAM 的本地离线计算方法

不以未实测 rays/s 或“几分钟完成整机”作承诺。需要基准测量的是几何复杂度、平均深度、散射比例、膜层算子成本、探测器体量、精度与 JIT/编译开销。

### 8.1 先写出内存模型

M_peak≈M_geometry+M_BVH+M_material+M_detector+N_live×B_state×f_temporary+M_JIT/allocator。

- B_state 用实际 dtype/字段相加，再测量临时数组峰值；位置/方向/λ/介质/权重/RNG/标签会占内存。自定义前向 Stokes 状态和 Mitsuba 反向 Mueller throughput 并不同价。
- 举例：4个波长的16元 Mueller，float32，仅 throughput 即256字节/活跃样本；4个波长的4元 Stokes 是64字节，尚不含任何射线/求交状态。此为算术例子，不代表引擎固定布局。
- 100层×512²×float32 的原始厚度场约100MiB；可保留，没必要保存所有维度展开的膜层响应。
- 若对512²位置×61λ×91θ储存4个complex64振幅，则约43.37GiB，单表已超本机VRAM和RAM。128²×61×61同样数据约1.82GiB。可改为厚度场+按命中实时TMM、小块缓存、基函数/低秩压缩或按空间/谱/角度切片，必须用留出样本检验插值/压缩误差。
- 2048²像素×61谱箱×4个Stokes×float64×均值/M2两份约15.25GiB，尚未加计数、几何和射线；不能整块塞16GB显存。只保留当前λ/ROI/批次的GPU统计，CPU/磁盘按块合并。

### 8.2 分批策略

1. 把任务分为光源/工况/λ或窄谱分层/视场/容差样本的独立作业；不改变物理模型，只改变积分调度。
2. 预热JIT后用小批测 M_base，再两个批量测斜率与瞬时峰值；批量选择基于实际空闲VRAM并留安全余量，而非使用标称16GB。
3. 前向计算默认不建立反向 AD tape；按反弹压缩存活队列。偏振反向 throughput 选择与精度分开测量。
4. 曲面/边缘求交、TMM参考值及长光程差适合先用float64参考；吞吐状态是否可float32必须通过极小鬼像和守恒误差验证，不能默认全double或全float都最优。
5. 仅采样保存少量完整路径用于debug，其余只积累统计与表面序列hash/类别；不要把全部样本×全部反弹状态写RAM。
6. 随机数按seed、全局sample_id、bounce、event_slot确定；分批/并行后可复现同一采样，防止“换批量结果变了”无法定位。
7. 磁盘结果用分块格式，记录可中断恢复的已完成样本区间及配置hash。远程已存在服务只需日后对接此作业协议，不另起服务实现。

**测速验收模板**：固定commit/驱动/后端、场景摘要、总射线数与实际交互数、λ数、平均/尾部深度、显存峰值、CPU RAM峰值、初始化/JIT时间、纯追迹时间、合并I/O时间、关键ROI误差。相同性能对比必须比较相同置信区间或误差，而不只比 rays/s。

## 九、最小可验证的成熟路线与验收门槛

### A. 局部膜层/偏振基线

用独立float64参考检验裸界面、无损单膜、AR双层/多层、HR、吸收膜；覆盖正/斜入射、前/后侧、临界角及谱边。检查 R/T/A、复相位、层顺序和材料插值。偏振检查 Malus 定律、四分之一波片、镜面反射符号、旋转同一系统后的不变量，及 I≥√(Q²+U²+V²)。

### B. 无散射的非顺序通量基线

从平行玻璃板、双表面透镜、两片镜片、含传感器反射的模型开始；验证首个双反射鬼像的表面序列、斑位置和通量。用小规模完全分裂作真值参照，再对照 MC、重要性偏置与RR。逐步加入基底吸收与色散。对真实相干平行板，明确使用相干或非相干参考，不能两种参考混验。

### C. 工程探测器和统计

已知Lambert面源/点源、孔径与探测器几何，解析验算总功率、距离规律、面积变化、半球积分。比较前向和反向估计的95%区间；4倍独立样本时标准误差约减半（有限方差区间内）。弱ROI不得仅看全图RMS。

### D. 杂散光与散射

新增光阑/镜筒/边缘倒角/支架/传感器盖板，分别开关材料和表面类别，找出主要贡献。用至少一块已知样片的实测散射曲线闭环；独立检验 BSDF 的半球能量积分。几何遮挡、公差、表面法向与网格近似误差分别扫参。

### E. 与成像波动层汇合

将主通道的复瞳及局部膜层相位传入现有/新建PSF模块，先验圆孔Airy或已知解析像差，再验证非均匀镀膜引入的幅度/相位扰动。对宽谱像分别算λ后按探测器权重加功率；只在有相干依据的路径之间加场。

### F. 成熟版放行条件

不设一个笼统“误差<1%”。由产品给出总通量、主像效率、最弱需检出鬼像比、关键ROI绝对误差、谱边位置和PSF/MTF容差，并分配：材料/工艺不确定度、模型近似、离散化误差、MC方差。无实测材料/系统数据时，可称“通过数值验证”，不能称“生产精度已验证”。

## 十、版本、许可证与可追溯快照

下列commit由官方GitHub API核验；是研究时快照，不是推荐未经回归便升级到master。动态文档的版本可能与发布包不同，落地时应锁定一个通过基准的release/commit及子模块。

| 项目 | 核验快照 / 发布信息 | 许可证核验 | 使用注意 |
|---|---|---|---|
| Mitsuba 3 | master `ab3e3b18445963707d83f2b31d3db0c1f5b7688f`，2026-10-07；latest release API 为 v3.9.0，2026-08-07 | LICENSE 为BSD三条款式条件，另含Enhancements授权段 | 不应套用旧Mitsuba 0.x的GPL说明；发行依赖和资产另审 |
| Dr.Jit | master `ed360e307113b8ba388805ac15606dd142e8311e`；上述Mitsuba实际pin到`6f7cbc2e51d3dccff49d104a4f6635d50b8465bd` | BSD-3-Clause | 使用Mitsuba的依赖锁定，不将独立master随意混配 |
| PBRT-v4 | master `b4ce9687e6c695f5582997c61b0c66cf064bdb4a`，2026-09-08 | Apache-2.0 | THIRD_PARTY及CUDA/OptiX条款另行核验 |
| Raysect | master `5ed9a21b5f6ec10b71e187d51da2b430bdc65e20`；v0.9.1，2025-08-25 | BSD-3-Clause | 官方README仍为Linux支持；未验证用户环境 |
| Optiland | 文档built from `4e893f53aee1312f2d091680b93dd2279711e197`，2026-10-06 | MIT | NSQ仍预发布；不能用stable顺序文档代表NSQ |

直接凭据：

- [Mitsuba commit](https://github.com/mitsuba-renderer/mitsuba3/commit/ab3e3b18445963707d83f2b31d3db0c1f5b7688f)、[v3.9.0](https://github.com/mitsuba-renderer/mitsuba3/releases/tag/v3.9.0)、[LICENSE](https://raw.githubusercontent.com/mitsuba-renderer/mitsuba3/master/LICENSE)
- [Dr.Jit commit](https://github.com/mitsuba-renderer/drjit/commit/ed360e307113b8ba388805ac15606dd142e8311e)、[LICENSE](https://raw.githubusercontent.com/mitsuba-renderer/drjit/master/LICENSE)
- [PBRT commit](https://github.com/mmp/pbrt-v4/commit/b4ce9687e6c695f5582997c61b0c66cf064bdb4a)、[仓库许可证入口](https://github.com/mmp/pbrt-v4)
- [Raysect commit](https://github.com/raysect/source/commit/5ed9a21b5f6ec10b71e187d51da2b430bdc65e20)、[v0.9.1](https://github.com/raysect/source/releases/tag/v0.9.1)、[仓库许可证入口](https://github.com/raysect/source)
- [Optiland commit](https://github.com/optiland/optiland/commit/4e893f53aee1312f2d091680b93dd2279711e197)、[仓库MIT入口](https://github.com/optiland/optiland)

这只是技术选型的许可证事实记录，不构成商业发行法律结论；商用产品发布时仍须检查所选固定版本的NOTICE、依赖、数据和模型资产条件。

## 十一、建议精读的核心原始来源

1. **Nimier-David等，Mitsuba 2，SIGGRAPH Asia 2019**：类型变体与可重定向前向/逆向框架，以及偏振光谱案例。价值是架构与表示，而非现成工业薄膜模块。[论文/补充材料入口](https://rgl.epfl.ch/publications/NimierDavidVicini2019Mitsuba2)
2. **Jakob等，Dr.Jit，SIGGRAPH 2022**：将高层光输运操作JIT特化到CPU/GPU；论文中的性能比较只适用于其基准，不迁移到本项目4070 Ti SUPER。[论文入口](https://rgl.epfl.ch/publications/Jakob2022DrJit)
3. **Belcour–Barla，2017**：薄膜干涉与微表面模型结合、光谱变化的抗混叠；适合借鉴局部算子组合，不替代任意多层TMM。[作者原始页面](https://belcour.github.io/blog/research/publication/2017/05/01/brdf-thin-film.html)
4. **Baek等，2020**：偏振反射测量与建模，是 measured_polarized 的材料模型依据。[论文/数据入口](https://rgl.epfl.ch/publications/Baek2020Image)
5. **Veach，1997/1998博士论文，第9–11章**：MIS、双向路径追踪、Metropolis；用来明确采样PDF/测度、罕见路径和无偏权重。[论文与章节](https://graphics.stanford.edu/papers/veach_thesis/)
6. **Zeltner–Georgiev–Jakob，2020**：Specular Manifold Sampling，专门针对镜面链难采样。[论文入口](https://rgl.epfl.ch/publications/Zeltner2020Specular)
7. **Vicini–Speierer–Jakob，2021**：PRB的恒定路径存储思路。必须区分论文能力与Mitsuba当前插件限制；本报告不承诺偏振PRB已可直接用。[论文入口](https://rgl.epfl.ch/publications/Vicini2021PathReplay)
8. **Dupuy–Jakob，2018**：光谱实测BRDF的自适应参数化、存储和采样。[论文/源码/数据入口](https://rgl.epfl.ch/publications/Dupuy2018Adaptive)

## 十二、仍需验证的清单

- 本机/远程实际驱动、CUDA/OptiX、Python、Mitsuba包与变体兼容性；本次未测试。
- 用户已有TMM的复振幅定义、吸收符号约定、厚层稳定性、反面入射、能流归一化；本次未读实际MVP代码。
- 用户真实玻璃、膜层n/k、沉积图、粗糙度PSD/BSDF、光源空间-角度-光谱分布及传感器反射/QE；没有这些，误差预算仍不完整。
- 自定义镀膜pBSDF和解析曲面的GPU编译/一致性，偏振源/探测器与路径标签；只确认有扩展接口，没有声称实现已存在。
- 完整偏振体散射、强相干多路径、各向异性膜层、端到端偏振逆优化；均为后续有边界的研发模块。
- 各候选库的生产性能、峰值内存和最弱鬼像置信区间；预算必须由小基准实际测出，不能由文档射线数推算。

**最终建议**：先以现有厚度场/TMM为材料真值，用Mitsuba/Dr.Jit建立可审计的前向非顺序偏振计算核，做“平板→单透镜→双片+传感器鬼像→真实结构散射”递进验收；PBRT/Raysect做小型独立标量交叉检查；Optiland保留顺序设计及开发NSQ的选项。达到定量前向可信后，再逐项投入局部相干成像与逆向优化。
