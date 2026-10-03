import unittest,sys,json,hashlib,tempfile,shutil
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'models'))
from reference import *

class ReferenceTests(unittest.TestCase):
    def test_zero_exp(self): np.testing.assert_array_equal(exp_so3([0,0,0]),np.eye(3))
    def test_group(self):
        for v in ([1e-10,2e-10,-1e-10],[.2,-.3,.4],[0,0,np.pi]):
            q=exp_so3(v);np.testing.assert_allclose(q.T@q,np.eye(3),atol=1e-14);self.assertAlmostEqual(np.linalg.det(q),1)
    def test_nominal_limit(self):
        c,q=pose(.3,.7,[.4,0,.8]);x,n=point_normal(c,q,[.1,.02,0]);np.testing.assert_allclose(q,rz(1.),atol=1e-15);np.testing.assert_allclose(c,rz(.3)@[.4,0,.8]);np.testing.assert_allclose(n,[0,0,-1])
    def test_normal_follows_tilt(self):
        c,q=pose(0,0,[0,0,1],planet_tilt_C=(.02,-.01));x,n=point_normal(c,q,[.1,0,0]);self.assertGreater(abs(n[0])+abs(n[1]),.01);self.assertAlmostEqual(n@n,1)
    def test_jacobians(self):
        c=np.array([.2,-.1,.8]);q=exp_so3([.1,.2,-.3]);x,n=point_normal(c,q,[.07,-.11,.02]);jx,jn=rigid_jacobians(c,x,n);h=1e-6
        for k in range(6):
            v=np.eye(6)[k]*h
            xp=c+v[:3]+exp_so3(v[3:])@(x-c);xm=c-v[:3]+exp_so3(-v[3:])@(x-c)
            np.testing.assert_allclose((xp-xm)/(2*h),jx[:,k],atol=8e-11,rtol=0)
            np.testing.assert_allclose((exp_so3(v[3:])@n-exp_so3(-v[3:])@n)/(2*h),jn[:,k],atol=8e-11,rtol=0)
    def test_wrong_rotation(self):
        with self.assertRaises(ValueError): point_normal([0,0,0],-np.eye(3),[0,0,0])
    def test_invalid_finite(self):
        with self.assertRaises(ValueError): exp_so3([0,np.nan,0])
    def test_gear_ratio(self):
        self.assertEqual(direct_external_ratio(120,36,True),Fraction(13,3));self.assertEqual(direct_external_ratio(120,37,True),Fraction(157,37))
    def test_topology_not_assumed(self):
        with self.assertRaises(ValueError): direct_external_ratio()
    def test_center_distance_unknown(self):
        with self.assertRaises(ValueError): nominal_center_distance(None)
    def test_center_change(self): self.assertAlmostEqual(nominal_center_distance(.001,120,37)-nominal_center_distance(.001,120,36),.0005)
    def test_backlash_memory(self):
        np.testing.assert_allclose(play_backlash([0,.2,.4,.3,.2,.1],.1,0),[0,.1,.3,.3,.3,.2])
    def test_backlash_zero(self): np.testing.assert_allclose(play_backlash([0,.2,-.1],0,0),[0,.2,-.1])
    def test_backlash_initial_invalid(self):
        with self.assertRaises(ValueError):play_backlash([0,1],.1,.2)
    def test_probe_layout(self):
        a=axial_probe_design([[0,0],[1,0],[0,1]])
        self.assertEqual(local_observability(a,np.empty((3,0)),np.eye(3),[1,1,1])['rank'],3)
        a=axial_probe_design([[-1,0],[0,0],[1,0]])
        self.assertEqual(local_observability(a,np.empty((3,0)),np.eye(3),[1,1,1])['rank'],2)
    def test_clock_constant(self):
        a=np.column_stack((np.ones(8),np.full(8,2.)))
        self.assertEqual(local_observability(a,np.empty((8,0)),np.eye(8),[1,1])['rank'],1)
    def test_clock_varying(self):
        a=np.column_stack((np.ones(8),np.linspace(1,2,8)))
        self.assertEqual(local_observability(a,np.empty((8,0)),np.eye(8),[1,1])['rank'],2)
    def test_height_source_nuisance(self):
        self.assertEqual(local_observability(np.full((4,1),-2.),np.ones((4,1)),np.eye(4),[1])['rank'],0)
    def test_height_independent_probe(self):
        a=np.array([[-2.],[1.]]);b=np.array([[1.],[0.]])
        self.assertEqual(local_observability(a,b,np.eye(2),[1])['rank'],1)
    def test_underdetermined_null(self):
        r=local_observability([[1,2,3]],np.empty((1,0)),[[1]],[1,1,1]);self.assertEqual(len(r['null_scaled']),2);self.assertIsNone(r['noise_conditional_covariance'])
    def test_covariance_full(self):
        C=np.array([[2.,.5],[.5,1.]])
        r=local_observability(np.eye(2),np.empty((2,0)),C,[1,1]);np.testing.assert_allclose(r['noise_conditional_covariance'],C,atol=1e-14)
    def test_nuisance_unit_invariance(self):
        a=np.arange(1,5)[:,None];b=np.column_stack((np.ones(4),np.arange(4)))
        r=local_observability(a,b,np.eye(4),[1]);rr=local_observability(a,b*[1e-9,1e8],np.eye(4),[1]);self.assertEqual(r['rank'],rr['rank'])
    def test_bad_covariance(self):
        for C in ([[1,2],[2,1]],[[1,0],[0,0]],[[1,1],[0,1]]):
            with self.assertRaises(ValueError):local_observability(np.eye(2),np.empty((2,0)),C,[1,1])
    def test_invalid_scales(self):
        with self.assertRaises(ValueError):local_observability([[1]],np.empty((1,0)),[[1]],[0])
    def test_template_reject(self):
        with self.assertRaises(ValueError):load_observation_dataset(ROOT/'data/measurement_template.json',True)
    def test_synthetic_requires_optin(self):
        with self.assertRaises(ValueError):load_observation_dataset(ROOT/'data/synthetic_observations.json')
    def test_synthetic_parse(self):
        r=load_observation_dataset(ROOT/'data/synthetic_observations.json',True);self.assertEqual(r['channels'][0]['value'],[0,.1,.2])
    def test_bad_dataset(self):
        base=json.loads((ROOT/'data/synthetic_observations.json').read_text())
        changes=[('unit','deg'),('time_map',{'offset_s':None,'scale':1,'evidence':'unknown'}),('raw_source',{'relative_path':'../outside.csv','sha256':'0'*64}),('raw_source',{'relative_path':'synthetic_encoder.csv','sha256':'0'*64})]
        with tempfile.TemporaryDirectory() as td:
            out=Path(td);shutil.copy(ROOT/'data/synthetic_encoder.csv',out/'synthetic_encoder.csv')
            for key,value in changes:
                d=json.loads(json.dumps(base));d['channels'][0][key]=value;(out/'d.json').write_text(json.dumps(d))
                with self.assertRaises(ValueError):load_observation_dataset(out/'d.json',True)
    def test_nonmonotone_and_nan_csv(self):
        d=json.loads((ROOT/'data/synthetic_observations.json').read_text())
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)
            for content in ('time_device_s,value\n0,1\n0,2\n','time_device_s,value\n0,nan\n'):
                raw=out/'synthetic_encoder.csv';raw.write_text(content);d['channels'][0]['raw_source']['sha256']=hashlib.sha256(raw.read_bytes()).hexdigest();(out/'d.json').write_text(json.dumps(d))
                with self.assertRaises(ValueError):load_observation_dataset(out/'d.json',True)
    def test_near_collinear_nuisance_unresolved(self):
        v=np.array([1.,-1.,1.,-1.]); eps=2.**-40
        B=np.column_stack((np.ones(4),np.ones(4)+eps*v))
        np.testing.assert_array_equal(B@[-1/eps,1/eps],v)
        for tol in (1e-10,1e-14):
            r=local_observability(v[:,None],B,np.eye(4),[1],tol)
            self.assertIsNone(r['rank']);self.assertIsNone(r['noise_conditional_covariance'])
            self.assertEqual(r['rank_status'],'unresolved_nuisance_subspace')
    def test_bad_csv_and_clock_mapping(self):
        d=json.loads((ROOT/'data/synthetic_observations.json').read_text())
        cases=[('time_device_s,value\n0,1,x\n1,2,x\n',1,0),('time_device_s,value\n0,1\n1e-6,2\n',1,1e12),('time_device_s,value\n1e308,1\n1.1e308,2\n',10,0)]
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)
            for content,scale,offset in cases:
                raw=out/'synthetic_encoder.csv';raw.write_text(content)
                d['channels'][0]['raw_source']['sha256']=hashlib.sha256(raw.read_bytes()).hexdigest()
                d['channels'][0]['time_map'].update(scale=scale,offset_s=offset)
                (out/'d.json').write_text(json.dumps(d))
                with self.assertRaises(ValueError):load_observation_dataset(out/'d.json',True)
if __name__=='__main__':unittest.main()
