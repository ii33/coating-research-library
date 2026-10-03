"""Numerical verification only; these tests do not validate real ITO samples."""
import cmath
import math
import random
import unittest

from model import (Q, ME, EPS0, Lorentz, DrudeLorentz, EmpiricalEpsilon,
                   cm3_to_m3, cm2_vs_to_m2_vs, nm_to_m, ohm_cm_to_ohm_m,
                   ev_to_rad_s, passive_nk, dc_conductivity, sheet_resistance,
                   coherent_rt, incoherent_substrate_rt, weighted_mean)


def material():
    return DrudeLorentz(cm3_to_m3(3e20), cm2_vs_to_m2_vs(35), 0.35, 3.9)


def direct_matrix_rt(wl, layers, n0, ns):
    """Independent characteristic-matrix reference; safe for modest thickness.

    Derived from E,H boundary continuity, NOT using the tested recursion.
    """
    a, b, c, d = 1 + 0j, 0j, 0j, 1 + 0j
    for n, thickness in layers:
        delta = 2 * math.pi * n * thickness / wl
        co, si = cmath.cos(delta), cmath.sin(delta)
        aa, bb, cc, dd = co, -1j * si / n, -1j * n * si, co
        a, b, c, d = a * aa + b * cc, a * bb + b * dd, c * aa + d * cc, c * bb + d * dd
    denominator = n0 * a + n0 * ns * b + c + ns * d
    r = (n0 * a + n0 * ns * b - c - ns * d) / denominator
    t = 2 * n0 / denominator
    return abs(r)**2, ns / n0 * abs(t)**2


class UnitsAndDC(unittest.TestCase):
    def test_unit_conversions(self):
        self.assertEqual(cm3_to_m3(1), 1e6)
        self.assertEqual(cm2_vs_to_m2_vs(1), 1e-4)
        self.assertAlmostEqual(nm_to_m(100), 1e-7, places=20)
        self.assertEqual(ohm_cm_to_ohm_m(1), 0.01)
        self.assertAlmostEqual(ev_to_rad_s(1) / 1.519267448e15, 1, places=8)

    def test_drude_dc_limit(self):
        m = material()
        expected = Q * m.carrier_density_m3 * m.mobility_opt_m2_vs
        self.assertAlmostEqual(m.drude_conductivity(0).real / expected, 1, places=13)
        self.assertEqual(m.drude_conductivity(0).imag, 0)
        self.assertAlmostEqual(m.drude_conductivity(m.damping_rad_s * 1e-8).real / expected, 1, places=13)

    def test_layered_parallel_conductance(self):
        self.assertAlmostEqual(sheet_resistance([(1e5, 20e-9), (2e5, 80e-9)]), 1 / 0.018)
        self.assertAlmostEqual(sheet_resistance([(1e5, 100e-9)]), 100)
        self.assertEqual(sheet_resistance([(0, 100e-9)]), math.inf)
        self.assertEqual(sheet_resistance([]), math.inf)

    def test_uniform_rho_identity_and_dc_opt_separation(self):
        sigma = dc_conductivity(cm3_to_m3(3e20), cm2_vs_to_m2_vs(25))
        rs = sheet_resistance([(sigma, 100e-9)])
        self.assertAlmostEqual(rs * 100e-9, 1 / sigma, places=16)
        self.assertNotEqual(sigma, material().drude_conductivity(0).real)


class OpticalMaterial(unittest.TestCase):
    def test_passive_drude_lorentz(self):
        m = DrudeLorentz(cm3_to_m3(3e20), 0.0035, 0.35, 3.9,
                        (Lorentz(0.3, ev_to_rad_s(4), ev_to_rad_s(0.4)),))
        for nm in range(400, 2501, 10):
            eps = m.epsilon(nm_to_m(nm))
            nk = m.nk(nm_to_m(nm))
            self.assertGreater(eps.imag, 0)
            self.assertGreater(nk.imag, 0)
            self.assertLess(abs(nk * nk - eps), 1e-12)
            self.assertGreaterEqual(m.drude_conductivity(ev_to_rad_s(1)).real, 0)

    def test_exact_parameter_nonidentifiability(self):
        a = material()
        factor = 1.4
        b = DrudeLorentz(a.carrier_density_m3 * factor,
                        a.mobility_opt_m2_vs / factor, a.effective_mass_me * factor,
                        a.epsilon_inf)
        for wl in (500e-9, 1000e-9, 2000e-9):
            self.assertLess(abs(a.epsilon(wl) - b.epsilon(wl)), 1e-12)

    def test_empirical_model_interpolation(self):
        data = EmpiricalEpsilon(((400e-9, 4 + 0.2j), (600e-9, 3 + 0.4j)))
        self.assertLess(abs(data.epsilon(500e-9) - (3.5 + 0.3j)), 1e-12)
        self.assertEqual(data.epsilon(600e-9), 3 + 0.4j)
        with self.assertRaises(ValueError):
            data.epsilon(700e-9)

    def test_invalid_and_outside_domain(self):
        for bad in (-1, math.nan, math.inf):
            with self.assertRaises(ValueError):
                cm3_to_m3(bad)
        with self.assertRaises(ValueError):
            passive_nk(3 - 0.1j)
        with self.assertRaises(ValueError):
            material().epsilon(300e-9)
        with self.assertRaises(ValueError):
            DrudeLorentz(1e26, 0, 0.35, 3.9)
        with self.assertRaises(ValueError):
            Lorentz(-0.1, 1e15, 1e14)


class ThinFilmOptics(unittest.TestCase):
    def test_no_film(self):
        same = coherent_rt(550e-9, [], 1, 1)
        self.assertEqual(same.R, 0)
        self.assertEqual(same.T, 1)
        glass = coherent_rt(550e-9, [], 1, 1.5)
        self.assertAlmostEqual(glass.R, 0.04, places=14)
        self.assertAlmostEqual(glass.T, 0.96, places=14)
        self.assertAlmostEqual(glass.A, 0, places=14)

    def test_zero_thickness_film(self):
        out = coherent_rt(550e-9, [(2 + 0.5j, 0)], 1, 1.5)
        self.assertAlmostEqual(out.R, 0.04, places=14)
        self.assertAlmostEqual(out.T, 0.96, places=14)

    def test_quarter_wave_antireflection(self):
        wl, ns = 550e-9, 1.5
        nf = math.sqrt(ns)
        out = coherent_rt(wl, [(nf, wl / (4 * nf))], 1, ns)
        self.assertLess(out.R, 1e-25)
        self.assertAlmostEqual(out.T, 1, places=14)

    def test_matches_independent_matrix(self):
        layers = [(2.0 + 0.05j, 80e-9), (1.8 + 0.4j, 120e-9)]
        for wl in (450e-9, 800e-9, 1550e-9):
            out = coherent_rt(wl, layers, 1, 1.5)
            R, T = direct_matrix_rt(wl, layers, 1, 1.5)
            self.assertAlmostEqual(out.R, R, places=13)
            self.assertAlmostEqual(out.T, T, places=13)

    def test_energy_conservation_and_passivity(self):
        rng = random.Random(20261003)
        for lossy in (False, True):
            for _ in range(100):
                layers = [(complex(rng.uniform(1.2, 3), rng.uniform(0, 0.5) if lossy else 0),
                           rng.uniform(10e-9, 500e-9)) for _ in range(4)]
                out = coherent_rt(rng.uniform(400e-9, 2500e-9), layers)
                self.assertGreaterEqual(out.A, -1e-12)
                self.assertGreaterEqual(out.R, 0)
                self.assertGreaterEqual(out.T, 0)
                if not lossy:
                    self.assertAlmostEqual(out.R + out.T, 1, places=12)

    def test_opaque_layer_stability(self):
        out = coherent_rt(500e-9, [(2 + 10j, 1.0)], 1, 1.5)
        self.assertTrue(math.isfinite(out.R))
        self.assertEqual(out.T, 0)
        self.assertGreater(out.A, 0)

    def test_reciprocity_transmittance(self):
        layers = [(2 + 0.1j, 100e-9), (1.7 + 0.2j, 60e-9)]
        forward = coherent_rt(550e-9, layers, 1, 1.5)
        backward = coherent_rt(550e-9, list(reversed(layers)), 1.5, 1)
        self.assertAlmostEqual(forward.T, backward.T, places=13)

    def test_bare_incoherent_glass(self):
        out = incoherent_substrate_rt(550e-9, [], 1.5)
        self.assertAlmostEqual(out.T, 0.96 / 1.04, places=13)
        self.assertAlmostEqual(out.R + out.T, 1, places=13)

    def test_incoherent_matches_uniform_phase_average(self):
        wl, ns = 550e-9, 1.5
        layers = [(2 + 0.1j, 100e-9), (1.8 + 0.2j, 60e-9)]
        inc = incoherent_substrate_rt(wl, layers, ns)
        samples = [coherent_rt(wl, layers + [(ns, (5 + i / 500) * wl / (2 * ns))], 1, 1)
                   for i in range(500)]
        self.assertAlmostEqual(inc.R, math.fsum(x.R for x in samples) / 500, places=12)
        self.assertAlmostEqual(inc.T, math.fsum(x.T for x in samples) / 500, places=12)
        self.assertGreater(inc.A, 0)

    def test_reject_unimplemented_absorbing_boundaries(self):
        with self.assertRaises(ValueError):
            coherent_rt(550e-9, [], 1 + 0.1j, 1.5)
        with self.assertRaises(ValueError):
            incoherent_substrate_rt(550e-9, [], 1.5 + 0.1j)

    def test_weighted_mean(self):
        self.assertAlmostEqual(weighted_mean([1, 2, 3], [0.6, 0.8, 1.0], [1, 1, 1]), 0.8)
        with self.assertRaises(ValueError):
            weighted_mean([1, 2], [0.6, 0.8], [0, 0])


if __name__ == '__main__':
    unittest.main(verbosity=2)
