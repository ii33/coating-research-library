import hashlib,json,unittest
from pathlib import Path
import numpy as np
import run_batched as b
class BatchedTests(unittest.TestCase):
    def test_provenance_hashes(self):
        p=json.loads((b.ROOT/'kernel/provenance.json').read_text())
        for f,r in p['files'].items():self.assertEqual(hashlib.sha256((b.ROOT/f).read_bytes()).hexdigest(),r['sha256'])
    def test_exact_budget_unique(self):
        for k in [1,2]:
            d,n=b.p.cavity(1.0037);m=b.Meter(d,n);b.batched(m,129,k)
            self.assertEqual(m.points,129);self.assertEqual(len(np.unique(m.w)),129)
            self.assertEqual(m.summary()['layer_point_work'],129*33)
            self.assertEqual(m.batch_sizes,[17]+[16]*7)
    def test_detection_no_reference_input(self):
        d,n=b.p.cavity(1.0037)
        for k in [1,2]:
            m=b.Meter(d,n);b.batched(m,129,k);self.assertGreater(m.summary()['sampled_max'],.5)
    def test_deterministic_and_control(self):
        d,n=b.p.cavity(.9917)
        for k in [1,2]:
            x=b.Meter(d,n);y=b.Meter(d,n);b.batched(x,129,k);b.batched(y,129,k)
            np.testing.assert_array_equal(x.w,y.w);np.testing.assert_array_equal(x.y,y.y)
    def test_independent_reference_scaled_coordinate(self):
        d,n=b.p.cavity(1.0037,16,100);r=b.p.reference(d,n,[b.BAND],points=16385)
        self.assertGreater(r['max'],.999);self.assertLess(r['meter']['matrix_recursion_R_max_abs_error'],1e-9)
        self.assertEqual(r['meter']['physical_points']>32768,True)
    def test_controls(self):
        n=np.array([2.35,1.45]*16);d=1/(4*n)
        for name in b.METHODS:
            m=b.Meter(d,n);b.run_method(name,m);self.assertLess(m.summary()['sampled_max'],.5)
    def test_completed_rows_and_layers(self):
        r=json.loads((b.ROOT/'results.json').read_text());self.assertEqual(len(r['references']),47)
        self.assertEqual(len(r['fixed_rows']),47*5)
        for row in r['fixed_rows']:self.assertEqual(row['physical_points'],129);self.assertEqual(row['layer_point_work'],129*row['layers'])
        for c in r['references']:self.assertEqual(len(c['d']),len(c['n']))
        for row in r['wall_rows']:self.assertGreaterEqual(row['total_wall_s'],row['wall_cap_s']);self.assertFalse(row['false_alarm'])
    def test_reference_not_contaminating(self):
        for c in b.make_cases():self.assertNotIn('reference',c)
        for name in b.METHODS:
            d,n=b.p.cavity(.995);m=b.Meter(d,n);b.run_method(name,m);self.assertEqual(m.points,129)
    def test_scaled_scalar_diagnostic(self):
        import diagnose_scaled_scalar as d
        data=json.loads((b.ROOT/'scaled_scalar_diagnostic.json').read_text())
        fixed=[r for r in data['rows'] if r['mode']=='points129']
        for row in fixed:
            self.assertEqual(row['physical_points'],129)
            self.assertEqual(row['layer_point_work'],129*65)
        corrected=[r for r in fixed if r['method']=='scalar_scaled']
        self.assertEqual(sum(r['false_pass'] for r in corrected),0)
        self.assertEqual(len(corrected),15)
        ds,nn=b.p.cavity(.98713,16,100);m=b.Meter(ds,nn);d.scalar_scaled(m,*b.BAND,129)
        self.assertGreater(m.summary()['sampled_max'],.5)
    def test_grid_distinct(self):
        a=b.samples(*b.BAND,129);c=b.samples(*b.BAND,129,True)
        self.assertEqual(len(np.unique(a)),129);self.assertEqual(len(np.unique(c)),129);self.assertFalse(np.array_equal(a,np.sort(c)))
if __name__=='__main__':unittest.main()
