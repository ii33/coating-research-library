#!/usr/bin/env python3
"""Render a self-contained Chinese research report from the frozen run outputs."""
import csv,hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent

def main():
    r=json.loads((ROOT/'results/results.json').read_text()); mech=json.loads((ROOT/'mechanism_checks.json').read_text());rr=r['runs'];summ=json.loads((ROOT/'results/summary.json').read_text())
    shared_calls=sum(len(x) for x in r['pools'].values());shared_updates=sum(sum(162*len(p['d']) for p in x) for x in r['pools'].values());ref_calls=sum(x['refinement_calls'] for x in rr);ref_updates=sum(sum(y['wavelength_layer_updates'] for y in x['refinements']) for x in rr)
    ac=dict(matrix_stack_calls=0,matrix_wavelength_samples=0,matrix_wavelength_layer_updates=0,independent_recursion_stack_calls=0,independent_recursion_wavelength_samples=0,independent_recursion_wavelength_layer_updates=0)
    audits=[x['audit'] for x in r['bases'].values()]
    for x in rr:audits.extend([x['best_global_audit'],x['best_protected_audit']])
    for a in audits:
        for key,val in a['audit_cost'].items():ac[key]+=val
        if 'frozen_protected_subset' in a:
            for key,val in a['frozen_protected_subset']['audit_cost'].items():ac[key]+=val
    selected=[]
    for x in rr:
        for z in x['refinements']:
            selected.append(dict(case=x['case'],seed=x['seed'],method=x['method'],pool_id=z['pool_id'],pack_length=z['pack_length'],position=z['position'],initial_P_violation=z['initial_score'][0],final_P_violation=z['final_score'][0],initial_global_V=z['initial_score'][1],final_global_V=z['final_score'][1],initial_E_anchor=z['initial_E_anchor'],initial_E_multi=z['initial_E_multi'],local_calls=z['calls'],wavelength_layer_updates=z['wavelength_layer_updates']))
    with (ROOT/'results/refinements.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(selected[0]));w.writeheader();w.writerows(selected)
    falseglobal=sum(x['best_global']['score'][1]<=1e-12 and not x['best_global_audit']['all_targets_pass'] for x in rr)
    falseP=sum(x['best_protected']['score'][0]<=1e-12 and not x['best_protected_audit']['frozen_protected_subset']['pass_frozen_protected_subset'] for x in rr)
    diagnostics=dict(complete_runs=len(rr),selected_refinements=len(selected),charged_search_calls=sum(x['total_search_stack_calls_charged'] for x in rr),charged_search_wavelength_layer_updates=sum(x['total_search_wavelength_layer_updates_charged'] for x in rr),actual_shared_screen_calls=shared_calls,actual_shared_screen_wavelength_layer_updates=shared_updates,actual_refinement_calls=ref_calls,actual_refinement_wavelength_layer_updates=ref_updates,actual_search_calls=shared_calls+ref_calls,actual_search_wavelength_layer_updates=shared_updates+ref_updates,base_training_setup_calls=len(r['bases']),base_training_setup_wavelength_layer_updates=len(r['bases'])*162*6,auxiliary_identity_matrix_calls=sum(x['auxiliary_identity_matrix_calls'] for x in r['pool_construction_statistics'].values()),auxiliary_identity_wavelength_layer_updates=sum(x['auxiliary_identity_wavelength_layer_updates'] for x in r['pool_construction_statistics'].values()),independent_final_audit_cost=ac,global_training_false_passes=falseglobal,frozen_P_training_false_passes=falseP,maximum_matrix_recursion_audit_error=max(x['matrix_recursion_max_error'] for x in audits),protected_short_initial_pool_feasible_count=sum(p['screen_score'][0]<=1e-12 for k,v in r['pools'].items() if k.startswith('protected_short_window:') for p in v),protected_short_local_terminal_P_feasible_count=sum(x['final_P_violation']<=1e-12 for x in selected if x['case']=='protected_short_window'))
    (ROOT/'results/diagnostics.json').write_text(json.dumps(diagnostics,indent=2))
    table='\n'.join('| '+ ' | '.join([x['method'],f"{x['global_R_min']*100:.4f}",f"{x['global_R_median']*100:.4f}",f"{x['global_R_max']*100:.4f}",f"{x['protected_R_median']*100:.4f}",str(x['short_preserved_long_improved'])+'/4'])+' |' for x in summ if x['case']=='protected_short_window')
    costtable='\n'.join('| '+ ' | '.join([case,str(seed),str(next(x['screen_calls'] for x in rr if x['case']==case and x['seed']==seed)),str(next(x['total_search_stack_calls_charged'] for x in rr if x['case']==case and x['seed']==seed)),str(next(x['total_search_wavelength_layer_updates_charged'] for x in rr if x['case']==case and x['seed']==seed))])+' |' for case in r['bases'] for seed in (11,29,47,83))
    text=f'''# 有限近恒等保护层包：小预算实测与失败记录

日期：2026-10-19。性质：原创研究试验；非真实材料设计、非主软件功能、非性能优越性证明。本轮未修改主软件，未发布任何仓库。

## 结论先行

在两个六层起点、5种筛选方式、4个配对种子、一次有限1–3层插包和相同局部光学预算下，双连续窗R≤1%的达标数为0/40。从已通过3–5 μm的起点出发，“保住整个短窗并改善长窗”各法均为0/4。所有方法的合格保护档案都只保留原六层，未出现更好的受保护设计。原双窗最佳候选也未被改进。

这只是不支持本轮固定包总厚、狭窄邻域、有限目录和240步随机修复下的优化优势，不能否定完整近恒等包研究方向。局部修复明确采用“先保护P，再降全局违规”的随机词典序规则；它不是精确求解硬保护约束的优化器。

## 1. 先验证真正成立的单点机制

无损法向层满足δ=ℓπ时M=(−1)^ℓI，因此放在任意界面不改变该波长的R/T。我们用原验证过的特征矩阵核，以及独立Fresnel递推，检查n=1.45/2.35、全部7个插入位置，共14组。在λ=4 μm采用一阶半波厚度。

- 中心R最大绝对变化：{max(x['center_abs_R_change'] for x in mech['checks']):.6g}
- 中心T最大绝对变化：{max(x['center_abs_T_change'] for x in mech['checks']):.6g}
- 3–5 μm内R最大绝对变化：{max(x['window_max_abs_R_change'] for x in mech['checks']):.8f}，即45.175个百分点
- 最坏插入后的短窗最大R：{max(x['window_max_R'] for x in mech['checks'])*100:.5f}%，原来仅0.56726%
- 将插入层改为n+0.005i后，中心R/T中性也被破坏。它是明确的合成吸收反例，绝非真实材料数据。

14组逐点检查、精确起始膜厚和折射率均在mechanism_checks.json。单点强度保护不保护连续窗、相位、群时延、斜入射或吸收情形。这里没有把单点机制当作双窗解。

![单点保护失败](figures/center_protection_failure.png)

## 2. 冻结物理模型与要求

空气n₀=1，半无限基片nₛ=3.42，法向、相干、各向同性；材料仅两个无色散合成常数n=1.45、2.35，k=0，无基片背面。两个原始连续窗口始终是3–5、8–12 μm，两窗均要求R≤0.01；窗间无目标。由于无损，T同时检查能量守恒，但没有用R改善暗中代替任何吸收目标。

所有正厚度[0.005,2.5] μm，总厚≤12 μm，合并后的物理层数≤9。相邻同材会合并并检查合并膜厚上限，不能靠拆层绕过上限。真实光学积分仍按名义插入后的6+k层计算，所以成本逐层记数；最终结构同时保存合并前后表示并复算等价性。

起点：

1. protected_short_window：原单窗最优六层，从空气依次L/H/L/H/L/H；3–5 μm最大R=0.567258%，8–12 μm最大R=55.002356%。它真的具有已达标整窗。
2. existing_best_dual_window：原双窗最优六层；3–5 μm最大R≈3.073473%，8–12 μm最大R≈3.216774%。没有任何一个整窗已达1%要求，绝不能把其中某窗称为已合格受保护窗。

两起点精确膜厚固定在results/config.json、run_layer_packs.py。原研究光学核被逐字节复制到verified_kernel/run_experiment.py，SHA-256为{r['config']['kernel_sha256']}，原源文件未修改。

## 3. 同候选池、同层/厚预算的5法比较

种子为11、29、47、83。每个起点×种子先生成同一候选池，含1、2、3层、所有二材料序列、7个界面、精确半波、随机固定总厚、相位网格种子。所有进入光学筛查的包，无论最终拒绝与否，均计入每种方法的筛查成本。

每个包长的总新膜厚固定相同，分别为{r['config']['pack_total_by_length_um']['1']:.9f}、{r['config']['pack_total_by_length_um']['2']:.9f}、{r['config']['pack_total_by_length_um']['3']:.9f} μm。因此不是靠给近恒等法更多层或更多总厚获胜。半波例子中非法的合并厚层先按相同规则排除。

- anchor_identity：按4 μm处到±I的归一化矩阵距离排序，相同距离按真实V/U打破平局。
- multipoint_identity：按3、3.5、4、4.5、5 μm五点最差近恒等距离排序；它仍只是种子评分，不是整窗保护证明。
- random_pack：从完全相同的合法池随机挑选。
- phase_covered：按4 μm处总光学相位模π的0.25、0.75附近覆盖选择，相同距离按真实V打破平局。
- best_V：直接选整个筛查池中真实最大违规V最小的包，作为强对照。

每种方法每个包长选择2包，共6包，每包240次真实光学调用，包含被拒绝的局部试探。每次评估含81点/窗，两窗162点；各法名义层数7/8/9各480次，故点×层成本精确相同。所有方法都可以保留共同完整筛查池中的全局最好候选，避免偷偷让某法多看结果，或只与弱随机对照比较。

固定P为起点在原训练点满足R≤0.008的要求。局部候选按(P最大正违规、全局V、平均正违规平方U)词典序接受；保护优先，但初始不合格候选可逐步减少P违规。新包各层只允许初值±0.25 μm、保持新包总厚严格不变，左右直接旧邻层各±0.18 μm，其余旧层不动。随机扰动逐步缩小，偶尔回到原始种子附近。包长1时因为总厚固定，其新层厚度不能动，只能修邻层。

每法分别保存：全目标V最小档案；P训练要求通过时的保护档案。独立审计决定能否称“保护整窗且改善”。单纯全局V下降但破坏旧窗不会算成功。

## 4. 全结果，含失败

从真正已达标短窗的起点出发，全局最好档案的最坏R如下。它们大幅损坏原短窗，不能解释为成功保护。表中数字为反射率百分数。

| 方法 | 最小R% | 中位R% | 最大R% | 保护档案中位R% | 保短窗且改善长窗 |
|---|---:|---:|---:|---:|---:|
{table}

anchor_identity全局最坏R中位约19.650%，best_V约19.897%，只是一轮极小样本中的轻微差别；两者均不保护短窗，而且两窗1%目标全部失败，所以不能据此声称新法优于强基线。多锚点种子也没有取得保护收益。

以anchor_identity、seed=11为例，全局档案短窗最大R约14.356%，长窗约19.651%，起点短窗为0.567%。它改进了原来55%的最坏长窗，却把旧合格窗损坏。这是必须保留的明确失败案例，而不是“改善成功”。

在已有双窗最佳候选上，所有5法×4种子最终均保留原六层，最坏R仍3.216774%，没有额外包能够带来可归档的改善。此起点两整窗本来就未达标，保护集合只是原来已经有余量的局部要求。

两类起点的全部40行运行在results/results.csv，240条被选包的初始/最终P违规和全局V在results/refinements.csv；完整候选池、局部最佳轨迹、膜厚、层序、独立审计点及峰位置均在results/results.json。没有只展示最好种子。

![同预算比较](figures/paired_seed_results.png)

## 5. 训练、独立审计与成本

所有最终档案分别检查每窗4097个含端点密点、4097个半步偏移点，以及密网格发现的所有局部峰附近的标量有界极值搜索；矩阵核再与独立Fresnel递推比较。原全部目标始终参加最终验收。P另外按“基准R≤0.008”的同一冻结规则，在独立密网格和偏移网格上重建并审查，而非只验证训练P。

- 全部最终审计的矩阵/独立递推最大R差：{diagnostics['maximum_matrix_recursion_audit_error']:.6g}
- 原全目标训练通过而独立审计失败：{falseglobal}；本轮原全目标没有任何训练通过样本，因此0并不代表稀网格永不漏峰。
- 保护档案训练P通过而冻结独立P失败：{falseP}；必须注意这些保护档案大多就是原始栈，不能把它当成新增包成功率。
- 短窗起点池中P通过包总数：{diagnostics['protected_short_initial_pool_feasible_count']}；其所有局部修复终点P通过数：{diagnostics['protected_short_local_terminal_P_feasible_count']}。本轮根本未找到能保住整个已合格短窗的新包。

每个起点×种子，以下单行成本对所有5种方法完全相同；其中局部修复固定1440次，其余是完整共享池筛查。虽然程序实际只筛池一次以复用结果，比较口径给每法都完整计入同一筛查成本。

| 起点 | 种子 | 筛查调用 | 每法搜索调用 | 每法波长×层更新 |
|---|---:|---:|---:|---:|
{costtable}

全部40法次的比较计费搜索调用为{diagnostics['charged_search_calls']:,}，波长×层更新{diagnostics['charged_search_wavelength_layer_updates']:,}。实际共享执行为{diagnostics['actual_search_calls']:,}次（共享筛查{shared_calls:,}＋局部{ref_calls:,}），波长×层更新{diagnostics['actual_search_wavelength_layer_updates']:,}。起点训练、近恒等矩阵评分以及最终审计另外记录在results/diagnostics.json，不混入某法的搜索预算。

独立最终审计共矩阵调用{ac['matrix_stack_calls']:,}次、矩阵波长×层更新{ac['matrix_wavelength_layer_updates']:,}；独立递推调用{ac['independent_recursion_stack_calls']:,}次、波长×层更新{ac['independent_recursion_wavelength_layer_updates']:,}。共享近恒等评分的辅助矩阵波长×层更新{diagnostics['auxiliary_identity_wavelength_layer_updates']:,}。这些不等价于昂贵全谱搜索调用，故单列而非忽略。

程序总墙钟约{r['wall_seconds']:.2f}秒，包含审计和Python开销。墙钟不是硬件独立的速度结论。有限研究预算仅用于公平实验，不是软件产品的默认运行上限。

## 6. 可复现与局限

在本目录执行：

    python mechanism_check.py
    python run_layer_packs.py
    python -m unittest -v test_layer_packs.py
    python analyze_results.py

核心环境：Python3.12、NumPy2.3.5、SciPy1.17.0。仅画图还需Matplotlib，数值复现不依赖图形库。默认使用本包内未改动kernel，也支持run_layer_packs.py --kernel-root指定另一份同源核。不得把本实验随机局部搜索称作全局最优、严格硬约束求解器或原方案的完整实现。

9项一致性测试通过：中心机制/离中心反例、两三层矩阵恒等、同材合并上限、池确定性与固定总厚、原目标冻结、完整40运行、精确配对成本、全部审计/边界、kernel来源及单个240步修复精确回放。test_report.txt保留原始测试日志。

限制包括：仅两种理想无损常数材料；只做一次插包，不做整轮删包/搬移或从空栈端到端搜索；包总厚被固定；只修包与邻层；窄信赖域和240步随机局部修复可能没有找到存在的可行保护包；只4个种子，不能做稳定统计优势判断。密点和局部峰检查不是连续区间的严格数学保证，未测斜入射、误差鲁棒性、真实吸收或制造数据。

后续若要检验完整方向，应独立放宽总厚/修复邻域并加入严格约束的厚度优化器，同时给强基线同等自由度和实际光学预算。当前应保留失败，不靠继续叠策略、换目标或补挑种子制造胜利。
'''
    (ROOT/'研究报告.md').write_text(text)
    print(json.dumps(diagnostics,indent=2))
if __name__=='__main__':main()
