#!/usr/bin/env python3
"""Descriptive, task-family-aware analysis. Diagnostic oracle never feeds search."""
import argparse,csv,json,time
from pathlib import Path
import numpy as np
import run_growth as e

ROOT=Path(__file__).resolve().parent

def analyze(folder):
    raw=json.loads((folder/'results.json').read_text());runs=raw['runs'];budget=max(r['budget'] for r in raw['summary'])
    aggregate=[];paired=[]
    for method in e.METHODS:
        rr=[r for r in raw['summary'] if r['kind']=='planted' and r['method']==method and r['budget']==budget]
        full=[r for r in runs if r['case'].startswith('planted') and r['method']==method]
        last=[r['snapshots'][-1] for r in full]
        aggregate.append(dict(method=method,target_families=len(rr),order_repeats=len(full),dense_successful_repeats=sum(r['dense_passes'] for r in rr),
                              families_any_success=sum(r['dense_passes']>0 for r in rr),families_all_success=sum(r['dense_passes']==r['runs'] for r in rr),
                              median_of_family_median_V=float(np.median([r['median_dense_V'] for r in rr])),
                              actual_search_calls=sum(r['calls'] for r in full),active_layer_updates=sum(r['active_wavelength_layer_updates'] for r in full),
                              total_search_wall_seconds=sum(r['wall_seconds'] for r in full),
                              median_final_layers=float(np.median([r['layers'] for r in last])),
                              two_edit_escapes=sum(sum(ev['event']=='two_edit_escape' for ev in r['events']) for r in full)))
    cases=sorted({r['case'] for r in raw['summary'] if r['kind']=='planted'})
    for other in e.METHODS:
        if other=='stagnation_two_edit':continue
        counts=dict(better_families=0,tied_families=0,worse_families=0)
        examples=[]
        for case in cases:
            get=lambda m:next(r for r in raw['summary'] if r['case']==case and r['method']==m and r['budget']==budget)
            a=get('stagnation_two_edit');b=get(other);delta=a['median_dense_V']-b['median_dense_V']
            relation='better' if delta<-1e-9 else 'worse' if delta>1e-9 else 'tied';counts[relation+'_families']+=1
            examples.append(dict(case=case,relation=relation,new_median_dense_V=a['median_dense_V'],baseline_median_dense_V=b['median_dense_V'],
                                 new_passes=a['dense_passes'],baseline_passes=b['dense_passes']))
        paired.append(dict(comparator=other,unit='one target family; each value is median of four candidate-order repeats',**counts,details=examples))
    final=dict(budget=budget,budget_kind=runs[0]['budget_kind'],aggregate=aggregate,paired=paired,
               search_cost=dict(matrix_calls=sum(r['calls'] for r in runs),active_wavelength_layer_updates=sum(r['active_wavelength_layer_updates'] for r in runs),
                                work_units=sum(r['work_units'] for r in runs),wall_seconds=sum(r['wall_seconds'] for r in runs)),
               max_audit_energy_error=max(s['dense_audit']['max_energy_error'] for r in runs for s in r['snapshots']),
               max_audit_matrix_recursion_error=max(s['dense_audit']['matrix_recursion_max_error'] for r in runs for s in r['snapshots']),
               false_sampled_passes=sum(s['score'][0]<=1e-12 and not s['dense_audit']['pass_sampled'] for r in runs for s in r['snapshots']))
    (folder/'analysis.json').write_text(json.dumps(final,ensure_ascii=False,indent=2)+'\n')
    e.csv_write(folder/'aggregate.csv',aggregate)
    print(folder.name,json.dumps(aggregate,ensure_ascii=False),flush=True)
    return final

def diagnostics(folder):
    raw=json.loads((folder/'results.json').read_text());e.load_kernel();start=time.perf_counter()
    spectra=[e.optics(i,e.TRAIN)[0] for i in range(len(e.STACKS))];result=[];sample_witnesses=[]
    for c in raw['config']['cases']:
        target=spectra[e.IDS[tuple(map(tuple,c['planted_stack']))]] if c['kind']=='planted' else np.zeros(len(e.TRAIN))
        sc=[e.score(R,target,c,e.TRAIN) for R in spectra];rank=lambda i:e.order(i,sc[i])
        minima=[i for i in range(len(e.STACKS)) if all(rank(i)<=rank(j) for j in e.neighbors_one(i))]
        local=[]
        visited={ev['current'] for r in raw['runs'] if r['case']==c['name'] and r['method']=='stagnation_two_edit' for ev in r['events'] if ev['event']=='one_edit_local_optimum'}
        for i in minima:
            pool=e.neighbors_two(i);j=min([i]+list(pool),key=rank);escapable=rank(j)<rank(i)
            rec=dict(id=i,stack=e.STACKS[i],V=sc[i][0],two_edit_improves=escapable,best_two_edit_id=j,best_two_edit_V=sc[j][0],visited_in_new_search=i in visited)
            if escapable:
                mids=set(e.neighbors_one(i))&set(e.neighbors_one(j));mid=min(mids,key=rank)
                rec.update(best_legal_intermediate_id=mid,best_legal_intermediate_V=sc[mid][0],strict_V_barrier=sc[mid][0]>sc[i][0]+1e-10)
                if i in visited and rec['strict_V_barrier']:
                    sample_witnesses.append(dict(case=c['name'],before=i,intermediate=mid,after=j,
                                                stacks=[e.STACKS[x] for x in (i,mid,j)],training_scores=[sc[x] for x in (i,mid,j)],
                                                dense_audits=[e.audit(x,c) for x in (i,mid,j)]))
            local.append(rec)
        result.append(dict(case=c['name'],one_edit_local_minima=len(minima),two_edit_escapable=sum(x['two_edit_improves'] for x in local),
                           strict_V_barriers=sum(x.get('strict_V_barrier',False) for x in local),local_minima=local))
    out=dict(cases=result,visited_strict_barrier_witnesses=sample_witnesses,
             cost=dict(matrix_calls=len(e.STACKS)+sum(a['matrix_calls'] for w in sample_witnesses for a in w['dense_audits']),
                       independent_recursion_calls=sum(a['recursion_calls'] for w in sample_witnesses for a in w['dense_audits']),
                       train_matrix_layer_updates=len(e.TRAIN)*sum(map(len,e.STACKS)),
                       witness_matrix_layer_updates=sum(a['matrix_layer_updates'] for w in sample_witnesses for a in w['dense_audits']),
                       witness_recursion_layer_updates=sum(a['recursion_layer_updates'] for w in sample_witnesses for a in w['dense_audits']),
                       wall_seconds=time.perf_counter()-start),
             scope='post-hoc finite-training-catalog landscape; all local minima included; no selection or oracle values returned to search')
    (folder/'mechanism_diagnostics.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print('mechanism',[(c['case'],c['one_edit_local_minima'],c['two_edit_escapable']) for c in result],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=ROOT/'results');p.add_argument('--diagnostics',action='store_true');a=p.parse_args()
    analyze(a.out)
    if a.diagnostics:diagnostics(a.out)
