# ITO 透明导电膜 从蒸镀工艺到仿真模型

**阶段一有界研究版 · 2026-10-03 · 未经本机台实测校准**

结论：先把“源与输运 → 膜材料状态 → 电学/光学观测”拆成可验证的模块。ITO蒸镀能够形成透明导电膜，但源料配比不能代替膜组成，氧流/温度不能唯一决定载流子与迁移率。最短可靠路径是以实际膜厚、方阻、Hall与T/R/椭偏数据闭合电光模型，再标定工艺到膜状态。

## 阅读顺序

1. [蒸镀工艺与成套证据窗口](process/report.md)：电子束、阻蒸、活化反应与离子辅助分开；记录来源访问层级、设备与测量条件
2. [源通量与材料状态接口](integration/01_flux_material_state.md)：配比口径、气相物种、源耗尽、几何、氧摄入、净库存及密度
3. [电学与光学模型](electro_optics/report.md)：分层方阻、载流子/迁移率、Drude–Lorentz、复折射率及相干/非相干光学
4. [校准实验与决策树](integration/02_calibration_validation.md)：最少测量、DOE、辨识、留批验证及误差传播
5. [工程基础如何约束ITO仿真](integration/03_engineering_foundations.md)：郭倩丞官方研究方向与成都国泰代表技术文章的适用边界
6. [证据与缺口总览](sources/README.md)：全文、摘要、官方建议、推导与合成结果分开

离线阅读器 `ITO研究报告.html` 在整包时由上述原创章节生成，不含第三方全文、网络脚本或在线字体。HTML已做结构与本地链接检查；云浏览器不允许打开file协议，整页浏览器排版尚未视觉核验，原创光谱图已检查像素。报告副本用于阅读；分章源文件、代码和证据账本是可继续维护的研究文件。

## 模型层次

- 校准经验路线：同设备、同材料域内的通量响应面 + 实测或拟合σ与有限域ε(λ)
- 有界机理路线：物种/元素守恒 + 明示氧化/损失/微结构闭合 + Drude–Lorentz与光学前向模型
- 直接实测输入路线：从净库存/厚度与电光实测进入下游，独立检验计算链

三者并列保留。没有“新模型替代旧模型”，也没有声称从电子枪功率直接算出唯一ITO性能。

## 实际云文件与复算

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s integration -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python electro_optics/test_model.py
PYTHONDONTWRITEBYTECODE=1 python integration/reference_state.py
PYTHONDONTWRITEBYTECODE=1 python electro_optics/demo.py
PYTHONDONTWRITEBYTECODE=1 python integration/chain_example.py
python verify_manifest.py
```

只用Python标准库做上述参考复算，不需网络、原文PDF、上游项目安装或真实设备。作者排版脚本build_reader.py另需pandoc，绘图脚本integration/plot_synthetic.py另需matplotlib；已附成品HTML/PNG，阅读和核心验证不依赖它们。测试只验证方程实现、边界与合成反例，不证明真实工艺可用。`material_state_contract.json`是拟议离线合同，未对接产品API。代码与输入单位均显式列出；缺少实测的真实模板保留null与blocked状态。

## 冻结边界

所有新增文件位于 `11_transparent_conductive_films/ito`。T01–T10及既有第二轮保持不变；其partial/not_run状态不升级。本研究不修改产品运行时，不操作机台，不执行重型计算，不上传或推送GitHub。原始论文如合法本地留存，位于sources/originals类目录，单独登记权益与哈希；不会进入面向用户的原创研究ZIP。

## 下一阶段真正缺什么

- 应用定义：基片/下层、工作波段及透过口径、Rs目标、允许热预算、散射/应力/附着约束
- 机台定义：电子枪或阻蒸源、氧控/残气、基片实际温度、几何/QCM、IAD能力
- 本批样片数据：物理厚度、成分、Rs、Hall、T/R及基片基线
- 关键历史低温PIAD全文与源化学细节，按证据缺口清单补齐；不把全部缺文作为现阶段阻断

本版范围是可追溯资料研究、方程/接口设计与小规模离线验证；未完成设备标定、材料模型辨识、批间可靠性和生产资格验证。
