#!/usr/bin/env python3
"""Pilot: finite layer edits followed by IDENTICAL continuous minimax refinement."""
from __future__ import annotations
import argparse,csv,hashlib,importlib.util,json,math,platform,time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize

ROOT=Path(__file__).resolve().parent
N=(1.45,math.sqrt(3.42),2.35)
D_SEEDS=(.2,1/math.sqrt(3.42),.9)
LO=.005;HI=2.;NMAX=6
TRAIN=np.r_[np.linspace(3,5,41),np.linspace(8,12,41)]
SEEDS=(11,29,47,83)
METHODS=('one_edit_local','stagnation_two_edit_local')
WORK_CHECKPOINTS=(10000,30000,60000)
LOCAL_CALLS=96
IMPROVEMENT=1e-7
KERNEL=None
KNOWN_D=(.8687914311440501,.16595496505818463,.0053528155003879085,.0051792662818528346,.2742767404282964,.5352681554140437)
KNOWN=tuple(zip((0,2,0,2,0,2),KNOWN_D))

def load_kernel():
    global KERNEL
    spec=importlib.util.spec_from_file_location('continuous_original_kernel',ROOT/'verified_kernel/run_experiment.py')
    KERNEL=importlib.util.module_from_spec(spec);spec.loader.exec_module(KERNEL)

def canonical(s):
    out=[]
    for m,d in s:
        if out and out[-1][0]==m:out[-1]=(m,out[-1][1]+float(d))
        else:out.append((int(m),float(d)))
    return tuple(out)

def legal(s):
    return len(s)<=NMAX and all(m in range(3) and LO-1e-12<=d<=HI+1e-12 for m,d in s) and all(s[i][0]!=s[i+1][0] for i in range(len(s)-1))

def key(s):return tuple((int(m),float(d)) for m,d in s)
def decode(s):return np.array([d for m,d in s]),np.array([N[m] for m,d in s])

def neighbors(s):
    out=set()
    for i in range(len(s)):
        z=canonical(s[:i]+s[i+1:])
        if legal(z):out.add(z)
        for m in range(3):
            for d in D_SEEDS:
                z=canonical(s[:i]+((m,d),)+s[i+1:])
                if legal(z):out.add(z)
    for i in range(len(s)+1):
        for m in range(3):
            for d in D_SEEDS:
                z=canonical(s[:i]+((m,d),)+s[i:])
                if legal(z):out.add(z)
    out.discard(s)
    return tuple(sorted(out))

def two_neighbors(s,one):
    out=set()
    for mid in one:out.update(neighbors(mid))
    return tuple(sorted(out-set(one)-{s}))

class LocalLimit(Exception):pass
class WorkLimit(Exception):pass

class Experiment:
    def __init__(self,seed,method,work_limit):
        self.seed=seed;self.method=method;self.rng=np.random.default_rng(seed);self.limit=work_limit
        self.calls=0;self.work=0;self.layers=0;self.cache={};self.best=None;self.trace=[];self.snapshots=[];self.evaluated=[]
        self.checkpoints=[x for x in WORK_CHECKPOINTS if x<=work_limit];self.next_check=0;self.start=time.perf_counter();self.events=[];self.repairs=[]
        self.graph_seconds=0.;self.refine_seconds=0.

    def rank(self,s):return (*self.cache[s]['score'],len(s),sum(d for m,d in s),s)

    def snapshot(self,b):
        return dict(budget=b,work_units=self.work,calls=self.calls,active_wavelength_layer_updates=self.layers,
                    best_stack=self.best,score=self.cache[self.best]['score'],layers=len(self.best),
                    wall_seconds=time.perf_counter()-self.start)

    def evaluate(self,s):
        s=key(s)
        if s in self.cache:return self.cache[s]
        assert legal(s)
        cost=1+len(s)
        if self.work+cost>self.limit:raise WorkLimit
        while self.next_check<len(self.checkpoints) and self.work+cost>self.checkpoints[self.next_check]:
            self.snapshots.append(self.snapshot(self.checkpoints[self.next_check]));self.next_check+=1
        R,T=KERNEL.tmm_normal(TRAIN,*decode(s));self.calls+=1;self.work+=cost;self.layers+=len(TRAIN)*len(s)
        info=dict(score=(float(np.max(R)),float(np.mean(R))),R=R)
        self.cache[s]=info;self.evaluated.append(s)
        if self.best is None or self.rank(s)<self.rank(self.best):
            self.best=s;self.trace.append(dict(call=self.calls,work_units=self.work,stack=s,score=info['score']))
        while self.next_check<len(self.checkpoints) and self.work==self.checkpoints[self.next_check]:
            self.snapshots.append(self.snapshot(self.checkpoints[self.next_check]));self.next_check+=1
        return info

    def refine(self,s,origin):
        begin=self.calls;ts=time.perf_counter();seen=[];materials=tuple(m for m,d in s)
        def spectrum(x):
            candidate=tuple(zip(materials,np.clip(x,LO,HI)))
            if candidate not in self.cache and self.calls-begin>=LOCAL_CALLS:raise LocalLimit
            z=self.evaluate(candidate);seen.append(candidate);return z['R']
        try:
            R=spectrum(np.array([d for m,d in s]));x0=np.r_[[d for m,d in s],float(np.max(R))]
            if len(s):
                def constraints(x):return x[-1]-spectrum(x[:-1])
                jac=np.r_[np.zeros(len(s)),1.]
                fit=minimize(lambda x:float(x[-1]),x0,jac=lambda x:jac,method='SLSQP',
                             bounds=[(LO,HI)]*len(s)+[(0.,1.)],constraints=[dict(type='ineq',fun=constraints)],
                             options=dict(maxiter=40,ftol=1e-10,eps=1e-6,disp=False))
                spectrum(fit.x[:-1]);status=str(fit.message)
            else:status='empty stack'
        except LocalLimit:status='96 actual spectrum call local cap'
        finally:self.refine_seconds+=time.perf_counter()-ts
        if not seen:return s
        best=min(set(seen),key=self.rank)
        self.repairs.append(dict(origin=origin,calls=self.calls-begin,input=s,output=best,score=self.cache[best]['score'],status=status))
        return best

    def shuffled(self,pool):return [pool[int(j)] for j in self.rng.permutation(len(pool))]
    def improved(self,a,b):return self.cache[a]['score'][0]<self.cache[b]['score'][0]-IMPROVEMENT

    def full_restart(self):
        s=[]
        for j in range(NMAX):
            choices=[m for m in range(3) if not s or m!=s[-1][0]]
            s.append((choices[int(self.rng.integers(len(choices)))],float(self.rng.uniform(LO,HI))))
        return tuple(s)

    def run(self):
        current=();self.evaluate(current);rounds=0
        try:
            while True:
                rounds+=1;t=time.perf_counter();one=neighbors(current);self.graph_seconds+=time.perf_counter()-t
                repaired=[];start_calls=self.calls
                for s in self.shuffled(one):repaired.append(self.refine(s,'one_edit'))
                nxt=min([current]+repaired,key=self.rank)
                self.events.append(dict(event='one_edit_neighborhood',round=rounds,pool_size=len(one),calls=self.calls-start_calls,
                                        before=current,before_score=self.cache[current]['score'],best=nxt,best_score=self.cache[nxt]['score']))
                if self.improved(nxt,current):current=nxt;continue
                self.events.append(dict(event='finite_one_edit_stagnation',round=rounds,call=self.calls,work_units=self.work,stack=current,score=self.cache[current]['score']))
                if self.method=='stagnation_two_edit_local':
                    t=time.perf_counter();two=two_neighbors(current,one);self.graph_seconds+=time.perf_counter()-t
                    self.events.append(dict(event='two_edit_begin',round=rounds,pool_size=len(two),call=self.calls,work_units=self.work))
                    repaired=[];start_calls=self.calls
                    for s in self.shuffled(two):repaired.append(self.refine(s,'two_edit'))
                    nxt=min([current]+repaired,key=self.rank)
                    self.events.append(dict(event='two_edit_complete',round=rounds,pool_size=len(two),calls=self.calls-start_calls,
                                            before=current,before_score=self.cache[current]['score'],best=nxt,best_score=self.cache[nxt]['score']))
                    if self.improved(nxt,current):current=nxt;continue
                current=self.refine(self.full_restart(),'random_full_restart')
                self.events.append(dict(event='full_restart',round=rounds,call=self.calls,work_units=self.work,stack=current,score=self.cache[current]['score']))
        except WorkLimit:pass
        present={s['budget'] for s in self.snapshots}
        for b in self.checkpoints:
            if b not in present:self.snapshots.append(self.snapshot(b))
        self.snapshots.sort(key=lambda s:s['budget'])
        return dict(seed=self.seed,method=self.method,calls=self.calls,work_units=self.work,active_wavelength_layer_updates=self.layers,
                    wall_seconds=time.perf_counter()-self.start,graph_seconds=self.graph_seconds,refine_seconds=self.refine_seconds,
                    best_stack=self.best,best_score=self.cache[self.best]['score'],evaluated_stacks=self.evaluated,
                    improvement_trace=self.trace,events=self.events,repairs=self.repairs,snapshots=self.snapshots)

def audit(s):
    wl=np.unique(np.r_[np.linspace(3,5,4097),3+(np.arange(4097)+.5)*2/4097,
                        np.linspace(8,12,4097),8+(np.arange(4097)+.5)*4/4097])
    R,T=KERNEL.tmm_normal(wl,*decode(s));q=KERNEL.reflection_recursion(wl,*decode(s));worst=float(np.max(R))
    windows=[]
    for lo,hi in ((3.,5.),(8.,12.)):
        mask=(wl>=lo)&(wl<=hi);rr=R[mask];ww=wl[mask];j=int(np.argmax(rr))
        windows.append(dict(window_um=[lo,hi],max_R=float(rr[j]),wavelength_um=float(ww[j])))
    return dict(points=len(wl),worst_R=worst,strict_one_percent_pass=worst<=.01+1e-12,
                feasible_four_percent_pass=worst<=.04+1e-12,V_one_percent=max(0,worst/.01-1),windows=windows,
                max_energy_error=float(np.max(abs(R+T-1))),matrix_recursion_max_error=float(np.max(abs(R-q))),
                matrix_calls=1,independent_recursion_calls=1,each_wavelength_layer_updates=len(wl)*len(s))

def write_csv(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=ROOT/'pilot');ap.add_argument('--seeds',type=int,default=4)
    ap.add_argument('--work-budget',type=int,default=60000,choices=WORK_CHECKPOINTS);a=ap.parse_args();load_kernel();a.out.mkdir(parents=True,exist_ok=True);ts=time.perf_counter()
    known=audit(KNOWN);assert legal(KNOWN) and known['feasible_four_percent_pass']
    config=dict(model='SYNTHETIC constant n and explicit k=0; not real material',material_n=N,material_k=[0.,0.,0.],n0=1.,ns=3.42,
                geometry='coherent normal incidence, planar isotropic, semi-infinite substrate, no backside',
                max_layers=NMAX,positive_thickness_bounds_um=[LO,HI],total_max_um=NMAX*HI,proposal_thickness_seeds_um=D_SEEDS,
                windows_um=[[3.,5.],[8.,12.]],training_points_per_window=41,training_wavelengths_um=TRAIN.tolist(),
                strict_target_R=.01,strict_feasibility='not established in this continuous domain',feasible_calibration_target_R=.04,
                known_feasible_stack=KNOWN,known_feasible_audit=known,known_feasible_used_by_search=False,
                score='minimize actual worst R, tie mean R and physical structure; targets are two separate reporting thresholds, no threshold-specific optimization',
                methods=METHODS,seeds=SEEDS[:a.seeds],work_budget=a.work_budget,work_checkpoints=[x for x in WORK_CHECKPOINTS if x<=a.work_budget],
                work_proxy='sum(1+actual canonical layers); no zero-thickness padding; actual calls, active layer updates and wall time separate',
                local_solver=dict(name='SLSQP epigraph minimax',maxiter=40,ftol=1e-10,finite_difference_eps_um=1e-6,max_actual_spectrum_calls=LOCAL_CALLS),
                significant_working_state_improvement_R=IMPROVEMENT,
                mechanism='finite any-position one-edit proposals, same continuous all-layer minimax repair; if no repaired endpoint improves by >1e-7 R, optional raw graph-distance-two endpoints with same repair, no middle score gate; otherwise same full six-layer random restart',
                canonicalization='adjacent same material merged and checked against 2 um bound after EVERY edit; does not split layers to evade limit',
                accounting='actual fresh TMM per exact new structure; one run exact optical cache; finite-difference and rejected points charged; no cross-method optical cache; final audits outside search',
                python=platform.python_version(),numpy=np.__version__,kernel_sha256=hashlib.sha256((ROOT/'verified_kernel/run_experiment.py').read_bytes()).hexdigest())
    (a.out/'config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n');runs=[];rows=[];audits={}
    for seed in SEEDS[:a.seeds]:
        for method in METHODS:
            r=Experiment(seed,method,a.work_budget).run()
            for snap in r['snapshots']:
                s=tuple(map(tuple,snap['best_stack']))
                if s not in audits:audits[s]=audit(s)
                snap['audit']=audits[s]
                rows.append(dict(seed=seed,method=method,budget=snap['budget'],calls=snap['calls'],work_units=snap['work_units'],
                                 active_wavelength_layer_updates=snap['active_wavelength_layer_updates'],wall_seconds=snap['wall_seconds'],
                                 layers=snap['layers'],train_worst_R=snap['score'][0],dense_worst_R=snap['audit']['worst_R'],
                                 V_one_percent=snap['audit']['V_one_percent'],strict_one_percent_pass=snap['audit']['strict_one_percent_pass'],
                                 feasible_four_percent_pass=snap['audit']['feasible_four_percent_pass']))
            runs.append(r);print(seed,method,'calls',r['calls'],'work',r['work_units'],'best',r['best_score'][0],flush=True)
    summary=[]
    for method in METHODS:
        for b in config['work_checkpoints']:
            sub=[r for r in rows if r['method']==method and r['budget']==b]
            summary.append(dict(method=method,budget=b,runs=len(sub),strict_one_percent_passes=sum(r['strict_one_percent_pass'] for r in sub),
                                feasible_four_percent_passes=sum(r['feasible_four_percent_pass'] for r in sub),
                                median_dense_worst_R=float(np.median([r['dense_worst_R'] for r in sub])),
                                min_dense_worst_R=min(r['dense_worst_R'] for r in sub),max_dense_worst_R=max(r['dense_worst_R'] for r in sub),
                                median_calls=float(np.median([r['calls'] for r in sub]))))
    result=dict(config=config,runs=runs,summary=summary,total_wall_seconds=time.perf_counter()-ts,
                audit_cost=dict(unique_stacks=len(audits),matrix_calls=1+len(audits),independent_recursion_calls=1+len(audits),
                                each_wavelength_layer_updates=known['each_wavelength_layer_updates']+sum(x['each_wavelength_layer_updates'] for x in audits.values())),
                audit_scope='Per completed run, audit saved checkpoints without feedback to later searches; per window union of linspace(lo,hi,4097) and lo+(j+0.5)*(hi-lo)/4097 for j=0..4096 (8193 unique points; shared center); 9/41 training wavelengths overlap; fixed finite grid, not a continuous interval certificate')
    (a.out/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');write_csv(a.out/'runs.csv',rows);write_csv(a.out/'summary.csv',summary)
    print(json.dumps(summary,ensure_ascii=False),flush=True);print('total seconds',result['total_wall_seconds'],flush=True)

if __name__=='__main__':main()
