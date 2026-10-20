# 角度约束交换小试

2026-10-20。独立研究，不改产品或上一份hybrid实验。中文结论见《研究报告.md》，冻结问题及必要基线修订见 PROTOCOL.md。

## 复现

```sh
python -m unittest -v test_angle_exchange.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python run_angle_exchange.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python analyze_angle_exchange.py --replay
```

核心依赖 NumPy 2.3.5 / SciPy 1.17.0；分析图需要matplotlib 3.10.8。Python 3.12。使用包内CSV，无需联网。optics_base.py和data/是前一hybrid实验的冻结自足副本。seed_sources.json保存全部10个初始厚度、前期成本和原始结果SHA256。

## 口径

每方法额外物理点预算上限200万，有限差分、参考检查、峰寻找全计入；局部收敛可提前停止，实际工作不同。静态方法一次连续精修，交换方法最多4轮。共同5°/81点参考网格参与档案保留，不是未见验证；独立最终网格为0.5°角度、每窗2048个错位波长中点加端点。局部二维波长/角细化仅针对各窗/偏振的最大R峰；P最小值取有限网格值。有限网格和局部R峰细化不构成连续证书。

全部方法都使用同一epigraph minimax续优化器，与前一实验的四次hinge搜索目标不同；新增点只作约束，固定均方次目标不重复计票。P是进入半无限基片的边界能流，不是有限器件出射透射率。

## 文件

- run_angle_exchange.py：点工作计数、散点复n/k求解、约束交换、静态强基线、固定参考档案、独立审计
- analyze_angle_exchange.py：30次确定性重放、成本/档案/指标核对、配对差与约束点转移分析
- test_angle_exchange.py、tests.log：核验、工作预算、峰搜索与两偏振审计回归
- results/results.json：全部30次完整记录；summary.csv/json、runs.csv为汇总
- results/constraint_transfer_diagnostics.json：加入的点改善与最终其他位置峰值的区别
- results/paired_comparisons.json：全部配对差值；replay.json：30次复现
- results/paired_results.png：所有既定种子，未挑选最好例子
- initial_static_restart/：撤回的弱静态重启对照和原始30次记录，不能用于最终排名
- data/：完整来源n/k表及数据工艺/范围说明，未外推或补零
