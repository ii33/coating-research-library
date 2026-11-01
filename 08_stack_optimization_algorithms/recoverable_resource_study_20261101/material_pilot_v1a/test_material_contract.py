"""Focused material/domain/assumption checks; no reference search."""
import os,unittest
from core_bridge import configure_core
from tasks import GROUPS,FAMILIES,make_task,source_records

class MaterialContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configure_core(os.environ['COATING_CORE_REPOSITORY'])
    def test_matched_goals_shared_seeds_and_assumptions(self):
        baseline=make_task(GROUPS[0],'ar')
        for group in GROUPS:
            task=make_task(group,'ar')
            self.assertEqual(task['request']['objectives'],baseline['request']['objectives'])
            self.assertEqual(task['search_seed'],baseline['search_seed'])
            self.assertIs(task['request']['environment']['assume_lossless'],True)
            self.assertTrue(task['optical_domain_checks'][2]['unknown_k_assumed'])
            for row in task['optical_domain_checks'][:2]:
                self.assertEqual(row['unknown_k_assumed'],row['material_id']=='ybf3')
    def test_known_k_preserved_and_unknown_requires_explicit_opt_in(self):
        from coat_sim.core.optical_constants import prepare_optical_set
        from coat_sim.core.film_synthesis_absorption import sample_synthesis_optical
        records,_=source_records('sio2_ta2o5')
        film=prepare_optical_set(records[0]['optical_sets'][0],k_sampling_policy='source')
        strict=sample_synthesis_optical(film,550.,assume_unknown_k_zero=False)
        assumed=sample_synthesis_optical(film,550.,assume_unknown_k_zero=True)
        self.assertEqual(strict[:2],assumed[:2]);self.assertGreater(strict[1],0.)
        substrate=prepare_optical_set(records[2]['optical_sets'][0],k_sampling_policy='source')
        with self.assertRaises(ValueError):sample_synthesis_optical(substrate,550.,assume_unknown_k_zero=False)
        self.assertEqual(sample_synthesis_optical(substrate,550.,assume_unknown_k_zero=True)[1],0.)
        with self.assertRaises(ValueError):sample_synthesis_optical(film,5000.,assume_unknown_k_zero=True)

if __name__=='__main__':unittest.main()
