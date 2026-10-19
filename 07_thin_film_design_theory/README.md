# T07 薄膜设计理论

首轮版本：2026-10-02。原始需求为“研究薄膜设计，总结各类设计理论”。本轮形成从Maxwell边界到设计规格的连贯理论手册、8组原创可运行算例、稳定散射矩阵小核及18条主要原作者/论文/官方资料来源。

状态：公开理论与合成计算包可交协调验收和T08衔接。实际材料、真实设备、生产/环境/损伤验证尚未执行；指定阶段审查状态另见验收记录。没有以首轮完成代替生产资格。

## 阅读路线

1. [Maxwell边界、复数约定与功率](reports/01_maxwell_conventions_and_observables.md)
2. [导纳、特征矩阵与稳定散射矩阵](reports/02_admittance_transfer_and_scattering.md)
3. [相干边界、厚基片、角谱与偏振](reports/03_coherence_substrates_angles_and_polarization.md)
4. [四分之一波、匹配与周期反射带](reports/04_quarter_wave_matching_and_periodic_bands.md)
5. [对称膜系、等效层与结构综合](reports/05_symmetric_equivalent_layers_and_synthesis.md)
6. [腔、相位与群延迟](reports/06_cavities_phase_and_group_delay.md)
7. [渐变剖面、rugate与needle变化](reports/07_gradients_rugates_and_needle_variations.md)
8. [规格、公差与实际制造边界](reports/08_specifications_sensitivity_and_manufacturing.md)
9. [算例与复算说明](reports/09_worked_examples_and_reproduction.md)，[自动生成指标](reports/09a_generated_results.md)

## 可直接复用

- [8组算例的完整结果](data/example_results.json)、[CSV数据](data/spectra/)、4张原创图
- [教学计算核](models/optics_kernel.py)、[算例生成器](models/run_examples.py)、[单元测试](tests/test_optics_kernel.py)
- [有单位的设计/测量/制造接口](data/design_theory_contract.json)、[公式索引](data/formula_index.csv)
- [18条来源登记](data/source_registry.json)、[来源摘要目录](sources/README.md)
- [验收与证据](reviews/ROUND1_ACCEPTANCE.md)、[未决边界](reviews/OPEN_ISSUES.md)、[T08移交](T08_HANDOFF.md)

## 贯穿全册的约定

时间exp(−iωt)，被动材料N=n+iκ；波长为真空µm，厚度为物理µm，层序incident→substrate，幅度为切向E。s/p都使用同一切向E反射符号。给反射/透射功率必须携带端口导纳，给相位/GD必须携带参考面。

## 本轮优先范围与停止边界

优先完成系统设计理论、公式假设、稳定数值表达、相干/角偏振、匹配/等效/腔/渐变/needle概念、规格/公差和实际制程接口。完整优化器和高性能实现留T08；特定标准与试验留T09；各向异性、通用部分相干和特殊扩展待十个大项目首轮之后再排。

核心结论不能只靠单一来源：基本边界交叉用作者教材与方法论文，数值用解析极限/三种表达/冻结T06核检查。对发现的公式归一化与网页导数不一致显式记录，不假装原文都已正确或完整取得。

## 公开阅读包复核

公开包不含原文目录，也不含重复console日志。第09章列出的无参数包检查是完整本地归档模式；公开包请使用：

```bash
PYTHONDONTWRITEBYTECODE=1 python 07_thin_film_design_theory/models/check_package.py --reader
```

reader模式明确跳过本地原文存在/哈希检查，仍验证公式、来源登记、本地链接、冻结数值、T06依赖和最终测试证据；不表示原件已随包发布。


## 2026-10-19 手工研究增量

[多光谱红外结构与云端算法研究](../manual_studies/2026-10-19_multispectral_ir_structures/README.md)：补充结构族与自由结构搜索的比较边界、理想前向模型与实际 IR 验收的区别，以及受限合成算法试验。本增量不改变本专题既有冻结结论和验收状态；实验使用合成常数折射率，未验证真实红外材料或器件。
