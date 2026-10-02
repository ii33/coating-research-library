# 第二轮优化器设备验证计划

日期：2026-10-02 UTC  
状态：fixture有限测试已记录；高保真设备计划全部 `not_run_awaiting_device`

## 1. 当前结果与计划状态

留存的synthetic fixture结果包括15个计划候选、13次oracle评价和2项制造约束拒绝，决策状态为 `inconclusive`。`verification/unit_tests.log`记录40项主套件测试通过；该数不合并独立审查，也不表示完整算法或物理模型通过。结果见[fixture摘要](../data/fixture_results.json)。

另有三个独立的高保真device job，每个job登记24个candidate slots。这24是设备计划规模，不是上述15个fixture候选，也不是已经评价的设计。所有jobs当前未运行，ray-bundle chunks和designs的输入路径/SHA都尚为空，物理认证为false。当前T02连续正向oracle仍partial；新计划不会升级其状态。

`RayOracle`接收调用方提供的有限、非负、已乘源与时间权重的RayBundle；`fidelity`不自动细化。chunked adapter允许每次仅载入一个工件点的bundle，保留该点的完整源节点和所有时间panels，不删节点或降采样。此功能控制材料化内存，不证明连续source/time积分误差。

## 2. 工作量拆分

每个job都分别记录candidate、通道、point、time panel、source node、ray与opaque-cell几何测试数。RayBundle中每条ray已有channel/point/time及带权贡献；当前预算口径为 `source_samples=ray_count`。geometry tests为 `ray_count × max_opaque_cells` 的预留上界；源积分节点及时间节点在bundle中已展开，运行器不从当前前向模型重新生成。工作单位不是FLOP或GPU吞吐。

| 未运行job | 候选 slots | 点数 | 时间panels/点 | source nodes/时间（vapor+ion） | 名义射线数 | 单点chunk rays | 单chunk基础内存估计 |
|---|---:|---:|---:|---:|---:|---:|---:|
| training | 24 | 13 | 509 | 39 + 39 | 12,387,024 | 39,702 | 7,622,784–30,491,136 bytes |
| independent_holdout | 24 | 17 | 997 | 115 + 115 | 93,558,480 | 229,310 | 44,027,520–176,110,080 bytes |
| area_validation | 24 | 236 | 1531 | 115 + 115 | 1,994,464,320 | 352,130 | 67,608,960–270,435,840 bytes |
| 合计 | 3 jobs | 266 | — | — | **2,100,409,824** | point_chunk_size=1 | — |

每个chunk保留对应point的全部time/source组合。ray chunk目录条目要求 `path/sha256/point_count/time_panels/ray_count`；runner先依据元数据预留工作，加载后再检查bundle实际长度和源计数。当前device plan的 `ray_bundle_chunks` 为空，因此这些是dry-run预算而非已提供的数据。

基础内存范围按192–768 bytes/ray估算；计划另含2–6倍的parse/copy/cache峰值乘数，但该乘数尚未设备测量，不是RAM/显存承诺。可见性cache和并行workers的真实峰值也要设备测量。ray、point、time、source、几何命中、内存的账分别保存，不能把不同操作加总假称FLOP。

## 3. 硬限额与执行边界

配置的全局ray reservation上限为 `2,100,409,824`，正好覆盖表中三项名义ray总量，不留未登记扩展空间。每个job同时设candidate上限24、与上述对应的ray/source/point-time/time-panel/plate-test各维硬限，以及墙时上限86,400秒。实际limits见[设备计划JSON](../verification/device_validation_plan.json)；目标中的 `h=1e-7 m`、`D=1e18 m⁻²`、吞吐0.7是占位条件，必须在判读前由用户/项目批准研究目标替换，不可当产品门槛。

`Search.Limits`通用默认值仍是100 evaluations、100,000 rays/source samples/point-time samples/time panels、1,000,000 plate tests和60秒；设备任务通过配置显式覆盖。`device_runner`当前默认单worker；并行须显式 `--allow-parallel`，最多4 workers。设备提交、执行队列和串行调度由主代理管理；本报告不表示已经启动。达到任一配置限额就停止并记录已完成候选及partial状态，不自动扩额、粗化网格或将缺失块补零。checkpoint位于候选边界：候选内部point chunk中断时，该候选未合并结果不记为完成，恢复时重算该候选；已预留预算不退回。

当前没有观测CPU/GPU型号、驱动、峰值RAM/显存、ray/s或完成时间。runner未提供GPU实现，GPU加速 `not_measured`；估算和既有fixture耗时都不外推设备性能。

## 4. 设备工作步骤

1. 只做plan-only预算检查：确认候选设计文件与全部point chunk文件路径/SHA、每块point/time/source元数据、global/per-job limits和输出路径。若任一输入无哈希、路径超出输入目录、bundle形状/源数不符或预留超限，拒绝执行。
2. 先运行有限合同回归：几何三态、opaque并集、独立通道、单位、分母跨零和ill-conditioned ratio处理、区间重叠返回inconclusive、checkpoint恢复及输入hash一致性。40项主测试的当前日志在上面引用；新改代码须报告新的对应测试结果。
3. 仅在输入合同和目标得到确认后，按training→independent_holdout→area_validation三批加载point chunks；每块处理完整source/time，不混合候选/通道缓存，先预留后核验实际cost，保存每候选错误轴和不确定结果。
4. 记录硬件可见状态、线程、峰值内存与观测墙时；这些是该设备本次实测值。遇预算/输入/积分告警后按原状态停止，不以增加网格追求全绿。
5. 训练集只供候选探索；independent holdout和area validation不得回流为训练后仍称独立。区间重叠要保留 `inconclusive`。本计划设置当前三组有限job，不能声明所有连续空间点、所有时刻或全局最优。

## 5. 数据来源最低要求

当前fixture和待运行计划都不是实机成膜数据。若未来提供物理RayBundle，须有可追溯双板有限厚几何/位姿/二进制分块/测量margin；蒸气、离子各自的源分布、能量/角分布、rate与连续时间变化/已知频带；工件和夹具位姿、运动相位、面积权重及留出点；材料净留存、密度、再溅射、仪器误差；经确认的h、D或epsilon区间、throughput和tau定义；N、D各自的七轴误差来源 `source/time/space/geometry/kernel/input/model` 与单位。未知量保持unknown；不能因ray bundles已有有限点就推断真实source support被覆盖。

T02的点2 τ仍依赖连续源支集及时间事件，点12离子紧参考未运行；T02误差估计和网格差不自动升级为候选总误差严格上界。C/I结构源图仍unsupported。

## 6. 结论口径

高保真计划一旦执行，最多说明这些登记候选在指定输入哈希、误差轴、离散point/time/source集合、预算与设备上的表现。`bounded_conditional`结果限于这些条件；若objective/constraint是estimated或unknown，就保留inconclusive。15候选fixture的当前决定已经inconclusive，不能选出生产最优板。有限候选截断不构成全局最优证明，完整T02 oracle仍partial，`physical_certification=false`。

本计划参照[device runner](../models/device_runner.py)、[chunked oracle](../models/chunked_oracle.py)、[Search/Limits](../models/optimizer.py)、[device plan dry-run](../verification/device_plan_dryrun.json)、[fixture results](../data/fixture_results.json) 与T02 [T03 handoff](../../../02_machine_modeling/round2_dual_coverage_error_budget/T03_ROUND2_HANDOFF.md)。所有未运行项均保持not_run标记。
