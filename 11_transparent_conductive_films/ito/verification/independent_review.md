# ITO 独立技术核验

核验时间：2026-10-03 UTC。核验范围：新增 ITO 研究的 integration、electro_optics 和已形成的 process 证据账本。所有执行均在临时复制目录完成；未修改作者代码、产品运行时或冻结 T01–T10。

## 结论

**所核验的参考计算链没有发现会改变当前合成结论的公式、单位、符号或核心数值实现阻断。** 17 项 integration 测试和 19 项 electro_optics 测试均重新通过；另用独立边界条件求解核对相干光学，用全相位平均核对非相干组合。以下结论仅是代码/算术核验，**不是实际 ITO 薄膜、工艺到材料映射或设备模型的物理验证，也不构成生产放行**。

三项有限修正/说明（最终均已关闭；见第8节）：

1. **引用定位需更精确（低严重度）**：integration 中 INT-S01 的 In₂O 主导气相命题成立，但最直接位置是 Bischof 原稿 Abstract、§4.3.1（印刷 pp.22–23；PDF 索引21–22）。原先 §§2–3、Table 3 主要定位方法/条件，不宜单独作为“主导物种”的定位。不会改变技术结论。**复核状态：11:18 UTC 已确认正文及 sources.json 改为 Abstract、§4.3.1；此项关闭。**
2. **证据构建脚本的打包依赖（低严重度；核心模型不受影响）**：process/build_evidence.py 原始版本第9行无条件读取 sources/originals/Korneluk_2023_CC-BY-4.0.pdf 计算 SHA。含原文的临时副本可以重建；只复制脚本、按计划排除原文后会 FileNotFoundError。应标注该脚本仅用于含原文的研究存档，或在原文缺席时保留已登记哈希、明确“本次未重新核验原文”，而不声称重新验过不存在的文件。无需为修复此项把论文原文加入用户包。**最终状态：作者中间生成器已移除，交付只含冻结账本和公开参考代码；此项关闭。**

3. **新来源未写入生成器（低严重度；可复现性）**：11:20 UTC 新版 process/report.md、sources.json 已加入 ITO-P15（Fraunhofer年报），但当时 build_evidence.py 没有 P15，重建会把它删除；sources.json 的 fulltext_engineering_count 仍为1而不是P08+P15的2，除非另明确“核心1+补充1”口径。应在生成器加入新来源并同步统计，不依靠事后手改生成文件。此项影响来源可追溯性，不影响电光合成数值。**最终状态：中间生成器已移除，冻结账本保留P15，工程全文计数已为2；此项关闭。**

本稿首次写入时 process/report.md 尚未生成；**11:20 UTC 已补做叙述复核**。新增 integration/03_engineering_foundations.md 也完成与模型边界的一致性检查，官方身份和网页全文核验由该补充内容的研究者负责，本次没有冒充重复核验其全部来源。后续变更若影响范围，应增加复核记录。

## 1. 源料、通量、库存及厚度

- 100 g 的 90/10 wt% In₂O₃/SnO₂ 原料，独立按物质的量计算 Sn/(In+Sn)=0.09284213997098024。代码结果相同。该数不是含氧总原子比例、实际膜组成或活性施主比例。
- 点源总粒子率与归一化半球角分布相乘，除距离平方，再乘一次接收表面投影；没有重复乘接收余弦。遮挡 visibility 直接损失通量，没有重新归一。测试中的距离×2、接收余弦×0.5、visibility×0.3 给通量比0.0375。
- 热气体撞击式 p/√(2πmkBT) 的质量口径是单粒子 kg，输出 particles m⁻² s⁻¹。O₂ 分子转氧核需乘2；报告没有把撞击率直接等同留存率。源热平衡的潜热与粒子/摩尔流量要求匹配。
- m_A=ΣA_eM_e/N_A 为 kg m⁻²，h=m_A/ρ_eff 为 m；实际有效密度与 QCM 软件密度分开。密度变化时的厚度导数含收缩项。
- 对 In、Sn、O 各自测试过量净损失均会 ValueError；输入字典不变。恰好耗尽得到零，下一步再损失被拒绝；不存在裁零后继续侵蚀库存的路径。此参考没有实现基片暴露后的损失模型，报告明确留作边界。
- 显式 partial、unknown、blocked 状态保留，完整质量账断言是调用者的前置条件；代码本身不能探测未建模污染物。

## 2. 方阻、Hall、Drude 与可辨识性

- 面内标量导电的 Rs=1/Σσ_jd_j 正确；不是跨膜串联电阻。连续性、共同面内电场、接触、各向异性和基片并联边界均有披露。
- 均匀单电子模型 RH=−rH/(qN)、NH=N/rH、μH=rHμtransport 正确；qNHμH=σ 并不使各参数自动成为微观真值。
- 用两层 Drude 低磁场电导张量独立求逆，核对 Nsheet,Hall=S₁²/S₂、μHall=S₂/S₁，两者相对误差均低于1e−12。这个测试仅在报告列明的同号、低场、rH=1、并联条件成立。
- cm⁻³→m⁻³、cm²/(V·s)→m²/(V·s)、Ω·cm→Ω·m、eV→rad/s 换算正确。
- exp(−iωt)、n+ik 与 εDrude=ε∞−ωp²/[ω(ω+iγ)]、σDrude=ε₀ωp²/(γ−iω) 相容。独立检查 ε=ε∞+iσ/(ε₀ω)；正阻尼的被动虚部和 σ(0)=Nqμopt 均符合约定。
- N→cN、m*→cm*、μopt→μopt/c 保持 ε 不变的不可辨识反例成立。报告没有因光谱点多或拟合好就宣称 N、m*、μ 唯一识别。
- μopt、μtransport、μH 分开，经验 ε 表与机制参数化并列；有限域、非抛物性、Hall 因子、微结构和散射限制均保留。

## 3. 相干与非相干光学独立数值检查

除作者自带测试外，另直接建立每个界面的 E、H 连续方程，求解全部正反向场振幅。该检查不调用代码中的递推关系或作者的特征矩阵测试函数。

| 独立检查 | 覆盖 | 结果 |
|---|---|---|
| E/H 边界直接线性求解 vs coherent_rt | 固定随机种子73021；250组；1–4层；实外介质；含吸收层；420–2400nm | R/T最大绝对差1.1102230246251565e−15 |
| 非相干结果 vs 明确有限基底的相位平均 | 10组；每组1024个完整均匀相位；有损前膜；入射/出射折射率可不同 | R/T/A最大绝对差4.996003610813204e−16 |
| 作者原测试重跑 | 无膜/零厚度/四分之一波长膜/互易性/能量/厚吸收层/经验插值/域外拒绝 | 19项通过 |
| 合成 demo 重跑 | 3组人工参数 | JSON和CSV与原保存结果逐字节相同 |

- T=(nout/nin)|t|² 的功率归一只用于实正入射/出射介质，代码会拒绝吸收边界。
- 反向前膜使用倒序层和交换介质。非相干公式仅支持无吸收厚基底、裸背面、完全相位平均；没有暗中添加吸收基底或部分相干支持。
- 无膜的半无限玻璃 T=0.96 与无损厚玻璃板 T=0.96/1.04 区分正确。
- 散射/雾度不包含在平面镜面模型中；报告不把缺失镜面能量自动称作吸收。
- 上述误差是限定测试空间的计算差异，不是实验误差或模型对真实样品的精度。

## 4. Process 账本快照检查

- 30个观察行的CSV/JSON逐字段匹配；10个命题的引用全部对应14个源ID。
- 12个带明确 Rs、d 和派生ρ的观察满足 ρ[Ω·cm]=Rs[Ω/□]×d[nm]×10⁻⁷。已有 Farhan 矛盾行仍明确隔离，没有拿其报告ρ替代派生值。
- 已列 FOM 与 T¹⁰/Rs 在原表舍入精度内相符。不同光谱口径、峰值/550nm/带平均/对裸玻璃比值未混为同一透过率。
- 原档案中唯一指向本地保存原文的 P03 文件确实存在，SHA与账本一致；此检查不能让不携带原文的分发包声称其也包含或重新核验了原文。
- 6项可靠全文研究、1项隔离全文、1项工程全文的计数与来源分类一致；其余摘要/章节片段未被计入全文。
- 对这些工艺论文的全部表格/图像未重新逐页独立审读；本节核验范围是账本一致性、算术、已披露口径及明显跨样本拼接风险，不是全部原文数据的第二次数字化。

## 5. 来源访问与证据边界

访问层级、来源身份与命题状态分别记录。抽检未发现把摘要访问写成已阅读全文、把厂商建议写成本机验证、或把合成数据写成实测的情况。不能将“同行评审来源等级A”解读为“该研究的所有细节已经核实”，应始终同时阅读 access_level 和命题状态。

本次独立复核成功打开并抽读：

- [Bischof作者原稿](https://juser.fz-juelich.de/record/1024859/files/Bischof%20Calphad%20102507%20Manuskript.pdf)：PDF文本可读；方法为铱Knudsen池，In₂O主导的表述可找到。不是开放式ITO蒸镀组分模型
- [Byrnes v5](https://arxiv.org/html/1603.02720v5)：HTML全文可读；时间约定、Fresnel、功率归一和非相干限制与代码一致
- [Furubayashi作者机构PDF](https://www.ele.kochi-tech.ac.jp/yamateko/acsaelm.9b00317.pdf)：PDF文本可读；特定RPD/后处理的迁移率非单调解释可找到。未重新读取全部图像像素
- [NIST Hall教程](https://www.nist.gov/pml/nanoscale-device-characterization-division/popular-links/hall-effect/hall-effect)：官方页面可读；不把历史教程称作现行标准
- [Fujiwara/Kondo摘要页](https://journals.aps.org/prb/abstract/10.1103/PhysRevB.71.075109)：摘要可读；本次不升级成全文审读
- [Gui等出版社页面](https://www.nature.com/articles/s41598-019-47631-5)：尽管出现cookie错误URL参数，工具仍返回完整正文文本；访问状态未据URL错误字样错误降级或升级

本次没有重新验证所有 Undermind 会话、全部受限源或许可证链；作者对未读全文及未核数值的保留应继续有效。没有新增论文原文到研究包，也没有把全文可读等同可再分发。

## 6. 所测试代码版本

以下为首次执行时内容的 SHA-256；若文件以后变化，不能直接沿用本次结论而不检查改动：

- integration/reference_state.py：77a5af86a339e7cb7a0fc3eb141aee207cb57cf27cf1a85177a2ed317ee639b0
- integration/test_reference_state.py：89c6d1470c25707c095f01610b05761c4a5a1de5dc02202d9fc2e3e309fe57db
- electro_optics/model.py：7234f9682c30274337309e68c6c28c7d0b10e31a186589a1edd2ec0ec5647b32
- electro_optics/test_model.py：dd0d8fa7ae1298994996fafdd56c76771a14f588061ea4b5f52ae9a15a60d222
- electro_optics/demo.py：70fc0ef73183d049404621ae909c3651a12530d029f6f7619d31d761365d1669

自带测试的复算命令：

```sh
cd integration && PYTHONDONTWRITEBYTECODE=1 python test_reference_state.py
cd ../electro_optics && PYTHONDONTWRITEBYTECODE=1 python test_model.py
PYTHONDONTWRITEBYTECODE=1 python demo.py
```

独立随机边界/相位/Hall核验脚本在本次临时目录中执行；未将临时运行产物写入作者目录。以上覆盖不足以取代实际膜厚、Rs/Hall、T/R/椭偏、成分/密度及整批留出实验。


## 7. 后续叙述复核（11:20 UTC）

- process/report.md 的主结论、条件表与30行证据账本一致，未把氧流量跨设备当配方；未把阴极/放电设置当到片单能能量，也未把无预热当作沉积全程室温。
- 独立复算95/5、90/10、80/20氧化物质量比分别为4.623720%、9.284214%、18.717290% Sn阳离子；90/10金属合金为9.703957%。报告舍入正确、源料和成膜口径分开。
- 各表Rs、ρ、厚度、退火时间/气氛和光学定义保持配套；Korneluk的Rs90与标称70nm只推出6.3×10⁻⁴ Ωcm，没有与摘要最低ρ强拼；Farhan矛盾仍隔离。
- 源处理、实际Ts(t)、离子能谱/通量及成分数据缺口明确；既有摘要来源未升级全文；Fraunhofer年报被明确写成关联线索，未冒称等同受限期刊全文。
- 工程基础补充只把光学常数、散射/吸收、基片背面和空间均匀性诊断迁移到ITO。没有将TiO₂/空气50:50 EMA体积分数、双腔Ta₂O₅/SiO₂参数或未读课程结论移植为ITO默认参数。与现有代码适用域无冲突。
- 未发现新增的物理模型阻断；当时待关闭的只是上方构建脚本依赖/来源再生成小项；最终状态见第8节。

## 8. 最终关闭复核（2026-10-03 11:22 UTC）

**本轮独立核验已完成，发现的三项小问题均已关闭。没有遗留的核心参考计算阻断。**

从当前目录新建独立临时副本，删除所有 originals 目录后复核：

- integration 17项测试、electro_optics 19项测试再次全部通过（共36项），不依赖论文原文
- process/build_evidence.py 确实已从交付内容删除；它是作者中间生成器，不再作为用户可执行/重建工具交付
- 冻结 process/sources.json 保留15个唯一源ID，包括P15；fulltext_engineering_count=2；30行CSV/JSON逐字段一致；10个命题的引用全部有效
- 无原文副本内没有PDF；这里核验的是新建的原文排除副本，不冒称已经检查了尚未生成的最终ZIP
- INT-S01正文与来源定位的修正仍在
- integration/reference_state.py 和 electro_optics/model.py 的SHA与此前独立边界条件/相位平均/Hall测试时完全相同

关闭结果只支持此次文档、有限域参考实现和合成算术交付。真实工艺的N/μ、厚度/密度、T/R/Rs、源分馏及可靠性仍需要设备和样片数据，不能据36个测试称作物理验证完成。

## 附录：独立检查脚本

可将下列脚本保存在临时目录，工作目录设为 ITO 目录后执行；不写入模型目录，不需第三方库。代码内的 N、μ、层厚和折射率均是明确的数值测试输入，不是材料拟合或设备参数。

```python
import sys, math, cmath, random
from pathlib import Path
sys.path[:0]=[str(Path.cwd()/'integration'),str(Path.cwd()/'electro_optics')]
import reference_state as s
import model as m

def solve(a,b):
    a=[list(row)+[y] for row,y in zip(a,b)]
    N=len(b)
    for i in range(N):
        k=max(range(i,N),key=lambda j:abs(a[j][i]));a[i],a[k]=a[k],a[i]
        p=a[i][i]; assert abs(p)>1e-20
        a[i]=[x/p for x in a[i]]
        for j in range(N):
            if j!=i:
                p=a[j][i];a[j]=[x-p*y for x,y in zip(a[j],a[i])]
    return [row[-1] for row in a]

def boundary_rt(wl,layers,n0,ns):
    # Independent direct E,H boundary solve; unknowns [r,A1,B1,...,t].
    n=[n0]+[x[0] for x in layers]+[ns];d=[0]+[x[1] for x in layers]+[0]
    L=len(layers);N=2*L+2;a=[];b=[]
    for j in range(L+1):
        # E and H at boundary: known incident + each medium's wave terms
        for h in (False,True):
            row=[0j]*N;rhs=0j
            if j==0:
                row[0]=(-n0 if h else 1);rhs=-(n0 if h else 1)
            else:
                p=cmath.exp(2j*math.pi*n[j]*d[j]/wl)
                row[2*j-1]=(n[j] if h else 1)*p
                row[2*j]=(-n[j] if h else 1)/p
            if j==L:
                row[-1]-=(ns if h else 1)
            else:
                row[2*j+1]-=(n[j+1] if h else 1)
                row[2*j+2]-=(-n[j+1] if h else 1)
            a.append(row);b.append(rhs)
    sol=solve(a,b)
    return abs(sol[0])**2,ns/n0*abs(sol[-1])**2

rng=random.Random(73021);max_rt=0;max_energy=0
for k in range(250):
    n0=rng.uniform(1,2);ns=rng.uniform(1,2.3);wl=rng.uniform(420e-9,2400e-9)
    layers=[(rng.uniform(.15,3.5)+1j*rng.uniform(0,.9),rng.uniform(0,180e-9)) for _ in range(rng.randrange(1,5))]
    r,t=boundary_rt(wl,layers,n0,ns);out=m.coherent_rt(wl,layers,n0,ns)
    max_rt=max(max_rt,abs(out.R-r),abs(out.T-t))
    assert abs(out.R-r)<2e-12 and abs(out.T-t)<2e-12
    assert min(out.R,out.T,out.A)>-2e-12
print('direct_boundary_random_cases=250 max_abs_RT_error=',max_rt)
# Incoherent averages with unequal exterior indices, including loss in front stack
max_phase=0
for k in range(10):
    wl=rng.uniform(500e-9,1800e-9);ns=rng.uniform(1.4,1.8);n0=rng.uniform(1,1.3);no=rng.uniform(1,1.3)
    layers=[(rng.uniform(1.3,2.5)+1j*rng.uniform(0,.3),rng.uniform(20e-9,150e-9)) for _ in range(3)]
    inc=m.incoherent_substrate_rt(wl,layers,ns,n0,no)
    vals=[m.coherent_rt(wl,layers+[(ns,(20+(i+.5)/1024)*wl/(2*ns))],n0,no) for i in range(1024)]
    err=max(abs(getattr(inc,key)-math.fsum(getattr(v,key) for v in vals)/1024) for key in ('R','T','A'))
    max_phase=max(max_phase,err);assert err<1e-12
print('incoherent_phase_average_cases=10 samples_each=1024 max_abs_RTA_error=',max_phase)
# Hall low-B tensor check. All electron species; compare magnitude of Hall sheet coefficient.
N=[2e26,7e26];mu=[.003,.0012];d=[40e-9,85e-9];B=1e-5
sxx=sum(m.Q*N[j]*mu[j]*d[j]/(1+(mu[j]*B)**2) for j in range(2))
sxy=sum(-m.Q*N[j]*mu[j]**2*d[j]*B/(1+(mu[j]*B)**2) for j in range(2))
rh=abs(sxy)/(sxx*sxx+sxy*sxy)/B
S1=sum(N[j]*mu[j]*d[j] for j in range(2));S2=sum(N[j]*mu[j]**2*d[j] for j in range(2))
assert abs((1/(m.Q*rh))/(S1*S1/S2)-1)<1e-12
assert abs((sxx*rh)/(S2/S1)-1)<1e-12
print('low_B_parallel_Hall_tensor_check=PASS')
# Independent 100 g source stoichiometry and mass/thickness checks.
x=(10/150.708)/(2*90/277.633+10/150.708)
assert abs(x-s.source_wt_to_cation_fraction(.1))<1e-15
print('90_10_wt_Sn_cation_fraction=',x)
A={'In':2e20,'Sn':1e19,'O':3.2e20};rho=7000
mass=sum(A[e]*s.M[e]/s.NA for e in A);h=s.conditional_thickness(A,rho,inventory_complete=True)
assert abs(h*rho/mass-1)<1e-15
original={'In':2.,'Sn':1.,'O':3.}
for flux,dt in [({'In':-3,'Sn':0,'O':0},1),({'In':0,'Sn':-2,'O':0},1),({'In':0,'Sn':0,'O':-4},1)]:
    try:s.inventory_step(original,flux,dt);raise AssertionError('depletion not rejected')
    except ValueError:pass
assert original=={'In':2.,'Sn':1.,'O':3.}
assert s.inventory_step({'In':2.},{'In':-1.},2)=={'In':0.}
try:s.inventory_step({'In':0.},{'In':-1.},.1);raise AssertionError
except ValueError:pass
assert s.cosine_point_flux(1e20,2,1,.5,2,.3)/s.cosine_point_flux(1e20,2,1,1,1)==.0375
print('inventory_mass_projection_checks=PASS')
# Full constitutive relation checks use epsilon minus bound background.
a=m.DrudeLorentz(3e26,.0035,.35,3.9)
for wl in (450e-9,1550e-9,2400e-9):
    omega=m.omega_from_wavelength(wl)
    eps=a.epsilon(wl);sigma=a.drude_conductivity(omega)
    assert abs(eps-(a.epsilon_inf+1j*sigma/(m.EPS0*omega)))<1e-12
    scaled=m.DrudeLorentz(a.carrier_density_m3*2,a.mobility_opt_m2_vs/2,a.effective_mass_me*2,3.9)
    assert abs(a.epsilon(wl)-scaled.epsilon(wl))<1e-12
print('Drude_sign_units_nonidentifiability_checks=PASS')
```
