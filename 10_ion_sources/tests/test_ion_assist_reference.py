import unittest, math, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'models'))
from ion_assist_reference import *

class Physics(unittest.TestCase):
 def test_single_charge(self):
  b=beam_moments(1,[Species('Ar+',1,1,100)])
  self.assertAlmostEqual(b['charged_particle_flux_m2_s']*E_CHARGE,1)
  self.assertAlmostEqual(b['incident_kinetic_power_W_m2'],100)
 def test_mixed_charge(self):
  b=beam_moments(1,[Species('Ar+',.8,1,100),Species('Ar2+',.2,2,200)])
  self.assertAlmostEqual(b['mean_charge_number'],1.2)
  self.assertAlmostEqual(b['incident_kinetic_power_W_m2'],100)
  self.assertTrue(math.isclose(b['charged_particle_flux_m2_s'],1/(1.2*E_CHARGE),rel_tol=1e-14))
 def test_molecular_count(self):
  b=beam_moments(1,[Species('O2+',1,1,100,2)])
  self.assertAlmostEqual(b['charged_nuclei_flux_m2_s']/b['charged_particle_flux_m2_s'],2)
 def test_no_implicit_charge_fractions(self):
  with self.assertRaises(ValueError):beam_moments(1,[Species('a',.8,1,100)])
 def test_invalid_species(self):
  for sp in [Species('a',1,0,100),Species('a',1,1,-1),Species('a',1,1,1,0),Species('a',1,1.5,1)]:
   with self.assertRaises(ValueError):beam_moments(1,[sp])
 def test_negative_fraction(self):
  with self.assertRaises(ValueError):beam_moments(1,[Species('a',-1,1,100),Species('b',2,1,100)])
 def test_empty(self):
  with self.assertRaises(ValueError):beam_moments(1,[])
 def test_zero_beam(self):self.assertEqual(beam_moments(0,[Species('Ar+',1,1,100)])['incident_kinetic_power_W_m2'],0)
 def test_nan(self):
  with self.assertRaises(ValueError):beam_moments(float('nan'),[Species('a',1,1,100)])
 def test_energy_potential(self):self.assertEqual(impact_energy_eV(2,120,20,3),203)
 def test_retarded(self):
  with self.assertRaises(ValueError):impact_energy_eV(1,0,100)
 def test_growth_units(self):
  g=atom_flux_from_net_growth(1,1,1,1)
  self.assertAlmostEqual(g['net_mass_flux_kg_m2_s'],1e-6)
  self.assertAlmostEqual(g['net_atom_flux_m2_s']/N_A,1e-3)
 def test_compound(self):
  g=atom_flux_from_net_growth(.3,2.2,60.0843,3)
  self.assertAlmostEqual(g['net_atom_flux_m2_s']/g['net_formula_flux_m2_s'],3)
 def test_unknown_density_not_zero(self):
  with self.assertRaises(ValueError):atom_flux_from_net_growth(1,0,60,3)
 def test_normalization(self):
  b=beam_moments(1,[Species('a',1,1,100)]);g=b['charged_particle_flux_m2_s']*10
  self.assertAlmostEqual(normalize_assist(b,g)['incident_eV_per_net_atom'],10)
 def test_neutrals_add_energy(self):
  b=beam_moments(1,[Species('a',1,1,100)]);g=b['charged_particle_flux_m2_s']
  self.assertAlmostEqual(normalize_assist(b,g,g,100)['incident_eV_per_net_atom'],200)
 def test_zero_growth_no_ratio(self):
  with self.assertRaises(ValueError):normalize_assist({},0)
 def test_sputter_zero(self):self.assertEqual(simple_resputter_net_flux(10,3,0),10)
 def test_sputter_erosion(self):self.assertEqual(simple_resputter_net_flux(1,3,1),-2)
 def test_cx_conservation(self):
  v=charge_exchange_split(123,0.01,300,.5,1e-19)
  self.assertAlmostEqual(v['energetic_ion_flux_m2_s']+v['fast_neutral_flux_m2_s'],123)
 def test_cx_vacuum(self):self.assertEqual(charge_exchange_split(123,0,300,1,1e-19)['fast_neutral_flux_m2_s'],0)
 def test_cx_long(self):self.assertEqual(charge_exchange_split(1,1e9,300,1,1e-19)['energetic_ion_flux_m2_s'],0)
 def test_integral_ratio(self):self.assertAlmostEqual(ratio_of_integrals([1,1],[1,9],[1,1]),.2)
 def test_not_mean_ratio(self):self.assertNotAlmostEqual(ratio_of_integrals([1,1],[1,9],[1,1]),(1+1/9)/2)
 def test_bad_integrals(self):
  with self.assertRaises(ValueError):integrate_samples([1],[1,2])
  with self.assertRaises(ValueError):integrate_samples([1],[0])
 def test_uncertainty_independent(self):self.assertAlmostEqual(relative_ratio_uncertainty(.1,.1,0),math.sqrt(.02))
 def test_uncertainty_correlation(self):
  self.assertAlmostEqual(relative_ratio_uncertainty(0,.1,.1,0,1),.2)
  self.assertAlmostEqual(relative_ratio_uncertainty(0,.1,.1,0,-1),0)
 def test_thermal_limits(self):
  self.assertEqual(lumped_temperature_rise(10,20,0,2),1)
  self.assertAlmostEqual(lumped_temperature_rise(10,20,2,1e6),5)
  self.assertEqual(lumped_temperature_rise(10,20,2,0),0)
 def test_projection(self):
  self.assertAlmostEqual(projected_flux(2,60),1)
  self.assertEqual(projected_flux(2,90),0)
  self.assertEqual(projected_flux(2,150),0)
 def test_angle_validation(self):
  with self.assertRaises(ValueError):projected_flux(1,181)

if __name__=='__main__':unittest.main(verbosity=2)
