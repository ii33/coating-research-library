#!/usr/bin/env python3
"""Finite-catalog empty-stack search. Synthetic normal-incidence research only."""
from __future__ import annotations
import argparse, csv, hashlib, importlib.util, itertools, json, math, platform, time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
N0=1.; NS=3.42; NMAX=4
MATERIALS=(1.45, math.sqrt(NS), 2.35)
THICKNESSES=(.2, 1/math.sqrt(NS), .9)
ACTIONS=tuple(itertools.product(range(3), range(3)))
SEEDS=(11,29,47,83)
BUDGETS=(81,241,721)
METHODS=((1,1,'score'),(1,4,'score'),(1,4,'complex'),(1,4,'intensity'),
         (2,1,'score'),(2,4,'score'),(2,4,'complex'),(2,4,'intensity'))
TRAIN=np.r_[np.linspace(3,5,41),np.linspace(8,12,41)]
ANCHOR_WL=np.array([3.,3.5,4.,4.5,5.,8.,10.,12.])
ANCHORS=np.array([int(np.argmin(abs(TRAIN-x))) for x in ANCHOR_WL])
REFERENCE_Z=-4.
KERNEL=None

def load_kernel(path):
    global KERNEL
    spec=importlib.util.spec_from_file_location('verified_coating_kernel',Path(path)/'run_experiment.py')
    KERNEL=importlib.util.module_from_spec(spec);spec.loader.exec_module(KERNEL)
    return KERNEL

def decode(stack):
    return np.array([THICKNESSES[d] for m,d in stack]),np.array([MATERIALS[m] for m,d in stack])

def canonical(ds,ns):
    dd=[];nn=[]
    for d,n in zip(ds,ns):
        if d==0: continue
        if nn and n==nn[-1]:dd[-1]+=float(d)
        else:dd.append(float(d));nn.append(float(n))
    return np.asarray(dd),np.asarray(nn)

def legal(stack):
    if len(stack)>NMAX:return False
    if any(a not in ACTIONS for a in stack):return False
    if any(stack[j][0]==stack[j+1][0] for j in range(len(stack)-1)):return False
    ds,ns=decode(stack)
    return bool(np.all(ds>=.2-1e-14) and np.all(ds<=.9+1e-14) and ds.sum()<=3.6+1e-13)

def all_stacks():
    out=[()];level=[()]
    for depth in range(NMAX):
        level=[(a,)+s for s in level for a in ACTIONS if not s or a[0]!=s[0][0]]
        out.extend(level)
    assert len(out)==2332 and all(legal(s) for s in out)
    return out

def optics(stack,wl,padded=True):
    ds,nn=decode(stack);D=float(ds.sum())
    if padded:
        ds=np.r_[ds,np.zeros(NMAX-len(ds))];nn=np.r_[nn,np.ones(NMAX-len(nn))]
    R,T=KERNEL.tmm_normal(wl,ds,nn)
    media=np.r_[N0,nn,NS]
    rr=np.full(len(wl),(media[-2]-media[-1])/(media[-2]+media[-1]),dtype=complex)
    for j in range(len(ds)-1,-1,-1):
        rj=(media[j]-media[j+1])/(media[j]+media[j+1])
        phase=np.exp(4j*np.pi*media[j+1]*ds[j]/wl)
        rr=(rj+rr*phase)/(1+rj*rr*phase)
    # Substrate interface is z=0, stack surface is z=-D, common air plane z=-4 um.
    # exp(-i wt), forward exp(+i kz): r_common=r_surface exp(2 i k0 (4-D)).
    common=rr*np.exp(4j*np.pi*N0*(-REFERENCE_Z-D)/wl)
    return R,T,common

def cases():
    out=[dict(name='simple_single_line_ar',kind='ar',windows=[[4.,4.]],tolerance=.0001),
         dict(name='single_window_ar_3_5',kind='ar',windows=[[3.,5.]],tolerance=.01),
         dict(name='dual_window_ar_3_5_8_12',kind='ar',windows=[[3.,5.],[8.,12.]],tolerance=.01)]
    for seed in SEEDS:
        rng=np.random.default_rng(seed+51000);s=()
        for _ in range(4):
            choices=[a for a in ACTIONS if not s or a[0]!=s[0][0]]
            s=(choices[int(rng.integers(len(choices)))],)+s
        out.append(dict(name=f'planted_four_layer_{seed}',kind='planted',windows=[[3.,5.],[8.,12.]],tolerance=.002,planted_stack=s))
    return out

def mask_for(case,wl):
    mask=np.zeros(len(wl),bool)
    for lo,hi in case['windows']:
        mask|=(wl>=lo-1e-12)&(wl<=hi+1e-12)
    return mask

def score_from_R(R,target,case,wl):
    mask=mask_for(case,wl);delta=R[mask] if case['kind']=='ar' else abs(R[mask]-target[mask])
    g=delta/case['tolerance']-1
    v=float(max(0.,np.max(g)));u=float(np.mean(np.maximum(g,0.)**2))
    return (v,u,float(np.max(g)))

def node_order(node):return (*node['score'],len(node['stack']),float(decode(node['stack'])[0].sum()),node['stack'])

def choose(frontier,width,mode):
    ranked=sorted(frontier,key=node_order)
    if mode=='score' or len(ranked)<=1:return ranked[:width]
    # Quality-filtered farthest-point sampling, fixed top-4B pool and fixed scales.
    pool=ranked[:max(width,4*width)];selected=[pool.pop(0)]
    feature='complex_signature' if mode=='complex' else 'intensity_signature'
    while pool and len(selected)<width:
        distances=[min(float(np.linalg.norm(n[feature]-s[feature])) for s in selected) for n in pool]
        j=max(range(len(pool)),key=lambda j:(distances[j],tuple(-x for x in pool[j]['score']),-j))
        selected.append(pool.pop(j))
    return selected

def run_search(case,target,seed,h,width,mode):
    rng=np.random.default_rng(seed);budget=max(BUDGETS);calls=0;active_updates=0;seen=set();archive=None;trace=[];snapshots=[]
    frontier=[];expanded=0;complete_expansions=0;expansion_depths={};wall=time.perf_counter()
    def evaluate(s):
        nonlocal calls,active_updates,archive
        assert s not in seen and legal(s)
        seen.add(s);R,T,r=optics(s,TRAIN);calls+=1;active_updates+=2*len(TRAIN)*len(s)
        node=dict(stack=s,score=score_from_R(R,target,case,TRAIN),
                  complex_signature=np.r_[r[ANCHORS].real,r[ANCHORS].imag]/math.sqrt(len(ANCHORS)),
                  intensity_signature=R[ANCHORS]/math.sqrt(len(ANCHORS)))
        if archive is None or node_order(node)<node_order(archive):
            archive=node;trace.append(dict(call=calls,stack=s,score=node['score']))
        if calls in BUDGETS:
            snapshots.append(dict(budget=calls,best_stack=archive['stack'],score=archive['score'],
                active_wavelength_layer_updates=active_updates,padded_wavelength_layer_updates=calls*len(TRAIN)*2*NMAX,
                active_matrix_layer_updates_if_unpadded=active_updates//2,executed_padded_matrix_layer_updates=calls*len(TRAIN)*NMAX))
        return node
    original=evaluate(());frontier=[original]
    while calls<budget and frontier:
        selected=choose(frontier,width,mode);selected_keys={x['stack'] for x in selected}
        frontier=[n for n in frontier if n['stack'] not in selected_keys]
        for parent in selected:
            if calls>=budget:break
            expanded+=1;depth=len(parent['stack']);expansion_depths[str(depth)]=expansion_depths.get(str(depth),0)+1
            steps=min(h,NMAX-depth);current=[parent];complete=True
            for step in range(steps):
                nxt=[]
                for node in current:
                    action_order=rng.permutation(len(ACTIONS))
                    for ai in action_order:
                        a=ACTIONS[int(ai)];s=node['stack']
                        if s and a[0]==s[0][0]:continue
                        child=(a,)+s
                        if calls>=budget:complete=False;break
                        new=evaluate(child);nxt.append(new)
                    if not complete:break
                current=nxt
                if not complete:break
            if complete:
                complete_expansions+=1
                frontier.extend(n for n in current if len(n['stack'])<NMAX)
    assert calls==budget,(case['name'],h,width,mode,calls)
    return dict(case=case['name'],seed=seed,h=h,width=width,mode=mode,method=f'h{h}_w{width}_{mode}',
                calls=calls,actual_optical_stack_calls=2*calls,unique_candidates=len(seen),
                active_wavelength_layer_updates=active_updates,padded_wavelength_layer_updates=calls*len(TRAIN)*2*NMAX,
                wall_seconds=time.perf_counter()-wall,expanded_parents=expanded,complete_expansions=complete_expansions,
                expansion_depths=expansion_depths,original_stack=(),original_score=original['score'],best_stack=archive['stack'],
                best_score=archive['score'],improvement_trace=trace,snapshots=snapshots)

def audit_stack(stack,case,points=4097):
    grids=[]
    for lo,hi in case['windows']:
        grids.append(np.array([lo]) if lo==hi else np.linspace(lo,hi,points))
        if lo!=hi:grids.append(lo+(np.arange(points)+.5)*(hi-lo)/points)
    wl=np.unique(np.concatenate(grids));R,T,r=optics(stack,wl,padded=False)
    target=optics(tuple(map(tuple,case['planted_stack'])),wl,padded=False)[0] if case['kind']=='planted' else np.zeros(len(wl))
    score=score_from_R(R,target,case,wl)
    return dict(points=len(wl),score=score,pass_sampled=score[0]<=1e-12,
                max_energy_error=float(np.max(abs(R+T-1))),complex_power_error=float(np.max(abs(abs(r)**2-R))),
                wavelengths_layer_updates=2*len(wl)*len(stack),audit_cost=dict(candidate_optical_stack_calls=2,target_optical_stack_calls=2 if case['kind']=='planted' else 0,candidate_wavelength_layer_updates=2*len(wl)*len(stack),target_wavelength_layer_updates=2*len(wl)*len(case.get('planted_stack',[]))),scope='fixed dense+half-offset sample audit, no continuum certificate')

def write_csv(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--kernel-root',type=Path,default=ROOT/'verified_kernel');ap.add_argument('--out',type=Path,default=ROOT/'results');args=ap.parse_args()
    load_kernel(args.kernel_root);args.out.mkdir(exist_ok=True,parents=True);started=time.perf_counter();cc=cases();stacks=all_stacks()
    config=dict(material_n=MATERIALS,k=0,thickness_catalog_um=THICKNESSES,max_layers=NMAX,max_total_um=3.6,
        min_contiguous_thickness_um=.2,max_contiguous_thickness_um=.9,adjacent_identical='excluded from finite search catalog; canonical physical merges tested separately',
        n0=N0,ns=NS,geometry='normal incidence, coherent planar isotropic, semi-infinite substrate, no backside',
        seeds=SEEDS,budgets=BUDGETS,methods=METHODS,train_wavelengths_um=TRAIN.tolist(),anchors_um=ANCHOR_WL.tolist(),
        common_air_reference_z_um=REFERENCE_Z,substrate_interface_z_um=0.,cases=cc,
        score='lexicographic (max(0,max(g)),mean(max(g,0)^2),max(g)), then physical layer count/total thickness/catalog tuple; AR g=R/tolerance-1, planted g=abs(R-R*)/tolerance-1',
        search='deferred-restart beam/frontier: retain unselected scored states as backup entrances; expand active beam h layers, evaluate all intermediate layers; frontier candidates are h-step endpoints. No thickness refinement, deletion or material swap.',
        diversity='best by score always retained; choose remaining by farthest Euclidean distance within fixed top 4B score-ranked pool; complex=Re/Im r at common plane; intensity=R at same anchors',
        accounting='no cross-method cache; every unique scored stack physically calls verified TMM plus independent complex Fresnel recursion, each padded to 4 iterations. Padded work equal by budget; active-layer work and wall time reported separately. Oracle and final audits outside search budget and counted separately.',
        oracle_scope='exhaustive finite catalog on fixed training constraints; not a continuous-thickness or continuum-wavelength optimum',
        kernel_sha256=hashlib.sha256((args.kernel_root/'run_experiment.py').read_bytes()).hexdigest(),numpy_version=np.__version__,python=platform.python_version())
    oracle_start=time.perf_counter();responses=[];physics_error=0.;energy_error=0.
    for s in stacks:
        R,T,r=optics(s,TRAIN);responses.append(R);physics_error=max(physics_error,float(np.max(abs(R-abs(r)**2))));energy_error=max(energy_error,float(np.max(abs(R+T-1))))
    responses=np.array(responses);stack_ids={s:i for i,s in enumerate(stacks)};targets={};oracles={}
    for c in cc:
        target=responses[stack_ids[tuple(map(tuple,c['planted_stack']))]] if c['kind']=='planted' else np.zeros(len(TRAIN));targets[c['name']]=target
        scores=[score_from_R(R,target,c,TRAIN) for R in responses]
        winner=min(range(len(stacks)),key=lambda i:(*scores[i],len(stacks[i]),float(decode(stacks[i])[0].sum()),stacks[i]))
        oracles[c['name']]=dict(stack=stacks[winner],score=scores[winner],finite_catalog_size=len(stacks),feasible_count=sum(s[0]<=1e-12 for s in scores),dense_audit=audit_stack(stacks[winner],c))
    oracle_cost=dict(stack_evaluations=len(stacks),actual_optical_stack_calls=2*len(stacks),padded_wavelength_layer_updates=2*len(TRAIN)*NMAX*len(stacks),
        active_wavelength_layer_updates=2*len(TRAIN)*sum(map(len,stacks)),wall_seconds=time.perf_counter()-oracle_start,
        complex_recursion_power_max_error=physics_error,lossless_energy_max_error=energy_error)
    print(json.dumps(dict(oracle=oracles,cost=oracle_cost),ensure_ascii=False),flush=True)
    runs=[];audit_cache={};rows=[]
    for c in cc:
        for seed in SEEDS:
            for h,width,mode in METHODS:
                run=run_search(c,targets[c['name']],seed,h,width,mode)
                for snap in run['snapshots']:
                    key=(c['name'],tuple(snap['best_stack']))
                    if key not in audit_cache:audit_cache[key]=audit_stack(snap['best_stack'],c)
                    snap['dense_audit']=audit_cache[key]
                    snap['oracle_V_gap']=snap['score'][0]-oracles[c['name']]['score'][0]
                    rows.append(dict(case=c['name'],seed=seed,method=run['method'],h=h,width=width,mode=mode,budget=snap['budget'],V=snap['score'][0],U=snap['score'][1],signed_max_g=snap['score'][2],train_pass=snap['score'][0]<=1e-12,dense_V=snap['dense_audit']['score'][0],dense_pass=snap['dense_audit']['pass_sampled'],oracle_V_gap=snap['oracle_V_gap'],layers=len(snap['best_stack']),active_wavelength_layer_updates=snap['active_wavelength_layer_updates'],padded_wavelength_layer_updates=snap['padded_wavelength_layer_updates'],stack=json.dumps(snap['best_stack'])))
                runs.append(run)
        print(c['name'],'done',flush=True)
    summary=[]
    for c in cc:
        for h,width,mode in METHODS:
            method=f'h{h}_w{width}_{mode}'
            for b in BUDGETS:
                subset=[r for r in rows if r['case']==c['name'] and r['method']==method and r['budget']==b]
                summary.append(dict(case=c['name'],method=method,budget=b,runs=len(subset),train_passes=sum(r['train_pass'] for r in subset),dense_passes=sum(r['dense_pass'] for r in subset),median_V=float(np.median([r['V'] for r in subset])),min_V=min(r['V'] for r in subset),max_V=max(r['V'] for r in subset),median_dense_V=float(np.median([r['dense_V'] for r in subset])),oracle_V=oracles[c['name']]['score'][0],median_oracle_V_gap=float(np.median([r['oracle_V_gap'] for r in subset]))))
    result=dict(config=config,oracle=oracles,oracle_cost=oracle_cost,runs=runs,summary=summary,total_wall_seconds=time.perf_counter()-started,
        final_audit_unique_case_stacks=len(audit_cache),final_audit_cost=dict(candidate_optical_stack_calls=sum(a['audit_cost']['candidate_optical_stack_calls'] for a in audit_cache.values()),target_optical_stack_calls=sum(a['audit_cost']['target_optical_stack_calls'] for a in audit_cache.values()),candidate_wavelength_layer_updates=sum(a['audit_cost']['candidate_wavelength_layer_updates'] for a in audit_cache.values()),target_wavelength_layer_updates=sum(a['audit_cost']['target_wavelength_layer_updates'] for a in audit_cache.values())),oracle_audit_cost=dict(candidate_optical_stack_calls=sum(a['dense_audit']['audit_cost']['candidate_optical_stack_calls'] for a in oracles.values()),target_optical_stack_calls=sum(a['dense_audit']['audit_cost']['target_optical_stack_calls'] for a in oracles.values()),candidate_wavelength_layer_updates=sum(a['dense_audit']['audit_cost']['candidate_wavelength_layer_updates'] for a in oracles.values()),target_wavelength_layer_updates=sum(a['dense_audit']['audit_cost']['target_wavelength_layer_updates'] for a in oracles.values())),final_audit_scope='run after snapshots; never fed back into search; dense plus offset grids do not prove continuum optimality')
    (args.out/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');write_csv(args.out/'runs.csv',rows);write_csv(args.out/'summary.csv',summary)
    (args.out/'summary.json').write_text(json.dumps(dict(summary=summary,oracle=oracles,oracle_cost=oracle_cost,total_wall_seconds=result['total_wall_seconds']),ensure_ascii=False,indent=2)+'\n')
    print('finished',len(runs),'runs',result['total_wall_seconds'],'seconds',flush=True)
if __name__=='__main__':main()
