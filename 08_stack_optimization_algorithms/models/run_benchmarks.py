#!/usr/bin/env python3
"""Offline deterministic T08 first-pass benchmark. Wall timings are observations.
Run from any cwd: OPENBLAS_NUM_THREADS=1 python models/run_benchmarks.py
"""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/t08-matplotlib')
from pathlib import Path
import sys,json,time,platform,hashlib,csv,resource,tracemalloc
import numpy as np
import scipy
from scipy.optimize import differential_evolution
from optimization_core import *
ROOT=Path(__file__).resolve().parents[1]


def cases():
    return {
      'B01':dict(seed='E02',bands=[Band('AR',3.5,4.5,'R',0,.03)],angles=[0,30],hold=[0,7.5,15,22.5,30],stress=[45],bounds=(.4,1.6)),
      'B02':dict(seed='E04',bands=[Band('HR',9,11,'R',1,.02)],angles=[0,45],hold=[0,11.25,22.5,33.75,45],stress=[60],bounds=(.55,1.45)),
      'B03':dict(seed='E05',bands=[Band('pass',1.059,1.069,'T',1,.05,1),Band('left_block',.97,1.,'T',0,.03,.3),Band('right_block',1.13,1.16,'T',0,.03,.3)],angles=[0,5],hold=[0,1.25,2.5,3.75,5],stress=[10,30],bounds=(.75,1.25))}


def main():
    start=time.perf_counter();seeds,_=load_examples();cs=cases();out=dict(status='synthetic_reference_optimization_not_measured',schema_version='1.0',seed=20261002,environment=dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__,platform=platform.platform(),thread_env={k:os.getenv(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']}),cases={},extra={})
    configs={}
    for name,c in cs.items():
        seed=seeds[c['seed']];d0=np.array([l['thickness_um'] for l in seed['layers']]);runs={}
        configs[name]=dict(source_seed=c['seed'],bands=[vars(x) for x in c['bands']],train_points=31,coarse_points=5,train_angles=c['angles'],holdout_points_per_band=601,holdout_angles=c['hold'],stress_angles=c['stress'],bounds_scaled=c['bounds'])
        for mode,label,points,limit in [('analytic','accurate',31,60),('finite_difference','finite_difference',31,60),('analytic','quick',5,10),('lbfgsb','lbfgsb',31,60)]:
            p=Problem(seed,c['bands'],points,c['angles']);r=solve(p,bounds=c['bounds'],mode=mode,max_nfev=limit)
            r['holdout']=evaluate_metrics(seed,r['thickness_um'],c['bands'],601,c['hold'])
            r['dense_same_angles']=evaluate_metrics(seed,r['thickness_um'],c['bands'],601,c['angles'])
            r['stress']=evaluate_metrics(seed,r['thickness_um'],c['bands'],601,c['stress'])
            r['constraints']=manufacturing_violations(r['thickness_um'],.03,total_max=np.inf)
            runs[label]=r
            print(name,label,'cost',r['cost'],'hold',r['holdout']['cost'],'sec',r['seconds'],'calls',r['budget']['spectrum_calls'],flush=True)
        # coarse candidate then full training grid. Validation kept independent.
        p=Problem(seed,c['bands'],31,c['angles']);r=solve(p,runs['quick']['x'],c['bounds'],max_nfev=45)
        r['seconds_total']=runs['quick']['seconds']+r['seconds'];r['combined_spectrum_calls']=runs['quick']['budget']['spectrum_calls']+r['budget']['spectrum_calls']
        r['holdout']=evaluate_metrics(seed,r['thickness_um'],c['bands'],601,c['hold']);runs['coarse_then_polish']=r
        init=evaluate_metrics(seed,d0,c['bands'],601,c['hold'])
        _,J=p.evaluate(r['x'],True);sv=np.linalg.svd(J,compute_uv=False)
        out['cases'][name]=dict(seed=c['seed'],initial_thickness_um=d0.tolist(),initial_holdout=init,runs=runs,jacobian_singular_values=sv.tolist())
        # spectra retain initial / accurate / quick at training edge and held-out middle angle
        mats=load_examples()[1]
        for band in c['bands']:
            w=np.linspace(band.lo,band.hi,601);n=[1]+[material(mats[l['material']],w) for l in seed['layers']]+[material(mats[seed['substrate']],w)]
            data={'wavelength_um':w}
            for label,d in [('initial',d0),('accurate',runs['accurate']['thickness_um']),('quick',runs['quick']['thickness_um'])]:
                for a in [c['hold'][2],c['angles'][-1]]:
                    for pol in ('s','p'):
                        z=optics.recursive(w,n,d,a,pol)
                        for field in ['R','T','A']:data[f'{label}_{a:g}_{pol}_{field}']=z[field]
            write_csv(ROOT/'data/spectra'/f'{name}_{band.name}.csv',data)
    # Global search on B01: repeated starts, sampled grid and bounded DE, no guarantee.
    c=cs['B01'];seed=seeds[c['seed']];rng=np.random.default_rng(20261002);rows=[]
    for k,x in enumerate([np.ones(2)]+[rng.uniform(.4,1.6,2) for _ in range(5)]):
        p=Problem(seed,c['bands'],21,c['angles']);r=solve(p,x,c['bounds'],max_nfev=50);r['start']=x.tolist();rows.append(r)
    p=Problem(seed,c['bands'],21,c['angles']);ts=time.perf_counter();grid=[]
    for x in np.ndindex(41,41):
        xx=.4+np.array(x)*1.2/40;r=p.forward_fun(xx);grid.append((float(.5*r@r),xx.tolist()))
    best=min(grid,key=lambda z:z[0]);grid_record=dict(best_cost=best[0],best_x=best[1],candidate_count=len(grid),seconds=time.perf_counter()-ts,budget=p.budget(),continuous_global_optimum_certified=False)
    p=Problem(seed,c['bands'],21,c['angles']);ts=time.perf_counter()
    def f(x):r=p.forward_fun(x);return .5*r@r
    de=differential_evolution(f,[(.4,1.6)]*2,rng=np.random.default_rng(20261002),popsize=8,maxiter=18,polish=False,updating='immediate',tol=1e-8)
    out['extra']['global_search']=dict(multistart=rows,grid=grid_record,DE=dict(cost=float(de.fun),x=de.x.tolist(),nfev=int(de.nfev),seconds=time.perf_counter()-ts,budget=p.budget(),success=bool(de.success),message=de.message))
    # Derivative validation across step sizes and energy derivatives.
    grad=[]
    for bid in cs:
        c=cs[bid];p=Problem(seeds[c['seed']],c['bands'],11,c['angles']);x=np.ones(len(p.d0));r,J=p.evaluate(x,True)
        for h in [1e-2,1e-3,1e-4,1e-5,1e-6,1e-7,1e-8]:
            ts=time.perf_counter();fd=np.column_stack([(p.forward_fun(x+h*np.eye(len(x))[j])-p.forward_fun(x-h*np.eye(len(x))[j]))/(2*h) for j in range(len(x))])
            grad.append(dict(case=bid,step_scaled=h,max_abs_error=float(np.max(abs(fd-J))),relative_fro_error=float(np.linalg.norm(fd-J)/max(np.linalg.norm(J),1e-30)),seconds=time.perf_counter()-ts))
    out['extra']['gradient_check']=grad
    # Finite-band counterexample: both train endpoints are transparent FP resonances.
    w=np.linspace(1.,1.2,20001);n=[1,3.5,1];d=[3/3.5]
    z=optics.recursive(w,n,d);coarse=optics.recursive([1.,1.2],n,d)
    out['extra']['undersampling']=dict(material_status='synthetic constant n=3.5, air both sides',thickness_um=d[0],train_wavelengths=[1.,1.2],train_max_R=float(max(coarse['R'])),dense_max_R=float(max(z['R'])),dense_argmax_um=float(w[np.argmax(z['R'])]),dense_points=len(w),continuous_bound_claim=False)
    write_csv(ROOT/'data/spectra/undersampling.csv',dict(wavelength_um=w[::10],R=z['R'][::10]))
    # Overfitting angle: B03 zero-degree-only optimization versus multi-angle holdout.
    c=cs['B03'];seed=seeds[c['seed']];p=Problem(seed,c['bands'],21,[0]);r=solve(p,bounds=c['bounds'],max_nfev=40)
    r['training_angle_holdout']=evaluate_metrics(seed,r['thickness_um'],c['bands'],601,[0]);r['angle_holdout']=evaluate_metrics(seed,r['thickness_um'],c['bands'],601,[2.5,5,10]);out['extra']['angle_overfit']=r
    # Scenario robustness: expectation over deterministic common-mode +-1%, not yield.
    factors=np.array([np.full(17,v) for v in [.99,1,1.01]])
    p=Problem(seed,c['bands'],13,c['angles'],factors=factors);r=solve(p,out['cases']['B03']['runs']['accurate']['x'],c['bounds'],max_nfev=30)
    holdf=1+rng.normal(0,.006,(64,1))+rng.normal(0,.003,(64,17))
    robust_eval={}
    for label,dv in [('nominal',out['cases']['B03']['runs']['accurate']['thickness_um']),('robust',r['thickness_um'])]:
        costs=[];worsts=[]
        for ff in holdf:
            ev=evaluate_metrics(seed,dv,c['bands'],121,[0,2.5,5],factors=[ff]);costs.append(ev['cost']);worsts.append(ev['sample_worst_normalized_target_error'])
        robust_eval[label]=dict(mean_cost=float(np.mean(costs)),quantile95_cost=float(np.quantile(costs,.95)),max_cost=float(max(costs)),mean_worst=float(np.mean(worsts)),all_scenario_costs=costs)
    out['extra']['robustness']=dict(fit=r,training_factors=[.99,1,1.01],holdout_scenarios=64,holdout_common_sigma=.006,holdout_independent_sigma=.003,distribution_status='illustrative_unmeasured_not_yield',comparison=robust_eval)
    # Finite needle insertion on E02, add vs replace and mandatory min thickness.
    c=cs['B01'];seed=seeds[c['seed']];d=np.array(out['cases']['B01']['runs']['accurate']['thickness_um']);needle=[]
    base=evaluate_metrics(seed,d,c['bands'],81,c['angles'])['cost']
    for mode in ['add','replace']:
        for host in range(2):
            newmat='ZnS_IR_proxy' if host==0 else 'YbF3_MWIR_proxy'
            for frac in [.25,.5,.75]:
                costs=[]
                for h in [1e-6,.03,.10]:
                    sn,dn=insert_layer(seed,d,host,frac,newmat,h,mode)
                    val=evaluate_metrics(sn,dn,c['bands'],81,c['angles'])['cost'];costs.append(val)
                needle.append(dict(mode=mode,host=host,position_fraction=frac,material=newmat,needle_slope_per_um=(costs[0]-base)/1e-6,finite_30nm_cost=costs[1],finite_100nm_cost=costs[2]))
    chosen=min(needle,key=lambda v:v['finite_30nm_cost']);sn,dn=insert_layer(seed,d,chosen['host'],chosen['position_fraction'],chosen['material'],.03,chosen['mode'])
    p=Problem(sn,c['bands'],31,c['angles']);refined=solve_constrained(p,np.ones(len(dn)),total_max_um=1.0,d_min_um=.03,maxiter=60)
    refined['holdout']=evaluate_metrics(sn,refined['thickness_um'],c['bands'],601,c['hold'])
    out['extra']['needle']=dict(accepted=bool(refined['holdout']['cost'] < out['cases']['B01']['runs']['accurate']['holdout']['cost'] and max(refined['violations'].values())<=1e-8),base_cost=base,candidates=needle,chosen=chosen,refined=refined,refined_seed=sn,total_cap_um=1.0)
    # Thickness epsilon constraints show a real tradeoff instead of one mixed score.
    trade=[]
    for cap in [.50,.60,.75,1.0]:
        p=Problem(seed,c['bands'],31,c['angles']);xx=np.array(out['cases']['B01']['runs']['accurate']['x']);xx*=min(1,cap/(xx@p.scale_d))
        rr=solve_constrained(p,xx,cap,d_min_um=.03);rr['cap_um']=cap;rr['holdout']=evaluate_metrics(seed,rr['thickness_um'],c['bands'],401,c['hold']);trade.append(rr)
    out['extra']['thickness_tradeoff']=trade
    # Local surrogate: seed -> accepted actual-model decreases, no ML claims.
    p=Problem(seed,c['bands'],31,c['angles']);sur=trust_region_surrogate(p,np.ones(2),steps=16)
    sur['holdout']=evaluate_metrics(seed,sur['thickness_um'],c['bands'],601,c['hold']);out['extra']['surrogate']=sur
    # Update target band using saved x; context changes => NEW cache.
    newbands=[Band('AR_updated',3.6,4.6,'R',0,.03)];warmcold={}
    for label,x in [('cold',np.ones(2)),('warm',out['cases']['B01']['runs']['accurate']['x'])]:
        p=Problem(seed,newbands,31,[0,30]);rr=solve(p,x,max_nfev=60);rr['holdout']=evaluate_metrics(seed,rr['thickness_um'],newbands,601,[0,15,30]);warmcold[label]=rr
    out['extra']['warm_start']=warmcold
    # Exact nonidentifiability: identical adjacent layers can trade thickness.
    w=np.linspace(1.3,1.7,41);z=spectrum_jacobian(w,[1,1.5,1.5,2.1],[.2,.3]);sv=np.linalg.svd(z['JR'],compute_uv=False)
    shift=optics.recursive(w,[1,1.5,1.5,2.1],[.27,.23])
    out['extra']['nonidentifiability']=dict(singular_values=sv.tolist(),spectrum_error_for_redistribution=float(max(abs(z['R']-shift['R']))),null_direction=[1,-1])
    # B03 extended accuracy route. Budgeted separately from equal-60-call trial.
    c=cs['B03'];seed=seeds[c['seed']];p=Problem(seed,c['bands'],61,c['angles'])
    rr=solve(p,out['cases']['B03']['runs']['coarse_then_polish']['x'],c['bounds'],max_nfev=240)
    rr['holdout']=evaluate_metrics(seed,rr['thickness_um'],c['bands'],1201,c['hold'])
    out['extra']['extended_precision_B03']=rr
    # Derivative throughput and Python-managed peak memory; 7 timing samples.
    perf=[]
    for L in [2,10,17,80]:
        w=np.linspace(1,1.2,61);n=[1]+[2.1 if j%2 else 1.45 for j in range(L)]+[1.52];d=np.full(L,.1)
        for label,fun in [('prefix_suffix',spectrum_jacobian),('forward_all_directions',spectrum_jacobian_forward)]:
            times=[]
            for _ in range(7):
                ts=time.perf_counter();zz=fun(w,n,d,45,'p');times.append(time.perf_counter()-ts)
            tracemalloc.start();fun(w,n,d,45,'p');_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
            perf.append(dict(layers=L,wavelengths=61,mode=label,seconds_samples=times,median_seconds=float(np.median(times)),peak_python_allocated_bytes=peak))
    out['extra']['kernel_performance']=perf
    out['peak_process_rss_kib_linux']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    out['elapsed_seconds']=time.perf_counter()-start
    (ROOT/'data/benchmark_config.json').write_text(json.dumps(configs,indent=2)+'\n')
    (ROOT/'data/benchmark_results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    (ROOT/'data/checkpoints.json').write_text(json.dumps({bid:dict(x=v['runs']['accurate']['x'],thickness_um=v['runs']['accurate']['thickness_um'],source_seed=v['seed'],context_fingerprint=v['runs']['accurate']['context_fingerprint']) for bid,v in out['cases'].items()},indent=2)+'\n')
    print('FINISHED seconds',out['elapsed_seconds'],flush=True)


def write_csv(path,data):
    with path.open('w') as f:
        wr=csv.writer(f);wr.writerow(data.keys());wr.writerows(zip(*data.values()))
if __name__=='__main__':main()
