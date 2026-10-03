# 08 · 本地验收、独立reader和边界

## 8.1 交付结构

reader.html把原创报告、结果、图与来源链接组织为无脚本离线reader；PNG/SVG为本轮原创，逐张看像素。HTML只通过静态本地链接/锚点/资源检查。既有浏览器布局权限限制保持unverified，不启动headless、不重试socket或升级权限绕过。PNG检查不等于浏览器布局已通过。

verification/reader_manifest.json精确记录payload路径、字节、hash。ZIP仅包含manifest允许的payload加manifest本身；控制回执、ZIP自身和sources/originals不在payload内，避免自引用。freeze_receipt在包外绑定manifest与ZIP的最终hash、计数及独立复算/负例证据；final_receipt_check再核对这些值。原文PDF只在本地sources/originals存档，两个原始PDF不分发。

## 8.2 独立解压验证

冻结器把ZIP解压到全新临时目录，使用复制依赖验证hash，检查reader全部本地资源，再运行窄单元测试和T05 unknown来源导入护栏。它不访问源项目siblings、网络或完整项目快照。还在隔离副本分别篡改payload、删除依赖、加入未列文件，要求reader都拒绝。

源项目旧冻结/root plans/product的前后hash比较单独在作者冻结阶段完成，只证明本次授权写入边界；它不是读者运行依赖。冻结后不修改旧目录，不上传，不push，不自动启动T09。

## 8.3 可以接受与仍待解决

本地研究实现已具备二维合同、完整预算驱动、tiny证据、UNKNOWN传播、目标界、反例、窄独核、PNG像素检查与可独立解压复算包。完成这些只称local_freeze，正式模型链pending；point12 partial与point2 conditional non-strict不升级。

尚未取得真实同状态n/k/密度/组成/温度数据，尚无真实仪器误差或来源联合可达性，尚未完整运行full矩阵、设备或多批次。若真实数据与合成合同不同，必须先升级数据和算子合同，不能直接把本包阈值拿去生产判定。

## 8.4 T09有界交接

下一题只给一个有限问题：如何把此二维候选集合证据与UNKNOWN状态安全映射到既定下一层验收接口，尤其保持“证据排除”“未决保留”“搜索未找到”三分语义。建议先沿用一个样品两通道及本JSON记录，研究同状态数据缺口与有限补测选择，不扩到37配方、设备任务或无限维源反演。具体见T09_ROUND3_HANDOFF.md。本交接不是启动授权。
