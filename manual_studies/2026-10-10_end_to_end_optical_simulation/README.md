# 端到端光学仿真成熟化研究

状态：资料基线（作者研究稿件已整理；来源核验与数值验证尚未由本包执行）  
作者/审查者与日期：三份原稿未署个人作者；整合：Codex；2026-10-10；独立审查者待定  
原始需求映射：`RQ-01` 膜层/沉积/偏振；`RQ-02` 几何光追到波动成像；`RQ-03` 非顺序光谱杂散光。ID 是本包内部索引；来源是 2026-10-10 用户委托及本目录 `incoming/` 的三份原稿，原消息无稳定行号。

## 阅读指南

- [综合报告](report.md)：统一物理层次、数据契约、证据边界、冲突处理和分阶段路线。
- [专题一：位置相关膜厚与偏振输运](topics/01_polarized_thickness_mapping.md)
- [专题二：波前、偏振光瞳与衍射成像](topics/02_wavefront_imaging_bridge.md)
- [专题三：非顺序光谱、偏振与杂散光](topics/03_nonsequential_spectral_straylight.md)
- [接口与验收矩阵](interface_acceptance_matrix.md)
- [来源目录](sources/README.md) / [来源索引](sources/index.md) / [结论—来源证据链](sources/claim_map.md) / [来源登记 JSON](sources/source_register.json)
- [建议新增导航段](suggested-navigation.md)

三份收到的原稿在 `incoming/` 中原样保留。专题文件按研究库提供的 11 节模板整理；正文摘要与原稿、来源记录互相链接。原稿中的“已核验”等作者自述照原文保留；`source_register.json` 的 `U` 只表示整合包没有重新访问来源。

## 基线与合并状态

目标研究库：`https://github.com/ii33/coating-research-library`  
基线：`main` commit `2f62e74ee8f90039148b71b6b0f9f4f41849d156`，tree `c9f1234fcdcf3d9551f2a8f2c43c8c2e300b3159`。  
目标路径：`manual_studies/2026-10-10_end_to_end_optical_simulation/`。  
本地包状态：待合并、未提交、未推送、未发布；这不是研究库工作副本，未改研究库 root `STATE`、README 或索引。

按已提供的权威 main 快照，`manual_studies/` 当前可见 `2026-10-02_morningtech_mxc`；此目录未显示先前 TFCalc 历史，不能据此判断 TFCalc 研究遗失。上游 README 中已有 ITO 与第三轮入口须保留。本包只建议新增一条导航，不直接编辑上游 README。

## 版本与核验说明

资料依据是三份研究代理稿件，原稿全文在 `incoming/`。来源索引从原稿的 Markdown 链接提取 104 个唯一 URL；本包未重新读取链接目标，未安装或运行候选软件，未做光学数值仿真，也未在目标机器上跑性能测试。每条来源登记当前标为 `evidence_level=U`、`read_status=metadata_only`；这不覆盖原稿中的来源等级、作者自述核验状态和命题状态。

只有在父任务审阅通过后，才将本包作为独立文件写回指定研究库路径；仍需另行决定是否通过已连接 GitHub 写回。本包不执行该动作。
