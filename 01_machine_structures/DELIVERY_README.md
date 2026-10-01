# 行星盘结构首轮研究包 v0.2

先读README或汇总技术手册。含6章、两张原创图、24条来源摘要、运动学复算与T02移交建议。原始第三方PDF与下载缓存不在本包中。

用户实机尚未校准；本轮资料基线建议进入下一专题。不要据此直接更改生产齿轮、离子参数或修正板。

复算：python reviews/planetary_kinematics_check.py
读者包检查：python verification/check_initial_release.py --reader
后者需要jsonschema进行来源schema检查；没有随包提供的原文PDF检查会明确跳过，不影响原创文件检查。
