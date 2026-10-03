import unittest,sys,json,copy,subprocess,os
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'models'))
import candidate_sets as s
from budget_driver import make_plan
from exact_intervals import I,F,f

class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.c,cls.k=s.load();s.validate_point(cls.c,cls.k,'1','1',s.Ledger(0,4,0));cls.r={q.stem:json.loads(q.read_text()) for q in (ROOT/'verification/tiny_final').glob('*.json')}
 def test_copied_chain(self):self.assertEqual(s.verify_dependencies(),96)
 def test_parent_and_derived_operator_identity(self):
  c=self.c;k=self.k;self.assertEqual(k['derived_observation_contract_sha256'],s.digest(c['derived_observation_contract']));self.assertEqual(c['derived_observation_contract']['channels'][0]['operator'],c['inherited_case']['measurement'])
 def test_hash_tamper(self):
  k=copy.deepcopy(self.k);k['derived_observation_contract_sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'derived_operator'):s.validate(self.c,k)
 def test_contract_dimension_rejected(self):
  k=copy.deepcopy(self.k);k['parameterization']['dimension']=3
  with self.assertRaisesRegex(ValueError,'unsupported_parameter'):s.validate(self.c,k)
 def test_source_failure_guards(self):
  for kind,status in [('negative','negative_net'),('crosszero','zero_or_crossing_net'),('tiny','ill_conditioned_net'),('inventory','inventory_unresolved'),('nonlambert','unsupported_or_unknown_source'),('state','unknown_state_mismatch'),('unknown_nk','unknown_material_state'),('unknown_density','unknown_density')]:
   c=copy.deepcopy(self.c['inherited_case']);b=c['bridge'];m=c['material'];r=b['t04_response']
   if kind=='negative':r['net_mass_kg_m2']=[-2e-7,-1e-7];r['signed_thickness_change_m']=[-2e-10,-1e-10]
   elif kind=='crosszero':r['net_mass_kg_m2']=[-1e-7,1e-7];r['signed_thickness_change_m']=[-1e-10,1e-10]
   elif kind=='tiny':r['signed_thickness_change_m']=[1e-16,2e-16]
   elif kind=='inventory':r['response_definition']['erosion_mass_kg_m2']=[1,1]
   elif kind=='nonlambert':b['source_contract']['n']=2
   elif kind=='state':m['nk_sample_state_id']='different'
   elif kind=='unknown_nk':m['nk_basis']='unknown'
   elif kind=='unknown_density':r['response_definition']['density_kg_m3']=None
   m['expected_bridge_payload_sha256']=s.digest(b)
   self.assertEqual(s.bo.source_gate(b,m)['status'],status,kind)
 def test_nm_um_layer_order(self):
  n,d,ids=s.bo.incident_stack(self.c['recipe']);self.assertEqual(ids,[6,5,4,3,2,1]);self.assertEqual(d[0],f(self.c['recipe']['layers'][5]['thickness_nm'])/1000)
 def test_exact_partition_all_saved_runs(self):
  for key in ['plane_M0_63','plane_joint_255','outer10_joint_31','zero_budget']:self.assertTrue(s.verify_cover(self.r[key]))
 def test_cover_gap_rejected(self):
  r=copy.deepcopy(self.r['plane_joint_255']);r['leaves'].pop()
  with self.assertRaisesRegex(ValueError,'coverage_hole'):s.verify_cover(r)
 def test_saved_out_in_evidence(self):
  for key in ['plane_M0_63','plane_joint_255','outer10_joint_31','zero_budget']:
   run=self.r[key];Y={ch['id']:v for ch,v in s.inherited.observation_boxes(self.c,run['channels'])}
   for row in run['leaves']:
    R={c:I(*v) for c,v in row['R_exact'].items()}
    if row['data_class']=='OUT':self.assertTrue(any(s.inherited.disjoint(r,Y[c]) for c,r in R.items()))
    elif row['data_class']=='IN':self.assertEqual(set(R),set(Y));self.assertTrue(all(s.inherited.contained(r,Y[c]) for c,r in R.items()))
 def test_recompute_outer10_exclusion(self):
  r=s.screen(self.c,self.k,max_nodes=31,box=s.domain(self.c,self.k,'1.1'));saved=self.r['outer10_joint_31']
  for key in r:self.assertEqual(r[key],saved[key],key)
  self.assertEqual(r['counts'],{'OUT':7,'IN':0,'UNKNOWN':0})
 def test_recompute_witness(self):
  w=s.validate_point(self.c,self.k,'1','1',s.Ledger(0,4,0));self.assertEqual(w,self.r['witnesses'][0]);self.assertTrue(w['proxy_feasible']);self.assertFalse(w['source_realization'])
 def test_no_node_budget_unknown(self):
  r=s.screen(self.c,self.k,max_nodes=0);self.assertEqual(r['counts'],{'OUT':0,'IN':0,'UNKNOWN':1});self.assertEqual(r['charged']['interval_wavelengths'],0)
 def test_no_optical_budget_unknown(self):
  r=s.screen(self.c,self.k,max_nodes=1,ledger=s.Ledger(1,0,0));self.assertEqual(r['counts']['UNKNOWN'],1);self.assertEqual(r['counts']['OUT'],0)
 def test_partial_channel_budget_unknown(self):
  r=s.screen(self.c,self.k,max_nodes=1,ledger=s.Ledger(1,2,0));self.assertEqual(r['counts']['OUT'],0);self.assertEqual(r['charged']['interval_wavelengths'],2)
 def test_arithmetic_failure_unknown(self):
  for exc in [ZeroDivisionError,ArithmeticError]:
   with patch.object(s,'channel_interval',side_effect=exc):r=s.screen(self.c,self.k,max_nodes=1)
   self.assertEqual(r['counts']['UNKNOWN'],1);self.assertEqual(r['counts']['OUT'],0)
 def test_objective_includes_unknown(self):
  r=s.screen(self.c,self.k,max_nodes=0);o=s.optimize_bounds(self.k,r,self.r['witnesses']);self.assertEqual(o['unknown_included'],1);self.assertEqual(self.r['plane_joint_255']['optimization']['unknown_included'],32);self.assertEqual(o['objective_lower_exact'],'0');self.assertFalse(o['global_optimizer_certificate'])
 def test_constraint_unknown_stays_in_optimum(self):
  r=s.screen(self.c,self.k,max_nodes=0);o=s.optimize_bounds(self.k,r,self.r['witnesses']);self.assertEqual(r['leaves'][0]['constraint_class'],'UNKNOWN');self.assertEqual(o['eligible_leaf_ids'],['r']);self.assertEqual(o['unknown_included'],1)
 def test_wrong_witness_contract_rejected(self):
  w=copy.deepcopy(self.r['witnesses']);w[0]['candidate_contract_sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'witness_contract'):s.optimize_bounds(self.k,s.screen(self.c,self.k,max_nodes=0),w)
 def test_modified_screen_rejected(self):
  r=s.screen(self.c,self.k,max_nodes=0);r['leaves'][0]['objective_exact']=['9','9']
  with self.assertRaisesRegex(ValueError,'unverified_or_modified_screen'):s.optimize_bounds(self.k,r,self.r['witnesses'])
 def test_forged_witness_rejected(self):
  w=copy.deepcopy(self.r['witnesses']);w[0]['objective_exact']=['0','0']
  with self.assertRaisesRegex(ValueError,'unverified_or_modified'):s.optimize_bounds(self.k,s.screen(self.c,self.k,max_nodes=0),w)
 def test_objective_prune_not_data_out(self):
  r=copy.deepcopy(self.r['plane_joint_255']);before=copy.deepcopy(r);o=r['optimization'];pruned=[q for q in o['annotations'] if q['disposition']=='PRUNED_OBJECTIVE_BOUND'];self.assertEqual(len(pruned),15);self.assertTrue(all(q['data_class']=='UNKNOWN' for q in pruned));self.assertEqual(r,before)
 def test_optimizer_miss_not_empty(self):
  q=self.r['searches'];self.assertEqual(q['deliberate_miss']['search_state'],'optimizer_not_found_within_budget');self.assertTrue(self.r['witnesses'][0]['proxy_feasible']);self.assertFalse(q['deliberate_miss']['finite_search_is_global_certificate'])
 def test_joint_existential_vs_separate(self):
  # f0(z)=z in [0,.1], f1(z)=z in [.9,1]: each separately possible, no shared z.
  self.assertTrue(0<=F(1,20)<=1);self.assertTrue(0<=F(19,20)<=1);self.assertTrue(s.inherited.disjoint(I(0,'0.1'),I('0.9',1)))
 def test_dependent_T(self):
  for X in [I('0.011','0.012'),I('0.02','0.03')]:
   Y=I('0.010583971','0.012583971');self.assertEqual(s.inherited.contained(X,Y),s.inherited.contained(1-X,1-Y));self.assertEqual(s.inherited.disjoint(X,Y),s.inherited.disjoint(1-X,1-Y))
 def test_global_product_alias(self):self.assertEqual(F(500,501)*F(501,500),1)
 def test_interval_touch_not_out(self):self.assertFalse(s.inherited.disjoint(I(0,1),I(1,2)))
 def test_outside_domain_rejected(self):
  with self.assertRaisesRegex(ValueError,'outside_contracted'):s.screen(self.c,self.k,box=s.Box(1,1,'1.2','1.2'))
 def test_driver_plan_caps(self):
  tiny=make_plan('tiny');full=make_plan('full');self.assertEqual(tiny['required_caps'],{'max_nodes':349,'max_interval_wavelengths':1337,'max_float_vectors':10});self.assertEqual(len(full['jobs']),8);self.assertEqual(full['default_mode'],'plan_only')
 def test_actual_budget_ledger(self):
  ledger=self.r['summary']['ledger'];self.assertEqual(ledger['nodes'],331);self.assertEqual(ledger['interval_wavelengths'],1166);self.assertEqual(ledger['float_vectors'],10);self.assertEqual(ledger['float_wavelengths'],40)
 def test_budget_invalid_rejected(self):
  with self.assertRaises(ValueError):s.Ledger(True,0,0)
  with self.assertRaises(ValueError):s.screen(self.c,self.k,max_nodes=-1)
if __name__=='__main__':unittest.main()
