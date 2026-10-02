# 私有 GitHub 研究基线

- 仓库：<https://github.com/ii33/coating-research-library>
- 可见性：私有；默认分支：`main`
- 发布内容：项目规划、按原字节保存的需求清单、原创研究报告和图示、必要摘要与引用链接、数据模板、来源登记和可复算脚本
- T01：来自冻结读者包 `T01_planetary_structures_v0.2_reader.zip`，SHA-256 `680e0148cff5bef02b290be16a979b9cc8896677bd3579b2d049b9920d2425b3`
- T02：来自冻结读者包 `T02_modeling_v0.1_reader.zip`，SHA-256 `684b63f228b31a2ba882b08f60cbc1e7a13173283d0e79b03fa4fc861d3c344b`；内容标识 `db16fe512e848532c5e2b00c3fc8d5ec3469d6a7764e5872840f98eff69ba1a2`
- T03：冻结读者包 `T03_mask_optimization_v0.1_reader.zip`，SHA-256 `36b2759639d2d7f519304c5bf77ebc6a38de44c572f78bfa6fa02f4a24debe73`；内容标识 `64f7ea5beaa18ef916b28ee20aff5f0abee6826698ac365b752ba0e561cd46cd`
- T04：公开研究v1，123份清单内文件及冻结清单；`reviews/freeze_manifest.json` SHA-256 `c85960d3b9703426a6fa7f2fe75d1f0ed699c267702df3eb1e2566865fd907f4`
- T05：v0.1首轮源研究，71份清单内文件及冻结清单；`release_manifest.json` SHA-256 `fc54cef8e0f0f4f16ebc73dbbb7b4e39c69580af1bc2dd68b9c4c3a1a556fb26`
- T06：67份清单内冻结文件及清单自身；`data/deliverable_manifest.json` SHA-256 `8311a45c4bb45542f2abe8098071d713497754a9bd01731b772f7143cef724f9`
- T07：65份清单内文件及清单自身；`data/deliverable_manifest.json` SHA-256 `9f382bc2d7d2f5a86570105695f1f9b95d5454caccadd19c0bed1ee85588b238`
- T08：73份精确允许文件；发布控制清单SHA-256 `6d0128b90679ef76e6b3bb9a59a88992ac1f72551647e00cbb556a2e05db6653`（控制清单自身不上传）
- T09：81份清单内文件及清单自身；`data/deliverable_manifest.json` SHA-256 `f375623abea029b72bc5ccfa1ac80a07099fde6af28c406794925057483ac441`
- T10：82份清单内文件及清单自身；`release_manifest.json` SHA-256 `fe064466972292515d4fcf8b0449b0ab54339b6c779fb555830739385daff72f`
- 阶段边界：T01–T10第一轮优先公共资料、理论和合成基础已覆盖，T01第二轮有界拓扑与双覆盖接口研究进行中；正式完整审查、实机校准和生产资格未完成

## 不纳入仓库的内容

T01与T07合计八份第三方原始PDF及原文提取文本、三份专题存档的第三方原文HTML、T04五份CC0原始光谱及整个originals目录、下载缓存、生成的压缩交付包、临时文件与本地环境配置不上传。来源记录中的原文路径和哈希是研究工作区存档记录，不表示仓库包含对应原文。需要查阅原文时使用来源登记中的官方链接，并遵守原站访问与权利条件。

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
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s 04_coating_and_substrate_materials/tests -v
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 python 05_evaporation_sources/tests/test_source_reference.py
PYTHONDONTWRITEBYTECODE=1 python 05_evaporation_sources/tests/check_release.py --reader
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s 06_optical_coating_families/tests -v
PYTHONDONTWRITEBYTECODE=1 python 06_optical_coating_families/models/check_package.py
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s 07_thin_film_design_theory/tests -v
PYTHONDONTWRITEBYTECODE=1 python 07_thin_film_design_theory/models/check_package.py --reader
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 python -m unittest discover -s 08_stack_optimization_algorithms/tests -v
PYTHONDONTWRITEBYTECODE=1 python 08_stack_optimization_algorithms/models/check_package.py
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s 09_standards_and_qualification/tests -v
PYTHONDONTWRITEBYTECODE=1 python 09_standards_and_qualification/models/check_package.py
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s 10_ion_sources/tests -v
PYTHONDONTWRITEBYTECODE=1 python 10_ion_sources/models/check_package.py --reader
```

读者模式的来源schema检查使用 `jsonschema`；原文PDF未随仓库发布，四项缺失原文检查会明确标为跳过。轻量检查不代表已进行实体设备校准或生产验证。

`github_snapshot_manifest.json`记录发布副本逐文件SHA-256。`planning_baseline_manifest.json`已按当前规划文件重算；`integrity_check.json`保留最初建库时点的历史核查，不代表后续技术结论验收。Git保留文件字节，不保存原文件的操作系统扩展属性。

T03冻结清单保留原始研究工作区的交付检查记录；原文HTML不随仓库发布。复跑采用 `--reader` 明确标记原文检查不适用于读者副本，且会重写生成的检查结果；不要将此重跑输出与冻结记录逐字节相同混为一谈。

T04本地完整测试为12/12通过；发布副本没有原始光谱，因此12项测试中原件哈希/重建项明确跳过，其余11项可离线运行。冻结检查记录不表示仓库包含原始数据；来源条件、未知值、严格上界和隔离参数未被发布流程改写。

T05清单排除完整originals目录、字节码、自清单与生成检查日志；发布保留原研究的数值和限制。`--reader`跳过原文存档存在/哈希/许可三项核查，不将本地原文的可读权限推导为仓库含全文。

T06六份光谱CSV为本库原创参考计算结果，按冻结字节发布，非第三方原始光谱。完整originals目录、缓存和两份重复控制台输出排除；最终测试日志、包检查JSON及两张原创图的预览作为冻结审计证据保留。

T07按明确允许列表发布；4份PDF和2份原文提取仅本地留存。读者模式明确跳过原文存在/哈希验证，其余包检查保留；最终测试日志、包检查JSON和四幅原创图预览作为冻结审计证据，重复控制台日志排除。真实材料、设备与指定正式审查状态未被发布流程改写。

T08使用作者明确的发布允许清单；整个sources/originals下6份第三方原文、缓存、ZIP与重复控制台日志排除。B03预算耗尽未收敛/未达教学规格等失败证据随冻结结果保留；原文缺席的读者副本只核查可用公开包，不误称查过未打包全文。T06/T07文件未改。

T09按81项原创文件清单及清单自身发布，排除整个originals、qa_render、缓存和临时文件；最终unit_test_output.txt保留为28项合成/单元检查证据。没有付费获取或分发标准全文；GJB现行证据、真实样品与能力缺口保留，不作产品合格或认证声明。

T10按release_manifest.json精确允许列表及清单自身发布，全部sources/originals、NASA原文/全文提取、缓存和ZIP排除。最终测试/来源检查记录保留为审计证据。有限关键数值独立复核通过，不等同指定完整外模型链、实际设备校准或生产资格。T01第二轮有界拓扑与双覆盖接口研究已启动，尚未冻结的扩展文件不纳入本次快照。

同次发布首轮有限复核与成熟度汇总：FIRST_SWEEP_REVIEW_DRAFT.md，SHA256 de68d0ac6ad78e4099202e863c4929a1681ebb950ffbab3d4de826bfa8a943aa；不补签指定完整外模型审查链。
