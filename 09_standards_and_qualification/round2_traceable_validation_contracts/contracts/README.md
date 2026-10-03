# 证据合同的使用边界

本目录不是一个可自动签发的认证协议。evidence_checklist.csv是工程门槛清单；evidence_packet.schema.json是仅限synthetic_demo的严格结构schema；models/evidence_contract.py对其中选择的字段关系做语义检查。

Schema不检查hash真实性、证书真伪、数据是否真的独立、原始物理量、完整不确定度或客户授权。semantic_ready=true不意味着checklist全部关闭，也不意味着认可/资格/放行。真实实验记录需要新的受控schema及专业审核；不要删除synthetic约束来绕过用途限制。

已实现规则：用途晋升拒绝、显式ID/run组留出泄漏、最终留出被消费、共享校准而无相关性处理、替代值进入实测用途、lock缺口、原始记录/变换缺口、参数切换事件顺序、未知挡板伪零通量、缺少校准域、必需数值阶段未收敛、预算上限、预定规则。

未实现：完整图DAG/数据文件验真、隐式样品或校准依赖发现、任意协方差矩阵验证、拟合/参数分布、风险积分、同时覆盖、标准抽样、具体环境/损伤方法、授权签名和实际放行。

单位合同：R/T用1或明确percent；本例速率nm/s、几何长度nm、频率Hz；parameter_snapshot密度kg/m3、Z和tooling用无量纲小数。坐标和quantity_kind必需，单位相同不保证被测量相同。任意其他单位须显式转换后进入，不静默猜测。

controller_mode指产生此读数的控制器通道模式，不是整个工厂的全局模式。处于时间功率模式的同一QCM速率/厚度输出不能当新实测；独立外部光学仪器应建立自己的采集记录及来源，不继承该控制器模式。

reading_origin=derived_from_measurement允许经明确变换从实测原始数据得到的结果；它不表示没有测量模型。measured同样必须保留原始观测和校准链。process_estimate可保留替代值用于估计，但不能混入独立实测校准/验证。

zero_flux_verified在此只是用户所提供的证据声明。本包要求实际关闭位置证据和单独的零通量依据，绝不以命令或零功率自动推出零通量；即便这些字段齐全，也不验证零通量依据是否物理充分。
