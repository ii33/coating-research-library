# T04 镀膜材料与基片材料工程手册

第一轮公开研究冻结 v1，2026-10-02。原文优先的12种膜料与4种基片全部建立独立卡；附76条来源及逐来源摘要、207条条件化参数、5组本地CC0原始n/k数据、可复算光学例与12项通过的数值/数据检查。**这里完成的是公开资料、工程推导与有限数值验证；没有完成本机成膜、来料、光学性能或量产验收。**

原始范围：[工程科研.txt](../00_project/工程科研.txt)第7行；前置：[T03移交](../03_correction_plate_optimization/T04_HANDOFF.md)。完成这些优先核心后转T05，未列材料扩展仍留待十个大项目首轮之后。

## 阅读入口

1. [工程手册总论](reports/01_engineering_handbook.md)：状态/单位、n/k、透过/反射、密度与光学厚度、蒸发接口、计量和误差预算
2. 按下面原文顺序阅读16张独立数据卡
3. [跨材料选择与证据缺口](reports/02_cross_material_selection.md)：NIR低损耗膜、多光谱窗口、金属反射层选择流程和冲突隔离
4. [数据结构与验证](reports/03_data_quality_and_validation.md)：schema、文件用途、版权及复用
5. [第一轮验收记录](reviews/first_round_acceptance.md)与[T05移交](T05_HANDOFF.md)

## 优先材料数据卡 原文顺序

| 顺序 | 镀膜材料或基片 | 独立工程卡 |
|---|---|---|
| 1 | Ta2O5 镀膜材料 | [五氧化二钽](cards/01_Ta2O5_film.md) |
| 2 | ZnS 镀膜材料 | [硫化锌膜](cards/02_ZnS_film.md) |
| 3 | TiO2 镀膜材料 | [二氧化钛](cards/03_TiO2_film.md) |
| 4 | YbF3 镀膜材料 | [氟化镱](cards/04_YbF3_film.md) |
| 5 | SiO2 镀膜材料 | [二氧化硅](cards/05_SiO2_film.md) |
| 6 | MgF2 镀膜材料 | [氟化镁](cards/06_MgF2_film.md) |
| 7 | Al2O3 镀膜材料 | [氧化铝](cards/07_Al2O3_film.md) |
| 8 | H4 镀膜材料 | [商品高折射率材料](cards/08_H4_film.md) |
| 9 | Ge 镀膜材料 | [锗膜](cards/09_Ge_film.md) |
| 10 | Cu 镀膜材料 | [铜膜](cards/10_Cu_film.md) |
| 11 | Cr 镀膜材料 | [铬膜](cards/11_Cr_film.md) |
| 12 | Al 镀膜材料 | [铝膜](cards/12_Al_film.md) |
| 13 | ZnS 基片 | [标准CVD与多光谱ZnS](cards/13_ZnS_substrate.md) |
| 14 | Ge 基片 | [锗光学基片](cards/14_Ge_substrate.md) |
| 15 | K9 基片 | [K9与明确标注的H-K9L代表](cards/15_K9_substrate.md) |
| 16 | ZnSe 基片 | [硒化锌](cards/16_ZnSe_substrate.md) |

YbF3身份已按用户确认关闭，不改成YF3。H4按厂家/货号/版本核对，不给予通用固定配方。K9实际来料牌号未知，本轮H-K9L代表不能自动替代用户库存，也不等同N-BK7。ZnS膜与CVD/HIP块材各自立卡。

## 有用的首轮结果

- Cu在632.8 nm的两组实际样品来源n/k，给理想半无限R约91.83%与96.89%；表值不是实际薄膜性能上限，也不能把差值当本机保证提升
- Ge n≈4的裸窗外透过约47%，不能把未透过光全部当体吸收；高温/掺杂/厚度需单独建模
- Ta2O5名义纯样品检出Ti、ZnS网页k可疑值、ZnS标准/MS硬度排序冲突已隔离，保留来源而不静默平均
- IAD可以降低氟化物水吸收，同时引入失氟、应力与短波损耗代价；H4的HD源料装填密度不等于最终膜密度

## 数据与复算

- [16项机器目录](data/materials_manifest.json)
- [76条合并来源登记](data/source_registry.json)及[sources说明](sources/README.md)
- [207条参数记录](data/property_records.json)与[数据schema](data/property_record.schema.json)
- [金属衍生光谱点](data/metal_nk_derived_points.json)、[原始数据哈希清单](data/local_originals_manifest.json)、[算例输出](data/worked_examples.json)

在本目录运行：

```sh
python models/optical_examples.py
python -m unittest discover -s tests -v
```

完整原始光谱按项目要求只留本地，不随公开仓库发布。若本地已有匹配哈希的原件，可用 `python models/build_nk_points.py` 重建派生点。卡片与合并参数由 `python models/build_material_package.py` 从三本证据分册生成；修改后需重新生成并测试。测试默认不联网、不安装依赖、不写全局项目状态。

## 证据分册与维护

- [氧化物/H4](reports/oxide_material_cards.md)
- [氟化物/硫化物/基片](reports/fluoride_sulfide_substrate_cards.md)
- [Ge与金属](reports/metal_ge_material_cards.md)

数据卡包含身份、物性表、光学条件、蒸发选择、失效/测试、安全、算例和未知项。已知数值不以无单位形式游离存在，未知值不填0。复核结果只代表实际完成的范围，指定完整模型审查链的最终状态由项目统一记录。
