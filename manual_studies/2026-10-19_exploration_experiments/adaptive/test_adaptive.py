import hashlib, json, unittest
from pathlib import Path
import numpy as np
import run_adaptive as a

class AdaptiveTests(unittest.TestCase):
    def test_vendor_kernel_unchanged(self):
        provenance=json.loads((a.ROOT/'kernel/provenance.json').read_text())
        self.assertEqual(hashlib.sha256(a.KERNEL.read_bytes()).hexdigest(),provenance['sha256'])
    def test_lossless_kernel(self):
        d,n=a.cavity(1.0037)
        r,t=a.tmm_normal(np.linspace(*a.BAND,301),d,n,1.,1.)
        self.assertLess(np.max(abs(r+t-1)),1e-11)
    def test_baseline_grids_distinct_unique(self):
        x=a.fixed_samples(3,5,13);y=a.fixed_samples(3,5,13,True)
        self.assertEqual(len(np.unique(x)),13);self.assertEqual(len(np.unique(y)),13)
        self.assertFalse(np.array_equal(np.sort(x),np.sort(y)))
        self.assertEqual(min(y),3);self.assertEqual(max(y),5)
    def test_adaptive_exact_work_and_hidden_peak(self):
        d,n=a.cavity(1.0037);m=a.Meter(d,n)
        a.adaptive(m,*a.BAND,129)
        self.assertEqual(m.points,129);self.assertEqual(m.summary()['layer_point_work'],129*33)
        self.assertGreater(m.summary()['sampled_max'],.9999)
        self.assertLess(a.tmm_normal(np.linspace(*a.BAND,129),d,n,1.,1.)[1].max(),.5)
    def test_ultranarrow_failure_is_retained(self):
        d,n=a.cavity(.98713,16,100);m=a.Meter(d,n);a.adaptive(m,*a.BAND,129)
        ref=a.reference(d,n,[a.BAND],points=16385)
        self.assertLess(m.summary()['sampled_max'],.5)
        self.assertGreater(ref['max'],.999)
    def test_response_repeatability(self):
        d,n=a.cavity(1.0037);x=a.Meter(d,n);y=a.Meter(d,n)
        a.adaptive(x,*a.BAND,129);a.adaptive(y,*a.BAND,129)
        np.testing.assert_array_equal(x.w,y.w);np.testing.assert_array_equal(x.y,y.y)
    def test_completed_records_exact_design_work(self):
        data=json.loads((a.ROOT/'results.json').read_text())
        self.assertEqual(len(data['design_rows']),12)
        for r in data['design_rows']:
            self.assertEqual(r['physical_points'],40000)
            self.assertEqual(r['layer_point_work'],240000)
            self.assertTrue(all(.005<=v<=2.5 for v in r['final_thickness_um']))
        for r in data['detection_rows']:
            self.assertEqual(r['physical_points'],17 if r['method']=='sparse17' else 129)
    def test_history_reset_for_independent_candidates(self):
        data=json.loads((a.ROOT/'results.json').read_text())
        for group in ['engineered_hidden_resonance','ultranarrow_stress','clean_stopband_pass']:
            cold=[r['sampled_max'] for r in data['detection_rows'] if r['group']==group and r['method']=='adaptive129']
            warm=[r['sampled_max'] for r in data['detection_rows'] if r['group']==group and r['method']=='tracked_adaptive129']
            self.assertEqual(cold,warm)
if __name__=='__main__':unittest.main()
