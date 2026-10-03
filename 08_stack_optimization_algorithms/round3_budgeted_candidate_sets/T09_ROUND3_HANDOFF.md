# T09 第三轮有界交接

仅交接，不启动下一题。T08在同一六层合成膜系与M0/M1冻结算子上新增二维(z,v6)集合筛选、覆盖树、预算账本与目标/约束传播。

最终tiny：331节点、1166次单波长包含调用、10个浮点向量（40个浮点波长核）；二维联合255节点有98 OUT/32 UNKNOWN；v6=1.1切片13节点、7 OUT叶完成整个Z排除；(1,1)是区间验证代理见证，故意一次搜索未找到不能改判OUT。目标下界包含32个UNKNOWN，15个仅作最优性剪枝，其data_class保持UNKNOWN；目标界仍宽[0,约1]。

建议下一步只研究：如何把此证据和未决集合映射到既定下一层验收接口，或者在同一两通道样品状态合同内定义有限补测/数据需求。不得默认扩成设备任务、37配方重优化或无限维源反演。

必须继承：

1. 完整T06 forward/response与T05 finite-Lambert归一化、资格、复制依赖hash；不可退成厚度中心
2. T07 derived_observation_contract_sha256与M0父hash；新谱/角/状态/带宽/背面须新合同
3. 同一样品各层/两通道共享z；候选各存在自己的z，不同批次独立，除非有共享证据
4. Z为正厚度来源外包络：OUT可排除其子集；IN或点见证不证明Q、ρ、留存等联合来源实际实现。若回源须joint domain，不猜unknown n/k/Q/ρ
5. data OUT/IN/UNKNOWN与optimizer_not_found独立；预算、数值失败和未决约束保留UNKNOWN；目标剪枝不是数据OUT
6. arithmetic containment与float diagnostic分开；有限搜索不是全局证书；T=1−R非独立；全层倍率与z结构别名不消失
7. 负净/跨零/近零/库存/来源/状态unknown guards保持；1e−15 m不是成核阈值
8. 参数/覆盖/见证三hash及进程内验证来源保持。保存JSON可经reader检查，重新调用优化API需预算化screen/validate_point重放
9. 完整driver默认plan_only，full/设备/多批次均未运行；不可绕quota。PNG已检查，HTML布局unverified不重试headless
10. reader复制依赖可独立解压；原文单独本地排除分发。旧冻结、root plans、product不改
11. 一次GPT-6 Luna窄核已完成，正式DeepSeek/Seed/Sol链pending；point12 partial、point2 conditional non-strict不升级

本交接不授权上传、push、生产发布、设备安排或自动启动下一题。本包在local_freeze停止。
