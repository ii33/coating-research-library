import hashlib,json
from pathlib import Path
import numpy as np
import pytest
import run_growth as e

@pytest.fixture(scope='module',autouse=True)
def kernel():e.load_kernel()

def test_catalog_legal_and_not_split_layer_loophole():
    assert len(e.STACKS)==2332 and len(set(e.STACKS))==2332
    assert [sum(len(s)==k for s in e.STACKS) for k in range(5)]==[1,9,54,324,1944]
    assert all(e.legal(s) for s in e.STACKS)
    assert not e.legal(((0,0),(0,1)))
    assert max(sum(e.THICKNESSES[d] for m,d in s) for s in e.STACKS)<=3.6+1e-14

def test_edit_graph_legality_reversibility_and_exact_two_hops():
    for i in np.random.default_rng(20261020).choice(len(e.STACKS),80,replace=False):
        i=int(i);one=set(e.neighbors_one(i));two=set(e.neighbors_two(i))
        assert i not in one|two and not one&two
        assert all(i in e.neighbors_one(j) for j in one)
        assert all(any(j in e.neighbors_one(k) for k in one) for j in two)
        assert all(e.legal(e.STACKS[j]) for j in one|two)
    assert set(e.neighbors_one(0))==set(range(1,10))

def test_kernel_fresnel_quarterwave_and_independent_recursion():
    R,T=e.optics(0,e.TRAIN);np.testing.assert_allclose(R,((1-e.NS)/(1+e.NS))**2,atol=1e-15)
    i=e.IDS[((1,1),)];R,T=e.optics(i,np.array([4.]));assert R[0]<1e-25
    for i in np.random.default_rng(3020).choice(len(e.STACKS),40,replace=False):
        R,T=e.optics(int(i),e.TRAIN);ds,ns=e.decode(e.STACKS[i])
        np.testing.assert_allclose(R+T,1,atol=2e-14)
        np.testing.assert_allclose(R,e.KERNEL.reflection_recursion(e.TRAIN,ds,ns),atol=2e-14)

def test_original_targets_not_chosen_by_new_performance():
    old=json.loads((e.ROOT/'baseline_reference_cases.json').read_text())
    old={x['name']:x for x in old}
    for c in e.cases(4):
        if c['kind']=='planted':assert [list(x) for x in c['planted_stack']]==old[c['name']]['planted_stack']

def test_call_budget_cache_and_archive():
    c=e.cases(4)[-1];target=e.optics(e.IDS[c['planted_stack']],e.TRAIN)[0]
    for m in e.METHODS:
        run=e.Search(c,target,11,m,241).run()
        assert run['calls']==len(run['evaluated_ids'])==len(set(run['evaluated_ids']))
        assert run['calls']<=241 and run['evaluated_ids'][0]==0
        if m!='greedy_front':assert run['calls']==241
        assert run['active_wavelength_layer_updates']==82*sum(len(e.STACKS[i]) for i in run['evaluated_ids'])
        assert all(tuple(a['score'])>=tuple(b['score']) for a,b in zip(run['improvement_trace'],run['improvement_trace'][1:]))

def test_work_matched_budget_with_unpadded_layers():
    c=e.cases(4)[-1];target=e.optics(e.IDS[c['planted_stack']],e.TRAIN)[0]
    for m in e.METHODS:
        run=e.Search(c,target,29,m,1205,True).run()
        assert run['work_units']==sum(1+len(e.STACKS[i]) for i in run['evaluated_ids'])<=1205
        if m!='greedy_front':assert 1205-run['work_units']<5
        for s in run['snapshots']:assert s['work_units']<=s['budget']

def test_frozen_audit_independent_target_recomputation():
    c=e.cases(4)[-1];i=e.IDS[c['planted_stack']];a=e.audit(i,c)
    assert a['score'][0]==0 and a['max_absolute_target_error']==0 and a['points']==16386
    assert a['matrix_recursion_max_error']<1e-12 and a['max_energy_error']<1e-12

def test_saved_complete_expansion_and_accounting():
    for folder in ('results','work_matched'):
        p=e.ROOT/folder/'results.json'
        if not p.exists():pytest.skip('full expansion not yet run')
        r=json.loads(p.read_text());assert len(r['runs'])==15*4*6
        assert len(r['config']['target_seeds'])==12
        assert r['config']['kernel_sha256']==hashlib.sha256((e.ROOT/'verified_kernel/run_experiment.py').read_bytes()).hexdigest()
        for run in r['runs']:
            assert len(run['snapshots'])==3
            for s in run['snapshots']:
                assert s['dense_audit']['max_energy_error']<1e-12
                assert s['dense_audit']['matrix_recursion_max_error']<1e-12
                assert s['calls']<=run['calls']
                if not run['method']=='greedy_front' and not folder=='work_matched':assert s['calls']==s['budget']

def test_deterministic_replay_one_full_run():
    p=e.ROOT/'results/results.json'
    if not p.exists():pytest.skip('full expansion not yet run')
    raw=json.loads(p.read_text());old=next(r for r in raw['runs'] if r['case']=='planted_four_layer_83' and r['seed']==47 and r['method']=='stagnation_two_edit')
    c=next(c for c in e.cases(12) if c['name']==old['case']);target=e.optics(e.IDS[c['planted_stack']],e.TRAIN)[0]
    new=e.Search(c,target,47,'stagnation_two_edit',721).run()
    assert new['evaluated_ids']==old['evaluated_ids']
    np.testing.assert_allclose(new['best_score'],old['best_score'],atol=0,rtol=0)
