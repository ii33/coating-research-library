# ZnS 既有研究与接入缺口核对

2026-10-04。结论：研究库已包含 ZnS 材料证据、通用蒸发算法、分物种质量守恒和后续响应合同；此前把“产品只接了材料配置”表述成“缺少研究基础”是不准确的。应先复用库内证据与代码，再补真正缺少的 ZnS 专属关系。

本次只做有界库存审计与已取得文献的整理，不改产品、不改既有冻结文件、不上传或推送。研究库路径以下均相对于项目根目录。

## 核查范围

本地全文搜索覆盖专题01至11及跨专题资料；核读T04/T05第一、二轮、T06光学代理、T08引用数据、T10条件矩阵。由于本地快照缺第三轮，另读取远端提交 `2b13f2c81aa8ca8aa3d25808692f15096e1c7866` 完整树，3245项且未截断，并核读T04/T05第三轮的README、关键证据章、模板及模型代码，以及10月3日文献补充。九个关键本地文件的Git blob SHA与该远端提交一致，详见[核对记录](../99_sources/supplements/2026-10-04_zns_reuse_audit/data/verified_remote_files.json)。这不是全部3245文件逐字重读，也不是产品代码审计。

## 复用矩阵

| 能力 | 库内已经有的证据或实现 | 当前接入判断 |
|---|---|---|
| ZnS源料性质及蒸发条件 | `04_coating_and_substrate_materials/cards/02_ZnS_film.md` §1.3；源分册 `reports/fluoride_sulfide_substrate_cards.md`；IR01/IR02原厂来源 | Mo舟/衬套、解离、速率/QCM设置、压力锚点和温度冲突均已存在。可先作为来源化材料选项，不应重新研究才显示 |
| 两点蒸气压 | 同卡§1.3：950°C时10⁻² mbar，1070°C时10⁻¹ mbar，即1223.15 K/1 Pa与1343.15 K/10 Pa | 仅在报告，未进入`data/property_records.json`；T05矩阵`vapor_pressure_model=null`。这是“报告→结构化→计算”断点，不是文献无资料 |
| ZnS膜结构化物性 | `04_.../data/property_records.json` IRP-001至010；`data/ir_property_records.json` | 10条：6个n、隔离k、QCM密度4.09、速率0.8–2.5 nm/s、未知膜导热率。允许目录参考模式；不能把design_ready=false误读成没有值，也不能自动改称本机实测 |
| ZnS块材热/力学性质 | `cards/13_ZnS_substrate.md`；IRP-045至060 | 标准CVD与Cleartran各自有密度、导热率等。源料粉床、薄膜、块材应分状态；块材数据可做明确标注的先验/敏感性，不应直接赋给高温颗粒床 |
| 蒸气压及HK核 | `05_evaporation_sources/models/source_reference.py`：`vapor_pressure_pa`、`hertz_knudsen_kg_m2_s` | 已有可复算函数，均为单物种/局部恒焓近似。可复用数学核；ZnS须增加分压/分物种适配，不能把总压配97.44 g/mol直接当真实解离蒸气 |
| 开放舟有限面发射 | 同文件：`rectangle_source`、`disk_source`、`flux_kg_m2_s`、`cosine_pdf` | 已有几何计算。可接Mo舟尺寸、料面与温度权重；n是条件参数，不是ZnS固有常数 |
| 盖舟/口沿 | 同文件：`circular_aperture`；`reports/02_resistance_sources_and_thermal_history.md` | 直视裁剪已编码；壁面捕集/再发射、通道传输概率只讨论未实现。盖舟不能仅改一个n称为物理模型 |
| 电阻舟热史 | 同文件：`lumped_history`；上述报告两热容方程 | 单热容显式Euler及质量/能量核算已写，测试用虚构单相材料；两节点模型是报告级。真实ZnS需相应热容、有效导热/接触和解离焓适配 |
| 电子束足迹与热源 | `gaussian_footprint`；`reports/03_electron_beam_sources_and_sweep.md` | 高斯发射权重已写，热PDE/扫束非线性已给公式。该函数是现象学发射足迹，不是已求解ZnS电子沉积能量/温度场 |
| 分物种粒子→元素→质量 | `05_.../round2_qcm_flux_transfer/models/qcm_flux.py`：`species_elements`、`mixture_from_mass`、`gas_impingement` | 已有算法，可传显式Zn/S原子量和Zn、S₂化学计数。但默认质量表只有Al/O，不能零修改称ZnS可跑 |
| 基片留存与净生长 | 同文件`retained_elements`及T04第二轮`models/contract.py` | 前者硬用全局Al/O质量表，需最小参数化适配；后者已有密度/组成/零净/负净守卫。保留未知值，不用它阻止“文献先验情景模式” |
| 材料映射与证据状态 | `04_.../round2_material_response_contract/data/priority_material_mapping.json` | ZnS映射到10条记录；n_reference的null表示未选特定记录，非无来源。材料库读取必须同时解析evidence_refs，不能只看value |
| 第三轮有界响应 | 远端`04_.../round3_bounded_material_response/models/bounded_response.py`及模板 | 代码显式只接synthetic/unmeasured_template，并拒绝真实校准材料预测。可复用有界积分/比较架构，需扩展输入类别与来源语义；不是隐藏的ZnS经验定律 |
| 第三轮源与留存辨识 | 远端`05_.../round3_source_retention_identifiability/models/source_retention.py` | 有angular_pdf、finite_incident、雅可比、秩分析和T04桥接，参考数值仍synthetic。可用于判断参数能否分离，不能代替ZnS源数据 |
| 光谱计算 | `06_optical_coating_families/data/material_proxies.json`的ZnS_IR_proxy；T08冻结代理复用 | ZnS n表已用于光学参考计算，k=0是显式理想假设。此处“已有材料仿真”是真实存在，但属于光学，不能自动等同蒸发源热化学 |
| 离子辅助耦合 | `10_ion_sources/data/material_response_matrix.json` MAT-02；`reports/04_conditional_material_matrix.md` | 有Zn/S/O、应力、FTIR、晶相及方法差异证据；没有可直接复用的Kaufman同条件完整响应常数。应沿其来源扩充，不重建无出处空表 |

## 已定位的四处断点

1. 报告中的部分源物性没有成为机器参数。尤其蒸气压锚点、z-ratio=0.775、源容器分类不应只留在人读卡片里。
2. 映射合同把“未选目标记录”表示成null；消费者若不追踪evidence_refs，会错误表现为完全无数据。
3. 通用源核已有，但材料专属热化学并未装配。默认Al/O常量和单分子HK不适合直接承担ZnS解离。
4. 第二、三轮大量精力用于真实验证资格/不可辨识性，参考算法刻意synthetic。产品仍需一个诚实的“文献参考预测/区间情景”层；它与机器已验证预测可以同时存在，不能只允许后者而让前者全空。

## 最小接入顺序

第一步复用：把现有ZnS卡片的条件化数字/供应商/出处和冲突状态读入材料详情；沿priority_material_mapping读取已存在的引用；输出不隐藏目录数据。

第二步计算：复用source_reference的有限源/遮挡/HK接口与qcm_flux的元素守恒，明确开放Mo舟、盖舟、电子束三种结构。先支持文献先验和用户提供源率两种输入。单物种函数保留但不能默默作为ZnS默认。

第三步补齐：只为确定缺项增加ZnS气相热力学、升华动力学和高温热物性。已得到的补充证据见[增量记录](../99_sources/supplements/2026-10-04_zns_reuse_audit/README.md)。对未建立的接触热阻、粉床导热和壁面留存，允许明确上下界敏感性；需要机器绝对精度时再做对应校核。

验收先分别检查资料溯源、单位、温域、组分/质量守恒和参考算例，再检查实际机台。不能把数值通过等同物理已验证，也不能以尚无物理验证为由不接已有研究。

## 当前范围与限制

没有改既有材料记录、既有冻结代码或生产设置，没有运行新科学测试，没有产品接入结果。远端关键词搜索Schaefer/Cardona未命中只作为辅助，不证明全库绝对不存在；补充记录标记为“本次有界库存未找到”，不以搜索空结果断言全球新发现。
