# T05 第二轮：QCM 到工件入射元素通量

**本地有界研究包，implementation_ready_validation_pending；没有生产tooling/真实机台标定。** 只新增本目录，未改前轮、root STATE或产品，未push/上传；没有ZIP。

## 先读

1. [频率—面质量推导与声学限制](reports/01_qcm_acoustics_and_units.md)
2. [几何、捕集率、物种与T04合同](reports/02_geometry_species_and_contract.md)
3. [辨识矩阵、有界稳健拟合与不确定度](reports/03_identifiability_and_uncertainty.md)
4. [合成反例、复算与未运行项](reports/04_results_reproduction_and_limits.md)
5. [一次窄量纲核查](reviews/independent_dimension_review.md) / [T06交接建议](T06_ROUND2_HANDOFF.md)

[index.html](index.html)是本地无ZIP阅读入口，链接本包的原创报告、原始程序、schema、样例与来源摘要。官方论文/手册正文使用来源链接；包内没有复制受限原文。

## 已做什么

- 固定SQM-160 §11公式/常数组的Sauerbrey与有限负载Z-match，独立漂移校正、GLS质量速率，明确基频/刚性/分支限制
- 归一化方位各向源与接收投影、QCM净捕集/反应/流出账、工件入射质量与Al/Al₂/O₂元素核数守恒
- logQ、n、a、可选logη的有界稳健拟合，独立源观测辨识矩阵，相关协方差传播
- 严格schema与真实unknown模板；60项小测通过，1次独立窄量纲检查；合成真值、秩亏、温漂、遮挡、离群反例
- 完整可断点的多时窗/多工位重采样driver，默认plan_only；light仅12个窗口拟合，heavy与设备验证not_run
- 7条可追溯主来源记录、4张原创图（PNG/SVG）、精确文件清单与独立目录reader

## 最小复算

需要Python、numpy、scipy、jsonschema。已有环境，无需联网/安装。先在本目录：

    PYTHONDONTWRITEBYTECODE=1 python models/reader.py --directory .
    PYTHONDONTWRITEBYTECODE=1 python models/contract.py examples/synthetic_al.json
    PYTHONDONTWRITEBYTECODE=1 python models/contract.py examples/actual_unknown.json
    PYTHONDONTWRITEBYTECODE=1 python models/validation_driver.py

reader校验精确载荷路径、大小、SHA256及来源/样例，再复制到临时独立目录复跑全部小测与确定性合成结果；不依赖兄弟专题。不运行heavy，不改变冻结载荷。完整复算命令与实际环境见报告04和verification。

## 冻结范围

freeze_manifest.json精确枚举载荷；不hash自身、verification/freeze_receipt.json和用于核查上游未改的verification/outside_before.json、verification/outside_scope_check.json。上述排除项也明确写入manifest。临时pycache不属于载荷。freeze_receipt记录manifest哈希与reader结论，避免循环自校验。没有打包ZIP或上传副本。

实际几何、源状态、密度、捕集率、气相组成、温漂/粘弹适用域仍未测。部分论文只有摘要/索引或访问失败，全文核验缺口保留。完整Seed/Sol指定审查链未运行，不能称完整算法独审完成。
