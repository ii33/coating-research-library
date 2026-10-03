import copy,json,math,sys,unittest
from dataclasses import replace
from fractions import Fraction as F
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'models'))
from trust_region import *
from analytic_oracle import exact_value_gradient

class ReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=Scene();cls.tr=local_trial(cls.s);cls.base=cls.tr['baseline']
    def test_full_forward_enclosure(self):
        value,j=exact_value_gradient(self.s)
        b=self.base['value_interval'];self.assertLessEqual(b['lo'],value);self.assertGreaterEqual(b['hi'],value)
        np.testing.assert_allclose(j,self.base['total_gradient'],rtol=1e-11,atol=1e-12)
    def test_event_step_accepted(self):
        self.assertEqual(self.tr['decision']['decision'],'accept')
        self.assertEqual(self.tr['comparison']['relation'],'b_better')
        self.assertLess(self.tr['trial']['objective_interval']['hi'],self.base['objective_interval']['lo'])
    def test_omitted_event_stagnates(self):
        r=local_trial(self.s,method='omit_events');self.assertEqual(r['status'],'zero_model_gradient_not_stationarity_proof')
        self.assertEqual(r['decision']['reason'],'pathological_predicted_reduction_denominator')
    def test_sign_and_pure_event_counterexamples(self):
        j=self.base['total_gradient'];sm=self.base['smooth_gradient'];self.assertGreater(j[0],0);self.assertLess(sm[0],0)
        self.assertEqual(sm[5],0);self.assertLess(j[5],0)
        v0=self.base['value_estimate_s_m2'];vp=evaluate(0.,replace(self.s,target_shift_m=self.s.target_shift_m+1e-4))['value_s_m2'];vm=evaluate(0.,replace(self.s,target_shift_m=self.s.target_shift_m-1e-4))['value_s_m2']
        self.assertLess(vm,v0);self.assertLess(v0,vp)
    def test_exact_topology_clipping(self):
        self.assertEqual(certify_segment(self.s,replace(self.s,plate_shift_m=.2),[0.])['status'],'reject_topology_crossing_or_guard')
        candidate,info=clipped_candidate(self.s,[0.],[.2,0.]);self.assertLess(info['alpha'],1)
        self.assertEqual(info['certificate']['status'],'encoded_affine_segment_certified')
        self.assertTrue(all(F(g['minimum_margin_exact'])>0 for g in info['certificate']['guards']))
    def test_ties_and_endpoints_unknown(self):
        self.assertEqual(full_forward(replace(self.s,plate_shift_m=.08))['objective_status'],'unknown')
        # Solve lower event at t0 algebraically; guard covers float rounding.
        b=self.s.half_width_m+(self.s.x0_m+self.s.target_shift_m)*self.s.z_near_m/self.s.height_m
        self.assertEqual(full_forward(replace(self.s,plate_shift_m=b))['objective_status'],'unknown')
    def test_geometry_unknown_not_transparent(self):
        q=full_forward(replace(self.s,shadow_boundary_uncertainty_m=1e-4));self.assertEqual(q['geometry_status'],'unknown')
        self.assertIsNone(q['value_estimate_s_m2']);self.assertEqual(compare(q,q)['relation'],'unresolved')
    def test_overlap_not_ranked(self):self.assertEqual(compare(self.base,self.base)['relation'],'unresolved')
    def test_ratio_pathology(self):
        for d in [Interval(0.,0.),Interval(-.1,.1),Interval(1e-15,1e-15),Interval.unknown()]:
            self.assertEqual(reduction_ratio(self.base,self.tr['trial'],d.to_dict())['reason'],'pathological_predicted_reduction_denominator')
        for target in [0.,1e-12,-1.]:
            with self.assertRaises(ValueError):objective_interval(Interval.point(1),target)
    def test_nonplate_change_rejected(self):
        with self.assertRaises(ValueError):certify_segment(self.s,replace(self.s,height_m=1.01),[0.])
    def test_reverse_velocity_enclosure(self):
        s=replace(self.s,velocity_m_s=-.4,x0_m=.4);r=full_forward(s)
        self.assertEqual(r['objective_status'],'bounded_encoded_discrete_source')
        self.assertLessEqual(r['value_interval']['lo'],r['value_estimate_s_m2']);self.assertGreaterEqual(r['value_interval']['hi'],r['value_estimate_s_m2'])
    def test_refinement_is_nested(self):
        a,_=rational_forward_interval(self.s,[0.],[1.],4);b,_=rational_forward_interval(self.s,[0.],[1.],8)
        self.assertLessEqual(a.lo,b.lo);self.assertGreaterEqual(a.hi,b.hi)
    def test_cache_contract_sensitivity(self):
        common,design=common_contract(self.s,[0.],[1.],1.,64);key=digest({'contract':common,'design':design})
        variants=[]
        for fld in ('clock_offset_s','source_shift_m','z_near_m','event_guard_s'):
            c,d=common_contract(replace(self.s,**{fld:getattr(self.s,fld)+1e-5}),[0.],[1.],1.,64);variants.append(digest({'contract':c,'design':d}))
        for field,val in [('source_nodes_m',[.01]),('source_weights',[.9]),('units',{'length':'mm'}),('code_sha256',{'x':'changed'})]:
            c=copy.deepcopy(common);c[field]=val;variants.append(digest({'contract':c,'design':design}))
        self.assertTrue(all(x!=key for x in variants))
        a=copy.deepcopy(self.base);a['contract_signature']='changed'
        with self.assertRaises(ValueError):compare(self.base,a)
    def test_nonlinear_heuristic_counterexample(self):self.assertLess(1-.8-4*.8**2,0)
    def test_encoded_positive_rate_guard(self):
        s=replace(self.s,q0=0.,q1_per_s=-1.)
        with self.assertRaises(ValueError):full_forward(s)

if __name__=='__main__':unittest.main()
