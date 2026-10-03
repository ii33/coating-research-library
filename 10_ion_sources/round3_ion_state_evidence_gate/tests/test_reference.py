import unittest,sys,math,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'models'))
from state_physics import *
from evidence_gate import *
from driver import run_tiny,plan
class Reference(unittest.TestCase):
 def test_default(self):self.assertFalse(plan()['executed'])
 def test_limit_solution(self):
  self.assertEqual(step(.3,0,0,0,2),{'x':.3,'integral_x_s':.6})
  self.assertAlmostEqual(step(0,1,0,0,1)['x'],1-math.exp(-1))
  self.assertAlmostEqual(step(.2,1,2,3,0)['x'],.2)
 def test_integral(self):
  s=step(0,1,0,1,1);self.assertAlmostEqual(s['integral_x_s'],.5*(1-(1-math.exp(-2))/2))
  s=step(.3,1e-12,0,0,1);self.assertAlmostEqual(s['integral_x_s'],.3+ .7e-12/2,places=15)
 def test_reject_erosion_rate(self):
  with self.assertRaises(ValueError):step(.3,1,0,-1,1)
 def test_extreme_rates_rejected(self):
  with self.assertRaises(ValueError):step(.3,1e308,1e308,1e308,1e-308)
  with self.assertRaises(ValueError):step(.3,1e200,0,0,1e200)
 def test_history_and_joint(self):
  pulse={'a_s1':1,'b_s1':0,'c_s1':0,'duration_s':1};repair={'a_s1':0,'b_s1':1,'c_s1':0,'duration_s':1}
  a=evolve(0,[pulse,repair])['final_occupancy'];b=evolve(0,[repair,pulse])['final_occupancy']
  self.assertAlmostEqual(a,(1-math.exp(-1))*math.exp(-1));self.assertAlmostEqual(b,1-math.exp(-1));self.assertLess(a,b)
  A=[{'dose_m2':.5,'energy_ev':50,'theta_deg':0},{'dose_m2':.5,'energy_ev':150,'theta_deg':60}]
  B=[{'dose_m2':.5,'energy_ev':50,'theta_deg':60},{'dose_m2':.5,'energy_ev':150,'theta_deg':0}]
  aa=correlated_kernel(A);bb=correlated_kernel(B);self.assertEqual(aa['mean_energy_ev'],bb['mean_energy_ev']);self.assertAlmostEqual(aa['mean_response_ev'],43.75);self.assertAlmostEqual(bb['mean_response_ev'],81.25)
 def test_unknown_not_zero(self):
  s=bounded_evolve([0,0],[{'duration_s':1,'a_s1':None,'b_s1':[1,1],'c_s1':[0,0]}]);self.assertEqual(s['x_bounds'],[0,1]);self.assertIsNone(s['nk'])
 def test_derived_no_old_values(self):
  p={'data_origin':'synthetic','evidence':{},'exposure':{'a':1}};a=derive_state(p);self.assertIsNone(a['nk']);self.assertIsNone(a['film_density_kg_m3']);p['exposure']['a']=2;self.assertNotEqual(a['state_id'],derive_state(p)['state_id'])
 def test_nonfinite(self):
  with self.assertRaises(ValueError):evaluate({'data_origin':'synthetic','claim':'history_state','v':float('nan')})
 def test_equivalence(self):
  self.assertEqual(equivalence({'x':[-1,1]},{'x':1})['status'],'conditional_accept')
  self.assertEqual(equivalence({'x':[-1,2]},{'x':1})['status'],'retain_unknown')
  self.assertEqual(equivalence({'x':[2,3]},{'x':1})['status'],'reject_claim')
 def test_case_matrix(self):self.assertTrue(all(x['passed']for x in run_tiny()['cases']))
if __name__=='__main__':unittest.main()
