#!/usr/bin/env python3
"""Finite-catalog growth/repair falsification experiment. SYNTHETIC optics only."""
from __future__ import annotations
import argparse, csv, hashlib, importlib.util, itertools, json, math, platform, time
from functools import lru_cache
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent
NS=3.42
MATERIALS=(1.45,math.sqrt(NS),2.35)
THICKNESSES=(.2,1/math.sqrt(NS),.9)
ACTIONS=tuple(itertools.product(range(3),range(3)))
TARGET_SEEDS=(11,29,47,83,101,131,167,197,229,263,307,347)
SEARCH_SEEDS=(11,29,47,83)
BUDGETS=(81,241,721)
METHODS=('greedy_front','frontier_w1','frontier_w4','random_full','one_edit_restart','stagnation_two_edit')
TRAIN=np.r_[np.linspace(3,5,41),np.linspace(8,12,41)]
KERNEL=None

def load_kernel():
    global KERNEL
    spec=importlib.util.spec_from_file_location('verified_kernel_growth',ROOT/'verified_kernel/run_experiment.py')
    KERNEL=importlib.util.module_from_spec(spec);spec.loader.exec_module(KERNEL)
    return KERNEL

def legal(s):
    return len(s)<=4 and all(a in ACTIONS for a in s) and all(s[i][0]!=s[i+1][0] for i in range(len(s)-1))

def decode(s):
    return np.array([THICKNESSES[d] for m,d in s]),np.array([MATERIALS[m] for m,d in s])

def catalog():
    out=[()];level=[()]
    for _ in range(4):
        level=[(a,)+s for s in level for a in ACTIONS if not s or a[0]!=s[0][0]]
        out.extend(level)
    return tuple(out)

STACKS=catalog(); IDS={s:i for i,s in enumerate(STACKS)}; FULL_IDS=tuple(i for i,s in enumerate(STACKS) if len(s)==4)

@lru_cache(None)
def neighbors_one(i):
    """One whole finite layer insertion/deletion/reassignment, at ANY position."""
    s=STACKS[i];out=set()
    for p in range(len(s)):
        z=s[:p]+s[p+1:]
        if legal(z):out.add(IDS[z])
        for a in ACTIONS:
            z=s[:p]+(a,)+s[p+1:]
            if legal(z):out.add(IDS[z])
    if len(s)<4:
        for p in range(len(s)+1):
            for a in ACTIONS:
                z=s[:p]+(a,)+s[p:]
                if legal(z):out.add(IDS[z])
    out.discard(i)
    return tuple(sorted(out))

@lru_cache(None)
def neighbors_two(i):
    """Graph-distance exactly two; no optical score gate on intermediate state."""
    one=set(neighbors_one(i));out=set()
    for j in one:out.update(neighbors_one(j))
    return tuple(sorted(out-one-{i}))

def cases(n):
    out=[dict(name='simple_single_line_ar',kind='ar',windows=[[4.,4.]],tolerance=.0001),
         dict(name='single_window_ar',kind='ar',windows=[[3.,5.]],tolerance=.01),
         dict(name='dual_window_ar',kind='ar',windows=[[3.,5.],[8.,12.]],tolerance=.01)]
    for seed in TARGET_SEEDS[:n]:
        rng=np.random.default_rng(seed+51000);s=()
        for _ in range(4):
            options=[a for a in ACTIONS if not s or a[0]!=s[0][0]]
            s=(options[int(rng.integers(len(options)))],)+s
        out.append(dict(name=f'planted_four_layer_{seed}',kind='planted',windows=[[3.,5.],[8.,12.]],tolerance=.002,planted_stack=s,target_seed=seed))
    return out

def optics(i,wl):
    return KERNEL.tmm_normal(wl,*decode(STACKS[i]))

def score(R,target,c,wl):
    mask=np.zeros(len(wl),bool)
    for lo,hi in c['windows']:mask|=(wl>=lo-1e-12)&(wl<=hi+1e-12)
    delta=R[mask] if c['kind']=='ar' else abs(R[mask]-target[mask])
    g=delta/c['tolerance']-1
    return (float(max(0,np.max(g))),float(np.mean(np.maximum(g,0)**2)),float(np.max(g)))

def order(i,sc):
    return (*sc,len(STACKS[i]),float(sum(THICKNESSES[d] for m,d in STACKS[i])),STACKS[i])

class Exhausted(Exception):pass

class Search:
    def __init__(self,c,target,seed,method,limit,work_mode=False):
        self.c=c;self.target=target;self.rng=np.random.default_rng(seed);self.seed=seed;self.method=method
        self.limit=limit;self.work_mode=work_mode;self.scores={};self.evaluated=[];self.best=None;self.trace=[]
        self.calls=0;self.layer_updates=0;self.work_units=0;self.snapshots=[];self.events=[]
        self.checkpoints=tuple(b*5 if work_mode else b for b in BUDGETS if b*5<=limit or not work_mode and b<=limit)
        self.next_checkpoint=0;self.start=time.perf_counter();self.terminated='budget'

    def snapshot(self,budget):
        return dict(budget=budget,calls=self.calls,work_units=self.work_units,
                    active_wavelength_layer_updates=self.layer_updates,wall_seconds=time.perf_counter()-self.start,
                    best_id=self.best,best_stack=STACKS[self.best],score=self.scores[self.best],layers=len(STACKS[self.best]),
                    total_thickness_um=float(sum(THICKNESSES[d] for m,d in STACKS[self.best])))

    def evaluate(self,i):
        if i in self.scores:return self.scores[i]
        cost=1+len(STACKS[i]);used=self.work_units if self.work_mode else self.calls
        if used+(cost if self.work_mode else 1)>self.limit:raise Exhausted
        # Snapshot work checkpoints BEFORE crossing, so each budget is respected.
        if self.work_mode:
            while self.next_checkpoint<len(self.checkpoints) and self.work_units+cost>self.checkpoints[self.next_checkpoint]:
                self.snapshots.append(self.snapshot(self.checkpoints[self.next_checkpoint]));self.next_checkpoint+=1
        R,T=optics(i,TRAIN);sc=score(R,self.target,self.c,TRAIN)
        self.scores[i]=sc;self.evaluated.append(i);self.calls+=1;self.work_units+=cost
        self.layer_updates+=len(TRAIN)*len(STACKS[i])
        if self.best is None or order(i,sc)<order(self.best,self.scores[self.best]):
            self.best=i;self.trace.append(dict(call=self.calls,work_units=self.work_units,id=i,score=sc))
        if not self.work_mode and self.calls in self.checkpoints:self.snapshots.append(self.snapshot(self.calls))
        if self.work_mode:
            while self.next_checkpoint<len(self.checkpoints) and self.work_units==self.checkpoints[self.next_checkpoint]:
                self.snapshots.append(self.snapshot(self.checkpoints[self.next_checkpoint]));self.next_checkpoint+=1
        return sc

    def rank(self,i):return order(i,self.scores[i])
    def shuffled(self,ids):return [ids[int(j)] for j in self.rng.permutation(len(ids))]

    def front_children(self,i):
        s=STACKS[i]
        if len(s)==4:return []
        return [IDS[(a,)+s] for a in ACTIONS if not s or a[0]!=s[0][0]]

    def frontier(self,width):
        frontier=[0]
        while frontier:
            selected=sorted(frontier,key=self.rank)[:width];ss=set(selected)
            frontier=[i for i in frontier if i not in ss]
            for parent in selected:
                for i in self.shuffled(self.front_children(parent)):
                    self.evaluate(i)
                    if len(STACKS[i])<4:frontier.append(i)

    def greedy(self):
        current=0
        while len(STACKS[current])<4:
            pool=self.front_children(current)
            for i in self.shuffled(pool):self.evaluate(i)
            nxt=min([current]+pool,key=self.rank)
            if nxt==current:break
            current=nxt
        self.terminated='irreversible_greedy_stopped'

    def random(self):
        for i in self.shuffled(FULL_IDS):self.evaluate(i)

    def local(self,use_two):
        current=0;restart_count=0
        while len(self.scores)<len(STACKS):
            one=neighbors_one(current)
            for i in self.shuffled(one):self.evaluate(i)
            nxt=min([current]+list(one),key=self.rank)
            if self.rank(nxt)<self.rank(current):current=nxt;continue
            self.events.append(dict(event='one_edit_local_optimum',current=current,call=self.calls,score=self.scores[current]))
            if use_two:
                two=neighbors_two(current)
                for i in self.shuffled(two):self.evaluate(i)
                nxt=min([current]+list(two),key=self.rank)
                if self.rank(nxt)<self.rank(current):
                    self.events.append(dict(event='two_edit_escape',before=current,after=nxt,call=self.calls,
                                            before_score=self.scores[current],after_score=self.scores[nxt]))
                    current=nxt;continue
            # Same full-stack restart rule in both variants; all trial calls charged.
            remaining=[i for i in FULL_IDS if i not in self.scores]
            if not remaining:remaining=[i for i in range(len(STACKS)) if i not in self.scores]
            if not remaining:break
            current=remaining[int(self.rng.integers(len(remaining)))];self.evaluate(current);restart_count+=1
            self.events.append(dict(event='random_full_restart',current=current,call=self.calls))
        self.terminated='catalog_exhausted'

    def run(self):
        self.evaluate(0)
        try:
            if self.method=='greedy_front':self.greedy()
            elif self.method.startswith('frontier_'):self.frontier(int(self.method[-1]))
            elif self.method=='random_full':self.random()
            else:self.local(self.method=='stagnation_two_edit')
        except Exhausted:pass
        # Stopped greedy keeps its actual cost, never presented as equal-budget.
        present={x['budget'] for x in self.snapshots}
        for b in self.checkpoints:
            if b not in present:self.snapshots.append(self.snapshot(b))
        self.snapshots.sort(key=lambda x:x['budget'])
        return dict(case=self.c['name'],seed=self.seed,method=self.method,budget_kind='one_plus_layer_work' if self.work_mode else 'spectral_calls',
                    limit=self.limit,calls=self.calls,active_wavelength_layer_updates=self.layer_updates,work_units=self.work_units,
                    wall_seconds=time.perf_counter()-self.start,terminated=self.terminated,best_id=self.best,best_stack=STACKS[self.best],
                    best_score=self.scores[self.best],evaluated_ids=self.evaluated,improvement_trace=self.trace,events=self.events,snapshots=self.snapshots)

def audit(i,c,points=4097):
    arrays=[]
    for lo,hi in c['windows']:
        arrays.append(np.array([lo]) if lo==hi else np.linspace(lo,hi,points))
        if lo!=hi:arrays.append(lo+(np.arange(points)+.5)*(hi-lo)/points)
    wl=np.unique(np.concatenate(arrays));R,T=optics(i,wl)
    if c['kind']=='planted':
        pi=IDS[tuple(map(tuple,c['planted_stack']))];target=optics(pi,wl)[0]
    else:target=np.zeros(len(wl))
    ds,ns=decode(STACKS[i]);independent=KERNEL.reflection_recursion(wl,ds,ns)
    sc=score(R,target,c,wl);delta=R if c['kind']=='ar' else abs(R-target)
    peak=int(np.argmax(delta))
    return dict(points=len(wl),score=sc,pass_sampled=sc[0]<=1e-12,max_absolute_target_error=float(delta[peak]),
                worst_wavelength_um=float(wl[peak]),max_R=float(np.max(R)),matrix_recursion_max_error=float(np.max(abs(R-independent))),
                max_energy_error=float(np.max(abs(R+T-1))),matrix_calls=1+(c['kind']=='planted'),recursion_calls=1,
                matrix_layer_updates=len(wl)*(len(STACKS[i])+(4 if c['kind']=='planted' else 0)),
                recursion_layer_updates=len(wl)*len(STACKS[i]))

def csv_write(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--targets',type=int,default=12);ap.add_argument('--out',type=Path,default=ROOT/'results')
    ap.add_argument('--work-matched',action='store_true');ap.add_argument('--seeds',type=int,default=4);ap.add_argument('--max-budget',type=int,default=721)
    args=ap.parse_args();load_kernel();args.out.mkdir(parents=True,exist_ok=True);start=time.perf_counter();cc=cases(args.targets)
    # Build structure graph only; no optical response or target enters it.
    graph_start=time.perf_counter()
    for i in range(len(STACKS)):neighbors_one(i)
    graph_wall=time.perf_counter()-graph_start
    config=dict(model='SYNTHETIC constant n; explicitly lossless k=0; no real-material claim',material_n=MATERIALS,material_k=[0.,0.,0.],
                n0=1.,ns=NS,geometry='coherent normal incidence, isotropic planar layers, semi-infinite substrate, no backside',
                thickness_catalog_um=THICKNESSES,max_layers=4,total_max_um=3.6,adjacent_same_material='excluded; finite catalog restriction, not all legal merged thicknesses',
                catalog_size=len(STACKS),target_seeds=TARGET_SEEDS[:args.targets],search_seeds=SEARCH_SEEDS[:args.seeds],
                cases=cc,methods=METHODS,train_wavelengths_um=TRAIN.tolist(),budgets=[b for b in BUDGETS if b<=args.max_budget],
                score='lexicographic (max(0,max(g)),mean(max(g,0)^2),max(g)); g=R/tau-1 or abs(R-R*)/tau-1; tie fewer layers, thickness, catalog tuple',
                mechanism='same one-edit any-position insertion/deletion/reassignment descent; on strict one-edit stagnation only, compare graph-distance-two endpoints with no intermediate optical score gate; otherwise same uniform full-stack restart',
                accounting='fresh unpadded TMM per unique evaluated stack per run; within-run exact cache; no search use of oracle, shared response table or audit; all rejected endpoints charged',
                work_budget='sum(1+physical_layers) per spectral call; combines call overhead and active layers as explicit proxy, not hardware-independent flop count',
                graph_build_seconds=graph_wall,kernel_sha256=hashlib.sha256((ROOT/'verified_kernel/run_experiment.py').read_bytes()).hexdigest(),
                python=platform.python_version(),numpy=np.__version__,args=dict(targets=args.targets,seeds=args.seeds,work_matched=args.work_matched,max_budget=args.max_budget))
    (args.out/'config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
    # Exhaustive training reference is separate and NEVER consulted by Search.
    ot=time.perf_counter();responses=[];energy=0.;cross=0.
    for i in range(len(STACKS)):
        R,T=optics(i,TRAIN);responses.append(R);energy=max(energy,float(np.max(abs(R+T-1))))
        ds,ns=decode(STACKS[i]);cross=max(cross,float(np.max(abs(R-KERNEL.reflection_recursion(TRAIN,ds,ns)))))
    responses=np.asarray(responses);oracle={};targets={}
    for c in cc:
        target=responses[IDS[tuple(map(tuple,c['planted_stack']))]] if c['kind']=='planted' else np.zeros(len(TRAIN));targets[c['name']]=target
        scores=[score(R,target,c,TRAIN) for R in responses];best=min(range(len(STACKS)),key=lambda i:order(i,scores[i]))
        oracle[c['name']]=dict(id=best,stack=STACKS[best],score=scores[best],feasible_count=sum(s[0]<=1e-12 for s in scores),audit=audit(best,c))
    oracle_cost=dict(matrix_calls=len(STACKS),independent_recursion_calls=len(STACKS),
                     matrix_wavelength_layer_updates=len(TRAIN)*sum(map(len,STACKS)),recursion_wavelength_layer_updates=len(TRAIN)*sum(map(len,STACKS)),
                     wall_seconds=time.perf_counter()-ot,max_energy_error=energy,matrix_recursion_max_error=cross)
    runs=[];rows=[];audits={}
    for c in cc:
        for seed in SEARCH_SEEDS[:args.seeds]:
            # Fixed method order; wall time descriptive only, not speed ranking.
            for method in METHODS:
                limit=args.max_budget*(5 if args.work_matched else 1)
                run=Search(c,targets[c['name']],seed,method,limit,args.work_matched).run()
                for snap in run['snapshots']:
                    key=(c['name'],snap['best_id'])
                    if key not in audits:audits[key]=audit(snap['best_id'],c)
                    snap['dense_audit']=audits[key]
                    rows.append(dict(case=c['name'],kind=c['kind'],seed=seed,method=method,budget_kind=run['budget_kind'],
                                     budget=snap['budget'],calls=snap['calls'],work_units=snap['work_units'],
                                     active_wavelength_layer_updates=snap['active_wavelength_layer_updates'],wall_seconds=snap['wall_seconds'],
                                     train_V=snap['score'][0],dense_V=snap['dense_audit']['score'][0],dense_pass=snap['dense_audit']['pass_sampled'],
                                     max_absolute_target_error=snap['dense_audit']['max_absolute_target_error'],layers=snap['layers'],
                                     total_thickness_um=snap['total_thickness_um'],oracle_V=oracle[c['name']]['score'][0],best_id=snap['best_id']))
                runs.append(run)
        print(c['name'],'done',flush=True)
    summary=[]
    for c in cc:
        for method in METHODS:
            for b in sorted({r['budget'] for r in rows}):
                sub=[r for r in rows if r['case']==c['name'] and r['method']==method and r['budget']==b]
                summary.append(dict(case=c['name'],kind=c['kind'],method=method,budget=b,runs=len(sub),dense_passes=sum(r['dense_pass'] for r in sub),
                                    median_dense_V=float(np.median([r['dense_V'] for r in sub])),min_dense_V=min(r['dense_V'] for r in sub),max_dense_V=max(r['dense_V'] for r in sub),
                                    median_calls=float(np.median([r['calls'] for r in sub])),median_layers=float(np.median([r['layers'] for r in sub]))))
    output=dict(config=config,oracle=oracle,oracle_cost=oracle_cost,runs=runs,summary=summary,total_wall_seconds=time.perf_counter()-start,
                final_audit_cost=dict(unique_case_stacks=len(audits),matrix_calls=sum(a['matrix_calls'] for a in audits.values()),
                                      independent_recursion_calls=sum(a['recursion_calls'] for a in audits.values()),
                                      matrix_layer_updates=sum(a['matrix_layer_updates'] for a in audits.values()),
                                      recursion_layer_updates=sum(a['recursion_layer_updates'] for a in audits.values())),
                audit_scope='Per completed run, audit saved checkpoints without feedback to later searches; per window union of linspace(lo,hi,4097) and lo+(j+0.5)*(hi-lo)/4097 for j=0..4096 (8193 unique points; shared center); 9/41 training wavelengths overlap; fixed finite grid, not a continuum certificate')
    (args.out/'results.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    csv_write(args.out/'runs.csv',rows);csv_write(args.out/'summary.csv',summary)
    (args.out/'summary.json').write_text(json.dumps(dict(summary=summary,oracle=oracle,total_wall_seconds=output['total_wall_seconds']),ensure_ascii=False,indent=2)+'\n')
    print('finished',len(runs),'runs;',output['total_wall_seconds'],'seconds',flush=True)

if __name__=='__main__':main()
