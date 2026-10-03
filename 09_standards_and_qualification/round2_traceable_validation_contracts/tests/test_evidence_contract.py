import json, math, sys, unittest
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'models'))
from evidence_contract import (baseline,validate,examples,interval_decision,fraction,
                               mean_u,difference_u,conditional_scalar,signed_and_clipped_integrals)

class EvidenceTests(unittest.TestCase):
    def test_baseline_is_research_only(self):
        r=validate(baseline());self.assertTrue(r['semantic_ready']);self.assertFalse(r['production_qualified']);self.assertFalse(r['hardware_validated'])
    def test_all_fifteen_fixture_outcomes(self):
        r=examples();self.assertEqual(len(r['cases']),15)
        for c in r['cases']:
            with self.subTest(c['name']):self.assertTrue(c['matches_expectation'])
    def test_closed_lower_boundary(self):
        self.assertEqual(interval_decision('.944','.004','.94')['decision'],'accept_under_rule')
        self.assertEqual(interval_decision('.936','.004','.94')['decision'],'indeterminate')
        self.assertEqual(interval_decision('.9359','.004','.94')['decision'],'reject_under_rule')
    def test_closed_upper_boundary(self):
        self.assertEqual(interval_decision('.996','.004',upper='1')['decision'],'accept_under_rule')
        self.assertEqual(interval_decision('1.004','.004',upper='1')['decision'],'indeterminate')
        self.assertEqual(interval_decision('1.0041','.004',upper='1')['decision'],'reject_under_rule')
    def test_high_precision_boundary_does_not_round_into_acceptance(self):
        self.assertEqual(interval_decision('0.94399999999999999999999999999','0.004','0.94')['decision'],'indeterminate')
        self.assertEqual(interval_decision('0.94400000000000000000000000001','0.004','0.94')['decision'],'accept_under_rule')
        self.assertEqual(fraction('94.399999999999999999999999999','percent'),'0.94399999999999999999999999999')
        with self.assertRaises(ValueError): interval_decision('1e1001','0','0')
    def test_two_sided_and_zero_u(self):
        self.assertEqual(interval_decision('.5','.5','0','1')['decision'],'accept_under_rule')
        self.assertEqual(interval_decision('0','0','0','1')['decision'],'accept_under_rule')
        self.assertEqual(interval_decision('0','.1','0','1')['decision'],'indeterminate')
    def test_invalid_intervals_rejected(self):
        for args in [('1','-1','0',None),('NaN','1','0',None),('Infinity','1','0',None),('1','1',None,None),('1','1','2','0'),(1.,'1','0',None)]:
            with self.subTest(args):
                with self.assertRaises(ValueError):interval_decision(*args)
    def test_percent_is_not_percentage_point_confusion(self):
        self.assertEqual(fraction('95','percent'),'0.95');self.assertEqual(fraction('0.4','percent'),'0.004')
        self.assertEqual(fraction('0.95','1'),'0.95')
        with self.assertRaises(ValueError):fraction('1','ppm')
    def test_common_uncertainty_floor(self):
        self.assertAlmostEqual(mean_u(.003,.001,25),.003006659275674582)
        self.assertAlmostEqual(mean_u(.003,0.,1000),.003)
        self.assertGreater(mean_u(.003,.001,25),math.sqrt(.003**2+.001**2)/5)
    def test_mean_input_guards(self):
        for args in [(-1,1,1),(1,1,0),(1,1,True),(1,1,2.5),(float('nan'),1,3)]:
            with self.assertRaises(ValueError):mean_u(*args)
    def test_pair_covariance(self):
        u=math.sqrt(.003**2+.001**2)
        self.assertAlmostEqual(difference_u(u,u,.003**2),math.sqrt(2)*.001)
        self.assertEqual(difference_u(1,1,1),0.)
        self.assertEqual(difference_u(1,1,-1),2.)
        with self.assertRaises(ValueError):difference_u(1,1,1.01)
    def test_conditional_gaussian_algebra(self):
        r=conditional_scalar(4,9,3,2);self.assertEqual(r['innovation_variance'],6.75);self.assertEqual(r['mean_shift'],1.5)
        with self.assertRaises(ValueError):conditional_scalar(1,1,1,0)
    def test_nonlinear_square_analytic(self):
        r=examples()['mathematics']['nonlinear_square'];self.assertAlmostEqual(r['analytic_expectation'],.04);self.assertAlmostEqual(r['analytic_u'],.0565685424949238)
    def test_negative_clipping_integral(self):
        r=signed_and_clipped_integrals([-1.,2.,-1.,2.],[1.,1.,1.,1.]);self.assertEqual(r['signed_nm'],2);self.assertEqual(r['max_zero_clipped_nm'],4)
        self.assertFalse(r['device_algorithm_claim'])
        with self.assertRaises(ValueError):signed_and_clipped_integrals([1.],[-1.])
    def test_parameter_event_order(self):
        p=baseline();o=p['observations'][0];o.update(parameter_switched=True,parameter_event_id='E1')
        p['events']=[{'id':'E1','kind':'parameter_change','t_s':9.,'snapshot_id':'P1'}]
        self.assertTrue(validate(p)['semantic_ready']);p['events'][0]['t_s']=11
        self.assertIn('PARAMETER_EVENT_MISSING',[x['code'] for x in validate(p)['errors']])
    def test_derivation_needs_transform(self):
        p=baseline();p['observations'][0].update(reading_origin='derived_from_measurement')
        self.assertIn('DERIVATION_MISSING',[x['code'] for x in validate(p)['errors']])
    def test_budget_not_collapsed_into_fit(self):
        p=baseline();p['numerics'].append({'id':'profile','status':'budget_exhausted','required_for_claim':True,'calls':45,'budget':45,'stop_reason':'max_calls'})
        self.assertIn('NUMERIC_INCOMPLETE',[x['code'] for x in validate(p)['errors']]);self.assertEqual(len(p['numerics']),2)
    def test_no_real_data_or_release_path(self):
        p=baseline();p['evidence_mode']='measured_real';r=validate(p);self.assertFalse(r['semantic_ready']);self.assertFalse(r['production_qualified'])
    def test_malformed_outer_shape(self):
        self.assertFalse(validate([])['semantic_ready']);self.assertFalse(validate({})['semantic_ready'])
        p=baseline();p['observations']=[[]];self.assertFalse(validate(p)['semantic_ready'])
    def test_duplicate_ids_rejected(self):
        p=baseline();p['observations'][1]['id']='O_F';self.assertIn('ID_INVALID',[x['code'] for x in validate(p)['errors']])
    def test_json_schema_shape(self):
        try: from jsonschema import Draft202012Validator
        except ImportError:self.skipTest('optional jsonschema unavailable')
        schema=json.loads((ROOT/'contracts/evidence_packet.schema.json').read_text());Draft202012Validator.check_schema(schema)
        v=Draft202012Validator(schema);self.assertEqual(list(v.iter_errors(baseline())),[])
        p=baseline();p['requested_claim']='production_acceptance';self.assertTrue(list(v.iter_errors(p)))
        p=baseline();p['parameter_snapshots'][0]['density_kg_m3']=-1;self.assertTrue(list(v.iter_errors(p)))
        p=baseline();p['unexpected_field']=1;self.assertTrue(list(v.iter_errors(p)))
    def test_fixture_files_match_generator(self):
        stored=json.loads((ROOT/'examples/tiny_results.json').read_text());self.assertEqual(stored,examples())

if __name__=='__main__':unittest.main()
