# 4 · 全部优先材料与基片的条件化矩阵

12种膜材与4种基片逐项覆盖原始优先清单。每条均保留Ar、O2、已证实范围、未知和试验门槛。这里的风险项包含机理假说，不表示均在该材料本机已经发生。实机生产电压/电流全部为null；没有通用最优配方。

强证据、作者解释、跨方法旁证、工程假说必须分开：P原始研究也可能只有摘要可读；M原厂说明不是独立实验；同化学式不同源型/沉积路线不得拼接。精确访问等级见来源表（上游背景引用：00_source_index.md；本派生包未附，非本地导航或运行依赖）及独立核查（上游背景引用：../reviews/independent_source_check.md；本派生包未附，非本地导航或运行依赖）。

氧化物不意味着氧越多越好；元素金属/Ge不意味着惰性轰击没有化学后果；氟化物不意味着氧在所有波段必然增损。所有材料至少同看光学、组成、应力和界面，不以单个n或附着指标放行。更细原料、基片等级和SDS沿用T04冻结卡。

## MAT-01 Ta2O5 · film

身份：纯Ta2O5目标；源料批次/氧比需核；T04材料卡（上游背景引用：../../04_coating_and_substrate_materials/cards/01_Ta2O5_film.md；本派生包未附，非本地导航或运行依赖）

- 证据条件：Kaufman + e-beam, fused silica, room temperature; study-specific beam/flow/rate；来源：IS-13, IS-11
- 已支持范围：原研究确有束参数–光学–压应力耦合，不把其单点最优移植
- Ar条件：Ar仅有动量作用仍可能改变氧含量；本轮不声称确定亏氧阈值
- O2条件：O2可提供反应氧；高辅助不等于一定更好
- 副作用/失败候选：氧亏/污染、压应力、再溅射、热负载
- 尚未知：目标波段n/k、体组成、密度、应力随厚度/时间的本机联合图
- 最小验证：R/T+SE+吸收；O/Ta；XRR；曲率；温度；二维厚度
- 进入下一步的门槛：先以吸收/应力预算作硬约束，再比较n和稳定性

## MAT-02 ZnS · film

身份：ZnS源料与ZnS块材分开；T04材料卡（上游背景引用：../../04_coating_and_substrate_materials/cards/02_ZnS_film.md；本派生包未附，非本地导航或运行依赖）

- 证据条件：IAD source/gas unverified in primary abstract; Zn(O,S) evidence is RF reactive sputtering；来源：IS-20, IS-21, IS-28
- 已支持范围：ZnS应力、损耗、结晶性与沉积温度耦合；源/气体未充分核
- Ar条件：候选惰性辅助；需检S/Zn、Ar俘获和粗糙，不能说必然优先失硫
- O2条件：氧是化学变量，可能改变硫氧组成；跨方法证据不能给IAD氧阈值
- 副作用/失败候选：成分偏移、吸收/散射、应力、晶相和再溅射
- 尚未知：Kaufman Ar/O2同条件的化学计量和IR吸收数据
- 最小验证：Zn/S/O；FTIR；XRD；AFM/散射；应力；附着；净速率
- 进入下一步的门槛：先单层基线与低剂量对照，缺目标IR吸收不得用可见透过放行

## MAT-03 TiO2 · film

身份：源料TiO2/Ti3O5等与成膜相态分开；T04材料卡（上游背景引用：../../04_coating_and_substrate_materials/cards/03_TiO2_film.md；本派生包未附，非本地导航或运行依赖）

- 证据条件：oxygen IAD; primary legacy studies with temperature/energy groups; CC103 comparison separate；来源：IS-11, IS-12, IS-16
- 已支持范围：低/高能轰击可呈相反化学计量趋势，污染与温度不能省略
- Ar条件：必须核氧亏与缺陷，不把惰性气体理解为材料无反应
- O2条件：供氧和轰击能共同改变组成；高能可能损害光学
- 副作用/失败候选：n上升同时k/散射/应力变坏；W等污染
- 尚未知：本机非晶/晶相、O/Ti、吸收检测限和膜厚匹配
- 最小验证：SE(n,k,d)；R/T/散射；O/Ti；XRD；XRR；曲率
- 进入下一步的门槛：不以最大n作唯一目标；同厚度、同温度比较

## MAT-04 YbF3 · film

身份：镱氟化物；不得写成YF3；T04材料卡（上游背景引用：../../04_coating_and_substrate_materials/cards/04_YbF3_film.md；本派生包未附，非本地导航或运行依赖）

- 证据条件：End-Hall MarkII, room temperature; not Kaufman evidence；来源：IS-19
- 已支持范围：End-Hall研究有耐久/光学条件证据；Kaufman精确窗口仍未知
- Ar条件：可能致密但F损失、俘获气体和应力须实测
- O2条件：氧化/氧氟化风险作为待验证机制；本轮无特定相确证
- 副作用/失败候选：F亏、氧/水污染、应力、IR损耗
- 尚未知：Kaufman下F/Yb、O、相态与波段损耗联合数据
- 最小验证：F/Yb/O；XRR；FTIR；应力；附着/湿热前后
- 进入下一步的门槛：不将Xe优于Ar的End-Hall结论升级到Kaufman

## MAT-05 SiO2 · film

身份：SiO/SiO2源料；膜OH/密度单独记录；T04材料卡（上游背景引用：../../04_coating_and_substrate_materials/cards/05_SiO2_film.md；本派生包未附，非本地导航或运行依赖）

- 证据条件：oxygen IAD; 1984/1985 source-specific temperature/energy conditions；来源：IS-11, IS-12
- 已支持范围：辅助可改变化学计量、含氢和污染；不能由n独断孔隙
- Ar条件：惰性致密化候选，Si/O及缺陷仍需核
- O2条件：氧化SiO蒸气与致密化是两条机制，O2不能代替能流计量
- 副作用/失败候选：压应力、OH/水、充电、源污染、再溅射
- 尚未知：本机净密度、湿度漂移、3µm附近吸收、真实温升
- 最小验证：FTIR；干/湿/再真空光谱；XRR；曲率；O/Si；电位
- 进入下一步的门槛：高密度与低OH/低应力共同约束

## MAT-06 MgF2 · film

身份：MgF2相态、纯度和基片温度要绑定；T04材料卡（上游背景引用：../../04_coating_and_substrate_materials/cards/06_MgF2_film.md；本派生包未附，非本地导航或运行依赖）

- 证据条件：mixed evidence: source-unverified Ar; Kaufman O2 2019 index; End-Hall Dumas separate；来源：IS-17, IS-18, IS-26, IS-29
- 已支持范围：Ar低能研究有失氟/UV边变化；氧辅助的VUV与vis/IR结果不可混为同波段
- Ar条件：可能改善力学同时失氟；无额外可见损耗不证明VUV/IR均合格
- O2条件：MgO解释在1987为作者推断；2019报告光学与附着权衡
- 副作用/失败候选：F亏、氧/水摄入、应力、附着劣化、波段依赖损耗
- 尚未知：本机粒种/通量与F/Mg、O、附着的剂量曲线
- 最小验证：F/Mg/O；VUV仅如适用；FTIR；XRR；曲率；附着
- 进入下一步的门槛：先定义使用波段和底层界面；不自动把O2列禁用或优选

## MAT-07 Al2O3 · film

身份：非晶薄膜不是蓝宝石；T04材料卡（上游背景引用：../../04_coating_and_substrate_materials/cards/07_Al2O3_film.md；本派生包未附，非本地导航或运行依赖）

- 证据条件：oxygen/argon original IAD studies; source model unverified; CC103 separate；来源：IS-14, IS-15, IS-16
- 已支持范围：n/k与辅助、温度共同变化；高电流并非持续提高n
- Ar条件：Ar辅助物性敏感；不能把高n当准确密度
- O2条件：氧供给可能改善组成，但过量/强轰击需测缺陷及应力
- 副作用/失败候选：应力、缺陷、吸收、再溅射、相态变化
- 尚未知：同机氧/氩对照，UV/IR k检测限，真实薄膜密度
- 最小验证：SE；吸收；Al/O；XRR；XRD；应力；附着
- 进入下一步的门槛：不搬1000eV/300°C实验组为本机推荐

## MAT-08 H4 · film

身份：厂商/货号/COA明确才可用；非固定化学式；T04材料卡（上游背景引用：../../04_coating_and_substrate_materials/cards/08_H4_film.md；本派生包未附，非本地导航或运行依赖）

- 证据条件：Patinal H4/H4HD, RF IAD manufacturer example; not Kaufman；来源：IS-24
- 已支持范围：T04有牌号条件化n/k和过强辅助风险；没有Kaufman通用配方
- Ar条件：对未核组成不预测响应；先核La/Ti/O或实际牌号元素
- O2条件：依具体商品反应氧需求验证，不能从H4缩写推流量
- 副作用/失败候选：吸收、应力变化、化学计量和源料历史
- 尚未知：用户实际牌号、膜M/ν/ρ、全谱k和应力
- 最小验证：COA；组成；SE/FTIR；密度；曲率；温度
- 进入下一步的门槛：组成未知时归一化摩尔质量保持null，允许先做质量基准比较

## MAT-09 Ge · film

身份：元素Ge膜；与GeO2、晶体基片分开；T04材料卡（上游背景引用：../../04_coating_and_substrate_materials/cards/09_Ge_film.md；本派生包未附，非本地导航或运行依赖）

- 证据条件：Ar-assisted AR stack at 220°C; source unspecified in abstract; reactive oxide route separate；来源：IS-27, IS-23
- 已支持范围：Ge层Ar辅助的特定AR系统有耐久收益；不构成本机剂量窗口
- Ar条件：候选致密化；Ar俘获、缺陷、应力和净侵蚀仍需检
- O2条件：目标元素Ge时须防氧化；GeO2旁证不等于低能氧化率已知
- 副作用/失败候选：相态/孔隙、O污染、俘获Ar、温敏吸收、再溅射
- 尚未知：Kaufman粒种/角度下Ge结构与目标IR n/k
- 最小验证：FTIR/SE；Ge/O/Ar；XRD/拉曼；应力；净厚度
- 进入下一步的门槛：分离真空内/出腔后氧化；不能用高n保证低k

## MAT-10 Cu · film

身份：Cu反射/导电用途与氧化铜用途区分；T04材料卡（上游背景引用：../../04_coating_and_substrate_materials/cards/10_Cu_film.md；本派生包未附，非本地导航或运行依赖）

- 证据条件：manufacturer general dose guidance only; no matched Kaufman optical primary study in round1；来源：IS-06, IS-07
- 已支持范围：本轮仅建立机理与测试门槛，Cu定量Kaufman最佳条件未知
- Ar条件：动量/清洗可能影响成核与界面；未证明净收益
- O2条件：元素金属目标下氧化为主要化学风险假说，应实测
- 副作用/失败候选：反射损耗、氧/杂质、应力、粗糙、再溅射
- 尚未知：同厚度Cu的反射/电阻/附着与通量能量关系
- 最小验证：Cu/O；R/T/吸收；AFM；片阻；应力；附着
- 进入下一步的门槛：不得照搬Al/Ag或厂家剂量轮作Cu保证

## MAT-11 Cr · film

身份：Cr金属/粘接层与Cr氧化物分开；T04材料卡（上游背景引用：../../04_coating_and_substrate_materials/cards/11_Cr_film.md；本派生包未附，非本地导航或运行依赖）

- 证据条件：manufacturer guidance; no matched Kaufman optical study in round1；来源：IS-06, IS-07
- 已支持范围：只支持作为待验证工程候选；没有无条件更好附着结论
- Ar条件：界面混合可能增附着也可能增加吸收/损伤
- O2条件：会改变金属与氧化物目标，不能当无害辅助气
- 副作用/失败候选：薄粘接层连续性、光损耗、应力、界面混层
- 尚未知：纳米Cr层有效厚度/组成/附着关系
- 最小验证：XPS/截面如适用；R/T；应力；附着；厚度
- 进入下一步的门槛：最终膜系吸收预算必须包含粘接层，不只看胶带测试

## MAT-12 Al · film

身份：金属Al薄膜及原生氧化层分别建模；T04材料卡（上游背景引用：../../04_coating_and_substrate_materials/cards/12_Al_film.md；本派生包未附，非本地导航或运行依赖）

- 证据条件：thermally evaporated Al with Ar IAD; original optical/mechanical study；来源：IS-22
- 已支持范围：Ar辅助可使Al压应力和电阻率上升，光学常数随动量输入变化
- Ar条件：可能改变致密度与空隙，但不可只最大化n
- O2条件：氧化层形成与元素Al反射目标有竞争，界面暴露需控
- 副作用/失败候选：压应力、Ar俘获、氧化、粗糙、再溅射
- 尚未知：本机反射目标波段与保护层/Al界面工艺
- 最小验证：R/T/吸收；Al/O/Ar；AFM；片阻；应力
- 进入下一步的门槛：Al的k变小不自动推出所有λ反射变大

## MAT-13 ZnS · substrate

身份：标准CVD与HIP/MS等级、抛光损伤分开；T04材料卡（上游背景引用：../../04_coating_and_substrate_materials/cards/13_ZnS_substrate.md；本派生包未附，非本地导航或运行依赖）

- 证据条件：T04 substrate card + indirect film chemistry evidence；来源：IS-07, IS-20, IS-28
- 已支持范围：没有取得本机ZnS块材Kaufman预清洗安全窗口
- Ar条件：污层去除需与表面粗化/计量偏差分离
- O2条件：可能改变表面S/O；具体产物/速率未知
- 副作用/失败候选：表面化学、软基片粗糙/散射、局部热与充电
- 尚未知：不同等级/抛光批的清洗去除率和附着收益
- 最小验证：前后AFM/散射；Zn/S/O；T/R；波前；温度
- 进入下一步的门槛：预清洗与IAD分组，空白基片先验，不能用膜数据保证块材

## MAT-14 Ge · substrate

身份：掺杂/电阻率、晶向、批次与面形；T04材料卡（上游背景引用：../../04_coating_and_substrate_materials/cards/14_Ge_substrate.md；本派生包未附，非本地导航或运行依赖）

- 证据条件：T04 substrate card; no exact preclean qualification；来源：IS-07, IS-23, IS-27
- 已支持范围：Ar辅助膜系收益不等于Ge清洗任意剂量安全
- Ar条件：去氧化/污染候选，须核缺陷、粗化和表面残留
- O2条件：表面氧化可能改变界面；氧化率未确定
- 副作用/失败候选：温敏吸收、表面缺陷、充电、面形
- 尚未知：实际基片电阻率与T依赖光损耗、表面剂量界限
- 最小验证：Ge/O；AFM；IR T/R/吸收；波前；T(t)
- 进入下一步的门槛：温升上限由基片/夹具/功能共同确定，不取文献沉积温度作上限

## MAT-15 K9 · substrate

身份：实际牌号先核；T04代表H-K9L不等于任意K9；T04材料卡（上游背景引用：../../04_coating_and_substrate_materials/cards/15_K9_substrate.md；本派生包未附，非本地导航或运行依赖）

- 证据条件：dielectric charging principle + T04 H-K9L card；来源：IS-03, IS-07
- 已支持范围：无本机K9 Kaufman预清洗/充电放行数据
- Ar条件：污染去除与碱组分/粗糙改变风险需对照
- O2条件：表面化学变化须测；对玻璃适用不等于对已镀面适用
- 副作用/失败候选：介质充电、局部热、表面粗化、波前/应力
- 尚未知：真实玻璃牌号、前后表面状态、温度/电位
- 最小验证：AFM/散射；表面化学；波前；T(t)；电位；附着
- 进入下一步的门槛：空白实材对照不能仅用Si见证替代

## MAT-16 ZnSe · substrate

身份：CVD光学级、缺陷/抛光批与SDS；T04材料卡（上游背景引用：../../04_coating_and_substrate_materials/cards/16_ZnSe_substrate.md；本派生包未附，非本地导航或运行依赖）

- 证据条件：T04 material/SDS + generic preclean, no matched Kaufman dataset；来源：IS-07
- 已支持范围：本輪不宣称已验证ZnSe预清洗窗口
- Ar条件：表面去除可能影响Zn/Se比例、粗糙和残留；方向未确定
- O2条件：氧化是待检风险，不能给低能阈值
- 副作用/失败候选：软脆表面损伤、吸收/散射、毒性清腔废料
- 尚未知：Kaufman前后Zn/Se/O、吸收与附着及安全清腔程序
- 最小验证：FTIR/适用量热；Zn/Se/O；AFM；波前；温度
- 进入下一步的门槛：先EHS核清腔/废料；破损/烧损不按普通光学玻璃处理
