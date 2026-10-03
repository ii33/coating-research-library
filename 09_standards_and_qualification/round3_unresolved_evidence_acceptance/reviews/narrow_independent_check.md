# T09R3 窄范围独立规则检查

范围：只读检查 `models/acceptance.py`、`cases/claims.json`、`verification/tiny/results.json` 及复制的 T08 `candidate_sets.py`；未运行 optical replay、heavy 任务或 formal chain。未发现所查规则的具体反例。

1. **全称命题与 UNKNOWN 保留**：`all_v_in` / `all_J_in` 的 `ret` 包含全部非 OUT 且非已证实约束 VIOLATED 的叶子，所以包括数据 UNKNOWN，也包括目标界剪枝叶。Tiny 当前结果快照汇总为 32 个 retained UNKNOWN，其中 15 个目标剪枝 UNKNOWN。全称范围外包络穿界时返回 `retain_unknown`；只有 `proxy_feasible` 的已验证见证区间严格落在范围外才 `reject_claim`。快照中 `all_v_narrow_lower` 是穿界但 UNKNOWN；`all_v_counterexample` 因已验证见证 `[1,1]` 落在 `[1.01,1.1]` 外而拒绝。
2. **min-J / gap 量词和比较**：阈值及边界均用 `Fraction`。`minimum_J_le` 按存在性命题处理：经验证的上界 `hi ≤ t` 才条件接受；外松弛下界 `lo > t` 才拒绝；其余 UNKNOWN。快照括区间为 `0` 至 `1 + 43/2^80`；阈值 `1.01` 接受、`0.25` UNKNOWN、`-0.01` 拒绝。`gap_le` 仅在精确 `hi-lo ≤ t` 时条件接受，宽括区间只保留 UNKNOWN，不用来反驳真实最优间隙。
3. **JSON 不是活动证明**：`acceptance._proof` 要求进程内登记的同一 Session 对象和未变更 payload digest；`replay_tiny` 重新运行预算内计算，只把存档结果用于指纹比对。复制的 T08 优化器也要求进程内登记的 screen / witness digest。因此单独载入的 JSON 不能充当 live proof。此项按代码静态核验，未执行回放。
4. **来源与生产结论**：`source_exists` 明确返回 `blocked_evidence`（proxy-IN 不证明 source/Q-rho reachability）；结果构造器固定 `production_release=false`、`physical_certification=false`，formal stage 为 `pending`。未把 synthetic 结果提升为来源、实测或生产结论。

**范围/快照说明**：检查时 `claims.json` 已有 27 项，但 `verification/tiny/results.json` 仍是 24 项快照；新加入的 `observation_M0_in` 三项尚未从该结果快照确认，只静态检查了其精确区间比较分支。因此本文的例证仅指该 24 项快照。明确未执行 DeepSeek / Seed / Sol 正式链或任何形式化验证。
