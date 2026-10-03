import unittest,copy,json
import numpy as np
from jsonschema import ValidationError
from process_optics import *
from inference import sensitivity,propagate,fit_synthetic,covariance_check
from batch_driver import run as batch_run
from vendor.optics_kernel import scattering,recursive
class ContractTests(unittest.TestCase):
 def setUp(self): self.r=json.loads((ROOT/'examples/synthetic_dielectric.json').read_text())
 def blocked(self,record):self.assertEqual(evaluate(record)['status'],'blocked_unknown_or_inapplicable')
 def test_all_fixtures_schema(self):
  for p in (ROOT/'examples').glob('*.json'):validate(json.loads(p.read_text()))
 def test_unknown_field_rejected(self):
  self.r['measurement']['wavelenght_um']=[.55]
  with self.assertRaises(ValidationError):validate(self.r)
 def test_missing_field_rejected(self):
  del self.r['measurement']['backside']
  with self.assertRaises(ValidationError):validate(self.r)
 def test_negative_k_rejected(self):
  self.r['optical_model']['parameters']['k']=-.1
  with self.assertRaises(ValidationError):evaluate(self.r)
 def test_inventory_to_geometry(self):self.assertAlmostEqual(film_inventory(self.r)['geometric_thickness_um'],.1,places=14)
 def test_thickness_types_separate(self):
  t=film_inventory(self.r);self.assertAlmostEqual(t['qcm_equivalent_thickness_um'],1/3);self.assertEqual(t['design_thickness_um'],.25);self.assertAlmostEqual(t['geometric_thickness_um'],.1)
 def test_mass_unit_kg(self):self.assertAlmostEqual(film_inventory(self.r)['areal_mass_kg_m2'],.00027)
 def test_arrival_is_not_net(self):
  b=self.r['process']['bins'][0];b['net_atoms_m2_s']=None;self.blocked(self.r)
 def test_retention_unknown(self):
  r=json.loads((ROOT/'examples/al_reference_conditional.json').read_text());r['process']['bins'][0]['balance']['Al']['retained_fraction']=None;self.blocked(r)
 def test_inventory_depletion(self):
  self.r['process']['bins'][0]['net_atoms_m2_s']['Al']=-1;self.blocked(self.r)
 def test_density_null(self):self.r['film_state']['density_kg_m3']=None;self.blocked(self.r)
 def test_bulk_density_blocked(self):self.r['film_state']['density_basis']='bulk';self.blocked(self.r)
 def test_qcm_density_blocked(self):self.r['film_state']['density_basis']='qcm_setting';self.blocked(self.r)
 def test_composition_incomplete(self):self.r['film_state']['composition_complete']=False;self.blocked(self.r)
 def test_composition_unknown(self):self.r['film_state']['stoichiometry']=None;self.blocked(self.r)
 def test_changing_density_blocked(self):self.r['film_state']['constant_composition_density']=False;self.blocked(self.r)
 def test_state_unknown(self):self.r['film_state']['state_id']=None;self.blocked(self.r)
 def test_state_mismatch(self):self.r['film_state']['state_id']='different';self.blocked(self.r)
 def test_sample_mismatch(self):self.r['optical_model']['sample_id']='wrong';self.blocked(self.r)
 def test_temperature_unknown(self):self.r['film_state']['measurement_temperature_K']=None;self.blocked(self.r)
 def test_temperature_outside(self):self.r['film_state']['measurement_temperature_K']=400;self.blocked(self.r)
 def test_bulk_nk_rejected(self):self.r['optical_model']['source_class']='public_bulk';self.blocked(self.r)
 def test_table_extrapolation_blocked(self):self.r['measurement']['wavelength_um']=[1.1];self.blocked(self.r)
 def test_bandpass_domain_checked(self):self.r['measurement']['wavelength_um']=[.4];self.r['measurement']['bandpass_nodes']=[{'offset_um':-.001,'weight':1}];self.blocked(self.r)
 def test_weights_checked(self):
  self.r['measurement']['bandpass_nodes'][0]['weight']=.8
  with self.assertRaises(ValueError):evaluate(self.r)
 def test_no_bulk_to_film_alpha(self):
  with self.assertRaises(Blocked):alpha_to_k(1,[.55],'bulk','film')
 def test_alpha_units(self):self.assertAlmostEqual(alpha_to_k(1,[1],'bulk','bulk')[0],1e-6/(4*np.pi))
 def test_unknown_scatter_blocked(self):self.r['measurement']['scatter']['basis']='unknown';self.blocked(self.r)
 def test_unknown_bulk_alpha_blocked(self):self.r['substrate']['bulk_alpha_per_m']=None;self.blocked(self.r)
 def test_semi_infinite_no_bulk_alpha_needed(self):
  self.r['measurement']['backside']='semi_infinite';self.r['substrate']['bulk_alpha_per_m']=None;self.assertEqual(evaluate(self.r)['status'],'conditional_calculation')
 def test_process_temperature_required(self):self.r['process']['bins'][0]['temperature_K']=None;self.blocked(self.r)
class OpticalTests(unittest.TestCase):
 def setUp(self):self.r=json.loads((ROOT/'examples/synthetic_dielectric.json').read_text())
 def test_energy_balance(self):
  o=evaluate(self.r)['observables'];np.testing.assert_allclose(np.array(o['R_total'])+o['T_total']+o['A_absorption'],1,atol=1e-12)
 def test_bulk_absorption_partition(self):
  self.r['substrate']['bulk_alpha_per_m']=200;o=evaluate(self.r)['observables'];np.testing.assert_allclose(np.array(o['A_film'])+o['A_bulk'],o['A_absorption'],atol=1e-12);self.assertGreater(o['A_bulk'][0],0)
 def test_scatter_deficit_not_absorption(self):
  self.r['measurement']['scatter'].update(fraction_of_R=.1,fraction_of_T=.2);o=evaluate(self.r)['observables'];np.testing.assert_allclose(np.array(o['L_specular']),np.array(o['A_absorption'])+o['S_out_of_specular'],atol=1e-12)
 def test_total_detector(self):
  self.r['measurement']['scatter'].update(fraction_of_R=.1,fraction_of_T=.2);self.r['measurement']['detector'].update(diffuse_R_collection=1,diffuse_T_collection=1);o=evaluate(self.r)['observables'];np.testing.assert_allclose(o['R_detected'],o['R_total']);np.testing.assert_allclose(o['T_detected'],o['T_total'])
 def test_polarization_average(self):
  self.r['measurement']['angle_deg']=50;self.r['measurement']['polarization']='s';s=evaluate(self.r)['observables']['R_total'];self.r['measurement']['polarization']='p';p=evaluate(self.r)['observables']['R_total'];self.r['measurement']['polarization']='unpolarized';u=evaluate(self.r)['observables']['R_total'];np.testing.assert_allclose(u,(np.array(s)+p)/2,atol=1e-14)
 def test_malitson_anchor(self):self.assertAlmostEqual(silica_index(np.array([.5876]))[0],1.458462342,places=8)
 def test_zero_film_bare_substrate(self):
  self.r=set_parameter(self.r,'thickness_scale',0);self.r['measurement']['backside']='semi_infinite';o=evaluate(self.r)['observables'];np.testing.assert_allclose(o['R_total'],((1-1.52)/(1+1.52))**2,atol=1e-14)
 def test_opaque_passive_stability(self):
  o=scattering([.55],[1,1+20j,1.5],[100]);self.assertTrue(np.isfinite(o['R'][0]));self.assertGreaterEqual(o['A'][0],0)
 def test_recursive_kernel_agreement_tiny(self):
  s=scattering([.5,.6],[1,1.8+.02j,1.52],[.1],45,'p');r=recursive([.5,.6],[1,1.8+.02j,1.52],[.1],45,'p');np.testing.assert_allclose(s['R'],r['R'],atol=1e-14)
 def test_literal_optical_thickness(self):
  o=evaluate(self.r);n=film_index(self.r,np.array(o['wavelength_um']));np.testing.assert_allclose(o['optical_thickness_n_d_um'],n.real*.1)
class DriverTests(unittest.TestCase):
 def setUp(self):self.r=json.loads((ROOT/'examples/synthetic_dielectric.json').read_text());self.p=json.loads((ROOT/'data/batch_plan.json').read_text())
 def test_default_plan_only(self):self.assertEqual(batch_run(self.p,self.r)['status'],'plan_only')
 def test_tiny_execute(self):
  self.p.update(bands_um=[[.5,.6,2]],angles_deg=[0],polarizations=['s'],monte_carlo_samples=0);o=batch_run(self.p,self.r,True);self.assertEqual(len(o['runs']),1);self.assertEqual(o['runs'][0]['result']['status'],'conditional_calculation')
 def test_tiny_uncertainty_two_draws(self):
  p=[{'name':'thickness_scale','nominal':1,'step':.001}];o=propagate(self.r,p,['R_detected'],[[.0001]],samples=2);self.assertEqual(o['monte_carlo']['valid'],2)
 def test_invalid_monte_carlo_draws_reported(self):
  p=[{'name':'k','nominal':.01,'step':.0001}];o=propagate(self.r,p,['R_detected'],[[1.0]],samples=2,seed=31);self.assertEqual(o['monte_carlo']['status'],'completed_with_domain_failures');self.assertEqual(o['monte_carlo']['requested'],2);self.assertGreater(len(o['monte_carlo']['failures']),0)
 def test_invalid_covariance_rejected(self):
  with self.assertRaises(ValueError):covariance_check([[1,2],[2,1]],2)
 def test_rank_R_only(self):
  self.r['measurement']['wavelength_um']=[.55];p=self.p['parameters'];o=sensitivity(self.r,p,['R_detected']);self.assertEqual(o['rank'],1);self.assertEqual(o['nullity_at_least'],3)
 def test_actual_fit_refused(self):
  self.r['evidence_kind']='unmeasured'
  with self.assertRaises(Blocked):fit_synthetic(self.r,['R_detected'],[.1],[.001],['A'],[1.8],[1],[3])
if __name__=='__main__':unittest.main()
