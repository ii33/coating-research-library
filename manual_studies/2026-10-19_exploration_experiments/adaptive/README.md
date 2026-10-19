# 自适应波长审计：可复现小实验

独立云端研究试验，未修改主软件；本包仅作研究脚本和合成结果的同步。所有 n/k 均为合成常数，k 明确设为 0。正入射、相干、各向同性膜层；实数半无限入射/出射介质，无背面。

## 复现

Python 3.12，现有 NumPy/SciPy 即可；本轮没有安装软件。

```sh
python run_adaptive.py
python -m unittest -v test_adaptive.py
python diagnose_reference_precision.py
```

脚本默认相对加载 `kernel/run_experiment.py`，是先前验证过的研究核的原样复制。其来源与 SHA-256 在 `kernel/provenance.json`。可用 `python run_adaptive.py --kernel-root /path/to/prior-study` 指定含同名核的目录。没有读取主软件、凭据、私有服务或先前候选结果的运行依赖。

数值实验的种子与工作预算固定；浮点结果应在同环境复现。墙钟实验采用 50ms 软限额，三次乱序重复，耗时及点数会随共享机器负载变化，不要求 bitwise 相同。每次会覆盖本目录当前结果；保留初始结果时可先复制目录。

## 文件

- `研究报告.md`：中文结论、失败与边界
- `run_adaptive.py`：主实验与实际物理工作计数
- `results.json`：完整候选、每窗指标、独立审计与成本
- `summary.json`、`detection.csv`、`optimization.csv`、`wall_limit.csv`：汇总与可筛选记录
- `test_adaptive.py`、`test_report.txt`：8 项单元/回归检查
- `diagnose_reference_precision.py`、`reference_precision_diagnostic.json`：保留一次参考审计器自身的失败及修复对照
- `failure_history.md`：错误重复采样初稿的失败记录；当前实现已修正，早期结论已作废
- `kernel/`：保持原样的已验证研究核及来源散列

本试验只是有限集合审计；没有连续区间证书、真实材料性能、制造资格或普遍优越性结论。
