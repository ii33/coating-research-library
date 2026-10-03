# T08 ROUND 2 · 带模型失配的稳健有限参数反演

离线入口：index.html。状态：implementation_ready_validation_pending，仅本地冻结；全部数值为合成条件。

核心交付：数据/校准/先验/模型候选分账、预算封顶多解发现、逐点重拟合剖面、相关误差留出预测、nuisance剖除后的候选测量条件信息增量，以及多解/偏置/相关噪声反例。

完整driver默认plan_only：163,584次拟合启动，最大196,391,832次观测向量调用，未运行。只执行必要小测试、tiny三启动和一次独立窄数学/单位核查。Tiny低端剖面由局部容差终止，高端剖面未收敛，原样保留。用户硬件未知，不阻断理论，也不虚构仪器、实测或生产验收。

复现：PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=models python models/reader.py --directory . --isolated

主要目录：reports为七章原理，models为参考实现与逐字冻结vendor，tests为小型正确性检查，verification为运行证据，sources为原始来源注册和原创摘要。sources/originals中合法公开下载PDF及提取文本仅本地保存，不进入reader允许列表。

有限搜索、局部满秩、很小残差与收敛状态均不是全局唯一或物理真值证书。发布与设备验证另行安排。
