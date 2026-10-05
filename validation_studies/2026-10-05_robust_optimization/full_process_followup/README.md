# 完整原队列工艺：当前检查点

请先读[CURRENT_STATUS.md](CURRENT_STATUS.md)和[分离门禁JSON](CURRENT_STATUS.json)。完整10888.888889秒配方的direct .0125→.00625秒时间稳定性通过；finite-periodic .0015625秒仅建立grid21/原12与16源节点、基线和固定探针的限定参考。空间/源CV分辨率及最终联合direct资格未建立，没有工程排名或新优化。RESULTS.md和convergence_results.json保留较早检查点，其旧time=false不是最新结论。

- [numeric identity与三条stored run谱系](NUMERIC_IDENTITY.json)
- [完整.00625与周期/尾段机制](continued_00625/stage_results.json)、[限定周期参考](continued_00625/periodic_finer/finer_results.json)
- [用户fast_cycle mean分支对照](fast_cycle_branch_check/branch_results.json)
- [grid/source诊断](spatial_source_diagnostics/diagnostic_results.json)、[固定完整圆盘面积补充](spatial_source_diagnostics/controlled_aggregate_results.json)、[源采样alias](spatial_source_diagnostics/source_moment_alias.json)
- [算法、单位与图解](docs/algorithms.html)
- [初始完整输入身份](selected_input_manifest.json)、[原snapshot](input_snapshot.json)，均只保留在研究工作区，紧凑包排除这些原文件

严格screen不是批准的生产公差；模型未实测校准。周期资格不自动迁移到更高grid/source，完整盘分片恒定统计也不是连续场精确积分。当前按指示停止加密，没有多小时任务运行。

文件审计不执行物理核：

    python -B verify_handoff.py
    python -B verify_handoff.py --workspace

紧凑包用于离线读结果、字段和代码审计。verify_handoff.py可在解压后核验包内文件；研究驱动仍依赖原工作区研究helpers、对应cub代码和用户原始输入，包不含产品源码或输入原件，不是独立安装器。不应直接重跑driver覆盖冻结结果。

单元测试（原工作区，无真实forward调用）：

    OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python -B -m unittest -v test_full_process.py
    cd spatial_source_diagnostics && OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python -B -m unittest -v test_cells.py

当前checkpoint合计130次真实CPU核调用，含重复pilot、周期片段和独立机制fixture。没有原配方截断、产品写入、GitHub动作或Library上传。
