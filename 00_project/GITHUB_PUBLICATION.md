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
- T01第二轮：46项允许文件及读者哈希清单；reader_manifest.json SHA-256 `4336e9cf78e9f71276fe6ef13b4c35e48a57a0955fd235798cbe94e8cee0aa23`
- 阶段边界：先前冻结内容不改；T02v0.3仍partial，T03/T04/T05实现就绪验证待完成；T06活动但未冻结成果不上传

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

## T01第二轮冻结增量

只发布 `01_machine_structures/round2_topology_alignment` 47文件，源ZIP SHA-256 `f13687c8692c389bfda95b6e82d372eb0aa6bf6ff281a1fada60f5dea5551aa8`；ZIP本身不上传。C/I原图准入unsupported、完整最终网格额外时间加密/连续极值/实机未完成。仅固定审计日志保留；原文、缓存和未来未冻结增量排除。

复核：`python -B 01_machine_structures/round2_topology_alignment/verification/build_reader.py --check`。此检查含24项单元测试，不会重跑全部研究网格。

## T02第二轮部分数值结果

发布 `02_machine_modeling/round2_dual_coverage_error_budget` 的精确允许文件及独立哈希清单；清单SHA-256 `9e0b83b83367ae82a3968be4f35ad450d56811a5e357f768fb20ebb390a40253`。状态frozen_bounded_partial，保留极近侧壁漏挡、源求积0.203%、独曝14.3ms>10ms和共同混叠反例。仅包检查通过，不能提升为全数值精度验证；尚不进入T03。原文、ZIP、缓存及后续未冻结修正不上传。

读者核验：`python -B 02_machine_modeling/round2_dual_coverage_error_budget/verification/build_reader.py --check --reader`。

## T02独立v0.2有限求交闭环

仅发布 `02_machine_modeling/round2_dual_coverage_error_budget/correctness_closure_v0_2` 17项允许文件，manifest SHA-256 `38cace86fd120248788747c5cbb3d14d2a462ca72b7b03d510a2236a38aa85af`。初次独立FAIL与修复后局部PASS证据均保留；只称受限编码几何求交子参考。旧v0.1的55文件和partial状态不变，0.203%/14.3ms源时间误差未解决，原件、ZIP、缓存排除。

只读完整性核验：`python -B 02_machine_modeling/round2_dual_coverage_error_budget/correctness_closure_v0_2/verification/reader_check.py --check --reader`，不运行会覆盖历史结果的独立审查脚本。

## 第二轮合并批次01

高计算量算法/设备driver完整实现，重型精度/性能验证待用户设备；小测试不是生产验收。减少上传频率，四项冻结增补合并一次提交。

- T02v03：44文件，`02_machine_modeling/round2_dual_coverage_error_budget/quadrature_control_v0_3/verification/reader_manifest.json` SHA-256 `d0a7ca29eee77f8e8e6db23971f4edc765bcf8c15a4d0f8091065c4fb14c8d7d`
- T03R2：44文件，`03_correction_plate_optimization/round2_dual_coverage_optimizer/verification/reader_manifest.json` SHA-256 `1b5755303e75c3d88edb78f204a1a9f7ac85b6aff931cb21051c42e46cc9dc27`
- T04R2：56文件，`04_coating_and_substrate_materials/round2_material_response_contract/freeze_manifest.json` SHA-256 `6475a92ab17538bea48c02524d55cad78e2a58845bfa035783176bcc6630ef90`
- T05R2：60文件，`05_evaporation_sources/round2_qcm_flux_transfer/freeze_manifest.json` SHA-256 `662af5524bb13c1094106dba2f9236af2e1f12d0dd57510ca547d338edf89e10`

严格按清单保留原创报告、代码、合成数据、原创图、短来源摘要及固定审计证据；ZIP、原文、缓存、无关日志不在集合中，不上传。T04含manifest自身，外层receipt不上传；T05另附作者明确确认的freeze_receipt，保留其引用的manifest哈希。T02条件包络、T03 inconclusive演示、未知真实参数和未执行重验证均保留。
