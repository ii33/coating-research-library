#!/usr/bin/env python3
import argparse,csv,json
from pathlib import Path
import numpy as np
import run_angle_exchange as a

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--replay',action='store_true');args=ap.parse_args();out=a.ROOT/'results';raw=json.loads((out/'results.json').read_text());rs=raw['results'];sources=json.loads((a.ROOT/'seed_sources.json').read_text())['sources'];checks={};replays=[] if args.replay else (json.loads((out/'replay.json').read_text()) if (out/'replay.json').exists() else []);pairs=[];pointchecks=[];reference_R={}
    checks['30_unique_runs']=len(rs)==30 and len({(r['case']['name'],r['seed'],r['method']) for r in rs})==30
    checks['all_point_budgets_respected']=all(r['actual_extra_points']<=r['extra_point_budget'] for r in rs)
    checks['point_and_call_accounts_match']=all(sum(v['points'] for v in r['cost_by_stage'].values())==r['actual_extra_points'] and sum(v['calls'] for v in r['cost_by_stage'].values())==r['actual_extra_optical_calls'] for r in rs)
    checks['reference_archive_never_worsens']=all(r['final_common_reference_max_violation']<=r['initial_common_reference_max_violation'] and all(x['archive_max_violation']<=y['archive_max_violation'] for x,y in zip(r['trace'][1:],r['trace'])) for r in rs)
    maxerr=0.
    for r in rs:
        wl,aa,pp,w=a.grid_queries(np.arange(0,46,5));m=a.PointModel(r['case'],wl,aa,pp);R,P=m.solve(r['thickness_um']);g,v,tie=a.metric(r['case'],R,P,w);reference_R[(r['case']['name'],r['seed'],r['method'])]=float(R.max());maxerr=max(maxerr,abs(v-r['final_common_reference_max_violation']))
        for q in r['extra_constraints']:
            m=a.PointModel(r['case'],[q['wavelength_um']],[q['angle_deg']],[q['pol']]);R,P=m.solve(r['thickness_um']);pointchecks.append({'case':r['case']['name'],'seed':r['seed'],'constraint':q,'final_R':float(R[0]),'drop_R_percentage_points':100*(q['R_when_found']-float(R[0]))})
        if args.replay:
            src=next(s for s in sources if s['case']['name']==r['case']['name'] and s['seed']==r['seed']);s=a.run(src,r['method'],r['extra_point_budget']);replays.append({'case':r['case']['name'],'seed':r['seed'],'method':r['method'],'thickness_bitwise_equal':s['thickness_um']==r['thickness_um'],'points_equal':s['actual_extra_points']==r['actual_extra_points'],'calls_equal':s['actual_extra_optical_calls']==r['actual_extra_optical_calls'],'stage_counts_equal':s['cost_by_stage']==r['cost_by_stage']});print('replayed',replays[-1],flush=True)
    checks['stored_reference_violation_recomputed_exactly']=maxerr==0
    if replays:checks['all30_replays_exact']=len(replays)==30 and all(all(v for k,v in r.items() if k.endswith('equal')) for r in replays)
    for case in ['synthetic10_multi','tabulated6_multi']:
        for baseline in ['original_angles','fixed_dense_angles']:
            ds=[];cost=[]
            for seed in [11,29,47,71,101]:
                x=next(r for r in rs if r['case']['name']==case and r['seed']==seed and r['method']=='angle_exchange');y=next(r for r in rs if r['case']['name']==case and r['seed']==seed and r['method']==baseline);delta=100*(x['audit']['refined_worst_R']-y['audit']['refined_worst_R']);ds.append(delta);cost.append({'seed':seed,'exchange_points':x['actual_extra_points'],'baseline_points':y['actual_extra_points'],'exchange_minus_baseline_R_percentage_points':delta})
            pairs.append({'case':case,'baseline':baseline,'seeds':[11,29,47,71,101],'paired_delta_percentage_points':ds,'median_paired_delta_percentage_points':float(np.median(ds)),'rows':cost})
    summary={'all_consistency_checks_passed':all(checks.values()),'checks':checks,'run_count':len(rs),'success_count':sum(r['audit']['pass'] for r in rs),'extra_point_work_total':sum(r['actual_extra_points'] for r in rs),'extra_optical_calls_total':sum(r['actual_extra_optical_calls'] for r in rs),'continuation_seconds_sum':sum(r['optimization_and_reference_seconds'] for r in rs),'final_independent_audit_grid_points_both_kernels':sum(r['audit']['grid_point_work_both_kernels'] for r in rs),'final_local_refinement_points':sum(r['audit']['local_refinement_points'] for r in rs),'max_independent_kernel_abs_error':max(r['audit']['independent_matrix_max_abs_error'] for r in rs),'exchange_runs_that_added_constraints':sum(bool(r['extra_constraints']) for r in rs if r['method']=='angle_exchange'),'constraints_total':len(pointchecks),'constraint_final_recheck_points':len(pointchecks),'reference_verification_points':3078*len(rs),'max_reference_metric_abs_error':maxerr}
    for name,data in [('paired_comparisons.json',pairs),('constraint_transfer_diagnostics.json',pointchecks),('replay.json',replays),('analysis_summary.json',summary)]: (out/name).write_text(json.dumps(data,indent=2))
    flat=[]
    for r in rs:
        peak=max(r['audit']['local_refinements'],key=lambda q:q['R']);flat.append({'case':r['case']['name'],'seed':r['seed'],'method':r['method'],'refined_worst_R_percent':100*r['audit']['refined_worst_R'],'common_reference_worst_R_percent':100*reference_R[(r['case']['name'],r['seed'],r['method'])],'added_constraints':len(r['extra_constraints']),'actual_extra_points':r['actual_extra_points'],'actual_extra_optical_calls':r['actual_extra_optical_calls'],'seconds':r['optimization_and_reference_seconds'],'peak_angle_deg':peak['angle_deg'],'peak_wavelength_um':peak['wavelength_um'],'peak_pol':peak['pol']})
    with (out/'runs.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
    import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
    fig,axs=plt.subplots(1,2,figsize=(12,4.5));colors={'original_angles':'#b15b25','fixed_dense_angles':'#3475a4','angle_exchange':'#3e8968'}
    for ax,case in zip(axs,['synthetic10_multi','tabulated6_multi']):
        for method in a.METHODS:
            xs=sorted([r for r in rs if r['case']['name']==case and r['method']==method],key=lambda r:r['seed']);ax.plot([str(r['seed']) for r in xs],[100*r['audit']['refined_worst_R'] for r in xs],marker='o',label=method,color=colors[method],alpha=.85)
        ax.axhline(1,color='black',ls=':',lw=1);ax.set_title(case);ax.set_xlabel('Frozen source seed');ax.set_ylabel('Independent grid + local refinement max R (%)');ax.grid(alpha=.15)
    axs[1].legend(fontsize=8);fig.tight_layout();fig.savefig(out/'paired_results.png',dpi=160);plt.close(fig)
    print(json.dumps(summary,indent=2));assert summary['all_consistency_checks_passed']
if __name__=='__main__':main()
