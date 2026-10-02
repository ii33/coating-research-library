# T04 第二轮材料响应输入合同

本地冻结的有界研究与实现包。把 N_net、h、D、U、R、epsilon 接到有条件、可追溯的材料/基片记录；没有实际膜校准或生产资格。仅新增本目录，未改前轮、产品或全局STATE，未push/上传。

## 先读这些

1. [材料与基片响应输入合同](reports/01_material_response_contract.md)：代表组合、守恒量、实际膜密度、组成与零/负净沉积边界
2. [单位和不确定度传播](reports/02_uncertainty_and_validation.md)：区间与协方差、七轴、不完整输入阻断
3. [辨识实验与合成校准](reports/03_identification_experiment_plan.md)：可辨识/不可辨识两例、实际最小测量、重任务计划
4. [逐字段机器映射](data/priority_material_mapping.json)：12膜料+4基片，207上游记录与336字段状态
5. [单次窄量纲核查](reviews/independent_dimension_review.md)、[下一T05建议](T05_ROUND2_HANDOFF.md)

SiO2薄膜/熔融石英基片是公开来源较完整的方法示范。熔融石英不属于原优先四种基片，不替代用户来料。10条来源重新有界核验；其余T04/T10证据保留继承访问层级，没有冒充完整再验证。来源摘要均原创，包内没有论文原件或完整光谱原始数据。

## 结果与边界

- strict JSON schema + stdlib验证器与区间计算；8个机器实例，其中真实代表模板6项输出因未测阻断
- 54/54轻量测试通过，包括8个独立窄回归；发现的3个库存/分母门控缺口已修复并保留修复前证据
- 合成正沉积例：N_net=2e19 atoms/m²、D=6e18 particles/m²、U≈128.1741 J/m²、R=0.3、epsilon=40 eV/net atom。人为膜密度2150 kg/m³对应h增量≈0.309365 nm，不是SiO2实验物性
- 零/跨零/负净沉积不给稳定R/epsilon；近零宽区间只留诊断界。成分/密度变动、净库存耗尽和块材密度误用阻断厚度转换
- 真正n/k、应力、附着、Y(E,theta)仍需目标样品的测量/有效物理模型。现有剂量指标不自动产生生产响应
- 100000次玩具校准重采样driver完整写出；任务plan_only/not_run，无设备资源采样、物理机器动作或付费任务

## 小型复算

Python 3.10+标准库可运行验证、计算、测试和reader。无需联网/安装依赖/原始论文：

```sh
python models/contract.py examples/positive.json
python models/contract.py examples/reference_unmeasured.json
python -m unittest discover -s tests -v
python models/calibration_driver.py --mode light
python models/calibration_driver.py --mode plan
python models/reader.py --directory .
```

重采样模式必须额外显式开关，当前不要运行。绘图重建另需matplotlib，仅作者小型绘图用；reader直接使用已冻图，不依赖matplotlib。原始冻结结果在verification/example_results.json与synthetic_calibration.json。

## 包与完整性

freeze_manifest.json精确列出reader载荷的相对路径、字节数和SHA256；reader对路径集合、重复路径、哈希、CRC、示例复算、证据索引和测试同时检查。T04_round2_material_response_contract_reader.zip只包含载荷+清单；清单与ZIP不循环hash自己。verification/freeze_receipt.json单独记录清单及ZIP哈希和reader结果。

verification/unchanged_baseline.json用于作者核前轮/全局未改，不随reader包发；冻结收据、ZIP和临时pycache也不属于payload。reader在独立临时目录解包运行，无法依赖项目兄弟目录或本地原件。继承的数值参数仍位于原冻结上游包；本包只附最小ID/单位/来源URL索引以解析所有映射引用，不假装把未随包附带的原文也验过。

状态 implementation_ready_validation_pending。未完成：实际样片输入、真实响应辨识、上游oracle闭合、重任务设备验证、完整指定审查链、生产验收。下一T05仅为建议，不自动启动。
