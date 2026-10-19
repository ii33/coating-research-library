import json
from pathlib import Path
import numpy as np
import pytest
import run_lookahead as e

@pytest.fixture(scope='module',autouse=True)
def kernel():
    e.load_kernel(e.ROOT/'verified_kernel')

def test_exhaustive_catalog_unique_legal_and_empty():
    s=e.all_stacks()
    assert len(s)==2332 and len(set(s))==2332
    assert s[0]==() and all(e.legal(x) for x in s)
    assert [sum(len(x)==j for x in s) for j in range(5)]==[1,9,54,324,1944]
    assert not e.legal(((0,0),(0,1)))

def test_zero_removal_and_adjacent_material_canonicalization():
    ds,nn=e.canonical([.2,0,.3,.4],[1.45,2.35,1.45,2.35])
    np.testing.assert_allclose(ds,[.5,.4]);np.testing.assert_allclose(nn,[1.45,2.35])
    R,T=e.KERNEL.tmm_normal(e.TRAIN,[.2,0,.3,.4],[1.45,2.35,1.45,2.35])
    r,t=e.KERNEL.tmm_normal(e.TRAIN,ds,nn)
    np.testing.assert_allclose(R,r,atol=1e-14);np.testing.assert_allclose(T,t,atol=1e-14)
    # Physical contiguous maximum cannot be evaded by splitting one material.
    d,n=e.canonical([.6,.6],[1.45,1.45]);assert d[0]>.9

def test_verified_kernel_complex_recursion_and_zero_padding():
    rng=np.random.default_rng(20261019);stacks=e.all_stacks()
    for i in rng.choice(len(stacks),50,replace=False):
        R,T,r=e.optics(stacks[i],e.TRAIN,True)
        r0,t0,q0=e.optics(stacks[i],e.TRAIN,False)
        np.testing.assert_allclose(R,r0,atol=1e-14);np.testing.assert_allclose(T,t0,atol=1e-14)
        np.testing.assert_allclose(r,q0,atol=2e-14)
        np.testing.assert_allclose(abs(r)**2,R,atol=2e-14)
        np.testing.assert_allclose(R+T,1,atol=2e-14)

def test_common_reference_plane_empty_stack():
    R,T,r=e.optics((),e.TRAIN)
    rbare=(e.N0-e.NS)/(e.N0+e.NS)
    np.testing.assert_allclose(r,rbare*np.exp(4j*np.pi*e.N0*4/e.TRAIN),atol=1e-14)

def test_exact_quarter_wave_single_line_and_absolute_zero_tolerance():
    c=e.cases()[0];R,T,r=e.optics(((1,1),),e.TRAIN)
    score=e.score_from_R(R,np.zeros(len(e.TRAIN)),c,e.TRAIN)
    assert score[0]==0 and score[2]<-.999999999
    assert np.isfinite(e.score_from_R(np.ones(len(e.TRAIN))*.1,np.zeros(len(e.TRAIN)),c,e.TRAIN)).all()

def test_archive_work_and_score_monotonicity():
    c=e.cases()[2];target=np.zeros(len(e.TRAIN))
    for h,w,m in e.METHODS:
        r=e.run_search(c,target,11,h,w,m)
        assert r['calls']==721 and r['actual_optical_stack_calls']==1442
        assert r['unique_candidates']==721 and r['original_stack']==()
        scores=[tuple(t['score']) for t in r['improvement_trace']]
        assert all(b<=a for a,b in zip(scores,scores[1:]))
        assert [s['budget'] for s in r['snapshots']]==list(e.BUDGETS)
        assert [s['padded_wavelength_layer_updates'] for s in r['snapshots']]==[b*82*8 for b in e.BUDGETS]
        assert all(e.legal(s['best_stack']) for s in r['snapshots'])

def test_saved_result_equal_budget_and_all_cases():
    p=e.ROOT/'results'/'results.json'
    if not p.exists():pytest.skip('run full experiment first')
    result=json.loads(p.read_text())
    assert len(result['runs'])==7*4*8
    assert max(result['oracle_cost'][k] for k in ['complex_recursion_power_max_error','lossless_energy_max_error'])<1e-12
    for run in result['runs']:
        assert run['original_stack']==[]
        assert run['calls']==721
        assert tuple(run['best_score'])<=tuple(run['original_score'])
        assert all(s['dense_audit']['max_energy_error']<1e-12 for s in run['snapshots'])
    for oracle in result['oracle'].values():assert oracle['finite_catalog_size']==2332
