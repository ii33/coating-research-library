#!/usr/bin/env python3
"""Post-hoc audit, attribution, paired comparison and deterministic replay."""
from pathlib import Path
import argparse,csv,json,platform,time
import numpy as np
import run_hybrid as h


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',default='results');ap.add_argument('--replay',action='store_true');args=ap.parse_args()
    out=h.ROOT/args.input;raw=json.loads((out/'results.json').read_text());rs=raw['results'];audit=[];replays=[];pairs=[]
    for i,r in enumerate(rs):
        best=dict(r);best['thickness_um']=r['best_aggregate_thickness_um'];a=h.audit(best,4097)
        d={'case':r['case']['name'],'method':r['method'],'seed':r['seed'],'archive_worst_R':r['audit']['angle_envelope_dense_worst_R'],'aggregate_worst_R':a['angle_envelope_dense_worst_R'],'archive_max_violation':r['audit']['max_standardized_violation'],'aggregate_max_violation':a['max_standardized_violation'],'delta_archive_minus_aggregate_worst_R':r['audit']['angle_envelope_dense_worst_R']-a['angle_envelope_dense_worst_R'],'aggregate_audit_point_solves':a['audit_point_solves_both_kernels'],'aggregate_audit_seconds':a['audit_seconds']};audit.append(d)
        if args.replay and r['seed']==11:
            s=h.run(r['case'],r['method'],r['seed'],r['budget'],r['train_points_per_window']);replays.append({'case':r['case']['name'],'method':r['method'],'seed':r['seed'],'thickness_bitwise_equal':r['thickness_um']==s['thickness_um'],'training_loss_bitwise_equal':r['training_loss_of_selected']==s['training_loss_of_selected'],'counts_equal':r['actual_objective_calls']==s['actual_objective_calls'],'stage_counts_equal':r['stage_counts']==s['stage_counts']});print('replayed',r['case']['name'],r['method'],replays[-1],flush=True)
    for name in sorted({r['case']['name'] for r in rs}):
        for left,right in [('local_de_local','classic_local'),('local_de_local','probe_local'),('de_local','classic_de'),('classic_local','random_local')]:
            aa={r['seed']:r for r in rs if r['case']['name']==name and r['method']==left};bb={r['seed']:r for r in rs if r['case']['name']==name and r['method']==right};seeds=sorted(aa.keys()&bb.keys());delta=[100*(aa[s]['audit']['angle_envelope_dense_worst_R']-bb[s]['audit']['angle_envelope_dense_worst_R']) for s in seeds]
            pairs.append({'case':name,'left':left,'right':right,'seeds':seeds,'left_minus_right_worst_R_percentage_points':delta,'median_delta_percentage_points':float(np.median(delta)),'left_wins_tolerance_1e-8':sum(d<-1e-8 for d in delta),'right_wins_tolerance_1e-8':sum(d>1e-8 for d in delta),'ties':sum(abs(d)<=1e-8 for d in delta)})
    (out/'archive_vs_aggregate.json').write_text(json.dumps(audit,indent=2));(out/'paired_comparisons.json').write_text(json.dumps(pairs,indent=2));(out/'replay.json').write_text(json.dumps(replays,indent=2))
    rows=[]
    for r in rs:
        rows.append({'case':r['case']['name'],'method':r['method'],'seed':r['seed'],'worst_R_percent':100*r['audit']['angle_envelope_dense_worst_R'],'trained_angles_worst_R_percent':100*r['audit']['trained_angles_dense_worst_R'],'min_entering_flux':r['audit']['min_entering_flux'],'pass':r['audit']['angle_envelope_dense_pass'],'actual_calls':r['actual_objective_calls'],'optical_point_solves':r['actual_optical_point_solves'],'optimization_seconds':r['wall_seconds_optimization_only'],'audit_seconds':r['audit']['audit_seconds'],'total_thickness_um':r['total_thickness_um'],'max_kernel_abs_error':r['audit']['independent_matrix_max_abs_error']})
    with (out/'runs.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    summary={'run_count':len(rs),'successful_designs':sum(r['audit']['angle_envelope_dense_pass'] for r in rs),'actual_objective_calls':sum(r['actual_objective_calls'] for r in rs),'actual_optical_point_solves':sum(r['actual_optical_point_solves'] for r in rs),'optimization_seconds_sum':sum(r['wall_seconds_optimization_only'] for r in rs),'independent_audit_point_solves_sum':sum(r['audit']['audit_point_solves_both_kernels'] for r in rs),'independent_kernel_max_abs_error':max(r['audit']['independent_matrix_max_abs_error'] for r in rs),'max_trained_vs_angle_envelope_R_delta':max(r['audit']['angle_envelope_dense_worst_R']-r['audit']['trained_angles_dense_worst_R'] for r in rs),'archive_improves_R_over_aggregate_count':sum(a['delta_archive_minus_aggregate_worst_R']<-1e-10 for a in audit),'archive_worsens_R_over_aggregate_count':sum(a['delta_archive_minus_aggregate_worst_R']>1e-10 for a in audit),'archive_ties_R_over_aggregate_count':sum(abs(a['delta_archive_minus_aggregate_worst_R'])<=1e-10 for a in audit),'max_archive_worsening_R_percentage_points':100*max(a['delta_archive_minus_aggregate_worst_R'] for a in audit),'max_archive_improvement_R_percentage_points':-100*min(a['delta_archive_minus_aggregate_worst_R'] for a in audit),'all_replays_equal':all(all(v for k,v in a.items() if k.endswith('equal')) for a in replays) if replays else None}
    (out/'analysis_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
    # Plot every method's median seed selected by dense worst R, not the best seed.
    import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
    colors=dict(zip(h.METHODS,['#2457a5','#ac6b27','#a83645','#257c67','#6744a0','#4b6673']))
    names=sorted({r['case']['name'] for r in rs});fig,axes=plt.subplots(len(names),2,figsize=(12,3*len(names)),squeeze=False)
    for i,name in enumerate(names):
        for method in h.METHODS:
            xs=sorted([r for r in rs if r['case']['name']==name and r['method']==method],key=lambda r:r['audit']['angle_envelope_dense_worst_R'])
            if not xs:continue
            r=xs[len(xs)//2];case=r['case'];mats,sub=h.materials(case);angs=[0.] if len(case['angles'])==1 else np.arange(0,46,5).tolist()
            for j,(lo,hi) in enumerate(h.WINDOWS):
                wl=np.linspace(lo,hi,501);model=h.OpticalModel(wl,mats,sub,angs);R,P=model.solve(r['thickness_um']);axes[i,j].plot(wl,100*R.max(axis=0),label=f'{method} (seed {r["seed"]})',color=colors[method],lw=1.6)
        for j in range(2):
            axes[i,j].axhline(1,color='black',ls=':',lw=1);axes[i,j].set_title(name+' / '+('3–5' if j==0 else '8–12')+' um');axes[i,j].set_xlabel('Wavelength (um)');axes[i,j].set_ylabel('Angle/polarization max R (%)');axes[i,j].grid(alpha=.15)
        axes[i,1].legend(fontsize=7,loc='upper right')
    fig.tight_layout();fig.savefig(out/'median_spectra.png',dpi=160);plt.close(fig)
    fig,axs=plt.subplots(2,2,figsize=(12,8));
    for ax,name in zip(axs.ravel(),names):
        for method in h.METHODS:
            xs=[r for r in rs if r['case']['name']==name and r['method']==method]
            if not xs:continue
            grid=np.arange(1,xs[0]['budget']+1);vv=[]
            for r in xs:
                rec=r['trace'];idx=np.searchsorted([a['calls'] for a in rec],grid,side='right')-1;vv.append(np.array([rec[max(0,k)]['max_standardized_violation'] for k in idx]))
            ax.semilogy(grid,np.maximum(1e-10,np.median(vv,axis=0)),label=method,color=colors[method])
        ax.set_title(name);ax.set_xlabel('Actual objective calls (includes finite differences)');ax.set_ylabel('Training max normalized violation');ax.grid(alpha=.15)
    axs[0,0].legend(fontsize=7);fig.tight_layout();fig.savefig(out/'median_convergence.png',dpi=160);plt.close(fig)
if __name__=='__main__':main()
