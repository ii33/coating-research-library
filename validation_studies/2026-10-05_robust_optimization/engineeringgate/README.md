# 实际步长≤0.05秒门禁

[结论与重新分级](RESULTS.md)优先于未改写的历史报告。所有工程排名仍blocked：本次是12秒合成窗，固定候选曾在不合格粗步长训练，空间/有限源及实机证据尚不足。满足时间门禁不等于代表完整工艺。

实际新档：0.05/0.025/0.0125秒，原cub内核240/480/960个节点，实际全节点与尾批进度核验。

- [配置](config.json)、[pilot](pilot_results.json)、[结果](gate_results.json)、[门禁状态](gate_status.json)、[CSV](summary.csv)
- [新小测试](tests_output.txt)、[隔离历史数学测试](historical_math_output.txt)
- [完整性](artifact_manifest.json)

在本目录复现：

    OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python -B -m unittest -v test_gate.py
    OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python -B check_historical_math.py
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python -B run_gate.py --pilot
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python -B run_gate.py
    OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python -B build_gate_report.py
    PYTHONDONTWRITEBYTECODE=1 python -B verify_gate.py

原始首轮和convergence_followup只读保留，包含其历史失败日志。没有重新优化或执行真实完整长工艺，也不使用0.0625秒的旧结果作为门禁后的工程阈值。
