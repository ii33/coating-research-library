# 89层固定候选敏感性计算基准数据 · block 1024

日期：2026-10-23。此目录只发布冻结科学数据、规范化名义审计和执行协议，不含软件源码或脚本。数据准备完成不表示性能基准已执行；新v2软件提交仍为null，尚未正式发布。公开基线和未来软件SHA状态见scientific-manifest.json。

## 下载与完整性

- [完整数据ZIP](sensitivity-89-fixed-benchmark-block1024-data.zip)：140966 bytes。
- ZIP SHA256：e8193f51a738a7af5f0e22c294de68d8e098f9609016bcdad9c856e9083b4bb7。
- ZIP内7份JSON与此目录对应文件原始字节一致，未重新序列化。科学数据身份、材料/网格/请求digest只用于复算与比较，不是源码hash库存。

## 固定的科学问题

- 两个固定89层候选：[baseline89.json](baseline89.json)、[candidate89.json](candidate89.json)。本基准不执行优化，不重新选解。
- 四窗原1nm网格，39–51°每0.5°，25角，共184600个光学条件；不沿用历史稀疏训练网格。
- 32个固定的独立有界均匀厚度误差场景，seed=20261023，幅值±0.5%，覆盖全部89层；实际系数在[scenarios32-seed20261023.json](scenarios32-seed20261023.json)。这是假设误差，不是设备校准或真实良率。
- [frozen-A.json](frozen-A.json)：计算6列厚度Jacobian；[frozen-B.json](frozen-B.json)：计算89列。两者的原优化变量和边界均保持同一6层，B的89计算列不等于扩大优化变量。
- A/B均block_size=1024，相同两候选、材料、场景、原规格和比较规则。请求19工作进程不代表已实际使用19个，也不代表任何加速比。

## 原运算符规范化

原物理要求保留HR的R≥0.99与IR的严格R<0.03。基准将两IR上界写为0.03，并显式strict_upper_bound_objective_indices=[2,3]，不在已nextafter下调的数字上再施加严格上界，避免重复偏移。没有增加margin，历史源文件不改写。

[normalized-nominal-audit.json](normalized-nominal-audit.json)已按规范化运算符完成两个候选的原网格名义前向复核：均通过。该审计没有计算导数列或32敏感性场景，没有运行优化器或性能基准，也不是连续域/制造证书。其耗时不是未来v2串并性能结果。

## 计划执行与尚未取得的结果

[scientific-manifest.json](scientific-manifest.json)冻结串行→进程、进程→串行的顺序，每个session均区分冷/热，比较原点R/T、Jacobian及严格布尔结果；资源预算和比较容差明确记录。内存/磁盘数字是估计或准入配置，不是实测RSS、可用主机容量或已达到的吞吐率。

当前optimizer_executed=false，performance_benchmark=false，敏感性场景实测数为0。只有在未来准确v2软件提交、目标主机结果、完整清理与科学一致性证据齐备后，才能另行报告速度/资源实测。不能用本数据包替代这些结果，也不能据其作制造良率或89层稳健改进结论。

前轮[名义保护实效报告](../nominal-preserving-effects-20261023.md)及其原始数据保持原样。本次追加仅为固定计算负载的可核查交接，不是重新运行前轮优化或修改其正负结果。
