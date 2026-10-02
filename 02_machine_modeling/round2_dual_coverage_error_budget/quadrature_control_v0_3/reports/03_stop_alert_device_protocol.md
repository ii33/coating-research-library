# 可复用停止/告警协议与设备验证待办

## 0. 先声明可解释的任务合同

每次新输入冻结：几何/源分布/运动版本与哈希、units、通量正支集或用户另行授权的物理阈值定义、rate事件/带宽/导数依据、源/time/空间误差预算、相对量分母、最大算量和停止条件。没有输入合同先标unsupported，不用更大网格掩盖缺口。本目录原预登记有修订记录，绝不倒写成“事先没打算跑”。

## 1. 分别为积分与duration选择方法

- 积分：优先显式几何分段，非负区间积分；硬阴影落在积分边界。局部source自适应、time自适应分别记录容差、evaluations、warning及误差估计；保留异族/非二倍时间/相位错开对照
- duration：在连续源支集上做几何事件。只要rate不严格正，增加rate零区间事件逻辑；当前driver对此标unresolved，不偷换成源盘支集
- unknown几何：下界按不透射，上界按可能透射；duration用逻辑区间传播。不能在一个bool里丢掉unknown
- near-zero积分：绝对容差必填，相对误差可能无定义；比值须检查分母下界>0。只在δN、δD是可信界且N_ref>δN时才可推比值界；估计差不能冒充这些δ

## 2. “通过”标签必须带证据等级

1. `analytic_truth`：独立解析量作比较；数值输出仍需区分普通浮点与validated arithmetic
2. `conditional_lipschitz_enclosure_not_validated_float`：全时间区间排除及显式guard，但guard未严格证明；保留条件
3. `reference_estimated_not_strict_bound`：低维/更强参考和异方法佐证，无严格包络
4. `warning_unresolved`：QUADPACK warning、达到limit、误差目标未达或事件未决
5. `not_run_awaiting_device`：算法/driver完成，实际验证尚未做
6. `physical_certification=false`：本增补所有输出都固定为false

设备的reference agreement只要求有限精度级之间一致且无warning，明确不表示严格误差认证。若要认证，另做validated trig、几何区间、导数界与嵌套积分误差传播；不能仅把容差调小。

## 3. 固定停止/报警规则

- 固定case/level清单完成就停，不因结果没全绿无限增加级数
- 到预算/墙时上限：落盘已完成point和partial reason，不伪造缺失结果，不静默粗化
- 任一source/time warning、输入投影分母不合法、rate带宽未知、rate零支集尚未处理、近零分母或unknown区间超目标：停止对应判定并标unresolved
- 两个估计相近不能独自过关；非二倍/错相位明显分离直接报警。已知频率要显式拆周期，不能靠自适应偶然撞到脉冲
- 主图/空间均值平稳不能取代source/time精度；sample PV不是连续最大值
- 候选目标区间重叠不排序；参考只为估计时，优化应保留稳健性告警，不能声称已找到可靠最优

默认积分相对门槛0.003、duration绝对门槛10ms沿用历史。参考base/tight检查使用max(2e−6 s/m²,5e−5×|参考transfer|)，事件条件区间宽0.1ms；这些是研究预设，不是实机产品容差。

## 4. 设备上真正要跑什么

[设备配置](../verification/device_validation_plan.json)是执行合同；[driver](../models/device_driver.py)默认不算，只有`--run`执行。数值函数及rate仍严格有限在本合成D输入域。

第一批建议selected点2/12：

- 两级source/time低维参考；source rel 2e−8/2e−10，time rel 2e−7/2e−9；事件leaf 1e−8s
- 固定网格16×128/T4096、异族32×257/T8191/phase0.271828、64×512/T16381
- 核查点12离子0.203%真实误差；复核点2duration条件包络；比较点2蒸气已有单个base值
- 不改参数继续生成全绿；在固定检查后冻结输出与未决

之后需要全诊断/全主图时，显式将point_set改diagnostic_13/area_236。算法没有把可配置规模锁成当前云端小测试，但也没有凭空声称这些已验。CPU/GPU选择、实际内存与墙时需要在用户设备运行后记录；没有自动连设备、下载软件或提交任务。

数据输出按point原子保存，带配置哈希与计数；多进程worker独立计算，限制BLAS线程避免嵌套并发。中断前已完整保存的point可人工审阅，本版不宣称自动resume。未完成point必须标not_run/partial，不能仅看run_manifest就接受。

## 5. 算量与性能口径

默认2点固定比较名义2,450,612,480 ray evaluations；13点15,928,981,120；236点289,172,272,640。合并rate事件、高频面板会增加time节点，计划值不是精确实际值。降维参考另数x slice、反导数端点、projection、time调用；不同操作代价不同，不相加伪装FLOP。

每点工作上限1e11、墙时上限86400s是可配置硬停，不是速度预测。流式每点/time-chunk避免一次分配全场四维数组，内存仍必须设备测量。可先用selected更少比较做硬件校准，但这不降低最终既定算法与精度验证任务，只改变调度次序。

## 6. 本次仍缺的实现/验证

- 已写完整有限几何的高分辨验证driver；运行整合与高精度可靠性待设备，当前仅做小API/数学核检查
- rate的零支集事件尚未实现；非严格正rate的duration被显式标unresolved
- 一般多板重叠/任意旋转基片/未知源分布未纳入当前接口，须新模型和推导
- 严格浮点误差、全片连续极值、真实校准与材料验证未解决
- 指定DeepSeek/Seed阶段流程并未在此凭空完成；本次仅当前执行者加一次Luna窄数值核查，不代替正式阶段签署
