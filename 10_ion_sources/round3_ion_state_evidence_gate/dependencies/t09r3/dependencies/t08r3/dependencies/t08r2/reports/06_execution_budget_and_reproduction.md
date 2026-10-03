# 06 · 完整驱动、预算与复现

## 6.1 高算量driver先行，默认不跑

先建立完整batch_driver.py接口与预算计划，再实现算子/目标/诊断模块与必要小测试。默认命令仅打印plan_only，既不创建执行目录，也不启动拟合。全计划为4真值×3场景×3候选×2损失×16起点×(1次主拟合+41个d剖面网格+100次重复噪声)=163,584次拟合启动。

每启动上限1,200次完整观测向量评价，拟合调用天花板196,300,800；留出/信息导数按最多8簇、3个步长、最多6参数和3项候选保守计91,032次，合计196,391,832。该数不是耗时、单核调用数或内存预测。p≤6时一次二阶Jacobian有1+2p次函数调用，计划取13；新d偏置列解析加入，不额外占导数调用。每case真值生成两次已计入。

存储量可显著增长：每case/model/loss保存全部启动与剖面/重复拟合证据。当前无并行、自动重试、断点恢复、压缩或隐藏云作业；每完成一个分支写progress.json，已存在输出目录拒绝覆盖。执行前由用户选择机器和预算；设备失败或中断后的resume策略需后续显式设计，不能覆盖原记录假称连续完成。

全driver已实现所有声明分支。未跑完整批量，因此其长时稳定性、覆盖率、收敛比例、真实性能与资源占用都未验收。默认configuration中heavy_run是待运行描述；最终run_receipt中的heavy_run表示是否实际执行非tiny配置，二者字段所在上下文不同，不能据计划配置说已经运行。

## 6.2 命令

在本目录运行，建议固定PYTHONDONTWRITEBYTECODE=1、PYTHONPATH=models，避免缓存污染冻结包。

- python models/batch_driver.py：全计划，不执行
- python -m unittest discover -s tests -v：必要小型正确性测试
- python models/diagnostics.py：原创反例与两起点光学别名路由
- python models/batch_driver.py --tiny --execute --max-jobs 3 --max-forward-calls 191 --output verification/一个全新目录：3启动路由测试
- python models/reader.py --directory .：只读精确清单/内容检查
- python models/reader.py --directory . --isolated：隔离复制reader允许内容并跑小测试，不跑完整driver

未来完整执行需同时显式--execute、全新--output、--max-jobs 163584和--max-forward-calls 196391832。这里给出参数供安排，不自动调用。输出必须在当前增量目录内；用户日后应先复制到其选定设备并保持原冻结副本只读。

## 6.3 已执行证据与不能推出的结论

小型单元测试涵盖冻结核hash、条件矩阵恒等式、相关重复、未校准d偏置、奇异联合协方差拒绝、Huber分块、Σ/K分离、硬调用计数、多起点、剖面重拟合、单位、合同拒绝、谱节点色散、预算与k=0单边导数。具体通过数以verification/unit_tests.txt为准。

Tiny主拟合1启动收敛，低端profile在45调用满足ftol/xtol，高端profile在45调用耗尽预算而未收敛；共176向量调用、3启动，未隐去失败。此tiny只跑constant+Gaussian+clean，不能宣称全部大矩阵执行成功。其它候选/loss通过的小测试只能支持对应公式或接口，不代表全批验证。

独立核查只有一次GPT-6 Luna窄数学/量纲检查：相关条件信息、nuisance空间与校准/厚度偏置尺度。无该范围错误不等于全面工程审查；没有假称DeepSeek执行、Seed Pro阶段独审或Sol完整算法审核已经完成。

## 6.4 可移植性

Python参考实现依赖numpy/scipy/matplotlib；冻结记录实际环境版本，requirements只定义最低功能依赖，未锁住整个操作系统/BLAS。数值迭代次数可因库版本不同变化，必须分别看数学容差和执行账本；冻结hash保证输入字节，不保证各平台浮点逐位一致。原始论文PDF和提取文本只在本地originals区存档，不属于离线reader运行依赖。
