# T06 第二轮：工艺输入 → 条件化膜状态 → 可测光谱

本地冻结研究包；只新增本目录。完整数值链已经实现，小数据算术/光学验证与一次窄核查不等于真实材料校准、指定模型完整独审或设备验证。没有新生产配方；没有 push、上传、ZIP、论文原文或设备任务。

## 先看结论

- T05 工件实际面积上的入射元素通量不是净留存。只有显式留存/反应/脱附/再溅射余额或独立净通量，加组成、实际膜密度及状态证据，才能得到几何厚度
- 本包公开参数例用 McPeak Al 膜 n/k 与 Malitson 熔融石英块材基片；工艺净余额、密度和转移到假设基片的条件是合成场景。没有伪装成本机实测
- 设计厚度250 nm、合成几何厚度300 nm、QCM等效厚度333.33 nm和逐波长 n d 各自保存，互不替换
- 稳定散射核执行多波长/角度/偏振、有限不相干基片、bulk吸收、带宽及探测收集合同；所有未知保留阻断
- 小反例可精确拟合错误模型：漏吸收时单点R完全匹配但T错3.89个百分点；漏散射时R/T可被错误k≈0.0400吸收拟合

## 阅读顺序

1. [状态与转换](reports/01_process_to_conditioned_film.md)
2. [光学和测量合同](reports/02_optics_and_measurement_contract.md)
3. [可证伪反例与辨识](reports/03_identifiability_and_failure_cases.md)
4. [测量需求与不确定度](reports/04_measurement_and_uncertainty_plan.md)
5. [复现、冻结与边界](reports/05_reproduction_and_acceptance.md)

可直接打开 `index.html` 阅读本包原创报告、图和源代码索引。`data/process_optics.schema.json` 是严格机器合同；`examples/` 含2个条件可算例与6个阻断例。`models/vendor/optics_kernel.py` 是冻结T07核逐字副本，以哈希证明继承；reader不依赖项目兄弟目录或联网。

## 默认安全复现

在本目录运行（依赖已安装时，无安装/联网）：

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=models python -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python models/data_qa.py
PYTHONDONTWRITEBYTECODE=1 python models/batch_driver.py
PYTHONDONTWRITEBYTECODE=1 python models/reader.py --directory .
```

`batch_driver.py` 默认 `plan_only`，完整批量计划尚未执行。`--execute --output <local-json>` 是未来明确安排设备后的入口；本轮只有测试中2波长、1角、零Monte Carlo的小路由，以及独立2抽样不确定度算术检查，不能报为批量/设备验证。不要把本地运行脚本等同生产标定。

本包当前状态见 `stage_status.json`；交接建议见 `T07_ROUND2_HANDOFF.md`。到此停止本轮范围，不自动扩展T07。
