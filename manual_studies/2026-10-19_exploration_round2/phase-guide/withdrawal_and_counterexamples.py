#!/usr/bin/env python3
"""Frozen-result true-power-only polishing and diagnostic counterexamples."""
import csv,json,math,time
from pathlib import Path
import numpy as np
from scipy.optimize import root
from run_phase import ROOT,amplitudes,optimize,CASES

def counterexamples():
    cost={'calls':0,'points':0,'point_layers':0}; st=time.perf_counter()
    def counted(wavelengths,thickness,n,*args,**kwargs):
        cost['calls']+=1; cost['points']+=len(wavelengths)
        cost['point_layers']+=len(wavelengths)*max(len(thickness),1)
        return amplitudes(wavelengths,thickness,n,*args,**kwargs)
    ns=3.42; nar=np.sqrt(ns); wl=np.array([4.]); q=4/(4*nar)
    rr=[]
    for delta in [-1e-7,1e-7]:
        r,_=counted(wl,[q+delta],[nar],reference_depth=2.5); rr.append(r[0])
    jump=float(abs(np.angle(rr[1]/rr[0])))
    # Passive absorption: low R no longer implies high T.
    def mismatch(x):
        rr=counted(wl,[x[1]],[x[0]+.2j],reference_depth=2.5)[0][0]
        return [rr.real,rr.imag]
    matched=root(mismatch,[1.65,.65]); assert matched.success
    an,ad=matched.x
    r,t=counted(wl,[ad],[an+.2j],reference_depth=2.5)
    absorption={'n':float(an),'k':.2,'d_um':float(ad),'R':float(abs(r[0])**2),'T':float(3.42*abs(t[0])**2),'A':float(1-abs(r[0])**2-3.42*abs(t[0])**2)}
    # Cavity resonance, with quarterwave mirrors; phase-small is not response-small.
    h,l=3.4,1.45; lam=4.; n=np.array([h,l]*6+[1.]+[l,h]*6)
    d=np.r_[np.array([lam/(4*h),lam/(4*l)]*6),lam/2,np.array([lam/(4*l),lam/(4*h)]*6)]
    r0,t0=counted(wl,d,n,n0=1,ns=1,reference_depth=len(n)*2.5)
    dp=d.copy(); dp[12]+=.0001
    r1,t1=counted(wl,dp,n,n0=1,ns=1,reference_depth=len(n)*2.5)
    highq={'layers':len(n),'cavity_change_um':.0001,'single_layer_phase_change_rad':2*np.pi*.0001/lam,'R_before':float(abs(r0[0])**2),'R_after':float(abs(r1[0])**2),'T_before':float(abs(t0[0])**2),'T_after':float(abs(t1[0])**2)}
    # Overdetermined independent pointwise phase directions cannot generally be realized.
    w=np.r_[np.linspace(3,5,9),np.linspace(8,12,9)]; nn=np.array([1.45,2.35]); dd=np.array([.3,.6]); depth=5.
    rs,_=counted(w,dd,nn,reference_depth=depth); J=np.zeros((len(w),2),complex)
    for j in range(2):
        x=dd.copy(); x[j]+=1e-6; J[:,j]=(counted(w,x,nn,reference_depth=depth)[0]-rs)/1e-6
    desired=1j*np.r_[np.ones(9),-np.ones(9)]*rs*.01
    A=np.r_[J.real,J.imag]; b=np.r_[desired.real,desired.imag]
    step=np.linalg.lstsq(A,b,rcond=None)[0]
    incompatible={'N_variables':2,'real_response_dimensions':len(b),'desired_phase_step_rad':.01,'relative_linear_least_squares_residual':float(np.linalg.norm(A@step-b)/np.linalg.norm(b)),'best_linear_thickness_step_um':step.tolist(),'meaning':'Opposite pointwise guide phases are a search bias, generally not an independently realizable specification.'}
    out={'reflection_zero':{'phase_jump_rad':jump,'max_R':float(max(abs(v)**2 for v in rr)),'meaning':'Opposite thickness perturbations produce nearly pi phase flip at negligible power: arg(r) is ill-conditioned.'},'passive_absorption':absorption,'high_Q':highq,'incompatible_phase_targets':incompatible}
    assert absorption['A']>0 and absorption['T']<.9 and absorption['R']<1e-20
    assert highq['single_layer_phase_change_rad']<1e-3 and abs(highq['R_after']-highq['R_before'])>.5
    assert jump>3. and incompatible['relative_linear_least_squares_residual']>.1
    cost['wall_seconds']=time.perf_counter()-st
    out['cost']=cost
    return out

def main():
    st=time.perf_counter()
    initial=json.loads((ROOT/'results.json').read_text()); rows=[]
    for old in initial['rows']:
        # Identical 12-iteration extra true-power solver and cost for every method.
        r=optimize(old['case'],old['seed'],'direct_local',start_override=old['d_um'],iter_override=12)
        r['raw_polish_V']=r['V']; r['raw_polish_mean_R']=r['mean_R']; r['raw_polish_d_um']=r['d_um']
        r['input_archive_origin_tau']=old['selected_archive_tau']
        r['pure_power_iterations_completed']=len(r['history'])
        r['all_polish_iterations_auxiliary_weight_zero']=all(h['auxiliary_weight']==0. and h['tau']==1. for h in r['history'])
        # Preserve the original physical archive on the SAME dense audit ranking.
        # This post-run choice is not fed back to the optimizer; it is explicit validation selection.
        retain=(r['V'],r['mean_R'])>(old['V'],old['mean_R'])
        r['retained_original_after_common_audit']=retain
        r['delivered_candidate_origin']=('original archived design' if retain or r['d_um']==old['d_um'] else 'new pure-power refinement')
        if retain:
            for key in ['V','mean_R','d_um','per_window','max_energy_error','minimum_A','pass_finite_grid']:
                r[key]=old[key]
        r['original_method']=old['method']; r['before_V']=old['V']; r['combined_point_layers']=old['total']['point_layers']+r['total']['point_layers']; rows.append(r)
    sensitivity=[]
    for seed in [11,29,47]:
        for theta in [0.,math.pi/6,2*math.pi/3]:
            sensitivity.append(optimize('dual_ar',seed,'phase_homotopy',theta_max=theta))
    counter=counterexamples()
    out={'scope':'Post-selection common true-power epigraph polishing, 12 iterations, exactly zero auxiliary weight. Dense final audit used for evaluation and explicit post-run validation selection; never fed back to optimization. Sensitivity is exploratory extra work, not counted in initial 80-iteration budget.','diagnostic_wall_seconds':time.perf_counter()-st,'polished':rows,'counterexamples':counter,'theta_sensitivity':sensitivity}
    (ROOT/'withdrawal_and_counterexamples.json').write_text(json.dumps(out,indent=2))
    fields=['case','seed','original_method','before_V','V','combined_point_layers','runtime_seconds_including_final_audit']
    with (ROOT/'withdrawal.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows({k:r[k] for k in fields} for r in rows)
    print(json.dumps(out['counterexamples'],indent=2))
    for r in rows:
        if r['case']=='dual_ar': print('polish',r['seed'],r['original_method'],r['before_V'],r['V'])
    for r in sensitivity: print('theta',r['seed'],r['theta_max'],r['V'])
if __name__=='__main__': main()
