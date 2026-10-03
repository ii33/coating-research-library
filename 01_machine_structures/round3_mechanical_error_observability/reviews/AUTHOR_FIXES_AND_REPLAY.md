# 独立发现后的作者修复与定点重放

2026-10-02 UTC。这是作者修复记录，不是新一轮独立审核，也不宣称原审核者已签署最终代码。初次INDEPENDENT_REVIEW.md和independent_results.json保持原始失败身份。

## 修复

- R1：共同时间构造后再检查有限性与严格递增。溢出及大offset吞掉间隔时拒绝，提示使用相对时间原点，不补点或静默去重
- R2：逐CSV行验证恰为两个字段，无额外列或缺失值；header匹配不再代替行级验证
- R3：保留B奇异谱和相对稳定性门槛max(tol,√机器epsilon)。干扰子空间病态时rank=null、rank_status=unresolved_nuisance_subspace、协方差/条件数=null。名义截断rank及null向量有明确条件标记，不作为数据可辨识证据
- 静态加固：原CSV只读一次bytes，hash与解析使用相同bytes，关闭两次读取间内容变化的身份缺口

R3是保守拒绝诊断，不是严格精确秩求解器；可能把数学上可合并的完全冗余列也标未决。需要结合模型证据消除冗余，或采用有依据的干扰约束/更稳健参考，不能直接放宽门槛追求满秩。

## 复测

作者新增两个unittest方法覆盖以上3个运行反例和两档tol，总数从29变31，最终通过。另原样调用独立脚本，输出另存repair_replay_results.json；核心数学检查通过，错误CSV及两种错误共同时间均被拒绝，病态干扰两档tol均返回conservative_unresolved，无有限协方差。最终实现hash及相关报告hash都在重放记录中。

初次独立结果SHA256：7c6339f47ff1a674699d815ad7bec7380276b2926adc63dd8b10f5e1aeb26704。重放记录只对应其输入hash；任何未来改动需新版本，不能覆盖此证据。独立脚本已变为默认stdout，只有显式--output才写，避免读者复算覆盖初次失败。
