"""Research consistency checks, not software/product certification."""
import hashlib, json, unittest
from pathlib import Path
import numpy as np
import run_layer_packs as e
import mechanism_check
ROOT=Path(__file__).resolve().parent

class PhysicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):e.load_kernel(ROOT/'verified_kernel')
    def test_halfwave_at_all_positions_and_failure_off_center(self):
        a=mechanism_check.check();self.assertEqual(len(a['checks']),14)
        self.assertLess(max(x['center_abs_R_change'] for x in a['checks']),1e-12)
        self.assertGreater(max(x['window_max_abs_R_change'] for x in a['checks']),.4)
    def test_two_three_layer_identity_matrix(self):
        for seq in ((1.45,2.35),(1.45,2.35,1.45)):
            n=np.array(seq);d=4/(2*n)
            self.assertLess(e.identity_score(d,n,[4]),1e-12)
            self.assertGreater(e.identity_score(d,n,[3,4,5]),.1)
    def test_canonical_merge_does_not_bypass_thickness_cap(self):
        self.assertFalse(e.legal([1.4,1.4],[1.45,1.45]))
        self.assertTrue(e.legal([1.,1.],[1.45,1.45]))
        w=np.linspace(3,12,100)
        a=e.KERNEL.tmm_normal(w,[1.,1.],[1.45,1.45])[0]
        b=e.KERNEL.tmm_normal(w,[2.],[1.45])[0]
        np.testing.assert_allclose(a,b,atol=1e-14)
    def test_pool_legal_fixed_total_and_order_determinism(self):
        base=np.array(e.STARTS['protected_short_window']);p=e.build_pool(base,11);q=e.build_pool(base,11)
        self.assertEqual(p,q)
        for x in p:
            self.assertTrue(e.legal(x['d'],x['n']))
            self.assertAlmostEqual(sum(x['pack_d']),e.PACK_TOTALS[x['pack_length']],places=11)
    def test_frozen_targets_not_replaced_by_identity_anchors(self):
        self.assertEqual(e.WINDOWS,((3.,5.),(8.,12.)))
        self.assertEqual(e.TARGET,.01)
        self.assertEqual(e.TRAIN_N,81)
        self.assertEqual(e.DENSE_N,4097)

class ResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=ROOT/'results'/'results.json'
        if not p.exists():raise unittest.SkipTest('full experiment is not finished')
        cls.results=json.loads(p.read_text())
    def test_all_methods_and_seeds_reported(self):
        rr=self.results['runs'];self.assertEqual(len(rr),40)
        self.assertEqual(len({(r['case'],r['seed'],r['method']) for r in rr}),40)
    def test_exact_paired_training_costs(self):
        rr=self.results['runs']
        for case in e.STARTS:
            for seed in e.SEEDS:
                group=[r for r in rr if r['case']==case and r['seed']==seed]
                self.assertEqual(len({r['total_search_stack_calls_charged'] for r in group}),1)
                self.assertEqual(len({r['total_search_wavelength_layer_updates_charged'] for r in group}),1)
                self.assertTrue(all(r['refinement_calls']==1440 for r in group))
                self.assertEqual(len({json.dumps(r['nominal_local_layer_length_histogram'],sort_keys=True) for r in group}),1)
    def test_all_independent_audits_and_bounds(self):
        for r in self.results['runs']:
            for key in ('best_global','best_protected'):
                p=r[key];a=r[key+'_audit'];self.assertTrue(e.legal(p['d'],p['n']))
                self.assertEqual(len(a['dense']),2);self.assertEqual(len(a['offset']),2);self.assertEqual(len(a['extrema']),2)
                self.assertLess(a['matrix_recursion_max_error'],1e-11)
                self.assertEqual(a['all_targets_pass'],a['worst_R']<=.01+1e-12)
                self.assertIn('frozen_protected_subset',a)
                cd,cn=e.canonical(p['d'],p['n']);self.assertLessEqual(len(cd),9)
                w=np.array([3,4,5,8,10,12.]);a1=e.KERNEL.tmm_normal(w,p['d'],p['n'])[0];a2=e.KERNEL.tmm_normal(w,cd,cn)[0]
                np.testing.assert_allclose(a1,a2,atol=1e-12)
    def test_kernel_provenance_and_replay_one_refinement(self):
        sha=hashlib.sha256((ROOT/'verified_kernel'/'run_experiment.py').read_bytes()).hexdigest()
        self.assertEqual(sha,self.results['config']['kernel_sha256'])
        run=self.results['runs'][0];pool=self.results['pools'][f"{run['case']}:{run['seed']}"];p=pool[run['refinements'][0]['pool_id']]
        wl=np.concatenate([np.linspace(lo,hi,e.TRAIN_N) for lo,hi in e.WINDOWS]);base=np.array(e.STARTS[run['case']]);br=e.KERNEL.tmm_normal(wl,base,e.BASE_N)[0]
        z=e.refine(p,br<=.008,wl,run['seed'])
        np.testing.assert_allclose(z['final_d'],run['refinements'][0]['final_d'],atol=1e-14)
        self.assertEqual(z['calls'],240)

if __name__=='__main__':unittest.main(verbosity=2)
