import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'models'))
import dual_finite as m
class Reference(unittest.TestCase):
    def test_frozen_hashes(self):
        import hashlib,json
        for p,h in json.loads((m.ROOT/'data/frozen_dependencies.json').read_text()).items():
            self.assertEqual(hashlib.sha256((m.ROOT/p).read_bytes()).hexdigest(),h,p)
    def test_direct_only(self):
        c=m.config();c['topologies']['C']={}
        with self.assertRaises(ValueError):m.pose(c,[0],[[0,0,0]])
    def test_unit_normals(self):
        with self.assertRaises(ValueError):m.pose(m.config(),[0],[[0,0,0]],[[0,0,-2]])
    def test_disk_analytic(self):
        H=.6;a=.12;src=m.t02.disk_source(a,8,32)
        flux=m.t02.transfer_kernel([[0,0,H]],[[0,0,-1]],src)[0]
        self.assertAlmostEqual(flux*np.pi*(H*H+a*a),1,places=10)
    def test_half_disk_thin(self):
        src=m.t02.disk_source(.12,8,32);b=m.t02.RectangleMask([1,0,.3],np.eye(3),1,2)
        full=m.t02.transfer_kernel([[0,0,.6]],[[0,0,-1]],src)[0]
        half=m.t02.transfer_kernel([[0,0,.6]],[[0,0,-1]],src,[b])[0]
        self.assertAlmostEqual(half/full,.5,places=12)
    def test_zero_radius_limit(self):
        s=m.t02.disk_source(1e-6,3,12);p=m.t02.point_source()
        a=m.t02.transfer_kernel([[.2,0,.6]],[[0,0,-1]],s)
        b=m.t02.transfer_kernel([[.2,0,.6]],[[0,0,-1]],p)
        self.assertLess(abs(a/b-1)[0],1e-7)
    def test_zero_weight_coincidence(self):
        s=m.t02.Source(np.array([[0,0,0],[0,0,1]]),np.array([[0,0,1]]*2),np.array([1.,0.]))
        self.assertTrue(np.isfinite(m.t02.transfer_kernel([[0,0,1]],[[0,0,-1]],s)).all())
    def test_active_coincidence_rejected(self):
        with self.assertRaises(ValueError):m.t02.transfer_kernel([[0,0,0]],[[0,0,-1]],m.t02.point_source())
    def test_backside_zero(self):
        s=m.t02.point_source(exponent=0)
        self.assertEqual(m.t02.transfer_kernel([[0,0,-1]],[[0,0,1]],s)[0],0)
    def test_projection_once(self):
        s=m.t02.point_source();x=np.array([[0,0,1.]])
        f=m.t02.transfer_kernel(x,[[0,0,-1]],s)[0]
        g=m.t02.transfer_kernel(x,[[.8,0,-.6]],s)[0]
        self.assertAlmostEqual(g/f,.6)
    def test_sidewall(self):
        thick=m.t02.RectangleMask([0,0,0],np.eye(3),1,1,.2)
        thin=m.t02.RectangleMask([0,0,0],np.eye(3),1,1,0)
        a=np.array([-.9,0,-.2]);b=np.array([3.1,0,.2])
        self.assertTrue(thick.blocked(a,b));self.assertFalse(thin.blocked(a,b))
    def test_open_endpoints(self):
        b=m.t02.RectangleMask([0,0,0],np.eye(3),1,1,.2)
        self.assertFalse(b.blocked([0,0,.1],[0,0,1]))
        self.assertTrue(b.blocked([0,0,.1],[0,0,0]))
    def test_grazing_convention(self):
        b=m.t02.RectangleMask([0,0,0],np.eye(3),1,1,.2)
        self.assertTrue(b.blocked([-2,1,0],[2,1,0]))
        self.assertFalse(b.blocked([-2,1+1e-12,0],[2,1+1e-12,0]))
        thin=m.t02.RectangleMask([0,0,0],np.eye(3),1,1,0)
        self.assertFalse(thin.blocked([-2,0,0],[2,0,0]))
    def test_union_not_double_loss(self):
        s=m.t02.disk_source(.1,3,16);b=m.t02.RectangleMask([.5,0,.3],np.eye(3),.5,1,.01)
        a=m.t02.transfer_kernel([[0,0,.6]],[[0,0,-1]],s,[b])
        c=m.t02.transfer_kernel([[0,0,.6]],[[0,0,-1]],s,[b,b])
        np.testing.assert_array_equal(a,c)
    def test_area_weights(self):
        p,w=m.grid(1);self.assertAlmostEqual(w.sum(),1);self.assertEqual(sum(w==0),34)
    def test_zero_ratio(self):
        out=m.t01.output_values(m.config(),np.array([[0,1,1,1.]]))
        self.assertTrue(np.isnan(out['ion_to_net_atom_ratio'][0]))
    def test_zero_compare(self):
        z=np.zeros((2,4));self.assertEqual(m.compare(z,z)['max_relative_integral_difference'],0)
        a=z.copy();a[0,0]=1;self.assertTrue(np.isinf(m.compare(a,z)['max_relative_integral_difference']))
    def test_zero_statistics_compare(self):
        z=m.metrics(m.config(),np.zeros((2,4)),np.ones(2)/2)
        self.assertEqual(z['ion_to_net_atom_ratio']['finite_area_fraction'],0)
        self.assertTrue(np.isinf(m.stats_compare(z,z)['mean_relative']))
    def test_shared_time_gate(self):
        c=m.config();t,w=m.t02.time_quadrature(0,7.3,127,1,c['clock']['vapor_gate_s'])
        gate=(t>=.55)&(t<6.55);self.assertAlmostEqual(w[gate].sum(),6.)
    def test_finite_source_differs(self):
        c=m.config();v=m.emitter(c,'vapor',2,7);i=m.emitter(c,'ion',2,7)
        self.assertFalse(np.allclose(v.positions_m,i.positions_m));self.assertNotEqual(v.exponent,i.exponent)
if __name__=='__main__':unittest.main()
