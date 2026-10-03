import unittest,json,copy,math,subprocess,sys
from pathlib import Path
from exact_intervals import I,C,PI,F,trig,phase
from bounded_optics import *
class ArithmeticTests(unittest.TestCase):
    def test_pi(self):self.assertLess(PI.lo,F('3.141592653589793238462644'));self.assertGreater(PI.hi,F('3.141592653589793238462643'))
    def test_add_enclosure(self):self.assertTrue((I('0.1')+I('0.2')).lo<=F('0.3')<=(I('0.1')+I('0.2')).hi)
    def test_mul_crossing(self):self.assertEqual((I(-2,3)*I(-4,5)).floats(),[-12.,15.])
    def test_div_zero(self):
        with self.assertRaises(ZeroDivisionError):I(1)/I(-1,1)
    def test_square_zero(self):self.assertEqual(I(-2,1).sq().floats(),[0.,4.])
    def test_sin_pi(self):self.assertTrue(trig(PI).lo<=0<=trig(PI).hi)
    def test_cos_zero(self):self.assertTrue(trig(I(0),True).lo<=1<=trig(I(0),True).hi)
    def test_wide_trig(self):self.assertEqual(trig(I(-100,100)).floats(),[-1.,1.])
    def test_complex(self):self.assertTrue((C(1,1)/C(1,-1)).im.lo<=1<=(C(1,1)/C(1,-1)).im.hi)
    def test_outward_float(self):
        x=I(F(1,3));a,b=x.floats();self.assertLessEqual(F(a),x.lo);self.assertGreaterEqual(F(b),x.hi)
    def test_reversed(self):
        with self.assertRaises(ValueError):I(2,1)
    def test_nan(self):
        with self.assertRaises(ValueError):I(float('nan'))
class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=load_case();cls.recipes=json.loads((ROOT/'data/legacy_selection.json').read_text())['records'];cls.r=cls.recipes[0]
    def test_dependency_copies(self):self.assertGreater(verify_dependencies(),40)
    def test_full_response_not_point(self):
        b=self.c['bridge']['t04_response'];self.assertLess(*b['signed_thickness_change_m']);self.assertIn('upstream_full_forward',b);self.assertEqual(len(b['response_contract_sha256']),64)
    def test_positive_gate(self):self.assertEqual(source_gate(self.c['bridge'],self.c['material'])['status'],'conditional_synthetic_only')
    def test_negative(self):
        b=copy.deepcopy(self.c['bridge']);b['status']='negative_net';self.assertIsNone(source_gate(b,self.c['material'])['bounds'])
    def test_crossing(self):
        b=copy.deepcopy(self.c['bridge']);b['status']='zero_or_crossing_net';self.assertIsNone(source_gate(b,self.c['material'])['bounds'])
    def test_inventory(self):
        b=copy.deepcopy(self.c['bridge']);b['status']='inventory_unresolved';self.assertIsNone(source_gate(b,self.c['material'])['bounds'])
    def test_near_zero(self):
        b=copy.deepcopy(self.c['bridge']);b['status']='ill_conditioned_net';self.assertIsNone(source_gate(b,self.c['material'])['bounds'])
    def test_nonlambert(self):
        b=copy.deepcopy(self.c['bridge']);b['status']='unsupported_non_lambert_frozen_bridge';self.assertIsNone(source_gate(b,self.c['material'])['bounds'])
    def test_unknown(self):
        b=copy.deepcopy(self.c['bridge']);b['status']='unknown_source_angular_law';self.assertIsNone(source_gate(b,self.c['material'])['bounds'])
    def test_tamper_full_forward(self):
        b=copy.deepcopy(self.c['bridge']);b['t04_response']['signed_thickness_change_m']=[1e-6,1e-6];self.assertEqual(source_gate(b,self.c['material'])['status'],'unbound_or_modified_full_forward_payload')
    def test_point_only(self):
        self.assertIsNone(source_gate({'status':'point_only','height_estimate_m':1e-6},self.c['material'])['bounds'])
    def test_density_qcm_bulk(self):
        for basis in ['qcm_setting','bulk_reference',None]:
            m=copy.deepcopy(self.c['material']);m['density_basis']=basis;self.assertIsNone(source_gate(self.c['bridge'],m)['bounds'])
    def test_nk_measured_claim(self):
        m=copy.deepcopy(self.c['material']);m['nk_basis']='measured';self.assertIsNone(source_gate(self.c['bridge'],m)['bounds'])
    def test_sample_mismatch(self):
        m=copy.deepcopy(self.c['material']);m['nk_sample_state_id']='different';self.assertIsNone(source_gate(self.c['bridge'],m)['bounds'])
    def test_finite_backside(self):
        op=copy.deepcopy(self.c['measurement']);op['substrate_mode']='finite'
        with self.assertRaises(ValueError):validate_operator(op)
    def test_angle(self):
        op=copy.deepcopy(self.c['measurement']);op['aoi_deg']=45
        with self.assertRaises(ValueError):validate_operator(op)
    def test_bandwidth_edge(self):
        op=copy.deepcopy(self.c['measurement']);op['wavelength_um'][0]='4.24'
        with self.assertRaises(ValueError):validate_operator(op)
    def test_scatter(self):
        op=copy.deepcopy(self.c['measurement']);op['scatter']='unknown'
        with self.assertRaises(ValueError):validate_operator(op)
    def test_weights(self):
        op=copy.deepcopy(self.c['measurement']);op['weights']=['1','1','1']
        with self.assertRaises(ValueError):validate_operator(op)
    def test_order_and_units(self):
        n,d,order=incident_stack(self.r);self.assertEqual(order,[6,5,4,3,2,1]);self.assertEqual(d[0],F(self.r['layers'][-1]['thickness_nm'])/1000)
    def test_bare_interface(self):
        r=reflectance([1,4],[],'4.26');self.assertTrue(r.lo<=F(9,25)<=r.hi)
    def test_quarterwave_interior_not_corners(self):
        m=reflectance([1,2,4],[I('0.5')],2*2);l=reflectance([1,2,4],[I('0.45')],4);h=reflectance([1,2,4],[I('0.55')],4)
        self.assertLess(float(m.hi),1e-20);self.assertGreater(float(l.lo),.001);self.assertGreater(float(h.lo),.001)
    def test_shared_ratio_not_independent(self):
        z=I('.99','1.01');a=I(1)*z;b=I(2)*z;independent=a/b
        self.assertLess(independent.lo,F(1,2));self.assertGreater(independent.hi,F(1,2));self.assertEqual(F(1,2),F(1)/2)
    def test_subdivision_cover(self):
        x=I('.98','1.02');cells=split_interval(x,7);self.assertLessEqual(cells[0].lo,x.lo);self.assertGreaterEqual(cells[-1].hi,x.hi)
        for a,b in zip(cells,cells[1:]):self.assertGreaterEqual(a.hi,b.lo)
    def test_contract_incomparable(self):self.assertEqual(distinguish({'response_contract_sha256':'a'},{'response_contract_sha256':'b'},0)['status'],'incomparable_contracts')
    def test_driver_default_plan_only(self):
        out=subprocess.check_output([sys.executable,str(ROOT/'models/validation_driver.py')],text=True);self.assertEqual(json.loads(out)['mode'],'plan_only')
    def test_tiny_results(self):
        x=json.loads((ROOT/'verification/tiny_results.json').read_text());self.assertEqual(x['A_vs_B']['status'],'distinguishable_under_declared_error');self.assertEqual(x['A_vs_C']['status'],'unresolved_overlap_not_proof_of_equivalence');self.assertLess(x['outcomes']['A']['R_bounds'][1],.05)
if __name__=='__main__':unittest.main()
