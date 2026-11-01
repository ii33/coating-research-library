import os
import unittest
from unittest.mock import patch
from dataclasses import asdict
from copy import deepcopy
from core_bridge import configure_core,request_from_dict
configure_core(os.environ['COATING_CORE_REPOSITORY'])
from tasks import make_task
from native_seeds import build_native_seed_bundle
from artifact_store import canonical_json

class NativeSeedContractTest(unittest.TestCase):
    def test_native_construction_never_scores_or_optimizes(self):
        from coat_sim.core import film_optics,film_auto_synthesis
        import scipy.optimize
        task=make_task(41000,'bandpass');base=request_from_dict(task['request']);before=canonical_json(asdict(base))
        with patch.object(film_optics,'coherent_rta',side_effect=AssertionError('physical scoring forbidden')),patch.object(film_auto_synthesis,'synthesize_film_design',side_effect=AssertionError('synthesis forbidden')),patch.object(scipy.optimize,'least_squares',side_effect=AssertionError('optimization forbidden')):
            bundle=build_native_seed_bundle(base,task['reference_wavelength_nm'])
        self.assertEqual(canonical_json(asdict(base)),before)
        self.assertFalse(bundle['audited']);self.assertEqual(bundle['physical_evaluations'],0)
        self.assertTrue(0<len(bundle['seeds'])<=8)
        self.assertEqual([r['layer_count'] for r in bundle['seeds']],sorted(r['layer_count'] for r in bundle['seeds']))
        self.assertTrue(all(r['layer_count']<=32 for r in bundle['seeds']))
    def test_task_with_native_seeds_is_deterministic(self):
        a=make_task(41001,'bandpass');b=make_task(41001,'bandpass')
        self.assertEqual(canonical_json(a),canonical_json(b))
        self.assertEqual(len(a['request']['objectives']),3)
        self.assertTrue(all(o['pointwise']['enabled'] for o in a['request']['objectives']))
        self.assertIsNone(a['request']['max_layers'])
        self.assertIsNone(a['request']['max_layer_thickness_nm'])
    def test_non_bandpass_does_not_receive_new_initialization(self):
        self.assertNotIn('native_seed_bundle',make_task(41000,'hr'))

if __name__=='__main__':unittest.main()
