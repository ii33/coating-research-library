import unittest
import numpy as np
from measurement import *
from identifiability import *
from scenarios import *
from batch_driver import configuration,plan,make_records

class ReferenceTests(unittest.TestCase):
    def test_bare_phase(self):
        # Zero thickness gives naked air/glass interface.
        a=amplitudes([1.8,.02,0.],.55,0.)
        self.assertAlmostEqual(a['s']['r'].real,(1-1.52)/(1+1.52),places=13)
        self.assertAlmostEqual(abs(ratio_from_amplitudes(a['s']['r'],a['p']['r'])+1),0.,places=13)
        self.assertAlmostEqual(abs(ratio_from_amplitudes(a['s']['r'],a['p']['r'],'same_tangential_p')-1),0.,places=13)
    def test_phase_wrap(self):
        self.assertAlmostEqual(circular_delta(np.deg2rad(-179),np.deg2rad(179)),np.deg2rad(2),places=13)
    def test_rho_covariance(self):
        v,C=psi_delta_to_rho(.5,3.1,np.array([[1e-6,2e-7],[2e-7,4e-6]]))
        self.assertTrue(np.linalg.eigvalsh(C).min()>0);self.assertAlmostEqual(np.linalg.norm(v),np.tan(.5))
        with self.assertRaises(ValueError):psi_delta_to_rho(0.,0.)
    def test_mixed_rho_rejected(self):
        r=record('rho_reim',a=60);r['spectral_nodes']=[[-.01,.5],[.01,.5]]
        with self.assertRaises(ValueError):observe(THETA,[r])
        pure=coherency_diagnostic(THETA,record('rho_reim',a=60))
        mixed=coherency_diagnostic(THETA,r)
        self.assertAlmostEqual(pure['degree_of_polarization'],1.,places=13)
        self.assertLess(mixed['degree_of_polarization'],1.)
    def test_polarization_mean(self):
        a=record('R',a=45);b={**a,'polarization':'p'};u={**a,'polarization':'unpolarized'}
        self.assertAlmostEqual(observe(THETA,[u])[0],np.mean(observe(THETA,[a,b])))
    def test_domain_contract_guards(self):
        for c in [Contract(scatter='unknown'),Contract(substrate_mode='finite'),Contract(evidence='measured'),Contract(actual_hardware='guessed')]:
            with self.assertRaises(ValueError):observe(THETA,[record('R')],c)
        r=record('R',w=.4);r['spectral_nodes']=[[-.01,.5],[.01,.5]]
        with self.assertRaises(ValueError):observe(THETA,[r])
        with self.assertRaises(ValueError):observe(THETA,[{'kind':'d_geo','independent':False}])
    def test_singular_noise_rejected(self):
        with self.assertRaises(ValueError):whitening([[1,-1],[-1,1]])
    def test_rank_and_null_dimension(self):
        for name,expected in [('single_R',1),('single_RT',2),('RT_plus_independent_d',3),('single_ellipsometric_ratio',2),('normal_incidence_ratio',0)]:
            rs=suite()[name];J,_=jacobian(function(rs),THETA,SCALES,BOUNDS);r=rank_report(J,covariance(rs))
            self.assertEqual(r['rank'],expected,name);self.assertEqual(len(r['null_directions_scaled']),3-expected)
            if expected<3:self.assertIsNone(r['covariance_scaled_local_if_full_rank'])
    def test_scaling_unit_invariance(self):
        f=function(suite()['RT_plus_independent_d']);J,_=jacobian(f,THETA,SCALES,BOUNDS)
        factor=np.array([1.,1.,1000.]);Jnm,_=jacobian(lambda z:f(z/factor),THETA*factor,SCALES*factor,(BOUNDS[0]*factor,BOUNDS[1]*factor))
        np.testing.assert_allclose(J,Jnm,rtol=1e-7,atol=1e-10)
    def test_nuisance_d_offset(self):
        E,m=nuisance_project(np.array([[1.]]),np.array([[1.]]),np.array([[1.]]))
        self.assertLess(np.linalg.norm(E),1e-14)
    def test_boundary_one_sided(self):
        f=lambda x:np.array([x[0]**2+3*x[1]])
        J,s=jacobian(f,[0.,2.],[1.,1.],([0.,0.],[3.,3.]))
        np.testing.assert_allclose(J,[[0,3]],atol=1e-10);self.assertEqual(s[0],'forward_second_order')
    def test_full_rank_fit_and_profile(self):
        # One tiny linear algebra fixture, no optical multistart scan.
        f=lambda x:np.array([x[0]+x[1],x[0]-x[1]])
        y=f([.2,.3]);bounds=([-1.,-1.],[1.,1.]);starts=[[0.,0.]]
        r=fit_multistart(f,y,np.eye(2),starts,bounds,[1,1]);np.testing.assert_allclose(r['best']['theta'],[.2,.3],atol=1e-8)
        p=profile_parameter(f,y,np.eye(2),starts,bounds,[1.,1.],0,[.2,.4])
        self.assertLess(p['rows'][0]['best']['chi2'],1e-16)
        self.assertAlmostEqual(p['rows'][1]['best']['chi2'],.08,places=9)
    def test_plan_never_executes(self):
        c=configuration();r=plan(c);self.assertEqual(r['status'],'plan_only')
        self.assertEqual(r['execution_status'],'not_run_awaiting_device')
        self.assertGreater(r['least_squares_start_jobs'],100000)
        self.assertGreater(len(make_records(c,'joint')),1)

if __name__=='__main__':unittest.main()
