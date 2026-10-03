import unittest,sys,json,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'models'))
import acceptance as a
class Check(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.s=a.replay_tiny()
 def test_01_claim_matrix(self):
  for row in json.loads((a.ROOT/'cases/claims.json').read_text()):
   with self.subTest(case=row['id']):self.assertEqual(a.evaluate(self.s,row['claim'])['status'],row['expected'])
 def test_02_saved_session_not_live(self):
  fake=a.Session(json.loads(json.dumps(self.s.payload)))
  with self.assertRaisesRegex(ValueError,'fresh_budgeted_replay'):a.evaluate(fake,a.claim('proxy_exists'))
 def test_03_mutation_detected(self):
  v=self.s.payload['joint']['counts']['UNKNOWN'];self.s.payload['joint']['counts']['UNKNOWN']=0
  try:
   with self.assertRaisesRegex(ValueError,'session_modified'):a.evaluate(self.s,a.claim('proxy_exists'))
  finally:self.s.payload['joint']['counts']['UNKNOWN']=v
 def test_04_unknowns_keep_pruned(self):
  r=a.evaluate(self.s,a.claim('all_v_in',range=['0.99','1.1']));self.assertEqual(r['retained_unknown_count'],32);self.assertEqual(r['objective_pruned_still_data_unknown'],15);self.assertEqual(len(r['claim_crossing_leaf_ids']),4)
 def test_05_boundary_equal_inclusive(self):
  q=self.s.payload['witness']['R_exact']['M0'];self.assertEqual(a.evaluate(self.s,a.claim('point_M0_in',range=q))['status'],'conditional_accept')
 def test_06_float_threshold_refused(self):
  with self.assertRaises(ValueError):a.evaluate(self.s,a.claim('minimum_J_le',threshold=1.01))
 def test_07_nan_refused(self):
  with self.assertRaises(ValueError):a.evaluate(self.s,a.claim('minimum_J_le',threshold='NaN'))
 def test_08_reversed_refused(self):
  with self.assertRaises(ValueError):a.evaluate(self.s,a.claim('all_v_in',range=['2','1']))
 def test_09_model_not_readout(self):
  q={'range':['0','0.012']};self.assertEqual(a.evaluate(self.s,a.claim('point_M0_in',**q))['status'],'conditional_accept');self.assertEqual(a.evaluate(self.s,a.claim('observation_M0_in',**q))['status'],'retain_unknown')
 def test_10_wide_gap_not_reject(self):self.assertEqual(a.evaluate(self.s,a.claim('gap_le',threshold='0.00001'))['status'],'retain_unknown')
 def test_11_no_production(self):
  for row in json.loads((a.ROOT/'cases/claims.json').read_text()):self.assertIs(a.evaluate(self.s,row['claim'])['production_release'],False)
 def test_12_replay_reproduces(self):self.assertTrue(all(a.summary(self.s)['frozen_replay_matches'].values()));self.assertEqual(a.summary(self.s)['ledger']['interval_wavelengths'],977)
 @classmethod
 def tearDownClass(cls):
  (a.ROOT/'verification/unit_resource_receipt.json').write_text(json.dumps({'session_replays':1,'ledger':a.summary(cls.s)['ledger'],'case_matrix_size':len(json.loads((a.ROOT/'cases/claims.json').read_text())),'no_heavy':True},indent=2)+'\n')
if __name__=='__main__':unittest.main(verbosity=2)
