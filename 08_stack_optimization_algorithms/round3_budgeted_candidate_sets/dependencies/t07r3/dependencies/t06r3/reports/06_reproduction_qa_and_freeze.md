# 06 复现、审查、独立阅读与冻结

## 1. 已执行与未执行

已执行：一次小的合成Lambert上游配置，三种变体各8共享latent格×3谱节点、一个8格配对差量，39项小测试，最多一次独立窄光学核查（5个单点、无扫频），本地PNG生成与实际像素检查，离线reader资源与哈希检查、脱离兄弟目录的reader自检。生成过程曾更新演示B从1.10为1.25并重跑小例，不属于正式批量扫描；探索与修正见执行台账。

未执行：完整12任务批量计划、任何设备/主机配额借用、真实光学/材料标定、现场验证、正式DeepSeek/Seed/Sol链。HTML布局未验证：父任务确认同云环境localhost浏览器被拒绝，headless Chromium经一次升级后仍socket权限拒绝。本轮不重复，不以另一浏览器/后端绕过。静态结构、链接、离线资源检查不冒充截图布局验证。

## 2. 小复现

在此目录、已有依赖环境中：

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=models python -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python models/validation_driver.py
PYTHONDONTWRITEBYTECODE=1 python models/reader.py --directory .
```

第一项约39项小测试；第二项只输出plan_only；第三项验证清单、SHA-256、资源链接和自包含性。冻结后不要原地重建图或结果再保留旧清单。若需再生，复制到新的候选目录并完整重冻结，保持本基线不变。

`build_inputs.py`用于重建一次小上游桥接；`run_tiny.py`用于三个8格演示；`validation_driver.py --execute`只提供未来执行接口，不代表授权。完整driver没有联网、任务调度、主机探测、CAPTCHA或密码逻辑。正式计算要先由用户安排，不能把有执行入口当作已执行。

## 3. reader与哈希层次

- `data/frozen_dependencies.json`绑定53份逐字复制依赖，原始T05内部清单继续保持相对路径可解
- 完整case保存全forward及来源合同，材料映射绑定整个bridge payload；光学结果保存response/bridge/material/measurement/optical合同hash
- `verification/reader_manifest.json`列出reader所有实际payload文件、精确字节数及SHA-256，不包含其自身或运行回执以避免循环
- `verification/freeze_receipt.json`绑定manifest自身hash、ZIP字节数/sha256、payload文件数、范围核对和QA状态
- reader ZIP包含payload和manifest；其ZIP内部文件集合必须严格等于清单集合加manifest。精确对应关系由孤立解包校验，而非只检查ZIP能打开
- 原目录之外的文件哈希与初始快照比较；清单/回执不宣称自我哈希，也不把文件哈希当物理认证

包内只含原创文字/代码/图、所选种子数据与既有项目依赖/恢复证据。不含第三方论文原文、Library账户或文件ID、登录凭据。没有上传、发布、push或产品变更。

## 4. 状态与停点

当前：local_freeze，formal_status=awaiting_seed；实际执行者自检和一次原生窄核查只标明各自范围。指定模型链未实际完成，不冒充正式审核。point12=partial_unchanged，point2=conditional_non_strict_unchanged，真实参数unknown，production_qualified=false。

`T07_ROUND3_HANDOFF.md`仅为下一阶段候选。本轮到本地冻结停止，不开始T07，不扩展成新优化任务。
