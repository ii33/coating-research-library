import math
import unittest
import run_gate


class GateTests(unittest.TestCase):
    def test_exact_requested_seconds(self):
        for dt,n in ((.05,240),(.025,480),(.0125,960)):
            count,actual=run_gate.steps_for_cap(12.,dt)
            self.assertEqual(count,n)
            self.assertEqual(actual,dt)

    def test_nonintegral_duration_rounds_up(self):
        count,actual=run_gate.steps_for_cap(12.013,.05)
        self.assertEqual(count,241)
        self.assertLessEqual(actual,.05)

    def test_above_ceiling_rejected(self):
        for dt in (.05000001,.1,0.,-1.,float('nan')):
            with self.assertRaises(ValueError):run_gate.steps_for_cap(12.,dt)

    def test_no_hidden_step_truncation(self):
        original=run_gate._simulate_on_backend
        class Settings:
            time_steps=241;duration_s=12.013
        def synthetic(*args,progress=None,**kwargs):
            for start in range(0,241,32):progress(min(start+32,241)/241)
            return {'time_batch_steps':32}
        try:
            run_gate._simulate_on_backend=synthetic
            out=run_gate.observed_cpu(Settings(),None,None,None,None,None,None)
            self.assertEqual(out['integration_audit']['actual_time_steps'],241)
            self.assertEqual(out['integration_audit']['final_partial_batch_steps'],17)
        finally:run_gate._simulate_on_backend=original

    def test_incomplete_progress_rejected(self):
        original=run_gate._simulate_on_backend
        class Settings:
            time_steps=240;duration_s=12.
        def synthetic(*args,progress=None,**kwargs):
            progress(224/240)
            return {'time_batch_steps':32}
        try:
            run_gate._simulate_on_backend=synthetic
            with self.assertRaises(RuntimeError):
                run_gate.observed_cpu(Settings(),None,None,None,None,None,None)
        finally:run_gate._simulate_on_backend=original


if __name__=='__main__':unittest.main()
