# 07 · 参考实现、重放与预算

## 7.1 双入口，避免保存文件取得权威

models/reader.py是离线字节/依赖/本地链接检查器，不调用优化器。它可以检查归档内记录与manifest匹配，但不证明数值结论正确。models/acceptance.py的evaluate只接受本进程replay_tiny创建并保持payload摘要不变的Session；手工Session或由JSON反序列化得到的对象拒绝。每次调用还对payload做内容指纹检查，防止重放后将UNKNOWN改成OUT。

replay_tiny逐一校验复制依赖、加载固定合同、重放双通道255节点、v=1.1切片最多31节点与(1,1)点。完整screen覆盖和witness经原API在本进程登记后，才调用optimize_bounds。保存结果仅用作fingerprint对照，从不直接传入优化API注册。进程内登记防误用，不是抗恶意Python代码或数字签名认证。

## 7.2 精确运行边界

driver默认plan_only，只打印计划；唯一执行选项tiny，要求新输出目录。显式cap为286节点、1148单波长包含调用、0浮点向量。实际每次tiny重放为268节点、977次包含核、0浮点搜索，无fallback。全计划/设备/多批/37配方都未执行，配額未绕过。

首次24主张replay、补入读数区别后的27主张final replay、单元测试共三次tiny重放，各自有记录；总调用不能只报告最后一次。verification/execution_history.json汇总三次实际重放与廉价静态/规则检查。修改报告、图形和reader不重新运行光学模型。

## 7.3 检查所覆盖的风险

27个案例含存在性、精确OUT切片、全称宽界/窄界/验证反例、min-J、gap、优化器失败、点响应/读数差别，以及真实用途、新状态、新算子、独立层、伪√N、不当概率化、unknown guard、猜客户规格和全谱过度结论。12项单元测试另覆盖反序列化对象、修改Session、目标剪枝保留、端点等号、float/NaN/反向区间输入等。

程序不会认证校准证书、判定照片真假、核实签名、估计真实协方差、生成真实覆盖概率或确定实际来源可达性。输入声明格式正确不等于科学事实成立；真实用途被限定scope gate阻止。

## 7.4 可移植读者和复现

解压reader包后，在包根运行：python models/reader.py。该操作不需要网络、浏览器或相邻T08目录。若要重新计算，则python models/driver.py --mode tiny --output verification/my_replay；这是新证据目录，故会被原精确manifest报告为extra，不能把带新结果的目录冒称原冻结包。建议在独立工作副本运行并单独保存新收据。

标准库即能运行核心逻辑；图形重建需要matplotlib，仅作离线原创图。reader.html没有script、iframe、远程字体或外部图像。PNG实际像素另审；HTML静态链接/结构可核，布局unverified，未重试受限headless/socket路径。
