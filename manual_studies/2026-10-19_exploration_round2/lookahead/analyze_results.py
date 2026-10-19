#!/usr/bin/env python3
"""Derive paired diagnostics without changing search results."""
from pathlib import Path
import csv,json
import numpy as np
import run_lookahead as e
ROOT=Path(__file__).resolve().parent

def main():
    r=json.loads((ROOT/'results/results.json').read_text());e.load_kernel(ROOT/'verified_kernel')
    paired=[];raw={}
    for run in r['runs']:
        for snap in run['snapshots']:raw[run['case'],run['seed'],run['method'],snap['budget']]=snap
    comparison_defs=[('h1_complex_vs_score','h1_w4_complex','h1_w4_score'),('h2_complex_vs_score','h2_w4_complex','h2_w4_score'),
        ('h1_complex_vs_intensity','h1_w4_complex','h1_w4_intensity'),('h2_complex_vs_intensity','h2_w4_complex','h2_w4_intensity'),
        ('h1_width4_vs_width1','h1_w4_score','h1_w1_score'),('h2_width4_vs_width1','h2_w4_score','h2_w1_score'),
        ('score_h2_vs_h1_width1','h2_w1_score','h1_w1_score'),('score_h2_vs_h1_width4','h2_w4_score','h1_w4_score')]
    for label,a,b in comparison_defs:
        for budget in e.BUDGETS:
            for group,cn in [('all_seven_cases',list(r['oracle'])),('four_planted_families',[c for c in r['oracle'] if c.startswith('planted')])]:
                pairs=[(raw[c,s,a,budget],raw[c,s,b,budget]) for c in cn for s in e.SEEDS]
                delta=np.array([x['dense_audit']['score'][0]-y['dense_audit']['score'][0] for x,y in pairs])
                paired.append(dict(comparison=label,budget=budget,case_group=group,paired_ordering_repeats=len(pairs),case_families=len(cn),better=int((delta < -1e-10).sum()),tied=int((abs(delta)<=1e-10).sum()),worse=int((delta > 1e-10).sum()),median_dense_V_difference=float(np.median(delta))))
    paths=[];calls=0;updates=0
    for c in e.cases():
        s=tuple(map(tuple,r['oracle'][c['name']]['stack']));target=np.zeros(len(e.TRAIN))
        if c['kind']=='planted':
            plant=tuple(map(tuple,c['planted_stack']));target=e.optics(plant,e.TRAIN)[0];calls+=2;updates+=len(e.TRAIN)*2*e.NMAX
        prefix=[]
        for k in range(len(s)+1):
            p=s[-k:] if k else ();R,T,z=e.optics(p,e.TRAIN);calls+=2;updates+=len(e.TRAIN)*2*e.NMAX
            prefix.append(dict(layers=k,stack=p,score=e.score_from_R(R,target,c,e.TRAIN)))
        barriers=[]
        for j in range(len(prefix)-2):
            a,b,d=[prefix[i]['score'][0] for i in (j,j+1,j+2)]
            if b>a+1e-10 and d<a-1e-10:barriers.append(dict(start_layers=j,V_before=a,V_one_layer=b,V_two_layers=d))
        paths.append(dict(case=c['name'],oracle_prepend_path=prefix,one_worse_two_better=barriers))
    wall=[x['wall_seconds'] for x in r['runs']]
    families={}
    for h,w,m in e.METHODS:
        method=f'h{h}_w{w}_{m}';families[method]={}
        for b in e.BUDGETS:
            solved=[]
            for c in [c for c in r['oracle'] if c.startswith('planted')]:
                hits=sum(raw[c,s,method,b]['dense_audit']['pass_sampled'] for s in e.SEEDS)
                if hits:solved.append(dict(case=c,ordering_hits=hits,total_orderings=4))
            families[method][str(b)]=solved
    diagnostic=dict(paired_comparisons=paired,solved_planted_families=families,oracle_path_diagnostics=paths,
        diagnostic_cost=dict(actual_optical_stack_calls=calls,padded_wavelength_layer_updates=updates),
        search_accounting=dict(total_runs=len(r['runs']),total_evaluations=sum(x['calls'] for x in r['runs']),total_optical_calls=sum(x['actual_optical_stack_calls'] for x in r['runs']),
            total_executed_padded_wavelength_layer_updates=sum(x['padded_wavelength_layer_updates'] for x in r['runs']),total_active_equivalent_wavelength_layer_updates=sum(x['active_wavelength_layer_updates'] for x in r['runs']),
            min_run_wall_seconds=min(wall),median_run_wall_seconds=float(np.median(wall)),max_run_wall_seconds=max(wall),total_search_wall_seconds=sum(wall)),
        note='Four ordering seeds repeat each target family; these are not independent target tasks. Diagnostics do not change target selection or search.')
    (ROOT/'results/diagnostics.json').write_text(json.dumps(diagnostic,ensure_ascii=False,indent=2)+'\n')
    with (ROOT/'results/paired_comparisons.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(paired[0]));w.writeheader();w.writerows(paired)
    print(json.dumps(dict(solved=families,accounting=diagnostic['search_accounting'],barriers={x['case']:x['one_worse_two_better'] for x in paths}),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
