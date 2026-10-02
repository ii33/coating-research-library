# 独立窄审查：量纲、净分母与库存边界

审查日期：2026-10-02 UTC。范围仅为 `models/contract.py`、`models/build_examples.py`、`tests/test_contract.py` 中的原子/式单元计数、N_net/h/D/U/R/epsilon 量纲、净分母分类、实际膜密度门控及初始/逐时间箱库存耗尽。仅查阅本地代码和执行 stdlib 轻量合成测试；未做设备采样、重任务、上传或后续阶段。此审查不构成生产许可、材料响应预测有效性或完整模型签字。

## 结论与发现

主计算路径的量纲和粒子计数一致；发现三处输入/库存门控缺口，已即时报告实施者，并在实施者修复后完成最后一次独立窄复验：54/54 通过（原 46 项 + 新增 8 项）。本轮已复现的三处缺口均关闭。审查者仅新增本报告与一个含 8 项窄测试的文件，未修改核心文件。

1. **真实中间库存负值被相对容差放行，影响 N_net/h/R/epsilon。** 原条件 `lower < -1e-12 * max(1, abs(upper))` 把物理不确定区间的上界当作容差尺度。可复现输入：Si 初始库存界 `[1e18, 1e20] atoms/m2`，第一箱 10 s 的通量为 `-(1e17+1e6) atoms/m2/s`，第二箱 10 s 通量为 `1e18 atoms/m2/s`，O 均取 Si 的 2 倍。第一箱可达的 Si 库存是 `-1e7 atoms/m2`，并非浮点单次舍入量级；原实现仍返回 `N_net=2.699999999997e19 atoms/m2`、`R≈0.222222222222469` 和有限正 h。后续补沉积不能恢复此路径的同一膜材料保证。实施者已改为任何中间库存下界 `<0` 都阻断；窄测试 07 已通过。

2. **初始库存只检查名义值，未检查负下界。** 原记录中把初始 Si 库存界下端改为 `-1e10 atoms/m2`，名义值保持 `1e20`，会得到 `validate=[]`；第一箱正沉积可以掩盖初始不可行支持集并放行 N_net。实施者已增加下界非负验证；窄测试 06 已通过。

3. **原子摩尔质量只检查名义值，未检查非正下界。** Si 摩尔质量名义值保留 `.028085 kg/mol`，界改为 `[-.1,.1] kg/mol`，原验证返回 `[]`，随后在式单元摩尔质量分母运算时抛出 `ContractError: denominator contains zero`。应在输入层要求质量界严格为正，与密度门控一致。实施者已改为拒绝名义值或区间下界 `<=0`；最后窄测试 08 通过。

## 已检查的量纲链

- 各元素通量为 `atoms/m2/s`，乘时间箱长度得到元素净库存变化；全部元素相加得到有符号 `N_net [atoms/m2]`，不是到达通量，也不是式单元数
- 固定且已验证化学计量下，`nu = sum(stoichiometry)`，`M_formula = sum(nu_e * M_e) [kg/mol]`；`n_atom = rho_film * N_A * nu / M_formula [atoms/m3]`，`N_formula_net = N_net / nu [formula_units/m2]`，`h_increment = N_net / n_atom [m]`
- 基准 SiO2 中 `nu=3`、`M_formula=.060083 kg/mol`；`N_net=2e19 atoms/m2`，式单元净数为该值的三分之一
- `D = sum(charged particle flux * dt) [charged_particles/m2]`；荷数与每粒子核数不另乘到 D。带双电荷双核粒子替代单电荷单核粒子时，同一已给定粒子通量的 D 不变
- `U = sum(all declared particle flux * dt * particle energy) * E_CHARGE [J/m2]`；粒子能量已为 `eV/particle`，不再乘荷数。显式中性粒子进入 U，不进入 D；未知中性库存保持 U/epsilon 阻断
- `R = D / N_net [charged_particles/net_atom]`；`epsilon = U / E_CHARGE / N_net [eV/net_atom]`。基准 `D=6e18`、`U=8e20*E_CHARGE`，所以 `R=.3`、`epsilon=40`
- h 仅允许实际有效膜密度、固定组成、匹配摩尔质量和不变密度/组成前提；基底密度改变不影响 h，`bulk_substrate` 密度来源或只具文献参考状态的膜密度不会被当作实测膜输入

## 净分母行为与限制

零及跨零分母不给 R/epsilon；净侵蚀给有符号负厚度增量但不给正增长语义的比例坐标。严格正、宽度不小于下界的分母标记 `ill_conditioned`，仅保留诊断区间，名义比值为 null。这是显式计算门槛，不是经实验标定的条件数阈值。区间为已给定界的外包运算，不提升为概率联合覆盖或连续时空保证。

库存按每个已解析时间箱检查；本轮验证包含“先耗尽、后补沉积、最终净值仍正”的情形。移除宽区间容差后的保守阻断不承诺消除所有近零舍入误阻断，也不保证时间箱内部未解析事件或真实膜/基底切换。精确零操作保留零界属于实施者配套修复，不应被解读为任意相消都精确。

## 验证记录

- 修复前：原 `test_contract.py` 的 46/46 通过，但上述 3 个独立最小反例成立；未把现有测试全绿当作边界完备性证据
- 新增文件：`tests/test_independent_dimensions.py`，恰好 8 项，无预期失败装饰、无跳过，直接断言安全契约
- 中间版本：库存两项修复后，新增测试 7/8 通过；合并发现运行 53/54 通过，唯一失败为 `test_08_molar_mass_interval_is_strictly_positive`
- 复跑命令：`python -m unittest discover -s tests -v`；全部测试为本地轻量测试，总运行时间小于 1 s
- 最终版本：2026-10-02 06:36 UTC，54/54 通过，退出码 0，测试报告运行时间 0.248 s；没有跳过、预期失败或设备测试

最终复验文件 SHA-256：

- `models/contract.py`: `b601099bb5e4a62a9c4dc7d6de2f7a8068c1305bcf055bc9137d2fc741414f07`
- `models/build_examples.py`: `0ef18e66dca130c4c7c746f545fbd9af0fe96d5aa4e6180933ab2fd1a120c90a`
- `tests/test_contract.py`: `747bf85b8526dae9f89478321d56073e1efc436b8d978d7125ebef167c438ab5`
- `tests/test_independent_dimensions.py`: `2e7a8942a6a8c27bc33088402614322b24db4c0326768578d9fcc4d1b8c26b08`

本报告的有限通过范围只覆盖上述量纲及门控，不涵盖再溅射模型、响应曲线、校准统计、材料真实性、设备验证、生产资格或整个接口的全域正确性。
