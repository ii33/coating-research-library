# 稳定光学核、能量与测量合同

## 1. 核的物理约定

冻结T07 `optics_kernel.py`不作数值改写。时间exp(-i omega t)，被动复折射率N=n+ik、n>0、k>=0，长度统一µm；beta=n_inc sin(theta)，kz=sqrt(N²−beta²)取向前衰减支。s偏振导纳q=kz，p偏振q=N²/kz，幅度为切向E。接口S矩阵以Redheffer星积级联，传播因子exp(i2π kz d/lambda)不引入增长指数。R=|r|²，T=Re(q_out)/Re(q_in)|t|²，A=1−R−T。损耗不裁零；约10^-16负数可视作浮点闭合残差，超过核容差报错。

条件包括平面、局域、各向同性、非磁、非增益层，非吸收入射介质；不含退偏、双折射、磁光、非局域、图案化结构。精确临界/掠入射退化和超出89.9°的AOI拒绝。金属强衰减时T下溢为0不代表经认证无限OD，也不提供实际仪器杂散光下限。稳定计算不等于材料或测量正确。[PO-S04]

## 2. 基片背面与体吸收

两种可执行模式：

- semi_infinite：T只是进入基片的通量，不是穿过真实基片后的外部透过率；A只含有限光学层。bulk alpha/背面未参与
- incoherent_finite_all_orders：前膜系统、反向膜系统、裸背面分别计算；基片相位随机化，所有横向走离往返光都被收集。厚度L、内部角theta_s、独立bulk alpha给单程功率P=exp(-alpha L/cos theta_s)

令前向(R_f,T_f,A_f)、反向(R_b,T_b,A_b)、背面(R_r,T_r)在实折射率端口归一。D=1−R_b R_r P²：

T_total=T_f T_r P/D
R_total=R_f+T_f T_b R_r P²/D
A_film=A_f+T_f R_r P² A_b/D
A_bulk=T_f(1−P)(1+R_r P)/D

因背面不吸收，有R_total+T_total+A_film+A_bulk=1。内部折射角随波长变化，所以反向前膜逐波长计算，不能使用单一外部角。alpha按m^-1、L按m；不会把mm/µm直接相乘。

这是“透明实n界面+独立Beer体损耗”的radiative-transfer近似，不是任意吸收介质界面的严格混合相干模型。bulk k较大、TIR/导波、散射反馈、相干基片条纹或部分横向收集时需别的模型；本模式不得假称适用。倾斜/wedge基片会改变返回光位置和相位，有限光斑/孔径若漏掉回光不能使用all_orders结果。实际背面镀膜尚不支持。

alpha=4πk/lambda仅是同一均匀介质强度衰减的单位关系。`alpha_to_k`要求证据scope与target scope相同；把块材吸收系数叫“薄膜k”明确阻断。bulk alpha不能补齐薄膜氧化、孔隙或缺陷损耗。

## 3. specular、total和探测到的R/T

模型先算零散射平面栈R,T,A，再用显式fraction_of_R/T作合成能量再分配：S_R=f_R R，S_T=f_T T；R_spec=R−S_R，T_spec=T−S_T。total包含对应半球散射，R_total、T_total不变。探测值R_det=R_spec+eta_R S_R，T_det=T_spec+eta_T S_T，其中eta是指定检测几何收集分数。

因此1−R_spec−T_spec=A_abs+S_R+S_T，不能把specular缺口全称吸收。只有匹配波段、校准、整个出射半球或适当全收集合同下，1−R_total−T_total才可作为A估计。[PO-S05/06] 积分球端口损失、样品替代、镜面排除挡板和探测器响应需要校准；某一NIST装置的8°条件不是本机普适标准。

本散射操作只是可证伪“漏项导致假吸收”的小模型：未计算粗糙界面场反馈、BRDF/BTDF、偏振转化、背散射重新入膜或多次散射吸收。不能用RMS粗糙度单值直接代替f_R/T，更不能把拟合出的f当实测BRDF。真实散射unknown时阻断；显式设0是场景假设，不是测得零。

## 4. 光谱/角度响应

measurement记录每个中心波长、角度、s/p或unpolarized，带宽离散响应节点offset_um/weight及角分布offset_deg/weight，节点权重均有限非负且和为1。程序在每个真实节点求值后按功率平均，含unpolarized=(s+p)/2，不平均复振幅。任何节点超出材料波段/角度域就阻断，不能只验中心波长。

本Al例三个谱节点±1 nm、0，权重1/6、2/3、1/6，角分布为delta45°；这是完全声明的合成离散仪器核，不声称精确Gaussian或实际狭缝带宽。实际仪器应提供线展宽函数或经收敛验证的积分节点；FWHM不足以唯一确定尾部。角分辨、NA、入射面、方位、光斑、波前、探测孔径和样品背面状态都影响对照。同样R/T曲线若合同不同，不能直接作为“复现实测”。
