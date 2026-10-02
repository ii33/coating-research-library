#!/usr/bin/env python3
"""Independent T07 teaching kernel, NOT a production optical engine.

Planar, local, isotropic, nonmagnetic, passive N=n+ik (n>0,k>=0), exp(-iwt).
All lengths in micrometres; amplitudes are tangential E. Incident N must be
real; exact critical/grazing and active/anisotropic/magnetic media rejected.
No imported optical library. NumPy only. See reports/01 and 02 for derivation.
"""
import numpy as np


def prepare(wavelength_um, indices, thickness_um, angle_deg=0, polarization='s'):
    w = np.atleast_1d(np.asarray(wavelength_um, dtype=float))
    d = np.asarray(thickness_um, dtype=float)
    if w.ndim != 1 or not w.size or not np.all(np.isfinite(w)) or np.any(w <= 0):
        raise ValueError('positive finite 1-D wavelength_um required')
    if d.ndim != 1 or len(indices) != len(d)+2 or not np.all(np.isfinite(d)) or np.any(d < 0):
        raise ValueError('finite nonnegative thickness_um for each internal layer required')
    if polarization not in ('s', 'p') or not np.isfinite(angle_deg) or not 0 <= angle_deg < 89.9:
        raise ValueError('polarization s/p; real AOI [0,89.9) degrees required')
    n = np.array([np.broadcast_to(np.asarray(x, complex), w.shape) for x in indices])
    if not np.all(np.isfinite(n)) or np.any(n.real <= 0) or np.any(n.imag < 0):
        raise ValueError('passive finite N=n+ik, n>0, k>=0 required')
    if np.any(n[0].imag != 0):
        raise ValueError('absorbing incident medium not supported')
    beta = n[0].real*np.sin(np.deg2rad(angle_deg))
    kz = np.sqrt(n*n-beta*beta+0j) # dimensionless k_z/k_0
    kz = np.where((kz.imag < 0) | ((kz.imag == 0) & (kz.real < 0)), -kz, kz)
    if np.any(np.abs(kz) < 1e-14):
        raise ValueError('exact critical or grazing degeneracy not supported')
    q = kz if polarization == 's' else n*n/kz
    return w, n, d, beta, kz, q


def identity_s(count):
    out = np.zeros((count, 2, 2), complex)
    out[:, 0, 1] = out[:, 1, 0] = 1
    return out


def interface(q_left, q_right):
    den = q_left+q_right
    if np.any(den == 0):
        raise FloatingPointError('singular interface')
    out = np.empty((len(q_left), 2, 2), complex)
    out[:, 0, 0] = (q_left-q_right)/den
    out[:, 1, 1] = -out[:, 0, 0]
    out[:, 0, 1] = 2*q_right/den
    out[:, 1, 0] = 2*q_left/den
    return out


def propagation(delta):
    p = np.exp(1j*delta) # only decaying exponentials on our physical branch
    out = np.zeros((len(p), 2, 2), complex)
    out[:, 0, 1] = out[:, 1, 0] = p
    return out


def star(a, b):
    """Cascade a followed by b; S maps [a_left, b_right] to [b_left, a_right]."""
    den = 1-a[:, 1, 1]*b[:, 0, 0]
    if np.any(den == 0):
        raise FloatingPointError('unresolved zero resonance denominator')
    out = np.empty_like(a)
    out[:, 0, 0] = a[:, 0, 0]+a[:, 0, 1]*b[:, 0, 0]*a[:, 1, 0]/den
    out[:, 0, 1] = a[:, 0, 1]*b[:, 0, 1]/den
    out[:, 1, 0] = b[:, 1, 0]*a[:, 1, 0]/den
    out[:, 1, 1] = b[:, 1, 1]+b[:, 1, 0]*a[:, 1, 1]*b[:, 0, 1]/den
    if not np.all(np.isfinite(out)):
        raise FloatingPointError('nonfinite scattering cascade')
    return out


def scattering(wavelength_um, indices, thickness_um, angle_deg=0, polarization='s', fields=False):
    """R,T,A for incidence from left. A excludes absorption in exit half-space.

    Flux entering an absorbing exit is T, not far-field transmission through it.
    Zero T may be floating-point underflow, NOT a certified infinite optical density.
    fields=True returns stable amplitudes at layer faces and flux differences.
    """
    w,n,d,beta,kz,q = prepare(wavelength_um,indices,thickness_um,angle_deg,polarization)
    segments=[]
    for j in range(len(n)-1):
        segments.append(interface(q[j], q[j+1]))
        if j < len(d):
            segments.append(propagation(2*np.pi*kz[j+1]*d[j]/w))
    prefix=[identity_s(len(w))]
    min_den=np.ones(len(w))
    for s in segments:
        min_den=np.minimum(min_den,np.abs(1-prefix[-1][:,1,1]*s[:,0,0]))
        prefix.append(star(prefix[-1],s))
    S=prefix[-1]; r=S[:,0,0]; t=S[:,1,0]
    R=np.abs(r)**2; T=q[-1].real/q[0].real*np.abs(t)**2; A=1-R-T
    if np.any(A < -1e-9) or np.any(T < -1e-12):
        raise FloatingPointError('passivity violation; results have not been clipped')
    result=dict(r=r,t=t,R=R,T=T,A=A,S=S,q=q,kz=kz,beta=beta,
                minimum_cascade_denominator=min_den)
    if fields:
        suffix=[None]*(len(segments)+1); suffix[-1]=identity_s(len(w))
        for k in range(len(segments)-1,-1,-1):
            suffix[k]=star(segments[k],suffix[k+1])
        def state(cut):
            den=1-prefix[cut][:,1,1]*suffix[cut][:,0,0]
            if np.any(den==0): raise FloatingPointError('unresolved internal-field resonance')
            forward=prefix[cut][:,1,0]/den
            backward=suffix[cut][:,0,0]*forward
            return np.array([forward,backward])
        left=np.array([state(2*j-1) for j in range(1,len(d)+1)]).reshape(len(d),2,len(w))
        right=np.array([state(2*j) for j in range(1,len(d)+1)]).reshape(len(d),2,len(w))
        def flux(a,j):
            e=a[0]+a[1]; h=q[j]*(a[0]-a[1])
            return np.real(e*np.conj(h))/q[0].real
        fleft=np.array([flux(left[j-1],j) for j in range(1,len(d)+1)]).reshape(len(d),len(w))
        fright=np.array([flux(right[j-1],j) for j in range(1,len(d)+1)]).reshape(len(d),len(w))
        result.update(layer_left=left,layer_right=right,layer_flux_left=fleft,
                      layer_flux_right=fright,layer_absorptance=fleft-fright)
    return result


def characteristic_matrix(wavelength_um, indices, thickness_um, angle_deg=0, polarization='s'):
    """Naive direct product, deliberately unprotected, for demonstrating failure."""
    w,n,d,beta,kz,q=prepare(wavelength_um,indices,thickness_um,angle_deg,polarization)
    M=np.tile(np.eye(2,dtype=complex),(len(w),1,1))
    with np.errstate(over='ignore', invalid='ignore', divide='ignore', under='ignore'):
        for j,dj in enumerate(d,1):
            delta=2*np.pi*kz[j]*dj/w
            c=np.cos(delta); s=np.sin(delta)
            L=np.empty_like(M)
            L[:,0,0]=L[:,1,1]=c
            L[:,0,1]=-1j*s/q[j]; L[:,1,0]=-1j*q[j]*s
            M=M@L
        B=M[:,0,0]+M[:,0,1]*q[-1]; C=M[:,1,0]+M[:,1,1]*q[-1]
        den=q[0]*B+C
        r=(q[0]*B-C)/den; t=2*q[0]/den
        R=np.abs(r)**2; T=q[-1].real/q[0].real*np.abs(t)**2
    return dict(r=r,t=t,R=R,T=T,A=1-R-T,M=M)


def recursive(wavelength_um, indices, thickness_um, angle_deg=0, polarization='s'):
    """Independent scalar Airy recursion; no S matrices and no matrix multiply."""
    w,n,d,beta,kz,q=prepare(wavelength_um,indices,thickness_um,angle_deg,polarization)
    r=(q[-2]-q[-1])/(q[-2]+q[-1]); t=2*q[-2]/(q[-2]+q[-1])
    for j in range(len(d)-1,-1,-1):
        p=np.exp(2j*np.pi*kz[j+1]*d[j]/w)
        rij=(q[j]-q[j+1])/(q[j]+q[j+1])
        tij=2*q[j]/(q[j]+q[j+1])
        den=1+rij*r*p*p
        t=tij*t*p/den
        r=(rij+r*p*p)/den
    R=np.abs(r)**2; T=q[-1].real/q[0].real*np.abs(t)**2
    return dict(r=r,t=t,R=R,T=T,A=1-R-T)


def local_profile(wavelength_um, indices, thickness_um, layer, z_um, angle_deg=0, polarization='s'):
    """One wavelength, 0-based finite layer. Stable local E and absorbed power/um.
    normalized_absorption_density integrates to that layer's absorptance.
    Tangential E is unit amplitude in incident medium.
    """
    if np.ndim(wavelength_um)!=0 or not 0<=layer<len(thickness_um):
        raise ValueError('scalar wavelength and valid zero-based layer required')
    z=np.atleast_1d(np.asarray(z_um,float)); dj=thickness_um[layer]
    if not np.all(np.isfinite(z)) or np.any(z<0) or np.any(z>dj):
        raise ValueError('positions must be inside selected layer')
    v=scattering(wavelength_um,indices,thickness_um,angle_deg,polarization,fields=True)
    j=layer+1; kz=v['kz'][j,0]; q=v['q'][j,0]; beta=v['beta'][0]
    af=v['layer_left'][layer,0,0]*np.exp(2j*np.pi*kz*z/wavelength_um)
    bb=v['layer_right'][layer,1,0]*np.exp(2j*np.pi*kz*(dj-z)/wavelength_um)
    et=af+bb; h=q*(af-bb)
    ez=np.zeros_like(et) if polarization=='s' else -beta/kz*(af-bb)
    e2=np.abs(et)**2+np.abs(ez)**2
    nj=complex(indices[j]); density=2*np.pi/wavelength_um*(nj*nj).imag*e2/v['q'][0,0].real
    return dict(E_t=et,E_z=ez,E2=e2,flux=np.real(et*np.conj(h))/v['q'][0,0].real,
                normalized_absorption_density=density)


def intensity_combine(front, reverse_front, rear, one_way_power):
    """One incoherent separator, propagating real-index ports, all orders collected.
    Bulk attenuation is separate. Not a general absorbing-interface coherence model.
    """
    p=np.asarray(one_way_power,float)
    if not np.all(np.isfinite(p)) or np.any(p<0) or np.any(p>1):
        raise ValueError('one_way_power must be finite in [0,1]')
    den=1-reverse_front['R']*rear['R']*p*p
    if np.any(den<=0): raise FloatingPointError('closed singular intensity cavity')
    T=front['T']*rear['T']*p/den
    R=front['R']+front['T']*reverse_front['T']*rear['R']*p*p/den
    return dict(R=R,T=T,A=1-R-T)


def phase_derivatives(omega_rad_s, amplitude, floor=1e-8):
    """Fixed specified ray/geometry, increasing uniform omega; returns seconds, s^2.
    User must refine frequency spacing and exclude amplitude zeros/endpoints.
    """
    omega=np.asarray(omega_rad_s,float); h=np.asarray(amplitude,complex)
    if omega.ndim!=1 or len(omega)<5 or h.shape!=omega.shape or np.any(np.diff(omega)<=0):
        raise ValueError('matching increasing frequency and amplitude arrays required')
    if not np.all(np.isfinite(omega)) or not np.all(np.isfinite(h)) or np.any(np.abs(h)<floor):
        raise ValueError('nonfinite input or phase undefined near amplitude zero')
    if not np.allclose(np.diff(omega),np.diff(omega)[0],rtol=1e-7,atol=0):
        raise ValueError('uniform omega grid required')
    phase=np.unwrap(np.angle(h)); gd=np.gradient(phase,omega,edge_order=2)
    return dict(phase=phase,GD_s=gd,GDD_s2=np.gradient(gd,omega,edge_order=2))
