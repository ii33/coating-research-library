#!/usr/bin/env python3
"""Replay every saved archive against its paid candidate prefix, not just a winner."""
import json,time
from pathlib import Path
import numpy as np
import run_growth as e

def main():
    e.load_kernel();start=time.perf_counter();responses=[e.optics(i,e.TRAIN)[0] for i in range(len(e.STACKS))]
    allchecks=[]
    for folder in ('pilot','results','work_matched'):
        raw=json.loads((e.ROOT/folder/'results.json').read_text());checked=0;events=0
        for c in raw['config']['cases']:
            target=responses[e.IDS[tuple(map(tuple,c['planted_stack']))]] if c['kind']=='planted' else np.zeros(len(e.TRAIN))
            scores=[e.score(R,target,c,e.TRAIN) for R in responses];rank=lambda i:e.order(i,scores[i])
            for r in raw['runs']:
                if r['case']!=c['name']:continue
                ids=r['evaluated_ids'];assert len(ids)==len(set(ids))==r['calls']
                assert ids[0]==0
                assert r['active_wavelength_layer_updates']==82*sum(len(e.STACKS[i]) for i in ids)
                assert r['work_units']==sum(1+len(e.STACKS[i]) for i in ids)
                for s in r['snapshots']:
                    prefix=ids[:s['calls']];assert s['best_id']==min(prefix,key=rank)
                    assert s['active_wavelength_layer_updates']==82*sum(len(e.STACKS[i]) for i in prefix)
                    assert s['work_units']==sum(1+len(e.STACKS[i]) for i in prefix)
                    np.testing.assert_allclose(s['score'],scores[s['best_id']],atol=0,rtol=0)
                    if r['budget_kind']=='spectral_calls':assert s['calls']<=s['budget']
                    else:assert s['work_units']<=s['budget']
                    checked+=1
                for t in r['improvement_trace']:
                    assert t['id']==min(ids[:t['call']],key=rank)
                    np.testing.assert_allclose(t['score'],scores[t['id']],atol=0,rtol=0)
                for ev in r['events']:
                    if ev['event']=='one_edit_local_optimum':
                        i=ev['current'];assert all(rank(i)<=rank(j) for j in e.neighbors_one(i));events+=1
                    if ev['event']=='two_edit_escape':
                        assert ev['after'] in e.neighbors_two(ev['before'])
                        assert rank(ev['after'])<rank(ev['before']);events+=1
        allchecks.append(dict(folder=folder,runs=len(raw['runs']),checked_snapshots=checked,checked_stagnation_or_escape_events=events))
    pilot=json.loads((e.ROOT/'pilot/results.json').read_text());full=json.loads((e.ROOT/'results/results.json').read_text())
    bykey={(r['case'],r['seed'],r['method']):r for r in full['runs']}
    for r in pilot['runs']:assert r['evaluated_ids']==bykey[(r['case'],r['seed'],r['method'])]['evaluated_ids']
    result=dict(all_checks_passed=True,checks=allchecks,pilot_sequences_unchanged_in_expansion=len(pilot['runs']),
                diagnostic_matrix_calls=len(e.STACKS),diagnostic_layer_updates=82*sum(map(len,e.STACKS)),wall_seconds=time.perf_counter()-start,
                scope='saved archive is best only among actually paid prefixes; exact costs, local minima, atomic legal two-edit improvements, fixed pilot replay; no extra search feedback')
    (e.ROOT/'validation_summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
