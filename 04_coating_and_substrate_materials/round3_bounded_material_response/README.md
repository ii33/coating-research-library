# T04 第三轮 材料响应的有界传递

结论：几何积分D的优劣不能直接当材料膜厚/性能优劣。全候选共享正比例并且目标同比换算时，当前相对目标才有保排名保证；角度、能量、温度改变核形状，或目标不同比换算，都可能改变排名。材料区间重叠返回无法分辨。

本包只到local freeze。参考law、所有算例及driver输入为synthetic，不是实机材料常数。保留完整T03 forward及事件资格；T02 point12仍partial、point2仍条件非严格。正式指定模型链pending，实机资格未验证。未改产品代码、根计划、用户电脑或冻结原件；未上传、未push。

## 阅读路线

1. [独立HTML reader](reader.html)：六章手册、三图、六来源摘要
2. [物理接口与单位](reports/01_physical_contract.md)
3. [原始证据与基片边界](reports/02_primary_evidence_and_substrates.md)
4. [有界核、事件项与排名](reports/03_bounded_kernel_and_ranking.md)
5. [已运行反例](reports/04_counterexamples_and_results.md)
6. [识别与验证计划](reports/05_identification_and_validation_plan.md)
7. [复算与限制](reports/06_reproduction_and_limits.md)
8. [T05候选交接](T05_ROUND3_HANDOFF.md)：交接不等于启动下一题

## 本地小验证

在本目录运行，依赖numpy与jsonschema：

    python -B verification/reader_check.py
    python -B -m unittest discover -s tests -v
    python -B models/device_driver.py

最后一条只输出plan_only，不启动重计算。复算示例用 models/run_examples.py --output 指向新外部文件；冻结后不要覆盖data/tiny_results.json。绘图为可选，另需matplotlib/Pillow。

来源：6个公开原始来源的原创摘要；2份CC BY 4.0原文单独本地保存，不进入reader。PNG已实际查看像素。HTML只做结构/资源检查；浏览器layout未经验证，保留既有socket/权限边界，不绕过。
