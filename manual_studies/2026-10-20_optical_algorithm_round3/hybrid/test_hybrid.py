import unittest
import numpy as np
import run_hybrid as h

class HybridTests(unittest.TestCase):
    def test_physics(self):
        r=h.physics_checks();self.assertLess(r['recursion_vs_matrix_max_abs_error'],1e-11)
    def test_bare_oblique_closed_form(self):
        m=h.OpticalModel(np.array([3.,8.,12.]),[],'synthetic_3.42',[0.,30.,45.]);R,P=m.solve([])
        for j,(a,p,w) in enumerate(m.scenarios):
            c=np.cos(np.deg2rad(a));ct=np.sqrt(1-(np.sin(np.deg2rad(a))/3.42)**2)
            r=(c-3.42*ct)/(c+3.42*ct) if p=='s' else (1/c-3.42/ct)/(1/c+3.42/ct)
            np.testing.assert_allclose(R[j],r*r,atol=1e-14);np.testing.assert_allclose(R[j]+P[j],1,atol=1e-14)
    def test_no_nk_extrapolation(self):
        with self.assertRaises(ValueError):h.nk_values('MgF2_Franta',np.array([1.,12.]))
    def test_known_k_preserved(self):
        nk=h.nk_values('MgF2_Franta',np.array([10.,12.]));self.assertTrue(np.all(nk.imag>1e-3))
    def test_weights_and_gap(self):
        obj=h.Objective(h.case_def('synthetic6_multi'),20)
        self.assertAlmostEqual(float((obj.sqrtw**2).sum()*len(obj.model.wl)),1.)
        self.assertFalse(np.any((obj.model.wl>5)&(obj.model.wl<8)))
    def test_exact_count_includes_finite_differences(self):
        o=h.Objective(h.case_def('synthetic6_normal'),17);x=h.templates(o.case)[0][1];h.local(o,x,17,'test');self.assertEqual(o.calls,17)
        with self.assertRaises(h.BudgetEnd):o.scalar(x)
    def test_archive_never_loses_minimax_candidate(self):
        o=h.Objective(h.case_def('synthetic6_normal'),50)
        for label,x in h.templates(o.case):o.scalar(x)
        worst=o.best_violation
        for i in range(10):o.scalar(np.random.default_rng(i).uniform(h.LOWER,h.UPPER,6))
        self.assertLessEqual(o.best_violation,worst)
    def test_all_methods_budget_and_repeatability(self):
        c=h.case_def('synthetic6_normal')
        for method in h.METHODS:
            r=h.run(c,method,11,120,21);s=h.run(c,method,11,120,21)
            self.assertEqual(r['actual_objective_calls'],120);self.assertEqual(r['stage_counts'],s['stage_counts']);self.assertEqual(r['thickness_um'],s['thickness_um'])
    def test_midpoint_audit_is_read_only(self):
        r=h.run(h.case_def('tabulated6_multi'),'classic_local',11,120,21);before=r['thickness_um'].copy();a=h.audit(r,65)
        self.assertEqual(before,r['thickness_um']);self.assertLess(a['independent_matrix_max_abs_error'],1e-11);self.assertGreater(a['min_coating_absorptance'],-1e-11)
    def test_real_flux_hinge(self):
        c=h.case_def('tabulated6_multi');o=h.Objective(c,1,21);r=o.residual(h.templates(c)[0][1]);self.assertEqual(len(r),3*5*2*21)
    def test_reject_negative_and_wrong_shape(self):
        c=h.case_def('synthetic6_normal');m,s=h.materials(c);model=h.OpticalModel(np.array([4.]),m,s,[0.])
        with self.assertRaises(ValueError):model.solve([-1]*6)
        with self.assertRaises(ValueError):model.solve([1]*5)

if __name__=='__main__':unittest.main(verbosity=2)
