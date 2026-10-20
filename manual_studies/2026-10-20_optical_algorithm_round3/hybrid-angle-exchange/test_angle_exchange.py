import json,unittest
import numpy as np
import run_angle_exchange as a

class ExchangeTests(unittest.TestCase):
    def test_kernel_and_grid(self):
        r=a.physics_tests();self.assertLess(r['scattered_vs_cartesian_kernel_max_abs_error'],1e-12)
    def test_point_budget_stops_before_extra_work(self):
        c=a.h.case_def('synthetic10_multi');m=a.PointModel(c,[3.,4.],[0.,30.],['s','p']);w=a.Work(1)
        with self.assertRaises(a.WorkEnd):w.solve(m,np.ones(10)*.1,'test')
        self.assertEqual(w.points,0);self.assertEqual(w.calls,0)
    def test_lossless_scattered_queries(self):
        c=a.h.case_def('synthetic10_multi');m=a.PointModel(c,[3.,4.,8.,12.],[0.,12.3,36.29,45.],['s','p','s','p']);R,P=m.solve(np.linspace(.005,1.3,10));np.testing.assert_allclose(R+P,1,atol=1e-12)
    def test_fixed_grid_work_counts(self):
        self.assertEqual(len(a.grid_queries([0.,30.,45.])[0]),810);self.assertEqual(len(a.grid_queries(np.arange(0,46,5))[0]),3078)
    def test_common_grid_weight_sum(self):
        for angles in ([0.,30.,45.],np.arange(0,46,5)):
            self.assertAlmostEqual(float(a.grid_queries(angles)[3].sum()),1.)
    def test_source_families_and_seeds_are_frozen(self):
        rows=json.loads((a.ROOT/'seed_sources.json').read_text())['sources'];self.assertEqual(len(rows),10)
        for case in ('synthetic10_multi','tabulated6_multi'):self.assertEqual(sorted(r['seed'] for r in rows if r['case']['name']==case),[11,29,47,71,101])
    def test_known_angle_counterexample_is_found_and_charged(self):
        rows=json.loads((a.ROOT/'seed_sources.json').read_text())['sources'];r=next(r for r in rows if r['case']['name']=='synthetic10_multi' and r['seed']==47);wl,aa,pp,w=a.grid_queries(np.arange(0,46,5));m=a.PointModel(r['case'],wl,aa,pp);work=a.Work(10000);R,P=work.solve(m,r['thickness_um'],'common_reference');added,diag=a.discover_peaks(r['case'],r['thickness_um'],m,R,P,work,[])
        peak=max(added,key=lambda q:q['R_when_found']);self.assertAlmostEqual(peak['angle_deg'],36.2973415,places=5);self.assertGreater(peak['R_when_found'],.1238);self.assertEqual(work.points,m.Q+sum(q['oracle_point_work'] for q in diag))
    def test_final_audit_refines_both_polarizations_even_at_normal_incidence(self):
        r=json.loads((a.ROOT/'seed_sources.json').read_text())['sources'][0];out=a.final_audit({'case':r['case'],'thickness_um':r['thickness_um']},32,15.)
        for window in ([3.,5.],[8.,12.]):self.assertEqual({q['pol'] for q in out['local_refinements'] if q['window_um']==window},{'s','p'})
    def test_budget_and_minimax_archive(self):
        rows=json.loads((a.ROOT/'seed_sources.json').read_text())['sources'];r=rows[0]
        for method in a.METHODS:
            s=a.run(r,method,100000);self.assertLessEqual(s['actual_extra_points'],100000);self.assertEqual(sum(d['points'] for d in s['cost_by_stage'].values()),s['actual_extra_points']);self.assertLessEqual(s['final_common_reference_max_violation'],s['initial_common_reference_max_violation'])
if __name__=='__main__':unittest.main(verbosity=2)
