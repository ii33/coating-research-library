"""Small complete-recipe contracts; synthetic injected fields, no cub runs."""
from copy import deepcopy
import json
import unittest
import numpy as np
import run_full_process as driver
from run_convergence import compare,passes


class FullProcessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads((driver.HERE/'config.json').read_text())
        cls.snapshot,cls.runtime,cls.native=driver.load_inputs(cls.config)

    def test_complete_original_duration(self):
        self.assertEqual(len(self.runtime['profile']['steps']),2)
        p=driver.capped_timing(self.runtime['profile'],.05)
        self.assertEqual(p['step_durations_s'],[7000.,3888.8888888888887])
        self.assertAlmostEqual(p['total_duration_s'],10888.888888888889)

    def test_all_record_hashes_valid(self):
        for r in self.snapshot['files']:
            import hashlib
            self.assertEqual(hashlib.sha256(driver.canonical_json_bytes(r['data'])).hexdigest(),r['sha256'])

    def test_actual_per_layer_caps(self):
        for dt in (.05,.025,.0125):
            p=driver.capped_timing(self.runtime['profile'],dt)
            self.assertTrue(all(x<=dt for x in p['step_time_step_s']))
            self.assertEqual(sum(p['step_time_steps']),p['time_steps'])
        self.assertEqual(driver.capped_timing(self.runtime['profile'],.0125)['time_steps'],871113)

    def test_probe_copies_geometry(self):
        before=deepcopy(self.runtime)
        p=driver.transform(self.runtime,True)
        self.assertEqual(self.runtime,before)
        self.assertEqual(p['machine']['sources'][0]['x_mm'],210.)
        self.assertEqual(p['machine']['sources'][1],self.runtime['machine']['sources'][1])
        self.assertEqual(p['profile']['steps'],self.runtime['profile']['steps'])

    def synthetic(self,settings,mask,xp,device,cancel,positions,weights,progress=None,**kwargs):
        axis=np.linspace(-150.,150.,settings.grid_size);x,y=np.meshgrid(axis,axis)
        field=np.where(x*x+y*y<=150.**2,1.,np.nan)
        for start in range(0,settings.time_steps,32):progress(min(start+32,settings.time_steps)/settings.time_steps)
        return {'field':field,'mean_raw':settings.duration_s,'x':axis,'y':axis,
                'device':'CPU','time_batch_steps':32}

    def test_complete_direct_and_periodic_clock(self):
        old=driver._simulate_on_backend
        try:
            driver._simulate_on_backend=self.synthetic
            for mode,calls in (('direct',2),('finite_periodic',4)):
                obs=driver.CoreObserver()
                row=driver.run_one(self.runtime,self.native,.05,21,mode,obs)
                self.assertEqual(row['total_duration_s'],10888.888888888889)
                self.assertEqual(row['total_target_nm'],7000.)
                self.assertEqual(len(row['step_results']),2)
                self.assertEqual(row['core_calls'],calls)
                self.assertTrue(all(r['all_steps_observed'] for r in obs.records))
                np.testing.assert_allclose(row['field_nm'][np.isfinite(row['field_nm'])],7000.)
                if mode=='finite_periodic':
                    self.assertEqual([r['duration_s'] for r in obs.records],[12.,4.,12.,.8888888888886868])
                else:
                    self.assertAlmostEqual(obs.records[1]['planet_phase_deg'],120.,places=7)
        finally:driver._simulate_on_backend=old

    def test_comparison_identity_and_zero_effect_guard(self):
        old=driver._simulate_on_backend
        try:
            driver._simulate_on_backend=self.synthetic
            row=driver.run_one(self.runtime,self.native,.05,21,'finite_periodic',driver.CoreObserver())
            diff=compare(row,row)
            self.assertEqual(diff['normalized_field_rms_pp'],0.)
            self.assertFalse(passes(diff,0.))
        finally:driver._simulate_on_backend=old


if __name__=='__main__':unittest.main()
