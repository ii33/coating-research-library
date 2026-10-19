# 第一阶段：固定处方角度、偏振与有限基片适用域诊断

54条件均实际执行：A/B×0、5、10、15、30、45°×s/p共24条件；
裸片、A/裸、B/裸、A/A、B/B、A/B×0.01、0.1、0.5、1、2mm共30条件。
新增诊断不取代正常入射半无限ZnS的原目标或独立验算结论。

入口：[完整报告](REPORT.html)、[角度指标](angle_summary.csv)、[整片指标](plate_summary.csv)、
[源k适用性](source_k_assessment.json)、[算法](algorithms.html)、[数值交叉核验](numerical_validation.json)。
所有实际完整采样光谱按CSV.GZ保存；这是科学数据压缩，不是运行缓存。
`cases/`保留每窗极值、位置、反射/透过门槛失效区间；`verification/run_events.jsonl`
保留实际完成事件与评价计数，排除重复心跳。

## 复核

已有Python/NumPy环境中运行，不需要产品仓库：

```powershell
python -B scripts/recheck.py --dense --output verification/portable_recheck.json
```

该命令重算54条件的报告极值位置及全部原密网格谱值，允许最大差2e-10。
原报告还执行了局部极值、冻结递推交叉检验、互易性以及完整矩阵相位平均；
这些记录保留，但本portable命令不冒称重新搜索所有连续极值。

## 重要边界

表面透过进入ZnS半空间与整片透过进入后方空气不同。前膜沿传播方向是
substrate_outward表的倒序，后膜是正序。Querry源为特定CVD样品的反射谱KK
反演数据，不能推广为所有光学级ZnS的实际毫米厚透射。原k和源零值均保留，
没有未知k补零、外推或拿薄膜常数替换块体。源DN/DK栏定义未核实，未作为误差界。
实际品级、实物厚度和相干性仍未知；10um情景的非相干假设尤其需要独立物理依据。
所有54情景有限采样；不构成制造验证或全局不可行证明。
