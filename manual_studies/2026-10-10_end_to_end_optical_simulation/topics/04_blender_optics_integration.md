# Blender 与光学薄膜、沉积仿真系统的接入评估

- 研究与访问日期：2026-10-10（UTC）
- 适用背景：Python / PySide6 主程序；已有顺序平面、球面光线追迹 MVP、局部薄膜 TMM 的 R/T/A 求解，以及队列和远程计算能力。
- 研究方式：查阅 Blender、Mitsuba 官方文档和项目源码；未安装或运行外部软件，未在本项目环境进行兼容性、性能或物理精度实测。
- 本文用途：架构研究与接口设计参考，不构成现有系统已实现相关功能的声明。

> 本专题参考编号 [1]–[21] 仅对应本文末尾的独立参考资料，不占用来源登记中的 SRC-000001–SRC-000104 编号。文档与源码阅读范围按本文记录，未进行外部软件运行或项目环境验证。

## 结论

可以把 Blender 接成带三维视图编辑的独立前端，并用其内置渲染器制作场景预览与演示。现有 PySide6、顺序光追、TMM、沉积模型和远程队列应继续保留。建议先采用“独立 Blender + 小型插件 + 版本化场景交换”的增量接入方式，不为获得三维编辑而迁移整套系统。

必须分别定义三种职责：

1. **场景编辑与结果展示**：Blender 负责布局、网格、相机、可视化及交互。
2. **视觉预览**：Cycles / EEVEE 提供适合观察和演示的图像，使用明确标注的显示材质。
3. **定量光学计算**：现有求解器负责膜堆、光路、沉积与探测器结果；需要更复杂的光谱、多次散射或偏振传输时，再评估 Mitsuba 后端。

## 1. Blender 能直接提供的能力

Blender 已提供三维布局、选取、移动旋转、网格编辑、材质预览、相机、灯光和动画。其 Python API 可添加参数面板、菜单、操作器、属性组及自定义渲染引擎。因此适合开发光学元件面板、场景导入导出、提交计算和读取结果等工具。[1]

`bpy.types.RenderEngine` 提供：

- `render(depsgraph)`：接入 F12 最终渲染。
- `begin_result` / `update_result` / `end_result`：回传线性浮点图像与通道。
- `view_update` / `view_draw`：自行实现交互式渲染视口。
- 进度、取消检测和渲染通道接口。

这说明可以让 Blender 展示自有求解器产生的图像，但自定义实时视口并非接入 F12 后自动获得的功能。[2]

后台任务可使用 `blender --background --python myscript.py`。因此 Blender 导出、结果可视化和批量渲染可作为现有队列中的独立任务类型，不必另造调度体系。[3]

## 2. 独立进程与嵌入窗口的选择

### 推荐：独立 Blender + 插件

建议先提供 PySide6 内的“在 Blender 编辑”按钮，以及 Blender 内的“保存并返回”“提交计算”按钮。首版用文件包交换场景和结果；需要高频同步后再增加本机 IPC。

这一建议属于工程判断：独立进程便于隔离 Qt 与 Blender 的事件循环、GPU 上下文、Python 版本和崩溃范围，也便于保持现有主程序可独立运行。

### 不建议首版：把 Blender 窗口直接嵌入 PySide6

官方 `bpy` Python 模块主要等价于后台模式，不应把 `import bpy` 理解为导入一个现成的 Qt 三维编辑控件。官方文档还指出 GPU 资源共享、单一 `.blend` 状态和模块重载等限制。[4]

窗口重父级等平台相关技巧即使可实现，也不等于受支持的跨平台嵌入 SDK。应在确有单窗口产品要求时单独做可行性验证，不能作为本次最小接入路线的前置条件。

官方明确提醒 Blender 的 Python 集成不具备一般线程安全保证。插件不可让长期运行的后台 Python 线程直接读写 `bpy` 场景数据。建议把计算放在外部进程，在 Blender 主线程的受控回调中应用更新。[5]

## 3. Cycles 的物理能力与边界

### 3.1 RGB 路径追踪不等于完整光谱求解

Cycles 是具有辐射量定义的物理渲染器，并非只能生成装饰性图像。但其官方开发文档明确说明当前采用 RGB 颜色，而非完整光谱传输。[6]

因此，渲染画面可用于场景检查、外观比较和可视化；不能仅凭画面看起来合理就认为已验证真实光谱响应、偏振信号或多层膜的定量行为。

### 3.2 薄膜支持的版本差异

- **Blender 4.2**：Principled BSDF 加入薄膜干涉，初始面向介质材料，EEVEE 不支持该效果。[7]
- **Blender 4.5 LTS 文档**：薄膜参数包括纳米厚度和薄膜 IOR，文档仍限定介质材料。[8]
- **Blender 5.0**：Principled BSDF 和 Metallic BSDF 已增加金属基底上介质薄膜产生的物理虹彩效果。[9]

所以不应笼统声称“Blender 不支持金属薄膜”。但这些现成节点仍不等于任意多层膜堆、完整 `n(λ)+ik(λ)`、层间复振幅和偏振传播的项目级 TMM 接口。

建议始终将现有 TMM 求解器作为定量来源。可把它生成的膜厚、入射角、反射/透射或颜色结果映射到 Blender 展示；若用近似 RGB 材质，要把近似性质写入结果元数据。

### 3.3 渲染相机不自动成为真实光学系统

普通相机和景深渲染不能自动替代真实镜头组的像差、波前、衍射 PSF/MTF 或标定后的探测器信号。这是对模型层级的判断：视角图像、几何光追和波动光学描述的是不同层面的量。

项目应继续明确哪些指标来自现有顺序光追、哪些来自 TMM、哪些来自后续波动传播或传感器模型。Blender 可展示这些结果，但不应充当未经验证的统一物理真值来源。

## 4. Mitsuba Blender bridge 的可用性

### 4.1 当前主分支与旧稳定包不能混为一谈

访问日期所见官方 `mitsuba-blender` 主分支 README 声明：[10]

- Blender 最低版本为 4.2；持续集成覆盖 4.2 与 4.5 LTS。
- 发布构建捆绑 Mitsuba 3.10.0。
- 可在 Blender 内选择 Mitsuba 后按 F12 渲染，并回传进度、支持取消与 AOV。
- 提供 Mitsuba XML 场景导入和导出。

同次查阅的 Releases 页面中，稳定标签 `v0.4.0` 的说明仍为支持 Blender 4.0，并采用 Mitsuba 3.5.0。[11] 当前主分支的扩展 manifest 则标记 `0.5.0`、最低 Blender `4.2.0`。[12]

因此应固定一个经过本项目测试的 Blender 版本、插件提交或构建、Mitsuba 版本组合。README 主分支、滚动 Nightly 和旧稳定包并不是相同交付物。本文没有验证任一下载构建的安装或运行成功。

### 4.2 已核实的源码边界

已查阅主分支 `mitsuba_blender/engine/final.py`：[13]

- F12 渲染入口确实读取场景中的 Mitsuba variant 并调用 Mitsuba。
- 实现了取消、进度及结果通道回写。
- `bl_use_preview=False`。
- 该渲染引擎类没有实现 `view_update` / `view_draw`。

因此可以把它列为 F12 最终渲染桥接方案，不能据此承诺已提供 Mitsuba 实时交互视口。插件初始化时使用 `scalar_rgb`，也不能单凭这个初始化值断言最终渲染只支持 RGB，因为最终渲染入口会重新选择场景 variant。

### 4.3 材质转换有边界

官方仓库列出了可转换的 Cycles 材质、纹理和发光节点。不支持的节点在严格模式下产生错误材质；宽松模式可能使用默认输入并记录警告。因此“成功导出”不等于物理材质无损转换。[10]

Mitsuba 自身支持光谱模式及 Stokes / Mueller 偏振传输，但从 RGB 材质自动转换不会恢复测得的真实光谱。科研用途仍需传入原始光谱、明确偏振基底、定义传感器响应，并为现有 TMM 实现及验证专用接口。[14][15]

特别需要注意：Mitsuba 官方偏振文档指出，默认成像流程可能把各波长 Stokes 分量经过色匹配后转换为 RGB；对定量应用，应明确固定波长或光谱通道输出，而不能直接把显示 RGB 通道当作原始偏振测量。[15]

### 4.4 对本项目的定位

Mitsuba 是可选的后端扩展，不是获得 Blender 三维编辑能力的必要依赖。只有出现复杂非顺序光传输、多次散射、光谱或偏振成像等明确需求时，才值得投入接入和验证。

## 5. 最小实施路线

以下为设计建议，尚未实施。

### 第一步：只做显示与编辑入口

- 现有项目导出“场景 JSON + 显示网格 + 结果数组”。
- Blender 插件读取文件并创建透镜、膜面、光源、光线、相机和结果图层。
- 主程序仍拥有光学和沉积项目数据的权威版本。

### 第二步：受控参数回传

- Blender 回传元件位姿、允许编辑的参数及观察相机。
- 主程序校验数据和适用范围后生成新的项目修订。
- 首版采用显式同步按钮，避免双向自动同步引发循环、覆盖或含糊的撤销状态。

### 第三步：计算与结果闭环

- 插件提供“运行光学计算”，提交到现有队列。
- 复用任务 ID、状态、取消和结果管理。
- 已完成结果按场景哈希回显，禁止悄悄覆盖正在编辑的新场景。

### 第四步：按需求扩展

- 需要在 Blender 渲染结果窗口展示求解器输出时，增加自定义 RenderEngine。
- 需要更复杂的物理光传输时，再评估 Mitsuba 后端。
- 需要高频交互时，再增加 IPC 和有节制的增量更新。

## 6. 建议的交换契约

### 6.1 几何与标识

- 每个对象、光学面、材料具有稳定 ID，例如 `object_id`、`surface_id`、`optical_material_id`。
- 解析平面、球面、孔径与后续非球面参数作为光学真值；显示三角网格作为独立派生数据。
- 记录前后表面关系、元件顺序、孔径裁剪、曲率符号和介质朝向。
- 不从低精度显示网格反推光学面。

### 6.2 单位

- 文件明确记录长度、波长、膜厚、时间和角度单位；例如几何使用 m，波长和膜厚使用 nm。
- 换算集中在边界，避免多个模块重复缩放。
- 不能假设调整 Blender 的 Unit Scale 就正确改变所有计算行为；官方说明其主要影响 UI 显示，部分模拟并不采用该缩放。[16]

### 6.3 坐标与姿态

- 明确左右手系、世界与局部坐标、矩阵存储顺序、矩阵乘法约定和角度单位。
- 明确法向朝向、入射侧和曲率半径正负约定。
- Blender 相机对象朝向为局部 −Z，上方为局部 +Y；求解器若采用 +Z 为光轴，应有唯一且经过测试的转换，不在多个导入器中重复转换。[17]
- 若选择 glTF 等格式作为显示网格载体，要明确它的轴向转换；其 PBR 材质不能替代科研光学材料契约。Blender 的 glTF 支持自定义属性 extras，但项目仍应定义独立的命名与版本规则。[18]

### 6.4 光学材料

- 分离 `visual_material` 与 `optical_material_id`。
- 光学材料保留 n/k 数据来源和版本、波长采样、插值方式、有效区间。
- 膜堆保留层序、每层材料与厚度场、基底、入射侧、相干性假设和所用模型版本。
- 不把显示 RGB 或粗糙度等 PBR 参数当成完整光学材料描述。

### 6.5 相机与探测器

- 观察相机与真实光学系统分别定义。
- 观察相机记录位姿、投影、视场、分辨率、裁剪和图像坐标约定。
- 定量探测器记录像面、像素间距、孔径、响应光谱、曝光、量纲及归一化方式。
- 是否纳入真实镜组、衍射、偏振器及其他器件由求解器模型明确声明。

### 6.6 结果与可复现性

- 保存任务 ID、场景哈希、求解器版本、数据版本、随机种子和必要的采样参数。
- 保存波长、偏振基底、数组坐标、数据单位与有效性范围。
- 原始浮点结果与经过色调映射的预览图分开；显示变换不得覆盖原始数值。
- 使用 schema 版本以及显式的不支持项检查，拒绝含糊降级。

## 7. 最小验收清单

1. 单位往返和已知尺度校验。
2. 坐标、相机投影和像素方向校验。
3. 法向、前后介质和曲率符号校验。
4. 单界面 Fresnel 与解析结果一致。
5. 单层膜与现有 TMM 基准一致。
6. 适用条件下的能量守恒检查，并区分吸收和未捕获通量。
7. 编辑后场景修订、任务输入、结果回显版本一致。
8. 插件取消、错误、重开文件和重复导入时无静默数据覆盖。

这些是建议的验收范围，不代表已经通过测试。性能、GPU 环境兼容性、Python 版本兼容性、Mitsuba 插件安装和定量精度均待项目内验证。

## 8. 许可边界

Blender 本体使用 GPL；Cycles 单独采用 Apache 2.0。生成的图像、模型与 `.blend` 数据不因此自动受 GPL 约束。发布 Blender 插件、修改版或捆绑软件时，应根据实际组件和分发方式遵循对应许可。Blender 官方许可说明要求公开分发的 Python 扩展遵守 GPL 兼容许可。[19]

`mitsuba-blender` 许可证为 BSD-3-Clause。[20] Mitsuba3 许可原文为 BSD 风格，并包含关于公开或提供给原作者的增强贡献的附加授权段落。发行时应保留版权与许可通知，同时审查捆绑依赖许可。[21]

上述为软件架构研究中的许可提示，不替代发行前对具体组合与分发方式的法律审查。本文不建议依靠进程边界简单推定所有许可义务均已消失。

## 参考资料

以下资料均于 **2026-10-10（UTC）** 查阅。动态主分支、Nightly 与 latest 文档可能继续变化；实际实施应锁定版本或提交后复核。

1. Blender 4.5 Python API Overview：<https://docs.blender.org/api/4.5/info_overview.html>
2. Blender 4.5 RenderEngine API：<https://docs.blender.org/api/4.5/bpy.types.RenderEngine.html>
3. Blender Python Tips and Tricks，后台执行工作流：<https://docs.blender.org/api/main/info_tips_and_tricks.html>
4. Blender 4.4，Blender as a Python Module：<https://docs.blender.org/api/4.4/info_advanced_blender_as_bpy.html>
5. Blender 5.0，Python Threads are Not Supported：<https://docs.blender.org/api/5.0/info_gotchas_threading.html>
6. Blender Developer Documentation，Cycles Units & Colors：<https://developer.blender.org/docs/features/cycles/units/>
7. Blender 4.2 LTS Cycles 发布说明：<https://developer.blender.org/docs/release_notes/4.2/cycles/>
8. Blender 4.5 LTS Principled BSDF 手册（所检索到的官方页面）：<https://docs.blender.org/manual/id/4.5/render/shader_nodes/shader/principled.html>
9. Blender 5.0 Cycles 发布说明：<https://developer.blender.org/docs/release_notes/5.0/cycles/>
10. Mitsuba Blender 官方仓库与当前主分支 README：<https://github.com/mitsuba-renderer/mitsuba-blender>
11. Mitsuba Blender Releases：<https://github.com/mitsuba-renderer/mitsuba-blender/releases>
12. Mitsuba Blender 当前主分支 manifest：<https://raw.githubusercontent.com/mitsuba-renderer/mitsuba-blender/master/mitsuba_blender/blender_manifest.toml>
13. Mitsuba Blender 当前主分支最终渲染引擎源码：<https://raw.githubusercontent.com/mitsuba-renderer/mitsuba-blender/master/mitsuba_blender/engine/final.py>
14. Mitsuba 3 Choosing variants：<https://mitsuba.readthedocs.io/en/latest/src/key_topics/variants.html>
15. Mitsuba 3 Polarization：<https://mitsuba.readthedocs.io/en/latest/src/key_topics/polarization.html>
16. Blender 5.1 Scene Properties / Units：<https://docs.blender.org/manual/en/5.1/scene_layout/scene/properties.html>
17. Blender 5.2 Drivers Panel，摄像机局部轴说明（所检索到的官方页面）：<https://docs.blender.org/manual/uk/5.2/animation/drivers/drivers_panel.html>
18. Blender 5.1 glTF 文档（所检索到的官方页面）：<https://docs.blender.org/manual/id/5.1/addons/import_export/scene_gltf2.html>
19. Blender 官方许可页的官方 staging 站点副本：<https://www.staging.blender.org/about/license/>。主站规范入口为 <https://www.blender.org/about/license/>；本次主站抓取失败，实际阅读内容来自官方 staging 页面，并由官方开发文档确认 Blender 本体为 GPL：<https://developer.blender.org/docs/license/>.
20. Mitsuba Blender LICENSE：<https://github.com/mitsuba-renderer/mitsuba-blender/blob/master/LICENSE>
21. Mitsuba3 LICENSE 原文：<https://raw.githubusercontent.com/mitsuba-renderer/mitsuba3/master/LICENSE>

## 访问与验证说明

本次部分 Blender current / latest 页面直接抓取失败，采用可检索到的官方版本化文档及官方发布说明交叉核对。上文涉及主分支源码的判断限于已查阅文件；未记录不可变提交哈希，不宜将其视为长期固定事实。正式落地时应把测试使用的提交与构建信息写入项目锁定清单。

未进行软件安装、下载执行、渲染、窗口嵌入、数值对比或集成测试；不存在“项目已接入”“性能已达标”或“定量结果已验证”的结论。
