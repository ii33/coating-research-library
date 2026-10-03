from pathlib import Path
import dataclasses,json,math,sys,tempfile,unittest
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'models'))
from event_reference import *
from analytic_oracle import exact_value_gradient
from offline_read import load
from device_driver import read_plan,estimate,run
from frozen.t01_pose_reference import exp_so3

class SmallChecks(unittest.TestCase):
    def test_event_primitive_jacobian(self):
        sc=Scene();r=evaluate(0.,sc);v,j=exact_value_gradient(sc)
        self.assertAlmostEqual(v,r['value_s_m2'],places=13);np.testing.assert_allclose(r['gradient'],j,atol=2e-12,rtol=2e-12)
    def test_negative_velocity(self):
        sc=dataclasses.replace(Scene(),x0_m=.4,velocity_m_s=-.4);r=evaluate(0.,sc);v,j=exact_value_gradient(sc)
        self.assertAlmostEqual(v,r['value_s_m2'],places=13);np.testing.assert_allclose(r['gradient'],j,atol=2e-12)
    def test_far_source_active_face(self):
        sc=Scene();r=evaluate(.3,sc);v,j=exact_value_gradient(sc,.3)
        np.testing.assert_allclose(r['gradient'],j,atol=3e-12);self.assertNotEqual(r['events'][0]['active_z_m'],r['events'][1]['active_z_m'])
    def test_event_signs(self):
        sc=Scene();r=evaluate(0.,sc);self.assertEqual([e['jump_V'] for e in r['events']],[-1,1])
        self.assertLess(r['event_gradient'][5],0.)
    def test_event_contribution_nonzero(self):
        r=evaluate(0.,Scene());self.assertGreater(abs(r['event_gradient'][0]),.1)
        self.assertGreater(np.max(np.abs(np.array(r['gradient'])-r['smooth_gradient'])),1.)
    def test_primitive_unit_integral(self):
        sc=dataclasses.replace(Scene(),q1_per_s=0.)
        n,w=np.polynomial.legendre.leggauss(64);t=(n+1)
        self.assertAlmostEqual(integral(0,2,0,sc),float(w@rate_kernel(t,0,sc)),places=13)
    def test_no_events_inside(self):
        sc=dataclasses.replace(Scene(),target_shift_m=2.);r=evaluate(0.,sc);v,j=exact_value_gradient(sc)
        np.testing.assert_allclose(r['event_gradient'],0.,atol=0);np.testing.assert_allclose(r['gradient'],j,atol=2e-12)
    def test_fully_blocked(self):
        sc=dataclasses.replace(Scene(),half_width_m=2.);r=evaluate(0.,sc)
        self.assertEqual(r['value_s_m2'],0.);np.testing.assert_array_equal(r['gradient'],np.zeros(7))
    def test_nominal_rational_visibility(self):
        sc=Scene();r=evaluate(0.,sc)
        # 41 generic rays, not a random/large benchmark; avoid exact event coordinates.
        for t in np.linspace(.001,1.999,41):
            clear=any(a<t<b for a,b in r['visible_intervals_s']);verdict=classify_ray(t,0.,sc).verdict
            self.assertEqual(verdict,Verdict.CLEAR if clear else Verdict.BLOCKED)
    def test_rational_near_boundary_unknown(self):
        sc=Scene();te=event_map(0.,sc)['events'][0]['time_s']
        self.assertEqual(classify_ray(te,0.,sc,local_margin_m=1e-6).verdict,Verdict.UNKNOWN)
        with self.assertRaises(TypeError):bool(classify_ray(te,0.,sc))
    def test_unknown_no_gradient(self):
        sc=dataclasses.replace(Scene(),shadow_boundary_uncertainty_m=.001);r=evaluate(0.,sc)
        self.assertEqual(r['sensitivity_status'],'geometry_unknown');self.assertIsNone(r['gradient'])
        e=r['uncertainty_envelope'];self.assertLess(e['lower'],r['value_s_m2']);self.assertGreater(e['upper'],r['value_s_m2'])
    def test_unknown_contains_boundary_witnesses(self):
        sc=dataclasses.replace(Scene(),shadow_boundary_uncertainty_m=.001);e=evaluate(0.,sc)['uncertainty_envelope']
        # +/- 0.0004 m plate displacement moves projected limits by 0.001 m.
        for b in (-.0004,0.,.0004):
            val=evaluate(0.,dataclasses.replace(sc,plate_shift_m=b,shadow_boundary_uncertainty_m=0))['value_s_m2']
            self.assertLessEqual(e['lower']-1e-12,val);self.assertLessEqual(val,e['upper']+1e-12)
    def test_face_tie_rejected(self):
        r=evaluate(.08,Scene());self.assertEqual(r['sensitivity_status'],'topology_switch_unresolved');self.assertIsNone(r['gradient'])
    def test_endpoint_rejected(self):
        sc=dataclasses.replace(Scene(),target_shift_m=.2);r=evaluate(0.,sc)
        self.assertEqual(r['sensitivity_status'],'endpoint_event_unresolved');self.assertIsNone(r['gradient'])
    def test_oracle_close_events_rejected(self):
        sc=dataclasses.replace(Scene(),half_width_m=1e-11)
        self.assertEqual(evaluate(0.,sc)['sensitivity_status'],'event_order_unresolved')
        with self.assertRaises(ValueError):exact_value_gradient(sc)
    def test_stationary(self):
        r=evaluate(0.,dataclasses.replace(Scene(),velocity_m_s=0.));self.assertIsNone(r['gradient']);self.assertGreater(r['value_s_m2'],0.)
    def test_low_speed_preserves_crossing_value(self):
        sc=dataclasses.replace(Scene(),t1=2e11,velocity_m_s=4e-12,q1_per_s=0.)
        r=evaluate(0.,sc);self.assertIsNone(r['gradient']);self.assertEqual(len(r['events']),2)
        self.assertGreater(r['value_s_m2'],0.);self.assertLess(r['value_s_m2'],integral(sc.t0,sc.t1,0.,sc))
    def test_grazing(self):
        self.assertIsNone(grazing_duration(0)['derivative']);self.assertAlmostEqual(grazing_duration(1e-4)['blocked_duration_s'],.02)
        self.assertEqual(grazing_duration(-1e-4)['blocked_duration_s'],0.)
    def test_invalid_scene(self):
        for changes in ({'height_m':.5},{'q0':-1.},{'event_guard_s':-1.},{'target_shift_m':float('nan')},{'amplitude':0.}):
            with self.assertRaises(ValueError):evaluate(0.,dataclasses.replace(Scene(),**changes))
    def test_flux_directional_translation(self):
        # At x=(1,0,2), n down, ns up, m=1: K=4/25; dK/dx=-16/125.
        r=flux_directional([1,0,2],[0,0,-1],[0,0,0],[0,0,1],[1,0,0],[0,0,0],[0,0,0],[0,0,0])
        self.assertAlmostEqual(r['value'],4/25);self.assertAlmostEqual(r['directional'],-16/125)
    def test_rotation_normal_and_point(self):
        c=np.array([0.,0.,2.]);x=np.array([.3,0.,2.]);n=np.array([0.,0.,-1.]);Jx,Jn=rigid_jacobians(c,x,n)
        q=np.array([0.,0.,0.,0.,1.,0.]);dx=Jx@q;dn=Jn@q
        np.testing.assert_allclose(dx,[0,0,-.3]);np.testing.assert_allclose(dn,[-1,0,0])
        r=flux_directional(x,n,[0,0,0],[0,0,1],dx,dn,[0,0,0],[0,0,0]);self.assertIsNotNone(r['directional'])
    def test_angular_boundary(self):
        r=flux_directional([1,0,0],[0,0,-1],[0,0,0],[0,0,1],[0,0,0],[0,0,0],[0,0,0],[0,0,0]);self.assertIsNone(r['directional'])
    def test_backface_zero(self):
        r=flux_directional([0,0,-1],[0,0,-1],[0,0,0],[0,0,1],[0,0,0],[0,0,0],[0,0,0],[0,0,0]);self.assertEqual(r['value'],0.)
    def test_clock_null(self):
        sc=Scene();j=np.array(evaluate(0.,sc)['gradient']);self.assertAlmostEqual(j[2],sc.velocity_m_s*j[0],places=13)
    def test_translation_gauge(self):
        j=np.array(evaluate(0.,Scene())['gradient']);self.assertAlmostEqual(j[0]+j[1]+j[4],0.,places=13)
    def test_covariance_correlation(self):
        j=np.array([1.,-1.]);C=np.array([[1.,.8],[.8,1.]])
        self.assertAlmostEqual(linear_output_variance(j,C,'differentiable_conditional')['variance'],.4)
        self.assertIsNone(linear_output_variance(j,C,'geometry_unknown')['variance'])
        with self.assertRaises(ValueError):linear_output_variance(j,[[1,2],[2,1]],'differentiable_conditional')
    def test_input_template_rejected(self):
        with self.assertRaises(ValueError):load(R/'data/measurement_template.json',True)
    def test_synthetic_explicit(self):
        with self.assertRaises(ValueError):load(R/'data/synthetic_contract.json')
        sc,s,w=load(R/'data/synthetic_contract.json',True);self.assertEqual(len(s),1)
    def test_extra_input_field_rejected(self):
        d=json.loads((R/'data/synthetic_contract.json').read_text());d['extra']=1
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'a.json';p.write_text(json.dumps(d))
            with self.assertRaises(ValueError):load(p,True)
    def test_driver_no_run(self):
        d=read_plan(R/'data/device_validation_plan.json');self.assertEqual(d['execution_mode'],'plan_only');self.assertFalse(d['execution_authorized']);self.assertGreater(estimate(d)['total_kernel_evaluations_upper'],1e9)
        with self.assertRaises(ValueError):run(d,None)
    def test_bad_weights_rejected(self):
        d=json.loads((R/'data/synthetic_contract.json').read_text());d['source_weights']=[-.2]
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'a.json';p.write_text(json.dumps(d))
            with self.assertRaises(ValueError):load(p,True)

if __name__=='__main__':unittest.main()
