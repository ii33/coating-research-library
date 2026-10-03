# T10第二轮 离子辅助可追溯观测与材料响应

版本T10-r2-v0.1.0，2026-10-02。本地冻结研究包；优先Kaufman栅控源。核心是区分源端设置、仪器响应、工件暴露和薄膜响应，并给出可以拒绝错误数据的离线合同与参考算法。

## 阅读

打开[index.html](index.html)即可离线阅读八章、三张原创图和来源摘要，不需服务器、网络脚本或字体下载。浏览器布局未验证；HTML结构/链接已做支持的检查。PNG图已逐张视觉检查。

1. [范围与证据](reports/01_scope_observables_and_evidence.md)
2. [Kaufman能量 电荷与快中性](reports/02_kaufman_energy_charge_and_neutrals.md)
3. [诊断前向模型与可辨识性](reports/03_diagnostic_forward_models.md)
4. [空间 时间与工位代表性](reports/04_spatial_temporal_representativeness.md)
5. [材料状态 净生长与净侵蚀](reports/05_material_state_growth_and_erosion.md)
6. [材料响应辨识与独立验证](reports/06_response_identification_and_validation.md)
7. [可复算案例](reports/07_reference_cases_and_counterexamples.md)
8. [实现 预算和冻结边界](reports/08_implementation_execution_and_limits.md)

## 关键结论

- 理想平面RFEA选择法向动能/电荷；角度影响包含cos²能量选择，不能只处理通量投影
- 完整校正的电流加权总E/q谱可给带电动能流；未知电荷态仍阻断粒子数，快中性仍另行分账
- 净库存跨零、宽正不稳定区间、净侵蚀和中途耗尽必须分别处理；不把巨大每净原子能量当优化收益
- 相同平均剂量和均能不足以唯一决定膜态和n/k；真实材料响应必须有独立样品与完整光学算子

## 已实现和未执行

33项轻量测试通过；一次窄独立单位/证据检查完成并修正局部问题。完整合成driver已写，默认plan_only，216条件×200重复的43200次逆解计划未执行。设备数据入口是离线导出记录验证；真实通信协议未获知，不虚构实时硬件驱动。

实际设备、膜层、产额、资格及生产均未验证。完整合成/实际导出数据/设备/材料验证状态not_run_awaiting_device。T02 partial、T03净侵蚀不支持、点12 not_run和τ非严格等上游边界保持不变。

## 复现

    PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 python -m unittest discover -s tests -v
    PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 python models/validation_driver.py
    PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 python models/validation_driver.py --mode tiny_synthetic
    PYTHONDONTWRITEBYTECODE=1 python models/audit_package.py --verify

程序默认标准输出；新执行结果写入新执行包，不覆盖冻结文件。依赖为当前环境已安装的NumPy、SciPy、jsonschema；图形再生另需Matplotlib，未安装任何软件。版本记录在verification/environment.json。

15条来源登记，21项哈希依赖复制。第三方原文不在reader；MXC只用原创派生审读，未复制手册/截图/全表。依赖文件保持原字节，仅供审计，它们原有的跨专题链接不作为本reader导航入口。

精确范围与SHA256见freeze_manifest.json及verification/freeze_receipt.json；目录外差异证据见verification/outside_scope_check.json。无上传、push、部署、外部分享、用户电脑或硬件操作。冻结后停止，后续批次由协调者处理。
