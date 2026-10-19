"""Small regression tests; no external packages beyond numpy/scipy needed."""
import unittest
import numpy as np
from run_experiment import (validate_physics, tmm_normal, reflection_recursion,
                             Objective, BudgetExhausted, run_one, CASES, metrics,
                             LAYER_N, TARGET_R)

class ExperimentTests(unittest.TestCase):
    def test_physics_validation(self):
        self.assertTrue(validate_physics()['all_checks_passed'])

    def test_recursion_single_layer_closed_form(self):
        wl = np.linspace(3., 12., 199)
        n0, nf, ns, d = 1., 1.8, 3.42, .73
        r01, r12 = (n0-nf)/(n0+nf), (nf-ns)/(nf+ns)
        phase = np.exp(4j*np.pi*nf*d/wl)
        expected = np.abs((r01+r12*phase)/(1+r01*r12*phase))**2
        r, _ = tmm_normal(wl, [d], [nf], n0, ns)
        np.testing.assert_allclose(r, expected, atol=2e-15, rtol=2e-14)

    def test_budget_counts_residual_and_scalar(self):
        o = Objective(CASES['single_ar_3_5'], 2)
        x = [.1]*6
        residual = o.residual(x)
        loss = o.scalar(x)
        self.assertEqual(o.calls, 2)
        self.assertAlmostEqual(float(residual@residual), loss)
        with self.assertRaises(BudgetExhausted):
            o.scalar(x)
        self.assertEqual(o.calls, 2)

    def test_equal_window_weight(self):
        one = Objective([(3., 5.)], 1)
        repeated = Objective([(3., 5.), (3., 5.)], 1)
        x = [.1]*6
        self.assertAlmostEqual(one.scalar(x), repeated.scalar(x), places=10)

    def test_gap_not_in_training_grid(self):
        o = Objective(CASES['dual_window_ar_3_5_8_12'], 1)
        self.assertFalse(np.any((o.all_wl>5.) & (o.all_wl<8.)))
        self.assertEqual(len(o.all_wl), 162)

    def test_grid_max_is_per_window(self):
        out = metrics([.1]*6, CASES['dual_window_ar_3_5_8_12'], 16385)
        self.assertEqual(len(out), 2)
        for m in out:
            self.assertGreaterEqual(m['max_R'], m['mean_R_sampled'])
            self.assertAlmostEqual(m['worst_violation_absolute'], max(m['max_R']-TARGET_R,0))
            self.assertLess(m['max_energy_error'], 1e-11)

    def test_invalid_exterior_rejected(self):
        with self.assertRaises(ValueError):
            tmm_normal([4], [.1], [1.8], ns=3.42+.01j)

if __name__ == '__main__':
    unittest.main()
