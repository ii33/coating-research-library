# T09第三轮 · 未决证据的有限验收

本包将T08的98 OUT/32 UNKNOWN、7叶OUT切片和(1,1)区间见证映射为27个限定主张；明确“条件接受、拒绝该主张、保留UNKNOWN、证据阻断”。

最关键结果：全部支持解位于v∈[0.95,1.1]可条件支持，更紧v≥0.99尚有4个相关盒；最优J界仍[0,约1]。同一0.012阈值下，名义M0模型响应通过，含±0.001硬误差的合成读数仍未知。

- 打开reader.html离线阅读8章及原创图
- python models/reader.py：精确payload/复制依赖/链接验证，无数值执行
- python models/driver.py：默认plan_only
- python models/driver.py --mode tiny --output verification/new_replay：显式tiny预算重放，仅在新工作副本中执行
- cases/claims.json与verification/tiny_final/results.json：主张与预期/实际结果
- sources/source_registry.json：主来源、访问层级和限制

所有内容为研发资料。无真实测量、客户规格、生产验收、真实来源见证或正式模型链完成。point12 partial、point2 conditional non-strict保持。HTML布局unverified；PNG另有实际像素检查。

本地冻结后停止，不上传、push或启动T10。
