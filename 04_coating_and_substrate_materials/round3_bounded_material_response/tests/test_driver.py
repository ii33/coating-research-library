import unittest,sys,json,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'models'))
from device_driver import load,estimate,execute
from bounded_response import Response,Scene
class DriverTests(unittest.TestCase):
 def test_default_plan(self):
  p,i=load(R/'data/device_validation_plan.json');self.assertEqual(p['execution_mode'],'plan_only');self.assertFalse(p['execution_authorized']);self.assertFalse(p['host_access_confirmed'])
 def test_budget(self):
  p,i=load(R/'data/device_validation_plan.json');e=estimate(p,i);self.assertEqual(e['forward_calls_upper'],16);self.assertEqual(e['rational_panel_visits_upper'],30720)
 def test_run_refuses_before_creating_output(self):
  p,i=load(R/'data/device_validation_plan.json')
  with self.assertRaises(ValueError):execute(p,i,None)
 def test_schema_and_semantic(self):
  from jsonschema import Draft202012Validator
  from dataclasses import asdict
  s=json.loads((R/'data/response.schema.json').read_text());v=Draft202012Validator(s);v.validate(json.loads(json.dumps(asdict(Response()))));Response().validate(Scene())
 def test_schema_rejects_extra(self):
  from jsonschema import Draft202012Validator,ValidationError
  from dataclasses import asdict
  s=json.loads((R/'data/response.schema.json').read_text());x=json.loads(json.dumps(asdict(Response())));x['material_measured_sticking']=1
  with self.assertRaises(ValidationError):Draft202012Validator(s).validate(x)
if __name__=='__main__':unittest.main()
