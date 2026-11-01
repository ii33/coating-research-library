"""Source-only contracts; no optical inverse design is executed."""
import hashlib,json,os,unittest
from pathlib import Path
from core_bridge import configure_core
from tasks import GROUPS,FAMILIES,source_records,make_task
from artifact_store import canonical_json

class ExpansionContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):configure_core(os.environ['COATING_CORE_REPOSITORY'])
    def test_distinct_numeric_sources_and_repeatable_tables(self):
        seen=set()
        for group in GROUPS:
            records,p=source_records(group)
            self.assertEqual((records,p),source_records(group))
            self.assertEqual(len(records),3)
            for record in records:
                optical=record['optical_sets'][0]
                numeric={k:optical[k] for k in ('wavelengths','n','k')}
                digest=hashlib.sha256(canonical_json(numeric)).hexdigest()
                self.assertNotIn(digest,seen);seen.add(digest)
                self.assertTrue(all(n>0 for n in optical['n']))
                self.assertTrue(optical['k'] is None or all(k>=0 for k in optical['k']))
    def test_matched_visible_goals_and_explicit_synthetic_identity(self):
        previous=Path(__file__).resolve().parent.parent/'material_pilot_v1a/cases/material-sio2_tio2-ar/input.json'
        baseline=json.loads(previous.read_text())
        for group in GROUPS:
            t=make_task(group,'ar')
            self.assertIs(t['synthetic'],True)
            self.assertEqual(json.loads(json.dumps(t['request']['objectives'])),baseline['request']['objectives'])
            self.assertEqual(t['search_seed'],baseline['search_seed'])
            self.assertIs(t['request']['environment']['assume_lossless'],True)
            self.assertTrue(t['optical_domain_checks'][2]['unknown_k_assumed'])
        self.assertEqual(len(GROUPS)*len(FAMILIES),48)

    def test_all_families_match_prior_goals_and_frozen_feature_interface(self):
        import importlib.util
        parent=Path(__file__).resolve().parent.parent
        source=parent/'predictor_pilot_v1'
        raw=(source/'source_manifest.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'64fec48053218216d17105b6580fd5503d599086d1aeb07565fe79f11cb531f5')
        entry=next(row for row in json.loads(raw)['files'] if row['path']=='features.py')
        self.assertEqual(hashlib.sha256((source/'features.py').read_bytes()).hexdigest(),entry['sha256'])
        spec=importlib.util.spec_from_file_location('frozen_predictor_features',source/'features.py')
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for family in FAMILIES:
            baseline=json.loads((parent/'material_pilot_v1a/cases'/f'material-sio2_tio2-{family}'/'input.json').read_text())
            for group in GROUPS:
                task=json.loads(canonical_json(make_task(group,family)))
                self.assertEqual(task['request']['objectives'],baseline['request']['objectives'])
                self.assertEqual(task['search_seed'],baseline['search_seed'])
                self.assertAlmostEqual(task['reference_wavelength_nm'],baseline['reference_wavelength_nm'])
                features=module.extract_features(task['request'])
                self.assertEqual(len(features['values']),208)

if __name__=='__main__':unittest.main()
