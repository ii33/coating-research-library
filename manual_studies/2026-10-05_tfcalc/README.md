# TFCalc 功能与算法独立研究

研究日期：2026年10月5日。

本目录保存原创派生研究、功能证据、验收夹具及交付文件。原始压缩包、厂家手册、教程文档和原页图片不包含在本目录或交付文件中；未发布至 GitHub。

## 用户交付

- `deliverables/TFCalc功能与技巧及项目实现方案.docx`：14页可编辑中文报告，覆盖完整设计与工艺链、算法、复用范围、接口、阶段门槛与验收矩阵
- `deliverables/TFCalc功能证据与实现检查清单.csv`：74条双语证据记录，中文列名、UTF-8 BOM，实施阶段与报告的 P0–P3 对齐

## 原创研究与证据

- `reports/TFCalc功能与技巧及项目实现方案.md`：报告正文源
- `reports/manual-algorithms.md`：详细功能、公开物理和独立算法推导；其研究分级 P0–P2 与交付报告分阶段 P0–P3 分别保存，不能混同为已完成状态
- `reports/reuse-audit.md`：现有产品与 T06/T07/T08 参考核的复用边界
- `evidence/feature-evidence.json` 和 `evidence/feature-evidence.csv`：研究原始分级及74项页码证据
- `evidence/validation-oracles.json`：22项解析/行为验收夹具，未宣称产品已经通过
- `evidence/validation.json`：DOCX全页视觉验证及CSV结构验证
- `evidence/provenance.json` 和 `evidence/derived_notes_hashes.json`：来源边界与派生资料读回哈希
- `evidence/delivery_receipt.json`：两个交付文件的已验证保存记录

所有新领域模型、TaskService接口、优化扩展、制造统计和空间耦合均为独立实施建议。商业软件未公开的内部规则没有被推断为事实；未复制其界面、标识或专有源代码。
