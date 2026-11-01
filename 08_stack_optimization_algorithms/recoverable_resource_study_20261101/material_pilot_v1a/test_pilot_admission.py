"""Pure admission/recovery contract tests. Mocked audits do not establish optics."""
import contextlib
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import run_pilot
from artifact_store import canonical_json
from core_bridge import configure_core
import os
configure_core(os.environ['COATING_CORE_REPOSITORY'])
from coat_sim.core.film_synthesis_archive import physical_design_hash
from reference import solve,PROFILE


def fixture_task(group,family):
    # Synthetic metadata fixture only: never evaluates optics or real material tables.
    return dict(case_id=f'material-{group}-{family}',reference_wavelength_nm=550.,
                request=dict(environment=dict(front_layers=[],back_layers=[])))


class AdmissionContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace=tempfile.TemporaryDirectory()
        cls.template=Path(cls.workspace.name)/'template';cls.template.mkdir()
        source=Path(run_pilot.__file__).parent
        for path in source.glob('*.py'):shutil.copy2(path,cls.template/path.name)
        shutil.copy2(source/'README.md',cls.template/'README.md')
        shutil.copytree(source/'docs',cls.template/'docs')
        with patch.object(run_pilot,'ROOT',cls.template),patch.object(run_pilot,'make_task',side_effect=fixture_task),contextlib.redirect_stdout(io.StringIO()):run_pilot.prepare()
        cls.ph=run_pilot.sha(cls.template/'plan.json');cls.mh=run_pilot.sha(cls.template/'source_manifest.json')
        cls.first=json.loads((cls.template/'plan.json').read_text())['case_ids'][0]
    @classmethod
    def tearDownClass(cls):cls.workspace.cleanup()
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'pilot';shutil.copytree(self.template,self.root)
    def tearDown(self):self.tmp.cleanup()
    def verify(self):return run_pilot.verify_admission(self.root,self.ph,self.mh,[self.first])
    def test_valid_and_declared_outputs_allowed(self):
        self.verify()
        out=self.root/'cases'/self.first/'result.json';out.write_text('{}')
        self.verify()
    def test_id_and_digest_checked_before_any_path_read(self):
        with patch.object(run_pilot,'_target',side_effect=AssertionError('premature path access')):
            for planhash,manifesthash,ids in [('bad',self.mh,[]),(self.ph,'bad',[]),(self.ph,self.mh,['../../etc'])]:
                with self.subTest(ids=ids):
                    with self.assertRaises(ValueError):run_pilot.verify_admission(self.root,planhash,manifesthash,ids)
    def test_whitelist_rejects_valid_syntax_but_undeclared_combinations(self):
        for value in ('material-unknown-unknown', 'material-a-b', 'train-41000-ar',
                      'material-../ar', 'material-A-b', 'material-a-b/extra'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                run_pilot.case_id(value)
    def test_invalid_or_duplicate_components_rejected(self):
        for groups in ((), ('a','a'), ('a-b',), ('../a',), (12,)):
            with self.subTest(groups=groups),patch.object(run_pilot,'GROUPS',groups),self.assertRaises(ValueError):
                run_pilot._case_set()
    def test_generated_task_wrong_identity_rejected_before_freezing_inputs(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(run_pilot,'ROOT',Path(tmp)),patch.object(run_pilot,'make_task',return_value={'case_id':'material-unknown-unknown'}):
            with self.assertRaisesRegex(ValueError,'identity'):
                run_pilot.prepare()
            self.assertFalse((Path(tmp)/'cases').exists())
    def test_plan_changed(self):
        with (self.root/'plan.json').open('ab') as f:f.write(b' ')
        with self.assertRaisesRegex(ValueError,'plan SHA'):self.verify()
    def test_manifest_changed(self):
        with (self.root/'source_manifest.json').open('ab') as f:f.write(b' ')
        with self.assertRaisesRegex(ValueError,'manifest SHA'):self.verify()
    def test_source_and_input_changes_rejected(self):
        for path in ('reference.py',f'cases/{self.first}/input.json'):
            p=self.root/path;original=p.read_bytes();p.write_bytes(original+b' ')
            with self.subTest(path=path),self.assertRaisesRegex(ValueError,'source manifest content mismatch'):self.verify()
            p.write_bytes(original)
    def test_unexpected_source_and_unknown_case_output_rejected(self):
        for path in ('surprise.py','cases/material-unknown-unknown/result.json'):
            p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('{}')
            with self.subTest(path=path),self.assertRaisesRegex(ValueError,'unexpected pilot file'):self.verify()
            p.unlink()
    def test_fresh_process_runtime_matches_prepare(self):
        code="import run_pilot; run_pilot.verify_admission('.',%r,%r,[%r])" % (self.ph,self.mh,self.first)
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
        run=subprocess.run([sys.executable,'-c',code],cwd=self.root,env=env,capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
    def test_runtime_change_rejected(self):
        runtime=run_pilot.runtime_summary();runtime['numpy']='different'
        with patch.object(run_pilot,'runtime_summary',return_value=runtime),self.assertRaisesRegex(ValueError,'runtime'):
            self.verify()
    def test_invalid_source_manifest_path_cannot_escape(self):
        # _source_paths validates case identity; attacker-controlled source paths are also rejected.
        plan=json.loads((self.root/'plan.json').read_text());plan['source_sha256']['../escape.py']='a'*64
        with self.assertRaisesRegex(ValueError,'source path'):run_pilot._validate_plan(plan)


class RecoveryContractTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        from tasks import GROUPS,FAMILIES
        self.task=fixture_task(GROUPS[0],FAMILIES[0])
        self.c=self.task['case_id'];self.case=self.root/'cases'/self.c;self.case.mkdir(parents=True)
        self.rh=hashlib.sha256(canonical_json(self.task)).hexdigest()
    def tearDown(self):self.tmp.cleanup()
    def result(self,**updates):
        result=dict(schema='offline-reference-result-v1',case_id=self.c,request_sha256=self.rh,state='completed',
            estimate_state='unknown_not_infeasible',profile=PROFILE,selected_hash=None,layer_count=None,total_thickness_nm=None,
            retained_witness_hashes=[])
        result.update(updates);(self.case/'result.json').write_bytes(canonical_json(result));return result
    def witness(self,n):
        design=deepcopy(self.task['request']['environment'])
        if n:design['front_layers']=[dict(id='L0',material_id='test_material',optical_set_id='test_optical_set',thickness=dict(value=10.,unit='nm'),note='offline reference candidate')]
        identity=physical_design_hash(design);d=10. if n else 0.
        row=dict(state='audited',physical_hash=identity,layer_count=n,total_thickness_nm=d,targets_met=True,
            solver_acceptable=True,within_constraints=True,within_material_pool=True,candidate_design=deepcopy(design),audit={'coverage':'mocked'})
        w=dict(request_sha256=self.rh,physical_design_hash=identity,layer_count=n,total_thickness_nm=d,design=design,audit=dict(candidate_reports=[row],pareto_witnesses=[deepcopy(row)]))
        folder=self.case/'witnesses';folder.mkdir(exist_ok=True);(folder/(identity+'.json')).write_bytes(canonical_json(w));return identity,w
    def test_unknown_without_witness_is_accepted(self):
        expected=self.result();self.assertEqual(solve(self.task,self.root),expected)
    def test_missing_null_field_rejected(self):
        result=self.result();del result['layer_count'];(self.case/'result.json').write_bytes(canonical_json(result))
        with self.assertRaisesRegex(ValueError,'missing required'):solve(self.task,self.root)
    def test_fake_audited_label_without_witness_rejected(self):
        self.result(estimate_state='audited_reference',layer_count=1,total_thickness_nm=10.)
        with self.assertRaisesRegex(ValueError,'selection or label'):solve(self.task,self.root)
    def test_missing_unselected_witness_rejected(self):
        h,_=self.witness(0)
        self.result(estimate_state='audited_reference',selected_hash=h,layer_count=0,total_thickness_nm=0.,retained_witness_hashes=sorted([h,'f'*64]))
        with self.assertRaisesRegex(ValueError,'inventory mismatch'):solve(self.task,self.root)
    def test_selection_recomputed_for_all_witnesses(self):
        a,_=self.witness(0);b,_=self.witness(1)
        self.result(estimate_state='audited_reference',selected_hash=b,layer_count=1,total_thickness_nm=10.,retained_witness_hashes=sorted([a,b]))
        with self.assertRaisesRegex(ValueError,'selection or label'):solve(self.task,self.root)
    def test_witness_filename_must_equal_physical_hash(self):
        h,_=self.witness(0);wrong='a'*64
        (self.case/'witnesses'/f'{h}.json').rename(self.case/'witnesses'/f'{wrong}.json')
        self.result(estimate_state='audited_reference',selected_hash=wrong,layer_count=0,total_thickness_nm=0.,retained_witness_hashes=[wrong])
        with self.assertRaisesRegex(ValueError,'filename'):solve(self.task,self.root)
    def test_witness_request_and_audit_resource_binding(self):
        h,w=self.witness(0);path=self.case/'witnesses'/f'{h}.json'
        self.result(estimate_state='audited_reference',selected_hash=h,layer_count=0,total_thickness_nm=0.,retained_witness_hashes=[h])
        self.assertEqual(solve(self.task,self.root)['selected_hash'],h)
        for mutation in ('request','audit'):
            changed=deepcopy(w)
            if mutation=='request':changed['request_sha256']='0'*64
            else:
                changed['audit']['candidate_reports'][0]['total_thickness_nm']=1.
                changed['audit']['pareto_witnesses'][0]['total_thickness_nm']=1.
            path.write_bytes(canonical_json(changed))
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):solve(self.task,self.root)

if __name__=='__main__':unittest.main()
