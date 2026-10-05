import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
import numpy as np
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from calibration import (FixedGeometry, fit_source, predict_fitted, mass_rate_to_mass_flux,
                         validate_actual_input, geometry_from_production_source, STUDY, _ref)
from condition_surrogate import QCMConditionGP
from run_study import geometry


class SourceCalibrationTests(unittest.TestCase):
    def setUp(self):
        self.geometry = geometry([8, 30, 55], [0, 120, 240])
        self.A = 2e-6

    def test_cosine_normalization_n0_n1_n4(self):
        nodes, weights = np.polynomial.legendre.leggauss(32)
        for n in [0., 1., 4.]:
            mu = (nodes + 1) / 2
            hemispherical_integral = float(np.sum(weights / 2 * 2 * np.pi * _ref.cosine_pdf(mu, n)))
            self.assertAlmostEqual(hemispherical_integral, 1., places=13)
        np.testing.assert_array_equal(_ref.cosine_pdf(np.array([-1, -.5, 0.]), 0.), [0., 0., 0.])

    def test_point_kernel_matches_independent_paper_formula(self):
        x = self.geometry.qcm_coords_m
        distance = np.linalg.norm(x, axis=1)
        mu = x[:, 2] / distance
        for n in [0., 1., 4.]:
            expected = (n + 1) / (2 * np.pi) * mu**n * mu / distance**2
            np.testing.assert_allclose(self.geometry.kernel(n), expected, rtol=1e-14)

    def test_analytic_derivative_point_and_finite_source(self):
        disk = _ref.disk_source(.04, nr=3, nphi=12)
        for geo in [self.geometry, geometry([8, 30, 55], source=disk)]:
            for n in [0., 1., 4.]:
                epsilon = 1e-6
                if n == 0:
                    numeric = (-3 * geo.kernel(n) + 4 * geo.kernel(n + epsilon) - geo.kernel(n + 2 * epsilon)) / (2 * epsilon)
                else:
                    numeric = (geo.kernel(n + epsilon) - geo.kernel(n - epsilon)) / (2 * epsilon)
                np.testing.assert_allclose(geo.kernel_derivative(n), numeric, rtol=2e-8, atol=1e-9)

    def test_noiseless_recovery_and_boundaries(self):
        for n in [0., 1., 4.]:
            fit = fit_source(self.geometry, self.geometry.predict(self.A, n), np.zeros(3))
            self.assertAlmostEqual(fit['A_kg_s'] / self.A, 1., places=7)
            self.assertAlmostEqual(fit['n'], n, places=7)
            self.assertEqual(fit['jacobian_rank'], 2)
            if n == 0:
                self.assertTrue(fit['boundary_solution'])
                self.assertIsNone(fit['covariance_lnA_n'])
            else:
                self.assertIsNotNone(fit['covariance_lnA_n'])

    def test_declared_n_cap_is_diagnostic_not_truth(self):
        truth = self.geometry.predict(self.A, 4.)
        fit = fit_source(self.geometry, truth, .01 * truth, n_max=2.)
        self.assertEqual(fit['n'], 2.)
        self.assertTrue(fit['boundary_solution'])
        self.assertTrue(fit['profile_open_at_cap'])
        self.assertTrue(any('cap' in warning for warning in fit['warnings']))

    def test_same_ring_rank_one_and_map_rejected(self):
        ring = geometry([30] * 6, np.arange(6) * 60)
        truth = ring.predict(self.A, 4.)
        fit = fit_source(ring, truth, .01 * truth)
        self.assertEqual(fit['jacobian_rank'], 1)
        self.assertFalse(fit['identifiable'])
        self.assertIsNone(fit['covariance_lnA_n'])
        self.assertTrue(fit['profile_open_at_cap'])
        with self.assertRaisesRegex(ValueError, 'not identifiable'):
            predict_fitted(fit, self.geometry, configuration_id=ring.configuration_id)
        for n in [0, 1, 4, 20]:
            A = float(np.mean(truth / ring.kernel(n)))
            np.testing.assert_allclose(ring.predict(A, n), truth, rtol=2e-14)

    def test_zero_source_has_no_shape_information(self):
        fit = fit_source(self.geometry, np.zeros(3), np.full(3, 1e-9))
        self.assertEqual(fit['A_kg_s'], 0.)
        self.assertEqual(fit['jacobian_rank'], 0)
        self.assertFalse(fit['identifiable'])
        self.assertIsNone(fit['covariance_lnA_n'])

    def test_baseline_subtraction_negative_data_not_positive_source(self):
        fit = fit_source(self.geometry, -np.ones(3) * 1e-9, np.ones(3) * 1e-9)
        self.assertEqual(fit['A_kg_s'], 0.)
        self.assertFalse(fit['identifiable'])

    def test_near_axis_uncertainty_worse_than_distinct_angles(self):
        near = geometry([1, 2, 3])
        results = []
        for geo in [near, self.geometry]:
            truth = geo.predict(self.A, 4.)
            results.append(fit_source(geo, truth, .01 * truth))
        self.assertGreater(results[0]['jacobian_condition'], 100 * results[1]['jacobian_condition'])
        self.assertGreater(results[0]['covariance_lnA_n'][1][1], 1000 * results[1]['covariance_lnA_n'][1][1])

    def test_more_same_angle_distances_do_not_identify_n(self):
        angles = np.deg2rad(30.)
        heights = np.array([.3, .6, .9])
        coords = np.column_stack((heights * np.tan(angles), np.zeros(3), heights))
        geo = FixedGeometry([[0, 0, 0]], [[0, 0, 1]], [1.], coords,
                            np.tile([0., 0., -1.], (3, 1)), np.full(3, 1e-4), 'same_angle_distances')
        truth = geo.predict(self.A, 1.)
        self.assertEqual(fit_source(geo, truth, .01 * truth)['jacobian_rank'], 1)

    def test_mass_rate_conversion_area_is_not_applied_twice(self):
        area = np.array([1e-4, 2e-4, 3e-4])
        flux, sd = mass_rate_to_mass_flux(area * 1e-6, area * 1e-8, area)
        np.testing.assert_allclose(flux, 1e-6)
        np.testing.assert_allclose(sd, 1e-8)
        with self.assertRaises(ValueError):
            mass_rate_to_mass_flux(np.ones(3), np.ones(3), np.zeros(3))

    def test_noise_floor_nonfinite_inputs_shapes_rejected(self):
        truth = self.geometry.predict(self.A, 1.)
        for floor in [0, -1e-9, float('nan')]:
            with self.assertRaises(ValueError):
                fit_source(self.geometry, truth, np.zeros(3), noise_floor_kg_m2_s=floor)
        for y, sd in [(truth[:2], np.ones(2)), (truth, [-1, 1, 1]), ([np.nan, 1, 1], np.ones(3))]:
            with self.assertRaises(ValueError):
                fit_source(self.geometry, y, sd)

    def test_actual_unknown_and_wrong_reading_type_rejected(self):
        actual = json.loads((STUDY / 'data/actual_unknown.json').read_text())
        with self.assertRaisesRegex(ValueError, 'explicit measurements'):
            validate_actual_input(actual)
        c = {**self.geometry.contract(), 'mass_flux_kg_m2_s': [1e-6] * 3,
             'sd_kg_m2_s': [1e-8] * 3, 'noise_floor_kg_m2_s': 1e-12, 'reading_type': 'areal_mass_flux'}
        self.assertEqual(validate_actual_input(c).configuration_id, self.geometry.configuration_id)
        c['reading_type'] = 'thickness_nm_s'
        with self.assertRaisesRegex(ValueError, 'areal_mass_flux'):
            validate_actual_input(c)
        c['reading_type'] = 'areal_mass_flux'; c['noise_floor_kg_m2_s'] = -1
        with self.assertRaises(ValueError):
            validate_actual_input(c)

    def test_configuration_id_checked_on_both_fit_and_receiving_geometry(self):
        truth = self.geometry.predict(self.A, 1.)
        fit = fit_source(self.geometry, truth, .01 * truth)
        other = geometry([8, 30, 55], configuration_id='changed_fixture')
        with self.assertRaisesRegex(ValueError, 'configuration mismatch'):
            predict_fitted(fit, other, configuration_id='changed_fixture')
        with self.assertRaises(ValueError):
            predict_fitted(fit, self.geometry, configuration_id='arbitrary')

    def test_production_geometry_adapter_reuses_actual_source_samples(self):
        settings = SimpleNamespace(source_x_mm=100., source_y_mm=-20., source_z_mm=0.)
        adapted = geometry_from_production_source(settings, {'kind': 'point'},
                        self.geometry.qcm_coords_m, self.geometry.qcm_normals,
                        self.geometry.qcm_area_m2, 'test_adapter')
        np.testing.assert_array_equal(adapted.source_nodes_m, [[.1, -.02, 0.]])
        np.testing.assert_array_equal(adapted.source_fractions, [1.])

    def test_invalid_normal_geometry_and_capture_fraction_rejected(self):
        base = self.geometry.contract()
        for key, value in [('qcm_normals', [[0., 0., -2.]] * 3),
                           ('qcm_area_m2', [0., 1e-4, 1e-4]),
                           ('capture_fraction', [1., 2., 1.]),
                           ('qcm_coords_m', [[0, 0, 0]] * 3),
                           ('source_fractions', [0.5])]:
            changed = {k: copy.deepcopy(v) for k, v in base.items() if k != 'receiver_model'}
            changed[key] = value
            with self.assertRaises(ValueError):
                FixedGeometry(**changed)


class ConditionGPTests(unittest.TestCase):
    def setUp(self):
        self.x = np.array([[40, 5], [100, 5], [40, 25], [100, 25], [70, 15]], float)
        self.y = np.column_stack([self.x[:, 0] * 1e-8, self.x[:, 1] * 1e-8, (self.x[:, 0] + self.x[:, 1]) * 1e-8])
        self.gp = QCMConditionGP(self.x, self.y, np.zeros_like(self.y), configuration_id='g1')

    def test_training_reproduction_and_finite_uncertainty(self):
        mean, sd = self.gp.predict(self.x, configuration_id='g1')
        np.testing.assert_allclose(mean, self.y, rtol=1e-9)
        self.assertTrue(np.all(np.isfinite(sd)))
        self.assertTrue(np.all(sd >= 0))

    def test_outside_hull_and_changed_configuration_rejected(self):
        for point in [[110, 15], [70, 30]]:
            with self.assertRaisesRegex(ValueError, 'extrapolation blocked'):
                self.gp.predict(point, configuration_id='g1')
        with self.assertRaisesRegex(ValueError, 'configuration changed'):
            self.gp.predict([70, 15], configuration_id='g2')

    def test_convex_hull_not_just_bounding_rectangle(self):
        x = np.array([[40, 5], [100, 5], [40, 25], [60, 10]], float)
        y = np.full((4, 3), 1e-6)
        gp = QCMConditionGP(x, y, np.full_like(y, 1e-8), configuration_id='triangle')
        with self.assertRaisesRegex(ValueError, 'extrapolation blocked'):
            gp.predict([90, 22], configuration_id='triangle')

    def test_degenerate_and_duplicate_conditions_rejected(self):
        for x in [np.array([[40, 5], [50, 5], [70, 5], [100, 5]]),
                  np.array([[40, 5], [60, 10], [80, 15], [100, 20]]),
                  np.array([[40, 5], [100, 5], [40, 25], [40, 25]])]:
            with self.assertRaises(ValueError):
                QCMConditionGP(x, np.full((4, 3), 1e-6), np.full((4, 3), 1e-8), configuration_id='g1')


if __name__ == '__main__':
    unittest.main()
