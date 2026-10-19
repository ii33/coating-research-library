#!/usr/bin/env python3
"""Small finite protective-pack experiment. Synthetic optics; not production design.

Reads the verified original research kernel without altering it. Set --kernel-root
if this folder is moved. All outputs are written into this experiment directory.
"""
from __future__ import annotations
import argparse, csv, hashlib, itertools, json, platform, sys, time
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent
DEFAULT_KERNEL=ROOT/'verified_kernel'
MATERIALS=np.array([1.45,2.35])
WINDOWS=((3.,5.),(8.,12.))
TARGET=.01
LOW=.005
HIGH=2.5
TOTAL_MAX=12.
SEEDS=(11,29,47,83)
METHODS=('anchor_identity','multipoint_identity','random_pack','phase_covered','best_V')
TRAIN_N=81
DENSE_N=4097
LOCAL_CALLS=240
STARTS_PER_LENGTH=2
PACK_TOTALS={1:4/(2*1.45),2:4/(2*1.45)+4/(2*2.35),3:2*4/(2*1.45)+4/(2*2.35)}
STARTS={
 'protected_short_window':[.6718207875641499,.9596658089704853,.2686941745557452,.16440325380469994,1.5589439301147199,.41467230316209586],
 'existing_best_dual_window':[.8687914311440501,.16595496505818463,.0053528155003879085,.0051792662818528346,.2742767404282964,.5352681554140437],
}
BASE_N=np.array([1.45,2.35]*3)
KERNEL=None
LAST_POOL_STATS={}

def load_kernel(path):
    global KERNEL
    sys.path.insert(0,str(path))
    import run_experiment as k
    KERNEL=k
    return k

def canonical(ds,ns):
    d=[];n=[]
    for a,b in zip(ds,ns):
        if n and b==n[-1]: d[-1]+=float(a)
        else: d.append(float(a));n.append(float(b))
    return np.array(d),np.array(n)

def legal(ds,ns):
    if np.any(np.array(ds)<LOW-1e-10) or np.any(np.array(ds)>HIGH+1e-10) or sum(ds)>TOTAL_MAX+1e-10: return False
    dd,nn=canonical(ds,ns)
    return len(dd)<=9 and np.max(dd)<=HIGH+1e-10

def pack_matrix(wl,ds,ns):
    out=np.tile(np.eye(2,dtype=complex),(len(np.atleast_1d(wl)),1,1))
    for d,n in zip(ds,ns):
        p=2*np.pi*n*d/np.atleast_1d(wl)
        z=np.empty_like(out);z[:,0,0]=z[:,1,1]=np.cos(p)
        z[:,0,1]=-1j*np.sin(p)/n;z[:,1,0]=-1j*n*np.sin(p)
        out=out@z
    return out

def identity_score(ds,ns,anchors):
    # Fixed E/H normalization based on geometric-mean exterior admittance.
    adm=np.sqrt(3.42); D=np.diag([np.sqrt(adm),1/np.sqrt(adm)])
    M=D@pack_matrix(np.asarray(anchors),ds,ns)@np.linalg.inv(D)
    return float(np.min(np.stack([np.linalg.norm(M-np.eye(2),axis=(1,2)),np.linalg.norm(M+np.eye(2),axis=(1,2))]),axis=0).max())

def project_sum(v,total,lo,hi):
    if len(v)==1:return np.array([total])
    a=float(np.min(v-hi))-1.;b=float(np.max(v-lo))+1.
    for _ in range(64):
        m=(a+b)/2
        if np.clip(v-m,lo,hi).sum()>total:a=m
        else:b=m
    return np.clip(v-(a+b)/2,lo,hi)

def build_pool(base,seed):
    global LAST_POOL_STATS
    proposed=0;legal_raw=0;aux_updates=0
    rng=np.random.default_rng(seed); out=[]
    for k in (1,2,3):
        total=PACK_TOTALS[k]
        specs=[]
        for seq in itertools.product(MATERIALS,repeat=k):
            ns=np.array(seq)
            if abs(np.sum(4/(2*ns))-total)<1e-10:specs.append((4/(2*ns),ns,'exact_halfwave'))
            for j in range(4 if k>1 else 1):
                u=project_sum(rng.uniform(LOW,HIGH,k),total,np.full(k,LOW),np.full(k,HIGH))
                specs.append((u,ns,'random_fixed_total'))
            if k>1:
                for j in range(2):
                    phase=np.mod(np.arange(k)+j*.5,k)+.5
                    u=project_sum(phase/phase.sum()*total,total,np.full(k,LOW),np.full(k,HIGH))
                    specs.append((u,ns,'phase_lattice_fixed_total'))
        for pd,pn,source in specs:
            for pos in range(7):
                proposed+=1
                ds=np.concatenate((base[:pos],pd,base[pos:])); ns=np.concatenate((BASE_N[:pos],pn,BASE_N[pos:]))
                if legal(ds,ns):
                    legal_raw+=1;aux_updates+=6*k
                    out.append(dict(id=len(out),pack_length=k,position=pos,source=source,pack_d=pd.tolist(),pack_n=pn.tolist(),d=ds.tolist(),n=ns.tolist(),pack_total_um=float(total),E_anchor=identity_score(pd,pn,[4.]),E_multi=identity_score(pd,pn,[3.,3.5,4.,4.5,5.]),phase_mod_pi=float(np.mod(2*np.sum(pd*pn)/4,1))))
    # Duplicates otherwise count as independent opportunities for some methods.
    seen=set();dedup=[]
    for p in out:
        key=(p['position'],tuple(p['pack_n']),tuple(np.round(p['pack_d'],11)))
        if key not in seen:seen.add(key);p['id']=len(dedup);dedup.append(p)
    LAST_POOL_STATS=dict(proposed_packs_including_illegal=proposed,legal_before_dedup=legal_raw,unique_optically_screened=len(dedup),rejected_before_optical_screen=proposed-legal_raw,auxiliary_identity_matrix_calls=2*legal_raw,auxiliary_identity_wavelength_layer_updates=aux_updates)
    return dedup

def values(rr,pmask):
    g=rr/TARGET-1
    return (float(max(0.,g[pmask].max())) if np.any(pmask) else 0.,float(max(0.,g.max())),float(np.mean(np.maximum(g,0)**2)))

def metrics(ds,ns,grid):
    R,T=KERNEL.tmm_normal(grid,ds,ns)
    z=[]
    for lo,hi in WINDOWS:
        sel=(grid>=lo)&(grid<=hi);rr=R[sel];tt=T[sel];w=grid[sel];i=int(rr.argmax())
        z.append(dict(window_um=[lo,hi],points=len(w),max_R=float(rr[i]),min_T=float(tt.min()),worst_wavelength_um=float(w[i]),V=float(max(0,rr[i]/TARGET-1)),U=float(np.mean(np.maximum(rr/TARGET-1,0)**2)),pass_window=bool(rr.max()<=TARGET+1e-12),max_energy_error=float(np.max(abs(rr+tt-1)))))
    return z

def dense_audit(ds,ns):
    dense=np.concatenate([np.linspace(lo,hi,DENSE_N) for lo,hi in WINDOWS])
    offset=np.concatenate([lo+(np.arange(DENSE_N)+.5)*(hi-lo)/DENSE_N for lo,hi in WINDOWS])
    a=metrics(ds,ns,dense);b=metrics(ds,ns,offset)
    rc=KERNEL.reflection_recursion(dense,ds,ns)
    rm,_=KERNEL.tmm_normal(dense,ds,ns)
    # Explicitly audit local maxima by scalar bounded optimization in grid brackets.
    from scipy.optimize import minimize_scalar
    extrema=[];extra=0
    for lo,hi in WINDOWS:
        w=np.linspace(lo,hi,DENSE_N);rr,_=KERNEL.tmm_normal(w,ds,ns)
        ids=np.flatnonzero((rr[1:-1]>rr[:-2])&(rr[1:-1]>rr[2:]))+1
        peaks=[(float(lo),float(rr[0])),(float(hi),float(rr[-1]))]
        for j in ids:
            fit=minimize_scalar(lambda q:-float(KERNEL.tmm_normal([q],ds,ns)[0][0]),bounds=(w[j-1],w[j+1]),method='bounded',options={'xatol':1e-12})
            extra+=int(fit.nfev);peaks.append((float(fit.x),float(-fit.fun)))
        extrema.append(dict(window_um=[lo,hi],max_R=max(y for x,y in peaks),peaks=[dict(wavelength_um=x,R=y) for x,y in peaks]))
    worst=max([x['max_R'] for x in a+b+extrema])
    return dict(dense=a,offset=b,extrema=extrema,worst_R=worst,V=max(0.,worst/TARGET-1),all_targets_pass=bool(worst<=TARGET+1e-12),protected_short_pass=bool(max(a[0]['max_R'],b[0]['max_R'],extrema[0]['max_R'])<=TARGET+1e-12),matrix_recursion_max_error=float(np.max(abs(rm-rc))),audit_extra_scalar_calls=extra,audit_cost=dict(matrix_stack_calls=5+extra,matrix_wavelength_samples=4*len(dense)+extra,matrix_wavelength_layer_updates=(4*len(dense)+extra)*len(ds),independent_recursion_stack_calls=1,independent_recursion_wavelength_samples=len(dense),independent_recursion_wavelength_layer_updates=len(dense)*len(ds)))

def audit_protected(ds,ns,base):
    dense=np.concatenate([np.linspace(lo,hi,DENSE_N) for lo,hi in WINDOWS])
    offset=np.concatenate([lo+(np.arange(DENSE_N)+.5)*(hi-lo)/DENSE_N for lo,hi in WINDOWS])
    grid=np.concatenate((dense,offset))
    br,_=KERNEL.tmm_normal(grid,base,BASE_N);mask=br<=.008
    rr,_=KERNEL.tmm_normal(grid,ds,ns)
    return dict(points=int(mask.sum()),max_R=float(rr[mask].max()),pass_frozen_protected_subset=bool(rr[mask].max()<=TARGET+1e-12),audit_cost=dict(matrix_stack_calls=2,matrix_wavelength_samples=2*len(grid),matrix_wavelength_layer_updates=len(grid)*(len(base)+len(ds))))

def choose(pool,method,seed):
    out=[];rng=np.random.default_rng(seed+9127)
    for k in (1,2,3):
        group=[p for p in pool if p['pack_length']==k]
        if method=='anchor_identity':arr=sorted(group,key=lambda p:(p['E_anchor'],p['screen_score'][1],p['screen_score'][2]))
        elif method=='multipoint_identity':arr=sorted(group,key=lambda p:(p['E_multi'],p['screen_score'][1],p['screen_score'][2]))
        elif method=='random_pack':arr=[group[j] for j in rng.permutation(len(group))]
        elif method=='best_V':arr=sorted(group,key=lambda p:(p['screen_score'][1],p['screen_score'][2]))
        elif method=='phase_covered':
            arr=[]
            for phase in (.25,.75):
                arr.append(min(group,key=lambda p:(abs(p['phase_mod_pi']-phase),p['screen_score'][1],p['id'])))
            arr += sorted(group,key=lambda p:p['id'])
        distinct=[]
        for p in arr:
            if p['id'] not in [x['id'] for x in distinct]:distinct.append(p)
            if len(distinct)==STARTS_PER_LENGTH:break
        assert len(distinct)==STARTS_PER_LENGTH
        out.extend(distinct)
    return out

def refine(p,pmask,wl,seed):
    rng=np.random.default_rng(seed);ds=np.array(p['d']);nn=np.array(p['n']);start=ds.copy();pos=p['position'];k=p['pack_length'];
    # Pack total is held fixed. Neighbor motion is bounded equally for all methods.
    lower=start.copy();upper=start.copy();lower[pos:pos+k]=np.maximum(LOW,start[pos:pos+k]-.25);upper[pos:pos+k]=np.minimum(HIGH,start[pos:pos+k]+.25)
    for j in (pos-1,pos+k):
        if 0<=j<len(ds):lower[j]=max(LOW,start[j]-.18);upper[j]=min(HIGH,start[j]+.18)
    bestscore=None;bestglobal=None;trace=[]
    for call in range(LOCAL_CALLS):
        if call==0:trial=ds.copy()
        else:
            scale=(.20 if call<LOCAL_CALLS*.4 else .07 if call<LOCAL_CALLS*.75 else .02)
            anchor=ds if call%11 else start
            trial=anchor+rng.normal(0,scale,len(ds))*(upper-lower)
            trial=np.clip(trial,lower,upper)
            trial[pos:pos+k]=project_sum(trial[pos:pos+k],p['pack_total_um'],lower[pos:pos+k],upper[pos:pos+k])
            for shrink in range(30):
                if legal(trial,nn):break
                trial=(trial+ds)/2
            if not legal(trial,nn):trial=ds.copy()
        rr,_=KERNEL.tmm_normal(wl,trial,nn);score=values(rr,pmask)
        if bestglobal is None or score[1:]<bestglobal['score'][1:]:bestglobal=dict(d=trial.tolist(),n=nn.tolist(),score=score)
        if bestscore is None or score<bestscore:bestscore=score;ds=trial.copy();trace.append(dict(call=call+1,score=score,d=trial.tolist()))
    return dict(pool_id=p['id'],pack_length=k,position=pos,selected_source=p['source'],initial_score=p['screen_score'],initial_E_anchor=p['E_anchor'],initial_E_multi=p['E_multi'],calls=LOCAL_CALLS,wavelength_layer_updates=LOCAL_CALLS*len(wl)*len(nn),final_d=ds.tolist(),final_n=nn.tolist(),final_score=bestscore,best_global=bestglobal,improvement_trace=trace)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--kernel-root',type=Path,default=DEFAULT_KERNEL);ap.add_argument('--out',type=Path,default=ROOT/'results');args=ap.parse_args()
    k=load_kernel(args.kernel_root);out=args.out;out.mkdir(parents=True,exist_ok=True)
    wl=np.concatenate([np.linspace(lo,hi,TRAIN_N) for lo,hi in WINDOWS]);runs=[];bases={};pools={};pool_stats={};clock=time.perf_counter()
    config=dict(model='SYNTHETIC n=1.45,2.35; k=0; n0=1, semi-infinite ns=3.42; normal incidence; no backside',windows_um=WINDOWS,target_max_R=TARGET,thickness_bounds_um=[LOW,HIGH],max_canonical_layers=9,total_thickness_max_um=TOTAL_MAX,pack_total_by_length_um=PACK_TOTALS,seeds=SEEDS,methods=METHODS,training_points_per_window=TRAIN_N,audit_dense_points_per_window=DENSE_N,audit_offset_points_per_window=DENSE_N,refinement_calls_per_selected_pack=LOCAL_CALLS,selected_packs_per_length=STARTS_PER_LENGTH,base_stacks=STARTS,kernel_source='verified_kernel/run_experiment.py; unchanged copy of original coating-research-experiments kernel',kernel_sha256=hashlib.sha256((args.kernel_root/'run_experiment.py').read_bytes()).hexdigest(),fixed_protected_mask='all original training constraints with initial R <= 0.008, no target relaxation',local_rule='lexicographic protected-constraint violation, global maximum standardized violation, mean squared positive violation; fixed pack total, pack +/-0.25 um and immediate old neighbors +/-0.18 um',archive_rule='keep original 6-layer base; separately archive full-target best V and fully protected shortlist result',scope='one finite editing round, not end-to-end layer synthesis; all screening evaluations including rejected candidates are charged identically to every method')
    (out/'config.json').write_text(json.dumps(config,indent=2))
    for ci,(case,base_list) in enumerate(STARTS.items()):
        base=np.array(base_list);br,_=k.tmm_normal(wl,base,BASE_N);pmask=br<=.008;base_score=values(br,pmask);ba=dense_audit(base,BASE_N);bases[case]=dict(d=base.tolist(),n=BASE_N.tolist(),audit=ba,protected_training_point_count=int(pmask.sum()),score=base_score)
        for seed in SEEDS:
            pool=build_pool(base,seed);screen_updates=0
            for p in pool:
                rr,_=k.tmm_normal(wl,p['d'],p['n']);p['screen_score']=values(rr,pmask);screen_updates+=len(wl)*len(p['d'])
            pools[f'{case}:{seed}']=pool;pool_stats[f'{case}:{seed}']=dict(LAST_POOL_STATS)
            for mi,method in enumerate(METHODS):
                starttime=time.perf_counter();selected=choose(pool,method,seed);ref=[]
                for j,p in enumerate(selected):ref.append(refine(p,pmask,wl,seed+10000*ci+100*j))
                # All algorithms may retain their common full-screen archive: this
                # gives best-V a fair strong baseline and prevents hidden lookups.
                allcand=[dict(d=base.tolist(),n=BASE_N.tolist(),score=base_score,origin='base')]
                allcand += [dict(d=p['d'],n=p['n'],score=p['screen_score'],origin=f"screen:{p['id']}") for p in pool]
                allcand += [dict(**r['best_global'],origin=f"refine:{r['pool_id']}") for r in ref]
                protected=[z for z in allcand if z['score'][0]<=1e-12]
                # Include protection-refined terminal state, which can differ from
                # each run's unconstrained global archive.
                protected += [dict(d=r['final_d'],n=r['final_n'],score=r['final_score'],origin=f"protected_refine:{r['pool_id']}") for r in ref if r['final_score'][0]<=1e-12]
                winner=min(allcand,key=lambda z:z['score'][1:]);pwinner=min(protected,key=lambda z:z['score'][1:]);audit=dense_audit(winner['d'],winner['n']);pa=dense_audit(pwinner['d'],pwinner['n']);pa['frozen_protected_subset']=audit_protected(pwinner['d'],pwinner['n'],base);audit['frozen_protected_subset']=audit_protected(winner['d'],winner['n'],base);cd,cn=canonical(winner['d'],winner['n']);pd,pn=canonical(pwinner['d'],pwinner['n'])
                nominal_calls=len(pool)+len(selected)*LOCAL_CALLS;updates=screen_updates+sum(r['wavelength_layer_updates'] for r in ref)
                row=dict(case=case,seed=seed,method=method,screen_calls=len(pool),refinement_calls=len(selected)*LOCAL_CALLS,total_search_stack_calls_charged=nominal_calls,total_search_wavelength_layer_updates_charged=updates,screen_shared_once_in_actual_execution=True,nominal_local_layer_length_histogram={str(6+x):sum(r['pack_length']==x for r in ref)*LOCAL_CALLS for x in (1,2,3)},wall_seconds_excluding_shared_screen=time.perf_counter()-starttime,best_global=winner,best_global_audit=audit,best_global_canonical_d=cd.tolist(),best_global_canonical_n=cn.tolist(),best_protected=pwinner,best_protected_audit=pa,best_protected_canonical_d=pd.tolist(),best_protected_canonical_n=pn.tolist(),protected_short_then_improved_long=bool(pa['protected_short_pass'] and max(x['max_R'] for x in pa['dense'][1:]+pa['offset'][1:]+pa['extrema'][1:])<max(x['max_R'] for x in ba['dense'][1:]+ba['offset'][1:]+ba['extrema'][1:])-1e-9),refinements=ref)
                runs.append(row)
                print(json.dumps(dict(case=case,seed=seed,method=method,worst_R=audit['worst_R'],protected_worst_R=pa['worst_R'],protected_short=pa['protected_short_pass'],all_pass=pa['all_targets_pass'],calls=nominal_calls)),flush=True)
                (out/'partial_runs.json').write_text(json.dumps(runs,indent=2))
    result=dict(config=config,environment=dict(python=sys.version,numpy=np.__version__,platform=platform.platform()),bases=bases,runs=runs,pools=pools,pool_construction_statistics=pool_stats,wall_seconds=time.perf_counter()-clock)
    (out/'results.json').write_text(json.dumps(result,indent=2));(out/'partial_runs.json').unlink()
    flat=[]
    for r in runs:
        flat.append({kk:r[kk] for kk in ('case','seed','method','screen_calls','refinement_calls','total_search_stack_calls_charged','total_search_wavelength_layer_updates_charged','wall_seconds_excluding_shared_screen','protected_short_then_improved_long')}|dict(best_global_R=r['best_global_audit']['worst_R'],best_protected_R=r['best_protected_audit']['worst_R'],protected_short_pass=r['best_protected_audit']['protected_short_pass'],all_targets_pass=r['best_global_audit']['all_targets_pass'],global_layer_count=len(r['best_global_canonical_d']),protected_layer_count=len(r['best_protected_canonical_d']),global_total_um=sum(r['best_global_canonical_d']),protected_total_um=sum(r['best_protected_canonical_d'])))
    with (out/'results.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
    summary=[]
    for case in STARTS:
        for method in METHODS:
            rr=[r for r in runs if r['case']==case and r['method']==method];best=np.array([r['best_global_audit']['worst_R'] for r in rr]);prot=np.array([r['best_protected_audit']['worst_R'] for r in rr]);summary.append(dict(case=case,method=method,seeds=len(rr),global_R_min=float(best.min()),global_R_median=float(np.median(best)),global_R_max=float(best.max()),protected_R_min=float(prot.min()),protected_R_median=float(np.median(prot)),protected_R_max=float(prot.max()),all_target_success=sum(r['best_global_audit']['all_targets_pass'] for r in rr),short_preserved_long_improved=sum(r['protected_short_then_improved_long'] for r in rr)))
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    with (out/'summary.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
    print('DONE',time.perf_counter()-clock,flush=True)
if __name__=='__main__':main()
