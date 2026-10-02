"""Narrow independent dimension/inventory regressions; no response qualification.

The final three assertions deliberately describe the safe contract, not the
pre-review implementation. A red result is an unresolved review finding.
"""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "models"))
from build_examples import all_examples, base, q
from contract import E_CHARGE, N_A, calculate, validate


class IndependentDimensionTests(unittest.TestCase):
    def test_01_atom_formula_and_all_six_output_units(self):
        out = calculate(base())
        expected_units = {
            "N_net": "atoms/m2", "h_increment": "m",
            "D": "charged_particles/m2", "U": "J/m2",
            "R": "charged_particles/net_atom", "epsilon": "eV/net_atom",
        }
        for key, unit in expected_units.items():
            self.assertEqual(out[key]["unit"], unit)
            lo, hi = out[key]["interval"]
            self.assertLessEqual(lo, out[key]["value"])
            self.assertGreaterEqual(hi, out[key]["value"])
        self.assertAlmostEqual(out["N_net"]["value"] / 2e19, 1)
        self.assertAlmostEqual(out["N_formula_net"]["value"] * 3 / 2e19, 1)
        atom_density = 2150 * N_A * 3 / .060083
        self.assertAlmostEqual(out["n_atom"]["value"] / atom_density, 1)
        self.assertAlmostEqual(out["h_increment"]["value"] * atom_density / 2e19, 1)
        self.assertAlmostEqual(out["D"]["value"] / 6e18, 1)
        self.assertAlmostEqual(out["U"]["value"] / (8e20 * E_CHARGE), 1)
        self.assertAlmostEqual(out["R"]["value"], .3)
        self.assertAlmostEqual(out["epsilon"]["value"], 40)

    def test_02_charged_particles_not_charge_or_nuclei_and_neutral_energy(self):
        record = base()
        before = calculate(record)
        beam = record["bins"][0]["beams"][0]
        beam.update(charge_number=2, nuclei_per_particle=2, species="O2++")
        neutral = copy.deepcopy(beam)
        neutral.update(charge_number=0, species="O2")
        record["bins"][0]["beams"].append(neutral)
        record["bins"][0]["neutral_inventory"] = "included"
        after = calculate(record)
        self.assertEqual(after["D"]["value"], before["D"]["value"])
        self.assertAlmostEqual(after["U"]["value"] / (1e21 * E_CHARGE), 1)
        self.assertAlmostEqual(after["epsilon"]["value"], 50)

    def test_03_zero_negative_crossing_and_ill_conditioned_denominators(self):
        examples = all_examples()
        cases = {"zero": "zero_or_crossing_zero", "erosion": "net_erosion",
                 "cross_zero": "zero_or_crossing_zero", "ill_conditioned": "ill_conditioned"}
        for name, condition in cases.items():
            with self.subTest(name=name):
                out = calculate(examples[name])
                self.assertEqual(out["ratio_conditioning"], condition)
                for key in ("R", "epsilon"):
                    self.assertEqual(out[key]["status"], "blocked")
                    self.assertIsNone(out[key]["value"])
                    self.assertEqual("diagnostic_interval" in out[key], name == "ill_conditioned")
        self.assertLess(calculate(examples["erosion"])["h_increment"]["value"], 0)

    def test_04_bulk_reference_and_substrate_density_cannot_supply_film_density(self):
        record = base()
        expected = calculate(record)["h_increment"]["value"]
        record["substrate"]["density"] = q(9999, "kg/m3", 0)
        self.assertEqual(calculate(record)["h_increment"]["value"], expected)
        record["film"]["density_basis"] = "bulk_substrate"
        self.assertEqual(calculate(record)["h_increment"]["status"], "blocked")
        record = base()
        record["film"]["density"]["status"] = "literature_reference"
        self.assertEqual(calculate(record)["h_increment"]["status"], "blocked")

    def test_05_final_positive_balance_cannot_hide_prior_exhaustion(self):
        record = base()
        for element, factor in (("Si", 1), ("O", 2)):
            record["initial_inventory_atoms_m2"][element] = q(1e18 * factor, "atoms/m2", 0)
            record["bins"][0]["net_element_flux"][element] = q(-2e17 * factor, "atoms/m2/s", 0)
            record["bins"][1]["net_element_flux"][element] = q(1e18 * factor, "atoms/m2/s", 0)
        record["bins"][0]["history_class"] = "erosion"
        out = calculate(record)
        for key in ("N_net", "h_increment", "R", "epsilon"):
            self.assertEqual(out[key]["status"], "blocked")

    def test_06_negative_initial_inventory_bound_is_rejected(self):
        record = base()
        record["initial_inventory_atoms_m2"]["Si"]["interval"][0] = -1e10
        self.assertTrue(validate(record), "Initial inventory support includes physically negative inventory")

    def test_07_true_small_inventory_deficit_is_not_a_roundoff_allowance(self):
        record = base()
        for element, factor in (("Si", 1), ("O", 2)):
            initial = q(1e20 * factor, "atoms/m2", 0)
            initial["interval"] = [1e18 * factor, 1e20 * factor]
            record["initial_inventory_atoms_m2"][element] = initial
            record["bins"][0]["net_element_flux"][element] = q(-(1e17 + 1e6) * factor, "atoms/m2/s", 0)
            record["bins"][1]["net_element_flux"][element] = q(1e18 * factor, "atoms/m2/s", 0)
        record["bins"][0]["history_class"] = "erosion"
        self.assertEqual(validate(record), [])
        # Lower-end physical history is -1e7 Si atoms/m2 after the first bin.
        self.assertEqual(calculate(record)["N_net"]["status"], "blocked")

    def test_08_molar_mass_interval_is_strictly_positive(self):
        record = base()
        record["film"]["element_molar_mass_kg_mol"]["Si"]["interval"] = [-.1, .1]
        self.assertTrue(validate(record), "Nonpositive molar-mass support must be rejected before h arithmetic")


if __name__ == "__main__":
    unittest.main()
