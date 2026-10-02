# 接口、执行协议与结果字段

## 1. 设计域

`Plate(name,bits,nx,ny,pitch_m,center_m,thickness_m)`：当前只支持水平、实验室固定格点板，pitch是最小格宽；1=有限厚实体，0=开口，不发出灰度制造参数。每个实体分块使用冻结v0.2 tri-state矩形求交。两个板槽可以为空以表达无板基线。xmin边由外部支承条件连接，支架遮挡/热变形不在此核中。`Manufacturing.check`的空结果只表示合成几何合同通过，非机加工认证；完整包络分离是充分而偏保守的板间检查。

`neighborhood`为有上限局部单步提案；`discrete_space`惰性枚举二进制×位置catalog×厚度catalog，可在完整有限集合预算内作穷举过滤。`max_candidates`是截断预算，不是全空间收敛证明。Search消费唯一候选列表，预测器只排序；每个结论仍经oracle计算。

## 2. 正向数据合同

`Ray(channel,point,time,source,target,contribution)`中contribution是已乘源权重/时间权重的非负原子或离子注量。禁止用蒸气权重或几何默认代替离子。`RayBundle`携带面积权重（0为独立见证）、共同时间分组/时长、原子密度、单能离子能量、无板平均厚度、provenance、误差来源和local_margin_m。

本次实现消费显式RayBundle，并未凭输入尺寸重建完整运动/连续源积分。设备上的bundle生产器必须保留source节点/法向/指数/率/时钟/运动/物种/材料及代码版本；这些都进入完整bundle与oracle哈希。`finite_fixture=false`时对每个N/D×point强制覆盖source/time/space/geometry/kernel/input/model七轴，任意遗漏、越界或非法point拒绝。未知轴半径为null，经验估计半径只能estimated。各轴有来源，不能偷偷设零。

数据序列入构造器即复制为tuple；provenance深拷贝。RayOracle持有bundle副本并检查冻结digest，防止构造后变更权重/错误点使旧签名生效。几何cache只保存(source,target,plate,margin,predicate-hash)的三态结果；完整加权key另包含全部bundle和算法版本。默认内存LRU16条，不持久化缓存，不携带到发布包。

局部几何unknown已在有限贡献区间内传播，error_sources同时记录point和time_index，**不会再重复widen**。有外给N/D累计误差却没有独立事件误差证据时，tau同样未知；小积分误差不使存在性时长获证。N分母跨零令R/epsilon无定义；Nlo>0而Nwidth>=Nlo时标ill_conditioned，保留诊断界，但R/epsilon资格unknown。

## 3. 决策与结果

所有约束均为g<=0：throughput=min_required−actual；ion_lower=max_p(lower−ion_p)；ion_upper=max_p(ion_p−upper)；h_target_deviation=max_relative_deviation−limit；ion_only_duration=max_p(tau_p)−limit。不存在或未配置的约束不会被隐式填阈值。所选离子变量为D或epsilon。

每项measure包含lo/hi、unit、status、errors、definition；null/null表示无界/未知而非零。逐点返回N_net、h、D、U、R、epsilon、tau、area_weight与ratio_conditioning。汇总返回均厚、吞吐/比值有效区域诊断；样本/见证最大偏差不冒称连续极值。

`compare`先检查oracle_signature、字段集合、units/definitions，再检查相关资格与可行性。双方可行且A所有目标上界<=B下界、至少一项严格小才A支配。反向已分离的目标为tradeoff，其余为inconclusive。顶层partial可能仅由未用作约束的tau未知造成；相关h/D条件界并不因此自动失效，也绝不使tau获证。

结果的 `certified_feasible_nondominated_ids` 是“有条件可行且未被已证明区间支配淘汰”的候选，不代表真实Pareto成员证明；archive_semantics明确限定。`unresolved_ids`保留相关未知或重叠候选；refinement_requests列候选、fidelity、axis、field、point_ids、time_window_s、action与是否数值加密可解决。input/model缺口须新证据，source/time/space也须新bundle/job，不自动将误差减半。跨签名/不同求积/不同校准结果禁止偷偷混比。

## 4. 控制与checkpoint

执行顺序：制造筛查 → 按完整estimate预留evaluations/rays/source_samples/point_time_samples/time_panels/plate_tests → oracle → 按候选顺序合并 → 原子checkpoint → 进度事件。重复几何cache可少做实际predicate，但保守预留不退账。失败/崩溃后的预留仍保留，因此重试不会重复消耗未记账算力。

checkpoint含schema、候选表/排序、oracle与制造合同signature、已评价记录、拒绝表、cursor、预算、失败；文件含payload SHA-256并原子替换、fsync。版本变更或低于已用量的新预算拒绝恢复。SHA用于完整性，不是防恶意篡改的身份签名。取消在射线/聚合chunk/点块之间检查；单次分数求交不抢占。wall_seconds为合作式停止界，不能保证操作系统硬中断。

串行后端可直接运行。受控本地线程最多4，必须explicit allow_parallel；只按原候选顺序合并，异步完成次序不改变输出。checkpoint写者只有协调线程。此版本没有GPU内核、远程任务提交、进程池或跨设备锁；禁止多协调器写同一checkpoint目录。

## 5. 与设备runner互通

`T03-device-request-v1`是JSON请求。每job含job_id、fidelity、device_ready、inputs、work_shape、limits、objectives、manufacturing、acceptance。inputs可为单ray_bundle或ray_bundle_chunks；每文件提供path与sha256，路径限定input-root内。点块条目另含point_count/time_panels/ray_count；每点保留全部时间/源，不能跨时间块相加后假装tau事件已处理。

`ChunkedRayOracle`逐块加载、核对计数、独立三态积分，再合并全局point IDs、条件区间目标max、加权mean/throughput和所有错误位置，不假设各块误差独立。同一原子密度/离子能量/无板基线必须一致。每块释放射线，cache仅1条；结果保留点值、标量统计而非射线。分块输入须用全域面积权重，不能每块自行归一化后冒充真实面积。当前协议无法替上游证明没有重复物理点；设备生产器须校验partition唯一性和几何/clock/误差来源一致。

无 `--execute` 只输出plan；高保真默认device_ready=false、path/hash空，因此无法假装已经执行。完整算量不在本云端跑。--execute验证总ray预约上限、输入SHA、实际shape/source计数、候选数和板测试上限。输出每job results/checkpoint和execution_manifest，含config哈希、状态、决策、gpu_executed=false。已有T02 `point_*.json`可经import_t02_evidence读取来源资格，但不转换成认证候选目标；点12缺失仍缺失。
