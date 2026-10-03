# T03第三轮 事件感知修正板局部信任域

版本v0.1.0，2026-10-02 UTC。本包只研究T02冻结有限厚板仿射截面的横移和半宽两参数。完整forward使用相同物理目标；有理仿射guards限制拓扑改变前步长，有理Darboux积分区间决定候选是否可分辨。

一次小步的J区间从[0.00494035,0.00555049]降至[0.00243993,0.00285334]，编码有限源目标上可接受。漏事件模型的板梯度为零，被作为模型停滞拒绝，不能称作真实收敛。工件横移反号、半宽纯事件、unknown/重叠拒排与病态分母反例均保留。

范围严格：新包的编码模型证据不是连续源或实机认证；T02旧point12仍partial，point2条件包络非严格。正式DeepSeek/Seed/Sol链pending。仅本地freeze，不上传/push，不启动T04，不修改根计划或旧frozen。

## 阅读

打开reader.html可离线阅读六章报告和两幅图。PNG已检查像素；HTML内容/内嵌资源可核验，浏览器布局unverified。原文全文不在reader，来源摘要和公开链接见sources/source_cards.md。

1. reports/01_scope_physical_objective.md：场景、物理量和唯一比较目标
2. reports/02_topology_trust_region.md：一阶启发式、余项与精确仿射证据
3. reports/03_forward_intervals_and_decisions.md：完整forward、区间与ratio门
4. reports/04_complete_algorithm_and_cache.md：完整参考算法、缓存、driver
5. reports/05_results_and_counterexamples.md：同目标对照与最小反例
6. reports/06_reproduction_limits_and_handoff.md：复算、剩余边界和停止条件

## 在全新目录复算

核心需要Python3.10+、NumPy。解压reader zip后，在其根目录运行：

```
python -B verification/reader_check.py --check --full --strict-tree
```

不需要兄弟目录、整项目审计、账号或网络。小测试、独立数学检查、tiny结果和默认plan_only输出都会被复核；不会执行设备验证。若Python/NumPy版本造成末位不同，严格证据比较可能报错，应保留差异并核对，不能用宽容模式静默改已保存结果。

查看计划：python -B models/device_driver.py。默认加--run必须拒绝。未来授权恢复后只复制配置到新位置，核验指定设备当前额度/权限，再运行包外全新输出；不得改此冻结目录或另换未授权远控。

## 证据身份

本版本reader精确包含52个成员；verification/public_allowlist.txt逐项列出。reader_manifest.json对除自身外的51个成员记录SHA-256和字节数。外置release_receipt.json记录zip及manifest身份、干净解压复算结果；freeze_record.json绑定receipt。收件者收到的zip没有外置回执自指。

data/frozen_dependencies.json逐个绑定本地冻结输入，reader只读这些包内副本。sources/originals与作者local snapshot不入allowlist/manifest/zip。旧来源不改动的结果见verification/origin_integrity_check.json。

T04_ROUND3_HANDOFF.md仅为下一题候选，本包在此停止。
