# T08 首轮研究验收

## 范围结论

已完成原文所要求的三条路线的有界方法研究与小规模参考：高精度/高性能、快速近似、可持续迭代。9章方法、16来源、3典型起点、4图、可复跑代码和失败证据。资料完成、数值验证、材料/生产验证分层。

## 已检查证据

- 36项离线单元/回归测试：test_output.txt
- 前缀后缀导数、全方向切线及独立Airy FD：MATH_SPOT_CHECK.md
- 三案例、五方法、追加预算、公差/结构/失效：benchmark_results.json
- 显式总厚度、有限minimax/R-A权重：extension_results.json
- 独立复制目录的36测试及三问题2步smoke：clean_copy_output.txt；没有冒称在新机器安装依赖后全量重跑
- 文件/数值/链接/上游冻结/公开排除：package_check_output.json

## 明确保留的不合格结果

B03主试验及追加精修耗尽预算并未达教学光谱规格；局部驻点不是全局最优。needle退化候选拒绝。warm-start没有稳定调用节省。代理误判被回证拒绝。缺连续波段证书、真实材料、设备、公差分布与生产标准验收。

## 审查地位

实际执行者的自检与GPT-6 Luna窄数学核查不能替代用户指定的DeepSeek/Seed/Sol完整链，相应角色保持pending，阶段schema为awaiting_seed。资料首轮是否收口/进入T09由协调者决定；不把方法包完整误写为实际膜系合格。
