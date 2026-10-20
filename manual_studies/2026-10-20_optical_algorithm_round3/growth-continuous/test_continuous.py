import json
from collections import Counter
import numpy as np
import pytest
import run_continuous as e

@pytest.fixture(scope='module',autouse=True)
def load():e.load_kernel()

def raw():return json.loads((e.ROOT/'pilot/results.json').read_text())

def test_canonical_merges_cannot_bypass_upper_bound():
    assert e.canonical(((0,.3),(0,.4),(2,.5)))==((0,.7),(2,.5))
    assert not e.legal(e.canonical(((0,1.1),(0,1.1))))
    assert not e.legal(((0,.2),(0,.3)))
    assert e.legal(e.KNOWN) and sum(d for m,d in e.KNOWN)<=12

def test_layer_edit_endpoints_and_two_hop_definition():
    for s in ((),((0,.2),),((0,.2),(2,.7)),e.KNOWN):
        one=e.neighbors(s);assert s not in one and all(e.legal(z) for z in one)
        two=e.two_neighbors(s,one);assert not set(one)&set(two) and s not in two
        assert all(e.legal(z) for z in two)
        for z in two[::max(1,len(two)//20)]:assert any(z in e.neighbors(mid) for mid in one)

def test_fresnel_quarter_wave_and_known_feasibility():
    R,T=e.KERNEL.tmm_normal(e.TRAIN,[],[]);np.testing.assert_allclose(R,((1-3.42)/(1+3.42))**2,atol=1e-15)
    R,T=e.KERNEL.tmm_normal([4.],[1/e.N[1]],[e.N[1]]);assert R[0]<1e-25
    a=e.audit(e.KNOWN);assert a['feasible_four_percent_pass'] and not a['strict_one_percent_pass']
    assert a['matrix_recursion_max_error']<1e-12 and a['max_energy_error']<1e-12

def test_local_solver_counts_numerical_difference_calls_and_preserves_archive():
    x=e.Experiment(11,e.METHODS[0],10000);s=((0,.5),(2,.4));x.evaluate(())
    best=x.refine(s,'test')
    assert 1<x.calls<=e.LOCAL_CALLS+1
    assert e.legal(best)
    assert x.work==sum(1+len(z) for z in x.evaluated)
    assert x.layers==82*sum(len(z) for z in x.evaluated)
    assert all(a['score']>=b['score'] for a,b in zip(x.trace,x.trace[1:]))

def test_saved_exact_costs_all_probes_legal_and_equal_budget():
    r=raw();assert len(r['runs'])==8 and not r['config']['known_feasible_used_by_search']
    for x in r['runs']:
        ss=[tuple(map(tuple,s)) for s in x['evaluated_stacks']]
        assert len(ss)==len(set(ss))==x['calls'] and ss[0]==()
        assert all(e.legal(s) for s in ss)
        assert x['work_units']==sum(1+len(s) for s in ss)<=60000
        assert 60000-x['work_units']<7
        assert x['active_wavelength_layer_updates']==82*sum(len(s) for s in ss)
        assert all(p['calls']<=e.LOCAL_CALLS for p in x['repairs'])
        for snap in x['snapshots']:
            assert snap['work_units']<=snap['budget']
            assert snap['calls']<=x['calls']
            assert snap['audit']['matrix_recursion_max_error']<1e-12

def test_saved_pair_identity_and_operator_was_not_exercised():
    r=raw()
    for seed in e.SEEDS:
        a=next(x for x in r['runs'] if x['seed']==seed and x['method']==e.METHODS[0])
        b=next(x for x in r['runs'] if x['seed']==seed and x['method']==e.METHODS[1])
        assert a['evaluated_stacks']==b['evaluated_stacks']
        assert a['best_score']==b['best_score']
        assert not any(x['event'] in ('finite_one_edit_stagnation','two_edit_begin') for x in b['events'])

def test_complete_work_checkpoint_replay():
    r=raw();old=next(x for x in r['runs'] if x['seed']==29 and x['method']==e.METHODS[0])
    new=e.Experiment(29,e.METHODS[0],10000).run()
    assert [list(map(list,s)) for s in new['evaluated_stacks']]==old['evaluated_stacks'][:new['calls']]
    np.testing.assert_allclose(new['best_score'],old['snapshots'][0]['score'],atol=0,rtol=0)

def test_no_finite_grid_certificate_or_wrong_target_pass():
    r=raw();assert r['config']['strict_target_R']==.01 and r['config']['feasible_calibration_target_R']==.04
    assert r['config']['strict_feasibility']=='not established in this continuous domain'
    for s in r['summary']:
        assert s['strict_one_percent_passes']==0
        assert s['feasible_four_percent_passes']==4
        assert .01<s['median_dense_worst_R']<.04
