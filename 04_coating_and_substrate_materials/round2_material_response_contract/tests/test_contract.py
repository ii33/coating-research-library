import copy,json,math,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'models'))
from build_examples import base,all_examples,q
from contract import calculate,validate,ContractError,propagate_covariance,E_CHARGE,N_A
from calibration_driver import fit,light,plan
class ContractTests(unittest.TestCase):
    def setUp(self):self.r=base()
    def bad(self,change):
        change(self.r);self.assertTrue(validate(self.r))
    def test_01_all_fixtures_valid(self):
        for r in all_examples().values():self.assertEqual(validate(r),[])
    def test_02_dimension_values(self):
        o=calculate(self.r);self.assertAlmostEqual(o['N_net']['value']/2e19,1);self.assertAlmostEqual(o['D']['value']/6e18,1)
        self.assertAlmostEqual(o['U']['value']/(8e20*E_CHARGE),1);self.assertAlmostEqual(o['R']['value'],.3);self.assertAlmostEqual(o['epsilon']['value'],40.)
    def test_03_formula_vs_atoms(self):
        o=calculate(self.r);self.assertAlmostEqual(o['N_net']['value']/o['N_formula_net']['value'],3)
    def test_04_density_conversion(self):
        o=calculate(self.r);n=2150*N_A*3/.060083;self.assertAlmostEqual(o['n_atom']['value']/n,1);self.assertAlmostEqual(o['h_increment']['value']/(2e19/n),1)
    def test_05_zero(self):self.assertEqual(calculate(all_examples()['zero'])['epsilon']['status'],'blocked')
    def test_06_erosion(self):
        o=calculate(all_examples()['erosion']);self.assertEqual(o['ratio_conditioning'],'net_erosion');self.assertIsNone(o['epsilon']['value']);self.assertLess(o['h_increment']['value'],0)
    def test_07_crosszero(self):self.assertEqual(calculate(all_examples()['cross_zero'])['ratio_conditioning'],'zero_or_crossing_zero')
    def test_08_illconditioned(self):
        o=calculate(all_examples()['ill_conditioned']);self.assertIsNone(o['R']['value']);self.assertIn('diagnostic_interval',o['R'])
    def test_09_unknown_neutrals(self):
        o=calculate(all_examples()['unknown_neutrals']);self.assertIsNone(o['U']['value']);self.assertIsNotNone(o['D']['value']);self.assertIsNotNone(o['U_observed_components']['value'])
    def test_10_bulk_density_blocked(self):self.assertIsNone(calculate(all_examples()['bulk_density_misuse'])['h_increment']['value'])
    def test_11_reference_missing(self):
        o=calculate(all_examples()['reference_unmeasured']);self.assertEqual(len(o['blocking_reasons']),6)
    def test_12_unit_formula_not_atoms(self):self.bad(lambda r:r['bins'][0]['net_element_flux']['Si'].update(unit='formula_units/m2/s'))
    def test_13_double_projection_rejected(self):self.bad(lambda r:r.update(flux_area_basis='beam_normal_area'))
    def test_14_angle_convention(self):self.bad(lambda r:r['bins'][0]['beams'][0]['cells'][0]['theta'].update(unit='deg_from_surface'))
    def test_15_molecular_current_not_count(self):
        a=calculate(self.r);self.r['bins'][0]['beams'][0].update(charge_number=2,nuclei_per_particle=2,species='O2++');b=calculate(self.r);self.assertEqual(a['D']['value'],b['D']['value'])
    def test_16_disjoint_time(self):self.bad(lambda r:r['bins'][1].update(t_start_s=11))
    def test_17_unknown_not_zero(self):self.bad(lambda r:r['film']['density'].update(status='unknown'))
    def test_18_inverted_interval(self):self.bad(lambda r:r['film']['density'].update(interval=[2300,2100]))
    def test_19_wrong_H4(self):self.bad(lambda r:r['film'].update(material_id='H4_film',identity_status='verified'))
    def test_20_wrong_YbF3(self):self.bad(lambda r:r['film'].update(material_id='YbF3_film',nominal_formula='YF3'))
    def test_21_unverified_composition_blocks_h(self):
        self.r['film']['composition_verified']=False;self.assertIsNone(calculate(self.r)['h_increment']['value'])
    def test_22_stoichiometry_mismatch_blocks_h(self):
        self.r['bins'][0]['net_element_flux']['O']=q(1e16,'atoms/m2/s');self.assertIsNone(calculate(self.r)['h_increment']['value'])
    def test_23_compaction_blocks_h(self):
        self.r['film']['density_composition_invariant']=False;self.assertIsNone(calculate(self.r)['h_increment']['value'])
    def test_24_inventory_exhaustion(self):
        r=all_examples()['erosion'];r['initial_inventory_atoms_m2']={e:q(0.,'atoms/m2') for e in ('Si','O')};self.assertIsNone(calculate(r)['N_net']['value'])
    def test_25_optics_not_predicted(self):
        o=calculate(self.r);self.assertTrue(all(v['value']['value'] is None for v in o['response_records']))
    def test_26_numeric_response_requires_evidence(self):self.bad(lambda r:r['response_records'][0].update(value=q(1.46,'1')))
    def test_27_yield_domain_required(self):self.bad(lambda r:r['resputter_yield_records'][0].update(state='calibrated'))
    def test_28_no_unknown_fields(self):self.bad(lambda r:r.update(hidden_recipe=999))
    def test_29_nan_rejected(self):self.bad(lambda r:r['film']['density'].update(value=float('nan')))
    def test_30_boolean_not_number(self):self.bad(lambda r:r.update(production_qualified=0))
    def test_31_partial_elements_not_total(self):
        self.r['atom_inventory_coverage']='partial';self.assertIsNone(calculate(self.r)['N_net']['value'])
    def test_32_missing_oxygen(self):
        del self.r['initial_inventory_atoms_m2']['O']
        for b in self.r['bins']:del b['net_element_flux']['O']
        self.assertIsNone(calculate(self.r)['N_net']['value'])
    def test_33_explicit_neutral_required(self):self.bad(lambda r:r['bins'][0].update(neutral_inventory='included'))
    def test_34_covariance_cancellation(self):self.assertEqual(propagate_covariance([1.,-1.],[[4.,4.],[4.,4.]]),0.)
    def test_35_covariance_independent(self):self.assertAlmostEqual(propagate_covariance([2.,3.],[[4.,0.],[0.,9.]]),math.sqrt(97))
    def test_36_nonpsd_rejected(self):
        with self.assertRaises(ContractError):propagate_covariance([1,1],[[1,2],[2,1]])
    def test_37_nonsym_rejected(self):
        with self.assertRaises(ContractError):propagate_covariance([1,1],[[1,0],[.1,1]])
    def test_38_calibration_identifiable(self):
        f=light()['fit'];self.assertEqual(f['status'],'synthetic_identifiable');self.assertLess(abs(f['eta']-.84),.03);self.assertLess(abs(f['yield_atoms_per_particle']-.32),.05)
    def test_39_calibration_unidentifiable_retained(self):
        f=light()['unidentifiable_fit'];self.assertEqual(f['status'],'unidentifiable');self.assertIsNone(f['eta'])
    def test_40_heavy_not_run(self):self.assertEqual(plan()['execution'],'not_run')
    def test_41_history_not_averaged(self):
        o=calculate(self.r);ratios=[sum(c['flux']['value'] for b_ in b['beams'] for c in b_['cells'])/sum(q_['value'] for q_ in b['net_element_flux'].values()) for b in self.r['bins']]
        self.assertNotAlmostEqual(o['R']['value'],sum(ratios)/len(ratios))
    def test_42_bounds_enclose_nominal(self):
        for k in ['N_net','D','U','R','epsilon','h_increment']:
            m=calculate(self.r)[k];self.assertLessEqual(m['interval'][0],m['value']);self.assertGreaterEqual(m['interval'][1],m['value'])
    def test_43_energy_per_particle_not_per_charge(self):self.bad(lambda r:r['bins'][0]['beams'][0]['cells'][0]['energy'].update(unit='eV/charge'))
    def test_44_no_erosion_bridge_to_T03(self):self.assertEqual(calculate(all_examples()['erosion'])['adapter_to_T03'],'blocked_signed_or_uncertain')
    def test_45_empty_bounds_not_exact(self):
        self.r['film']['density'].update(interval=None,interval_kind='none');self.assertIsNone(calculate(self.r)['h_increment']['value'])
    def test_46_missing_temp_does_not_predict_response(self):
        from build_examples import unknown
        self.r['bins'][0]['surface_temperature']=unknown('K');self.assertEqual(calculate(self.r)['response_prediction'].split(':')[0],'not_implemented')
if __name__=='__main__':unittest.main()
