"""Narrow independent dimensional/sign/conservation checks for qcm_flux.py."""
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "models"))
from qcm_flux import (  # noqa: E402
    MOLAR_MASS,
    N_A,
    QUARTZ_N,
    QUARTZ_RHO,
    design_matrix,
    frequency_from_mass,
    mass_areal,
    mixture_from_mass,
    point_kernel,
    rank_report,
    rate_from_frequency,
    species_elements,
    transfer_qcm_to_workpiece,
)


class AcousticDimensions(unittest.TestCase):
    def test_sauerbrey_si_units_and_sign(self):
        self.assertEqual(QUARTZ_N, 1661.0)  # Hz m, not Hz cm
        self.assertEqual(QUARTZ_RHO, 2649.0)  # kg m^-3
        f0, f = 6.0e6, 5_999_000.0
        expected_kg_m2 = QUARTZ_RHO * QUARTZ_N * (f0 - f) / f0**2
        got = float(mass_areal(f, f0, method="sauerbrey"))
        self.assertGreater(got, 0.0)  # added mass lowers frequency
        self.assertAlmostEqual(got, expected_kg_m2, places=15)

    def test_zmatch_si_expression_and_finite_branch(self):
        f0, f, z = 6.0e6, 5.4e6, 1.08
        x = np.pi * (f0 - f) / f0
        expected_kg_m2 = QUARTZ_RHO * QUARTZ_N / (np.pi * f * z) * np.arctan(z * np.tan(x))
        self.assertAlmostEqual(float(mass_areal(f, f0, z)), expected_kg_m2, places=14)
        self.assertGreater(float(mass_areal(f, f0, z)), 0.0)
        with self.assertRaises(ValueError):
            mass_areal(f0 / 2, f0, z)
        with self.assertRaises(ValueError):
            mass_areal(f0 * 1.001, f0, z)

    def test_nonempty_initial_load_does_not_bias_rate_slope(self):
        f0, z, m0, rate = 6.0e6, 1.08, 1.0e-4, 2.0e-7
        t = np.arange(7.0)
        frequencies = frequency_from_mass(m0 + rate * t, f0, z)
        self.assertGreater(float(mass_areal(frequencies[0], f0, z)), 0.0)
        fit = rate_from_frequency(t, frequencies, f0, drift_hz=np.zeros_like(t), z_ratio=z)
        self.assertAlmostEqual(fit["slope_kg_m2_s"], rate, delta=abs(rate) * 1e-8)


class TransferAndChemistry(unittest.TestCase):
    def test_kernel_is_inverse_square_and_includes_receiver_projection(self):
        r = 2.0
        axial = point_kernel([[0.0, 0.0, r]], [[0.0, 0.0, -1.0]], n=0.0)
        tilted = point_kernel([[r / np.sqrt(2), 0.0, r / np.sqrt(2)]],
                              [[-1.0, 0.0, 0.0]], n=0.0)
        self.assertAlmostEqual(float(axial[0]), 1.0 / (2.0 * np.pi * r**2), places=14)
        # Same r and isotropic emission; incidence cosine is 1/sqrt(2).
        self.assertAlmostEqual(float(tilted[0] / axial[0]), 1.0 / np.sqrt(2.0), places=14)
        self.assertAlmostEqual(float(axial[0]), 1.0 / (2.0 * np.pi * r**2), places=14)  # m^-2

    def test_qcm_to_workpiece_projection_conserves_source_rate(self):
        result = transfer_qcm_to_workpiece(2.0, capture_q=0.5, k_q=4.0, k_w=2.0,
                                           reactive_retained=0.1, outgoing=0.2)
        q_incident = (2.0 - 0.1 + 0.2) / 0.5
        self.assertAlmostEqual(result["source_rate_kg_s"], q_incident / 4.0)
        self.assertAlmostEqual(result["incident_workpiece_kg_m2_s"], q_incident * 2.0 / 4.0)

    def test_al_al2_o2_nuclei_and_mass_balance(self):
        stoich = {"Al": {"Al": 1}, "Al2": {"Al": 2}, "O2": {"O": 2}}
        particles = {"Al": 3.0, "Al2": 4.0, "O2": 5.0}
        got = species_elements(particles, stoich)
        expected_al, expected_o = 3.0 + 2.0 * 4.0, 2.0 * 5.0
        self.assertEqual(got["element_flux_atoms_m2_s"], {"Al": expected_al, "O": expected_o})
        expected_mass = (expected_al * MOLAR_MASS["Al"] + expected_o * MOLAR_MASS["O"]) / N_A
        self.assertAlmostEqual(got["mass_flux_kg_m2_s"], expected_mass, places=38)
        mixed = mixture_from_mass(1.0e-4, {"Al": 0.2, "Al2": 0.3, "O2": 0.5}, stoich)
        self.assertAlmostEqual(mixed["mass_flux_kg_m2_s"], 1.0e-4, places=16)


class IdentificationRank(unittest.TestCase):
    def test_eta_and_q_need_independent_source_row(self):
        xyz = np.array([[0, 0, 0.5], [0.1, 0, 0.5], [0, 0.2, 0.5],
                        [0.3, 0, 0.5], [0, 0.4, 0.5], [0.2, 0.3, 0.5]], dtype=float)
        normals = np.tile([0.0, 0.0, -1.0], (len(xyz), 1))
        without_independent_q = design_matrix(xyz, normals, 2.4, 0.25, fit_capture=True)
        self.assertTrue(np.array_equal(without_independent_q[:, 0], without_independent_q[:, -1]))
        self.assertFalse(rank_report(without_independent_q)["identifiable"])

        with_independent_q = design_matrix(xyz, normals, 2.4, 0.25,
                                           fit_capture=True, independent_source_count=1)
        self.assertTrue(np.array_equal(with_independent_q[-1], [1.0, 0.0, 0.0, 0.0]))
        self.assertTrue(rank_report(with_independent_q)["identifiable"])


if __name__ == "__main__":
    unittest.main()
