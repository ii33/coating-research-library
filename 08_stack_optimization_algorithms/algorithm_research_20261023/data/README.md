# 公开科学数据

此目录仅包含事先固定试验的科学配置、处方/冻结材料、误差系数和结果。阅读[复现协议](../reproducibility.md)，再看[实效报告](../sensitivity-results.md)。

- AR-local、AR-zero-bound-risk、HR-8layer各有config/results两份JSON。
- large-config/results保存89层完整输入、优化变量与全部已报告变体，含逐样本留出及额外名义诊断。
- comparison.csv与summary.json为汇总；small-canonical-crosscheck.json与large-system-endpoints.json为额外物理复核。

config最外层是研究实验封装，request才是正式敏感性请求。请求内保留软件校验所需的冻结材料sha256字段；不包含源码文件hash库存、执行脚本、日志或内部路径。研究软件提交与数据解释在上级文档中明确列出。

所有概率/分位数均局限于所声明材料、光学网格、有限误差样本。±0.2%均匀幅值是研究假设，不是工艺能力。大例每误差模型仅16个留出样本，不能估计量产良率，也不能把优化候选替代原89层设计。
