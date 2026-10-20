# 经典种子与局部/全局混合搜索

日期：2026-10-20。独立云端研究，不修改产品。结果与局限见《研究报告.md》；评分、预算、方法和阶段调整见 PROTOCOL.md。

## 复现

Python 3.12；NumPy/SciPy 是运行核心依赖，matplotlib 用于分析绘图，PyYAML仅用于可选的原始快照数据提取。全部优化与主审计无需联网。

```sh
python -m unittest -v test_hybrid.py
python run_hybrid.py --physics-only
python run_hybrid.py --budget 4000 --seeds 11 29 47 --output pilot --audit-points 1025
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python run_hybrid.py --budget 6000 --output results
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python analyze_hybrid.py --input results --replay
python diagnose_angle_peaks.py
python verify_deliverable.py
```

小试原始记录保留了当时的五法版本；当前脚本默认追加 probe_local，复跑小试若要完全匹配原记录，请显式指定 --methods classic_local random_local classic_de de_local local_de_local。主复核六法配置一致。

## 文件

- run_hybrid.py：稳定斜入射s/p功率递推、独立矩阵核、预算包装器、六个算法消融、冻结训练档案及错位网格/加密角度审计
- test_hybrid.py、tests.log：预算、复现、数据覆盖及物理回归
- data/：带来源的完整n/k裁剪表与出处；没有缺失k补零
- results/results.json：逐次完整厚度、最小聚合目标厚度、阶段成本、训练轨迹与审计
- results/summary.json/.csv、runs.csv：分组和逐次汇总
- results/paired_comparisons.json：配对差值，避免只报最好种子
- results/archive_vs_aggregate.json：相同搜索轨迹中档案保留的后验消融
- results/replay.json：seed11全部问题/方法确定性重跑
- results/deliverable_consistency.json：120次唯一性、精确预算、阶段/点数账目、训练指标及分组汇总重算、审计网格重合披露
- results/median_spectra.png、median_convergence.png：中位种子而非最佳种子光谱、五种子中位训练轨迹

## 物理与证据边界

前三个任务全为显式合成无损n/k。第四个任务使用来源明确的标量复n/k，仍是理想平整、相干、各向同性模型；未建模有限基片厚度、背面、粗糙度、温度扰动、工艺容差或本批材料薄膜测量。进入半无限吸收基片的边界通量不是器件背面出射透射率。有限波长和角度审计不是连续域证明。

算法组件不主张原创或一般排名。6/10层是两个分别冻结的参数空间，并非自动层数/层序联合搜索。3–5与8–12双窗是减反要求，窗间没有阻带要求。

## 技术参考

- Byrnes, Multilayer optical calculations，斜入射、吸收、复角分支：https://arxiv.org/abs/1603.02720
- SciPy DE官方文档：https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.optimize.differential_evolution.html
- SciPy least_squares官方文档：https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.optimize.least_squares.html
- 数据引用：data/ATTRIBUTION.md 与 provenance.json
