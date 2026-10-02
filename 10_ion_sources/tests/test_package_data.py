import unittest, json, csv, math
from pathlib import Path
from copy import deepcopy
import jsonschema
P=Path(__file__).resolve().parents[1]

def read(n):return json.loads((P/'data'/n).read_text())

class Package(unittest.TestCase):
 def test_schema_valid(self):jsonschema.Draft202012Validator.check_schema(read('ion_assist_record.schema.json'))
 def test_template_valid(self):jsonschema.validate(read('measurement_record_template.json'),read('ion_assist_record.schema.json'))
 def test_measured_requires_evidence(self):
  t=read('measurement_record_template.json');t['at_substrate']['surface_temperature']['status']='measured'
  with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(t,read('ion_assist_record.schema.json'))
 def test_unknown_is_null(self):
  t=read('measurement_record_template.json');t['at_substrate']['surface_temperature']['value']=300
  with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(t,read('ion_assist_record.schema.json'))
 def test_material_count_and_coverage(self):
  r=read('material_response_matrix.json');self.assertEqual(len(r),16)
  self.assertEqual({x['material'] for x in r if x['form']=='film'},{'Ta2O5','ZnS','TiO2','YbF3','SiO2','MgF2','Al2O3','H4','Ge','Cu','Cr','Al'})
  self.assertEqual({x['material'] for x in r if x['form']=='substrate'},{'ZnS','Ge','K9','ZnSe'})
 def test_no_production_recipe(self):
  for r in read('material_response_matrix.json'):
   self.assertIsNone(r['kaufman_production_voltage_V']);self.assertIsNone(r['kaufman_production_current_A']);self.assertFalse(r['process_qualified'])
 def test_source_references_exist(self):
  ids={s['source_id'] for s in read('source_registry.json')}
  for r in read('material_response_matrix.json'):self.assertTrue(set(r['source_ids'])<=ids)
 def test_sources_unique_and_summarized(self):
  r=read('source_registry.json');self.assertEqual(len(r),len({s['source_id'] for s in r}))
  for s in r:self.assertTrue((P/'sources/summaries'/f"{s['source_id']}.md").exists())
 def test_hall_is_not_kaufman(self):
  r={s['source_id']:s for s in read('source_registry.json')}
  self.assertIn('End-Hall',r['IS-19']['source_type']);self.assertIn('NOT Kaufman',r['IS-29']['source_type'])
 def test_no_real_qualification(self):self.assertFalse(read('measurement_record_template.json')['qualification']['process_qualified'])
 def test_monte_carlo_matches_log_analytic(self):
  r=read('demo_results.json')['uncertainty'];self.assertLess(abs(r['monte_carlo_cv']/r['exact_lognormal_cv']-1),.02)
 def test_motion_converges(self):
  c=read('demo_results.json')['motion_convergence'];e=[r['relative_error_to_12800'] for r in c]
  self.assertTrue(all(e[i]>e[i+1] for i in range(len(e)-1)));self.assertLess(e[-2],1e-6)
 def test_power_independent_charge_count(self):
  b=read('demo_results.json')['baseline'];self.assertAlmostEqual(b['beam']['incident_kinetic_power_W_m2'],.48*90)
 def test_source_originals_not_release(self):
  for s in read('source_registry.json'):self.assertFalse(s['release_original'])
 def test_test_matrix_has_no_thresholds(self):
  rows=list(csv.DictReader((P/'data/test_matrix.csv').open()));self.assertEqual(len(rows),16)
  self.assertTrue(all(not r['acceptance_threshold'] and not r['severity'] for r in rows))
 def test_original_license(self):
  r=read('local_originals_manifest.json');self.assertTrue(all(s['archive_allowed'] for s in r))
  self.assertTrue(all(s['release_policy']=='local_only_exclude_all_originals' for s in r))


class AdditionalSchema(unittest.TestCase):
 def test_units_cannot_silently_change(self):
  t=read('measurement_record_template.json');t['at_substrate']['positive_ion_current_density']['unit']='mA/cm2'
  with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(t,read('ion_assist_record.schema.json'))
 def test_synthetic_cannot_qualify(self):
  t=read('measurement_record_template.json');t['record_kind']='synthetic';t['qualification']['process_qualified']=True
  with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(t,read('ion_assist_record.schema.json'))
 def test_endhall_has_no_grids(self):
  t=read('measurement_record_template.json');t['source_identity'].update(source_type='end_hall_gridless',grid_count=2)
  with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(t,read('ion_assist_record.schema.json'))
 def test_species_current_basis_explicit(self):
  t=read('measurement_record_template.json');t['species']=[{'label':'synthetic O2+','charge_number':1,'fraction':1,'fraction_basis':'electric_current','energy_eV':100,'status':'synthetic'}]
  jsonschema.validate(t,read('ion_assist_record.schema.json'))

if __name__=='__main__':unittest.main(verbosity=2)
