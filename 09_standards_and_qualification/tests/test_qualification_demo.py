import copy,json,math,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'models'))
from qualification_demo import *

class Arithmetic(unittest.TestCase):
 def test_independent_difference(self): self.assertAlmostEqual(paired_standard_uncertainty(3,4),5)
 def test_positive_correlation(self): self.assertAlmostEqual(paired_standard_uncertainty(2,2,.75),math.sqrt(2))
 def test_perfect_correlation(self): self.assertEqual(paired_standard_uncertainty(2,2,1),0)
 def test_negative_correlation(self): self.assertEqual(paired_standard_uncertainty(2,2,-1),4)
 def test_invalid_uncertainty(self):
  for args in [(-1,1,0),(1,-1,0),(1,1,1.01),(1,1,float('nan'))]:
   with self.subTest(args=args),self.assertRaises(ValueError):paired_standard_uncertainty(*args)
 def test_lower_accept(self): self.assertEqual(interval_decision(.95,.004,lower=.94),'accept_under_demo_rule')
 def test_lower_reject(self): self.assertEqual(interval_decision(.93,.004,lower=.94),'reject_under_demo_rule')
 def test_lower_overlap(self): self.assertEqual(interval_decision(.942,.004,lower=.94),'indeterminate_under_demo_rule')
 def test_upper_accept(self): self.assertEqual(interval_decision(4,1,upper=5),'accept_under_demo_rule')
 def test_upper_overlap(self): self.assertEqual(interval_decision(5,1,upper=5),'indeterminate_under_demo_rule')
 def test_upper_reject(self): self.assertEqual(interval_decision(7,1,upper=5),'reject_under_demo_rule')
 def test_closed_equal_boundary(self): self.assertEqual(interval_decision(5,0,5,5),'accept_under_demo_rule')
 def test_touching_outside_is_indeterminate(self): self.assertEqual(interval_decision(4,1,lower=5),'indeterminate_under_demo_rule')
 def test_invalid_decision(self):
  for args in [(1,-1,0,None),(1,1,None,None),(1,1,2,1),(float('nan'),1,0,None)]:
   with self.subTest(args=args),self.assertRaises(ValueError):interval_decision(*args)
 def test_zero_failure_exact(self): self.assertAlmostEqual(zero_failure_upper(1),.95)
 def test_zero_failure_monotonic(self): self.assertGreater(zero_failure_upper(10),zero_failure_upper(100))
 def test_zero_failure_invalid(self):
  for n in [0,-1,1.5,True]:
   with self.subTest(n=n),self.assertRaises(ValueError): zero_failure_upper(n)
 def test_minimum_n(self):
  n=minimum_zero_failure_n(.01);self.assertEqual(n,299);self.assertLessEqual(zero_failure_upper(n),.01);self.assertGreater(zero_failure_upper(n-1),.01)
 def test_invalid_probability(self):
  for p in [0,1,-.1,float('inf')]:
   with self.subTest(p=p),self.assertRaises(ValueError):minimum_zero_failure_n(p)
 def test_coarse_grid_failure(self):
  self.assertGreater(min(synthetic_transmittance(x) for x in range(1000,1101,10)),.94)
  self.assertLess(synthetic_transmittance(1045),.94)
 def test_synthetic_outputs_labeled(self):
  r=build_results();self.assertFalse(r['real_compliance_statement']);self.assertFalse(r['execution_authorized']);self.assertEqual(r['data_class'],'synthetic_demonstration')
 def test_template_fail_closed(self):
  p=json.loads((ROOT/'templates/qualification_plan.json').read_text());self.assertTrue(plan_gaps(p))
 def test_unapproved_exclusion(self):
  p={'tests':[{'test_id':'T','applicability':'not_applicable','exclusion_reason':'not needed'}]}
  self.assertIn('T.approved_exclusion',plan_gaps(p))
 def test_missing_normative_check(self):
  p={'tests':[{'test_id':'T','applicability':'applicable'}]}
  self.assertIn('T.normative_procedure_verified',plan_gaps(p))
 def test_duplicate_test_id(self):
  p={'tests':[{'test_id':'T','applicability':'undecided'}]*2}
  self.assertIn('tests[1].unique_test_id',plan_gaps(p))
 def test_registry_no_claimed_fulltext(self):
  reg=json.loads((ROOT/'data/source_registry.json').read_text())
  self.assertEqual(len({r['source_id'] for r in reg['sources']}),len(reg['sources']))
  self.assertTrue(all(not r['original_archived'] for r in reg['sources']))
 def test_standards_no_fake_threshold(self):
  r=json.loads((ROOT/'data/standards_map.json').read_text());self.assertFalse(r['contract_ready'])
  self.assertTrue(all(s['acceptance_threshold'] is None for s in r['standards']))
 def test_future_gb_not_effective(self):
  rows=json.loads((ROOT/'data/official_status_mil_gb.json').read_text())['standards']
  for r in rows:
   if r['id'] in ['GB/T 26332.2-2026','GB/T 26332.3-2026']:
    self.assertEqual(r['status'],'即将实施');self.assertEqual(r['implementation_date'],'2027-01-01')
if __name__=='__main__':unittest.main()
