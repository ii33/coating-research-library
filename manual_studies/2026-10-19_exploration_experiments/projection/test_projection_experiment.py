import contextlib
import io
import json
import math
import unittest
from pathlib import Path
import numpy as np
import run_projection_experiment as e

class ProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        e.COUNTS.clear()
        cls.physics=e.check_physics()
        cls.cases=[e.experiment('test_interior',e.D_MAX),e.experiment('test_boundary',.4)]

    def test_scalar_amplitudes_match_verified_power_kernel(self):
        self.assertLess(self.physics['amplitude_R_vs_verified_kernel_max_error'],1e-13)
        self.assertLess(self.physics['amplitude_T_vs_verified_kernel_max_error'],1e-13)
        self.assertLess(self.physics['lossless_energy_max_error'],1e-13)

    def test_common_reference_and_length_unit_invariance(self):
        self.assertLess(self.physics['common_reference_ambient_insertion_error'],1e-13)
        self.assertLess(self.physics['um_vs_nm_identical_physics_error'],1e-13)

    def test_redundant_same_material_split(self):
        self.assertLess(self.physics['same_material_split_error'],1e-13)
        for case in self.cases:
            row=next(r for r in case['candidates'] if r['label']=='redundant_same_material_split')
            self.assertLess(abs(row['finite_max_R']-case['base_max_R']),1e-13)
            self.assertLess(row['orthogonal_norm'],1e-12)

    def test_interior_analytic_stationarity_and_all_finite_scores(self):
        case=self.cases[0]
        # delta(3um)+delta(5um)=pi balances the two endpoint maxima.
        expected=1/(2*1.45*(1/3+1/5))
        self.assertAlmostEqual(case['base_d_um'][0],expected,places=10)
        self.assertLess(case['tangent_stationarity_norm'],1e-10)
        self.assertLess(case['max_raw_projected_inner_error'],1e-10)
        for mu in case['active_mu']:self.assertGreaterEqual(mu,0.)
        self.assertAlmostEqual(sum(case['active_mu']),1.)
        self.assertEqual(case['methods']['raw_inner']['order_labels'],case['methods']['projected_inner']['order_labels'])

    def test_boundary_frozen_projection_and_invalid_full_projection(self):
        case=self.cases[1]
        self.assertEqual(case['free_coordinates'],[False])
        self.assertLess(case['max_raw_projected_inner_error'],1e-13)
        self.assertGreater(case['max_incorrect_full_projected_score_error'],1.)
        self.assertGreater(case['full_stationarity_norm'],1.)

    def test_all_candidates_and_repairs_legal_and_budgeted(self):
        for case in self.cases:
            for row in case['candidates']:
                for ds in [row['d'],row['repaired_d']]:
                    self.assertTrue(all(e.D_MIN-1e-12 <= d <= case['bound_upper_um']+1e-12 for d in ds))
                self.assertTrue(all(a!=b for a,b in zip(row['n'],row['n'][1:])))
                self.assertLessEqual(row['repair_calls'],e.REPAIR_BUDGET)
                self.assertGreaterEqual(row['repaired_dense_max_R'],0.)
                self.assertLessEqual(row['repaired_dense_max_R'],1.+1e-12)
                self.assertAlmostEqual(row['repaired_dense_min_T']+row['repaired_dense_max_R'],1.)

    def test_no_tiny_numerical_gain_misreported_as_advantage(self):
        for case in self.cases:
            finite=case['methods']['finite_max_R']
            bounded=case['methods']['bounded_predicted_max_R']
            for k in ['top1','top3']:
                self.assertLess(abs(finite[k]['best_dense_max_R']-bounded[k]['best_dense_max_R']),1e-7)
                self.assertFalse(finite[k]['feasible'])
                self.assertEqual(finite[k]['allocated_amplitude_calls'],0)

    def test_reproducibility(self):
        again=e.experiment('test_repeat',e.D_MAX)
        original=self.cases[0]
        for key in ['base_d_um','base_max_R','oracle_dense_max_R','methods','random_seeds','candidates']:
            self.assertEqual(original[key],again[key])

if __name__=='__main__':unittest.main(verbosity=2)
