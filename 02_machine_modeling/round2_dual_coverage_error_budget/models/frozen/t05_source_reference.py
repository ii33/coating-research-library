"""T05 v0.1 reference only: SI, free-molecular positive mass kernels.
No hardware connections; no real material constants or production recipes.
"""
from dataclasses import dataclass
import numpy as np

R = 8.31446261815324
SIGMA = 5.670374419e-8


def finite(a, name):
    a = np.asarray(a, dtype=float)
    if not np.all(np.isfinite(a)):
        raise ValueError(name + ' must be finite')
    return a


def unit_rows(a, name):
    a = finite(a, name)
    if a.ndim != 2 or a.shape[1] != 3:
        raise ValueError(name + ' must be N by 3')
    if not np.allclose(np.linalg.norm(a, axis=1), 1, atol=1e-10, rtol=0):
        raise ValueError(name + ' must contain unit normals')
    return a


def cosine_pdf(mu, n):
    """Angular density per sr on the FRONT hemisphere; n>=0, not radiance."""
    mu = finite(mu, 'mu')
    n = float(finite(n, 'n'))
    if n < 0 or np.any(np.abs(mu) > 1 + 1e-12):
        raise ValueError('n>=0 and -1<=mu<=1 required')
    out = np.zeros_like(mu)
    front = mu > 0  # prevents back emission for n=0, 0**0
    out[front] = (n + 1) / (2 * np.pi) * np.minimum(mu[front], 1)**n
    return out


@dataclass
class Source:
    nodes_m: np.ndarray
    normals: np.ndarray
    fractions: np.ndarray
    exponent: float = 1.0

    def validate(self):
        p = finite(self.nodes_m, 'nodes')
        n = unit_rows(self.normals, 'source normals')
        w = finite(self.fractions, 'fractions')
        if p.ndim != 2 or p.shape[1] != 3 or n.shape != p.shape or w.shape != (len(p),):
            raise ValueError('source dimensions disagree')
        if not len(w) or np.any(w < 0) or not np.isclose(w.sum(), 1, atol=1e-12, rtol=0):
            raise ValueError('nonnegative fractions must sum to one')
        cosine_pdf(np.array([1.]), self.exponent)
        return p, n, w


def disk_source(radius_m, nr=12, nphi=48, exponent=1, center=(0, 0, 0)):
    """Equal-area midpoint rings; nr*nphi positive mass-fraction nodes."""
    radius_m = float(finite(radius_m, 'radius'))
    center = finite(center, 'center')
    if radius_m < 0 or center.shape != (3,) or not isinstance(nr, int) or not isinstance(nphi, int) or min(nr, nphi) < 1:
        raise ValueError('invalid disk geometry')
    if radius_m == 0:
        return Source(center[None, :], np.array([[0., 0., 1.]]), np.array([1.]), exponent)
    r = radius_m * np.sqrt((np.arange(nr) + 0.5) / nr)
    phi = 2 * np.pi * (np.arange(nphi) + 0.5) / nphi
    rr, pp = np.meshgrid(r, phi, indexing='ij')
    nodes = np.column_stack((rr.ravel()*np.cos(pp.ravel()), rr.ravel()*np.sin(pp.ravel()), np.zeros(rr.size))) + center
    return Source(nodes, np.tile([0., 0., 1.], (rr.size, 1)), np.full(rr.size, 1/rr.size), exponent)


def rectangle_source(width_m, length_m, nx=16, ny=8, exponent=1):
    dims = finite([width_m, length_m], 'rectangle dimensions')
    if np.any(dims <= 0) or not isinstance(nx, int) or not isinstance(ny, int) or min(nx, ny) < 1:
        raise ValueError('positive rectangle dimensions and integer resolution required')
    x = ((np.arange(nx)+0.5)/nx-0.5)*width_m
    y = ((np.arange(ny)+0.5)/ny-0.5)*length_m
    xx, yy = np.meshgrid(x, y)
    nodes = np.column_stack((xx.ravel(), yy.ravel(), np.zeros(xx.size)))
    return Source(nodes, np.tile([0., 0., 1.], (xx.size, 1)), np.full(xx.size, 1/xx.size), exponent)


def gaussian_footprint(source, center_xy_m, sigma_m, floor_fraction=0):
    """Phenomenological emission footprint, NOT temperature or deposited beam power.
    floor_fraction is a convex uniform/background mixture, in [0,1].
    """
    nodes, normals, base = source.validate()
    c = finite(center_xy_m, 'center_xy')
    vals = finite([sigma_m, floor_fraction], 'footprint parameters')
    if c.shape != (2,) or sigma_m <= 0 or not 0 <= floor_fraction <= 1:
        raise ValueError('invalid footprint')
    logg = -np.sum((nodes[:, :2]-c)**2, axis=1)/(2*sigma_m**2)
    active = base > 0
    g = np.zeros_like(base)
    g[active] = base[active] * np.exp(logg[active]-logg[active].max())
    g /= g.sum()
    weights = (1-floor_fraction)*g + floor_fraction*base
    return Source(nodes, normals, weights, source.exponent)


def flux_kg_m2_s(source, receivers_m, receiver_normals, mass_rate_kg_s, visibility=None):
    """Incident mass flux. visibility shape (Nreceiver,Nsource), 0..1.
    mass_rate is pre-occlusion emitted hemispherical mass, not QCM nm/s.
    """
    s, ns, w = source.validate()
    x = finite(receivers_m, 'receivers')
    nx = unit_rows(receiver_normals, 'receiver normals')
    q = float(finite(mass_rate_kg_s, 'mass rate'))
    if x.ndim != 2 or x.shape[1] != 3 or nx.shape != x.shape or q < 0:
        raise ValueError('invalid receivers or mass rate')
    d = x[:, None, :] - s[None, :, :]
    rr = np.linalg.norm(d, axis=2)
    if np.any((rr <= 0) & (w[None, :] > 0)):
        raise ValueError('receiver coincides with active source')
    rr = np.where(rr > 0, rr, 1.)  # zero-weight nodes must not make false singularities
    u = d / rr[:, :, None]
    mu_s = np.einsum('ijk,jk->ij', u, ns)
    mu_i = np.maximum(0, -np.einsum('ijk,ik->ij', u, nx))
    v = np.ones_like(rr) if visibility is None else finite(visibility, 'visibility')
    if v.shape != rr.shape or np.any(v < 0) or np.any(v > 1):
        raise ValueError('visibility must be Nreceiver by Nsource in [0,1]')
    return q * np.sum(cosine_pdf(mu_s, source.exponent) * mu_i * v / rr**2 * w, axis=1)


def circular_aperture(source, receivers_m, plane_z_m, radius_m, center_xy=(0, 0)):
    """Single zero-thickness horizontal aperture. No wall re-emission/scattering.
    Used for illustrative rim recession ONLY where plane lies between every ray.
    """
    all_s, _, w = source.validate()
    active = w > 0
    s = all_s[active]
    x = finite(receivers_m, 'receivers')
    c = finite(center_xy, 'aperture center')
    finite([plane_z_m, radius_m], 'aperture parameters')
    if x.ndim != 2 or x.shape[1] != 3 or c.shape != (2,) or radius_m <= 0:
        raise ValueError('invalid aperture')
    dz = x[:, None, 2]-s[None, :, 2]
    if np.any(dz == 0):
        raise ValueError('horizontal ray cannot use this aperture')
    t = (plane_z_m-s[None, :, 2])/dz
    if np.any(t <= 0) or np.any(t >= 1):
        raise ValueError('aperture must strictly separate all sources and receivers')
    hit = s[None, :, :2]+t[:, :, None]*(x[:, None, :2]-s[None, :, :2])
    out = np.zeros((len(x), len(all_s)))
    out[:, active] = (np.sum((hit-c)**2, axis=2) <= radius_m**2).astype(float)
    return out


def fit_point_logflux(receivers_m, receiver_normals, flux, sigma_log=0.01, center=(0, 0, 0)):
    """Weighted log-space least squares, known geometry, independent lognormal errors.
    Fit only Q,n. Covariance is local, conditional on this geometry/model/noise.
    """
    x = finite(receivers_m, 'receivers')
    nx = unit_rows(receiver_normals, 'receiver normals')
    j = finite(flux, 'observed flux')
    c = finite(center, 'center')
    sd = np.broadcast_to(finite(sigma_log, 'sigma_log'), j.shape)
    if x.ndim != 2 or x.shape[1] != 3 or nx.shape != x.shape or j.shape != (len(x),) or c.shape != (3,) or np.any(j <= 0) or np.any(sd <= 0):
        raise ValueError('invalid fit data')
    d = x-c
    rr = np.linalg.norm(d, axis=1)
    if np.any(rr <= 0):
        raise ValueError('zero distance')
    u = d/rr[:, None]
    mu = u[:, 2]
    mui = -np.sum(u*nx, axis=1)
    if np.any(mu <= 0) or np.any(mui <= 0):
        raise ValueError('fit requires front-side positive projections')
    y = np.log(j*rr**2/mui)
    X = np.column_stack((np.ones(len(x)), np.log(mu)))
    A, b = X/sd[:, None], y/sd
    if np.linalg.matrix_rank(A) < 2:
        raise ValueError('Q,n not identifiable from this angular layout')
    beta = np.linalg.lstsq(A, b, rcond=None)[0]
    bound = bool(beta[1] < 0)
    if bound:
        beta = np.array([np.sum(y/sd**2)/np.sum(1/sd**2), 0.])
    n = float(beta[1]); logq = float(beta[0]+np.log(2*np.pi)-np.log(n+1))
    covariance_beta = np.linalg.inv(A.T@A)
    J = np.array([[1, -1/(n+1)], [0, 1]])
    residuals = (X@beta-y)/sd
    return {'mass_rate_kg_s':float(np.exp(logq)), 'exponent':n,
            'chi2':float(residuals@residuals), 'degrees_of_freedom':None if bound else len(x)-2,
            'df_note':'boundary constrained fit: ordinary chi-square df not assigned' if bound else 'interior fixed-geometry two-parameter fit',
            'covariance_logQ_n':None if bound else (J@covariance_beta@J.T).tolist(),
            'scaled_design_condition':float(np.linalg.cond(A)),
            'boundary_fit':bound}


def vapor_pressure_pa(T_K, T_ref_K, p_ref_Pa, delta_H_J_mol):
    """Local constant-enthalpy Clausius-Clapeyron approximation for ONE species.
    User must supply a validated temperature interval; do not fit from melting point.
    """
    a = finite([T_K, T_ref_K, p_ref_Pa, delta_H_J_mol], 'vapor parameters')
    if np.any(a <= 0):
        raise ValueError('positive vapor parameters required')
    try:
        with np.errstate(over='raise', invalid='raise'):
            value = p_ref_Pa*np.exp(-delta_H_J_mol/R*(1/T_K-1/T_ref_K))
    except FloatingPointError as exc:
        raise ValueError('vapor pressure exceeds numerical/model domain') from exc
    return float(finite(value, 'computed vapor pressure'))


def hertz_knudsen_kg_m2_s(T_K, p_eq_Pa, molar_mass_kg_mol, alpha=1, p_back_Pa=0):
    """Net evaporation under equal-temperature ideal single-species approximation.
    Condensation branch deliberately rejected, not silently clipped.
    """
    finite([T_K,p_eq_Pa,molar_mass_kg_mol,alpha,p_back_Pa], 'HK parameters')
    if T_K <= 0 or molar_mass_kg_mol <= 0 or p_back_Pa < 0 or p_eq_Pa < p_back_Pa or not 0 <= alpha <= 1:
        raise ValueError('invalid HK evaporation conditions')
    value = alpha*(p_eq_Pa-p_back_Pa)*np.sqrt(molar_mass_kg_mol/(2*np.pi*R*T_K))
    return float(finite(value, 'computed evaporation flux'))


def lumped_history(parameters, power_W, dt_s):
    """Explicit Euler pedagogical heat/mass balance; single phase, fixed effective C.
    power_W[k] acts over [k*dt,(k+1)*dt]. Returns edge states and step-average Q.
    All parameters are required; NO defaults are a material/production calibration.
    """
    p = parameters; power = finite(power_W, 'power')
    req = ['initial_temperature_K','bath_temperature_K','effective_heat_capacity_J_K',
           'conductance_W_K','emissivity','radiating_area_m2','evaporating_area_m2',
           'latent_heat_J_kg','initial_mass_kg','molar_mass_kg_mol','T_ref_K','p_ref_Pa',
           'delta_H_J_mol','alpha','absorbed_fraction','valid_T_min_K','valid_T_max_K']
    vals = finite([p[k] for k in req], 'thermal parameters')
    finite(dt_s, 'dt')
    if power.ndim != 1 or np.any(power < 0) or dt_s <= 0 or np.any(vals < 0):
        raise ValueError('invalid heat history inputs')
    if min(p['effective_heat_capacity_J_K'],p['initial_temperature_K'],p['bath_temperature_K']) <= 0:
        raise ValueError('positive heat capacity and absolute temperatures required')
    if not all(0 <= p[k] <= 1 for k in ['emissivity','alpha','absorbed_fraction']):
        raise ValueError('fractions outside [0,1]')
    if not 0 < p['valid_T_min_K'] < p['valid_T_max_K']:
        raise ValueError('invalid temperature calibration interval')
    if p['molar_mass_kg_mol'] <= 0 or not np.isclose(p['delta_H_J_mol']/p['molar_mass_kg_mol'], p['latent_heat_J_kg'], rtol=1e-8, atol=0):
        raise ValueError('single-species constant-enthalpy model requires latent_heat=delta_H/molar_mass')
    if not p['valid_T_min_K'] <= p['initial_temperature_K'] <= p['valid_T_max_K']:
        raise ValueError('initial temperature outside declared interval')
    T = np.empty(len(power)+1); m = np.empty_like(T); q = np.empty(len(power)); energy_residual = np.empty_like(q)
    T[0],m[0]=p['initial_temperature_K'],p['initial_mass_kg']
    for k, P in enumerate(power):
        if not p['valid_T_min_K'] <= T[k] <= p['valid_T_max_K']:
            raise ValueError('temperature leaves declared thermodynamic interval')
        pv = vapor_pressure_pa(T[k],p['T_ref_K'],p['p_ref_Pa'],p['delta_H_J_mol'])
        unconstrained = p['evaporating_area_m2']*hertz_knudsen_kg_m2_s(T[k],pv,p['molar_mass_kg_mol'],p['alpha'])
        q[k] = min(unconstrained, m[k]/dt_s)
        m[k+1] = max(0, m[k]-q[k]*dt_s)
        loss = p['conductance_W_K']*(T[k]-p['bath_temperature_K']) + p['emissivity']*SIGMA*p['radiating_area_m2']*(T[k]**4-p['bath_temperature_K']**4)
        net = p['absorbed_fraction']*P-loss-p['latent_heat_J_kg']*q[k]
        T[k+1] = T[k]+dt_s*net/p['effective_heat_capacity_J_K']
        if not np.isfinite(T[k+1]) or not p['valid_T_min_K'] <= T[k+1] <= p['valid_T_max_K']:
            raise ValueError('Euler unstable or temperature outside declared interval')
        energy_residual[k] = p['effective_heat_capacity_J_K']*(T[k+1]-T[k])-dt_s*net
    return {'time_s':np.arange(len(T))*dt_s,'temperature_K':T,'mass_kg':m,'mass_rate_kg_s':q,'energy_residual_J':energy_residual}
