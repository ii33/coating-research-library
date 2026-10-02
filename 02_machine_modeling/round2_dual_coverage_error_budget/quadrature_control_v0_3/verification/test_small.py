"""Small API/analytic tests only; never executes device workload."""
from pathlib import Path
import sys,math,unittest,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'models'))
import shadow_integral as s
import device_driver as d
import run_control as r

class SmallTests(unittest.TestCase):
    def test_admitted_points(self):
        for p in [[.061,0,0],[0,0,.001],[math.nan,0,0],[0,0]]:
            with self.assertRaises(ValueError):s.Model(p,'vapor')
    def test_bad_channel(self):
        with self.assertRaises(ValueError):s.Model([0,0,0],'other')
    def test_bad_support_controls(self):
        m=s.Model([0,0,0],'vapor')
        for a,b,e in [(0,1,0),(1,0,1e-5),(0,8,1e-5)]:
            with self.assertRaises(ValueError):m.support_intervals(a,b,e)
    def test_hull(self):
        p=s.hull([(0,0),(1,0),(1,1),(0,1),(.5,.5)])
        self.assertEqual(len(p),4);self.assertGreater(np.sum(s.cross2(p,np.roll(p,-1,axis=0))),0)
    def test_rate_contract(self):
        for cfg in [{'kind':'constant','value':-1},{'kind':'sinusoid','frequency_hz':1,'amplitude':2},{'kind':'unknown'}]:
            with self.assertRaises(ValueError):d.Rate(cfg)
    def test_rate_zero_not_positive(self):
        self.assertFalse(d.Rate({'kind':'constant','value':0}).strict_positive)
        self.assertFalse(d.Rate({'kind':'sinusoid','frequency_hz':1,'amplitude':1}).strict_positive)
    def test_bandwidth_splitting(self):
        rate=d.Rate({'kind':'sinusoid','frequency_hz':1016,'amplitude':.8})
        p=rate.split_points(0,.01,.25)
        self.assertLessEqual(max(np.diff(p)),1/(8*1016)+1e-15)
    def test_rate_knots(self):
        rate=d.Rate({'kind':'piecewise_linear','times_s':[0,1.234,7.3],'values':[1,2,1]})
        self.assertIn(1.234,rate.split_points(0,7.3,1));self.assertEqual(rate(1.234),2)
    def test_duration_unknown_propagation(self):
        v={'visible':[[.55,3]],'covered':[[3,6]],'unknown':[[6,6.55]]};i={'visible':[[0,7.3]],'covered':[],'unknown':[]}
        z=r.duration_enclosure(v,i);self.assertAlmostEqual(z['lower_s'],4.3);self.assertAlmostEqual(z['upper_s'],4.85)
    def test_work_stop(self):
        b=s.Budget(limit=1)
        with self.assertRaises(RuntimeError):b.add('ray_evaluations',2)
    def test_small_evidence(self):
        q=json.loads((ROOT/'data/small_checks.json').read_text());x=q['A_support']['2']['duration']
        self.assertLess(x['width_ms'],.1);self.assertLess(x['upper_s'],1.365)
        self.assertEqual(q['C']['v02_nominal'],'blocked');self.assertEqual(q['C']['with_local_margin_1e_14'],'unknown')
    def test_source_kernel_unmasked_reference(self):
        import legacy_adapter as legacy
        for ch in ['vapor','ion']:
            model=s.Model([0,0,0],ch)
            self.assertLess(model.cover_slack(2.),-2*model.a)
            src=legacy.emitter(model.c,ch,8,64)
            x,n=legacy.pose(model.c,np.array([2.]),[[0,0,0]])
            reference=float(legacy.t02.transfer_kernel(x,n,src)[0,0])
            value=model.source_flux(2.,2e-10,2e-9)
            self.assertLess(abs(value-reference)/reference,1e-7)
    def test_device_outer_wrapper_analytic(self):
        class Dummy:
            c={'clock':{'vapor_gate_s':[0.,1.]}}
            channel='vapor';source_calls=0;max_source_abserr=0.;source_quad_warnings=[];Qtotal=1.
            def source_flux(self,t,*args):self.source_calls+=1;return 1+t*t
        control={'max_time_panel_s':.25,'time_epsabs_s_m2':1e-9,'time_epsrel':1e-9,'source_epsabs_m2':1e-9,'source_epsrel':1e-9,'source_limit':20,'time_limit':20}
        z=d.reference(Dummy(),control,d.Rate({'kind':'constant','value':1.}),[])
        self.assertAlmostEqual(z['integral_SI'],4/3);self.assertEqual(z['warning_count'],0)
    def test_device_plan_only(self):
        c=json.loads((ROOT/'verification/device_validation_plan.json').read_text());self.assertEqual(len(d.select_points(c)),2)
        c['point_set']='area_236';self.assertEqual(len(d.select_points(c)),236)
if __name__=='__main__':unittest.main()
