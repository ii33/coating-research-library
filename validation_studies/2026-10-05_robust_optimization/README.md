# 实际 cub 内核的名义 / 稳健优化独立验证

2026-10-05 UTC。独立合成 proof study，使用 cub `415635cf3ec3ba6e65cfabbb90bef1e9940245fb` 现有有限源、行星运动、双板遮挡正向内核。产品只读，所有写入都在本目录。没有产品改造、用户数据改写、GitHub 提交或生产资格结论。

## 阅读入口

- [结果与证据边界](RESULTS.md)：三种子、1%/5%、名义权衡、配对留出、加密与失败
- [离线单文件算法说明](docs/algorithms.html)：坐标、单位、公式、图解、真实调用预算、采样与近似
- [冻结研究配置](study_config.json)
- [实际输出 JSON](results/study_results.json)、[简洁 CSV](results/summary.csv)
- [基础源哈希与环境](results/baseline_manifest.json)、[完整性清单](results/artifact_manifest.json)
- [小验证输出](tests_output.txt)，仅接口/数值身份测试

## 复现

需要已有 Python 3.12 和 NumPy；无新增安装，不需要 pytest。产品目录须为本目录向上到 `projects/deposition_sim` 的既有只读副本，不是自包含产品复制包。

在本目录运行：

    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python -B -m unittest -v test_evaluator.py
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python -B run_study.py
    OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python -B build_report.py
    PYTHONDONTWRITEBYTECODE=1 python -B verify_artifacts.py

默认 driver 为有界 CPU 小比较，不运行高保真工程任务。输出存于本目录，覆盖同名研究输出时需自行保存旧版；不得把输出路径指向产品目录或既有库专题。

## 与所给论文的关系

借鉴 [Shrivastava 等，arXiv:2405.03092v1](https://arxiv.org/html/2405.03092v1) §III.1 的方法思路：一起考虑性能、约束和过程扰动敏感性。本研究以 mean(CV)+λ·SD(CV) 和明确合成约束做有限情景验证；没有复刻其 Bayesian 优化器、Mo 应力/电阻阈值或实验结论。未下载或附第三方全文。

## 明确限制

1%/5% 是人为敏感性分布：位置标准差为 100 mm 参考尺度的 1%/5%，A/n/rpm 为各自名义值的 1%/5%。相关假设和刚体内部相关见算法说明。仅 3 个非名义训练情景和 3 个搜索重复，留出统计不等于机器可靠性。源 A 在归一化 CV/η 中抵消，绝对源强/膜厚稳定性没有得到验证。零厚度板和细胞面积覆盖近似也没有得到制造或连续空间精度认证。

公共 `simulate` wrapper 会持久化后端成功记录。适配器直接调用其原样 CPU 积分 kernel、原 finite-source sampler 和指数解析，避免向产品写入 backend-memory；这不是改写物理算法。完整产品 Python 哈希前后核查，baseline commit 由既有部署记录佐证，迁移目录本身没有 `.git`，不声称重新完成远程仓库审计。
