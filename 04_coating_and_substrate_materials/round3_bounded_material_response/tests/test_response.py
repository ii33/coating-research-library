import unittest,sys,json,math
from pathlib import Path
from dataclasses import replace,asdict
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'models'))
from bounded_response import *
from run_examples import examples
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.e=examples(32)
 def test_ranking_reverses_with_angle(self):
  self.assertEqual(self.e['cases']['unit_response']['comparison']['relation'],'b_better');self.assertEqual(self.e['cases']['angular_response']['comparison']['relation'],'a_better')
 def test_uncertainty_overlap(self):self.assertEqual(self.e['cases']['angular_uncertain']['comparison']['relation'],'unresolved')
 def test_scalar_fixed_target_can_reverse(self):self.assertEqual(self.e['cases']['scalar_fixed_target']['comparison']['relation'],'a_better')
 def test_same_scale_target_preserves(self):
  for k in ['A','B']:
   x=self.e['cases']['unit_response'][k]['objective_interval'];y=self.e['cases']['scalar_correlated_target'][k]['objective_interval'];np.testing.assert_allclose(x,y,rtol=1e-13,atol=1e-15)
 def test_density_uncertainty(self):self.assertEqual(self.e['cases']['density_uncertain']['comparison']['relation'],'unresolved')
 def test_unknown(self):self.assertIsNone(self.e['cases']['unknown_retention']['A']['signed_thickness_change_m'])
 def test_real_stays_unknown(self):self.assertEqual(self.e['cases']['real_YbF3_Ge_template']['A']['status'],'unknown')
 def test_negative_not_zero(self):
  x=self.e['cases']['negative_net']['A'];self.assertLess(x['signed_thickness_change_m'][1],0);self.assertIsNone(x['objective_interval'])
 def test_cross_zero_no_reward(self):self.assertEqual(self.e['cases']['cross_zero_net']['A']['status'],'zero_or_crossing_net')
 def test_inventory(self):self.assertEqual(self.e['cases']['inventory_unresolved']['A']['status'],'inventory_unresolved')
 def test_normalization_states(self):
  for k in ['zero','negative','cross_zero','near_zero','unknown']:self.assertIsNone(self.e['denominator_examples'][k]['value'])
 def test_target_floor(self):
  with self.assertRaises(ValueError):forward(Scene(),Response(),target_m=1e-16)
 def test_invalid_bounds(self):
  for q in [[1.,0.],[-1.,1.],[False,1.],[0.,math.nan],[0.,math.inf]]:
   with self.assertRaises(ValueError):forward(Scene(),replace(Response(),sticking_s0=q))
 def test_density_basis(self):
  with self.assertRaises(ValueError):forward(Scene(),replace(Response(),density_basis='bulk_crystal'))
 def test_response_outside_domain(self):
  with self.assertRaises(ValueError):forward(Scene(),replace(Response(),energy_history_eV=(100.,1.)))
 def test_unknown_temperature_dependency(self):
  x=forward(Scene(),replace(Response(),temperature_history_K=None,temperature_c=(.1,.1)));self.assertEqual(x['status'],'unknown')
 def test_irrelevant_temperature_allowed(self):self.assertEqual(forward(Scene(),replace(Response(),temperature_history_K=None))['status'],'bounded_synthetic_response')
 def test_upstream_full_and_events_retained(self):
  x=self.e['cases']['angular_response']['A']['upstream_full_forward'];self.assertIsNotNone(x['event_gradient']);self.assertNotEqual(x['event_gradient'][4],0);self.assertFalse(x['physical_certification'])
 def test_upstream_unknown_not_zero(self):
  x=forward(replace(Scene(),shadow_boundary_uncertainty_m=1e-4),Response());self.assertEqual(x['status'],'unknown');self.assertIsNone(x['objective_interval'])
 def test_contract_mismatch_rejected(self):
  with self.assertRaises(ValueError):compare(self.e['cases']['unit_response']['A'],self.e['cases']['angular_response']['B'])
 def test_unit_response_equivalence(self):
  x=self.e['cases']['unit_response']['A'];np.testing.assert_allclose(x['retained_transfer_s_m2'],list(x['upstream_full_forward']['value_interval'].values()),rtol=1e-14)
 def test_weighted_event_finite_difference(self):
  sc=Scene();r=Response(angular_a=(.8,.8),energy_b=(.2,.2),temperature_c=(.3,.3));base=forward(sc,r,panels=16)
  for i,k in enumerate(('plate_shift_m','half_width_m')):
   eps=1e-6;a=replace(sc,**{k:getattr(sc,k)+eps});b=replace(sc,**{k:getattr(sc,k)-eps});va=point_estimate_and_gradient(a,[0.],[1.],r)[0];vb=point_estimate_and_gradient(b,[0.],[1.],r)[0]
   self.assertAlmostEqual((va-vb)/(2*eps)/base['material_design_gradient_m_per_m'][i],1.,delta=2e-7)
 def test_finite_source_multiple_nodes(self):
  x=forward(Scene(),Response(angular_a=(.5,.5)),nodes=[-.02,.025],weights=[.4,.6],panels=16);self.assertEqual(x['status'],'bounded_synthetic_response');self.assertFalse(x['continuous_source_certification'])
 def test_reverse_motion(self):
  x=forward(replace(Scene(),x0_m=.4,velocity_m_s=-.4),Response(),panels=16);self.assertEqual(x['status'],'bounded_synthetic_response')
 def test_refinement_enclosure(self):
  a=forward(Scene(),Response(angular_a=(.4,.6)),panels=8);b=forward(Scene(),Response(angular_a=(.4,.6)),panels=16);self.assertGreaterEqual(b['signed_thickness_change_m'][0],a['signed_thickness_change_m'][0]);self.assertLessEqual(b['signed_thickness_change_m'][1],a['signed_thickness_change_m'][1])
if __name__=='__main__':unittest.main()
