# 固定稳健/名义设计的分轴数值跟进

只写本子目录，不修改首轮交付、首轮 manifest、产品或训练搜索。使用已选1%/seed11和5%/seed29双设计，固定首轮相同前4个留出潜变量，并另存零扰动结果。不是重新独立验证或优化器性能实验。

- [结果与接受判据](RESULTS.md)
- [执行前配置](config.json)，[pilot](pilot_results.json)，[实测成本规划](execution_plan.json)
- [完整字段](followup_results.json)，[分轴CSV](summary.csv)，[判据计算](acceptance_results.json)
- [下一档未运行成本估计](next_level_costs.json)
- [小数学/接线检查](tests_output.txt)，[完整性清单](artifact_manifest.json)

复现已有有界配置，在本目录运行：

    OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python -B -m unittest -v test_followup.py
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python -B run_followup.py --pilot
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python -B run_followup.py
    OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python -B build_report.py

相同前4情景是预定、已用过的数值诊断数据，不用于重新挑选设计或参数。间隔差、节点原点极差不是严格误差界。phase设置只是等价的数值节点原点探针，未改变被解释的物理积分窗。90-mm内部ROI完全覆盖用于识别边界面域效应，不替代100-mm全口径要求。所有结果保持合成/有限预算的证据层级。
