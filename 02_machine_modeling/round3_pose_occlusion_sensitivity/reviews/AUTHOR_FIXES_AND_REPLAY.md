# 作者修复与定点重放

唯一一轮窄独立检查找到一个接口一致性缺陷：正常参考核已对近合并事件给出event_order_unresolved，但闭式Dual oracle缺相同门控，仍可能返回七维普通梯度。复现为Scene(half_width_m=1e-11)，两个事件间隔约1.25e-10 s，小于2e-10 s门槛。

作者在analytic_oracle端点检查后补入事件间隔检查，拒绝该分支，并加入unittest回归。没有改事件公式、输入几何或前轮状态。`author_replay.py`单独验证reference仍拒绝、oracle现在拒绝、普通分支保持一致；输出在repair_replay_results.json。初始independent_results.json及其哈希保持不变，没有假装原轮全通过。

这是作者定点修复和重放，不是第二轮独立审核。正式DeepSeek V4.1 Flash执行/自审、Seed 2.1 Pro独审及GPT-6 Sol High算法签署均未发生，仍pending。库内的模型名称仅为未执行的指定角色说明，不是这次实际调用证明。

随后作者在未执行的device driver中补上源级、光滑阶数、跨源族的梯度独立差异记录。只做语法和plan_only检查，heavy路径保持not_run；唯一独核对driver的结论仅对应初始静态门控，不是后续新增比较汇总的执行验证。
