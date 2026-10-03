# 复算证据与适用限制

## 1 内容和证据位置

| 内容 | 输入/实现 | 证据 |
|---|---|---|
| 归一化与有限源 | models/source_retention.py | tests/test_source_retention.py及独立量纲结果 |
| 联合秩与全局反例 | models/diagnostics.py | data/tiny_results.json |
| 条件拟合与资源driver | models/validation_driver.py | 42项小测中的无噪声恢复、拒绝秩亏和未授权执行 |
| 实际状态保留unknown | data/unmeasured_source_template.json | 独立字段、不按材料名补参数 |
| T04完整依赖 | data/frozen_dependencies.json | 每个副本源相对路径、字节数和SHA256 |
| 小测原始输出 | verification/unit_tests.log | 原始unittest计数与状态 |
| 唯一窄独核 | reviews/INDEPENDENT_UNIT_CHECK.md | 13项、仅单位与归一化/桥接 |
| 视觉与阅读器 | verification/visual_check.json | PNG逐张像素检查；HTML仅静态结构/链接 |
| 精确冻结身份 | verification/reader_manifest.json | 每项载荷路径、字节数、SHA256 |
| ZIP与脱离目录复算 | verification/release_receipt.json、detached_reader_verification.json | ZIP SHA256、精确成员、独立目录执行结果 |

原始文件在新目录外的基线快照只供本地修改范围检查，不装进reader。origin_integrity_check.json给出范围核查结果。冻结清单不把自身或包含其哈希的receipt再纳入payload，避免循环自校验；ZIP包含载荷和manifest，但不包含ZIP自己、原文、pycache或本地范围快照。

## 2 已运行的小计算

42项单元测试包括半球积分、Lambert 1/π、源/接收投影不重复、有限源权重、可见性不重归一、角域/参数/负量拒绝、全局等效反例、倾斜诊断、解析雅可比与中心差分、7参数秩、单次无噪声拟合、完整forward相等、unknown保留、非Lambert拒绝及driver默认不执行。

一次独立核查使用自己写出的角积分和移动目标原函数，13项通过；它没有重写模型或重新做整套科学审查。独立脚本是可读复核材料，本轮只执行一次。reader脱离测试复跑的是42项常规小测、确定性结果和默认plan_only，不再次调用独核脚本。

半球归一化最大独核误差约1.21×10⁻¹⁴；这是离散求积与双精度的数值一致性，不代表实机蒸发角谱精度。没有给真实参数置信区间。名义满秩不等于全局唯一解，独立Q/ρ/共同η_Q的假设必须另有证据。

## 3 图像和HTML

三张图各有PNG/SVG。PNG已经实际打开逐张检查：标签、图例、单位、synthetic声明可读，没有截断/遮挡。图3把低于10⁻¹⁴的奇异值画在明确标注的显示下限，原始奇异值保存在JSON，不把绘图下限解释为数值误差或秩阈值。

渲染期间Fontconfig报告默认字体缓存目录不可写，但PNG/SVG成功生成并做像素检查。没有修改权限或安装字体以绕过。HTML生成器使用本地静态内容，reader检查器核查链接、锚点和资产；已知socket/浏览器布局权限限制未恢复，本轮不重复探测或换路线，因此不能声称浏览器布局验收通过。

## 4 未运行和仍未知

未运行500次噪声重复driver、实际设备/源控制、连续源离散收敛、任意非Lambert到T04事件核的扩展、反应/碰撞输运、源温度求解、多层QCM声学、旧point2/12参考或离子参考。用户主机quota/权限未恢复，本轮没有尝试远控替代。正式DeepSeek、Seed与Sol指定审查链均pending。

真实输入缺口包括有效组分Q、源相态/耗料/热史、质量发射面与扫束关联、原始频率资格、实际捕集、工件留存/密度、几何/法向/时窗/遮挡误差，以及这些误差的相关性。源码中合成搜索域不解决缺口；状态模板中的null必须保持到有来源证据为止。

本包不修改root STATE/ROADMAP、第一/二轮、已冻结上游、产品或37条配方。只在新第三轮目录写入；本地冻结后停止，未push、未upload，未启动T06。
