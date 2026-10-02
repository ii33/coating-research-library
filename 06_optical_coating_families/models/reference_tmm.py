#!/usr/bin/env python3
"""T06 small reference, isotropic planar films; units um; N=n+ik, exp(-iwt).
Tangential electric field admittance: s=qz, p=N^2/qz. Both r use the
same tangential E convention (p amplitude sign differs from some texts).
Real incident index only. No fitting, production optimization, roughness,
anisotropy, diffuse scattering, thermal prediction, or damage prediction.
"""
import numpy as np


def _wavelengths(w):
    w=np.atleast_1d(np.asarray(w,dtype=float))
    if w.ndim!=1 or not np.all(np.isfinite(w)) or np.any(w<=0):
        raise ValueError('wavelengths must be a positive finite one-dimensional array, in um')
    return w


def coherent(wavelength_um, indices, thickness_um, angle_deg=0, polarization='s'):
    """Coherent finite coating between semi-infinite media; T enters exit medium.
    Each index is scalar or one value per wavelength. A=1-R-T is absorption
    in the finite coating, not absorption downstream in a semi-infinite exit.
    """
    w=_wavelengths(wavelength_um)
    d=np.asarray(thickness_um,dtype=float)
    if d.ndim!=1 or len(indices)!=len(d)+2 or not np.all(np.isfinite(d)) or np.any(d<0):
        raise ValueError('one finite nonnegative physical thickness per internal layer')
    if polarization not in ('s','p') or not np.isfinite(angle_deg) or not 0<=angle_deg<89.9:
        raise ValueError('polarization s/p and incidence angle [0,89.9) degrees required')
    n=np.array([np.broadcast_to(np.asarray(x,dtype=complex),w.shape) for x in indices])
    if not np.all(np.isfinite(n)) or np.any(n.real<=0) or np.any(n.imag<0):
        raise ValueError('passive finite N=n+ik with n>0, k>=0 required')
    if np.any(n[0].imag!=0): raise ValueError('absorbing incident medium unsupported')
    kx=n[0]*np.sin(np.deg2rad(angle_deg))
    qz=np.sqrt(n*n-kx*kx+0j)
    # Decay forward in absorbing or evanescent layers, positive propagation otherwise.
    qz=np.where((qz.imag<0)|((qz.imag==0)&(qz.real<0)),-qz,qz)
    if np.any(np.abs(qz)<1e-14): raise ValueError('exact critical/grazing singularity unsupported')
    q=qz if polarization=='s' else n*n/qz
    a=np.ones_like(w,dtype=complex); b=np.zeros_like(a); c=b.copy(); e=a.copy()
    for j,dj in enumerate(d,1):
        delta=2*np.pi*qz[j]*dj/w
        if np.any(np.abs(delta.imag)>25):
            raise ValueError('opaque layer outside stable reference range; use scattering-matrix solver')
        u=np.cos(delta); v=-1j*np.sin(delta)/q[j]; z=-1j*q[j]*np.sin(delta)
        a,b,c,e=a*u+b*z,a*v+b*u,c*u+e*z,c*v+e*u
    B=a+b*q[-1]; C=c+e*q[-1]; den=q[0]*B+C
    r=(q[0]*B-C)/den; t=2*q[0]/den
    R=np.abs(r)**2; T=np.real(q[-1])/np.real(q[0])*np.abs(t)**2
    A=1-R-T
    if not np.all(np.isfinite(R+T+A)): raise FloatingPointError('nonfinite optical result')
    if np.any(R<-1e-9) or np.any(T<-1e-9) or np.any(A<-1e-8):
        raise FloatingPointError('passivity check failed; do not silently clip')
    return dict(R=R,T=T,A=A,r=r,t=t)


def combine_incoherent(front, reverse_front, back, attenuation):
    """Intensity sum, all specular orders collected; real-index interface media.
    front: external -> substrate; reverse_front: substrate -> external;
    back: substrate -> external. attenuation is one-way internal intensity P.
    Thick substrate interface absorption must be negligible; bulk alpha is
    separate. This is NOT a general strongly absorbing substrate solution.
    """
    p=np.asarray(attenuation,dtype=float)
    if not np.all(np.isfinite(p)) or np.any(p<0) or np.any(p>1):
        raise ValueError('one-way intensity attenuation must lie in [0,1]')
    den=1-reverse_front['R']*back['R']*p*p
    if np.any(den<=1e-14): raise ValueError('singular closed intensity cavity')
    T=front['T']*p*back['T']/den
    R=front['R']+front['T']*p*p*back['R']*reverse_front['T']/den
    return dict(R=R,T=T,A=1-R-T)


def plate(wavelength_um, n_external, n_substrate, layers, thickness_um,
          substrate_mm, alpha_cm_inv, angle_deg=0, polarization='s', rear='bare'):
    """Weak-interface-loss bulk plate, front layers incident -> substrate.
    rear='same' means the same coating seen from the outside of rear face;
    the physical ray inside the substrate encounters that coating reversed.
    """
    w=_wavelengths(wavelength_um)
    ns=np.broadcast_to(np.asarray(n_substrate,dtype=complex),w.shape)
    n0=np.broadcast_to(np.asarray(n_external,dtype=complex),w.shape)
    if np.any(ns.imag!=0) or np.any(n0.imag!=0):
        raise ValueError('plate interface indices must be real; bulk absorption uses alpha')
    if not np.isfinite(substrate_mm) or substrate_mm<0: raise ValueError('invalid substrate thickness')
    alpha=np.broadcast_to(np.asarray(alpha_cm_inv,dtype=float),w.shape)
    if np.any(~np.isfinite(alpha)) or np.any(alpha<0): raise ValueError('alpha must be finite nonnegative cm^-1')
    # Reference limits this function to constant n0 and ns over wavelength at oblique AOI.
    ratio=n0.real*np.sin(np.deg2rad(angle_deg))/ns.real
    if np.any(ratio>=1): raise ValueError('evanescent bulk plate unsupported')
    angles=np.rad2deg(np.arcsin(ratio))
    front=coherent(w,[n0,*layers,ns],thickness_um,angle_deg,polarization)
    if angle_deg and not np.allclose(angles,angles[0],atol=1e-12,rtol=0):
        # Dispersive Snell angles need separate scalar evaluations, not one wrong mean angle.
        rows=[]
        for j,wl in enumerate(w):
            nj=[complex(np.broadcast_to(np.asarray(n),w.shape)[j]) for n in layers]
            rows.append(plate([wl],n0[j],ns[j],nj,thickness_um,substrate_mm,alpha[j],angle_deg,polarization,rear))
        return {k:np.array([r[k][0] for r in rows]) for k in rows[0]}
    reverse=coherent(w,[ns,*layers[::-1],n0],thickness_um[::-1],float(angles[0]),polarization)
    if rear=='bare': back=coherent(w,[ns,n0],[],float(angles[0]),polarization)
    elif rear=='same': back=reverse
    else: raise ValueError('rear must be bare or same')
    p=np.exp(-alpha*(substrate_mm/10)/np.sqrt(1-ratio*ratio))
    total=combine_incoherent(front,reverse,back,p)
    total.update(front_R=front['R'],front_T=front['T'],front_A=front['A'],bulk_single_pass_T=p)
    return total


def evaluate_material(material,wavelength_um):
    """Explicit assumptions required in records; never interpolate outside declared bounds."""
    w=_wavelengths(wavelength_um); lo,hi=material['calculation_bounds_um']
    if np.any(w<lo) or np.any(w>hi): raise ValueError(f"{material['id']}: wavelength outside calculation bounds; extrapolation forbidden")
    if material['model']=='constant':
        return np.full(w.shape,complex(material['n'],material['k']))
    if material['model']=='linear_table':
        tab=np.array(material['table_wavelength_n_k'],dtype=float)
        if tab.ndim!=2 or tab.shape[1]!=3 or len(tab)<2 or np.any(np.diff(tab[:,0])<=0) or np.any(tab[:,1]<=0) or np.any(tab[:,2]<0) or not np.all(np.isfinite(tab)):
            raise ValueError('invalid sorted passive n/k table')
        if np.any(w<tab[0,0]) or np.any(w>tab[-1,0]): raise ValueError('table extrapolation forbidden')
        return np.interp(w,tab[:,0],tab[:,1])+1j*np.interp(w,tab[:,0],tab[:,2])
    raise ValueError('unknown material model')


def band_metrics(wavelength_um,spectrum,band):
    """Uniform wavelength weighting; endpoint interpolation, no external extrapolation."""
    w=_wavelengths(wavelength_um); lo,hi=band
    if np.any(np.diff(w)<=0) or not w[0]<=lo<hi<=w[-1]: raise ValueError('invalid band/grid')
    x=np.r_[lo,w[(w>lo)&(w<hi)],hi]; out={}
    for key in ['R','T','A']:
        y=np.interp(x,w,spectrum[key])
        out[key+'_mean']=float(np.trapezoid(y,x)/(hi-lo))
        out[key+'_min']=float(y.min());out[key+'_max']=float(y.max())
    out['wavelength_band_um']=[lo,hi]
    out['weighting']='uniform wavelength; sampled extrema, not certified continuous extrema'
    return out
