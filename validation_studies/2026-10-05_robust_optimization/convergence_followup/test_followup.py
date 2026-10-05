"""Phase/ROI/partition checks use synthetic injected fields, no cub computation."""
from dataclasses import replace
import json
import math
import unittest

import numpy as np
from run_followup import HERE, FIRST, FollowupEvaluator, roi_weights, get_cases
from evaluator import scenario_draws, clipped_cell_weights
from build_report import axis_assessment, phase_assessment


class FollowupTests(unittest.TestCase):
    def test_interior_roi_coverage_is_constant(self):
        for grid in (21, 41, 61):
            axis = np.linspace(-100., 100., grid)
            x, y = np.meshgrid(axis, axis)
            valid = x*x+y*y <= 10000.
            weights, coverage = roi_weights(axis, valid, 90.)
            self.assertAlmostEqual(weights.sum(), 1., places=12)
            self.assertLess(abs(coverage-1.), 5e-6)
            self.assertGreaterEqual(weights.min(), 0.)

    def test_constant_field_phase_identity(self):
        settings_seen = []
        def constant(settings, mask, xp, device, cancel, source_positions, source_weights, **kwargs):
            settings_seen.append(settings)
            axis = np.linspace(-100., 100., settings.grid_size)
            x, y = np.meshgrid(axis, axis)
            field = np.where(x*x+y*y <= 10000., 1., np.nan)
            return {"field": field, "mean_raw": 1., "x": axis}
        z = np.zeros(12); z[11] = 1.
        for alpha in (.25, .5, .75):
            ev = FollowupEvaluator({"grid_size": 21, "time_steps": 96, "source_order": 3}, alpha)
            ev.forward = constant
            row = ev.evaluate([100., 5., 5.], z, .05)
            rpm = 15.*1.05
            shift = (alpha-.5)*12/96
            self.assertAlmostEqual(settings_seen[-1].carrier_phase_deg, 6*rpm*shift)
            self.assertAlmostEqual(settings_seen[-1].planet_phase_deg, 6*rpm*(1+120/36)*shift)
            self.assertEqual(row["cv_percent"], 0.)
            self.assertAlmostEqual(row["interior90_cv_percent"], 0., places=12)
            self.assertEqual(ev.counter.forward_calls, 2)

    def test_node_offsets_stay_in_original_window(self):
        for alpha in (.25, .5, .75):
            n=96; times=(np.arange(n)+alpha)*12/n
            self.assertGreater(times.min(), 0.)
            self.assertLess(times.max(), 12.)

    def test_case_draws_are_original_holdout_prefix(self):
        cfg=json.loads((HERE/'config.json').read_text())
        first=json.loads((FIRST/'results/study_results.json').read_text())
        for case in get_cases(cfg,first):
            self.assertTrue(np.array_equal(case['holdout'],scenario_draws(case['seed'],64,'holdout')[:4]))
            self.assertEqual(set(case['designs']),{'nominal','robust'})

    def test_full_circle_coverage_changes_are_disclosed(self):
        coverage=[]
        for grid in (21,41,61):
            axis=np.linspace(-100.,100.,grid);x,y=np.meshgrid(axis,axis)
            _,c=clipped_cell_weights(axis,x*x+y*y<=10000.,100.)
            coverage.append(c)
        self.assertLess(coverage[0],coverage[-1])
        self.assertLess(coverage[-1],1.)

    def test_gap_relative_acceptance(self):
        def rung(a,b):
            return {'methods':{'nominal':{'mean_cv_percent':a},'robust':{'mean_cv_percent':b}}}
        stable=[rung(1.,.95),rung(1.001,.951),rung(1.0015,.9515)]
        self.assertTrue(axis_assessment(stable,.05,'mean_cv_percent')['passed'])
        changing=[rung(1.,.95),rung(1.02,.97),rung(1.021,.971)]
        self.assertFalse(axis_assessment(changing,.05,'mean_cv_percent')['passed'])
        reversal=[rung(1.,1.05),rung(1.,.95),rung(1.,.95)]
        self.assertFalse(axis_assessment(reversal,.05,'mean_cv_percent')['passed'])

    def test_phase_spread_acceptance(self):
        def rung(a,b):
            return {'methods':{'nominal':{'mean_cv_percent':a},'robust':{'mean_cv_percent':b}}}
        self.assertTrue(phase_assessment([rung(1.,.95),rung(1.001,.951),rung(1.002,.952)],.05,'mean_cv_percent')['passed'])
        self.assertFalse(phase_assessment([rung(1.,.95),rung(1.02,.97),rung(1.,.95)],.05,'mean_cv_percent')['passed'])


if __name__=='__main__':
    unittest.main()
