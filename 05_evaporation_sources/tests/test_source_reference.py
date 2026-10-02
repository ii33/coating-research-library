import sys, unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'models'))
from source_reference import *


def thermal_parameters():
    return dict(initial_temperature_K=900.,bath_temperature_K=300.,effective_heat_capacity_J_K=8.,
      conductance_W_K=.04,emissivity=.4,radiating_area_m2=.0004,evaporating_area_m2=.0001,
      latent_heat_J_kg=2e6,initial_mass_kg=.02,molar_mass_kg_mol=.05,T_ref_K=1200.,p_ref_Pa=2.,
      delta_H_J_mol=1e5,alpha=.7,absorbed_fraction=.8,valid_T_min_K=250.,valid_T_max_K=2000.)

class SourceTests(unittest.TestCase):
    def setUp(self):
        self.x=np.array([[0.,0.,.5],[.2,0.,.5]])
        self.n=np.tile([0.,0.,-1.],(2,1))
    def test_angular_normalization(self):
        z,w=np.polynomial.legendre.leggauss(80);mu=(z+1)/2
        for n in [0,1,2,7,20]:
            self.assertAlmostEqual(float(np.sum(cosine_pdf(mu,n)*w/2)*2*np.pi),1,places=12)
    def test_n_zero_backface(self):
        np.testing.assert_array_equal(cosine_pdf(np.array([-1.,0.]),0),0)
    def test_n_one_lambert(self):
        mu=np.array([.1,.5,1.]);np.testing.assert_allclose(cosine_pdf(mu,1),mu/np.pi)
    def test_negative_n(self):
        with self.assertRaises(ValueError):cosine_pdf([1.],-1)
    def test_nan_exponent(self):
        with self.assertRaises(ValueError):cosine_pdf([1.],np.nan)
    def test_invalid_mu(self):
        with self.assertRaises(ValueError):cosine_pdf([1.1],1)
    def test_disk_weights(self):
        s=disk_source(.05);p,n,w=s.validate();self.assertAlmostEqual(w.sum(),1);self.assertTrue(np.all(w>0))
    def test_rectangle_weights(self):
        s=rectangle_source(.1,.02);self.assertAlmostEqual(s.fractions.sum(),1)
    def test_zero_radius_point(self):
        s=disk_source(0);self.assertEqual(len(s.fractions),1)
    def test_disk_axis_analytic(self):
        a,H,Q=.08,.2,3e-6;s=disk_source(a,nr=256,nphi=16)
        j=flux_kg_m2_s(s,[[0,0,H]],[[0,0,-1]],Q)[0]
        self.assertLess(abs(j/(Q/(np.pi*(H*H+a*a)))-1),2e-7)
    def test_point_inverse_square(self):
        s=disk_source(0);j=flux_kg_m2_s(s,[[0,0,1],[0,0,2]],self.n,1)
        self.assertAlmostEqual(j[0]/j[1],4)
    def test_rate_linear(self):
        s=disk_source(.03);a=flux_kg_m2_s(s,self.x,self.n,2);b=flux_kg_m2_s(s,self.x,self.n,1)
        np.testing.assert_allclose(a,2*b)
    def test_receiver_backface(self):
        np.testing.assert_array_equal(flux_kg_m2_s(disk_source(0),self.x,-self.n,1),0)
    def test_source_backface(self):
        s=disk_source(0,exponent=0);s.normals*=-1
        np.testing.assert_array_equal(flux_kg_m2_s(s,self.x,self.n,1),0)
    def test_negative_rate(self):
        with self.assertRaises(ValueError):flux_kg_m2_s(disk_source(0),self.x,self.n,-1)
    def test_negative_weights(self):
        s=disk_source(.03,nr=1,nphi=2);s.fractions=np.array([-1.,2.])
        with self.assertRaises(ValueError):s.validate()
    def test_unormalized_weights(self):
        s=disk_source(0);s.fractions*=2
        with self.assertRaises(ValueError):s.validate()
    def test_unormalized_normals(self):
        with self.assertRaises(ValueError):flux_kg_m2_s(disk_source(0),self.x,2*self.n,1)
    def test_zero_distance(self):
        with self.assertRaises(ValueError):flux_kg_m2_s(disk_source(0),[[0,0,0]],[[0,0,-1]],1)
    def test_full_occlusion(self):
        np.testing.assert_array_equal(flux_kg_m2_s(disk_source(0),self.x,self.n,1,np.zeros((2,1))),0)
    def test_visibility_bounds(self):
        with self.assertRaises(ValueError):flux_kg_m2_s(disk_source(0),self.x,self.n,1,np.full((2,1),1.1))
    def test_footprint_positive(self):
        s=gaussian_footprint(disk_source(.05),(.02,0),.01,.1);s.validate();self.assertTrue(np.all(s.fractions>0))
    def test_footprint_underflow_protection(self):
        s=gaussian_footprint(disk_source(.05),(100,0),1e-5);s.validate()
    def test_aperture_recession(self):
        s=disk_source(0,center=(0,0,-.03));v=circular_aperture(s,[[0,0,1],[1,0,1]],0,.02)
        np.testing.assert_array_equal(v,[[1],[0]])
    def test_aperture_plane_rejected(self):
        with self.assertRaises(ValueError):circular_aperture(disk_source(0),self.x,1,.03)
    def test_point_fit_exact(self):
        x=np.column_stack((np.linspace(0,.7,15),np.zeros(15),np.full(15,.5)));nn=np.tile([0,0,-1.],(15,1))
        j=flux_kg_m2_s(disk_source(0,exponent=3),x,nn,2e-6);f=fit_point_logflux(x,nn,j)
        self.assertAlmostEqual(f['exponent'],3,places=11);self.assertLess(abs(f['mass_rate_kg_s']/2e-6-1),1e-12)
    def test_single_angle_unidentifiable(self):
        with self.assertRaises(ValueError):fit_point_logflux([[0,0,1],[0,0,2]],[[0,0,-1],[0,0,-1]],[1,1])
    def test_nonpositive_fit_observation(self):
        with self.assertRaises(ValueError):fit_point_logflux(self.x,self.n,[1,0])
    def test_hk_zero_gradient(self):
        self.assertEqual(hertz_knudsen_kg_m2_s(1000,2,.05,p_back_Pa=2),0)
    def test_hk_linear_pressure(self):
        a=hertz_knudsen_kg_m2_s(1000,2,.05);b=hertz_knudsen_kg_m2_s(1000,4,.05);self.assertAlmostEqual(b/a,2)
    def test_hk_molecular_mass_scaling(self):
        a=hertz_knudsen_kg_m2_s(1000,2,.05);b=hertz_knudsen_kg_m2_s(1000,2,.2);self.assertAlmostEqual(b/a,2)
    def test_hk_condensation_rejected(self):
        with self.assertRaises(ValueError):hertz_knudsen_kg_m2_s(1000,1,.05,p_back_Pa=2)
    def test_hk_alpha_bounds(self):
        with self.assertRaises(ValueError):hertz_knudsen_kg_m2_s(1000,1,.05,alpha=2)
    def test_vapor_anchor(self):
        self.assertEqual(vapor_pressure_pa(1200,1200,2,1e5),2)
    def test_vapor_monotonic(self):
        self.assertGreater(vapor_pressure_pa(1300,1200,2,1e5),vapor_pressure_pa(1100,1200,2,1e5))
    def test_thermal_mass_conservation(self):
        p=thermal_parameters();h=lumped_history(p,np.full(200,100),.1)
        self.assertLess(abs(h['mass_kg'][0]-h['mass_kg'][-1]-np.sum(h['mass_rate_kg_s'])*.1),1e-15)
        self.assertTrue(np.all(np.diff(h['mass_kg'])<=0));self.assertTrue(np.all(h['mass_rate_kg_s']>=0))
    def test_thermal_energy_discrete(self):
        h=lumped_history(thermal_parameters(),np.full(100,100),.1);self.assertLess(np.max(abs(h['energy_residual_J'])),2e-12)
    def test_depletion_no_negative_mass(self):
        p=thermal_parameters();p['initial_mass_kg']=1e-10;h=lumped_history(p,np.full(100,100),.1)
        self.assertEqual(h['mass_kg'][-1],0);self.assertEqual(h['mass_rate_kg_s'][-1],0)
    def test_thermal_refinement(self):
        p=thermal_parameters();a=lumped_history(p,np.full(400,100),.1);b=lumped_history(p,np.full(800,100),.05)
        self.assertLess(abs(a['temperature_K'][-1]-b['temperature_K'][-1]),.1)
    def test_vapor_interval_enforced(self):
        p=thermal_parameters();p['valid_T_max_K']=901
        with self.assertRaises(ValueError):lumped_history(p,[1e5],1)
    def test_thermal_fraction_bounds(self):
        p=thermal_parameters();p['absorbed_fraction']=1.1
        with self.assertRaises(ValueError):lumped_history(p,[100],.1)

    def test_inactive_node_coincidence(self):
        s=Source(np.array([[0.,0.,0.],[0.,0.,.5]]),np.tile([0.,0.,1.],(2,1)),np.array([1.,0.]))
        a=flux_kg_m2_s(s,self.x,self.n,1)
        b=flux_kg_m2_s(disk_source(0),self.x,self.n,1)
        np.testing.assert_allclose(a,b)
    def test_footprint_zero_weight_nearest(self):
        s=Source(np.array([[0.,0.,0.],[1.,0.,0.]]),np.tile([0.,0.,1.],(2,1)),np.array([0.,1.]))
        g=gaussian_footprint(s,(0,0),1e-4);g.validate();np.testing.assert_array_equal(g.fractions,[0.,1.])
    def test_fit_boundary_no_ordinary_df(self):
        x=np.column_stack((np.linspace(0,.7,6),np.zeros(6),np.full(6,.5)));n=np.tile([0.,0.,-1.],(6,1))
        rr=np.linalg.norm(x,axis=1);mu=x[:,2]/rr;j=mu/rr**2*mu**(-.5)
        f=fit_point_logflux(x,n,j);self.assertTrue(f['boundary_fit']);self.assertIsNone(f['degrees_of_freedom']);self.assertIsNone(f['covariance_logQ_n'])
    def test_thermo_inconsistent_latent_rejected(self):
        p=thermal_parameters();p['latent_heat_J_kg']*=1.5
        with self.assertRaises(ValueError):lumped_history(p,[100],.1)
    def test_thermal_empty_invalid_initial_rejected(self):
        p=thermal_parameters();p['initial_temperature_K']=2300
        with self.assertRaises(ValueError):lumped_history(p,[],.1)
    def test_vapor_overflow_rejected(self):
        with self.assertRaises(ValueError):vapor_pressure_pa(2000,1,1e300,1e6)
    def test_t02_same_node_equivalence(self):
        sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'02_machine_modeling/models'))
        import deposition_reference as t02
        s=gaussian_footprint(disk_source(.04,exponent=2),(.01,0),.012,.1)
        upstream=t02.Source(s.nodes_m,s.normals,s.fractions,s.exponent)
        np.testing.assert_allclose(flux_kg_m2_s(s,self.x,self.n,2e-6),2e-6*t02.transfer_kernel(self.x,self.n,upstream),rtol=5e-15)
    def test_aperture_inactive_node(self):
        s=Source(np.array([[0.,0.,0.],[0.,0.,.5]]),np.tile([0.,0.,1.],(2,1)),np.array([1.,0.]))
        v=circular_aperture(s,self.x,.1,.1)
        self.assertEqual(v.shape,(2,2));np.testing.assert_array_equal(v[:,1],0)
        np.testing.assert_allclose(flux_kg_m2_s(s,self.x,self.n,1,v),flux_kg_m2_s(disk_source(0),self.x,self.n,1,circular_aperture(disk_source(0),self.x,.1,.1)))
    def test_spherical_total_mass(self):
        mu=(np.arange(10000)+.5)/10000;u=np.column_stack((np.sqrt(1-mu*mu),np.zeros(len(mu)),mu))
        j=flux_kg_m2_s(disk_source(0,exponent=3),2*u,-u,2e-6)
        total=np.mean(j)*2*np.pi*4
        self.assertLess(abs(total/2e-6-1),1e-8)
    def test_aperture_escape_mass(self):
        mu=(np.arange(10000)+.5)/10000;u=np.column_stack((np.sqrt(1-mu*mu),np.zeros(len(mu)),mu))
        s=disk_source(0,center=(0,0,-.03));x=s.nodes_m[0]+1000*u
        v=circular_aperture(s,x,0,.04);j=flux_kg_m2_s(s,x,-u,2e-6,v)
        escaped=np.mean(j)*2*np.pi*1000**2
        self.assertLess(abs(escaped/2e-6-.04**2/(.03**2+.04**2)),1e-4)

if __name__=='__main__':unittest.main(verbosity=2)
