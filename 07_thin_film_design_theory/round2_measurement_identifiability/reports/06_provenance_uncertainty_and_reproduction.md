# 06 · 来源、继承边界与可复现验收

## 6.1 上游不能因逆问题而消失的约束

本轮只在`07_thin_film_design_theory/round2_measurement_identifiability`新增内容。原需求`00_project/工程科研.txt`将报告目标设为可复用工程手册/教材；本轮承接T06手交的测量算子与有限参数辨识问题，不推进生产实验。原文、当前路线图、T06报告与手交在开工时已读取，目录外基线保存在verification/outside_before.json；不修改根STATE/ROADMAP，也不改产品模拟器、用户电脑或早先冻结增量。

以下保留为持续限制：

1. T05到达工件的入射量不等于净留存；反应、解吸、再溅射及初始库存未闭合时不能反推实际膜厚。元素/分子/式单元口径、局部实际面积不能混用
2. T04实际组分、膜态密度、温度、相态、孔隙、氧化与历史缺失时，不提供工艺→n/k的确定函数。public_bulk不能填film；bulk α不能冒充film k。H4供应/组成未知不会被椭偏自动解释，YbF3也不能改成YF3
3. T06的Al参考来自特定公开薄膜n/k，是assumed_transfer条件计算；省略氧化层，未重现McPeak论文整个模板剥离栈。本轮未复用该数值，所有n/k示例均synthetic；不能借用其材料身份给当前结果赋予真实来源
4. 设计d、几何d、QCM等效d、光学nd分别存档；同一联合拟合出的n/k/d不能当三组独立验证。QCM声学、温漂、tooling未校准；单QCM的源强/形状与ηQ辨识缺口仍在
5. specular缺口含散射；吸收分账必须遵守真实收集几何。背面/基片体吸收/相干性/孔径不能靠拟合吞并。本轮明确拒绝未实现分支，不将拒绝记为工程失败或实测证伪
6. T02v0.3完整oracle仍partial；T03非负贡献优化器不支持净侵蚀；点12连续参考/离子参考及设备高算量验证not_run；tau仍是非严格条件包络。当前增加光学理论不晋升上述状态

## 6.2 七轴不确定度

| 轴 | 本轮应保留的内容 | 当前证据 |
|---|---|---|
| source | 材料常数的原始样品/拟合模型/数据协方差/版权与版本 | 例子纯合成；真实材料协方差未知 |
| time | 工艺、温度、老化、仪器漂移及采样异步 | 未测，不能填0 |
| space | 非均匀厚度与不同光斑/几何表征位置 | 统一层仅场景假设 |
| geometry | AOI、NA、偏振、表面积、楔角与收集孔径 | 节点已显式定义；真实值未知 |
| kernel | 稳定核、分支、谱/角离散、差分步长、局部线性化 | 仅小型正确性检查 |
| input | d、n/k参数化、校准、噪声及相关性 | 合成尺度/Σ；不能替代证书 |
| model | 氧化、粗糙/散射反馈、各向异性、背面、缺失状态 | 当前接口排除，真实样品待验证 |

未知项在机器合同中用null/unknown/not_run；没有这些信息时不把已知几项方差平方和称作“总误差”。即使数值核误差极小，source和model误差也可能主导。rank阈值是软件诊断，不是七轴误差预算闭合证书。

## 6.3 来源阅读与合法保留

只采用原作者方法、原始对比实验或官方计量资料。`sources/source_registry.json`记录版本、DOI/官方URL、具体已读范围及不能支持的结论；`sources/summaries`保存原创短摘要。对Hilfiker/Jellison只声称已读可访问的出版者摘要与摘录，未读取商业全文。原始数学与合成反例由本项目自行推导，公式和代码不复制文献软件。

冻结T07 kernel逐字复制至models/vendor/optics_kernel.py，源路径和SHA256列在data/frozen_dependencies.json。前向核是本项目首轮原有独立教学实现，不把它冒充外部成熟库。其所有物理域限制保留。其它被读上游文件仅记录hash，不成为本地reader运行依赖。

本轮没有下载受限原文。MI-S04原刊明确CC Attribution，官方PDF合法下载并仅本地存档，字节与哈希单列；它不进入reader。已有T07合法本地原稿保留在原处，不拷入reader。来源链接可供有权访问者查阅。没有版权原件、论文图像、ZIP、缓存或数据导出混入发布允许列表；allowlist存在不等于授权发布，当前只本地冻结，不上传、不部署、不push。

## 6.4 复现顺序

在本目录，设置PYTHONDONTWRITEBYTECODE=1、PYTHONPATH=models后：

1. `python -m unittest discover -s tests -v`：小型公式、相位、单位、rank、合同拒绝及线性拟合/剖面测试
2. `python models/diagnostics.py`：少量固定场景的Jacobians、半/双步检查、精确厚度别名和偏振混合诊断
3. `python models/batch_driver.py`：只计划，不执行完整批量
4. `python models/reader.py --directory .`：校验精确路径/字节/哈希，在隔离临时目录复制允许内容，再执行上述小检查并对照保存的diagnostics

`verification/tiny_driver`保存已执行的4启动任务路由结果。任何profile或fit有未收敛项都保留而非丢弃；此tiny样本所有路径有数值返回，也不能声称大批成功。不得为重现“小测试”自动运行默认完整batch。

## 6.5 审查、接受和停止边界

作者完成实现、原创推导、源码/结果自查、必要小测试与一次独立窄相位/量纲核查。实际窄核查角色为GPT-6 Luna，仅查指定范围；报告见reviews/independent_phase_dimensional_check.md。不把它冒充DeepSeek执行、Seed Pro阶段独审或Sol完整算法复核；这些指定链角色未实际完成，机器状态分别保持pending/not_run。

当前状态implementation_ready_validation_pending：条件算子和可审查代码完成，物理实验、用户设备、真实仪器适配、生产校准、重型性能/覆盖/全局搜索验证均not_run_awaiting_device或not_run。满秩与小残差都不是accepted/production-qualified。

freeze只在精确manifest/receipt、reader隔离自校和目录外变化核对后成立。哈希防意外字节变化，不是可信签名；有权改代码和清单者能同时改二者。若有已知并发根规划发布，保留原before，只按外部负责人确认的逐文件新hash归因，不静默重设基线。

下一有界交接只是建议，不自动启动。当前在本地freeze停止；不以还有可研究的理论为由无限加大扫描、启动设备或扩大范围。
