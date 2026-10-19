#!/usr/bin/env python3
"""Finite first-pass, synthetic normal-incidence reflection homotopy falsification.
No data or code from main software. A copied verified kernel is read-only reference.
"""
from __future__ import annotations
import csv, hashlib, json, math, platform, time
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import minimize
from verified_kernel import tmm_normal, reflection_recursion
ROOT=Path(__file__).resolve().parent
TARGET=.01; LOWER=.005; UPPER=2.5; SR=math.sqrt(TARGET)
SEEDS=[11,29,47]; ITER_PER_BRANCH=20
CASES={'simple_ar':{'windows':[(3.,5.)], 'n':[1.45,2.35]},
       'dual_ar':{'windows':[(3.,5.),(8.,12.)], 'n':[1.45,2.35]*3}}
METHODS=['direct_local','direct_multistart','direct_multistart_cap','amplitude_homotopy','phase_homotopy','phase_no_step']

def amplitudes(wl,d,n,n0=1.,ns=3.42, reference_depth=None, plane_shift=0.):
    """r at fixed air coordinate x=-reference_depth; substrate front x=0.
    Layers occupy [-sum(d),0]. Surface-reference results when depth is None.
    An added plane_shift moves the *fixed* air reference farther from substrate.
    """
    wl=np.asarray(wl,float); d=np.asarray(d,float); n=np.asarray(n,complex)
    if len(d)!=len(n) or np.any(wl<=0) or np.any(d<0): raise ValueError('invalid geometry')
    if np.imag(n0)!=0 or np.imag(ns)!=0 or np.real(n0)<=0 or np.real(ns)<=0: raise ValueError('real exteriors required')
    a=np.ones(wl.shape,complex); b=np.zeros_like(a); c=b.copy(); dd=a.copy()
    for nj,dj in zip(n,d):
        delta=2*np.pi*nj*dj/wl; co=np.cos(delta); si=np.sin(delta)
        m01=-1j*si/nj; m10=-1j*nj*si
        a,b,c,dd=a*co+b*m10,a*m01+b*co,c*co+dd*m10,c*m01+dd*co
    den=n0*(a+b*ns)+c+dd*ns
    r=(n0*(a+b*ns)-c-dd*ns)/den; t=2*n0/den
    if reference_depth is not None:
        air=reference_depth+plane_shift-np.sum(d)
        if air < -1e-10: raise ValueError('reference plane intersects coating')
        r=r*np.exp(4j*np.pi*n0*air/wl); t=t*np.exp(2j*np.pi*n0*air/wl)
    return r,t

def grid(windows,n): return np.concatenate([np.linspace(a,b,n) for a,b in windows])
def score(R): return (max(float(np.max(R)/TARGET-1),0.),float(np.mean(R)))
class Meter:
    def __init__(self,n): self.n=len(n); self.counts={}; self.seconds={}
    def forward(self,wl,d,n,kind,**kw):
        st=time.perf_counter(); ans=amplitudes(wl,d,n,**kw); dt=time.perf_counter()-st
        v=self.counts.setdefault(kind,{'calls':0,'points':0,'point_layers':0})
        v['calls']+=1; v['points']+=len(wl); v['point_layers']+=len(wl)*max(len(n),1)
        self.seconds[kind]=self.seconds.get(kind,0.)+dt
        return ans

def physics_checks():
    rng=np.random.default_rng(1234); errR=errT=errRec=energy=gauge=0.
    for _ in range(30):
        N=int(rng.integers(1,9)); n=rng.uniform(1.2,3.5,N); d=rng.uniform(0,2.5,N); wl=np.linspace(.5,14,97)
        for absorb in [False,True]:
            nn=n+1j*rng.uniform(.001,.04,N) if absorb else n
            r,t=amplitudes(wl,d,nn,reference_depth=N*UPPER)
            R,T=tmm_normal(wl,d,nn)
            errR=max(errR,float(np.max(abs(abs(r)**2-R)))); errT=max(errT,float(np.max(abs(3.42*abs(t)**2-T))))
            errRec=max(errRec,float(np.max(abs(abs(r)**2-reflection_recursion(wl,d,nn)))))
            if not absorb: energy=max(energy,float(np.max(abs(abs(r)**2+3.42*abs(t)**2-1))))
            rp,_=amplitudes(wl,d,nn,reference_depth=N*UPPER,plane_shift=1.713)
            gauge=max(gauge,float(np.max(abs(rp-r*np.exp(4j*np.pi*1.713/wl)))))
    assert max(errR,errT,errRec,energy,gauge)<1e-10
    # A lossless bare interface is stationary in intensity, but not in amplitude.
    wl=np.array([4.]); nar=math.sqrt(3.42); depth=2.5; eps=1e-5
    r0,_=amplitudes(wl,[0.],[nar],reference_depth=depth)
    rp,_=amplitudes(wl,[eps],[nar],reference_depth=depth)
    rm,_=amplitudes(wl,[eps/2],[nar],reference_depth=depth)
    derivative_forward=(abs(rp[0])**2-abs(r0[0])**2)/eps
    derivative_half=(abs(rm[0])**2-abs(r0[0])**2)/(eps/2)
    dsurf=(amplitudes(wl,[eps],[nar])[0]-amplitudes(wl,[0.],[nar])[0])/eps
    r01=(1-nar)/(1+nar); r12=(nar-3.42)/(nar+3.42)
    exact_dr_surface=2j*(2*np.pi*nar/4)*r12*(1-r01*r01)/(1+r01*r12)**2
    dr_fixed=np.exp(4j*np.pi*depth/4)*(exact_dr_surface-4j*np.pi/4*((1-3.42)/(1+3.42)))
    aux_gradients=[]
    for sigma in [-1,1]:
        guide=.85*r0[0]*np.exp(1j*sigma*np.pi/3*np.sin(np.pi*.15))
        aux_gradients.append(float(2*np.real(np.conj(r0[0]-guide)*dr_fixed)/SR**2))
    assert abs(exact_dr_surface.real)<1e-15 and aux_gradients[0]*aux_gradients[1]<0
    quarter=4/(4*nar); rq,tq=amplitudes(wl,[quarter],[nar],reference_depth=depth)
    # Exact stationary derivative for real indices; one-sided finite difference is O(h).
    assert abs(derivative_half)<.51*abs(derivative_forward) and abs(rq[0])**2<1e-25
    # Covariant guide: arbitrary fixed reference shifts leave auxiliary loss invariant.
    d0=np.array([.13,.72]); d=np.array([.27,.55]); nn=np.array([1.45,2.35]); w=np.linspace(3,5,31)
    losses=[]
    for shift in [0.,1.713]:
        rs,_=amplitudes(w,d0,nn,reference_depth=5.,plane_shift=shift)
        r,_=amplitudes(w,d,nn,reference_depth=5.,plane_shift=shift)
        guide=.6*rs*np.exp(1j*np.pi/3*np.sin(np.pi*.4))
        losses.append(float(np.mean(abs(r-guide)**2)))
    assert abs(losses[0]-losses[1])<1e-14
    return {'matrix_R_max_error':errR,'matrix_T_max_error':errT,'independent_recursion_R_max_error':errRec,'energy_max_error':energy,'fixed_plane_covariance_error':gauge,'guide_loss_fixed_plane_shift_difference':abs(losses[0]-losses[1]),'zero_thickness':{'exact_dR_dd':0.,'exact_surface_dr_dd_real':float(exact_dr_surface.real),'exact_surface_dr_dd_imag':float(exact_dr_surface.imag),'auxiliary_dF_dd_sign_branches':aux_gradients,'forward_derivative_h':derivative_forward,'forward_derivative_h_half':derivative_half,'surface_dr_dd_real':float(dsurf.real[0]),'surface_dr_dd_imag':float(dsurf.imag[0]),'quarterwave_thickness_um':quarter,'quarterwave_R':float(abs(rq[0])**2),'quarterwave_T':float(3.42*abs(tq[0])**2)},'scope':'synthetic normal incidence coherent planar layers, real semi-infinite exteriors; no oblique/incidence, backside, uncertainty or continuous certificate'}

def optimize(case,seed,method,plane_shift=0.,surface_artifact=False, theta_max=math.pi/3, start_override=None, iter_override=None):
    cfg=CASES[case]; windows=cfg['windows']; n=np.array(cfg['n']); N=len(n); depth=N*UPPER
    train=grid(windows,41); audit=grid(windows,257); final=grid(windows,2049)
    rng=np.random.default_rng(seed); x0=rng.uniform(.04,1.7,N)
    starts=[x0]+[rng.uniform(.04,1.7,N) for _ in range(3)]
    branches=1 if method=='direct_local' else 4
    iterations=(ITER_PER_BRANCH*4 if branches==1 else ITER_PER_BRANCH) if iter_override is None else iter_override
    if start_override is not None: starts[0]=np.asarray(start_override,float).copy()
    signs=[np.ones(len(windows)), -np.ones(len(windows)),np.array([1 if j%2==0 else -1 for j in range(len(windows))]),np.array([-1 if j%2==0 else 1 for j in range(len(windows))])]
    meter=Meter(n); best=None; bestx=None; archive=[]; history=[]; QPtime=0.; rejected=0; phase_clipped=0; guide_seconds=0.
    refkw={'reference_depth':None if surface_artifact else depth,'plane_shift':plane_shift}
    def evaltrain(x,kind='train'): return meter.forward(train,x,n,kind,**refkw)[0]
    def update(x,branch,stage,aux):
        nonlocal best,bestx
        r,t=meter.forward(audit,x,n,'archive_audit',**refkw); R=abs(r)**2; T=3.42*abs(t)**2
        s=score(R)
        if best is None or s<best:
            best=s; bestx=x.copy(); archive.append({'branch':branch,'tau':stage,'V':s[0],'mean_R':s[1],'d_um':x.tolist(),'auxiliary_weight':aux,'max_energy_error':float(np.max(abs(R+T-1)))})
    st=time.perf_counter()
    for branch in range(branches):
        x=starts[branch].copy(); rs=evaltrain(x,'seed'); update(x,branch,0.,0.)
        rho=.4
        for it in range(iterations):
            is_hom='homotopy' in method or method=='phase_no_step'
            tau=[.15,.35,.55,.75,.9,1.][min(it//3,5)] if is_hom else 1.
            aux=1-tau
            r=evaltrain(x); R=abs(r)**2; g=R/TARGET-1
            guide_st=time.perf_counter()
            sigma=np.repeat(signs[branch],41) if method.startswith('phase') else np.zeros(len(train))
            guide=(1-tau)*rs*np.exp(1j*sigma*theta_max*np.sin(np.pi*tau))
            guide_seconds+=time.perf_counter()-guide_st
            Jr=np.empty((len(train),N),complex)
            for j in range(N):
                h=1e-5; h=-h if x[j]+h>UPPER else h
                xx=x.copy(); xx[j]+=h; Jr[:,j]=(evaltrain(xx,'jacobian_fd')-r)/h
            Jg=2*np.real(np.conj(r[:,None])*Jr)/TARGET
            limit=np.full(N,rho)
            if method in ['phase_homotopy','amplitude_homotopy','direct_multistart_cap']:
                plimit=train.min()/(8*np.real(n)); phase_clipped+=int(np.any(plimit<limit)); limit=np.minimum(limit,plimit)
            lo=np.maximum(LOWER-x,-limit); hi=np.minimum(UPPER-x,limit)
            # QP has no physical calls; epigraph t>=0 preserves true max(0,g).
            reg=.005/(max(rho,.01)**2)
            def qfun(y):
                p=y[:-1]; residual=r+Jr@p-guide
                return aux*np.mean(abs(residual/SR)**2)+tau*y[-1]+reg*np.dot(p,p)
            def qjac(y):
                residual=r+Jr@y[:-1]-guide
                return np.r_[aux*2*np.real(np.conj(Jr).T@residual)/(len(train)*SR**2)+2*reg*y[:-1],tau]
            constraint={'type':'ineq','fun':lambda y:y[-1]-g-Jg@y[:-1], 'jac':lambda y:np.column_stack([-Jg,np.ones(len(g))])}
            qst=time.perf_counter()
            fit=minimize(qfun,np.r_[np.zeros(N),max(0,float(g.max()))],jac=qjac,bounds=list(zip(lo,hi))+[(0,None)],constraints=[constraint],method='SLSQP',options={'maxiter':40,'ftol':1e-9})
            QPtime+=time.perf_counter()-qst
            p=fit.x[:-1] if np.all(np.isfinite(fit.x)) else np.zeros(N)
            trial=np.clip(x+p,LOWER,UPPER); rt=evaltrain(trial,'trial'); gt=abs(rt)**2/TARGET-1
            actual_old=aux*np.mean(abs((r-guide)/SR)**2)+tau*max(0,float(g.max()))
            actual_new=aux*np.mean(abs((rt-guide)/SR)**2)+tau*max(0,float(gt.max()))
            prediction=qfun(np.r_[np.zeros(N),max(0,float(g.max()))])-qfun(fit.x)
            ratio=(actual_old-actual_new)/max(prediction,1e-14)
            accepted=actual_new<actual_old-1e-12 or np.linalg.norm(p)<1e-10
            if accepted:
                x=trial
                if ratio>.7: rho=min(.8,rho*1.4)
            else: rejected+=1; rho=max(.002,rho*.5)
            update(trial,branch,tau,aux)
            history.append({'branch':branch,'iteration':it,'tau':tau,'auxiliary_weight':aux,'accepted':bool(accepted),'actual_objective':float(actual_new),'predicted_decrease':float(prediction),'ratio':float(ratio),'training_V':max(0,float(gt.max())),'step_um':float(np.max(abs(p))),'max_single_layer_delta_phase':float(np.max(2*np.pi*np.real(n)*abs(p)/train.min())),'qp_success':bool(fit.success)})
    runtime=time.perf_counter()-st
    r,t=meter.forward(final,bestx,n,'final_audit',**refkw); R=abs(r)**2; T=3.42*abs(t)**2
    finalscore=score(R); per=[]
    for j,(a,b) in enumerate(windows):
        rr=R[j*2049:(j+1)*2049]; tt=T[j*2049:(j+1)*2049]
        per.append({'window_um':[a,b],'max_R':float(rr.max()),'min_T':float(tt.min()),'V':max(float(rr.max()/TARGET-1),0.)})
    total={k:sum(v[k] for v in meter.counts.values()) for k in ['calls','points','point_layers']}
    return {'case':case,'seed':seed,'method':method,'plane_shift_um':plane_shift,'surface_reference_ablation':surface_artifact,'V':finalscore[0],'mean_R':finalscore[1],'pass_finite_grid':bool(finalscore[0]<=1e-8),'d_um':bestx.tolist(),'per_window':per,'max_energy_error':float(np.max(abs(R+T-1))),'minimum_A':float(np.min(1-R-T)),'runtime_seconds_including_final_audit':time.perf_counter()-st,'guide_construction_seconds':guide_seconds,'theta_max':theta_max,'runtime_seconds_excluding_final_audit':runtime,'physical_kernel_seconds':sum(meter.seconds.values()),'qp_seconds':QPtime,'counts':meter.counts,'total':total,'rejected_trials':rejected,'phase_bound_active_iterations':phase_clipped,'all_branches_reached_tau1':all(any(h['branch']==b and h['tau']==1. and h['auxiliary_weight']==0 for h in history) for b in range(branches)),'selected_archive_tau':archive[-1]['tau'],'final_auxiliary_weight':0.,'archive':archive,'history':history,'starting_designs_um':[s.tolist() for s in starts[:branches]]}

def main():
    st=time.perf_counter(); checks=physics_checks(); (ROOT/'physics_checks.json').write_text(json.dumps(checks,indent=2))
    rows=[]
    for case in CASES:
        for seed in SEEDS:
            for method in METHODS:
                r=optimize(case,seed,method); rows.append(r)
                print(case,seed,method,'V',round(r['V'],6),'wall',round(r['runtime_seconds_excluding_final_audit'],3),flush=True)
                (ROOT/'results.json').write_text(json.dumps({'rows':rows,'checks':checks},indent=2))
    # Fixed-plane coordinate covariance and deliberately moving-plane ablation.
    reference=[]
    base=next(r for r in rows if r['case']=='dual_ar' and r['seed']==11 and r['method']=='phase_homotopy')
    for shift,surface in [(1.713,False),(0.,True)]:
        r=optimize('dual_ar',11,'phase_homotopy',plane_shift=shift,surface_artifact=surface); reference.append(r)
    shift=reference[0]
    checks['optimization_fixed_plane_shift_V_difference']=abs(shift['V']-base['V'])
    checks['optimization_fixed_plane_shift_thickness_max_difference']=float(np.max(abs(np.array(shift['d_um'])-base['d_um'])))
    checks['moving_surface_reference_V']=reference[1]['V']
    summary=[]
    for case in CASES:
        for method in METHODS:
            rr=[r for r in rows if r['case']==case and r['method']==method]
            summary.append({'case':case,'method':method,'seeds':len(rr),'passes':sum(r['pass_finite_grid'] for r in rr),'median_V':float(np.median([r['V'] for r in rr])),'min_V':min(r['V'] for r in rr),'max_V':max(r['V'] for r in rr),'total_wall_seconds':sum(r['runtime_seconds_excluding_final_audit'] for r in rr),'total_point_layers':sum(r['total']['point_layers'] for r in rr)})
    metadata={'numpy':np.__version__,'scipy':scipy.__version__,'python':platform.python_version(),'train_points_per_window':41,'archive_points_per_window':257,'final_points_per_window':2049,'target_R':TARGET,'bounds_um':[LOWER,UPPER],'theta_max':math.pi/3,'phase_bound':math.pi/4,'seeds':SEEDS,'total_wall_seconds':time.perf_counter()-st,'notes':['All synthetic and fixed topology; no real-material performance claim.','Archive compares original positive-part minimax V then equal-window mean R.','Every branch runs exact original power epigraph with t>=0 at tau=1; no residual auxiliary term.','Selected archive may come from earlier tau but is separately audited on actual R/T.','Cost counts all forward finite differences and both archive/final audit; QP uses no hidden forward calls.','No confidence interval/general success rate inference from three paired seeds.']}
    out={'metadata':metadata,'checks':checks,'summary':summary,'rows':rows,'reference_ablation':reference}
    (ROOT/'results.json').write_text(json.dumps(out,indent=2)); (ROOT/'summary.json').write_text(json.dumps({'metadata':metadata,'checks':checks,'summary':summary},indent=2))
    fields=['case','seed','method','V','mean_R','pass_finite_grid','runtime_seconds_excluding_final_audit','physical_kernel_seconds','qp_seconds','rejected_trials','phase_bound_active_iterations','all_branches_reached_tau1','selected_archive_tau']
    with (ROOT/'results.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields+['calls','points','point_layers']); w.writeheader()
        for r in rows: w.writerow({**{k:r[k] for k in fields},**r['total']})
    with (ROOT/'summary.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(summary[0])); w.writeheader(); w.writerows(summary)
    print('SUMMARY',json.dumps(summary),flush=True)
if __name__=='__main__': main()
