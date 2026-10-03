"""Conditional synthetic single-film observations; no actual hardware calibration.
Lengths: micrometres. exp(-i omega t); passive N=n+ik. Reuses byte-frozen T07 core.
Only real nonabsorbing semi-infinite substrate, smooth isotropic layer is executed.
Finite/backside/scattering/partial coherence contracts are deliberately rejected.
"""
from dataclasses import dataclass
import numpy as np
from vendor.optics_kernel import scattering


@dataclass(frozen=True)
class Contract:
    substrate_n: float = 1.52
    wavelength_domain_um: tuple = (0.4, 1.0)
    substrate_mode: str = 'semi_infinite'
    scatter: str = 'explicit_zero_synthetic'
    sample_state: str = 'synthetic_nondispersive_local_band'
    actual_hardware: object = None
    evidence: str = 'synthetic'

    def validate(self):
        if self.evidence != 'synthetic' or self.sample_state != 'synthetic_nondispersive_local_band':
            raise ValueError('this demonstration does not ingest actual or transferred material data')
        if self.substrate_mode != 'semi_infinite' or self.scatter != 'explicit_zero_synthetic':
            raise ValueError('unknown scatter or finite/backside response requires a new operator')
        if self.actual_hardware is not None:
            raise ValueError('no verified hardware adapter exists')
        if not np.isfinite(self.substrate_n) or self.substrate_n <= 0:
            raise ValueError('real positive substrate_n required')
        low, high = self.wavelength_domain_um
        if not np.isfinite([low, high]).all() or not 0 < low < high:
            raise ValueError('finite ordered positive wavelength domain required')


def node_arrays(wavelength_um, angle_deg, spectral_nodes=((0., 1.),), angle_nodes=((0., 1.),)):
    """Return product quadrature nodes. Offsets are um and degrees; weights dimensionless."""
    if not np.isfinite([wavelength_um, angle_deg]).all():
        raise ValueError('finite centers required')
    def validate(x):
        x = np.asarray(x, float)
        if x.ndim != 2 or x.shape[1] != 2 or not len(x) or not np.isfinite(x).all():
            raise ValueError('nonempty finite (offset,weight) nodes required')
        if np.any(x[:, 1] < 0) or not np.isclose(x[:, 1].sum(), 1., rtol=0, atol=1e-12):
            raise ValueError('nonnegative normalized weights required')
        return x
    s, a = validate(spectral_nodes), validate(angle_nodes)
    return [(wavelength_um+sw, angle_deg+aa, ww*wa) for sw, ww in s for aa, wa in a]


def amplitudes(theta, wavelength_um, angle_deg, contract=Contract()):
    contract.validate()
    p = np.asarray(theta, float)
    if p.shape != (3,) or not np.isfinite(p).all() or p[0] <= 0 or p[1] < 0 or p[2] < 0:
        raise ValueError('finite theta=(n,k,d_um), n>0,k>=0,d>=0 required')
    lo, hi = contract.wavelength_domain_um
    if not lo <= wavelength_um <= hi:
        raise ValueError('wavelength outside declared synthetic domain; no extrapolation')
    vals = [scattering(wavelength_um, [1., p[0]+1j*p[1], contract.substrate_n],
                       [p[2]], angle_deg, pol) for pol in ['s', 'p']]
    return {pol: {k: v[k][0] for k in ['r','R','T','A']} for pol, v in zip(['s','p'], vals)}


def ratio_from_amplitudes(rs, rp_tangential, convention='opposed_reflected_p', floor=1e-10):
    """rho = rp_basis/rs, not a universal instrument definition of Delta.
    opposed_reflected_p uses e_p,r=(-cos(theta),0,-sin(theta)), hence rp_basis=-rp_t.
    same_tangential_p uses kernel amplitudes directly. Time convention stays exp(-iwt).
    """
    if abs(rs) <= floor:
        raise ValueError('rho undefined/ill-conditioned near rs=0; use raw Jones/Mueller data')
    if convention not in ('opposed_reflected_p','same_tangential_p'):
        raise ValueError('explicit supported phase convention required')
    return (-1 if convention == 'opposed_reflected_p' else 1)*rp_tangential/rs


def circular_delta(a, b):
    """Principal radian phase difference; +/-pi represent the same branch-cut endpoint."""
    return np.angle(np.exp(1j*(np.asarray(a)-np.asarray(b))))


def psi_delta_to_rho(psi_rad, delta_rad, covariance_rad2=None):
    """Local covariance transport; rejects singular covariance instead of inventing noise."""
    if not np.isfinite([psi_rad,delta_rad]).all() or not 0 < psi_rad < np.pi/2:
        raise ValueError('interior finite Psi required; endpoint phase is not informative')
    t = np.tan(psi_rad); c,s = np.cos(delta_rad),np.sin(delta_rad)
    out = np.array([t*c,t*s])
    if covariance_rad2 is None:
        return out, None
    C = np.asarray(covariance_rad2, float)
    if C.shape != (2,2) or not np.isfinite(C).all() or not np.allclose(C,C.T,atol=1e-14,rtol=1e-12):
        raise ValueError('symmetric 2x2 covariance in radian squared required')
    np.linalg.cholesky(C)
    H = np.array([[(1+t*t)*c,-t*s],[(1+t*t)*s,t*c]])
    return out,H@C@H.T


def observe(theta, records, contract=Contract()):
    """records are explicit conditional channels: R/T, rho_reim, or independent d.
    rho_reim is restricted to a single monochromatic ray. Never average rho/Delta.
    A isn't offered as an additional independent datum because A=1-R-T.
    """
    theta=np.asarray(theta,float)
    if theta.shape!=(3,) or not np.isfinite(theta).all() or theta[0]<=0 or theta[1]<0 or theta[2]<0:
        raise ValueError('finite valid theta=(n,k,d_um) required')
    out=[]
    for record in records:
        kind=record['kind']
        if kind == 'd_geo':
            if record.get('independent') is not True:
                raise ValueError('geometric thickness must carry independent measurement declaration')
            contract.validate();out.append(float(theta[2]));continue
        if kind not in ('R','T','rho_reim'):
            raise ValueError('unsupported channel')
        nodes=node_arrays(record['wavelength_um'],record['angle_deg'],
                          record.get('spectral_nodes',((0.,1.),)),record.get('angle_nodes',((0.,1.),)))
        if kind == 'rho_reim':
            if len(nodes)!=1 or nodes[0][2]!=1:
                raise ValueError('mixed rays need coherency/Mueller operator, not averaged rho')
            w,a,_=nodes[0];v=amplitudes(theta,w,a,contract)
            rho=ratio_from_amplitudes(v['s']['r'],v['p']['r'],record['convention'])
            out.extend([rho.real,rho.imag]);continue
        pol=record.get('polarization')
        if pol not in ('s','p','unpolarized'):
            raise ValueError('explicit polarization required')
        value=0.
        for w,a,weight in nodes:
            v=amplitudes(theta,w,a,contract)
            value+=weight*(.5*(v['s'][kind]+v['p'][kind]) if pol=='unpolarized' else v[pol][kind])
        out.append(value)
    y=np.asarray(out,float)
    if not len(y) or not np.isfinite(y).all():raise ValueError('finite nonempty observation vector required')
    return y


def coherency_diagnostic(theta, record, contract=Contract()):
    """Equal p/s incident amplitudes, mutually incoherent ray mixture, common reference axes.
    Stokes convention Q=Cpp-Css,U=2Re(Cps),V=2Im(Cps). Not an instrument adapter.
    """
    C=np.zeros((2,2),complex)
    for w,a,weight in node_arrays(record['wavelength_um'],record['angle_deg'],
                                 record.get('spectral_nodes',((0.,1.),)),record.get('angle_nodes',((0.,1.),))):
        v=amplitudes(theta,w,a,contract)
        sign={'opposed_reflected_p':-1,'same_tangential_p':1}[record['convention']]
        j=np.array([sign*v['p']['r'],v['s']['r']])
        C+=weight*np.outer(j,j.conj())
    total=float(np.trace(C).real)
    if total<=1e-20:raise ValueError('no reflected signal')
    s=np.array([(C[0,0]-C[1,1]).real,2*C[0,1].real,2*C[0,1].imag])/total
    return {'coherency':C,'normalized_stokes':s,'degree_of_polarization':float(np.linalg.norm(s))}
