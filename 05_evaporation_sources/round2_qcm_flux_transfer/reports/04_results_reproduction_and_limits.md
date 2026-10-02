# 04 轻量结果、复算与未运行项

## 1 必要的小测

verification/diagnostics.json冻结了完整合成计算。已知真值Q=2e−6 kg/s、n=2.4、a=0.25、ηQ=0.92，经原始频率面质量链恢复Q的相对误差约1e−12（双精度与求根误差级，不是物理精度）。两个保留工件位置入射质量通量为3.00626e−6与1.61838e−6 kg/m²/s，对应Al核通量6.70982e19与3.61214e19 atoms/m²/s。密度/tooling均未进入计算。

验证分开为：解析极限/单位与守恒、严格合同QA、声明合成真值恢复、故意违反假设的反例。60项轻量测试通过，其中7项来自一次独立窄量纲核查。模型指定的完整Seed/Sol审查链没有运行，不能据此宣称算法已获完整独审签署。

## 2 已实现的可证伪反例

- 单轴上QCM：Q=2e−6,n=1与Q=1e−6,n=3信号完全相同，45°处入射通量比为0.5。证明总率与角谱未由一个读数分离
- 捕集率混淆：6监视点对[logQ,n,a,logη]仍秩3；真正独立源量测才能在示例中提升至4
- 漂移：真实净率1e−8 kg/m²/s、未校正漂移+2 Hz/s，误推净率约−2.30824e−7；正确移除外部漂移后恢复真值。负率不取绝对值变蒸发
- 遮挡：传感器V=0.2却按V=1解释会把总源率估成20%；V=0直接拒绝反演。多点稳健损失可减轻孤立坏点，但不能识别所有共同遮挡
- 离群：一个读数乘1.5，soft_l1给Q≈1.98629e−6,n≈2.45992,a≈0.24304；普通线性损失给Q≈1.83491e−6,n≈3.44677,a≈0.12947。不是宣称稳健方法对任何污染都有保证
- 有限负载：z=1的精确周期关系、f→f0小负载极限、非零初始加载下的斜率都独立测试；跨数学分支、非基频、非刚性输入拒绝
- Al₂团簇与O₂反应：粒子数和核数分别累加，质量守恒；外部氧增重不被藏入ηAl>1

## 3 重任务完整程序与默认计划

models/validation_driver.py默认mode=plan，仅计算资源计划。已写出连续多窗口、累计晶体负载、同一时窗多监视点、原始频率噪声/漂移生成、mass→rate反演、有界拟合、空间保留位置及时间积分、已知真值偏差、参数覆盖诊断和重复分位统计。它不依赖实机或外部API。

计划为1000重复×120窗口×4情景=480000次拟合，12监视点×11时点约63360000个频率样本。按明确未实测的每窗口0.02…2 CPU秒预算，单核约2.67…266.67小时；64 MB内存底额加算法数据，检查点磁盘约960 MB。不是设备实测，也没有预留或购买资源。不同机器、BLAS、失败重试和文件系统可显著改变实际耗时。

每个case/replicate单独原子写检查点，RNG种子由base seed、replicate、case确定。resume只接受完成标记且配置及qcm_flux/driver源代码联合哈希相同的文件；配置变更明确报错，禁止静默混用。最终输出按时间窗口的[Q,n,a]经验分位和保留点累计质量误差。轻量模式只有1重复、3窗口、8监视点；其分位相同是样本数为1的必然结果，不能称95%覆盖。

本轮只运行light，四情景12个窗口拟合完成。名义保留通量最大相对误差约0.0160%，相关漂移情景约0.5703%；这些值来自人为0.05Hz噪声、0.08Hz/s漂移残差模型。遮挡/孤立离群情景的稳健拟合没有放大成大面积失真，但这只是当前布点与污染比例的合成反例，不是实机稳定性证书。

heavy需要同时--mode heavy、--execute、--acknowledge-synthetic-only和显式输出目录。当前heavy_validation=not_run、device_validation=not_run、actual_calibration=not_run；这三个状态相互独立。

## 4 复现方法

Python 3.10+；numpy、scipy、jsonschema；只有重建图需matplotlib。已装环境版本记录在verification/environment.json。无需安装软件、联网或访问原论文。

    python models/contract.py examples/synthetic_al.json
    python models/contract.py examples/actual_unknown.json
    python -m unittest discover -s tests -v
    python models/diagnostics.py
    python models/data_qa.py
    python models/validation_driver.py
    python models/validation_driver.py --mode light --output /tmp/t05_light_new
    python models/reader.py --directory .

运行写文件的重建脚本会更新verification载荷，冻结后应先复制本目录再做实验；reader只读本目录，在独立临时副本复算，不触碰冻结输出。reader拒绝额外/缺失/修改载荷、路径穿越与符号链接，检查所有载荷字节数和SHA256。ZIP不创建；index.html直接阅读本包原创报告和原始代码，来源全文使用官方链接，未取得/未授权再分发的原文不藏在reader中。

## 5 状态与边界

状态implementation_ready_validation_pending，本地冻结。未更改首轮/前轮、root STATE或产品，未push/上传。本轮没有用户设备采样、真实沉积操作、外部计算API调用或付费。实际工具因子、晶体/工件捕集率、角谱参数、几何与膜密度全部待测；无法据本包直接生成生产配方、均匀性验收或光谱预测。

来源资料有访问等级：两本官方手册核读、Sauerbrey仅出版摘要、Lu–Lewis全文/出版页未可读、QCM-D原研究仅索引可读内容，标准数据官方页面已读。证据缺口明确保留，不以二手摘要冒充全文。
