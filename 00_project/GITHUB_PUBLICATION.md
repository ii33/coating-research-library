# 私有 GitHub 研究基线

- 仓库：<https://github.com/ii33/coating-research-library>
- 可见性：私有；默认分支：`main`
- 发布内容：项目规划、按原字节保存的需求清单、原创研究报告和图示、必要摘要与引用链接、数据模板、来源登记和可复算脚本
- T01：来自冻结读者包 `T01_planetary_structures_v0.2_reader.zip`，SHA-256 `680e0148cff5bef02b290be16a979b9cc8896677bd3579b2d049b9920d2425b3`
- T02：来自冻结读者包 `T02_modeling_v0.1_reader.zip`，SHA-256 `684b63f228b31a2ba882b08f60cbc1e7a13173283d0e79b03fa4fc861d3c344b`；内容标识 `db16fe512e848532c5e2b00c3fc8d5ec3469d6a7764e5872840f98eff69ba1a2`
- T03：冻结读者包 `T03_mask_optimization_v0.1_reader.zip`，SHA-256 `36b2759639d2d7f519304c5bf77ebc6a38de44c572f78bfa6fa02f4a24debe73`；内容标识 `64f7ea5beaa18ef916b28ee20aff5f0abee6826698ac365b752ba0e561cd46cd`
- 阶段边界：T01–T03理论优先范围可移交，T04接续启动；实机验证、制造放行和指定模型完整正式审查未完成

## 不纳入仓库的内容

四份第三方原始PDF、两份专题存档的第三方原文HTML、下载缓存、生成的压缩交付包、临时文件与本地环境配置不上传。来源记录中的原文路径和哈希是研究工作区存档记录，不表示仓库包含对应原文。需要查阅原文时使用来源登记中的官方链接，并遵守原站访问与权利条件。

## 复核

从仓库根目录运行：

```sh
python 00_project/check_github_snapshot.py
python 01_machine_structures/verification/check_initial_release.py --reader
python 01_machine_structures/reviews/planetary_kinematics_check.py
python 02_machine_modeling/verification/run_verification.py
python 02_machine_modeling/verification/check_release.py
python 02_machine_modeling/models/run_case.py 02_machine_modeling/data/synthetic_case.json --output /tmp/t02-example
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 python 03_correction_plate_optimization/verification/run_verification.py
python 03_correction_plate_optimization/verification/check_release.py --reader
```

读者模式的来源schema检查使用 `jsonschema`；原文PDF未随仓库发布，四项缺失原文检查会明确标为跳过。轻量检查不代表已进行实体设备校准或生产验证。

`github_snapshot_manifest.json`记录发布副本逐文件SHA-256。`planning_baseline_manifest.json`已按当前规划文件重算；`integrity_check.json`保留最初建库时点的历史核查，不代表后续技术结论验收。Git保留文件字节，不保存原文件的操作系统扩展属性。

T03冻结清单保留原始研究工作区的交付检查记录；原文HTML不随仓库发布。复跑采用 `--reader` 明确标记原文检查不适用于读者副本，且会重写生成的检查结果；不要将此重跑输出与冻结记录逐字节相同混为一谈。
