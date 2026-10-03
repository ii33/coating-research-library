import unittest,sys,json,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'models'))
import set_exclusion as s
from exact_intervals import I,F,f

class ReferenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.c=s.load_case();cls.r=json.loads((ROOT/'verification/tiny_results.json').read_text())
 def test_dependency_chain(self):self.assertEqual(s.verify_dependencies(),85)
 def test_parent_operator_unchanged(self):self.assertEqual(self.c['derived_observation_contract']['channels'][0]['operator'],self.c['inherited_case']['measurement'])
 def test_source_gate_positive_and_qualified_only(self):
  g=s.validate_case(self.c);self.assertEqual(g['status'],'conditional_synthetic_only');self.assertGreater(g['bounds'].lo,0)
 def test_inherited_payload_tamper(self):
  c=copy.deepcopy(self.c);c['inherited_case']['bridge']['source_contract']['n']=2
  with self.assertRaisesRegex(ValueError,'inherited_case_changed'):s.validate_case(c)
 def test_derived_hash_tamper(self):
  c=copy.deepcopy(self.c);c['derived_observation_contract']['channels'][1]['operator']['aoi_deg']=5
  with self.assertRaisesRegex(ValueError,'derived_contract_hash'):s.validate_case(c)
 def test_operator_unsupported(self):
  op=copy.deepcopy(self.c['inherited_case']['measurement']);op['substrate_mode']='finite'
  with self.assertRaises(ValueError):s.bo.validate_operator(op)
 def test_source_failure_guards(self):
  for kind,status in [('negative','negative_net'),('crosszero','zero_or_crossing_net'),('tiny','ill_conditioned_net'),('inventory','inventory_unresolved'),('nonlambert','unsupported_or_unknown_source'),('state','unknown_state_mismatch')]:
   c=copy.deepcopy(self.c['inherited_case']);b=c['bridge'];m=c['material'];r=b['t04_response']
   if kind=='negative':r['net_mass_kg_m2']=[-2e-7,-1e-7];r['signed_thickness_change_m']=[-2e-10,-1e-10]
   elif kind=='crosszero':r['net_mass_kg_m2']=[-1e-7,1e-7];r['signed_thickness_change_m']=[-1e-10,1e-10]
   elif kind=='tiny':r['signed_thickness_change_m']=[1e-16,2e-16]
   elif kind=='inventory':r['response_definition']['erosion_mass_kg_m2']=[1,1]
   elif kind=='nonlambert':b['source_contract']['n']=2
   elif kind=='state':m['nk_sample_state_id']='different'
   m['expected_bridge_payload_sha256']=s.digest(b)
   self.assertEqual(s.bo.source_gate(b,m)['status'],status,kind)
 def test_unit_and_order(self):
  n,d,ids=s.bo.incident_stack(self.c['recipe']);self.assertEqual(ids,[6,5,4,3,2,1]);self.assertEqual(d[0],f(self.c['recipe']['layers'][-1]['thickness_nm'])/1000)
 def test_subdivision_cover_and_leaf_classification(self):
  for r in self.r['runs']:
   D=I(*r['domain_exact']);L=r['leaves'];self.assertLessEqual(f(L[0]['z_exact'][0]),D.lo);self.assertGreaterEqual(f(L[-1]['z_exact'][1]),D.hi)
   for a,b in zip(L,L[1:]):self.assertGreaterEqual(f(a['z_exact'][1]),f(b['z_exact'][0]))
   Y={ch['id']:v for ch,v in s.observation_boxes(self.c,r['channels'])}
   for leaf in L:
    pred={k:I(*v) for k,v in leaf['R_exact'].items()}
    if leaf['class']=='OUT':self.assertTrue(any(s.disjoint(v,Y[k]) for k,v in pred.items()))
    if leaf['class']=='IN':self.assertEqual(set(pred),set(Y));self.assertTrue(all(s.contained(v,Y[k]) for k,v in pred.items()))
 def test_recompute_decisive_exclusion(self):
  h=self.c['parameterization']['hypotheses'][1];r=s.branch_exclude(self.c,h,['M0','M1']);expected=next(q for q in self.r['runs'] if q['hypothesis']==h['id'] and q['channels']==['M0','M1']);self.assertEqual(r,expected);self.assertEqual(r['status'],'excluded_encoded_model')
 def test_feasible_points_are_enclosures(self):
  H={h['id']:h for h in self.c['parameterization']['hypotheses']}
  for w in self.r['witnesses']:
   q=s.point_witness(self.c,H[w['hypothesis']],w['z_exact'],w['channels']);self.assertEqual(w,q);self.assertTrue(q['all_point_enclosures_inside_data'])
 def test_budget_keeps_unknown(self):
  h=self.c['parameterization']['hypotheses'][0];r=s.branch_exclude(self.c,h,['M0'],max_nodes=1)
  self.assertEqual(r['status'],'unresolved_outer_overlap');self.assertEqual(r['counts']['UNKNOWN'],1)
 def test_structural_product_alias(self):
  D=s.z_domain(self.c);z=F(500,501);self.assertLessEqual(D.lo,z);self.assertGreaterEqual(D.hi,z);self.assertEqual(z*F(501,500),1)
  h=self.c['parameterization']['hypotheses'][2]
  for d,m in zip(self.c['recipe']['layers'],h['multipliers']):self.assertEqual(f(d['thickness_nm'])*f(m)*z,f(d['thickness_nm']))
 def test_dependent_T_adds_no_constraint(self):
  Y=I('0.010583971','0.012583971');X=I('0.011','0.012');self.assertEqual(s.contained(X,Y),s.contained(1-X,1-Y));self.assertEqual(s.disjoint(X,Y),s.disjoint(1-X,1-Y))
 def test_outer_overlap_is_not_intersection_proof(self):
  # Two disjoint finite sets have overlapping hulls. A shared hull is not a witness.
  A={0,2};B={1};self.assertFalse(A&B);self.assertFalse(s.disjoint(I(0,2),I(1)))

if __name__=='__main__':unittest.main()
