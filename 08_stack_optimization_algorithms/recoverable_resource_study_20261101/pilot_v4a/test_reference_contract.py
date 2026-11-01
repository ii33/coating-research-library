import os
import unittest
import tempfile
import time
from unittest.mock import patch
from pathlib import Path
import json
from dataclasses import asdict
from copy import deepcopy
import numpy as np
from core_bridge import configure_core,request_from_dict
configure_core(os.environ['COATING_CORE_REPOSITORY'])
from tasks import make_task
from reference import select_witness,design_from_thickness,delete_and_merge
from artifact_store import canonical_json

class ReferenceContractTest(unittest.TestCase):
    def test_input_is_deterministic_with_no_runtime_memory_probe(self):
        a=make_task(41000,'mean_mix');b=make_task(41000,'mean_mix')
        self.assertEqual(canonical_json(a),canonical_json(b))
        self.assertEqual(a['request']['resource_guard_resolution']['mode'],'explicit')
        self.assertIsNone(a['request']['resource_guard_resolution']['available_bytes'])
        for o in a['request']['objectives']:
            self.assertTrue(o['mean']['enabled']);self.assertFalse(o['pointwise']['enabled'])
            self.assertTrue(o['mean']['strict_lower'])
        restored=asdict(request_from_dict(a['request']))
        self.assertEqual(canonical_json(restored),canonical_json(a['request']))
    def test_group_materials_shared_but_targets_not_spliced(self):
        a=make_task(41000,'ar');b=make_task(41000,'bandpass')
        self.assertEqual(a['request']['frozen_material_snapshot']['materials'],b['request']['frozen_material_snapshot']['materials'])
        self.assertEqual(len(a['request']['objectives']),1);self.assertEqual(len(b['request']['objectives']),3)
        films=[m for m in a['request']['frozen_material_snapshot']['materials'] if m['id']!='glass']
        self.assertTrue(all(min(m['optical_sets'][0]['k'])>0 for m in films))
        self.assertFalse(a['request']['environment']['assume_lossless'])
    def test_selection_keeps_one_real_pair_and_rejects_invalid_zero(self):
        rows=[dict(layer_count=1,total_thickness_nm=20.,physical_design_hash='a'),dict(layer_count=2,total_thickness_nm=1.,physical_design_hash='b')]
        self.assertIs(select_witness(rows,100.),rows[0])
        for n,d in [(0,1.),(1,0.),(2.5,1.),(1,float('nan'))]:
            with self.assertRaises(ValueError):select_witness([dict(layer_count=n,total_thickness_nm=d,physical_design_hash='c')],100.)
    def test_layer_direction_and_delete_merge(self):
        base=request_from_dict(make_task(41000,'hr')['request'])
        design=design_from_thickness(base,[('low','nk'),('high','nk'),('low','nk')],np.array([.1,.2,.3]),1000.)
        self.assertEqual([r['thickness']['value'] for r in design['front_layers']],[300.,200.,100.])
        before=deepcopy(design);merged=delete_and_merge(design,1)
        self.assertEqual(len(merged['front_layers']),1)
        self.assertEqual(merged['front_layers'][0]['thickness']['value'],400.)
        self.assertEqual(design,before)
    def test_completed_result_cannot_be_reused_for_different_input(self):
        from reference import solve
        task=make_task(41000,'hr')
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'cases'/task['case_id'];path.mkdir(parents=True)
            (path/'result.json').write_text(json.dumps(dict(case_id=task['case_id'],request_sha256='incorrect')))
            with self.assertRaisesRegex(ValueError,'different input'):solve(task,directory)
    def test_budget_stop_after_audit_keeps_the_immediately_saved_witness(self):
        import reference
        task=make_task(41001,'ar')
        task['request']['objectives'][0]['pointwise']['upper_bound']=.5
        with tempfile.TemporaryDirectory() as directory:
            witnessdir=Path(directory)/'cases'/task['case_id']/'witnesses'
            class StopAfterSavedWitness:
                def __init__(self,_seconds):self.started=time.monotonic()
                def is_set(self):return witnessdir.exists() and any(witnessdir.glob('*.json'))
                def check(self):
                    if self.is_set():raise reference.BudgetStop('test stop after successful durable audit')
            with patch.object(reference,'Control',StopAfterSavedWitness):result=reference.solve(task,directory)
            self.assertEqual(result['state'],'declared_budget_stopped')
            self.assertEqual(result['estimate_state'],'audited_reference')
            self.assertEqual(result['layer_count'],0)
            self.assertEqual(len(list(witnessdir.glob('*.json'))),1)
            self.assertEqual(reference.solve(task,directory),result)
    def test_analytic_jacobian_matches_finite_difference_in_normalized_units(self):
        from coat_sim.core.film_optics import coherent_rta
        from coat_sim.core.film_optimization_derivatives import _analytic_one_polarization
        wave=np.linspace(.8,1.2,9);indices=np.tile(np.array([1.,1.45+.0001j,2.2+.0002j,1.6]),(9,1));x=np.array([.17,.12])
        for pol in ('s','p'):
            jr,jt=_analytic_one_polarization(wave,indices,x,['0','1'],{'0':0,'1':1},35.,pol)
            for i in range(2):
                plus=x.copy();minus=x.copy();plus[i]+=1e-6;minus[i]-=1e-6
                a=coherent_rta(wave,indices,plus,angle_deg=35.,polarization=pol)
                b=coherent_rta(wave,indices,minus,angle_deg=35.,polarization=pol)
                for metric,jac in [('R',jr),('T',jt)]:
                    finite=(np.array(a[metric])-np.array(b[metric]))/(2e-6)
                    np.testing.assert_allclose(jac[:,i],finite,rtol=2e-5,atol=2e-7)

if __name__=='__main__':unittest.main()
