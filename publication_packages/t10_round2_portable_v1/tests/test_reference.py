from pathlib import Path
import sys,unittest,math,json,copy
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'models'))
from ion_observables import *
from evidence_contract import validate_packet
from validation_driver import plan,reference_cases
R=Path(__file__).resolve().parents[1]
class Physics(unittest.TestCase):
    def test_charge_energy(self):
        self.assertEqual(impact_energy(0,2,120,20),200)
        with self.assertRaises(ContractError): impact_energy(0,1,0,1)
    def test_fractions(self):
        j=E_CHARGE*1.2e18
        np.testing.assert_allclose(flux_from_corrected_current(j,[.8,.2],[1,2]),[8e17,2e17])
        np.testing.assert_allclose(flux_from_corrected_current(j,[2/3,1/3],[1,2],'current'),[8e17,2e17])
    def test_fraction_rejects(self):
        for fractions,charges in [([.2,.2],[1,2]),([1],[0]),([1],[True])]:
            with self.assertRaises(ContractError):flux_from_corrected_current(1,fractions,charges)
    def test_collector_sign(self):
        flux=2e18;g=.4;ge=3e17;b=.012
        result=correct_collector_current(E_CHARGE*((1+g)*flux-ge)+b,b,ge,1,g)
        self.assertAlmostEqual(result['charged_particle_flux_m2_s']/flux,1)
    def test_neutrals(self):
        x=moments([Cell(1e18,100,1),Cell(1e18,100,0)],'unknown')
        self.assertIsNone(x['total_kinetic_flux_w_m2']);self.assertAlmostEqual(x['observed_kinetic_flux_w_m2'],2*x['charged_kinetic_flux_w_m2'])
    def test_energy_per_charge(self):
        x=moments([Cell(8e17,100,1),Cell(2e17,200,2)],'complete_conditional')
        self.assertAlmostEqual(x['charged_kinetic_flux_w_m2'],100*x['ion_current_a_m2'])
    def test_rfea_normal_energy(self):
        c=[Cell(1e18,100,1,math.pi/3)]
        a=rfea_matrix(c,[0,20,30],np.ones((3,1)))
        np.testing.assert_allclose(a[:,0]/E_CHARGE,[1,1,0])
    def test_rfea_exact_threshold(self):
        a=rfea_matrix([Cell(0,100,1,math.pi/3)],[25],[[1]])
        self.assertEqual(a[0,0]/E_CHARGE,.5)
    def test_mean_charge_domain(self):
        with self.assertRaises(ContractError):correct_collector_current(1,0,0,.5,0)
    def test_exact_inventory_exhaustion(self):
        r=net_normalization(1,1,1,[1,2],{'O':[1,1]},{'O':[[-1,-1],[1,2]]})
        self.assertEqual(r['status'],'inventory_depletion_possible')
    def test_rfea_neutral_blind(self):
        a=rfea_matrix([Cell(0,100,0)],[0],[[1]])
        self.assertEqual(a[0,0],0)
    def test_rank_deficiency(self):
        a=rfea_matrix([Cell(0,100,1),Cell(0,200,2)],[0,50,150],np.ones((3,2)))
        self.assertEqual(invert_nonnegative(a,[1,1,0],np.eye(3))['status'],'unidentifiable')
    def test_inverse(self):
        a=rfea_matrix([Cell(0,50,1),Cell(0,150,1)],[0,100],np.ones((2,2)))
        truth=np.array([2e18,1e18]);x=invert_nonnegative(a,a@truth,np.eye(2)*1e-4)
        np.testing.assert_allclose(x['flux_m2_s'],truth,rtol=1e-10)
    def test_covariance_rejects(self):
        with self.assertRaises(ContractError):invert_nonnegative([[1,0],[0,1]],[1,1],[[1,2],[2,1]])
    def test_aperture(self):
        self.assertEqual(aperture_average([0,2],[.5,.5],True),1)
        with self.assertRaises(ContractError):aperture_average([2],[.5],False)
    def test_time_history(self):
        b=[{'t0_s':0,'t1_s':1,'v':2},{'t0_s':1,'t1_s':3,'v':0}]
        self.assertEqual(time_integrate(b,'v',0,3),2)
        b[1]['t0_s']=2
        with self.assertRaises(ContractError):time_integrate(b,'v',0,3)
    def test_net_states(self):
        for bounds,state in [([-2,-1],'net_erosion'),([0,0],'zero_or_crossing'),([-1,1],'zero_or_crossing'),([1,3],'ill_conditioned'),([3,4],'positive_conditional')]:
            self.assertEqual(net_normalization(1,1,1,bounds)['status'],state)
    def test_inventory_path(self):
        r=net_normalization(1,1,1,[2,3],{'O':[0,0]},{'O':[[-1,0],[2,3]]})
        self.assertEqual(r['status'],'inventory_depletion_possible')
    def test_missing_neutral_epsilon(self):
        r=net_normalization(1,1,None,[3,4]);self.assertIsNone(r['epsilon_ev_net_atom']);self.assertIsNotNone(r['R'])
    def test_film_vs_bulk(self):
        r=inventory_thickness(1e20,3,.0600843,2200,True,True,'bulk');self.assertIsNone(r['thickness_increment_m'])
    def test_thickness_sign(self):
        r=inventory_thickness(-1e20,3,.0600843,2200,True,True,'synthetic_declared');self.assertLess(r['thickness_increment_m'],0)
    def test_correlation(self):
        self.assertAlmostEqual(propagate_linear([[1,-1]],[[.04,.02],[.02,.04]])[0,0],.04)
    def test_nan(self):
        with self.assertRaises(ContractError):Cell(float('nan'),100,1)
class Evidence(unittest.TestCase):
    def setUp(self):self.p=json.loads((R/'examples/synthetic_complete.json').read_text())
    def test_synthetic_valid(self):self.assertEqual(validate_packet(self.p)['status'],'conditional_research_structure_valid')
    def test_actual_unknown(self):
        p=json.loads((R/'examples/actual_unknown.json').read_text());r=validate_packet(p)
        self.assertEqual(r['status'],'blocked_evidence');self.assertGreater(len(r['errors']),10)
    def test_relabel(self):
        self.p['data_origin']='actual';r=validate_packet(self.p)
        self.assertIn('SYNTHETIC_AS_ACTUAL',[x['code'] for x in r['errors']])
    def test_no_release(self):
        self.p['claim_class']='production_acceptance';self.assertEqual(validate_packet(self.p)['status'],'blocked_evidence')
    def test_split_leak(self):
        self.p['response_split'][1]['run_id']='r_fit';self.assertIn('LEAKED_RUN',[x['code'] for x in validate_packet(self.p)['errors']])
    def test_unknown_field(self):
        self.p['instrument_guess']='Kaufman';self.assertEqual(validate_packet(self.p)['status'],'blocked_structure')
        del self.p['instrument_guess'];self.p['coordinate']['position_m'][0]=float('inf')
        self.assertEqual(validate_packet(self.p)['status'],'blocked_structure')
    def test_profile_endpoint(self):
        self.p['numeric_stage']={'status':'budget_exhausted','used_as_interval_endpoint':True};self.assertIn('NUMERIC_ENDPOINT_UNRESOLVED',[x['code'] for x in validate_packet(self.p)['errors']])
    def test_plan_only(self):
        p=plan();self.assertEqual(p['mode'],'plan_only');self.assertFalse(p['heavy_execution_authorized_in_this_round']);self.assertEqual(p['case_count'],216)
    def test_reference_completes(self):
        r=reference_cases();self.assertEqual(r['heavy_sweep'],'not_run_awaiting_device');self.assertEqual(r['same_energy_per_charge_ambiguity']['rank'],1)
    def test_response_leak(self):
        rows=[{'sample_id':'s1','run_id':'same','split':'fit','operator_id':'o','material_state_id':'m','features':[1],'value':1,'standard_uncertainty':1},{'sample_id':'s2','run_id':'same','split':'final','operator_id':'o','material_state_id':'m','features':[1],'value':1,'standard_uncertainty':1}]
        with self.assertRaises(ContractError):grouped_response_fit(rows,'o','m')
if __name__=='__main__':unittest.main()
