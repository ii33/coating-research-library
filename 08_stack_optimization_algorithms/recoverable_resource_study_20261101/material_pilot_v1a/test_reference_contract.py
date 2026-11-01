"""Pure reference selection contract; does not evaluate optical models."""
import unittest
from reference import select_witness

class ReferenceContractTest(unittest.TestCase):
    def test_selection_keeps_one_real_pair_and_rejects_invalid_zero(self):
        rows=[dict(layer_count=1,total_thickness_nm=20.,physical_design_hash='a'),dict(layer_count=2,total_thickness_nm=1.,physical_design_hash='b')]
        self.assertIs(select_witness(rows,100.),rows[0])
        for n,d in [(0,1.),(1,0.),(2.5,1.),(1,float('nan'))]:
            with self.assertRaises(ValueError):select_witness([dict(layer_count=n,total_thickness_nm=d,physical_design_hash='c')],100.)

if __name__=='__main__':unittest.main()
