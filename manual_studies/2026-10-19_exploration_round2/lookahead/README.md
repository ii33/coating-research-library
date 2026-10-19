# 有限前瞻与复响应多样性：第二轮小目录研究

2026-10-19。仅云端研究，不修改或发布主软件；本包仅同步研究脚本与合成结果。结论见 [研究报告](研究报告.md)。

本目录独立可搬移；`verified_kernel/run_experiment.py` 是既有已验证研究内核的原样副本。默认只用相对路径；也可显式传入 `--kernel-root`。没有用户数据、运行凭据或网络依赖。

## 复现

Python 3.11/3.12，安装 `requirements.txt` 后，在本目录运行：

    python run_lookahead.py
    python analyze_results.py
    python -m pytest -q test_lookahead.py

完整试验约 37 秒（本次共享云端机器，仅量级参考）。所有实验输出写入本目录的 `results/`。`--out` 可指定搜索结果目录，但分析脚本默认读取本目录 `results/`。不需要访问原软件仓库。

当前结果：7 个预设目标族 × 4 个候选枚举顺序种子 × 8 种搜索配置 = 224 轮；81、241、721 个评价的嵌套检查点。每个目标族的 4 次顺序重复不是 4 个独立物理任务。完整小目录包括空栈，共 2,332 个栈。每个候选都实际调用原内核和独立复振幅递推，不用预计算表替代搜索光学计算。

## 文件

- `run_lookahead.py`：目录、目标、穷举参照、搜索与密/偏移网格审计
- `analyze_results.py`：成对消融、种植目标族命中、逐层路径诊断
- `test_lookahead.py`、`test_report.txt`：7 个测试及实际通过结果
- `results/results.json`：完整配置、原空栈、搜索改善轨迹、检查点、参考解、成本与审计
- `results/runs.csv`、`summary.csv`：全部逐轮检查点及汇总
- `results/diagnostics.json`、`paired_comparisons.csv`：成对比较、路径障碍与成本核对
- `MANIFEST.json`：排除临时日志与缓存后的实际发布文件清单
- `verified_kernel/run_experiment.py`：原样内核；SHA-256 记录在结果配置中
- `MANIFEST.json`：交付文件哈希

注意：这里的“宽度”是有备用入口的前沿搜索每批展开宽度，不是总前沿内存上限。h=1、宽度1 是按当前分数选下一入口的贪心最佳优先搜索，允许从已评分备用分支重启，不能称为只沿单条路径且永不回退的传统贪心。h=2 是有限两层整包展开；没有连续厚度精修、删层、换序或一般剩余层数可达性证明。
