import sys,unittest,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'models'))
from optimization_core import *

class OpticsDerivatives(unittest.TestCase):
    def setUp(self):self.w=np.linspace(.9,1.2,17);self.d=np.array([.12,.21,.13]);self.n=[1,2.1,1.45,2.1,1.52]
    def test_01_forward_prefix_match(self):
        for a in [0,45]:
            for p in ['s','p']:
                x=spectrum_jacobian(self.w,self.n,self.d,a,p);y=spectrum_jacobian_forward(self.w,self.n,self.d,a,p)
                for k in ['R','T','JR','JT']:np.testing.assert_allclose(x[k],y[k],atol=2e-12)
    def test_02_independent_airy_gradient(self):
        x=spectrum_jacobian(self.w,self.n,self.d,45,'p')
        for j in range(3):
            h=np.eye(3)[j]*1e-6
            for k in ['R','T']:
                fd=(optics.recursive(self.w,self.n,self.d+h,45,'p')[k]-optics.recursive(self.w,self.n,self.d-h,45,'p')[k])/2e-6
                np.testing.assert_allclose(x['J'+k][:,j],fd,atol=2e-8)
    def test_03_absorbing_gradient(self):
        n=[1,2+.3j,1.4,1.8+.01j,1.5]
        x=spectrum_jacobian(self.w,n,self.d,60,'s')
        for j in range(3):
            h=np.eye(3)[j]*1e-6
            fd=(optics.recursive(self.w,n,self.d+h,60,'s')['T']-optics.recursive(self.w,n,self.d-h,60,'s')['T'])/2e-6
            np.testing.assert_allclose(x['JT'][:,j],fd,atol=2e-8)
    def test_04_energy_derivative(self):
        x=spectrum_jacobian(self.w,self.n,self.d);np.testing.assert_allclose(x['JR']+x['JT'],0,atol=2e-13)
    def test_05_energy_bookkeeping(self):
        x=spectrum_jacobian(self.w,[1,2+.4j,1.5], [.2]);np.testing.assert_allclose(x['R']+x['T']+x['A'],1,atol=2e-15);np.testing.assert_allclose(x['JR']+x['JT']+x['JA'],0,atol=2e-15)
    def test_06_zero_thickness(self):
        x=spectrum_jacobian(self.w,self.n,[0,0,0]);np.testing.assert_allclose(x['R'],((1-1.52)/(1+1.52))**2,atol=2e-15)
    def test_07_opaque_layer(self):
        x=spectrum_jacobian([1.], [1,2+5j,1.5],[100]);self.assertTrue(np.isfinite(x['JR']).all());self.assertEqual(float(x['T'][0]),0)
    def test_08_eighty_layers(self):
        n=[1]+[1.45,2.1]*40+[1.5];d=np.full(80,.15)
        x=spectrum_jacobian(self.w,n,d,45,'s');y=spectrum_jacobian_forward(self.w,n,d,45,'s')
        np.testing.assert_allclose(x['JR'],y['JR'],atol=3e-12)
    def test_09_negative_thickness_rejected(self):
        with self.assertRaises(ValueError):spectrum_jacobian(self.w,self.n,[-.1,.2,.3])
    def test_10_gain_rejected(self):
        with self.assertRaises(ValueError):spectrum_jacobian([1],[1,2-.1j,1.5],[.1])
    def test_11_bad_complex_step_counterexample(self):
        # Direct complex-step of a nonholomorphic real power gives zero.
        x=.3;h=1e-15;wrong=np.imag(abs(x+1j*h)**2)/h;self.assertEqual(wrong,0);self.assertGreater(abs(wrong-2*x),.5)
    def test_12_no_layer(self):
        z=spectrum_jacobian([1.], [1,1.5],[]);self.assertEqual(z['JR'].shape,(1,0));self.assertAlmostEqual(z['R'][0],.04)

class ObjectiveTests(unittest.TestCase):
    def setUp(self):self.seed=load_examples()[0]['E02'];self.b=[Band('AR',3.5,4.5,'R',0,.03)]
    def test_13_quadrature_normalization(self):
        w=np.array([1,1.2,1.7,2]);q=trapezoid_weights(w);self.assertAlmostEqual(sum(q),1);self.assertAlmostEqual(q@w,1.5)
    def test_14_quadrature_reject_order(self):
        with self.assertRaises(ValueError):trapezoid_weights([2,1])
    def test_15_chain_rule(self):
        p=Problem(self.seed,self.b,13,[0,30],factors=[[.99,1.02],[1.01,.97]]);x=np.ones(2);r,J=p.evaluate(x,True)
        for j in range(2):
            h=np.eye(2)[j]*1e-6;fd=(p.forward_fun(x+h)-p.forward_fun(x-h))/2e-6;np.testing.assert_allclose(J[:,j],fd,atol=2e-8)
    def test_16_cache(self):
        p=Problem(self.seed,self.b,7,[0]);p.fun([1,1]);calls=p.forward_calls;p.jac([1,1]);self.assertEqual(calls,p.forward_calls);self.assertEqual(p.cache_hits,1)
    def test_17_cache_context_identity(self):
        p=Problem(self.seed,self.b,7,[0]);q=Problem(self.seed,self.b,7,[30]);self.assertNotEqual(p.fingerprint,q.fingerprint)
    def test_18_fingerprint_scale(self):
        p=Problem(self.seed,self.b,7,[0]);q=Problem(self.seed,self.b,7,[0],scale_d=[1,1]);self.assertNotEqual(p.fingerprint,q.fingerprint)
    def test_19_repeated_scenario_cost_invariance(self):
        p=Problem(self.seed,self.b,7,[0]);q=Problem(self.seed,self.b,7,[0],factors=[[1,1],[1,1]])
        r=p.fun([1,1]);s=q.fun([1,1]);self.assertAlmostEqual(r@r,s@s)
    def test_20_hinge_inactive(self):
        p=Problem(self.seed,[Band('loose',3.5,4.5,'R',1,.03,sense='upper')],7,[0]);r,J=p.evaluate([1,1],True);self.assertEqual(np.linalg.norm(r),0);self.assertEqual(np.linalg.norm(J),0)
    def test_21_bad_material_range(self):
        m=load_examples()[1]['YbF3_MWIR_proxy']
        with self.assertRaises(ValueError):material(m,[6.])
    def test_22_directional_objective_gradient(self):
        p=Problem(self.seed,self.b,13,[0,30]);x=np.ones(2);r,J=p.evaluate(x,True);v=np.array([.7,-.2]);h=1e-6
        a=p.forward_fun(x+h*v);b=p.forward_fun(x-h*v);self.assertAlmostEqual((a@a-b@b)/(4*h),(J.T@r)@v,places=7)
    def test_23_solver_reduces(self):
        p=Problem(self.seed,self.b,13,[0,30]);r=p.fun([1,1]);z=solve(p,max_nfev=30);self.assertLess(z['cost'],.5*r@r);self.assertTrue(all(.4<=x<=1.6 for x in z['x']))
    def test_24_fd_vs_analytic_solver(self):
        a=solve(Problem(self.seed,self.b,13,[0,30]),max_nfev=30);b=solve(Problem(self.seed,self.b,13,[0,30]),mode='finite_difference',max_nfev=30);self.assertAlmostEqual(a['cost'],b['cost'],places=9)
    def test_25_total_thickness_constraint(self):
        p=Problem(self.seed,self.b,13,[0,30]);r=solve_constrained(p,[.75,.75],.5);self.assertLessEqual(sum(r['thickness_um']),.5+1e-8)
    def test_26_minimax(self):
        r=sampled_minimax_R(self.seed,np.linspace(3.5,4.5,7),[0,30],maxiter=50);self.assertLess(r['constraint_violation'],1e-6);self.assertLess(r['t'],1)

class TopologyTests(unittest.TestCase):
    def setUp(self):self.seed=load_examples()[0]['E02'];self.d=np.array([.33,.33])
    def test_27_add_conservation(self):
        s,d=insert_layer(self.seed,self.d,0,.5,'ZnS_IR_proxy',.03,'add');self.assertAlmostEqual(sum(d),.69)
    def test_28_replace_conservation(self):
        s,d=insert_layer(self.seed,self.d,0,.5,'ZnS_IR_proxy',.03,'replace');self.assertAlmostEqual(sum(d),.66)
    def test_29_replace_invalid(self):
        with self.assertRaises(ValueError):insert_layer(self.seed,self.d,0,.1,'ZnS_IR_proxy',.2,'replace')
    def test_30_merge_same(self):
        s,d=insert_layer(self.seed,self.d,0,.5,'YbF3_MWIR_proxy',.03,'add');ss,dd=merge_identical_layers(s,d);self.assertEqual(len(dd),2);self.assertAlmostEqual(dd[0],.36)
    def test_31_merged_spectrum(self):
        w=np.linspace(1,1.3,30);a=optics.recursive(w,[1,1.4,1.4,2],[.2,.3]);b=optics.recursive(w,[1,1.4,2],[.5]);np.testing.assert_allclose(a['R'],b['R'],atol=2e-15)
    def test_32_nonidentifiability(self):
        z=spectrum_jacobian(np.linspace(1,1.3,30),[1,1.4,1.4,2],[.2,.3]);sv=np.linalg.svd(z['JR'],compute_uv=False);self.assertLess(sv[-1],1e-12)
    def test_33_manufacturing_violations(self):
        z=manufacturing_violations([.01,.8],.03,.7,.75,1);self.assertAlmostEqual(z['min_thickness_um'],.02);self.assertAlmostEqual(z['total_thickness_um'],.06);self.assertEqual(z['layer_count'],1)
    def test_34_surrogate_actual_acceptance(self):
        p=Problem(self.seed,[Band('AR',3.5,4.5,'R',0,.03)],13,[0,30]);z=trust_region_surrogate(p,[1,1],steps=16)
        self.assertTrue(all(q['actual_reduction']>0 and q['rho']>.1 for q in z['trace'] if q['accepted']));self.assertTrue(any(not q['accepted'] for q in z['trace']))
    def test_35_undersampling(self):
        a=optics.recursive([1,1.2],[1,3.5,1],[3/3.5]);b=optics.recursive(np.linspace(1,1.2,1001),[1,3.5,1],[3/3.5]);self.assertLess(max(a['R']),1e-25);self.assertGreater(max(b['R']),.72)
    def test_36_frozen_kernel_copy(self):
        expected=json.loads((ROOT/'data/frozen_dependencies.json').read_text())['07_thin_film_design_theory/models/optics_kernel.py'];self.assertEqual(hashlib.sha256((ROOT/'models/vendor/t07_optics_kernel.py').read_bytes()).hexdigest(),expected)

if __name__=='__main__':unittest.main()
