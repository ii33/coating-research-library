import math, unittest
from reference_state import *
class StateTests(unittest.TestCase):
    def test_source_endpoints(self):
        self.assertEqual(source_wt_to_cation_fraction(0),0);self.assertEqual(source_wt_to_cation_fraction(1),1)
    def test_wt_not_at(self):
        self.assertAlmostEqual(source_wt_to_cation_fraction(.1),.0928,places=4)
    def test_bad_fraction(self):
        for x in (-1,1.1,float('nan')):
            with self.assertRaises(ValueError): source_wt_to_cation_fraction(x)
    def test_gas_scaling(self):
        f=gas_impingement(1,300,1e-26)
        self.assertAlmostEqual(gas_impingement(2,1200,1e-26)/f,1)
    def test_gas_zero(self): self.assertEqual(gas_impingement(0,300,1e-26),0)
    def test_gas_invalid(self):
        with self.assertRaises(ValueError): gas_impingement(1,0,1e-26)
    def test_angle_normalization(self):
        for n in (0,1,3,10):
            k=20000;integral=sum((n+1)*((i+.5)/k)**n/k for i in range(k))
            self.assertAlmostEqual(integral,1,places=6)
    def test_flux_projection(self):
        a=cosine_point_flux(1e20,2,1,1,1)
        self.assertAlmostEqual(cosine_point_flux(1e20,2,1,.5,2)/a,.125)
    def test_shadow_back(self):
        self.assertEqual(cosine_point_flux(1,1,1,1,1,0),0)
        self.assertEqual(cosine_point_flux(1,0,-1,1,1),0)
    def test_geometry_invalid(self):
        with self.assertRaises(ValueError): cosine_point_flux(1,1,1,1,0)
    def test_inventory(self):
        self.assertEqual(inventory_step({'In':2},{'In':-1},1),{'In':1})
    def test_depletion_rejected(self):
        with self.assertRaises(ValueError): inventory_step({'In':1},{'In':-2},1)
    def test_element_mismatch(self):
        with self.assertRaises(ValueError): inventory_step({'In':1},{'O':2},1)
    def test_mass_stoichiometry(self):
        a={'In':2*NA,'Sn':0,'O':3*NA}
        self.assertAlmostEqual(mass_per_area(a),2*M['In']+3*M['O'])
    def test_density_contraction(self):
        a={'In':2e20,'Sn':1e19,'O':3.2e20}
        h=conditional_thickness(a,6000,inventory_complete=True)
        self.assertAlmostEqual(conditional_thickness(a,7200,inventory_complete=True)/h,6000/7200)
    def test_partial_rejected(self):
        with self.assertRaises(ValueError): conditional_thickness({'In':1,'Sn':1,'O':1},7000,inventory_complete=False)
    def test_unknown_not_zero(self):
        self.assertIsNone(actual_unknown_record()['carrier_density_m3'])
if __name__=='__main__':unittest.main()
