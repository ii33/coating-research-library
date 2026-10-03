# T05 第三轮 蒸发源与材料留存可辨识性

本地有界研究包 v0.1.0。核心结论：同一个轴上QCM和全部平行见证片可以同时对应两套不同源角谱/留存；改变接收法向、观测源方向并补足独立尺度证据，才可能在受限模型内分开它们。所有数值为synthetic，实际材料与设备参数仍unknown。

## 阅读顺序

1. [增量、单位与双时钟](reports/01_scope_and_physical_contract.md)
2. [原始设备与论文实例](reports/02_device_evidence_and_process_states.md)
3. [反例与有条件测量设计](reports/03_identifiability_and_diagnostic_design.md)
4. [完整T04桥接及算法](reports/04_frozen_response_bridge_and_algorithm.md)
5. [复算、证据与限制](reports/05_reproduction_and_limits.md)
6. [T06有界候选交接](T06_ROUND3_HANDOFF.md)

[reader.html](reader.html)是原创报告、图与来源摘要的本地阅读入口。reader ZIP自带33个hash绑定依赖，脱离兄弟目录可校验、复跑小测和确定性示例。不包含第三方原文或账户标识；不上传或发布。

## 已有可复算结果

- n=3、a=0与n=1、a=1、Q加倍的精确全局等效反例；新方向的合成响应相差2倍
- 7参数模型：单QCM秩1，多方向无尺度锚秩5，独立Q和ρ锚下局部秩7；每QCM自由捕集时10参数仅秩9
- 源总率、每立体角强度、有限源质量权重和接收投影分离；Lambert桥接只除π一次
- 保留整个T04响应及上游forward、依赖哈希、未知/负净/零分母guard；非Lambert明确不桥接
- 42项小测通过，最多一次独立窄量纲核查13项通过；3张PNG已逐张看像素

## 最小本地复算

现有Python环境已有numpy/scipy；不需要联网或安装。在解压后的独立目录执行：

    PYTHONDONTWRITEBYTECODE=1 python verification/reader_check.py
    PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
    PYTHONDONTWRITEBYTECODE=1 python models/diagnostics.py --output /tmp/t05r3-results.json
    PYTHONDONTWRITEBYTECODE=1 python models/validation_driver.py

最后一个命令默认plan_only，没有执行500次待运行计划。检查checkpoint实现不代表已跑heavy。正式DeepSeek/Seed/Sol链pending；point12仍partial，point2仍条件非严格。HTML资源完整性已检查，浏览器布局因已知socket权限边界未验证，本轮不尝试升级/绕过。没有实机标定、连续源认证或生产放行。
