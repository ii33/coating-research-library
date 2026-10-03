# T08 第三轮：预算化候选集合

先打开reader.html。研究边界：同一六层合成膜系、M0/M1两个冻结通道、二维(z, 最外层倍率)。不涉及37条生产配方、实测标定或设备运行。

核心结果：双通道二维255节点后仍有32个UNKNOWN；最外层×1.1切片在13节点/7个OUT叶上完成排除。一次有限搜索未找到与(1,1)代理可行见证同时存在。优化目标下界必须包含UNKNOWN，最优性剪枝不改观测分类。

数值核心与reader只需Python标准库。命令详见reports/05_driver_and_resource_accounting.md。默认driver plan_only；完整计划未跑。verification/tiny_final是最终基线，原始尝试保留作历史。

离线解压后python models/reader.py --directory .即可检查本包；无需源项目siblings或全项目目录。30项窄测试含13节点排除和点见证复算。PNG像素已检查；HTML布局unverified。

状态：local_freeze；point12 partial，point2 conditional non-strict；正式DeepSeek/Seed/Sol链pending。无上传、push或自动启动T09。
