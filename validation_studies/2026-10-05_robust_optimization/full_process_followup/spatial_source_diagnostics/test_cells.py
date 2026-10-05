import math
import unittest
import numpy as np
from full_disk_cells import disk_polygon_area,full_disk_weights,aggregate


class CellTests(unittest.TestCase):
    def test_enclosing_square(self):
        p=np.array([[-2,-2],[2,-2],[2,2],[-2,2]],float)
        self.assertAlmostEqual(disk_polygon_area(p,1.),math.pi,places=12)
    def test_inside_square(self):
        p=np.array([[-.5,-.5],[.5,-.5],[.5,.5],[-.5,.5]])
        self.assertAlmostEqual(disk_polygon_area(p,2.),1.,places=12)
    def test_quarter_circle(self):
        p=np.array([[0,0],[2,0],[2,2],[0,2]],float)
        self.assertAlmostEqual(disk_polygon_area(p,1.),math.pi/4,places=12)
    def test_full_disk_partition(self):
        for n in (21,41,61):
            a=np.linspace(-150,150,n);x,y=np.meshgrid(a,a);v=x*x+y*y<=150**2
            w,c=full_disk_weights(a,v,150)
            self.assertAlmostEqual(c,1.,places=10)
            self.assertAlmostEqual(w.sum(),1.,places=12)
            self.assertGreater(w[v].min(),0.)
    def test_constant_and_symmetry(self):
        a=np.linspace(-150,150,21);x,y=np.meshgrid(a,a);v=x*x+y*y<=150**2
        f=np.where(v,7000.,np.nan);s=aggregate(f,a,150)
        self.assertLess(s['controlled_full_disk_cv_percent'],1e-10)
        w,c=full_disk_weights(a,v,150)
        np.testing.assert_allclose(w,np.flip(w,0),atol=1e-13)
        np.testing.assert_allclose(w,np.flip(w,1),atol=1e-13)


if __name__=='__main__':unittest.main()
