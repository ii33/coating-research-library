import unittest,json,hashlib
from pathlib import Path
import numpy as np
from inversion import Problem,Ledger,fit_one,multistart,profile,huber_cost
from design import conditional_increment,information_difference,auxiliary_rows
from scenarios import operator,record,make_problem,noise_covariance
from batch_driver import configuration,plan
from vendor.measurement import Contract,observe
ROOT=Path(__file__).resolve().parents[1]

def linear_problem(loss='gaussian',calibration=None,priors=None):
    return Problem('linear',['a','b'],([-10,-10],[10,10]),np.array([1.,1.]),[{'kind':'d_geo'},{'kind':'d_geo'}],np.array([1.,2.]),np.eye(2),np.zeros((2,2)),lambda x,r:np.array([x[0],x[0]+x[1]]),calibration or [],priors or [],loss)

class ReferenceTests(unittest.TestCase):
    def test_frozen_copies(self):
        for r in json.loads((ROOT/'data/frozen_dependencies.json').read_text()):self.assertEqual(hashlib.sha256((ROOT/r['copy']).read_bytes()).hexdigest(),r['sha256'])
    def test_conditional_matches_joint_information(self):
        J0=np.array([[1.,2.],[2.,1.]]);J1=np.array([[.2,3.]])
        C0=np.array([[2.,.3],[.3,1.]]);C1=np.array([[1.]]);B=np.array([[.1,.2]])
        A,D,_=conditional_increment(J0,J1,C0,C1,B)
        J=np.vstack([J0,J1]);C=np.block([[C0,B.T],[B,C1]])
        np.testing.assert_allclose(A.T@A+D.T@D,J.T@np.linalg.solve(C,J),rtol=1e-12)
    def test_correlated_repeat(self):
        for rho in [0.,.9,.999]:
            _,A,_=conditional_increment([[1]],[[1]],[[1]],[[1]],[[rho]])
            self.assertAlmostEqual(float((A.T@A)[0,0]),(1-rho)/(1+rho),places=11)
    def test_unknown_new_bias_zero_increment(self):
        A,B,_=conditional_increment([[1,0]],[[1,1]],[[1]],[[.01]],[[0]])
        r=information_difference(A,B,np.empty((0,2)),1)
        self.assertAlmostEqual(r['interest_increment'][0][0],0.,places=11)
    def test_known_candidate_positive_increment(self):
        A,B,_=conditional_increment([[1]],[[1]],[[1]],[[.01]],[[0]])
        r=information_difference(A,B,np.empty((0,1)),1)
        self.assertAlmostEqual(r['interest_increment'][0][0],100.)
    def test_bad_covariance_rejected(self):
        with self.assertRaises(ValueError):conditional_increment([[1]],[[1]],[[1]],[[1]],[[1]])
    def test_penalty_not_robustified(self):
        p=linear_problem('huber',[{'index':0,'mean':0.,'sigma':.1}],[{'index':1,'mean':0.,'sigma':.2}])
        _,d=p.evaluate(np.array([2.,3.]),Ledger(5))
        self.assertEqual(d['calibration_loss'],200.)
        self.assertEqual(d['prior_loss'],112.5)
    def test_data_noise_and_discrepancy_separate(self):
        p=linear_problem();p.discrepancy_cov=np.eye(2)*3;p.__post_init__()
        _,d=p.evaluate(np.zeros(2),Ledger(2))
        self.assertAlmostEqual(d['raw_noise_only_chi2'],5.)
        self.assertAlmostEqual(d['effective_covariance_chi2'],1.25)
    def test_hard_calls_count_numerical_jacobian(self):
        ledger=Ledger(50);a=fit_one(linear_problem(),[0.,0.],4,100,ledger)
        self.assertEqual(a['forward_calls'],4);self.assertFalse(a['converged'])
        self.assertIsNotNone(a['best_evaluated'])
    def test_small_multistart_fit(self):
        ledger=Ledger(200);r=multistart(linear_problem(),[[0,0],[3,3]],60,20,ledger)
        x=r['clusters'][0]['representative']['x'];np.testing.assert_allclose(x,[1,1],atol=1e-5)
        self.assertFalse(r['global_minimum_certified'])
    def test_profile_refits_free_parameter(self):
        cfg={'max_calls_per_start':40,'max_nfev':15,'cluster_distance_scaled':.1}
        r=profile(linear_problem(),[[0,0]],0,[.5,1.5],cfg,Ledger(100))
        for row in r['rows']:
            x=row['clusters'][0]['representative']['x'];self.assertAlmostEqual(x[1],2-row['fixed_value'],places=5)
    def test_covariance_scale_rows(self):
        p=linear_problem(calibration=[{'index':1,'mean':0.,'sigma':.2}]);p.scales[1]=.1
        np.testing.assert_allclose(auxiliary_rows(p,p.calibration),[[0,.5]])
    def test_forward_refuses_unsupported_contract(self):
        with self.assertRaises(ValueError):observe([1.8,.02,.1],[record('R')],Contract(scatter='unknown'))
        r=record('rho_reim',.6,60);r['spectral_nodes']=[[-.01,.5],[.01,.5]]
        with self.assertRaises(ValueError):operator('linear_n')([1.8,.02,.1,1.,0.,.2],[r])
    def test_linear_n_applied_at_quadrature_nodes(self):
        r=record('R',.6,45);r['spectral_nodes']=[[-.02,.5],[.02,.5]]
        x=[1.8,.02,.1,1.,0.,.4]
        got=operator('linear_n')(x,[r])[0]
        expected=.5*sum(observe([1.8+.4*(w-.6),.02,.1],[record('R',w,45)])[0] for w in [.58,.62])
        self.assertAlmostEqual(got,expected,places=13)
    def test_default_plan_only_budget(self):
        p=plan(configuration());self.assertEqual(p['fit_start_jobs'],163584);self.assertEqual(p['status'],'plan_only')
        self.assertEqual(p['total_forward_call_ceiling'],196391832)
    def test_real_hardware_input_rejected(self):
        with self.assertRaises(ValueError):make_problem({'conditional_synthetic':True,'actual_hardware':'unverified'},'constant','gaussian')
    def test_correlated_heldout_conditioning(self):
        from inversion import heldout
        from scenarios import discrepancy_features
        x=np.array([1.8,.02,.1,1.,0.]);rr=[record('R',.5,45),record('T',.6,45)];hh=[record('R',.7,55)]
        f=operator('constant');yf=f(x,rr)+np.array([.001,-.002]);yh=f(x,hh)+.004
        case={'conditional_synthetic':True,'actual_hardware':None,'fit_records':rr,'heldout_records':hh,'fit_y':yf.tolist(),'heldout_y':yh.tolist(),'noise_covariance':noise_covariance(rr).tolist()}
        problem=make_problem(case,'constant_correlated_discrepancy','huber');r=heldout(problem,x,case,Ledger(5))
        cross=discrepancy_features(hh)@discrepancy_features(rr).T
        expected=.004-cross@np.linalg.solve(problem.V,yf-f(x,rr))
        np.testing.assert_allclose(r['conditional_innovation'],expected,atol=1e-15)
        self.assertFalse(r['parameter_uncertainty_included'])
    def test_k_boundary_jacobian(self):
        from vendor.identifiability import jacobian
        rr=[record('R',.6,45)];f=operator('constant');x=np.array([1.8,0.,.1,1.,0.])
        J,s=jacobian(lambda q:f(q,rr),x,np.array([.2,.02,.05,.01,.1]),([1.1,0.,.005,.9,-.5],[3.,.3,1.5,1.1,.5]))
        self.assertEqual(s[1],'forward_second_order');self.assertTrue(np.isfinite(J).all())
if __name__=='__main__':unittest.main()
