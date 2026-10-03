# 08 · 有限验收、冻结与后续边界

## 8.1 可以验收的是本地研究交付物

验收对象为原创报告、明确主张、源账本、可运行reference validator及cases、独立reader、复制依赖、静态图与准确运行记录。通过本地测试表示这些声明在该实现与合成输入上按预期工作。它没有完成正式算法阶段签署，也不能替代实验室能力、真实计量或生产质量体系。

本轮仅安排一次配置为GPT-6 Luna的窄规则/单位独立检查（底层实际模型标识未另核）；实际发现与作者回应保存在reviews。DeepSeek执行、Seed Pro阶段审查、Sol完整算法审查均未完成。任何local_freeze或文件pass不得重写formal_stage_acceptance=pending。point12 partial与point2 conditional non-strict原样继承。

## 8.2 精确文件集与两层收据

reader_manifest精确列举可分发payload的相对路径、字节数与SHA256，验证missing/changed/extra。包含114项复制依赖，独立解压后复核其相同hash，不向上查找相邻源目录。manifest自身及最终收据为避免自引用不列自身hash；收据绑定manifest和zip的hash。控制文件排除集合写入reader.py，不能依靠glob忽略任意新增文件。

zip仅包括manifest列举的payload及manifest；不含目录外baseline、第三方原件、缓存、内部消息或工具标识。解压验证同时检查文件集和链接。另有篡改单字节、缺文件、增文件、依赖复制异常的负例检查；这些是字节完整性检查，不是可信时间戳、签章或供应链真实性。

## 8.3 外围不可变性与视觉状态

开工前采集研究库目录外2394个文件的byte/hash基线；冻结时比较既有文件和新增文件。只应出现本目录变化；并行任务若有变化需如实列出，不重置基线抹掉差异。不修改root plans、旧冻结、product或设备文件。

原创图包括量词/状态流、主张对应的4盒细化域、同一0.012阈值下点模型与合成读数差别、有限请求路由。PNG需实际像素查看，记录不等同于HTML已渲染。HTML布局保持unverified，不反复尝试已受限的socket/headless浏览器。

## 8.4 T10仅有界交接

若后续研究离子源，先将其能量/角度/电流/中和/时序证据映射到已有response/状态合同及guard；未知项仍unknown。不得把本轮光学proxy IN升级为离子作用或沉积净厚度已验证，也不得默认用户有某设备。T10建议只研究有限接口与证据缺口，不自动运行设备、开新谱/状态或触发大型模型。

此目录以精确收据和local_freeze结束。没有push、upload、deploy、生产发布或下一题启动。
