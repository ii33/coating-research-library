#!/usr/bin/env python3
"""Render an evidence-only report from frozen machine-readable results."""
import hashlib,json
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent
x=json.loads((P/'results.json').read_text()); y=json.loads((P/'withdrawal_and_counterexamples.json').read_text())
rows=x['rows']; polish=y['polished']; methods=['direct_local','direct_multistart','direct_multistart_cap','amplitude_homotopy','phase_homotopy','phase_no_step']
def rr(case,m,post=False): return [r for r in (polish if post else rows) if r['case']==case and r['original_method' if post else 'method']==m]
def med(case,m,post=False): return float(np.median([r['V'] for r in rr(case,m,post)]))
lines=['# 复反射辅助同伦：第二轮独立小预算验证','',
'日期：2026-10-19 UTC。仅独立云端研究目录；没有修改或发布主软件。物理模型是合成常数 n/k、正入射、相干平整薄膜、无损半无限外介质。不是实际 IR 材料设计，也不是物理不可行性结论。','',
'## 结论','',
f"在三个配对种子的双窗问题上，相位同伦优于未限步的普通四起点；但加上完全相同相位步长上限的普通四起点后，相位的归因不成立。主试验中限步普通法中位 V={med('dual_ar','direct_multistart_cap'):.6f}，相位法 {med('dual_ar','phase_homotopy'):.6f}；同等追加 12 次纯功率精修后分别为 {med('dual_ar','direct_multistart_cap',True):.6f} 与 {med('dual_ar','phase_homotopy',True):.6f}。限步普通法在三例中赢两例，且墙钟更低。首轮证据支持保留简单限步对照，不支持把新增复杂度归功于复相位。",'',
'全部 36 个主试验及精修后交付候选均未达到 R≤1% 的有限密网格目标。两层简单单窗各方法的中位数几乎相同，相位没有实用收益；direct_local 的 seed47 出现 V≈20.9446 的明显差解，不能把中位数接近解释成每次运行都接近。三个种子不足以估计一般成功率。','',
'## 可复现设置','',
'- simple_ar：两层 [1.45,2.35]，3–5 μm；dual_ar：六层 [1.45,2.35]×3，3–5 和 8–12 μm。外介质 n0=1，ns=3.42；材料均为无损合成常数。',
'- 每层厚度 0.005–2.5 μm，固定拓扑，无插层、删层或主软件接口。相同种子 11、29、47 与相同四个实际起点。direct_local 只用第一起点，但总迭代数同为 80；它比四起点少付三个初始化审计的成本，单列实际工作量。',
'- 每窗固定 41 点求解；独立 257 点原始目标档案不影响优化轨迹；每个候选按 V=max(0,max(R/0.01−1))、窗口等权平均 R 排序。R/T 均用物理前向复算。',
'- 四分支各 20 次外迭代；同伦 τ=[0.15,0.35,0.55,0.75,0.9,1]，前五阶段各三次，最后五次。θmax=π/3。每支都会以 t≥0 的原始功率 epigraph 运行 τ=1，辅助项严格为零。',
'- same-cap 普通法、幅度同伦和相位同伦均满足每层 |Δδ|≤π/4；phase_no_step 仅取消该上限。所有法保留相同真实信赖域接受检验和有限差分厚度雅可比。',
'- 每个外迭代完整计入 N 次有限差分、当前值、试探值、被拒步和档案审计。QP 本身不调用物理内核。相位目标构造耗时、QP 耗时、核耗时及总墙钟分别保存。没有用批量调用数假装等算力。',
'- 最后 2049 点/窗是独立加密评价，包含 257 个档案点及 1792 个新增内部点；不是完全不重叠的留出集。纯功率精修后在这个相同固定网格比较原候选和新候选，较差时保留原候选；比较使用已计费物理结果，原始精修候选也完整保留。该交付选择属于验证选择，不能再称作未触碰的统计留出。',
'- 对每个主试验选中候选，额外运行相同 12 次纯功率 epigraph 精修。源候选可能来自较早同伦阶段，input_archive_origin_tau 保留来源；纯功率实际轨迹及零辅助权重独立验证，不把来源重标为 τ=1。','',
'## 主试验：完全相同四起点下的消融','',
'| 问题 | 方法 | 中位 V | 有限网格通过 | 三次墙钟秒（含最终审计） | 三次点×层总工作 |','|---|---|---:|---:|---:|---:|']
for case in ['simple_ar','dual_ar']:
 for m in methods:
  r=rr(case,m); lines.append(f"| {case} | {m} | {med(case,m):.6f} | {sum(z['pass_finite_grid'] for z in r)}/3 | {sum(z['runtime_seconds_including_final_audit'] for z in r):.4f} | {sum(z['total']['point_layers'] for z in r):,} |")
lines+=['','## 严格撤除辅助项后的同成本复查','',
'下面每种方法均再付 12 次实际纯功率迭代；同问题四起点方法总工作严格一致。原始档案在同一最终审计上不允许退步。','',
'| 方法 | seed11 V | seed29 V | seed47 V | 双窗中位 V | 每次合并点×层 |','|---|---:|---:|---:|---:|---:|']
for m in methods:
 r=sorted(rr('dual_ar',m,True),key=lambda z:z['seed']); lines.append(f"| {m} | {r[0]['V']:.6f} | {r[1]['V']:.6f} | {r[2]['V']:.6f} | {med('dual_ar',m,True):.6f} | {r[0]['combined_point_layers']:,} |")
c=y['counterexamples']; p=x['checks']; z=p['zero_thickness']
lines+=['','## 解析起点、固定参考面和物理反例','',
f"1. 裸界面零厚度的精确 dR/dd=0，但 dr/dd 是非零纯虚数（{z['exact_surface_dr_dd_imag']:.6f}i /μm）。有限差分步长减半时强度斜率估计也减半；合法四分之一波厚度 {z['quarterwave_thickness_um']:.9f} μm 得 R={z['quarterwave_R']:.3g}、T≈1。这否定了‘一阶功率针插停滞就无可改进’。固定参考面下，正负分支的辅助一阶斜率分别为 {z['auxiliary_dF_dd_sign_branches']}；它只说明能移动，不证明降低原始目标。",'',
'2. 固定基片前边界 x=0，薄膜占据 [−Σd,0]；所有可行设计的同一空气参考面是 x=−N·2.5 μm。相对于瞬时前表面的 r，显式乘 exp[4πi n0(N·2.5−Σd)/λ]，t 也补偿相应单程空气相位。没有通过独立修改 r/t 的目标相位制造额外自由度。',
f"   共同固定面再外移 1.713 μm 后，复数协变误差 {p['fixed_plane_covariance_error']:.3g}，辅助损失差 {p['guide_loss_fixed_plane_shift_difference']:.3g}；重跑设计厚度最大差 {p['optimization_fixed_plane_shift_thickness_max_difference']:.3g} μm，V 差 {p['optimization_fixed_plane_shift_V_difference']:.3g}。这是数值误差尺度，远小于方法差异。故意使用随膜厚移动的表面参考面的消融 V={p['moving_surface_reference_V']:.6f} 已单独保存，不能与固定面的目标偷换。",'',
f"3. 深反射零点：±10⁻⁷ μm 微扰使相位跳变 {c['reflection_zero']['phase_jump_rad']:.9f} rad，而最大 R 仅 {c['reflection_zero']['max_R']:.3g}。零反射附近 arg(r) 不是稳定验收量。",'',
f"4. 吸收反例：单层 n={c['passive_absorption']['n']:.9f}+0.2i、d={c['passive_absorption']['d_um']:.9f} μm，可令 R={c['passive_absorption']['R']:.3g}，但 T={c['passive_absorption']['T']:.6f}、A={c['passive_absorption']['A']:.6f}。反射归零不能代替透射验收。它是独立诊断，未把吸收情景混进无损搜索比较。",'',
f"5. 高 Q：25 层无损腔的单层相位只变 {c['high_Q']['single_layer_phase_change_rad']:.6g} rad，R 就从 {c['high_Q']['R_before']:.3g} 跳到 {c['high_Q']['R_after']:.6f}。单层相位上限不是多层功率信赖域或连续证书。",'',
f"6. 两个厚度变量对 18 个波长相反的局部反射相位旋转，最佳线性拟合残差仍为目标范数的 {100*c['incompatible_phase_targets']['relative_linear_least_squares_residual']:.3f}%。各窗引导不保证可由同一个膜系同时实现。",'',
'## θ 敏感性与失败记录','',
'相位旋转为 0 时逐位复现幅度同伦对照，测试已通过。以下额外敏感性试验单列计费，不拿其中最好参数回填主试验。','',
'| seed | θ=0 V | θ=π/6 V | θ=π/3 V | θ=2π/3 V |','|---|---:|---:|---:|---:|']
for seed in [11,29,47]:
 a=[next(r for r in y['theta_sensitivity'] if r['seed']==seed and abs(r['theta_max']-th)<1e-12)['V'] for th in [0,np.pi/6,2*np.pi/3]]
 center=next(r['V'] for r in rows if r['case']=='dual_ar' and r['seed']==seed and r['method']=='phase_homotopy')
 lines.append(f'| {seed} | {a[0]:.6f} | {a[1]:.6f} | {center:.6f} | {a[2]:.6f} |')
fail=sum(not h['qp_success'] for r in rows for h in r['history'])
lines+=['',f'主试验保留 {fail} 个 SLSQP 子问题非成功状态；返回步骤必须经过真实功率验收，未把它写成收敛证明。所有被拒步、QP 状态、分支、τ、实际/预测下降和阶段档案均留在 JSON。详见 failure_history.md。','',
'## 验证范围和下一步判断','',
 f"独立物理反例诊断另外计费：{c['cost']['calls']} 次前向、{c['cost']['points']} 个点、{c['cost']['point_layers']} 点×层，墙钟 {c['cost']['wall_seconds']:.6f} 秒。它们不加入主试验的同预算比较。",'',
f"复制核与复振幅实现的 R 最大差 {p['matrix_R_max_error']:.3g}、T 差 {p['matrix_T_max_error']:.3g}，与独立 Fresnel 递推 R 差 {p['independent_recursion_R_max_error']:.3g}；无损能量误差 {p['energy_max_error']:.3g}。11 项回归覆盖固定面、零厚度、实际工作量、配对起点、辅助项撤除、档案排序、同网格不回退和物理反例。",'',
'本轮最合适的判断是：复相位机制暂不保留为优先方案；普通 minimax 配合相同物理步长控制已经有更好的小样本中位结果。若继续，应先用更多配对起点检验限步基线，再决定是否值得研究相位分支。没有真实色散、角度/偏振、相关制造误差、背面或连续域认证；不能把有限网格未达标说成可行域不可行。','',
'## 文件与重跑','',
'- run_phase.py：36 次主比较、固定参考面核与成本计数、参考面消融。verified_kernel.py 是原已核验教学核的完整便携复制，源核保持未改。',
'- withdrawal_and_counterexamples.py：统一纯功率精修、θ 敏感性、零点/吸收/高 Q/不可实现相位反例。',
'- results.json/results.csv、summary.json/summary.csv：主结果及完整轨迹；withdrawal_and_counterexamples.json/withdrawal.csv：精修、额外诊断与工作量。',
'- test_phase.py/test_report.txt、failure_history.md：回归与失败记录。write_report.py 仅从结果渲染本报告。',
'- 重跑：OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python run_phase.py；再运行 python withdrawal_and_counterexamples.py、python -m unittest -v test_phase、python write_report.py。',
'- 依赖仅 numpy/scipy，无新安装、无训练数据、无代理模型。实际版本见 requirements.txt。',
'']
(P/'研究报告.md').write_text('\n'.join(lines))
(P/'README.md').write_text('# Fixed-plane reflection homotopy screening\n\nRead 研究报告.md for the evidence and negative conclusion. This standalone directory does not modify the production software or publish anything.\n\nReproduce with:\n\n    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python run_phase.py\n    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python withdrawal_and_counterexamples.py\n    python -m unittest -v test_phase\n    python write_report.py\n\nThe final 2049-point grid is a nested densification; it is used for explicit post-run archive selection, not an untouched statistical holdout or continuous proof.\n')
(P/'requirements.txt').write_text('numpy==2.3.5\nscipy==1.17.0\n')
files=[f for f in P.iterdir() if f.is_file() and f.name!='MANIFEST.json']
manifest={'files':[{'path':f.name,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(files)],'verified_kernel_original_sha256':'fb53b898a1e3db511c7ba98bb92648fd15b38f894de79fbeed312049a0acfca6','portable_kernel_sha256':hashlib.sha256((P/'verified_kernel.py').read_bytes()).hexdigest()}
assert manifest['verified_kernel_original_sha256']==manifest['portable_kernel_sha256']
(P/'MANIFEST.json').write_text(json.dumps(manifest,indent=2))
print('Report and manifest written:',len(files),'files')
