# 复算 发布与后续边界

## 独立读者包

reader含完整报告、静态HTML、PNG/SVG图、冻结代码依赖、输入合同、必要测试、机器可读结果、精确allowlist和hash manifest。解压到全新目录后可运行reader_check --check --full --strict-tree，不读取兄弟T02/T03目录，不导入整项目审计器，也不要求原项目的运行状态。

manifest排除自身hash以避免自指；外置release_receipt绑定archive和manifest的hash，freeze_record再绑定receipt。archive只按固定allowlist写入；不把外置receipt塞回archive制造循环。SHA-256证明包身份，仍需单独相信来源和验证科学内容。

原文副本位于作者本地sources/originals，均不进入reader、allowlist或manifest；读者仅获来源短摘要和公开链接。已冻结来源和根计划只读，新增内容限定本轮目录。作者本地origin_snapshot用于比较旧文件字节，不是读者复算依赖，也不入包。无需Library、账号或内部会话标识。

## 轻量复算

Python3.10以上和NumPy即可运行核心小测试。图已随包提供，重画图才需Matplotlib/Pillow。默认设备入口plan_only，无远程I/O。

```
python -B verification/reader_check.py --check --full --strict-tree
python -B -m unittest discover -s verification -p test_small.py -v
python -B models/run_examples.py
python -B models/device_driver.py
```

full检查只运行小测试、stdout反例和默认plan读取，比较保存的数值结果，核对冻结依赖hash及独核/修复证据。它不能重新证明原项目所有T01至T10正确，也不能恢复旧点12未完成运行。reader包内不包含绘图依赖下载器、网络爬取或账号操作。

## 原有缺口不被升级

data/inherited_point2_point12_reference.json逐字保留旧结果：点2 base只是reference_estimated_not_strict_bound，tight中断；点12 ion未运行。项目口径的continuous base/tight仍partial，本轮不修改任何一个历史状态。新增有限源有理包络属于本轮明确公式，不能将其与旧几何/连续源误差拼接成完整证明。

高算量设备的hostquota/权限阻塞尚未恢复。本轮不联系设备、不换远控路线、不运行历史continuous验证。之后任何有意义的设备结论都需当前授权、预算、机器标识、输入/代码hash及真实输出；计划文件和预估不是执行证据。

正式DeepSeek执行、Seed阶段独审、Sol算法签署链均pending；实际作者自审和一次Luna窄核查不替代它们。本包状态local_freeze_only，不登记algorithm accepted。

## 可视化资格

图使用保存的tiny结果及直接解析guard曲线生成。PNG像素须实际打开查看；仅有图文件或脚本exit0不等于视觉已验。HTML可检查文本、锚点、内嵌资产和无外部脚本，但本环境尚无浏览器布局验证。沿用已知权限边界，不为截图升级socket权限或改用未授权浏览器路线。HTML布局明确unverified。

## 后续交接与停止

T04候选仅研究材料/基片响应怎样改变当前传递量到厚度、光学性质和工艺质量的解释。它不能将本轮板形直接推广成材料最优方案。具体有界问题见T04_ROUND3_HANDOFF.md。

本轮停止于本地冻结，不上传、不push、不修改根计划、不自行启动T04。没有更多设备或物理证据时，保持unknown/partial是正确终点。
