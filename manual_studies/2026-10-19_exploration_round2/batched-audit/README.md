# 批量区间审计 第二轮独立云端实验

先读 `研究报告.md`。主要结论：批量能降标量开销，但修正坐标后的标量方法在65层超窄组同129点漏0/3，批量双区间仍漏2/3；50ms两者分类持平，未证明批量分类优势。

## 复现

现有 Python 3.12、NumPy/SciPy，无需主软件或旧实验目录：

```sh
python run_batched.py
python diagnose_scaled_scalar.py
python -m unittest -v test_batched.py
```

主实验47个物理候选，7次完整任务计时，9个候选×5次×2种软墙钟预算。程序覆盖本目录当前输出；保存初始结果请先复制。浮点分类应确定复现，墙钟及其截止时的分类可能受共享负载影响。

`prior_adaptive.py` 是原样冻结的历史研究对照，仅供导入参考审计器与旧标量方法，并非当前推荐求解器或本轮运行入口。其历史 __main__ 保留以维持原文件散列，不应直接启动；本轮运行入口只有上方两条实验命令和测试命令。`kernel/run_experiment.py` 同样原样复制。来源/散列在 `kernel/provenance.json`。默认相对导入，自带完整核。

- `results.json`：完整候选厚度/n、独立参考、固定成本和计时账本
- `summary.json`、`fixed_budget.csv`、`warmed_task_timing.csv`、`wall_budget.csv`：汇总与原始CSV
- `scaled_scalar_diagnostic.*`：事后无量纲标量消融，不能当事前注册结果
- `test_batched.py`、`test_report.txt`：回归检查
- `研究报告.md`：结果、计时噪声、软截止超时、成本和边界

所有材料n为合成常数，k明确为0，正入射相干、半无限实数外介质；没有主软件变更、发布、训练、制造资格或连续区间证书。

最终检查：10项单元/回归测试全部通过；94次固定预算批量复算均为129个不同真实波长点。独立复核已对47片逐一重算参考与分类，无分类不一致。
