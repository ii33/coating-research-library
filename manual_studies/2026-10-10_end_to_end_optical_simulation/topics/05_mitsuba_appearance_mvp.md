# Mitsuba 薄膜真实外观单帧第一版契约与验证计划

研究日期：2026 年 10 月 10 日，UTC。

适用项目：现有 Python / PySide6 主程序、薄膜 TMM、工艺逐层沉积场、任务队列与远程计算；已有 XZ 顺序光追继续保留。本报告只研究接入方案，没有安装 Mitsuba，没有执行渲染，没有验证用户 Windows 或 RTX 4070 Ti SUPER 的实际兼容性和速度。

> 本专题的主要一手证据使用独立参考列表，不并入本研究目录现有 SRC-000001–SRC-000104 登记。Mitsuba 3.9.0 与 Dr.Jit 1.4.0 是由固定 tag 依赖文件支撑的候选组合，不代表当前最新版本；mitsuba-blender 主分支提到的 3.10.0 未安装验证。

## 结论

建议引入 Mitsuba 3 作为独立的外观成像后端，先交付一张可追溯到工艺快照的静态图。第一版采用自定义光滑多层膜 BSDF、离线 TMM 查表、真实基片几何、已知光谱的有限面积光源和理想相机。无需 Blender，也不应把现有 XZ 顺序光追改造成外观渲染器。

**保真优先的最小路线是逐波长独立追迹，再合成颜色。** 用 `cuda_ad_mono` 或 `llvm_ad_mono`，在每个波长任务开始前把所有光源、端介质折射率、膜系和其他材质求值到该波长。这样基片的真实色散影响每个波长的折射方向，输出也是可检查的 `Lλ` 图。此处的 `mono` 只负责标量光传输；不是把彩色场景转成灰度再冒充某一波长。多次独立 trace 的成本必须测量，不能承诺交互速度。

`cuda_ad_spectral` 是后续有吸引力的加速路线。它适合波长相关 R/T、但所有同一光谱包分量可共用几何方向的场景。端介质色散明显时，必须采用独立波长路径或经过验证的分波段近似，不能让不同波长悄悄共享一个参考折射率。[变体文档](https://mitsuba.readthedocs.io/en/latest/src/key_topics/variants.html)、[固定版本传感器接口](https://raw.githubusercontent.com/mitsuba-renderer/mitsuba3/v3.9.0/include/mitsuba/render/sensor.h)

以下接口、验收阈值和分阶段选择是本项目的设计建议，不是 Mitsuba 官方保证。

## 1 第一版必须足够小

### 第一版交付范围

- 一个固定工艺快照，一件样品，一个观察相机，一张静态图。
- 一个有前面、背面、侧面的真实闭合透明基片。首个标准样例用平行平板，随后必须接入一份来自工艺模型的实际基片几何；不能只交测试球。
- 前表面一个各向同性、局部平面、光滑膜堆；允许逐层厚度在面内变化。膜内可以有吸收，膜两端用于几何传输的介质先限于透明、实折射率介质。
- 背面明确指定为裸基片，或另一个有独立材料和厚度场的膜面。侧面也有明确材料，不能遗漏或默认继承前膜。
- 已知光谱的矩形面光源，加可选的已知光谱均匀环境；理想针孔或正交相机，无真实镜头组和自动曝光。
- 普通前向路径追踪，保存线性数据和单独的显示图；使用既有队列提交、取消、复现与收集结果。

### 明确不放进第一版

粗糙多层膜、微表面多次散射、真实相机镜头组、衍射与 PSF、荧光、非线性光学、磁光和双折射、薄膜内横向耦合、波导模式、实时编辑、逆向设计、自动微分优化、任意光谱 HDRI 编辑器、完整偏振路径追踪。

首版的“真实外观”指在明确输入与近似下计算场景光谱辐射，再转换成显示图；不意味着对所有材料、照明和观察条件已经具有实测级预测能力。

## 2 端到端数据契约

推荐提供一个版本化、不可变的 `AppearanceJob` 包。主程序拥有原始工艺数据，渲染进程只消费快照；渲染结束不反写工艺场。相机或光源改变可复用快照和 R/T 缓存，膜系、材料或厚度改变必须失效相关缓存。

### 2.1 必填对象

| 对象 | 最少内容 | 必须检查 |
| --- | --- | --- |
| job | schema 版本、任务 ID、快照 ID、输入内容哈希 | 版本未知时报错，不猜字段含义 |
| geometry | 顶点/三角面或受支持的解析曲面、米制尺度、坐标系、物体到世界变换 | 闭合性、法向、背面、负缩放与退化三角形 |
| surface binding | surface ID、哪一侧是外侧、膜面与基片面的绑定、UV 或物理坐标映射 | 不重叠、不串面、映射可逆或具有明确采样规则 |
| stack | 材料 ID 列表、沉积先后顺序、从外侧入射的物理层序 | 层数与逐层厚度数组一致，不能只存总厚度 |
| layer fields | 每一层的物理厚度场、有效域掩膜、单位、网格或插值规则 | 缺失不是零；零厚度可表示该处该层不存在 |
| optical constants | 各层 `n(λ), k(λ)`，端介质 `n(λ)`，有效波段、数据出处 | 吸收符号约定、波长单位、插值和禁止外推策略 |
| illumination | 光源形状、位置朝向、光谱值、物理量类型、单位和标定状态 | 辐亮度、辐强度、照度不能混用 |
| camera | 位姿、FOV 或正交范围、分辨率、裁切面、观察介质 | near clip 不能穿过或跳过样品前表面 |
| render | 波长网格/积分权重、spp、seed、深度/RR、backend、质量模式 | 所有近似和截断规则写入结果 |
| display | XYZ 观察者、白点/适应策略、曝光、色域、传递函数 | 原始数据不随显示设置改变 |

建议几何统一为米，外部膜厚统一为纳米，光学求解器入口进行一次显式单位转换；禁止在不同子模块重复换算。`d_j(u,v)` 是垂直于局部表面的物理厚度。如果工艺给的是固定世界轴方向厚度，必须先转换，不能直接交给 TMM。

工艺中的沉积顺序通常从基片向外生长。例如先沉积 L1，再 L2，空气侧入射层序就是 `air → L2 → L1 → substrate`。需要分别保存“制造顺序”和“光学访问顺序”，避免文件正序被误当成光传播顺序。

材料快照还应保留温度、密度、组分或工艺状态与光学常数的关联；现有模型没有这些量时，只能声明使用某组固定光学常数，不能从“材料同名”推断工艺后光学性质完全不变。

### 2.2 最小输出

- `spectral_radiance`：每个像素的波长采样值 `Lλ(x,y)`，Float32，附实际波长和积分权重；有绝对标定时写明单位，无标定时写明 relative。
- `linear_xyz` 和 `linear_rgb`：Float32 图，保留负 RGB 和超出显示范围的值；它们不是 PNG 像素值。
- `preview.png`：记录曝光、白点适应、色域映射与 sRGB 编码后的显示图。
- `manifest.json`：输入哈希、TMM/插件/渲染器版本、环境、光谱模式、误差预算、近似、seed、spp、耗时、警告和输出哈希。
- `validation.json`：本次物理与数据有效性检查；不完整任务只输出明确的 partial 状态，不把缺失波长填零后当成完整彩色图。

科研诊断可增加表面 ID、UV、法向、有效域和膜厚图，但不是第一版独立的大型 AOV 系统。

## 3 波长追迹路线与基片色散

### 3.1 推荐先实现单波长批处理

对每个离散波长 `λ_i`：

1. 在外部适配层计算光源 `L_e(λ_i)`、每个普通材质的该波长值、基片 `n_sub(λ_i)` 和外介质 `n_ext(λ_i)`。
2. 选择该波长的多层膜 R/T 表，并让 BSDF 从显式 `lambda_nm` 任务参数读取波长，不读取 mono 模式不存在的光谱采样向量。
3. 用标量非偏振路径追踪渲染一张浮点图。场景内全部输入都是已在此波长求值的标量；不得把原始 SPD 或 RGB 直接交给 mono 的自动灰度转换。
4. 收集 `Lλ_i`。波长积分在外部进行，色匹配函数、光源 SPD 和 `Δλ` 各乘一次；光源已经参与传输，合成 XYZ 时不能再次乘光源 SPD。

这是一组单色几何光学求解构成的多光谱计算。每个波长内可以使用不同的基片折射方向。仍需做波长积分收敛，离散采样并不意味着连续光谱精确解。

一个持久化渲染工作进程中复用几何/加速结构，按波长更新参数与 LUT；不要给每条 ray 启 Python，也不要未经测量就在单张 GPU 上同时启动几十个抢显存的进程。先顺序批处理，后决定是否微批并行。AD variant 可以只用于前向计算，无需开启梯度。

### 3.2 可选的 packet spectral 加速

自定义 BSDF 从 `si.wavelengths` 取多个波长，返回 Spectrum 权重。只要端介质不色散，或经过检验允许固定参考折射率，多个波长共用一个折射方向就具有清晰模型含义。膜层本身的 `n,k` 与干涉 R/T 仍可随波长变化。

对于真实色散基片，可把波段分开运行，每个窄波段固定该波段代表折射率，波段内仍进行 spectral sampling。此法有受控但非零的几何色散近似；以减半波段宽度后的方向、位置、XYZ 和色差变化验收。不能把有限宽度 SRF 的积分结果称为严格单波长结果。

精确 hero-wavelength、路径分裂或定制传感器属于后续方案，不能仅因为 `set_variant('cuda_ad_spectral')` 就宣称已支持色散路径。Mitsuba 的 `BSDFSample3f` 有一个出射方向和一个相对折射率，插件需要尊重这个数据结构。[BSDF 数据结构](https://raw.githubusercontent.com/mitsuba-renderer/mitsuba3/v3.9.0/include/mitsuba/render/bsdf.h)

## 4 多层膜 BSDF 的物理契约

### 4.1 TMM 交付功率量

输入为局部位置、入射侧、波长和入射角，输出 `R_s, R_p, T_s, T_p`；所有 R/T 是功率比例，不是电场振幅。非偏振初始光的单次相互作用使用：

`R = (R_s + R_p) / 2`

`T = (T_s + T_p) / 2`

`A = 1 - R - T`

上述 `A` 定义先限于被动膜层、实折射率透明端介质。对于实折射率端介质，T 包含 `n_t cosθ_t / (n_i cosθ_i)` 的通量归一化，不能直接使用 `|t|²`。复杂吸收入射介质不满足这套最简假设，首版应拒绝。[TMM 原作者实现](https://raw.githubusercontent.com/sbyrnes321/tmm/master/tmm_core.py)、[原作者推导](https://arxiv.org/abs/1603.02720)

每次 TMM 结果必须满足被动性和数值有效性。允许仅在事先规定的小舍入阈值内纠正 `-ε`；不能用无条件 `clip(0,1)` 或强制 `T=1-R` 掩盖求解、插值、单位和符号错误。

### 4.2 反射 透射 吸收分支

推荐用一个具有明确期望值的基准采样器先验收，再做减噪优化。单波长时取 `q_R=R, q_T=T, q_A=A`。抽中反射、透射时分别返回对应 delta lobe；抽中吸收时返回零权重并安全终止。吸收不是“再乘一个 A 的反射材质”。

若采用 spectral packet，一个标量随机数决定整条路径的分支，可用包内分量平均值作为 `q_R,q_T,q_A`；每个光谱分量必须分别除以真正选择概率。例如采到反射时该分量权重为 `R(λ)/q_R`，不能返回全 1。平均值只是 proposal，不是把光谱 R/T 变成一个灰色材料。

也可不显式抽吸收：令 `q_R=mean(R)/(mean(R)+mean(T))`、`q_T=1-q_R`，仍返回 `R/q_R`、`T/q_T`。这会把吸收作为 throughput 衰减隐式计入，能避免大量零贡献路径。两种方案都要验证相同期望值；不要错误地把 R/T 归一化后直接当无损权重。

零概率分支不可被选择，不允许除零；`R+T=0` 时直接零贡献。需要遵守 `BSDFContext` 的 lobe/component mask；如果只启用某一分支，重新定义采样概率但保留该分支真实物理权重。active mask 和空样本必须安全。

### 4.3 eta 与 radiance importance 模式

定义当前 `si.wi` 所在介质为 i，采样透射 `wo` 所在介质为 t；`eta_it=n_t/n_i`，`eta_ti=n_i/n_t`。

- 反射：`bs.eta=1`，`weight_R=R/q_R`。
- 透射：`bs.eta=eta_it`。
- Radiance 模式：`weight_T=(T/q_T) * eta_ti²`。
- Importance 模式：`weight_T=T/q_T`。
- `bs.pdf` 是实际选中 delta 分支的离散概率；不是另一个连续立体角密度。
- `sample()` 返回的是采样权重；纯 delta BSDF 的普通 `eval()` / `pdf()` 对连续方向查询返回零。不能再在外部额外乘一次 cos 或除一次 pdf。

这与固定版本 `dielectric.cpp` 的 eta² 约定一致。TMM 的功率通量归一化和 BSDF 的辐亮度 eta² 是两个不同转换，不能互相替代，也不能重复附加。应使用官方 `reflect` / `refract` 的方向约定，测试前后两侧。官方 path integrator 还使用 `bs.eta` 修正 Russian roulette 判据，因此“权重算对但 eta 始终设 1”也不是完整实现。[dielectric 源码](https://raw.githubusercontent.com/mitsuba-renderer/mitsuba3/v3.9.0/src/bsdfs/dielectric.cpp)、[Fresnel 方向约定](https://raw.githubusercontent.com/mitsuba-renderer/mitsuba3/v3.9.0/include/mitsuba/render/fresnel.h)、[path integrator](https://raw.githubusercontent.com/mitsuba-renderer/mitsuba3/v3.9.0/src/integrators/path.cpp)

无传播透射方向时令 `T=0`，不生成虚假的折射 ray；含吸收薄膜时不能仅因为端介质达到全反射条件就强制 `R=1`，仍可能有膜吸收。

## 5 表面 朝向和透明体必须一致

膜 BSDF 代表纳米层的局部相干散射；基片几何代表毫米级实体的光路。两个层级不能双计数。

### 5.1 推荐实体接口

前膜只计算 `外介质 → 薄膜层 → 基片` 的局部边界 R/T。透射后 ray 真正进入基片，传播到背面再经历裸界面或背面膜。宏观多次反射由 Mitsuba 路径追踪处理。前膜表中不应再塞入“整块基片 + 背面”的总透射，否则背面贡献会算两次。

首版透明基片体内先不吸收。若后续要实现 Beer–Lambert 体吸收，应有独立体介质和 `volpath` 等介质感知积分器；表面膜吸收与体吸收分开，且需要一致的米制吸收系数。不能仅添加一个 medium 对象却继续默认普通 surface path 就称为生效。将复杂折射率基片近似为实折射率界面加体吸收，也要明示近似和验收范围。[介质接口说明](https://mitsuba.readthedocs.io/en/latest/src/generated/plugins_bsdfs.html)

### 5.2 入射侧与逆序

- 几何法向指向 exterior；正面/背面由射线和有效物理法向判定。
- 正面取 `n_ext → L_outer … L_inner → n_sub`。
- 从基片返回前膜时，取 `n_sub → L_inner … L_outer → n_ext`，并使用该侧实际入射角。
- 非对称且有吸收的膜堆，两侧反射率一般不同；不能把正面 R 表拿去给背面用。
- 不允许用 `twosided` 包装器简单翻法线来掩盖光学层序问题。
- 不在第一版叠加 normal map 或 bump map。平板使用一致的几何与着色法向；曲面法向的插值必须作为几何精度问题验收，不让视觉平滑法向改变物理表面却不记录。

### 5.3 thindielectric 不满足这个需求

官方 `thindielectric` 模拟薄的成对介质界面，透射光不发生净角偏转，内部反射采用其自身的薄介质处理；它不是任意层序、`n(λ)+ik(λ)` 和空间膜厚的相干 TMM。它不能作为多层膜插件的替身，也不能拿来隐藏未知基片厚度。[官方 thindielectric 定义](https://mitsuba.readthedocs.io/en/latest/src/generated/plugins_bsdfs.html#thin-dielectric-material-thindielectric)

未来若支持忽略横向位移的零厚度 sheet，必须另立模型：两端介质、是否包括整块基片、相干/非相干处理都要声明，并证明厚度与视角下位移可忽略。首版不把它当默认透明体。

### 5.4 相干性边界

每个薄膜堆内部保留相干干涉；分离的基片前后表面之间用几何光学功率路径叠加，不保留毫米级腔的复相位。激光照明、超薄基片或高相干 etalon 若需要前后表面干涉，必须拒绝首版定量预测或转专用相干模型。把两个相干 BSDF 用路径追踪连接起来不等于自动形成整个系统的相干波解。

## 6 非偏振近似的明确边界

对于单次相互作用，未偏振入射的强度可用 s/p 功率平均。对于连续多次反射/透射，每次都重新平均相当于丢弃上一步产生的偏振；即使光源最初未偏振、相机没有偏振片，也可能影响最终可见强度。

平面内两次反射的简单例子：正确强度含 `(R_s1 R_s2 + R_p1 R_p2)/2`，逐次标量平均则得到 `(R_s1+R_p1)(R_s2+R_p2)/4`，通常不相同。透明平板内反射也属于这个问题，不能以“普通相机”作为忽略偏振的充分理由。Mitsuba 官方也明确指出镜面多次相互作用等场景会出现非偏振与偏振结果差异。[官方偏振说明](https://mitsuba.readthedocs.io/en/stable/src/key_topics/polarization.html)

第一版输出必须标记 `polarization_model=unpolarized_reset_approximation`。首批验收使用接近法向、主要由一次膜反射或简单透射贡献的受控场景，并对代表性的两界面、斜角和多反射路径用 s/p 分开传播的参考结果量化偏差。若超出项目容许误差，只能交“近似预览”，不能把图片标为该条件下已验证预测。

全偏振扩展需要复振幅/相位差、Mueller 变换、入射/出射偏振基底和旋转；仅把 variant 改成 `_polarized`、或保存 Rs/Rp 两张表都不够。首版 R/T 表不要冒充将来完整偏振所需的数据，但应保留原始 TMM 和膜系以便重建。

## 7 查表设计

### 7.1 不在每条路径中运行 Python TMM

在任务预处理阶段用现有可信 TMM 批量计算。BSDF 热路径仅做位置映射、表查找、插值、分支和方向计算，用 Dr.Jit 类型表达；不能在每次 `sample()` 中转 NumPy、拷回 CPU、用 Python 循环逐 ray 求解或打印数组。官方 Python 插件教程支持 JIT 路线，但示例的带色 dielectric 不是可直接照抄的膜 BSDF。[官方 Python 插件教程](https://mitsuba.readthedocs.io/en/latest/src/others/custom_plugin.html)

### 7.2 第一版表布局

对每个快照和膜面，表的轴为 `surface sample × λ × μ × incident side × channel`，其中 `μ=|cosθ_i|`，channel 为 R/T。空间样本来自 UV 或工艺物理坐标。逐层厚度先在每个空间点完整求值，再计算当地膜堆；不要创建每一层厚度一根轴的高维全参数表。

这样既保留各层独立非均匀性，又不把工艺结果偷换成“所有层按同一总厚度系数缩放”。如果数据实际确有低秩或同尺度结构，可以以后利用，但必须先证明。

建议最初为单波长批次只上传一个 `u × v × μ` 的 Float32 切片，四通道为正反两侧 R/T。Dr.Jit 1D/2D/3D texture 或显式 gather 足以表达，不要求原生 4D texture。比如 32×32 空间点、65 个角度点、4 通道，占 1,064,960 字节，约 1.02 MiB；95 个波长全存约 96.5 MiB，仅为原始表数据，不能当整场景显存预算。

### 7.3 插值和精度

- 空间分辨率由厚度变化和可见条纹变化决定；光学响应可能比厚度场变化快，不能只看几何网格疏密。
- 波长与角度节点需要覆盖干涉窄峰、掠射和临界角附近。5 nm 或 65 角度点只能是起始配置，不是精度保证。
- 对有效单元使用共同非负权重的线性插值，有助于保留 R/T 的被动凸约束；这不能保证物理曲线形状正确，仍须用未参与建表的 TMM 点验证。
- 表不能跨越材料边界、遮罩边缘、UV 接缝或缺失数据插值。角度、波长、空间越界不静默 clamp；根据显式规则拒绝或细化。
- 临界角附近按传播/非传播域分段，杜绝插值得到不可能的传播透射。对有吸收膜保留相应 R/A 行为。
- 第一版校验用软件 Float32 插值。CUDA 硬件纹理插值的权重精度有限，应作为经过比对的性能选项，而不是默认无误差替换。Dr.Jit 文档提示其硬件线性插值权重使用有限定点精度。[Dr.Jit textures](https://drjit.readthedocs.io/en/stable/textures.html)

缓存键至少包括：快照、几何映射、全部逐层字段、材料数据、TMM 版本、两侧端介质、相干策略、波长/角度/空间网格和插值版本。只以总厚度和材料名称做键不足以复现。

## 8 照明 光谱与显示颜色

### 8.1 先使用可追溯光谱

面光源至少给出形状、面积、姿态、发射方向和 spectral radiance。若只有灯具 SPD 的相对形状，可以做相对颜色与固定曝光比较，但没有几何与亮度标定就不宣称绝对辐亮度或真实曝光。有限面积光源也比只放一个点光更适合观察理想镜面样品；纯 delta 镜面与 delta 点光不能依赖普通路径采样稳定连接。[Mitsuba 发光体定义](https://mitsuba.readthedocs.io/en/latest/src/generated/plugins_emitters.html)

第一版支持用户提供 SPD 和有名字、有出处的参考照明。没有实测 SPD 时允许明确选择参考光源生成条件图；界面与结果都显示照明假设，不把参考光源写成实测灯具。

### 8.2 环境图不能恢复丢失的光谱

RGB HDRI 可以给出空间亮度和颜色线索，但三通道不能唯一确定每个方向的真实 SPD。官方 envmap 在 spectral 模式下把 RGB 转成光谱模型系数，这是一个升谱模型，不是对现场光谱的测量。[固定版本 envmap 源码](https://raw.githubusercontent.com/mitsuba-renderer/mitsuba3/v3.9.0/src/emitters/envmap.cpp)

首版定量/可追溯模式只用均匀光谱环境和已知光谱面光；RGB HDRI 可作为明确标记的视觉预览扩展。更复杂的光谱环境可用真实 `L_e(ω,λ)` 数据，或经过声明的可分离模型 `E(ω) S(λ)`；不要默认所有彩色环境像素共享同一真实光源 SPD。

### 8.3 三类输出不可混同

1. 光谱辐射数据：逐波长方案中的 `Lλ`，或 spectral 方案中由 `specfilm` 输出的 SRF 加权波段积分。后者有有限响应宽度，不是精确单点光谱。
2. 线性色度数据：对 `Lλ` 按 CIE 1931 2° 观察者积分成 XYZ，再转换线性 RGB。官方提供 1 nm 色匹配函数数据；积分范围、权重和归一化要固定。[CIE 原始数据](https://cie.co.at/datatable/cie-1931-colour-matching-functions-2-degree-observer)
3. 显示图：固定曝光、明确白点适应和色域映射，再 sRGB 编码。色调映射只用于显示，不能用于评估膜厚导致的真实色差。

建议 `XYZ = K Σ_i Lλ_i [x̄_i,ȳ_i,z̄_i] w_i`。K 的含义必须记录：可以是定义良好的相对尺度，也可以是完成光度标定后的物理尺度；不能既按白样归一化又声称保留绝对辐亮度。场景对比必须使用同一曝光、同一适应白点和同一 K，不逐图自动归一化。

原始线性 RGB 可有负值或大于 1，保留它们用于分析；显示端再处理色域和亮度。不能把 clip 后 PNG 的 RGB 当真实颜色真值。标准观察者结果也不等于具体手机相机 RAW，要预测某个相机需要其通道 SRF、镜头透过率和曝光模型。

Mitsuba 的 `hdrfilm` 可输出线性 RGB/XYZ，`specfilm` 可记录多个 SRF 通道；spectral variant 默认仍可能只得到 RGB 图。首版应明确用哪个路径生成哪个量，不依赖文件扩展名判断。[HDR film 源码](https://raw.githubusercontent.com/mitsuba-renderer/mitsuba3/v3.9.0/src/films/hdrfilm.cpp)、[Spectral film 源码](https://raw.githubusercontent.com/mitsuba-renderer/mitsuba3/v3.9.0/src/films/specfilm.cpp)

## 9 版本与 Windows GPU 条件

本次可直接核查的锁定候选是 **Mitsuba v3.9.0 + Dr.Jit 1.4.0**：v3.9.0 的官方 `pyproject.toml` 明确固定该 Dr.Jit 依赖。发布页可读到 v3.9.0，但本报告不据此宣称它是全部渠道的最新版本。[v3.9.0 发布](https://github.com/mitsuba-renderer/mitsuba3/releases/tag/v3.9.0)、[依赖文件](https://raw.githubusercontent.com/mitsuba-renderer/mitsuba3/v3.9.0/pyproject.toml)

另一个独立事实是：读取到的 `mitsuba-blender` 主分支 README 声明捆绑 Mitsuba 3.10.0。主分支说明、滚动构建、GitHub 发布列表和实际可下载 wheel 不同；本次未验证 3.10.0 的 release 页面和目标环境安装。该差异不需要本项目引入 Blender，也不应拿主分支声明覆盖已核查 tag 的 API 契约。[Blender 桥接主分支说明](https://raw.githubusercontent.com/mitsuba-renderer/mitsuba-blender/master/README.md)

固定 v3.9.0 README 声明 Windows x86-64、Python ≥3.9、GPU 路线 NVIDIA driver ≥535、CPU 并行 LLVM ≥11.1，并列出 CUDA/LLVM 的 mono 与 spectral AD 变体。这是候选环境要求，不是目标机器的通过记录。最新编译文档又有 Python ≥3.10 的构建要求，不能把最新版构建条件与旧 tag wheel 条件随意拼接。[固定版本 README](https://raw.githubusercontent.com/mitsuba-renderer/mitsuba3/v3.9.0/README.md)、[编译文档](https://mitsuba.readthedocs.io/en/latest/src/developer_guide/compiling.html)

对用户的 Windows + RTX 4070 Ti SUPER，建议实际实施时在隔离 worker 环境完成以下准入检查，再决定是否作为默认后端：

1. 记录 Windows、Python、GPU、驱动、Mitsuba、Dr.Jit、包来源和实际安装文件版本；不直接污染 PySide6 主环境。
2. 检查目标 Python/架构有对应官方 wheel；确认 `mi.variants()` 中目标 variant 存在。
3. 验证 CUDA/OptiX 可实际初始化，完成官方小场景和自定义 BSDF smoke test；GPU 型号本身不证明驱动、上下文和依赖都正确。
4. 分别测试 `cuda_ad_mono`、`cuda_ad_spectral`，需要 CPU 回退时测试 LLVM 的相应模式和实际 LLVM 可用性。
5. 首次 JIT、预计算、加速结构、每波长 trace、写盘、总时间和显存峰值分别统计。只报告测到的数据。
6. 输出失败时保留诊断，允许切换到已经验证的 CPU 模式；不偷偷切 RGB 或降低物理精度。

官方说明 CUDA 后端可动态使用系统驱动库，不要求为 Mitsuba 手工安装某一固定 CUDA Toolkit。出现兼容问题先查目标组合，不能把重装整套 CUDA 当通用修复。[GPU 编译说明](https://mitsuba.readthedocs.io/en/latest/src/developer_guide/compiling.html#gpu-variants)

## 10 验证计划与建议门槛

下列数值是第一轮建议的开发验收阈值，需要结合用途和参考实现调整；本次没有任何已通过的测试结果。以解析/独立求解器验证物理，以高精度 TMM 验证 LUT，以收敛试验验证 Monte Carlo 和离散化，避免同一错误实现互相“证明”。

### Gate A 数据和单界面

- 空膜堆与官方 smooth dielectric 在正反两侧、法向到掠射、临界角两侧一致。裸空气/玻璃法向 `n=1.5` 的 R 应为 0.04。
- 厚度为零的层消失后，与移除该层结果一致；nm/m 错位用专门反例拦截。
- 单层膜用独立解析解核对，至少覆盖无损四分之一波减反层、吸收层、非对称层序。
- 双精度参考的无损 `|R+T-1|` 目标 ≤1e-8；被动吸收样例要求 R/T/A 有效且和为 1。GPU/插值生产门槛另行放宽，不能把同一个阈值套全部数值层。
- 正反两侧和 Snell 配对角的透射互易关系通过；不要求非对称吸收膜的正反 R 相同。

### Gate B BSDF 采样与传输约定

- 固定 R/T/A 的大量采样，分支频率与 q 一致，返回权重的均值与预期贡献在统计置信范围内。
- 验证三事件采样与两事件吸收衰减方案一致；packet 的每波长结果一致，不能只看通道平均。
- 专测 radiance / importance、仅反射/仅透射 mask、零概率、R+T=0、inactive lane、TIR 和吸收 TIR。
- 检查折射前后 `bs.eta`，一块无吸收闭合平板穿出到原介质后 eta² 因子应正确抵消；单个跨介质接口不应强行抵消。
- 用预定解析贡献或数值积分作参考，建议抽样误差落在 3 标准误差内；误差不收敛视为实现问题，不能靠加 spp 掩盖。

### Gate C LUT

- 使用未参与建表的随机与困难点，包含角度/波长/空间中点、厚度梯度大处、窄峰和临界角附近。
- 初步目标 `max |ΔR|, |ΔT| ≤1e-3`，敏感应用更严。窄谱峰额外检查峰位和带宽，不只检查随机平均误差。
- 把空间、角度、波长分辨率分别加倍，报告误差变化；尚未收敛的轴不得标为 final。
- 固定显示条件下，代表性无噪声色样的 LUT 引入色差可先以 ΔE00 ≤0.5 为候选门槛。用于指标的白点和归一化固定；不能在 tone map 后测。
- 软件插值作为参考，独立测量硬件纹理与 Float16 误差，未过门槛不启用。

### Gate D 场景与成像

- 透明平板、单面涂层平板、非对称膜、反向观察、楔形或曲面实际基片各一例；背面/侧面开关与膜面 ID 可目视和数值检查。
- 两份“总厚度相同、逐层分配不同”的场必须产生 TMM 预期的不同颜色，防止错误压缩为总厚度图。
- 将工艺场平移/旋转后，颜色变化随正确的基片位置移动；UV 接缝无串色。
- 逐波长色散路径用至少三个波长的 Snell 出射角/落点做解析比较；packet 近似必须与逐波长参考对照。
- 均匀已知光源、灰/白参考、简单谱线组合验证 `Lλ → XYZ → linear RGB`；窄波段 specfilm 测试响应面积与单位，防止漏乘或重复乘波段宽度。
- 多次镜面路径对比 s/p 参考，报告非偏振近似误差；超过门槛时输出预览标签或拒绝量化结论。

### Gate E 数值收敛和实际交付

- 相同输入与 seed 在同一已锁定环境可复现；跨 backend 允许浮点差异，以误差与置信区间比对，不要求逐 bit 相同。
- 分别增加 spp、光谱节点、LUT 分辨率和路径深度；禁止把不同误差来源合并成一个“渲染质量”开关后无法诊断。
- 使用多 seed 或独立批次估计 Monte Carlo 噪声，候选目标是关键 ROI 亮度相对标准误差 &lt;1%；接近黑色区域另用绝对误差。
- 高反射膜可能需要较长路径，不能固定小 `max_depth` 却称能量完整。无限深度配 RR 或已证明足够的有限截断都可，需记录尾部贡献检验。
- 最后交实际工艺样品的单帧，能从结果回溯到每层厚度场、材料光谱和照明；同时附清楚的模型限制。

## 11 缺少数据时的退化与拒绝政策

| 缺少或不适用项 | 允许的最小退化 | 必须拒绝或明确标记的内容 |
| --- | --- | --- |
| 无实际几何 | 明示假设尺寸的平板演示 | 不称为该工艺基片的真实外观 |
| 只有表面没有实体厚度 | 单面反射的受控测试 | 不猜透射位移、背面和实体多反射 |
| 缺背面膜说明 | 请明确选择裸背面作假设 | 不默认前后膜相同 |
| 只有总厚度 | 若明确给出各层均匀厚度，可做均匀设计样品 | 不从总厚度恢复不存在的逐层非均匀性 |
| 层数据缺失 | 显示缺失区域/任务错误 | 不把缺失当 0，不沿用旧快照填补 |
| 缺 n/k 或光谱越界 | 选取有来源的明确替代材料，作为假设演示 | 不静默外推、不从 RGB 猜 n/k |
| 没有实测光源 SPD | 明示 D65 等参考照明或用户给定假设 SPD | 不声称还原现场灯光颜色 |
| 有 SPD 形状无绝对亮度 | 相对辐射量、固定曝光对比 | 不给绝对辐亮度/曝光预测 |
| 仅有 RGB HDRI | 单独标记升谱近似的预览 | 不称为实测光谱照明 |
| 基片色散明显 | 逐波长 trace；或验证过的窄波段近似 | 不暗用全谱常折射率 |
| 基片体吸收/散射显著 | 在后续介质模型完善前暂缓透射预测 | 不借膜 A 代替路径长度相关体吸收 |
| 偏振、多镜面误差显著 | 明示近似预览 | 不声称偏振正确或已达定量容差 |
| 高相干整腔、衍射或各向异性 | 转相应专用模型研究 | 不用本 MVP 输出定量波动结果 |
| GPU 不可用 | 已验证的 LLVM 后端，报告耗时变化 | 不静默改 RGB、跳层或降光谱范围 |
| 采样/缓存/波段未完成 | partial 数据与进度 | 不把部分谱当完整最终颜色 |

这些规则应作为任务校验器的一部分，而不只是报告里的免责声明。

## 12 实施顺序和完成定义

1. **环境与纯接口样机**：锁版本，读写 Job/Result，单色白光无膜场景通过；复用已有远程任务流程。
2. **单点膜 BSDF**：固定厚度、单波长、平板、正反入射，完成 Gate A/B。此时不做复杂 UI。
3. **逐波长单帧**：引入真实光源 SPD、基片色散与 `Lλ` 输出，完成颜色合成，接入真实闭合基片。
4. **工艺厚度映射与缓存**：逐层场、面内查表、误差细化，通过 Gate C/D。
5. **主程序入口**：PySide6 只增加快照选择、照明/相机、提交/取消、结果图和近似提示；最终从实际工艺样品复现单帧并通过 Gate E。

第一版完成标准不是“能出一张漂亮图”，而是同一包输入能复现图像，输入缺失不会被静默补猜，R/T 与 eta² 已有独立验证，逐层厚度确实进入模型，线性数据与显示图能清晰区分，未建模的偏振/相干/粗糙度不会被误报为已支持。

之后按实际瓶颈选择一个扩展：packet 光谱加速、体吸收、粗糙表面或全偏振。不要为了将来逆向设计，在单帧前向链路尚未验证时同时引入全部可微功能。

## 主要一手证据索引

以下均为此次实际查阅的官方文档或项目源码；固定 tag 的链接优先用作实现依据，latest/stable 页面只用于能力说明，实施时仍需与锁定版本核对。

- [Mitsuba v3.9.0 release](https://github.com/mitsuba-renderer/mitsuba3/releases/tag/v3.9.0)
- [v3.9.0 pyproject 与 Dr.Jit 依赖](https://raw.githubusercontent.com/mitsuba-renderer/mitsuba3/v3.9.0/pyproject.toml)
- [v3.9.0 平台要求与默认 variants](https://raw.githubusercontent.com/mitsuba-renderer/mitsuba3/v3.9.0/README.md)
- [官方 Python BSDF 插件教程](https://mitsuba.readthedocs.io/en/latest/src/others/custom_plugin.html)
- [v3.9.0 BSDF 接口](https://raw.githubusercontent.com/mitsuba-renderer/mitsuba3/v3.9.0/include/mitsuba/render/bsdf.h)
- [v3.9.0 dielectric](https://raw.githubusercontent.com/mitsuba-renderer/mitsuba3/v3.9.0/src/bsdfs/dielectric.cpp)
- [v3.9.0 Fresnel 与折射方向](https://raw.githubusercontent.com/mitsuba-renderer/mitsuba3/v3.9.0/include/mitsuba/render/fresnel.h)
- [v3.9.0 path integrator](https://raw.githubusercontent.com/mitsuba-renderer/mitsuba3/v3.9.0/src/integrators/path.cpp)
- [v3.9.0 传感器契约](https://raw.githubusercontent.com/mitsuba-renderer/mitsuba3/v3.9.0/include/mitsuba/render/sensor.h)
- [v3.9.0 hdrfilm](https://raw.githubusercontent.com/mitsuba-renderer/mitsuba3/v3.9.0/src/films/hdrfilm.cpp)
- [v3.9.0 specfilm](https://raw.githubusercontent.com/mitsuba-renderer/mitsuba3/v3.9.0/src/films/specfilm.cpp)
- [v3.9.0 envmap 光谱升谱](https://raw.githubusercontent.com/mitsuba-renderer/mitsuba3/v3.9.0/src/emitters/envmap.cpp)
- [Mitsuba 变体说明](https://mitsuba.readthedocs.io/en/latest/src/key_topics/variants.html)
- [Mitsuba 偏振说明](https://mitsuba.readthedocs.io/en/stable/src/key_topics/polarization.html)
- [Dr.Jit 纹理及插值精度](https://drjit.readthedocs.io/en/stable/textures.html)
- [Mitsuba Windows 与 GPU 构建说明](https://mitsuba.readthedocs.io/en/latest/src/developer_guide/compiling.html)
- [TMM 原作者实现](https://raw.githubusercontent.com/sbyrnes321/tmm/master/tmm_core.py)
- [TMM 原作者多层膜推导](https://arxiv.org/abs/1603.02720)
- [CIE 1931 2° 原始色匹配函数](https://cie.co.at/datatable/cie-1931-colour-matching-functions-2-degree-observer)
- [mitsuba-blender 主分支版本声明](https://raw.githubusercontent.com/mitsuba-renderer/mitsuba-blender/master/README.md)

## 访问与验证说明

版本与平台要求来自本报告列出的固定 tag 或官方文档；v3.9.0 与 Dr.Jit 1.4.0 是已固定依赖依据的候选，不是“最新版本”结论。mitsuba-blender 主分支 README 声明 3.10.0，但该构建未在目标环境安装或运行。

未进行软件安装、下载执行、渲染、Windows/RTX 4070 Ti SUPER 兼容性检查、数值对比或集成测试；Mitsuba 是待授权、待验证的建议方案，不构成“项目已接入”或“结果已验证”的声明。
