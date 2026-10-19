import hashlib,json,unittest
from pathlib import Path
import numpy as np
from run_phase import ROOT,CASES,LOWER,UPPER,amplitudes,physics_checks
from verified_kernel import tmm_normal
from withdrawal_and_counterexamples import counterexamples
class PhaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'results.json').read_text())
        cls.extra=json.loads((ROOT/'withdrawal_and_counterexamples.json').read_text())
    def test_kernel_and_amplitudes(self):
        p=physics_checks()
        for key in ['matrix_R_max_error','matrix_T_max_error','independent_recursion_R_max_error','energy_max_error','fixed_plane_covariance_error']:
            self.assertLess(p[key],1e-10)
    def test_fixed_reference_correction_and_coordinate_covariance(self):
        w=np.linspace(3.,12.,33); n=[1.45,2.35]; d=[.5,.9]
        r,t=amplitudes(w,d,n); rf,tf=amplitudes(w,d,n,reference_depth=5.)
        np.testing.assert_allclose(rf,r*np.exp(4j*np.pi*(5-sum(d))/w),atol=1e-14)
        np.testing.assert_allclose(tf,t*np.exp(2j*np.pi*(5-sum(d))/w),atol=1e-14)
        r2,_=amplitudes(w,d,n,reference_depth=5.,plane_shift=1.713)
        np.testing.assert_allclose(r2,rf*np.exp(4j*np.pi*1.713/w),atol=1e-13)
    def test_zero_thickness_not_infeasibility(self):
        p=self.data['checks']['zero_thickness']; self.assertEqual(p['exact_dR_dd'],0.)
        self.assertLess(abs(p['forward_derivative_h_half']),.51*abs(p['forward_derivative_h']))
        self.assertLess(p['quarterwave_R'],1e-25)
        self.assertGreater(p['quarterwave_thickness_um'],LOWER)
    def test_matched_starts_and_actual_cost(self):
        for case in CASES:
            for seed in [11,29,47]:
                rr=[r for r in self.data['rows'] if r['case']==case and r['seed']==seed and r['method']!='direct_local']
                self.assertEqual(len(rr),5)
                self.assertEqual(len({r['total']['point_layers'] for r in rr}),1)
                for r in rr[1:]: self.assertEqual(r['starting_designs_um'],rr[0]['starting_designs_um'])
                for r in rr:
                    self.assertEqual(r['counts']['jacobian_fd']['calls'],80*len(CASES[case]['n']))
                    self.assertEqual(r['counts']['trial']['calls'],80)
                    self.assertEqual(r['counts']['archive_audit']['calls'],84)
                    self.assertEqual(r['counts']['final_audit']['calls'],1)
    def test_true_epigraph_final_and_phase_bound(self):
        for r in self.data['rows']:
            self.assertTrue(r['all_branches_reached_tau1']); self.assertEqual(r['final_auxiliary_weight'],0.)
            if r['method'] in ['direct_multistart_cap','amplitude_homotopy','phase_homotopy']:
                self.assertLessEqual(max(h['max_single_layer_delta_phase'] for h in r['history']),np.pi/4+1e-8)
    def test_archive_order_and_power_reaudit(self):
        for r in self.data['rows']:
            values=[(a['V'],a['mean_R']) for a in r['archive']]
            for a,b in zip(values,values[1:]): self.assertLess(b,a)
            d=np.array(r['d_um']); self.assertTrue(np.all(d>=LOWER)); self.assertTrue(np.all(d<=UPPER))
            cfg=CASES[r['case']]; w=np.r_[tuple(np.linspace(a,b,2049) for a,b in cfg['windows'])]
            R,T=tmm_normal(w,d,cfg['n'])
            self.assertAlmostEqual(r['V'],max(0,float(R.max()/.01-1)),places=11)
            self.assertLess(float(np.max(abs(R+T-1))),1e-12)
    def test_final_grid_overlap_is_disclosed(self):
        archive=np.linspace(3,5,257); final=np.linspace(3,5,2049)
        self.assertEqual(len(set(archive)&set(final)),257)
        self.assertEqual(len(set(final)-set(archive)),1792)
    def test_zero_rotation_equals_amplitude_control(self):
        for r in self.extra['theta_sensitivity']:
            if r['theta_max']!=0: continue
            baseline=next(z for z in self.data['rows'] if z['case']=='dual_ar' and z['seed']==r['seed'] and z['method']=='amplitude_homotopy')
            self.assertEqual(r['V'],baseline['V']); self.assertEqual(r['d_um'],baseline['d_um'])
    def test_true_power_withdrawal_is_complete(self):
        for r in self.extra['polished']:
            self.assertTrue(all(h['tau']==1 and h['auxiliary_weight']==0 for h in r['history']))
            self.assertEqual(r['final_auxiliary_weight'],0.)
            self.assertEqual(len(r['history']),12)
            self.assertTrue(r['all_polish_iterations_auxiliary_weight_zero'])
            self.assertEqual(r['pure_power_iterations_completed'],12)
            self.assertLessEqual(r['V'],r['before_V'])
            self.assertIn('input_archive_origin_tau',r)
    def test_counterexamples(self):
        d=counterexamples()
        self.assertGreater(d['cost']['calls'],0)
        self.assertGreater(d['cost']['point_layers'],d['cost']['points'])
        self.assertLess(d['passive_absorption']['R'],1e-20)
        self.assertLess(d['passive_absorption']['T'],.6)
        self.assertGreater(d['high_Q']['R_after'],.8)
        self.assertGreater(d['reflection_zero']['phase_jump_rad'],3.)
        self.assertGreater(d['incompatible_phase_targets']['relative_linear_least_squares_residual'],.9)
    def test_reference_coordinate_shift_does_not_change_ranking_scale(self):
        self.assertLess(self.data['checks']['optimization_fixed_plane_shift_V_difference'],1e-4)
        self.assertLess(self.data['checks']['optimization_fixed_plane_shift_thickness_max_difference'],1e-5)
if __name__=='__main__': unittest.main(verbosity=2)
