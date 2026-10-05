"""Small identity/contract tests, not physical or manufacturing validation."""
from dataclasses import asdict
import unittest
import numpy as np
from evaluator import (Evaluator, objective, scenario_draws, scenarios_hash,
                       masks_for_design, weighted_metrics, source_hashes)
from run_study import optimize, paired_bootstrap, summarize

DESIGN = [100., 5., 5.]
CONSTRAINTS = {"cv_max_percent": 2., "throughput_min": .85}


class EvaluatorTests(unittest.TestCase):
    def test_zero_perturbation_identity(self):
        ev = Evaluator()
        a = ev.evaluate(DESIGN)
        b = ev.evaluate(DESIGN, np.arange(12.), 0.)
        self.assertEqual(a, b)
        self.assertEqual(ev.counter.forward_calls, 4)

    def test_zero_scenario_objective_identity(self):
        row = Evaluator().evaluate(DESIGN)
        self.assertEqual(objective([row] * 4, "robust", CONSTRAINTS),
                         objective([row], "nominal", CONSTRAINTS))

    def test_deterministic_evaluator(self):
        z = scenario_draws(11, 1, "holdout")[0]
        self.assertEqual(Evaluator().evaluate(DESIGN, z, .05),
                         Evaluator().evaluate(DESIGN, z, .05))

    def test_budget_counts_bare_reference(self):
        ev = Evaluator(budget=2)
        self.assertTrue(ev.evaluate(DESIGN)["valid"])
        self.assertEqual(ev.counter.forward_calls, 2)
        with self.assertRaisesRegex(RuntimeError, "budget exhausted"):
            ev.evaluate(DESIGN)
        self.assertEqual(ev.counter.forward_calls, 2)

    def test_atomic_budget_preflight(self):
        ev = Evaluator(budget=1)
        with self.assertRaises(RuntimeError):
            ev.evaluate(DESIGN)
        self.assertEqual(ev.counter.forward_calls, 0)

    def test_failed_calls_are_charged(self):
        def fail(*args, **kwargs):
            raise RuntimeError("injected forward failure")
        ev = Evaluator(forward=fail)
        self.assertFalse(ev.evaluate(DESIGN)["valid"])
        self.assertEqual(ev.counter.forward_calls, 1)
        self.assertEqual(ev.counter.failed_forward_calls, 1)
        self.assertEqual(len(ev.failures), 1)

    def test_invalid_degenerate_design(self):
        ev = Evaluator()
        for design in ([100., 0., 5.], [np.nan, 5., 5.], [100., 5.]):
            self.assertFalse(ev.evaluate(design)["valid"])
        self.assertEqual(ev.counter.forward_calls, 0)
        self.assertEqual(ev.counter.invalid_candidates, 3)

    def test_invalid_amplitude_and_exponent(self):
        ev = Evaluator()
        for j in (9, 10):
            z = np.zeros(12); z[j] = -100.
            self.assertFalse(ev.evaluate(DESIGN, z, .05)["valid"])
        self.assertEqual(ev.counter.forward_calls, 0)

    def test_invalid_board_height(self):
        z = np.zeros(12); z[5] = 100.
        ev = Evaluator()
        self.assertFalse(ev.evaluate(DESIGN, z, .05)["valid"])
        self.assertEqual(ev.counter.forward_calls, 0)

    def test_amplitude_cancels_relative_metrics(self):
        ev = Evaluator()
        a = ev.evaluate(DESIGN)
        z = np.zeros(12); z[9] = 2.
        b = ev.evaluate(DESIGN, z, .05)
        self.assertAlmostEqual(a["cv_percent"], b["cv_percent"], places=12)
        self.assertAlmostEqual(a["throughput"], b["throughput"], places=12)
        self.assertAlmostEqual(b["area_mean_raw"] / a["area_mean_raw"], 1.1, places=12)

    def test_train_holdout_separation(self):
        a = scenario_draws(11, 3, "train")
        b = scenario_draws(11, 64, "holdout")
        self.assertNotEqual(scenarios_hash(a), scenarios_hash(b))
        self.assertFalse(any(np.array_equal(x, y) for x in a for y in b))
        self.assertTrue(np.array_equal(b, scenario_draws(11, 64, "holdout")))

    def test_area_weighting_and_coverage_disclosed(self):
        ev = Evaluator(); row = ev.evaluate(DESIGN)
        self.assertAlmostEqual(ev.weights.sum(), 1., places=12)
        self.assertTrue(.9 < row["represented_area_fraction"] < 1.)
        self.assertGreater(np.ptp(ev.weights[ev.weights > 0]), 0.)
        self.assertEqual(row["source_samples"], 9)

    def test_zero_deposition_not_perfect(self):
        result = {"field": np.ones((2, 2)), "mean_raw": 0.}
        with self.assertRaises(ValueError):
            weighted_metrics(result, np.ones((2, 2)) / 4)

    def test_masks_geometrically_non_degenerate(self):
        masks = masks_for_design(DESIGN, np.zeros(12))
        self.assertEqual(len(masks), 2)
        self.assertEqual([m["z_mm"] for m in masks], [350., 450.])
        for m in masks:
            p = m["outer"]
            self.assertGreater(np.ptp(p[:, 0]), 0.)
            self.assertGreater(np.ptp(p[:, 1]), 0.)

    def test_optimizer_budget_and_determinism(self):
        config = {"resolution": {"grid_size": 21, "time_steps": 8, "source_order": 3},
            "training_actual_forward_budget_per_method": 16,
            "random_training_scenarios": 3, "bounds": [[80., 240.], [3., 30.], [3., 30.]],
            "initial_design": DESIGN, "constraints": CONSTRAINTS, "lambda_sd": 1.}
        for mode in ("nominal", "robust"):
            a = optimize(config, 11, .01, mode)
            b = optimize(config, 11, .01, mode)
            self.assertEqual(a["design"], b["design"])
            self.assertEqual(a["training_rank"], b["training_rank"])
            self.assertEqual(a["counter"]["forward_calls"], 16)

    def test_paired_interval_identical_designs(self):
        rows = [Evaluator().evaluate(DESIGN)] * 8
        data = paired_bootstrap(rows, rows, CONSTRAINTS, 11, 200)
        for metric in data.values():
            self.assertEqual(metric["estimate"], 0.)
            self.assertEqual(metric["percentile_95_interval"], [0., 0.])

    def test_invalid_rows_count_as_violations(self):
        row = Evaluator().evaluate(DESIGN)
        summary = summarize([row, {"valid": False}], CONSTRAINTS)
        self.assertEqual(summary["invalid_n"], 1)
        self.assertEqual(summary["violation_count"], 1)

    def test_product_source_unchanged(self):
        before = source_hashes()
        Evaluator().evaluate(DESIGN)
        self.assertEqual(before, source_hashes())


if __name__ == "__main__":
    unittest.main()
