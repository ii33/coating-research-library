import unittest,sys,math,json,tempfile,copy
from pathlib import Path
from dataclasses import replace
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'models'))
from source_retention import *
from diagnostics import design,row,examples
from validation_driver import fit,load,execute

class KernelTests(unittest.TestCase):
 def test_lambert_pi(self):self.assertAlmostEqual(angular_pdf(.4,0,1),.4/math.pi)
 def test_no_duplicate_projection(self):self.assertAlmostEqual(point_incident(2.,.5,.4,2.,0.,1),.1/math.pi)
 def test_hemisphere_normalization(self):
  xx,ww=np.polynomial.legendre.leggauss(20)
  for n in [0,1,3,10]:
   for c in [-.8,0,.8]:
    val=sum(w/2*angular_pdf((x+1)/2,2*math.pi*(j+.5)/24,n,c)*2*math.pi/24 for x,w in zip(xx,ww) for j in range(24))
    self.assertAlmostEqual(val,1.,places=12)
 def test_back_emission(self):self.assertEqual(angular_pdf(-.4,0,0),0.)
 def test_back_receiver(self):self.assertEqual(point_incident(1.,1.,-.2,1.,0.,1.),0.)
 def test_no_area_twice(self):
  nd={'position':[0,0,0],'normal':[0,0,1],'tangent1':[1,0,0]}
  self.assertAlmostEqual(finite_incident(2.,[nd],[1.],[0,0,1],[0,0,-1],1.),2/math.pi)
 def test_blocked_mass_not_renormalized(self):
  nd={'position':[0,0,0],'normal':[0,0,1],'tangent1':[1,0,0]}
  self.assertAlmostEqual(finite_incident(2.,[nd,nd],[.3,.7],[0,0,1],[0,0,-1],1.,visible=[1,0]),.6/math.pi)
 def test_invalid_weights(self):
  for x in [[],[.2,.3],[-1.,2.],[float('nan')]]:
   with self.assertRaises(ValueError):normalized_weights(x)
 def test_invalid_parameters(self):
  for p in [Parameters(n=-1),Parameters(c=1),Parameters(s0=0),Parameters(a=1.1),Parameters(eta_q=2),Parameters(rho_kg_m3=0)]:
   with self.assertRaises(ValueError):p.validate()
 def test_retention_bounds(self):
  for u in [0,.2,.5,1.]:self.assertTrue(0<=retained_fraction(u,.7,.8)<=1)
 def test_normal_vectors_rejected(self):
  with self.assertRaises(ValueError):finite_incident(1.,[{'position':[0,0,0],'normal':[0,0,2],'tangent1':[1,0,0]}],[1.],[0,0,1],[0,0,-1],1.)

class IdentificationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.out=examples()
 def test_global_not_only_local_ambiguity(self):
  d=self.out['exact_global_ambiguity'];np.testing.assert_allclose(d['parallel_A'],d['parallel_B'],rtol=2e-15,atol=0);self.assertEqual(d['axis_QCM_A'],d['axis_QCM_B'])
 def test_tilt_separates(self):
  d=self.out['exact_global_ambiguity'];self.assertAlmostEqual(d['tilted_witness_B']/d['tilted_witness_A'],2.)
 def test_off_axis_qcm_separates(self):
  d=self.out['exact_global_ambiguity'];self.assertAlmostEqual(d['off_axis_QCM_B']/d['off_axis_QCM_A'],2.)
 def test_single_rank(self):self.assertEqual(self.out['single_qcm']['rank'],1)
 def test_unanchored_rank(self):self.assertEqual(self.out['unanchored_multidirection']['rank'],5)
 def test_anchored_rank(self):self.assertEqual(self.out['anchored_multidirection']['rank'],7)
 def test_free_capture_not_identified(self):self.assertFalse(self.out['independent_capture_each_qcm']['full_column_rank'])
 def test_jacobian_against_difference(self):
  p=Parameters();z=p.vector();eps=1e-6;rs=design();J=log_jacobian(rs,p);J2=np.zeros_like(J)
  for j in range(7):
   a=z.copy();b=z.copy();a[j]+=eps;b[j]-=eps
   J2[:,j]=(np.log([prediction(r,Parameters.from_vector(a)) for r in rs])-np.log([prediction(r,Parameters.from_vector(b)) for r in rs]))/(2*eps)
  np.testing.assert_allclose(J,J2,atol=3e-9,rtol=3e-8)
 def test_pair_recovery(self):self.assertAlmostEqual(self.out['paired_tilt']['a'],.4)
 def test_pair_identical_angles(self):
  with self.assertRaises(ValueError):paired_retention_a(1.,1.,1.,1.)
 def test_pair_no_zero_mass(self):
  for m in [0,-1]:
   with self.assertRaises(ValueError):paired_retention_a(m,1.,1.,.5)
 def test_zero_measurement_not_floored(self):
  with self.assertRaises(ValueError):log_jacobian([dict(row('qcm_mass_rate'),visibility=0)],Parameters())
 def test_noise_scale_guard(self):
  with self.assertRaises(ValueError):rank_report(np.ones((2,2)),[1,0])
 def test_fit_noiseless(self):
  rows=design();p=Parameters();initial=Parameters(Q_kg_s=1.8e-6,n=1.5,c=.1,eta_q=.7,s0=.6,a=.3,rho_kg_m3=1800.)
  out=fit(rows,[prediction(r,p) for r in rows],[.02]*len(rows),initial)
  self.assertTrue(out['success']);np.testing.assert_allclose(list(out['parameters'].values()),list(asdict(p).values()),rtol=1e-6)
 def test_fit_refuses_rank_deficiency(self):
  with self.assertRaises(ValueError):fit(design(False),[prediction(r,Parameters()) for r in design(False)],[.02]*8,Parameters())

class ContractTests(unittest.TestCase):
 def test_clock_independence(self):
  a=two_clocks(1,0,0,1,.2,0,.1);b=two_clocks(1,0,.5,1,.2,0,.1)
  self.assertEqual(a['relative_source_rate'],b['relative_source_rate']);self.assertNotEqual(a['position_m'],b['position_m'])
 def test_unknown_q_and_retention_preserved(self):
  x=bridge_t04(t04.Scene(),t04.Response(source_scale_kg_s=None,sticking_s0=None),None,panels=4)
  self.assertEqual(x['status'],'unknown');self.assertIn('source_scale_kg_s',x['t04_response']['missing']);self.assertIn('sticking_s0',x['t04_response']['missing'])
 def test_bridge_full_forward_present(self):
  x=bridge_t04(t04.Scene(),t04.Response(source_scale_kg_s=None),(1e-6,1e-6),panels=4)
  self.assertIn('upstream_full_forward',x['t04_response']);self.assertEqual(x['point12'],'partial_unchanged');self.assertIn('response_contract_sha256',x['t04_response'])
 def test_bridge_pi_once(self):
  r=t04.Response(source_scale_kg_s=None);x=bridge_t04(t04.Scene(),r,(1e-6,1e-6),panels=4);y=t04.forward(t04.Scene(),replace(r,source_scale_kg_s=(1e-6/math.pi,)*2),panels=4)
  self.assertEqual(x['t04_response'],y)
 def test_bridge_rejects_double_scale(self):
  with self.assertRaises(ValueError):bridge_t04(t04.Scene(),t04.Response(),(1e-6,1e-6))
 def test_bridge_rejects_hidden_normalization(self):
  with self.assertRaises(ValueError):bridge_t04(t04.Scene(amplitude=1/math.pi),t04.Response(source_scale_kg_s=None),(1e-6,1e-6))
 def test_bridge_nonlambert_not_smuggled(self):
  x=bridge_t04(t04.Scene(),t04.Response(source_scale_kg_s=None),(1e-6,1e-6),n=2);self.assertIsNone(x['t04_response']);self.assertEqual(x['status'],'unsupported_non_lambert_frozen_bridge')
 def test_unknown_angular_separate(self):
  x=bridge_t04(t04.Scene(),t04.Response(source_scale_kg_s=None),(1e-6,1e-6),n=None);self.assertEqual(x['status'],'unknown_source_angular_law')
 def test_negative_net_guard(self):
  x=bridge_t04(t04.Scene(),t04.Response(source_scale_kg_s=None,erosion_mass_kg_m2=(1e-5,1e-5)),(1e-6,1e-6),panels=4);self.assertEqual(x['status'],'negative_net');self.assertIsNone(x['t04_response']['objective_interval'])
 def test_zero_denominator_guards_preserved(self):
  for den in [[0,0],[-1,1],[-2,-1],[1e-15,1e-15]]:self.assertIsNone(t04.normalize_positive([1,1],den,1e-12)['value'])
 def test_mxc_substitute_rejected(self):
  x={k:True for k in ['locked','actual_visibility_known','clock_mapping_known','material_snapshot_known','shared_source_window']};x.update(provenance='setpoint_substitute',feedback_coordinate='sample_display_rate');self.assertFalse(qualify_observation(x)['qualified_for_conditional_diagnostic'])
 def test_mxc_unknown_clock_rejected(self):self.assertFalse(qualify_observation({})['qualified_for_conditional_diagnostic'])
 def test_valid_qualified_diagnostic_not_calibration(self):
  x={k:True for k in ['locked','actual_visibility_known','clock_mapping_known','material_snapshot_known','shared_source_window']};x.update(provenance='raw_frequency_derived_mass',feedback_coordinate='crystal_model_rate');y=qualify_observation(x);self.assertTrue(y['qualified_for_conditional_diagnostic']);self.assertFalse(y['physical_calibration'])
 def test_driver_default_plan_only(self):
  p,i=load(R/'data/device_validation_plan.json');self.assertEqual(p['mode'],'plan_only');self.assertFalse(p['authorized'])
 def test_driver_not_authorized(self):
  p,i=load(R/'data/device_validation_plan.json')
  with self.assertRaises(ValueError):execute(p,i,None)
 def test_driver_bad_hash(self):
  p=json.loads((R/'data/device_validation_plan.json').read_text());p['input_sha256']='0'*64
  with tempfile.TemporaryDirectory() as td:
   d=Path(td)/'plan.json';d.write_text(json.dumps(p))
   with self.assertRaises(ValueError):load(d)

if __name__=='__main__':unittest.main()
