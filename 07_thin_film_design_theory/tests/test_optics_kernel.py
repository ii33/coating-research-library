import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'models'))
from optics_kernel import (scattering, characteristic_matrix, recursive, local_profile,
                           intensity_combine, phase_derivatives, star, identity_s, interface, propagation)

class OpticsTests(unittest.TestCase):
    def close(self,x,y,tol=2e-12): np.testing.assert_allclose(x,y,atol=tol,rtol=tol)
    def test_bare_interface(self):
        for pol in ('s','p'):
            o=scattering(1,[1.3,1.7],[],polarization=pol)
            self.close(o['r'],-.4/3); self.close(o['t'],2.6/3)
            self.close(o['R']+o['T'],1)
    def test_brewster(self):
        o=scattering(1,[1,1.5],[],np.degrees(np.arctan(1.5)),'p')
        self.assertLess(float(o['R'][0]),1e-29)
    def test_total_internal_reflection(self):
        for pol in ('s','p'):
            o=scattering(1,[1.5,1],[],50,pol)
            self.close(o['R'],1); self.close(o['T'],0)
            self.assertGreater(o['kz'][-1,0].imag,0)
    def test_frustrated_total_internal_reflection(self):
        for pol in ('s','p'):
            o=scattering(1,[1.5,1,1.5],[.08],50,pol)
            self.assertGreater(o['T'][0],0); self.close(o['R']+o['T'],1)
            self.close(o['t'],recursive(1,[1.5,1,1.5],[.08],50,pol)['t'])
    def test_zero_thickness(self):
        self.close(scattering(1,[1,3+.5j,1.5],[0])['r'],scattering(1,[1,1.5],[])['r'])
    def test_equal_index_layer(self):
        o=scattering([.8,1,1.3],[1.5,1.5,1.5],[.4]); self.close(o['R'],0)
        self.close(o['t'],np.exp(2j*np.pi*1.5*.4/np.array([.8,1,1.3])))
    def test_layer_splitting(self):
        for pol in ('s','p'):
            a=scattering([.8,1,1.3],[1,2+.1j,1.5],[.7],50,pol)
            b=scattering([.8,1,1.3],[1,2+.1j,2+.1j,1.5],[.31,.39],50,pol)
            self.close(a['r'],b['r']); self.close(a['t'],b['t'])
    def test_quarter_wave_ar(self):
        ns=1.52; nf=np.sqrt(ns); w=1.5
        o=scattering(w,[1,nf,ns],[w/4/nf]); self.assertLess(o['R'][0],1e-29)
    def test_quarter_wave_mirror(self):
        h,l,ns,m=2.1,1.45,1.52,8
        o=scattering(1,[1]+[h,l]*m+[ns],[1/4/h,1/4/l]*m)
        y=ns*(h/l)**(2*m); self.close(o['R'],((1-y)/(1+y))**2)
    def test_characteristic_determinant_moderate(self):
        v=characteristic_matrix([.8,1,1.2],[1,1.6+.02j,2.2,1.5],[.1,.2],35,'p')
        self.close(np.linalg.det(v['M']),1)
    def test_random_cross_solver_and_passivity(self):
        rng=np.random.default_rng(702)
        for loss in (0,.08):
            for pol in ('s','p'):
                for _ in range(20):
                    n=[1,*list(rng.uniform(1.3,3,8)+1j*rng.uniform(0,loss,8)),1.6]
                    d=rng.uniform(.01,.3,8); ang=float(rng.uniform(0,70)); w=np.array([.7,1,1.5])
                    a=scattering(w,n,d,ang,pol,fields=True)
                    for b in (recursive(w,n,d,ang,pol),characteristic_matrix(w,n,d,ang,pol)):
                        self.close(a['r'],b['r']);self.close(a['t'],b['t'])
                    self.assertGreater(np.min(a['A']),-2e-12)
                    self.assertGreater(np.min(a['layer_absorptance']),-2e-12)
                    self.close(np.sum(a['layer_absorptance'],axis=0),a['A'])
    def test_reciprocity_same_beta(self):
        for pol in ('s','p'):
            for loss in (0,.15):
                n=[1.2,2.4+1j*loss,1.45,2.0+.5j*loss,1.7];d=[.14,.22,.18];a0=40
                a1=np.degrees(np.arcsin(n[0]*np.sin(np.deg2rad(a0))/n[-1]))
                a=scattering([.8,1,1.3],n,d,a0,pol);b=scattering([.8,1,1.3],n[::-1],d[::-1],a1,pol)
                self.close(a['T'],b['T']);self.close(a['q'][-1]*a['t'],a['q'][0]*b['t'])
                if loss==0:self.close(a['R'],b['R'])
                else:self.assertGreater(np.max(np.abs(a['R']-b['R'])),.01)
    def test_power_normalized_s_matrix(self):
        for loss in (0,.2):
            o=scattering(1,[1,2+1j*loss,1.4,1.8],[.15,.23],40,'p')
            q0,q1=o['q'][0,0].real,o['q'][-1,0].real
            D=np.diag(np.sqrt([q0,q1])); sn=D@o['S'][0]@np.linalg.inv(D)
            self.close(sn,sn.T)
            eigen=np.linalg.eigvalsh(sn.conj().T@sn)
            self.assertLessEqual(eigen.max(),1+2e-12)
            if loss==0:self.close(eigen,[1,1])
    def test_absorbing_exit_flux(self):
        for pol in ('s','p'):
            o=scattering(1,[1,2+.3j],[],45,pol)
            self.close(o['A'],0)
            self.close(o['R']+o['T'],1)
    def test_local_absorption_density(self):
        for pol in ('s','p'):
            n=[1,1.8+.09j,2.2+.17j,1.6];d=[.23,.31]
            o=scattering(1,n,d,38,pol,fields=True)
            for j,dj in enumerate(d):
                z=np.linspace(0,dj,10001); p=local_profile(1,n,d,j,z,38,pol)
                self.close(np.trapezoid(p['normalized_absorption_density'],z),o['layer_absorptance'][j,0],1e-8)
                self.close(p['flux'][0]-p['flux'][-1],o['layer_absorptance'][j,0])
    def test_opaque_limit_and_transfer_overflow(self):
        n=[1,.2+6j,1.5];d=[100]
        for pol in ('s','p'):
            o=scattering(1,n,d,0,pol,fields=True)
            r=(1-n[1])/(1+n[1]);self.close(o['r'],r);self.close(o['T'],0)
            self.close(o['layer_absorptance'].sum(axis=0),o['A'])
            self.assertFalse(np.all(np.isfinite(characteristic_matrix(1,n,d)['r'])))
    def test_lossless_many_pairs(self):
        o=scattering(1,[1]+[2.1,1.45]*1200+[1.52],[1/8.4,1/5.8]*1200)
        self.close(o['R'],1);self.assertTrue(np.isfinite(o['T']).all())
    def test_star_associativity(self):
        a=interface(np.array([1.]),np.array([2.]));b=propagation(np.array([.4+.5j]));c=interface(np.array([2.]),np.array([1.5]))
        self.close(star(star(a,b),c),star(a,star(b,c)))
        self.close(star(a,identity_s(1)),a)
    def test_incoherent_plate_phase_average(self):
        front=scattering(1,[1,1.5],[]);rear=scattering(1,[1.5,1],[])
        inc=intensity_combine(front,rear,rear,1)
        phi=np.arange(4096)*2*np.pi/4096
        amp=np.array([scattering(1,[1,1.5,1],[v/(3*np.pi)])['t'][0] for v in phi])
        self.close(np.mean(abs(amp)**2),inc['T']);self.assertLess(abs(amp.mean())**2,1e-25)
        self.close(inc['T'],(1-.04)/(1+.04))
    def test_group_delay_sign(self):
        omega=np.linspace(1e15,1.01e15,101);tau=15e-15
        v=phase_derivatives(omega,np.exp(1j*omega*tau))
        self.close(v['GD_s'],tau,1e-25)
        self.assertLess(np.max(np.abs(v['GDD_s2'][2:-2])),1e-34)
    def test_no_phase_at_zero(self):
        with self.assertRaises(ValueError): phase_derivatives(np.arange(5.),np.zeros(5))
    def test_t06_frozen_reference(self):
        prev=ROOT.parent/'06_optical_coating_families'
        spec=importlib.util.spec_from_file_location('t06_reference',prev/'models/reference_tmm.py')
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        mats=json.loads((prev/'data/material_proxies.json').read_text())['materials']
        lookup=mats
        cases=json.loads((prev/'data/starter_stacks.json').read_text())['examples']
        for ex in cases:
            w=np.linspace(*ex['wavelength_grid_um'][:2],151)
            n=[np.ones_like(w),*[mod.evaluate_material(lookup[x['material']],w) for x in ex['layers']],mod.evaluate_material(lookup[ex['substrate']],w)]
            d=[x['thickness_um'] for x in ex['layers']]
            for ang in ex['angles_deg']:
                for pol in ('s','p'):
                    a=scattering(w,n,d,ang,pol);b=mod.coherent(w,n,d,ang,pol)
                    self.close(a['r'],b['r'],5e-11);self.close(a['T'],b['T'],5e-11)
    def test_empty_stack_fields(self):
        o=scattering([1,2],[1,1.5],[],fields=True)
        self.assertEqual(o['layer_absorptance'].shape,(0,2))
        self.close(o['layer_absorptance'].sum(axis=0),o['A'])
    def test_band_edges_from_trace(self):
        h,l=2.1,1.45;gap=4/np.pi*np.arcsin((h-l)/(h+l))
        for w in [1/(1+gap/2),1/(1-gap/2)]:
            m=characteristic_matrix(w,[1,h,l,1],[1/(4*h),1/(4*l)])['M'][0]
            self.close(np.trace(m)/2,-1)
    def test_symmetric_equivalent_layer(self):
        for w in [.7,.9,1.,1.4,2.]:
            m=characteristic_matrix(w,[1,2.1,1.45,2.1,1],[1/16.8,1/5.8,1/16.8])['M'][0]
            self.close(m[0,0],m[1,1]);delta=np.arccos(complex(m[0,0]));q=-1j*np.sin(delta)/m[0,1]
            me=np.array([[np.cos(delta),-1j*np.sin(delta)/q],[-1j*q*np.sin(delta),np.cos(delta)]])
            self.close(m,me)
    def test_cavity_gd_converges(self):
        c=299792458.;w0=2*np.pi*c/(1.5e-6);expected=1.5*5e-6/c*1.04/.96
        errors=[]
        for count in [101,201,401]:
            omega=np.linspace(.995*w0,1.005*w0,count);wl=2*np.pi*c/omega*1e6
            a=scattering(wl,[1,1.5,1],[5])['t']
            gd=phase_derivatives(omega,a)['GD_s'][count//2]
            errors.append(abs(gd-expected))
        self.assertLess(errors[-1],errors[0]/10)
        self.assertLess(errors[-1],2e-21)
    def test_source_normalization_counterexample(self):
        q0,qs=1.3,1.7
        t_printed=2/(q0+qs)
        t_conventional=scattering(1,[q0,qs],[])['t'][0]
        self.assertGreater(abs(t_printed-t_conventional),.1)
        self.close(q0*qs*t_printed**2,(qs/q0)*abs(t_conventional)**2)
    def test_invalid_inputs(self):
        cases=[(0,[1,1.5],[],0,'s'),(1,[1,1.5],[-1],0,'s'),(1,[1+.01j,1.5],[],0,'s'),
               (1,[1,1.5-.01j],[],0,'s'),(1,[1,1.5],[],90,'s'),(1,[1,1.5],[],0,'x'),
               (1,[1,0],[],0,'s'),(1,[1,1.5],[],float('nan'),'s')]
        for args in cases:
            with self.assertRaises(ValueError):scattering(*args)
        with self.assertRaises(ValueError):scattering(1,[1.5,1],[],np.degrees(np.arcsin(1/1.5)))

if __name__=='__main__': unittest.main(verbosity=2)
