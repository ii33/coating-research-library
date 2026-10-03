# 05 · 完整驱动和资源账本

## 5.1 默认不执行

budget_driver.py默认mode=plan_only、plan=full，只校验输入并打印计划。完整有界矩阵仍只处理本六层二维域：M0与M0+M1两种观测，各自节点上限127、511、2047、8191，合计8个作业。它不是无限维研究，也不是37条配方重优化。所有分支用同一个已实现的run_plan循环，full从未执行。

执行需同时显式mode=execute、plan、三个足够覆盖最坏费用的上限和本增量目录内的新输出目录。重用已存在目录或域外输出被拒绝。没有并行服务、设备选择、云作业、自动重试、断点续跑或宿主机quota绕过。未来运行完整计划仍须另行授权机器和预算；代码给出能力不等于已经取得执行权限。

## 5.2 精确收费口径

Tiny上限为349节点、1337次单波长包含调用、10个浮点完整观测向量。作业为M0二维63节点、双通道二维255节点、v=1.1切片31节点、零预算二维域。搜索从(1,1)最多9个浮点向量，再从(z_lo,0.9)给1次；最多验证一个见证，共4次包含调用。每个浮点向量有4个波长核，本次总40次浮点波长核。目标/约束有理区间和覆盖校验不增加光学核费用，但仍消耗CPU，不能把计数说成耗时预测。

完整计划最坏节点数是21752，包含上限76136（M0每节点3、双通道每节点4，加见证4），浮点向量10。终端实时耗时和这些逻辑上限是不同量。内核失败在调用前计费；搜索的候选提议不收费，实际进入前向才收费。外部库max_nfev可能不含差分Jacobian额外调用，SciPy官方说明正是为什么不能用库计数代替模型账本[BS-S04]；本轮使用自带有限pattern search，不调用SciPy优化器。

## 5.3 复现命令

在本目录执行，先设置PYTHONDONTWRITEBYTECODE=1，避免污染冻结文件。Python标准库即可完成数值核、测试与reader；matplotlib/Pillow只用于重绘PNG/SVG。

- python models/budget_driver.py：只读完整计划
- python models/budget_driver.py --plan tiny：只读tiny计划
- python -m unittest discover -s tests -v：窄范围正确性/反例与13节点排除、见证复算
- python models/reader.py --directory .：精确清单、复制依赖与静态链接检查；不需要旧项目目录
- python models/budget_driver.py --mode execute --plan tiny --max-nodes 349 --max-interval-wavelengths 1337 --max-float-vectors 10 --output verification/new_tiny：在解压副本中新目录复现，不改冻结原件

full计划的执行接口已实现，但本手册不要求读者运行它来验收tiny，也不把full长时稳定性、内存或性能算为已通过。

## 5.4 实际执行历史

初次尝试在普通浮点适配器遇到Fraction字符串19/20不能float转换，尚未进行区间工作即停止；修正为显式float(v)，同时保留精确候选坐标。失败目录及错误说明保留。随后tiny完成一次。窄审推动见证/覆盖记录来源检查后，以相同小上限再次执行最终tiny，验证最终driver路径；不是新增大规模参数扫掠。两次成功tiny各331节点、1166包含调用、10浮点向量。verification/tiny_final为报告基线，早先结果仅保留执行历史。

单元测试、隔离复算和窄审各自有独立小费用，不混入最终tiny账本。单元测试重算13节点切片、两个点验证（8次波长包含）和2次预算中断内核；reader隔离测试同样执行。窄独核最多16次单波长包含。所有记录的用途、版本和边界需与主tiny分开读。
