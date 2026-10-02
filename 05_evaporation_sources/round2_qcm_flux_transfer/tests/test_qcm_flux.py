import unittest,sys,json,copy
from pathlib import Path
import numpy as np
from scipy.integrate import quad
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'models'))
from qcm_flux import *
from contract import convert,validate

class Acoustic(unittest.TestCase):
 def test_zero(self):self.assertEqual(float(mass_areal(6e6,6e6,1.08)),0.)
 def test_sign(self):self.assertGreater(float(mass_areal(5999000,6e6)),0)
 def test_small_load(self):self.assertAlmostEqual(float(mass_areal(6e6-1,6e6)/mass_areal(6e6-1,6e6,method='sauerbrey')),1.,places=5)
 def test_z_one_period(self):
  f0=6e6;f=5.6e6;self.assertAlmostEqual(float(mass_areal(f,f0,1.)),QUARTZ_RHO*QUARTZ_N*(f0-f)/(f0*f),places=10)
 def test_roundtrip(self):
  m=np.array([0.,1e-6,.001,.01]);np.testing.assert_allclose(mass_areal(frequency_from_mass(m,6e6,1.08),6e6,1.08),m,atol=1e-14,rtol=1e-9)
 def test_analytic_derivative(self):
  f=5.8e6;h=.1;fd=(mass_areal(f+h,6e6,1.08)-mass_areal(f-h,6e6,1.08))/(2*h);self.assertAlmostEqual(float(fd/mass_frequency_derivative(f,6e6,1.08)),1,places=7)
 def test_branch(self):
  for f in [3e6,6e6+1,-1,np.nan]:
   with self.assertRaises(ValueError):mass_areal(f,6e6)
 def test_viscoelastic_reject(self):
  with self.assertRaises(ValueError):mass_areal(5999000,6e6,rigid=False)
 def test_overtone_reject(self):
  with self.assertRaises(ValueError):mass_areal(5999000,6e6,fundamental=False)
 def test_drift_requires_evidence(self):
  with self.assertRaises(ValueError):rate_from_frequency([0,1,2],[6e6-1,6e6-2,6e6-3],6e6)
 def test_rate_recovers(self):
  t=np.arange(10.);m=1e-5+t*1e-6;f=frequency_from_mass(m,6e6)+2*t;r=rate_from_frequency(t,f,6e6,drift_hz=2*t)
  self.assertAlmostEqual(r['slope_kg_m2_s']/1e-6,1.,places=8)
 def test_loss_preserved(self):
  t=np.arange(5.);f=frequency_from_mass(1e-4-t*1e-6,6e6);self.assertLess(rate_from_frequency(t,f,6e6,drift_hz=0.)['slope_kg_m2_s'],0)
 def test_covariance(self):
  t=np.arange(5.);f=frequency_from_mass(1e-5+t*1e-6,6e6);r=rate_from_frequency(t,f,6e6,drift_hz=0.,frequency_covariance_hz2=np.eye(5)*.01);self.assertGreater(r['slope_std_kg_m2_s'],0)
 def test_time_gate(self):
  with self.assertRaises(ValueError):rate_from_frequency([1,0,2],[6e6]*3,6e6,drift_hz=0)

class Transfer(unittest.TestCase):
 def test_axis(self):self.assertAlmostEqual(point_kernel([[0,0,.5]],[[0,0,-1]],1)[0],1/(np.pi*.25))
 def test_back(self):self.assertEqual(point_kernel([[0,0,-.5]],[[0,0,1]],0)[0],0)
 def test_occlusion(self):self.assertEqual(point_kernel([[0,0,.5]],[[0,0,-1]],1,visibility=[0])[0],0)
 def test_singular(self):
  with self.assertRaises(ValueError):point_kernel([[0,0,0]],[[0,0,-1]],1)
 def test_normalization(self):
  n=2.3;a=.8
  integral=quad(lambda mu:quad(lambda phi:(n+1)/(2*np.pi)*mu**n*(1+a*(1-mu*mu)*np.cos(2*phi)),0,2*np.pi)[0],0,1)[0]
  self.assertAlmostEqual(integral,1,places=9)
 def test_capture(self):self.assertAlmostEqual(source_incident_from_qcm(1,.5,.1,.2),2.2)
 def test_bad_capture(self):
  for x in [0,1.1,None]:
   with self.assertRaises((ValueError,TypeError)):source_incident_from_qcm(1,x)
 def test_shadow_division(self):
  with self.assertRaises(ValueError):transfer_qcm_to_workpiece(1,.9,0,1)
 def test_transfer(self):self.assertAlmostEqual(transfer_qcm_to_workpiece(2,.5,4,np.array([2.]))['incident_workpiece_kg_m2_s'][0],2)
 def test_negative_arrival(self):
  with self.assertRaises(ValueError):source_incident_from_qcm(-1,1)
 def test_unnormalized(self):
  with self.assertRaises(ValueError):point_kernel([[0,0,1]],[[0,0,-2]],1)

class Chemistry(unittest.TestCase):
 def test_al_atoms(self):self.assertAlmostEqual(mixture_from_mass(MOLAR_MASS['Al']/N_A,{'Al':1},{'Al':{'Al':1}})['total_atomic_flux_atoms_m2_s'],1)
 def test_cluster(self):
  v=mixture_from_mass(1.,{'Al':.5,'Al2':.5},{'Al':{'Al':1},'Al2':{'Al':2}});self.assertAlmostEqual(v['total_atomic_flux_atoms_m2_s']/(N_A/MOLAR_MASS['Al']),1)
 def test_reactive_conservation(self):
  v=retained_elements({'Al':2.,'O2':1.5},{'Al':{'Al':1},'O2':{'O':2}},{'Al':1.,'O2':1.});self.assertEqual(v['net_element_flux_atoms_m2_s'],{'Al':2.,'O':3.})
 def test_reactive_mass_exceeds_source(self):
  v=retained_elements({'Al':2.,'O2':1.5},{'Al':{'Al':1},'O2':{'O':2}},{'Al':1.,'O2':1.});self.assertGreater(v['net_mass_flux_kg_m2_s'],2*MOLAR_MASS['Al']/N_A)
 def test_gas(self):self.assertEqual(gas_impingement(0,300,.032),0)
 def test_bad_formula(self):
  with self.assertRaises(ValueError):species_elements({'Al':1},{'Al':{'Al':1.5}})
 def test_fraction(self):
  with self.assertRaises(ValueError):mixture_from_mass(1,{'Al':.7},{'Al':{'Al':1}})

class Identification(unittest.TestCase):
 def setUp(self):
  self.x=np.array([[0,0,.5],[.1,0,.5],[0,.2,.5],[.3,0,.5],[0,.4,.5],[.2,.3,.5]])
  self.norm=np.tile([0,0,-1],(len(self.x),1));self.y=2e-6*point_kernel(self.x,self.norm,2.4,.25)*.92
 def test_recover(self):
  f=fit_source(self.x,self.norm,self.y,.01,capture=.92,loss='linear');np.testing.assert_allclose([f['Q_kg_s']/2e-6,f['n'],f['a']],[1,2.4,.25],rtol=1e-6)
 def test_single_rank(self):self.assertEqual(rank_report(design_matrix(self.x[:1],self.norm[:1],2))['rank'],1)
 def test_repeated_axis_rank(self):
  x=[[0,0,.4],[0,0,.5],[0,0,.6]];self.assertEqual(rank_report(design_matrix(x,[[0,0,-1]]*3,2))['rank'],1)
 def test_capture_rank(self):self.assertFalse(rank_report(design_matrix(self.x,self.norm,2,fit_capture=True))['identifiable'])
 def test_independent_q_breaks_scale(self):
  f=fit_source(self.x,self.norm,self.y,.01,capture=.9,fit_capture=True,independent_source=(2e-6,.01),loss='linear');self.assertAlmostEqual(f['capture'],.92,places=6)
 def test_rank_reject(self):
  with self.assertRaises(ValueError):fit_source(self.x,self.norm,self.y,.01,fit_capture=True)
 def test_zero_not_floored(self):
  y=self.y.copy();y[0]=0
  with self.assertRaises(ValueError):fit_source(self.x,self.norm,y,.01)
 def test_robust_covariance_not_fake(self):self.assertIsNone(fit_source(self.x,self.norm,self.y,.01,capture=.92)['covariance'])
 def test_correlated_propagation(self):
  p=propagate_covariance(lambda x:[x[0]-x[1]],[1.,1.],[[1,.9],[.9,1]]);self.assertAlmostEqual(p['covariance'][0][0],.2,places=8)
 def test_non_psd(self):
  with self.assertRaises(ValueError):propagate_covariance(lambda x:x,[1,1],[[1,2],[2,1]])

class Contract(unittest.TestCase):
 def setUp(self):self.r=json.loads((R/'examples/synthetic_al.json').read_text())
 def test_synthetic(self):self.assertEqual(convert(self.r)['status'],'synthetic_computed')
 def test_truth(self):self.assertAlmostEqual(convert(self.r)['source_rate_kg_s']/2e-6,1,places=8)
 def test_unknown(self):self.assertEqual(convert(json.loads((R/'examples/actual_unknown.json').read_text()))['status'],'blocked_unmeasured')
 def test_density_not_used(self):
  v=convert(self.r);self.r['parameters']['display_density_setting']['value']=9999;self.assertEqual(convert(self.r)['source_rate_kg_s'],v['source_rate_kg_s'])
 def test_no_synthetic_leak(self):
  self.r['record_kind']='actual_unmeasured'
  with self.assertRaises(ValueError):validate(self.r)
 def test_extra_fields(self):
  self.r['bogus']=2
  with self.assertRaises(Exception):validate(self.r)
 def test_unknown_nonnull(self):
  self.r['parameters']['z_ratio']['status']='unknown'
  with self.assertRaises(ValueError):validate(self.r)

if __name__=='__main__':unittest.main()
