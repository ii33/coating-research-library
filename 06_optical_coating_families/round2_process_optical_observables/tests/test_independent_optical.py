"""Small, independent unit/optics spot checks for the process-observables model.

These do not validate materials, a physical sample, instrumentation, or production
qualification. From the round2_process_optical_observables directory, run with
``python -m unittest discover -s tests -p 'test_independent_optical.py'``.
"""
import json
from pathlib import Path
import sys
import unittest

import numpy as np

HERE = Path(__file__).resolve().parents[1]
MODELS = HERE / "models"
sys.path.insert(0, str(MODELS))

from batch_driver import run as run_batch  # noqa: E402
from process_optics import (  # noqa: E402
    Blocked,
    NA,
    MOLAR_MASS_KG,
    ROOT,
    alpha_to_k,
    evaluate,
    film_index,
    film_inventory,
)
from vendor.optics_kernel import scattering as local_scattering  # noqa: E402


def load_json(path):
    return json.loads(path.read_text())


def synthetic_record():
    return load_json(ROOT / "examples" / "synthetic_dielectric.json")


def one_wavelength_record():
    record = synthetic_record()
    record["measurement"]["wavelength_um"] = [0.55]
    return record


class IndependentOpticalSpotChecks(unittest.TestCase):
    def test_atoms_per_area_to_kg_per_area_to_um_and_qcm_separate(self):
        record = synthetic_record()
        final_atoms = (
            record["process"]["initial_inventory_atoms_m2"]["Al"]
            + record["process"]["bins"][0]["net_atoms_m2_s"]["Al"]
            * (record["process"]["bins"][0]["end_s"] - record["process"]["bins"][0]["start_s"])
        )
        independent_mass = final_atoms * MOLAR_MASS_KG["Al"] / NA
        independent_um = independent_mass / record["film_state"]["density_kg_m3"] * 1e6
        result = film_inventory(record)

        self.assertAlmostEqual(result["final_inventory_atoms_m2"]["Al"], final_atoms, places=5)
        self.assertAlmostEqual(result["areal_mass_kg_m2"], independent_mass, places=15)
        self.assertAlmostEqual(result["geometric_thickness_um"], independent_um, places=14)
        self.assertAlmostEqual(independent_mass, 2.7e-4, places=14)
        self.assertAlmostEqual(independent_um, 0.1, places=14)
        self.assertAlmostEqual(result["qcm_equivalent_thickness_um"], 9e-4 / 2700 * 1e6, places=14)
        self.assertEqual(result["design_thickness_um"], 0.25)
        self.assertNotAlmostEqual(result["qcm_equivalent_thickness_um"], result["geometric_thickness_um"])

    def test_bulk_alpha_to_dimensionless_k_units_and_scope_guard(self):
        alpha_per_m = 25000.0
        wavelength_um = np.array([0.55])
        expected = alpha_per_m * wavelength_um * 1e-6 / (4 * np.pi)
        actual = alpha_to_k(alpha_per_m, wavelength_um, "bulk", "bulk")
        np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-16)
        with self.assertRaises(Blocked):
            alpha_to_k(alpha_per_m, wavelength_um, "bulk", "film")

    def test_n_plus_ik_sign_and_hand_fresnel_check(self):
        record = one_wavelength_record()
        wavelength = np.array([0.55])
        nfilm = film_index(record, wavelength)
        nsub = np.array([record["substrate"]["n"]])
        thickness_um = film_inventory(record)["geometric_thickness_um"]
        k0 = 2 * np.pi / wavelength[0]
        propagation = np.exp(1j * k0 * nfilm[0] * thickness_um)
        self.assertGreater(nfilm[0].imag, 0)
        self.assertAlmostEqual(abs(propagation), np.exp(-k0 * nfilm[0].imag * thickness_um), places=14)
        self.assertLess(abs(propagation), 1.0)  # exp(-i wt), passive n+ik decays

        r01 = (1 - nfilm[0]) / (1 + nfilm[0])
        r12 = (nfilm[0] - nsub[0]) / (nfilm[0] + nsub[0])
        r_hand = (r01 + r12 * propagation**2) / (1 + r01 * r12 * propagation**2)
        expected_R = abs(r_hand) ** 2
        local = local_scattering(wavelength, [1, nfilm, nsub], [thickness_um], 0, "s")
        np.testing.assert_allclose(local["R"], [expected_R], rtol=2e-13, atol=2e-14)

    def test_finite_incoherent_substrate_all_orders_against_hand_sum(self):
        record = one_wavelength_record()
        record["measurement"].update(angle_deg=35, polarization="p")
        record["substrate"].update(bulk_alpha_per_m=220.0, thickness_m=1e-3)
        wavelength = np.array([0.55])
        thickness_um = film_inventory(record)["geometric_thickness_um"]
        nfilm = film_index(record, wavelength)
        nsub = np.full_like(wavelength, record["substrate"]["n"])
        angle_sub_deg = np.rad2deg(np.arcsin(np.sin(np.deg2rad(35)) / nsub[0]))

        front = local_scattering(wavelength, [1, nfilm, nsub], [thickness_um], 35, "p")
        reverse = local_scattering(wavelength, [nsub, nfilm, 1], [thickness_um], angle_sub_deg, "p")
        rear = local_scattering(wavelength, [nsub, 1], [], angle_sub_deg, "p")
        one_way = np.exp(
            -record["substrate"]["bulk_alpha_per_m"]
            * record["substrate"]["thickness_m"]
            / np.cos(np.deg2rad(angle_sub_deg))
        )
        den = 1 - reverse["R"][0] * rear["R"][0] * one_way**2
        expected_R = front["R"][0] + front["T"][0] * reverse["T"][0] * rear["R"][0] * one_way**2 / den
        expected_T = front["T"][0] * rear["T"][0] * one_way / den
        expected_Afilm = front["A"][0] + front["T"][0] * rear["R"][0] * one_way**2 * reverse["A"][0] / den
        expected_Abulk = front["T"][0] * (1 - one_way) * (1 + rear["R"][0] * one_way) / den

        out = evaluate(record)
        self.assertEqual(out["status"], "conditional_calculation")
        obs = out["observables"]
        for key, expected in (
            ("R_total", expected_R),
            ("T_total", expected_T),
            ("A_film", expected_Afilm),
            ("A_bulk", expected_Abulk),
        ):
            self.assertAlmostEqual(obs[key][0], expected, places=12, msg=key)
        self.assertAlmostEqual(obs["A_absorption"][0], expected_Afilm + expected_Abulk, places=12)
        self.assertAlmostEqual(obs["R_total"][0] + obs["T_total"][0] + obs["A_absorption"][0], 1.0, places=12)

    def test_specular_deficit_includes_scatter_but_absorption_does_not(self):
        record = one_wavelength_record()
        record["measurement"]["scatter"].update(fraction_of_R=0.2, fraction_of_T=0.35)
        record["measurement"]["detector"].update(diffuse_R_collection=0.25, diffuse_T_collection=0.5)
        obs = evaluate(record)["observables"]
        expected_scatter = 0.2 * obs["R_total"][0] + 0.35 * obs["T_total"][0]
        self.assertAlmostEqual(obs["S_out_of_specular"][0], expected_scatter, places=14)
        self.assertAlmostEqual(
            obs["L_specular"][0], obs["A_absorption"][0] + expected_scatter, places=14
        )
        self.assertAlmostEqual(
            obs["R_detected"][0], obs["R_specular"][0] + 0.25 * 0.2 * obs["R_total"][0], places=14
        )
        self.assertAlmostEqual(
            obs["T_detected"][0], obs["T_specular"][0] + 0.5 * 0.35 * obs["T_total"][0], places=14
        )

    def test_actual_unmeasured_record_blocks_instead_of_returning_optics(self):
        actual = load_json(ROOT / "examples" / "actual_unmeasured.json")
        result = evaluate(actual)
        self.assertEqual(result["status"], "blocked_unknown_or_inapplicable")
        self.assertIn("reason", result)
        self.assertNotIn("observables", result)
        self.assertFalse(result["production_qualified"])

    def test_batch_default_is_plan_only_without_device_or_gpu_claim(self):
        plan = load_json(ROOT / "data" / "batch_plan.json")
        out = run_batch(plan, synthetic_record())
        self.assertEqual(out["status"], "plan_only")
        self.assertNotIn("runs", out)
        self.assertEqual(out["automatic_GPU"], False)
        self.assertEqual(out["device_validation"], "not_run")
        self.assertEqual(out["physical_experiment"], "not_run")


if __name__ == "__main__":
    unittest.main()
