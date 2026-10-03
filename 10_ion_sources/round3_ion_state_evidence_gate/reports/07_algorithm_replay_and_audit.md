# 07 · 完整参考算法、有限执行和精确审计

## 可运行的实现

- state_physics.py：常值bin精确状态解、缺陷埋藏积分、率盒比较传播、联合能角反例、质量闭合光学反例
- evidence_gate.py：父合同重建与hash验证、输出特定证据分流、新state派生、净/库存守卫、硬界等价判据
- driver.py：默认plan_only；tiny最多32个gate案例、16个模型bin、8个joint cells、20 s；offline_packet只作离线声明证据评审，不与设备连接
- reader.py：精确文件集、SHA256、复制依赖和HTML静态链接检查；不跑数值求解

参考算法从输入到输出完整实现，未将未实现的实机适配器伪装为driver。重计算使用新工作副本与新输出文件，已有路径拒绝覆盖。CLI没有heavy模式；未来实验识别、大扫参与新光学重建只出计划。

## 本轮实际执行

24个gate案例覆盖旧合成准入、变化/未知state、operator hash变化、实际数据冒用合成常数、六类暴露缺项、侵蚀/跨零/近零/库存耗尽、带电能流特例、无过程史的样品观测和密度缺项。11项轻量单元测试另含解析极限、积分稳定性和非有限数拒绝。修复前后tiny各显式执行一次，修复前后单元矩阵自检各调用一次相同tiny函数；均不是独立实验重复，运行次数在execution_ledger中逐条列出。

上游光学内核调用0次、真实设备调用0次。图像制作只对固定原创合成小例画图，不是大规模优化验证。一次窄独立单位检查的范围和发现单独记录；未完成正式DeepSeek执行、Seed阶段审查和Sol算法审查，formal_review_chain保持pending。

## 重现入口

    python models/reader.py
    python models/driver.py
    PYTHONDONTWRITEBYTECODE=1 python models/driver.py --mode tiny --output verification/new_tiny.json
    PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v

前两条在冻结reader可直接运行。后两条会生成新执行记录，应在解压副本中进行，不把它们覆盖成原冻结证据。Python标准库即可跑本轮核心；复制的上游算法保留自己的依赖要求，但本轮不执行它们。画图需要matplotlib，HTML使用内置的有限Markdown子集渲染器，不依赖外部包。

## 两层收据而非自签名

manifest精确列payload路径、字节和hash。外层receipt绑定manifest与zip，解压后没有siblings也能运行reader、default driver并加载复制父合同。控制收据不自哈希，排除集合明确列出；负例检查须拒绝改字节、缺文件、增文件、重复manifest路径。任何hash都不证明实验真实、量值溯源或作者身份。

原始论文不入包，内部账户/消息/工具标识不入包。原创SVG/PNG用于报告；PNG需实际像素查验。HTML只静态链接核验，布局unverified，不重试既有受限headless或socket路线。
