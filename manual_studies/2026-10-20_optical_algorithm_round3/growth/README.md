# 停滞触发的两编辑结构修复

2026-10-20，独立云端、合成无损材料、原2332栈有限目录。未修改产品或发布仓库。主要结论及负结果见[研究报告](研究报告.md)。

## 重跑

Python3.12；本次NumPy2.3.5、SciPy1.17.0，测试pytest9.1.1。在本目录执行：

    python run_growth.py --targets 4 --seeds 4 --out pilot
    python run_growth.py --targets 12 --seeds 4 --out results
    python run_growth.py --targets 12 --seeds 4 --work-matched --out work_matched
    python analyze_growth.py --out results --diagnostics
    python analyze_growth.py --out work_matched
    python -m pytest -q test_growth.py
    python validate_saved.py

完整两组数值主试验共约55秒，仅共享云端量级。无需网络或原始软件仓库。全部路径相对包目录，可从任意当前工作目录用绝对脚本路径执行。run_growth.py的--out可改为新位置；分析时传相同位置。

## 文件

- experiment_plan.md：小试、冻结机制、后续固定目标族和核验口径
- run_growth.py：模型、合法结构图、生长/回修算法、真实调用及审计
- analyze_growth.py：按目标族汇总、完整反面比较、事后全目录局部陷阱诊断
- test_growth.py、test_report.txt：回归及完整721调用精确回放
- baseline_reference_cases.json：旧轮七个目标原样配置，只用作回归参考
- verified_kernel/run_experiment.py：未修改原核，SHA-256记于每个配置
- pilot、results、work_matched：配置、所有候选ID序列、最好档案轨迹、停滞/两编辑事件、三个检查点、真实成本、CSV及密审计
- results/mechanism_diagnostics.json：全部一编辑局部最小与两跳出口、实际访问的严格中间变坏见证；仅事后诊断，从不喂回搜索
- MANIFEST.json：交付文件哈希
- validate_saved.py、validation_summary.json：对小试及两组主试验共2664个检查点逐一核对，档案恰为实际已付费候选前缀中的最优；同时核对3427个停滞/跳跃事件和全部小试候选序列在扩展中未改变

12族×4顺序重复才是主种植评估；不要把重复当独立任务。结果优势只属中等预算谱重建；低预算较差、多个族失败、双窗AR未解的结果同样保留。工作预算Σ(1+实际层数)只是透明的计算量代理，实际调用/活跃层点/墙钟另列。密采样合并 `linspace(lo,hi,4097)` 与 `lo+(j+0.5)(hi-lo)/4097`（j=0..4096），每窗中心重复后共8193个唯一点，并与41点训练网格重合9点。每个 run 结束后审计该 run 的检查点；审计和穷举参考值不反馈给后续搜索。有限目录和密采样均不证明一般连续最优或连续波长合格。
