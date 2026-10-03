# 第二轮候选发布计划：没有上传

2026-10-02 UTC。此处只是后续批次的精确候选清单，不批准发布、不推送GitHub/Library、不重封T10、不创建新凭据。

## 已有与待发分开

此前四增补为T02v0.3、T03R2、T04R2、T05R2，协调者提供的已发布提交为31744525b4cdde04fad31aaf58e6148f7819ce62。本次未访问远端复验。T06–T10已本地冻结，仍未发布；首轮与已发二轮内容不重复纳入本次增量候选。

[精确逐文件allowlist](round2_prospective_publish_allowlist.txt)共382项：T06 63项、T07 56项、T08 72项、T09 87项、T10 83项、MXC_DERIVED 5项、ROOT_PLANNING 16项。[逐文件字节/SHA256清单](round2_prospective_publish_manifest.json)覆盖除自身之外的所有候选，并记录原始freeze manifest与receipt身份。原收据原字节保留，不以此次文件选择重写其历史含义。

## T10完整公开包：阻塞

唯一识别到含私有Library身份的冻结载荷：

- 10_ion_sources/round2_observable_material_response/dependencies/manual_studies/2026-10-02_morningtech_mxc/evidence/provenance.json
- 大小833字节，SHA256 2bf7342e3b525894e684b4f4dd621fedc28e766f42256ba8190c8bdbac826803
- 依赖由T10的dependencies/provenance.json、freeze_manifest.json及原T10_round2_observable_material_response_reader.zip明确引用/包含

候选清单排除这个文件和整个原ZIP。仍原样保存并候选列入freeze_manifest.json与verification/freeze_receipt.json，但这只保留历史身份，**不能使缺一项的公开投影成为原82项载荷的完整可复现包**。T10候选投影共有81项原payload加manifest、receipt，共83项；原ZIP的83 entries则是82项payload加manifest，两者不是同一范围。

静态检查还发现audit_package.py --verify依赖原ZIP、外置freeze receipt、21个上游兄弟文件和全库outside snapshot。ZIP单独解压缺外置收据/上下文；删掉上述私有依赖会产生路径/哈希不一致，原ZIP比对还可能遇到缺文件异常。没有在本次重跑此入口，也不把历史整库审计通过改称独立reader通过。HTML与本地图形可读投影不等于完整审计。

处置边界：原freeze、依赖副本和receipt不可变；未来由独立派生发布包去除私有身份、明确独立核查范围并生成新的清单/收据。此次不重封、不审批、不执行修复。完整T10公开reader状态保持blocked，候选集合不能直接整批当完成包发布。

## MXC与先前配方

- MXC候选仅5个原创派生文件：README、中文分析源、11页DOCX、page_evidence.csv与validation.json。原104页厂商手册、截图、完整表格、提取文本不在候选中
- manual_studies下的evidence/provenance.json和delivery_receipt.json含私有来源/输出身份，保留本地。现有README对本地provenance的文字指引不是公开副本存在的承诺
- DOCX正文/内部XML检查未见Library标识，但本地文件具有Library扩展属性。仅发布文件内容字节，禁止携带user.library-file-id、user.library-file-version或任何其他文件系统扩展属性
- 旧37配方原JSON/XLSX/ZIP不重复发布/导入；本轮只新增交叉引用概要。恢复区原Library身份与恢复审计留在本地，00_project/LOCAL_ONLY_RECOVERY_PROVENANCE.json明确不入候选
- T10包含用户原始研究要求的既有只读依赖副本，这是用户来源的研究基线，不是厂商手册或第三方原文；本地原件亦不修改

## 排除规则

不使用目录通配上传。精确allowlist以外一律排除，尤其：

1. 所有sources/originals、第三方原文/完整提取、厂商手册与截图
2. 所有ZIP、cache、__pycache__、pyc、临时下载/渲染/凭据/会话、重复未列日志
3. 原/新私有Library、backing file、用户会话标识；本地来源文件与恢复搜索结果
4. 未运行的大输出、设备日志/用户原始数据及未授权产品文件
5. 新文件系统xattrs和任意未列附件

原冻报告/receipt/失败证据若在明确载荷或特列收据内，按原字节保留；不为好看改写失败、不删减后沿用完整性结论。SHA256只表明字节身份，不认证来源真伪、算法正确或生产资格。

## 本轮核对与停止

只做哈希核对、根规划一致性和候选文本/Office内部XML的私有标识扫描；不运行测试或reader，也不进行网络发布。现有1535文件基线中的冻结专题、历史收据、手册派生文件均保持原字节。最终差异/完整性记录见[本地收口核对](round2_consolidation_integrity.json)。
