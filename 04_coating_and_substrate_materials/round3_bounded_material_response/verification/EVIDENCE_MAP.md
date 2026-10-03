# 需求与证据映射

| 要求 | 证据 | 边界 |
|---|---|---|
| 固定几何运动时钟 | data/tiny_results.json两Scene；dependencies/t03全models | 仅既定两板候选和仿射族 |
| 比例与核形状分离 | reports/01、03；bounded_response.py | 真实系数unknown |
| 材料/基片经验 | sources/summaries/BR-S01–06；reports/02 | 来源数值不做拟合输入 |
| 排名反转/重叠 | reports/04；data/tiny_results.json | 合成反例 |
| 正比例需要目标同步 | test_same_scale_target_preserves；独立单位核查 | 侵蚀等项也需完整同比 |
| 负、零、近零、unknown | test_response.py及denominator_examples | 不截断、不奖赏 |
| 完整上游forward/event | upstream_full_forward对象；23复制依赖清单 | point12 partial、point2非严格不变 |
| 完整待授权算法 | models/device_driver.py；data/device_validation_plan.json | 默认plan_only，未运行重任务 |
| 独立reader | reader_check.py；reader_manifest.json；外部解压验证 | 内容完整性不是科学证明 |
| 原文与摘要分开 | sources/originals_local归档回执 | 2个CC BY原文排除reader |
| 可视化验收 | visual_check.json | PNG查看；HTML layout未验证 |
| 冻结不越权 | origin_integrity_check.json；release_receipt.json | 根计划/产品/用户电脑未改 |
| 一次窄独查 | reviews/INDEPENDENT_UNIT_CHECK.md | 不代替指定链，不重复审查 |
