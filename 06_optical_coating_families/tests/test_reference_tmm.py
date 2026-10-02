import unittest,sys,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'models'))
from reference_tmm import coherent,plate,evaluate_material,band_metrics,combine_incoherent
from run_atlas import load,compute


def airy_independent(w,ns,ds,angle,pol):
    # Independent interface-recursion implementation, no characteristic matrices.
    ns=np.array(ns,dtype=complex);u=ns[0]*np.sin(np.deg2rad(angle));qz=np.sqrt(ns*ns-u*u+0j)
    q=qz if pol=='s' else ns*ns/qz
    rs=(q[:-1]-q[1:])/(q[:-1]+q[1:]);ts=2*q[:-1]/(q[:-1]+q[1:])
    r,t=rs[-1],ts[-1]
    for j in range(len(ds)-1,-1,-1):
        phase=np.exp(2j*np.pi*qz[j+1]*ds[j]/w);den=1+rs[j]*r*phase*phase
        r,t=(rs[j]+r*phase*phase)/den,ts[j]*t*phase/den
    return abs(r)**2,q[-1].real/q[0].real*abs(t)**2

class Physics(unittest.TestCase):
 def test_normal_fresnel(self):
  r=coherent([1],[1,1.5],[]);self.assertAlmostEqual(r['R'][0],.04,14);self.assertAlmostEqual(r['T'][0],.96,14)
 def test_p_brewster(self):
  r=coherent([1],[1,1.5],[],np.rad2deg(np.arctan(1.5)),'p');self.assertLess(r['R'][0],1e-27)
 def test_s_oblique_fresnel(self):
  th=np.deg2rad(45);th2=np.arcsin(np.sin(th)/1.5);r=((np.cos(th)-1.5*np.cos(th2))/(np.cos(th)+1.5*np.cos(th2)))**2
  self.assertAlmostEqual(coherent([1],[1,1.5],[],45,'s')['R'][0],r,14)
 def test_p_oblique_fresnel(self):
  th=np.deg2rad(45);th2=np.arcsin(np.sin(th)/1.5);r=((1.5*np.cos(th)-np.cos(th2))/(1.5*np.cos(th)+np.cos(th2)))**2
  self.assertAlmostEqual(coherent([1],[1,1.5],[],45,'p')['R'][0],r,14)
 def test_quarter_wave_ar(self):
  r=coherent([1.2],[1,np.sqrt(4),4],[1.2/8]);self.assertLess(r['R'][0],1e-27)
 def test_single_film_airy(self):
  ns=[1,1.7+.03j,2.4]
  for pol in ('s','p'):
   a=coherent([1.3],ns,[.34],43,pol);R,T=airy_independent(1.3,ns,[.34],43,pol)
   self.assertAlmostEqual(a['R'][0],R,13);self.assertAlmostEqual(a['T'][0],T,13)
 def test_random_lossless_conservation(self):
  rng=np.random.default_rng(19)
  for pol in ('s','p'):
   for _ in range(50):
    ns=[1,*rng.uniform(1.1,4.3,8),1.6];ds=rng.uniform(.01,.8,8);a=coherent(np.linspace(.7,2,31),ns,ds,67,pol)
    self.assertLess(np.max(np.abs(a['R']+a['T']-1)),3e-12)
 def test_random_absorbing_independent_recursion(self):
  rng=np.random.default_rng(37)
  for pol in ('s','p'):
   for _ in range(50):
    ns=[1,*(rng.uniform(1.2,3,6)+1j*rng.uniform(0,.3,6)),1.5];ds=rng.uniform(.01,.4,6);a=coherent([1.1],ns,ds,53,pol);R,T=airy_independent(1.1,ns,ds,53,pol)
    self.assertAlmostEqual(a['R'][0],R,12);self.assertAlmostEqual(a['T'][0],T,12);self.assertGreaterEqual(a['A'][0],0)
 def test_total_internal_reflection_s(self):
  a=coherent([1],[1.5,1],[],60,'s');self.assertAlmostEqual(a['R'][0],1,13);self.assertAlmostEqual(a['T'][0],0,13)
 def test_total_internal_reflection_p(self):
  a=coherent([1],[1.5,1],[],60,'p');self.assertAlmostEqual(a['R'][0],1,13);self.assertAlmostEqual(a['T'][0],0,13)
 def test_absorbing_exit_flux_not_bulk_absorption(self):
  a=coherent([1],[1,2+1j],[]);self.assertAlmostEqual(a['A'][0],0,13);self.assertAlmostEqual(a['R'][0],.2,13)
 def test_zero_thickness_identity(self):
  a=coherent([1],[1,2+.1j,1.5],[0]);b=coherent([1],[1,1.5],[])
  for k in ['R','T']:self.assertAlmostEqual(a[k][0],b[k][0],14)
 def test_split_homogeneous_layer(self):
  a=coherent([1],[1,2+.1j,1.5],[.4]);b=coherent([1],[1,2+.1j,2+.1j,1.5],[.15,.25])
  for k in ['R','T','A']:self.assertAlmostEqual(a[k][0],b[k][0],13)
 def test_reciprocity_transmission(self):
  a=coherent([1.1],[1,2+.1j,1.4,1.5],[.12,.3],45,'p');theta=np.rad2deg(np.arcsin(np.sin(np.pi/4)/1.5));b=coherent([1.1],[1.5,1.4,2+.1j,1],[.3,.12],theta,'p');self.assertAlmostEqual(a['T'][0],b['T'][0],13)
 def test_bare_lossless_ge_plate(self):
  a=plate([10],1,4,[],[],5,0);self.assertAlmostEqual(a['T'][0],(1-.36)/(1+.36),13);self.assertAlmostEqual(a['A'][0],0,13)
 def test_bare_absorbing_plate(self):
  a=plate([10],1,4,[],[],5,.2);p=np.exp(-.1);T=(1-.36)**2*p/(1-.36**2*p*p);R=.36+(1-.36)**2*.36*p*p/(1-.36**2*p*p)
  self.assertAlmostEqual(a['T'][0],T,13);self.assertAlmostEqual(a['R'][0],R,13);self.assertGreater(a['A'][0],0)
 def test_incoherent_equals_phase_average(self):
  # Uniform one-way phase of homogeneous slab is equivalent to incoherent averaging.
  phases=np.linspace(0,np.pi,10001,endpoint=False); vals=[]
  for phase in phases:vals.append(coherent([1],[1,1.5,1],[phase/(2*np.pi*1.5)])['T'][0])
  target=plate([1],1,1.5,[],[],1,0)['T'][0];self.assertAlmostEqual(float(np.mean(vals)),target,12)
 def test_oblique_bulk_path(self):
  a=plate([1],1,1.5,[],[],10,.1,45);cos=np.sqrt(1-(np.sin(np.pi/4)/1.5)**2);self.assertAlmostEqual(a['bulk_single_pass_T'][0],np.exp(-.1/cos),14)
 def test_dispersive_oblique_plate_scalar_equivalence(self):
  a=plate([3,4],1,np.array([4.04,4.02]),[np.array([2.23,2.22])],[.4],5,.01,30,'p','same')
  for j,(w,n,l) in enumerate(zip([3,4],[4.04,4.02],[2.23,2.22])):
   b=plate([w],1,n,[l],[.4],5,.01,30,'p','same');self.assertAlmostEqual(a['T'][j],b['T'][0],14)
 def test_normal_s_p_equality(self):
  a=coherent([1.3],[1,2+.1j,1.4,1.5],[.2,.3],0,'s');b=coherent([1.3],[1,2+.1j,1.4,1.5],[.2,.3],0,'p');self.assertAlmostEqual(a['R'][0],b['R'][0],14)

class Guards(unittest.TestCase):
 def test_forbid_extrapolation(self):
  _,m=load()
  with self.assertRaises(ValueError):evaluate_material(m['K9_NIR_proxy'],[10])
 def test_no_ybf3_lwir_extrapolation(self):
  _,m=load()
  with self.assertRaises(ValueError):evaluate_material(m['YbF3_MWIR_proxy'],[10])
 def test_negative_k(self):
  with self.assertRaises(ValueError):coherent([1],[1,2-.1j,1.5],[.2])
 def test_negative_thickness(self):
  with self.assertRaises(ValueError):coherent([1],[1,2,1.5],[-.2])
 def test_absorbing_incident(self):
  with self.assertRaises(ValueError):coherent([1],[1+.1j,2],[])
 def test_bad_polarization(self):
  with self.assertRaises(ValueError):coherent([1],[1,2],[],0,'u')
 def test_bad_unit_value(self):
  with self.assertRaises(ValueError):coherent([0],[1,2],[])
 def test_nonfinite(self):
  with self.assertRaises(ValueError):coherent([1],[1,np.nan],[])
 def test_opaque_layer_guard(self):
  with self.assertRaises(ValueError):coherent([1],[1,2+10j,1.5],[100])
 def test_absorbing_substrate_plate_guard(self):
  with self.assertRaises(ValueError):plate([1],1,1.5+.1j,[],[],1,.2)
 def test_negative_alpha(self):
  with self.assertRaises(ValueError):plate([1],1,1.5,[],[],1,-.2)
 def test_bad_rear(self):
  with self.assertRaises(ValueError):plate([1],1,1.5,[],[],1,0,rear='unknown')
 def test_bad_band(self):
  with self.assertRaises(ValueError):band_metrics([1,2],dict(R=[0,0],T=[1,1],A=[0,0]),[.9,1.2])
 def test_table_order(self):
  m=dict(id='x',model='linear_table',calculation_bounds_um=[1,2],table_wavelength_n_k=[[2,2,0],[1,1,0]])
  with self.assertRaises(ValueError):evaluate_material(m,[1.5])

class Atlas(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.examples,cls.materials=load()
 def test_six_stacks_and_explicit_assumptions(self):
  self.assertEqual(len(self.examples),6)
  for m in self.materials.values():self.assertTrue(m['assumptions']);self.assertFalse(m['design_ready']);self.assertTrue(m['anchor_records'])
 def test_unit_consistency(self):
  for e in self.examples:
   for d in e['layers']:self.assertAlmostEqual(d['thickness_nm'],d['thickness_um']*1000,12)
 def test_all_sampled_passive(self):
  for e in self.examples:
   w,sp=compute(e,self.materials,points=31)
   for a in sp.values():
    self.assertLess(np.max(np.abs(a['R']+a['T']+a['A']-1)),1e-12)
    self.assertGreater(np.min(a['A']),-1e-9)
 def test_grid_convergence(self):
  for e in self.examples:
   num=e['wavelength_grid_um'][2]; w,a=compute(e,self.materials);v,b=compute(e,self.materials,points=2*num-1)
   for band in e['bands_um'].values():
    x=band_metrics(w,a['0_s'],band);y=band_metrics(v,b['0_s'],band)
    self.assertLess(abs(x['T_mean']-y['T_mean']),1e-5)
    self.assertLess(abs(x['T_min']-y['T_min']),1e-5)
 def test_dual_minimum_is_not_broadband(self):
  e=self.examples[2];w,s=compute(e,self.materials);m=band_metrics(w,s['0_s'],[3,5]);self.assertLess(m['T_min'],.5)
 def test_single_cavity_does_not_prove_od3(self):
  e=self.examples[4];w,s=compute(e,self.materials);m=band_metrics(w,s['0_s'],[.97,1]);self.assertGreater(m['T_max'],.001)
 def test_protected_al_absorbs(self):
  e=self.examples[5];w,s=compute(e,self.materials,points=51);self.assertGreater(s['0_s']['A'].min(),.01)
 def test_ar_backsurface_matters(self):
  e=self.examples[1];w,a=compute(e,self.materials,rear='bare',points=61);v,b=compute(e,self.materials,rear='same',points=61);self.assertGreater(b['0_s']['T'].mean()-a['0_s']['T'].mean(),.25)

if __name__=='__main__':unittest.main(verbosity=2)
