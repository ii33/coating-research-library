# 实现、复现证据与接受边界

## 交付与范围

只新增 `06_optical_coating_families/round2_process_optical_observables`。目录外文件在开工时取SHA256并在freeze时复查；T06实现没有触及首轮、其它topic、产品、root STATE或仓库元状态。开工快照至冻结期间，另一个已授权的规划发布任务更新了7个根规划文件；已由协调者及该任务提供逐文件当前SHA256确认，完整记在verification/concurrent_planning_changes.json。原始before快照保留，其余1097个目录外文件逐字未变；边界结果明确为passed_with_attributed_concurrent_changes，不能表述成整个项目零变化。未发现当前项目副本Git根，不把文件完整性快照冒充Git commit。没有push或上传；reader为普通目录，没有ZIP，没有论文原文。

本包为algorithmic阶段，实际作者/工具完成小数据实现与自审；来源核对和一次窄量纲/光学核查使用GPT-6 Luna。指定DeepSeek、Seed Pro、Sol完整阶段审核未实际运行，对应状态仍not_run；窄核查不能冒称它们的独立接受。状态为 `implementation_ready_validation_pending`，不是accepted或production-qualified。

## 复现路径

`models/build_inputs.py`生成严格schema和案例；修改它后须重建案例并复核变化。`process_optics.py`做输入验证和完整转换；`inference.py`是有界合成拟合、局部灵敏度与协方差；`batch_driver.py`默认只返回plan。`diagnostics.py`重建少量反例；`plot_figures.py`只画已保存结果，不另跑光学扫描。

单元测试以 `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=models python -m unittest discover -s tests -v`运行，日志在verification/unit_tests.txt。独立窄核查证据见reviews/independent_optical_check.md及独立测试文件。`data_qa.py`校验严格fixture、121点公共数据范围和vendor T07核逐字哈希；不读取论文原文、不依赖上游运行。

`reader.py`先验证精确路径允许列表、字节数与SHA256，再把唯一允许的payload复制到隔离临时目录，只执行小测试、data QA、默认plan和现存诊断再现对比。禁止符号链接/越界路径/额外文件/原文/ZIP。相邻项目目录不参与，未包含论文全文也不假称包含。PNG/SVG是本包原创图；源文献只以URL和原创摘要呈现。

SHA256用于偶发损坏/变更检测，不是可信签名。掌握清单写权限的人可同时替换代码与哈希，因此不构成抗恶意篡改认证。排除仅限清单自身、自校回执和目录外快照/对照文件及pycache/pyc；检查这些排除集合必须与代码一致。修改payload后须重新自审和freeze，不能沿用旧回执。

## 本轮已核实与未核实

已核实：单位转换的实现与合成算术；在声明域内被动稳定光学计算；有限不相干基片的能量分账；镜面/半球/检测值区别；missing/domain拒绝；合成非唯一/遗漏项的明确反例；默认不启动批量；局部reader无上游依赖。

未核实：实际沉积工艺→n/k响应；本机实际膜密度、组成、氧化、温度和历史；公共Al薄膜向假设基片迁移；实际散射与真实探测器卷积；大型网格/层数/角度/Monte Carlo收敛；指定审核链；设备速度/稳定性；量产工艺校准/接受。真实设备、物理实验和完整批量统一not_run。

上游必须继续保留：T02完整oracle partial；T03现有非负贡献优化器不接净侵蚀；点12离子参考not_run；tau非严格条件包络；T05单QCM源强/形状及etaQ不可辨识、QCM声学/温漂/工具因子未校准。当前研究包没有把这些合并成一个未知会自行消失的总误差。

## 不等于交付的行为

能在本地计算条件光谱，不等于测得实际材料参数；拟合残差很小，不等于唯一识别或模型无漏项；设备计划存在，不等于已经运行；单测通过，不等于生产验证；本地HTML reader不是部署网站。这些语义均在机器status与报告中保留。
