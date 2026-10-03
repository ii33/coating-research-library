# 2026-10-02 第二轮尾批与第三轮统一发布

此文件所在提交是私有仓库`ii33/coating-research-library`的统一研究发布批次。发布基线为main的`31744525b4cdde04fad31aaf58e6148f7819ce62`，预检时远端共有1043个文件且未发生后续变更。采用该tree作为base，保留全部既有无关路径，以非force快进更新main。

## 精确范围

- R2T06–T09：沿用先前候选的完整原字节载荷、manifest和收据，重新核对原字节
- R2T10：仅发布`publication_packages/t10_round2_portable_v1/PUBLICATION_ALLOWLIST.txt`规定的94文件。允许清单SHA256为`13129575843d7230f5803446444bf0f4774a1bfa8ed23fe1689a45b3cabac375`，新派生manifest为`d5d358e5d430cd1e7836cc49c0abbeddbf981f9fdb81e7c9df16b1576db7e90b`
- R3T01–T10：每个精确reader manifest内全部payload、manifest自身及特列外置冻结/检查收据。递归复制依赖不去重删除，保持全部冻结身份
- MXC：五个已有原创派生文件的内容字节。原手册、截图、完整厂商表、提取文本及私有存储身份不发布；不复制文件系统扩展属性
- 根状态、任务、综合、证据与本批允许清单/manifest

原R2T10 `freeze_manifest.json`身份属于原冻结包；本批不上传原包残缺投影，也不沿用其完整审计结论。独立portable的只读完整性入口是`python -B models/verify_portable.py --verify`。

## 可核对文件与历史语义

[本批允许清单](CONSOLIDATED_PUBLICATION_ALLOWLIST.txt)精确列出本次目标文件；[本批manifest](CONSOLIDATED_PUBLICATION_MANIFEST.json)按路径记录字节数、SHA256与Git blob SHA。manifest排除自身以避免循环，允许清单包含manifest。Git提交/tree提供最终发布身份，提交SHA不反向嵌入自身。

[第三轮证据索引](ROUND3_EVIDENCE_INDEX.json)绑定每题的冻结manifest/receipt。各原收据对ZIP的引用是本地历史档案身份；ZIP不在此次Git发布中。已发布的是可解读的完整载荷目录，并非ZIP下载承诺。

历史报告/receipt中的“未发布”“下一题未启动”或旧候选T10阻塞状态保留，不为发布改写冻结字节。当前状态以根STATE与本文件为准；旧`round2_prospective_publish_*`仅记录当时382项候选，不能取代当前清单。

## 验证与资格

本批做manifest路径/字节/大小、复制依赖、来源冻结保护、私有标识与秘密扫描，以及必要的隔离reader只读完整性/生命周期检查。Office仅传输文件内容字节并检查内部XML。不重新执行全套科学小测试、不重建reader、不跑heavy/device、不重新独审。历史测试数按题独立保留，不汇总成全库科学通过率。

正式模型链pending；设备0、heavy plan_only；点12 partial、点2 conditional non-strict；HTML浏览器布局unverified。第三轮有界研究完成不授予物理、统计覆盖、全局最优或生产资格。第四轮未启动。

## 排除与恢复

禁止上传第三方原文、ZIP、`__pycache__`/pyc、运行缓存、凭据/密钥/钱包、私有存储/账号/用户消息身份、原始设备数据或未列文件。原始冻结来源和私有来源记录完整保留在本地。上传仅使用精确允许清单；逐内容复用已有blob，对当前远端tree增补，不删除旧文件。

远端提交后应核对main指向、所有允许文件blob与既有未触碰路径，并查看该精确提交的CI。没有CI不宣称“CI通过”。发布阶段状态和最终远端核对结果由协调者另行报告，任何未通过或未执行项明确保留。
