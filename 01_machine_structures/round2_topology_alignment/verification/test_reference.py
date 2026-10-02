import sys, unittest, math
from pathlib import Path
from copy import deepcopy
from fractions import Fraction
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'models'))
import dual_coverage as m

class ReferenceTests(unittest.TestCase):
    def setUp(self): self.c=m.load_config()
    def test_direct_contact(self):
        r=m.rates(self.c,'D'); self.assertEqual(120*(r['sun']-r['carrier'])+36*(r['output']-r['carrier']),0)
    def test_compound_three_constraints(self):
        r=m.rates(self.c,'C');c=r['carrier'];b=r['compound'];i=r['input'];w=r['output']
        self.assertEqual(160*(0-c)-32*(b-c),0)
        self.assertEqual(88*(i-c)+40*(b-c),0)
        self.assertEqual(32*(b-c)+64*(w-c),0)
    def test_signed_ratios(self):
        for k,q in [('D',Fraction(13,3)),('C',Fraction(7,2)),('I',Fraction(-7,5))]:
            r=m.rates(self.c,k);self.assertEqual(r['output']/r['carrier'],q)
    def test_compound_geometry(self):
        p=self.c['topologies']['C'];mod=p['module_m'];R=self.c['geometry']['orbit_radius_m']
        b=mod*(p['ring_teeth']-p['lower_teeth'])/2
        self.assertEqual(b,mod*(p['input_teeth']+p['upper_teeth'])/2)
        d=mod*(p['lower_teeth']+p['output_teeth'])/2
        xb=(R*R+b*b-d*d)/(2*R);yb=math.sqrt(b*b-xb*xb)
        self.assertAlmostEqual(math.hypot(xb-R,yb),d)
        self.assertLess(R+mod*p['output_teeth']/2,mod*p['ring_teeth']/2)
    def test_direct_standard_geometry(self):
        self.assertAlmostEqual(.004*(120+36)/2,self.c['geometry']['orbit_radius_m'])
    def test_rational_closure(self):
        for k,T in [('D',12),('C',8),('I',20)]:
            r=m.rates(self.c,k);self.assertEqual(m.rational_period([r['carrier'],r['output']]),T)
        self.assertEqual(m.rational_period(m.rates(self.c,'C').values()),88)
    def test_historical_37(self):
        self.c['topologies']['D']['planet_teeth']=37
        r=m.rates(self.c,'D');self.assertEqual(r['output']*60,Fraction(2355,37));self.assertEqual(m.rational_period([r['carrier'],r['output']]),148)
    def test_paper_decimal_closure(self):
        self.assertEqual([m.rational_period([1,Fraction(x)]) for x in ['.80','.82','.83','.86','.87','-.086']],list(map(Fraction,[5,50,100,50,100,500])))
    def test_stationary_limit(self):
        self.c['geometry']['carrier_rps']='0'
        for k in ('D','C'): self.assertTrue(all(v==0 for v in m.rates(self.c,k).values()))
        self.assertIsNone(m.rational_period([0,0]))
        self.assertEqual(m.rates(self.c,'I')['output'],Fraction(-7,20))
    def test_pose_closure_marked_point_normal(self):
        for k,T in [('D',12),('C',8),('I',20)]:
            x,n=m.pose(self.c,k,[.31,.31+T],[[.04,.01,0]],[[.6,0,-.8]])
            np.testing.assert_allclose(x[0],x[1],atol=1e-13);np.testing.assert_allclose(n[0],n[1],atol=1e-13)
    def test_local_radius_and_normal(self):
        t=np.linspace(0,7.3,101);x,n=m.pose(self.c,'D',t,[[.04,.03,0]],[[.6,0,-.8]])
        c,_=m.pose(self.c,'D',t,[[0,0,0]])
        np.testing.assert_allclose(np.linalg.norm(x-c,axis=-1),.05,atol=1e-14)
        np.testing.assert_allclose(np.linalg.norm(n,axis=-1),1,atol=1e-14)
    def test_rigid_invariance_both_channels_all_cases(self):
        ang=.53;Q=np.array([[math.cos(ang),0,math.sin(ang)],[0,1,0],[-math.sin(ang),0,math.cos(ang)]])
        a=np.array([.31,-.18,.42]);c2=m.transformed_scene(self.c,Q,a)
        t=np.linspace(.61,6.4,39);x,n=m.pose(self.c,'I',t,[[.02,.01,0],[.04,-.01,0]])
        for case in self.c['cases']:
            old=m.flux_at(self.c,t,x,n,case);new=m.flux_at(c2,t,x@Q.T+a,n@Q.T,case)
            np.testing.assert_allclose(new[0],old[0],rtol=1e-13,atol=1e4)
            np.testing.assert_allclose(new[1],old[1],rtol=1e-13,atol=1e3)
            np.testing.assert_array_equal(new[2],old[2])
    def test_backside_and_grazing(self):
        x=np.array([[[0,0,.6]]]);t=[1.0]
        gv,gi,_=m.flux_at(self.c,t,x,np.array([[[0,0,1]]]),'none')
        self.assertEqual(gv.item(),0);self.assertEqual(gi.item(),0)
        gv,gi,_=m.flux_at(self.c,t,x,np.array([[[0,1,0]]]),'none')
        self.assertEqual(gi.item(),0)
    def test_exact_flux_scales(self):
        t=[1.];x=np.array([[self.c['vapor']['position_L_m']]])+np.array([0,0,.6]);n=np.array([[[0,0,-1]]])
        gv,_,_=m.flux_at(self.c,t,x,n,'none');self.assertAlmostEqual(gv.item()/2e19,1.)
        d=np.array(self.c['ion']['direction_L']);si=np.array(self.c['ion']['origin_L_m'])
        x=np.array([[si+d]])
        _,gi,_=m.flux_at(self.c,t,x,np.array([[-d]]),'none');self.assertAlmostEqual(gi.item()/2e18,1.)
    def test_thin_plate_intersection(self):
        p=self.c['plates']['vapor_plate'];center=np.array(p['origin_L_m'])
        self.assertTrue(m.blocked(center-[0,0,1],center+[0,0,1],p))
        self.assertFalse(m.blocked(center-[1,0,0],center+[1,0,0],p))
        self.assertFalse(m.blocked(center+[0,0,1],center+[0,0,2],p))
    def test_physical_channel_selectivity(self):
        pts,_=m.diagnostic_grid(.06);t=np.linspace(.56,6.54,1001)
        n=m.fields(self.c,'D',t,pts,'none');v=m.fields(self.c,'D',t,pts,'vapor_only');i=m.fields(self.c,'D',t,pts,'ion_only')
        np.testing.assert_array_equal(v[:,:,1],n[:,:,1]);np.testing.assert_array_equal(i[:,:,0],n[:,:,0])
        self.assertTrue(np.any(v[:,:,0]==0));self.assertTrue(np.any(i[:,:,1]==0))
    def test_area_weights_and_r_squared(self):
        pts,w=m.disk_grid(.06,12,48,72)
        self.assertAlmostEqual(w.sum(),1.);self.assertAlmostEqual(w@(pts[:,0]**2+pts[:,1]**2),.06**2/2)
    def test_zero_denominator_refused(self):
        out=m.output_values(self.c,np.array([[0,1,1,1],[-1,1,1,1],[2,1,1,1]]))
        self.assertTrue(np.isnan(out['ion_to_net_atom_ratio'][0]));self.assertTrue(np.isnan(out['ion_to_net_atom_ratio'][1]))
        self.assertEqual(out['ion_to_net_atom_ratio'][2],.5)
    def test_ratio_of_integrals_not_average_ratios(self):
        out=m.output_values(self.c,np.array([[4,4,4*100*m.E_CHARGE,1.]]))
        self.assertEqual(out['ion_to_net_atom_ratio'][0],1.);self.assertEqual(out['eV_per_net_atom'][0],100.)
    def test_constant_field_analytic_and_ion_alone(self):
        r=m.EventIntegrator(self.c,'D').integrate(np.array([[0,0,0]]),cases=['none'],uniform_vapor=True)['none'][0]
        self.assertAlmostEqual(r[0]/2e19,6.,places=10);self.assertAlmostEqual(r[3],1.3,places=9)
    def test_zero_deposition_integral(self):
        self.c['clock']['vapor_gate_s']=[8,9]
        r=m.EventIntegrator(self.c,'D').integrate(np.array([[0,0,0]]),cases=['none'])['none'][0]
        self.assertEqual(r[0],0);self.assertGreater(r[1],0);self.assertAlmostEqual(r[3],7.3,places=9)
    def test_uniform_parallel_vapor_uses_its_own_ray(self):
        p=np.array([[-.0295,.0510954988,0.]])
        x,n=m.pose(self.c,'D',[2.],p)
        gv,_,_=m.flux_at(self.c,[2.],x,n,'ion_only',uniform_vapor=True)
        self.assertEqual(gv.item(),0.)
        with self.assertRaises(NotImplementedError):
            m.EventIntegrator(self.c,'D').integrate(p,cases=['ion_only'],uniform_vapor=True)
    def test_stationary_exact_edge_event_solver(self):
        self.c['geometry']['carrier_rps']='0'
        ei=m.EventIntegrator(self.c,'D')
        e=ei.point_events(np.array([.023,0,0]));self.assertLessEqual(len(e),4)
        val=ei.integrate(np.array([[.023,0,0]]),cases=['vapor_only'])['vapor_only']
        self.assertTrue(np.isfinite(val).all())
    def test_event_solver_against_independent_midpoint(self):
        pts=np.array([[.03,.02,0]]);ref=m.EventIntegrator(self.c,'C').integrate(pts)
        mid=m.midpoint(self.c,'C',pts,32771)
        for case in ref:
            np.testing.assert_allclose(mid[case][0,:3],ref[case][0,:3],rtol=3e-3)
            self.assertLess(abs(mid[case][0,3]-ref[case][0,3]),3e-3)

if __name__=='__main__': unittest.main(verbosity=2)
