"""Assess predefined successive-change criteria; no new forward calls."""
from pathlib import Path
import hashlib
import json
import math

HERE=Path(__file__).resolve().parent


def axis_assessment(rungs, reference_gap, metric, fraction=.2):
    """Observed-change screening, explicitly not a rigorous numerical bound."""
    if len(rungs)<3:
        return {"passed":False,"reason":"Fewer than three refinement levels"}
    pairs=[(r['methods']['nominal'][metric],r['methods']['robust'][metric]) for r in rungs]
    gaps=[b-a for a,b in pairs]
    threshold=fraction*min(abs(gaps[-1]),abs(reference_gap))
    mean_changes={mode:[abs(pairs[i][j]-pairs[i-1][j]) for i in range(len(pairs)-2,len(pairs))]
                  for j,mode in enumerate(('nominal','robust'))}
    gap_changes=[abs(gaps[i]-gaps[i-1]) for i in range(len(gaps)-2,len(gaps))]
    signs=[math.copysign(1,g) if g else 0 for g in gaps[-3:]]
    stable=signs[0]!=0 and len(set(signs))==1
    passed=threshold>0 and stable and max(gap_changes)<threshold and all(max(x)<threshold for x in mean_changes.values())
    return {"passed":bool(passed),"threshold_pp":threshold,"gaps_pp":gaps,
            "last_two_method_mean_changes_pp":mean_changes,
            "last_two_gap_changes_pp":gap_changes,"last_three_gap_signs_stable":stable,
            "reason":"Passed observed-change screen" if passed else "Observed changes too large relative to method gap, or rank unstable"}


def phase_assessment(rungs, reference_gap, metric, fraction=.2):
    if len(rungs)!=3:
        return {"passed":False,"reason":"Missing node-origin offset"}
    pairs=[(r['methods']['nominal'][metric],r['methods']['robust'][metric]) for r in rungs]
    gaps=[b-a for a,b in pairs]
    threshold=fraction*min(abs(gaps[1]),abs(reference_gap))
    spreads={mode:max(p[j] for p in pairs)-min(p[j] for p in pairs)
             for j,mode in enumerate(('nominal','robust'))}
    signs=[math.copysign(1,g) if g else 0 for g in gaps]
    return {"passed":threshold>0 and all(v<threshold for v in spreads.values()) and len(set(signs))==1 and signs[0]!=0,
            "threshold_pp":threshold,"method_mean_phase_spread_pp":spreads,
            "gaps_pp":gaps,"gap_phase_spread_pp":max(gaps)-min(gaps),
            "phase_rank_stable":len(set(signs))==1 and signs[0]!=0}


def case_for(level,seed,uncertainty):
    return next(c for c in level['cases'] if c['seed']==seed and c['level']==uncertainty)


def main():
    p=json.loads((HERE/'followup_results.json').read_text())
    cfg=p['config'];assessments=[]
    for case in cfg['cases']:
        seed,level=case['seed'],case['level'];ref=cfg['reference_full16_gap_pp'][f'{level}_{seed}']
        a={'seed':seed,'level':level,'axes':{},'phase':{}}
        for axis in ('time','grid','source'):
            rungs=[case_for(p['levels'][key],seed,level) for key in p['axis_keys'].get(axis,[])]
            a['axes'][axis]={domain:axis_assessment(rungs,ref,metric,cfg['acceptance']['relative_fraction'])
                for domain,metric in (('full_disk','mean_cv_percent'),('interior90','mean_interior90_cv_percent'))}
        for n in cfg['phase_test_time_steps']:
            levels=[p['levels'][key] for key in p['axis_keys'].get('phase',[]) if p['levels'][key]['resolution']['time_steps']==n]
            levels.sort(key=lambda v:v['alpha'])
            rungs=[case_for(v,seed,level) for v in levels]
            a['phase'][str(n)]={domain:phase_assessment(rungs,ref,metric,cfg['acceptance']['relative_fraction'])
                for domain,metric in (('full_disk','mean_cv_percent'),('interior90','mean_interior90_cv_percent'))}
        a['all_axes_and_phase_pass']=all(d['passed'] for axis in a['axes'].values() for d in axis.values()) and all(d['passed'] for n in a['phase'].values() for d in n.values())
        assessments.append(a)
    (HERE/'acceptance_results.json').write_text(json.dumps(assessments,indent=2)+'\n')
    lines=['# 数值跟进：分离积分、网格与有限源采样','',
        '2026-10-05 UTC · 固定设计 · 首轮交付文件只读','',
        '## 结论','',
        '低时间节点数是本次观察到的最大变化来源。固定 grid41/source25、同一设计和同一四个扰动，1% 名义平均 CV 从 96 节点的 0.63406% 降到 1536 节点的 0.38823%。5%/seed29 方法排序仅改变时间节点数就反转，96 节点 robust−nominal 为 −0.00981 百分点，192/384/768/1536 节点变为 +0.02103/+0.03452/+0.03550/+0.03746 百分点。','',
        '这是已选设计和固定四情景的数值诊断；不是重新独立验证、没有重新优化，也不能泛化为总体可靠性。所有轴的接受状态见下表，未通过的轴不升级为收敛。','',
        '## 预设接受条件','',
        '阈值 = 0.2×min(当前固定四情景的方法均值 CV 差绝对值，首轮 16 情景加密方法差绝对值)。时间/网格/源每一轴最后两次加密，两方法的均值改变及方法差改变都须小于阈值，且最后三档排名同号。完整表示面域和固定90-mm内部区域都检查。节点原点相位探针要求两方法均值的三种采样偏移极差也小于阈值且排名稳定。','',
        '这只是与待比较差幅有关的观察变化筛查，绝不是严密误差界。只有几个离散等级，二值遮挡可能有混叠，未知误差可能超过相邻档差值；不能声称真实物理精度。','',
        '|扰动/种子|轴|完整表示面域|固定内部90 mm|完整域阈值/百分点|','|---|---|---|---|---:|']
    for a in assessments:
        for axis,d in a['axes'].items():
            lines.append(f"|{a['level']:.0%}/{a['seed']}|{axis}|{'pass' if d['full_disk']['passed'] else 'unresolved'}|{'pass' if d['interior90']['passed'] else 'unresolved'}|{d['full_disk'].get('threshold_pp',0):.6f}|")
        for n,d in a['phase'].items():
            lines.append(f"|{a['level']:.0%}/{a['seed']}|node origin, N={n}|{'pass' if d['full_disk']['passed'] else 'unresolved'}|{'pass' if d['interior90']['passed'] else 'unresolved'}|{d['full_disk'].get('threshold_pp',0):.6f}|")
    lines+=['','## 各轴原始数值','',
        '全部平均仅为相同四个留出情景，零扰动另存，不混入其均值。差为 robust−nominal，负数有利于稳健。','',
        '|轴|grid/time/source nodes|α|扰动/种子|名义均值 CV %|稳健均值 CV %|差/百分点|内部90-mm差/百分点|','|---|---|---|---|---:|---:|---:|---:|']
    csv=['axis,grid,time,source_order,alpha,level,seed,nominal_mean_cv_percent,robust_mean_cv_percent,gap_pp,interior90_gap_pp,actual_calls,wall_s']
    for axis,keys in p['axis_keys'].items():
        for key in keys:
            lev=p['levels'][key];res=lev['resolution']
            for c in lev['cases']:
                x=c['methods']['nominal'];y=c['methods']['robust'];gap=y['mean_cv_percent']-x['mean_cv_percent'];igap=y['mean_interior90_cv_percent']-x['mean_interior90_cv_percent']
                lines.append(f"|{axis}|{res['grid_size']}/{res['time_steps']}/{res['source_order']**2}|{lev['alpha']}|{c['level']:.0%}/{c['seed']}|{x['mean_cv_percent']:.6f}|{y['mean_cv_percent']:.6f}|{gap:+.6f}|{igap:+.6f}|")
                csv.append(','.join(map(str,[axis,res['grid_size'],res['time_steps'],res['source_order'],lev['alpha'],c['level'],c['seed'],x['mean_cv_percent'],y['mean_cv_percent'],gap,igap,lev['actual_forward_calls'],lev['wall_s']])))
    (HERE/'summary.csv').write_text('\n'.join(csv)+'\n')
    lines+=['','## 面域与节点原点解释','',
        '原产品圆盘节点只表示盘内中心单元。full-disk 指这些盘内节点对应的圆盘交集单元；21/41/61 网格的覆盖率约97.52%/98.67%/99.00%，所以该统计面域随网格变化。另计算同一个物理半径90 mm的内部ROI，90-mm边界落在所有网格都完全有代表点的范围内：10-mm内缩大于粗网格方格半对角7.07 mm。全部需要的中心仍在产品100-mm圆盘内，不造盘外值。内部ROI覆盖率约100%，权重来自原字段单元面积；它只是帮助区分边缘面域变化与内部采样，不是用中央区域替换用户全口径要求。','',
        '原核中点为(k+0.5)Δt。设置载盘与行星的初相分别增加6·rpm·δt及6·rpm·(1+120/36)·δt，δt=(α−0.5)Δt，等价于对原物理通量在(k+α)Δt取样。每情景用其真实扰动rpm，α=0.25/0.5/0.75的全部节点仍在原积分窗内部。此处只探测数值求积节点原点，不把结果称为真实启动相位鲁棒性。','',
        '分轴锚点不同：时间轴grid41/source25；网格轴time768/source25；源轴grid41/time768；节点原点在grid41/source25。没有假设各轴误差线性相加，也没有完成最大grid/time/source组合的联合认证。','',
        '## 资源、失败与下一档成本','',
        f"Pilot 8 次真实 cub 调用；主跟进 {p['actual_forward_calls']} 次，墙钟 {p['wall_s']:.2f} s。每唯一档20情景评价（2病例×2方法×[名义+4扰动]），每评价含有板和同场景无板两个实际调用，因此每档40次；相同档在多轴中复用已存结果，未再次计费。测试7项，仅注入常数场/数学身份，共6个模拟调用，不额外执行cub。",'',
        '600-call计数上限是硬约束；600-second墙钟为依据pilot成本逐档允许/跳过的软资源限制，单档没有硬超时中止器。实测和计划均存档，不冒充精确预测。源A仍在相对指标中抵消；没有生产参数或绝对厚度新证据。','']
    failures=sum(m['counter']['failed_forward_calls']+m['counter']['invalid_candidates'] for lev in p['levels'].values() for c in lev['cases'] for m in c['methods'].values())
    lines.append(f"输入/正向失败：{failures}；跳过档：{len(p['skips'])}。首轮文件及产品Python哈希前后均保持一致。")
    pilot=json.loads((HERE/'pilot_results.json').read_text())
    coeff=max(r['wall_s']/(r['resolution']['grid_size']**2*r['resolution']['time_steps']*r['resolution']['source_order']**2) for r in pilot['rows'])
    estimates=[]
    for label,g,n,q in [('time 3072',41,3072,5),('time 6144',41,6144,5),('grid 81',81,768,5),('source order 9',41,768,9),('joint 61/1536/49',61,1536,7)]:
        seconds=coeff*g*g*n*q*q*20
        estimates.append({'setting':label,'grid':g,'time_steps':n,'source_order':q,'actual_forward_calls_if_run':40,'estimated_wall_s':seconds,'status':'not_run'})
        lines.append(f"- 若继续 {label}：同20评价40次调用，按pilot规模外推约{seconds:.1f} s；本次未运行")
    (HERE/'next_level_costs.json').write_text(json.dumps(estimates,indent=2)+'\n')
    lines+=['','必要后续取决于未通过轴：时间轴至少追加3072并视判据决定6144；网格至少81再判断是否要更密；源轴至少9阶。达到各自观察变化阈值后，再做固定最大组合及新独立批次核查。若总体排名小于有限情景、数值或模型误差，不作工程最优建议。本次有界跟进在这些预定轴和资源范围结束。','']
    (HERE/'RESULTS.md').write_text('\n'.join(lines))
    # Freeze only this new directory; do not regenerate the first-round manifest.
    files={str(f.relative_to(HERE)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(HERE.rglob('*')) if f.is_file() and f.name!='artifact_manifest.json' and '__pycache__' not in f.parts}
    (HERE/'artifact_manifest.json').write_text(json.dumps({'files':files,'count':len(files)},indent=2)+'\n')
    print(json.dumps({'assessments':assessments,'files_hashed':len(files)},indent=2))


if __name__=='__main__':
    main()
