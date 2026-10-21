# 0a631b7 宽带高反生产入口验证

基线：0a631b7428486ab08fe0f27aa8938c50783f5280。云端原clean checkout仅作快进更新；未修改源码、未发布、未操作用户电脑。旧438da39证据完整保留。

## 结论

以下是从零运行真实生产入口的有界集成证据，不是单元测试结果，也未注入此前研究处方。

- 32层候选覆盖已生效：12/24/32层各30个提案，共90个。
- 两次搜索均seed0、1worker、数学线程1、120秒，顺序运行。仅训练采样由5 nm改为1 nm及其派生冻结元数据变化。原材料色散/全部已知k、400–700 nm、0°/30°各s/p、R≥0.98、32层和10–500 nm/层及总≤5000 nm均不变。
- 审计乘数保持5不变，因此5 nm请求独立密网格为1 nm、偏移0.5 nm；1 nm请求独立密网格为0.2 nm、偏移0.1 nm。这是采样步长变化的派生结果，不是额外放宽参数。

## hr_broad_visible_5nm

- 停止：state=cancelled，termination_reason=cancelled；120秒runner计时器触发协作取消，入口总耗时120.249471秒（含清理），未延长搜索。
- 训练最坏R=0.959325426492，555.000000000 nm，30° p。
- 返回候选只读独立终审最坏R=0.959279422887，554.280052983 nm，30° p。
- 是否达到0.98：否；生产overall_raw_success=False。
- 反馈实际计数：revision=3，网格外点12个，repair_stages=1，local_stages=2，额外父级评估141次。真实algorithm_progress反馈事件：{'audit_incumbent': 3, 'validation_complete': 3, 'audit_feedback_added': 3, 'structural_local_refinement': 1, 'audit_feedback_repair': 1}（已排除heartbeat重复快照）。
- 候选身份SHA256：65a6030da883da5c82b5dbad54eaf7a190dcd5ccfed19210daf252b20ca03a5d；层数32；运行内训练/审计身份一致=True。
- 保留审计checkpoint身份：65a6030da883da5c82b5dbad54eaf7a190dcd5ccfed19210daf252b20ca03a5d。
- 清理：{'active_worker_pids': [], 'cleanup_complete': True, 'execution_state': 'closed'}。

|角度|偏振|独立终审最低R|波长/nm|
|---:|:---:|---:|---:|
|0°|s|0.967627812987|400.000000000|
|0°|p|0.967627812987|400.000000000|
|30°|s|0.967645006520|685.880219957|
|30°|p|0.959279422887|554.280052983|

## hr_broad_visible_1nm

- 停止：state=cancelled，termination_reason=cancelled；120秒runner计时器触发协作取消，入口总耗时120.350874秒（含清理），未延长搜索。
- 训练最坏R=0.957951409614，400.000000000 nm，0° s。
- 返回候选只读独立终审最坏R=0.957951409614，400.000000000 nm，0° s。
- 是否达到0.98：否；生产overall_raw_success=False。
- 反馈实际计数：revision=2，网格外点8个，repair_stages=1，local_stages=2，额外父级评估147次。真实algorithm_progress反馈事件：{'audit_incumbent': 2, 'validation_complete': 2, 'audit_feedback_added': 2, 'structural_local_refinement': 1, 'audit_feedback_repair': 1}（已排除heartbeat重复快照）。
- 候选身份SHA256：f477669f8d10725b5e144e7933cd99491bb84d618ed017007b30f9898847f42e；层数32；运行内训练/审计身份一致=True。
- 保留审计checkpoint身份：f477669f8d10725b5e144e7933cd99491bb84d618ed017007b30f9898847f42e。
- 清理：{'active_worker_pids': [], 'cleanup_complete': True, 'execution_state': 'closed'}。

|角度|偏振|独立终审最低R|波长/nm|
|---:|:---:|---:|---:|
|0°|s|0.957951409614|400.000000000|
|0°|p|0.957951409614|400.000000000|
|30°|s|0.968716070542|601.219130613|
|30°|p|0.958447906308|700.000000000|

## 反馈是否覆盖训练未达标候选

源码的archive即时审计仍以训练达标为门槛；但反射器裸基底、结构局部精修后及后续阶段存在直接audit_archive调用，所以训练未达标候选仍有生产入口进入独立审计。只有已完成审计中位于原训练网格之外的失败点被加入反馈。局部修复还需要非空镀层、预算余量且目标未验证通过。

实际运行的repair_stages、固定快照局部工作计数、algorithm_progress事件和checkpoint原始训练未通过标记共同构成集成触发证据，不以187项定向回归替代本结论。每次局部调用保持单一不可变反馈快照，训练评分和原始独立审计仍分开保留。

注意：取消/时间边界的返回分支按completed training best冻结候选，不无条件返回audited_best。因此本报告同时保留返回候选、运行内审计和best-audited-checkpoint身份；不得将另一候选的审计嫁接为返回候选的成功。

## 旧窄陷波处方只读回归

- 旧训练minR=.9671293120处方，在新生产审计中最坏R=0.212431280889，λ=407.702180065 nm，0° s。
- 审计是否通过：False。旧窄陷波仍被拒绝，没有计入新的默认自动算法成功。

## 证据与限制

- proposal-coverage.json：真实提案入口90个候选的层数与身份。
- paired-request-differences.json、request-*.json：成对冻结请求及逐字段差异。
- 每次运行目录中的progress.jsonl、result.json、best-audited-checkpoint.json、candidate_layers.csv：真实生产流程、候选身份与层厚。
- independent-audit-*.json、independent-summary-*.json：预算外只读终审，未增加搜索/修复，也不把事后终审当生产新成功。
- feedback-trigger-source-evidence.json：精确源码行与触发条件；source-identity-before/after.json：提交与源文件校验。
- preflight-failed.log记录一次搜索计时前的验证包装清单摘要配置失败，修复的仅是研究目录中的包装脚本；没有运行算法，也未重置任何已消耗的搜索预算。
- 仅每种采样一次seed0/120秒，不构成成功率或全局最优证明。有限密网格/偏移/括住的极值不是连续光谱证明，更不是制造公差或实验认证。
- 最终检查：{'commit': '0a631b7428486ab08fe0f27aa8938c50783f5280', 'source_unchanged': True, 'git_status': '', 'old_evidence_archive_unchanged': True, 'production_runs': 2, 'extended_search_budget': False}。

