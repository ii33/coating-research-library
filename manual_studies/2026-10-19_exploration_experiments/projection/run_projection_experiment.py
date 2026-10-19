#!/usr/bin/env python3
"""Small falsification test. Existing verified power kernel is imported read-only.
All thickness/wavelength units are um; optical constants are synthetic real scalars.
No software integration, repository publication, or production-material assertion.
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode = True
import csv, hashlib, importlib.util, itertools, json, math, platform, time
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import minimize, lsq_linear
from scipy.stats import spearmanr

ROOT=Path(__file__).resolve().parent
KERNEL=ROOT/'verified_power_kernel.py'
spec=importlib.util.spec_from_file_location('verified_power_kernel',KERNEL)
kernel=importlib.util.module_from_spec(spec);sys.modules[spec.name]=kernel;spec.loader.exec_module(kernel)
N0, NS = 1.0,3.42
WL=np.linspace(3.,5.,31)
D_MIN,D_MAX=.05,1.2
D_SCALE=.2
H_X=1e-5
REFERENCE_Z=-10.
TARGET=.01
REPAIR_BUDGET=160
SEEDS=[11,29,47]
MATERIALS=[1.2,1.45,2.35,3.1]
BIRTH_D=[.05,.15,.35,.7]
TRUST_UM=.05
LAMBDA=1e-6
COUNTS={}

def scalar_amplitudes(wl,ds,nn,n0=N0,ns=NS,reference_z=REFERENCE_Z):
    """Independent Fresnel recursion, global input plane z=-10, substrate z=0.
    Surface at z=-sum(ds). exp(-i wt), forward exp(+i kz).
    t is flux normalized. Common plane factors remove moving-surface artifacts.
    """
    wl=np.atleast_1d(np.asarray(wl,float));ds=np.asarray(ds,float);nn=np.asarray(nn,complex)
    media=np.array([n0,*nn,ns],complex)
    rr=np.full(wl.shape,(media[-2]-media[-1])/(media[-2]+media[-1]),complex)
    tt=np.full(wl.shape,2*media[-2]/(media[-2]+media[-1]),complex)
    for j in range(len(ds)-1,-1,-1):
        delta=2*np.pi*media[j+1]*ds[j]/wl
        rij=(media[j]-media[j+1])/(media[j]+media[j+1])
        tij=2*media[j]/(media[j]+media[j+1])
        phase=np.exp(2j*delta);den=1+rij*rr*phase
        tt=tij*tt*np.exp(1j*delta)/den
        rr=(rij+rr*phase)/den
    distance=-sum(ds)-reference_z
    rr*=np.exp(4j*np.pi*n0*distance/wl)
    tt*=np.sqrt(ns/n0)*np.exp(2j*np.pi*n0*distance/wl)
    return rr,tt

def phi(r):return np.r_[r.real,r.imag]
def r_from_phi(p):q=len(p)//2;return p[:q]+1j*p[q:]
def g_of_R(R):return (np.asarray(R)-TARGET)/TARGET

def evaluate(ds,nn,phase,need_phi=True,wl=WL):
    item=COUNTS.setdefault(phase,dict(power_kernel_calls=0,amplitude_recursion_calls=0,wavelength_layer_products=0,wall_seconds=0.))
    start=time.perf_counter();item['power_kernel_calls']+=1
    item['wavelength_layer_products']+=len(wl)*max(1,len(ds))
    R,T=kernel.tmm_normal(wl,ds,nn,N0,NS)
    p=None
    if need_phi:
        item['amplitude_recursion_calls']+=1;item['wavelength_layer_products']+=len(wl)*max(1,len(ds))
        r,t=scalar_amplitudes(wl,ds,nn);p=phi(r)
    item['wall_seconds']+=time.perf_counter()-start
    return R,p

def canonical(ds,nn,upper=D_MAX):
    d=[];n=[]
    for a,b in zip(ds,nn):
        if d and b==n[-1]:d[-1]+=float(a)
        else:d.append(float(a));n.append(float(b))
    if any(a<D_MIN-1e-12 or a>upper+1e-12 for a in d):return None
    return np.array(d),np.array(n)

def catalog(ds,nn,upper=D_MAX):
    rows=[];seen=set()
    def add(label,dd,mm):
        out=canonical(dd,mm,upper)
        if out is None:return
        d,n=out;key=(tuple(np.round(d,12)),tuple(n))
        if key in seen:return
        seen.add(key);rows.append(dict(label=label,d=d,n=n))
    for j in range(len(ds)+1):
        for n,d in itertools.product(MATERIALS,BIRTH_D):
            add(f'insert_{j}_n{n}_d{d}',np.insert(ds,j,d),np.insert(nn,j,n))
    for j in range(len(ds)):
        for n in MATERIALS:
            if n!=nn[j]:mm=nn.copy();mm[j]=n;add(f'replace_{j}_n{n}',ds,mm)
        add(f'delete_{j}',np.delete(ds,j),np.delete(nn,j))
    # Redundant same-material split is deliberately retained as a labeled diagnostic.
    if len(ds)==1 and ds[0]>=2*D_MIN:
        add('redundant_same_material_split',[ds[0]/2,ds[0]/2],[nn[0],nn[0]])
    return rows

class BudgetEnd(Exception):pass

def repair(ds,nn,budget,phase,lower=D_MIN,upper=D_MAX):
    ds=np.asarray(ds,float);nn=np.asarray(nn,float)
    if len(ds)==0:
        R,_=evaluate(ds,nn,phase,False)
        return dict(d=[],max_R=float(max(R)),calls=1,status='no thickness degrees of freedom')
    lo=np.full(len(ds),lower);hi=np.full(len(ds),upper)
    cache={};best_R=math.inf;best_d=None;calls=0
    def get(x):
        nonlocal calls,best_R,best_d
        d=np.clip(np.asarray(x)*D_SCALE,lo,hi);key=tuple(d)
        if key not in cache:
            if calls>=budget:raise BudgetEnd()
            calls+=1;R,_=evaluate(d,nn,phase,False);cache[key]=R
            merit=float(max(R))
            if merit<best_R:best_R,best_d=merit,d.copy()
        return cache[key]
    R0=get(ds/D_SCALE)
    y0=np.r_[ds/D_SCALE,max(R0)]
    try:
        sol=minimize(lambda y:y[-1],y0,method='SLSQP',
          bounds=[(a/D_SCALE,b/D_SCALE) for a,b in zip(lo,hi)]+[(0.,1.)],
          constraints=[dict(type='ineq',fun=lambda y:y[-1]-get(y[:-1]))],
          options=dict(maxiter=100,ftol=1e-12,eps=1e-6,disp=False))
        status=str(sol.message)
    except BudgetEnd:status='actual power-kernel call budget exhausted'
    return dict(d=best_d.tolist(),max_R=best_R,calls=calls,status=status)

def jacobian(ds,nn,phase):
    columns=[]
    for j in range(len(ds)):
        dp=ds.copy();dm=ds.copy();dp[j]+=D_SCALE*H_X;dm[j]-=D_SCALE*H_X
        _,pp=evaluate(dp,nn,phase);_,pm=evaluate(dm,nn,phase)
        columns.append((pp-pm)/(2*H_X))
    return np.stack(columns,axis=1) if columns else np.zeros((2*len(WL),0))

def normals(r):
    rows=np.zeros((len(WL),2*len(WL)))
    for i in range(len(WL)):rows[i,i]=2*r[i].real/TARGET;rows[i,len(WL)+i]=2*r[i].imag/TARGET
    return rows

def check_physics():
    rng=np.random.default_rng(20261019);max_r=max_t=max_energy=0.
    for _ in range(20):
        num=int(rng.integers(0,7));d=rng.uniform(D_MIN,D_MAX,num);n=rng.uniform(1.2,3.5,num)
        R,T=kernel.tmm_normal(WL,d,n,N0,NS);r,t=scalar_amplitudes(WL,d,n)
        max_r=max(max_r,float(max(abs(R-abs(r)**2))));max_t=max(max_t,float(max(abs(T-abs(t)**2))))
        max_energy=max(max_energy,float(max(abs(abs(r)**2+abs(t)**2-1))))
    d=np.array([.33,.51]);n=np.array([1.45,2.35]);r,t=scalar_amplitudes(WL,d,n)
    # Appending an exterior-index layer in front moves the local surface only.
    ra,ta=scalar_amplitudes(WL,np.r_[.27,d],np.r_[N0,n])
    phase_invariance=max(float(max(abs(r-ra))),float(max(abs(t-ta))))
    rs,ts=scalar_amplitudes(WL*1000,d*1000,n,reference_z=REFERENCE_Z*1000)
    unit_invariance=max(float(max(abs(r-rs))),float(max(abs(t-ts))))
    rc,tc=scalar_amplitudes(WL,[.44,.62],[1.45,2.35]);rd,td=scalar_amplitudes(WL,[.22,.22,.62],[1.45,1.45,2.35])
    split_error=max(float(max(abs(rc-rd))),float(max(abs(tc-td))))
    checks=dict(amplitude_R_vs_verified_kernel_max_error=max_r,amplitude_T_vs_verified_kernel_max_error=max_t,
      lossless_energy_max_error=max_energy,common_reference_ambient_insertion_error=phase_invariance,
      um_vs_nm_identical_physics_error=unit_invariance,same_material_split_error=split_error)
    assert max(checks.values())<2e-13,checks
    return checks

def experiment(case,upper):
    start=time.perf_counter();phase=f'{case}_base_repair'
    fit=repair([.4],[1.45],2000,phase,upper=upper)
    ds=np.array(fit['d']);nn=np.array([1.45])
    R,p=evaluate(ds,nn,f'{case}_screen');r=r_from_phi(p);A=jacobian(ds,nn,f'{case}_jacobian')
    G=normals(r);dgdX=G@A
    active=np.where(R>=max(R)-1e-8)[0]
    if len(active)==2:
        a,b=dgdX[active,0];mu=np.array([-b/(a-b),a/(a-b)])
    else:mu=np.ones(len(active))/len(active)
    b=mu@G[active]
    free=(ds>D_MIN+1e-7)&(ds<upper-1e-7)
    AF=A[:,free]
    if AF.shape[1]:
        u,s,vt=np.linalg.svd(AF,full_matrices=False);keep=s>1e-10*max(s);U=u[:,keep];P=U@U.T
    else:s=np.array([]);P=np.zeros((len(p),len(p)))
    # Incorrect unconstrained projection is diagnostic only, not claimed valid at bounds.
    ua,sa,_=np.linalg.svd(A,full_matrices=False);Pall=ua@ua.T
    rows=catalog(ds,nn,upper)
    for e in rows:
        Re,pe=evaluate(e['d'],e['n'],f'{case}_screen');v=pe-p;vp=v-P@v
        raw=-float(b@v);projected=-float(b@vp)
        cosine=projected/(np.linalg.norm(b)*np.linalg.norm(vp)) if np.linalg.norm(vp)>1e-12 and np.linalg.norm(b)>1e-12 else -1.0
        # Base-J bounded response-preservation compensation. Finite edit derivatives
        # may differ; this is intentionally an approximate screening diagnostic.
        # Only original surviving material is compensable; replacement/deletion have none.
        retained=not e['label'].startswith(('replace','delete'))
        if retained:
            retained_d=e['d'][np.where(e['n']==nn[0])[0][0]]
            lo=np.maximum((D_MIN-retained_d)/D_SCALE,-TRUST_UM/D_SCALE)*np.ones(len(ds))
            hi=np.minimum((upper-retained_d)/D_SCALE,TRUST_UM/D_SCALE)*np.ones(len(ds))
            # lsq_linear requires strict bounds; remove frozen columns if any.
            movable=hi-lo>1e-13
            z=np.zeros(len(ds))
            if np.any(movable):
                M=np.vstack([A[:,movable],np.sqrt(LAMBDA)*np.eye(sum(movable))]);rhs=np.r_[-v,np.zeros(sum(movable))]
                res=lsq_linear(M,rhs,bounds=(lo[movable],hi[movable]),tol=1e-12,max_iter=200)
                z[movable]=res.x
            c=v+A@z
        else:z=np.zeros(len(ds));c=v
        predicted_R=abs(r_from_phi(p+c))**2
        e.update(raw_inner=raw,projected_inner=projected,projected_cosine=cosine,
          incorrect_full_projection_inner=-float(b@(v-Pall@v)),
          finite_max_R=float(max(Re)),bounded_predicted_max_R=float(max(predicted_R)),
          orthogonal_norm=float(np.linalg.norm(vp)),projected_cosine_informative=bool(np.linalg.norm(vp)>1e-12 and np.linalg.norm(b)>1e-12),compensation_um=(z*D_SCALE).tolist())
        fixed=repair(e['d'],e['n'],REPAIR_BUDGET,f'{case}_all_candidate_repairs',upper=upper)
        audit_R,_=evaluate(fixed['d'],e['n'],f'{case}_dense_audit',False,wl=np.linspace(3,5,2049))
        mid_wl=np.r_[3.,3.+(np.arange(2048)+.5)*(2./2048),5.]
        mid_R,_=evaluate(fixed['d'],e['n'],f'{case}_midpoint_audit',False,wl=mid_wl)
        e.update(repaired_midpoint_max_R=float(max(mid_R)),repaired_audited_max_R=max(float(max(audit_R)),float(max(mid_R))),repaired_max_R=fixed['max_R'],repaired_dense_max_R=float(max(audit_R)),repaired_dense_min_T=1-float(max(audit_R)),
          repair_calls=fixed['calls'],repair_point_layer_equivalent_work=fixed['calls']*len(WL)*max(1,len(e['n'])),repair_status=fixed['status'],repaired_d=fixed['d'])
    methods={'raw_inner':True,'projected_inner':True,'projected_cosine':True,
       'finite_max_R':False,'bounded_predicted_max_R':False}
    oracle=min(e['repaired_audited_max_R'] for e in rows);summaries={}
    # Equal refinement allocations. The exhaustive label-generation phase is not
    # counted as an online method: each method buys only k repairs from its list.
    common_calls=1+len(rows)
    for name,descending in methods.items():
        order=sorted(range(len(rows)),key=lambda i:(-rows[i][name] if descending else rows[i][name],rows[i]['label']))
        scores=np.array([(-e[name] if descending else e[name]) for e in rows])
        valid=np.isfinite(scores)
        corr=spearmanr(scores[valid],[rows[i]['repaired_audited_max_R'] for i in range(len(rows)) if valid[i]])
        m=dict(spearman_lower_is_better=float(corr.statistic),order_labels=[rows[i]['label'] for i in order])
        for k in [1,3]:
            chosen=[rows[i] for i in order[:k]];best=min(e['repaired_audited_max_R'] for e in chosen)
            projected=name in ('projected_inner','projected_cosine','bounded_predicted_max_R')
            # Raw's b and phi require no J for known equal active weights in this
            # symmetric one-layer case. Here KKT recovery also used J, so actual
            # measured shared setup includes its 2 base finite-difference calls.
            m[f'top{k}']=dict(best_audited_max_R=best,archive_best_audited_max_R=min(float(max(R)),best),best_dense_max_R=min(e['repaired_dense_max_R'] for e in chosen),regret=best-oracle,feasible=best<=TARGET,
             allocated_power_calls=common_calls+(0 if name=='finite_max_R' else 2*len(ds))+k*REPAIR_BUDGET,
             allocated_amplitude_calls=0 if name=='finite_max_R' else common_calls+2*len(ds),
             reconstructed_actual_online_power_calls=common_calls+(0 if name=='finite_max_R' else 2*len(ds))+sum(e['repair_calls'] for e in chosen),
             reconstructed_actual_online_amplitude_calls=0 if name=='finite_max_R' else common_calls+2*len(ds),
             actual_repair_power_calls=sum(e['repair_calls'] for e in chosen),
             actual_selected_repair_point_layer_equivalent_work=sum(e['repair_point_layer_equivalent_work'] for e in chosen),
             calls_note='equal per-candidate refinement cap, not equal end-to-end actual cost; finite-power baseline needs no amplitudes/J; projected methods and KKT-dual reconstruction charged for J; dense audit excluded but separately counted')
        summaries[name]=m
    random=[]
    for seed in SEEDS:
        rng=np.random.default_rng(seed);ix=rng.permutation(len(rows))
        random.append(dict(seed=seed,top1_audited_max_R=rows[ix[0]]['repaired_audited_max_R'],
          top3_audited_max_R=min(rows[i]['repaired_audited_max_R'] for i in ix[:3]),
          labels=[rows[i]['label'] for i in ix[:3]]))
    # Exact expected random top-k minimum over all combinations, no Monte Carlo uncertainty.
    labels=np.sort([e['repaired_audited_max_R'] for e in rows]);n=len(labels)
    rand_expected={str(k):sum(float(labels[i])*math.comb(n-i-1,k-1)/math.comb(n,k) for i in range(n-k+1)) for k in [1,3]}
    for e in rows:e['d']=e['d'].tolist();e['n']=e['n'].tolist()
    return dict(case=case,base_d_um=ds.tolist(),base_n=nn.tolist(),base_max_R=float(max(R)),
      base_optimization=fit,bound_upper_um=upper,free_coordinates=free.tolist(),
      active_wavelength_um=WL[active].tolist(),active_mu=mu.tolist(),active_derivative_dg_dx=dgdX[active,0].tolist(),
      tangent_stationarity_norm=float(np.linalg.norm(AF.T@b)),full_stationarity_norm=float(np.linalg.norm(A.T@b)),
      singular_values=s.tolist(),max_raw_projected_inner_error=max(abs(e['raw_inner']-e['projected_inner']) for e in rows),
      max_incorrect_full_projected_score_error=max(abs(e['raw_inner']-e['incorrect_full_projection_inner']) for e in rows),
      candidate_count=len(rows),oracle_audited_max_R=oracle,oracle_dense_max_R=min(e['repaired_dense_max_R'] for e in rows),methods=summaries,random_seeds=random,
      exact_expected_random_best_audited_R=rand_expected,candidates=rows,wall_seconds=time.perf_counter()-start)

def main():
    start=time.perf_counter();checks=check_physics()
    results=[experiment('interior',D_MAX),experiment('upper_boundary',.4)]
    out=dict(date_utc='2026-10-19',scope='synthetic lossless normal-incidence AR, no claims for real materials',
       numpy=np.__version__,scipy=scipy.__version__,python=platform.python_version(),
       cost_work_note='wavelength_layer_products is an interface-equivalent work proxy, with max(1,N); not literal layer updates, FLOPs, or matched runtime',source_power_kernel=KERNEL.name,source_power_kernel_sha256=hashlib.sha256(KERNEL.read_bytes()).hexdigest(),
       source_power_kernel_provenance='Exact unchanged copy of run_experiment.py from the earlier verified synthetic coating-search experiment, 2026-10-19; bundled for portable offline reproduction',
       config=dict(n0=N0,ns=NS,training_wavelength_um=WL.tolist(),independent_audit_points=2049,midpoint_audit_points=2050,midpoint_audit='2048 disjoint interior midpoints plus mandatory endpoints; union maximum used for all labels',
        thickness_unit='um',d_min_um=D_MIN,d_max_um=D_MAX,d_scale_um=D_SCALE,reference_input_z_um=REFERENCE_Z,
        reference_output_z_um=0.,response='Re/Im r at common reference; no imposed phase target',W='identity positive definite',
        svd_relative_cutoff=1e-10,central_difference_h_in_x=H_X,x_definition='d / 0.2 um',target_R=TARGET,
        constraints='every wavelength R <= .01; same-material neighbors canonicalized; positive layers >= .05 um; all candidate and repair layers obey case upper bound, 1.2 or .4 um',
        repair='SLSQP epigraph min t, all R_q <= t; best actual legal iterate retained',repair_call_cap=REPAIR_BUDGET,
        birth_material_n=MATERIALS,birth_thickness_um=BIRTH_D,compensation_trust_um=TRUST_UM,compensation_lambda=LAMBDA,
        random_seeds=SEEDS,unitcheck_seed=20261019),
       checks=checks,results=results,costs=COUNTS,total_wall_seconds=time.perf_counter()-start,
       stopping='Stop after this two-case finite catalog. Inner-product novelty is falsified algebraically. Ranking gains, if any, require independent broader tests; no main feature or publication.')
    (ROOT/'results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False))
    fields=['case','label','d_um','n','raw_inner','projected_inner','projected_cosine','finite_max_R','bounded_predicted_max_R','repaired_max_R','repaired_dense_max_R','repaired_midpoint_max_R','repaired_audited_max_R','repair_point_layer_equivalent_work','repair_calls','repair_status']
    with (ROOT/'candidates.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for result in results:
            for e in result['candidates']:
                row={k:e[k] for k in fields if k in e};row.update(case=result['case'],d_um=json.dumps(e['d']),n=json.dumps(e['n']));w.writerow(row)
    print(json.dumps(dict(checks=checks,results=[{k:v for k,v in r.items() if k not in ['candidates']} for r in results],costs=COUNTS,total_wall_seconds=out['total_wall_seconds']),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
