import sys,json,copy,tempfile,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'models'))
from contract import validate,convert
from validation_driver import DEFAULT,plan,execute

class Gates(unittest.TestCase):
 def test_nonfinite_unused_parameter_rejected(self):
  r=json.loads((R/'examples/synthetic_al.json').read_text());r['parameters']['display_density_setting']['value']=float('nan')
  with self.assertRaises(ValueError):validate(r)
 def test_plan_only(self):
  p=plan(DEFAULT);self.assertEqual(p['status'],'plan_only');self.assertEqual(p['fit_count'],480000)
 def test_checkpoint_resume_and_wrong_config(self):
  cfg=dict(DEFAULT,replicates=1,windows=1,monitors=6,cases=['nominal'])
  with tempfile.TemporaryDirectory() as d:
   first=execute(cfg,d);second=execute(cfg,d);self.assertEqual(first['summaries'],second['summaries'])
   with self.assertRaises(ValueError):execute(dict(cfg,seed=cfg['seed']+1),d)
 def test_low_signal_blocks(self):
  r=json.loads((R/'examples/synthetic_al.json').read_text());q=r['qcm'];q['frequency_covariance_hz2']=[[1e8 if i==j else 0. for i in range(11)] for j in range(11)]
  self.assertEqual(convert(r)['status'],'blocked_low_signal')
