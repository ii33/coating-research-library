"""T10R2 offline reference kernels. No device commands or hardware/network I/O.

Cell flux is integrated over an energy-angle cell and per ACTUAL surface area.
Energy is kinetic eV per incident particle, never automatically eV/charge.
All calculations are conditional on supplied, independently justified inputs.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Sequence
import numpy as np
from scipy.optimize import lsq_linear

E_CHARGE = 1.602176634e-19  # exact C
AVOGADRO = 6.02214076e23  # exact mol^-1

class ContractError(ValueError):
    pass

def finite(value, name, lower=None, strict=False):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (float, int, np.number)) or not math.isfinite(float(value)):
        raise ContractError(f'{name}: finite real required')
    x = float(value)
    if lower is not None and (x <= lower if strict else x < lower):
        raise ContractError(f'{name}: outside permitted domain')
    return x

@dataclass(frozen=True)
class Cell:
    flux_m2_s: float
    energy_ev_particle: float
    charge_z: int
    theta_rad: float = 0.0
    phi_rad: float = 0.0
    mass_kg: float = 6.6335209e-26  # SYNTHETIC Ar-mass placeholder, explicit field in schema
    species: str = 'synthetic_Ar'
    nuclei_per_particle: int = 1

    def __post_init__(self):
        finite(self.flux_m2_s, 'flux', 0)
        finite(self.energy_ev_particle, 'energy', 0)
        finite(self.theta_rad, 'theta', 0)
        finite(self.phi_rad, 'phi')
        finite(self.mass_kg, 'mass', 0, True)
        if self.theta_rad > math.pi / 2:
            raise ContractError('theta must be incident hemisphere [0, pi/2]')
        if isinstance(self.charge_z, bool) or not isinstance(self.charge_z, int) or self.charge_z < 0:
            raise ContractError('charge_z must be nonnegative integer')
        if isinstance(self.nuclei_per_particle, bool) or not isinstance(self.nuclei_per_particle, int) or self.nuclei_per_particle < 1:
            raise ContractError('nuclei_per_particle must be positive integer')
        if not isinstance(self.species, str) or not self.species:
            raise ContractError('species identity required')


def impact_energy(initial_ev, charge_z, plasma_v, surface_v):
    """Collisionless fixed charge energy balance. Negative result means inaccessible.
    Requires conserved charge, no intervening potential barrier, negligible magnetic
    work, known potentials. Function does not certify trajectory accessibility.
    """
    finite(initial_ev, 'initial energy', 0)
    if isinstance(charge_z, bool) or not isinstance(charge_z, int) or charge_z < 1:
        raise ContractError('positive integer charge required')
    value = initial_ev + charge_z * (finite(plasma_v, 'plasma V') - finite(surface_v, 'surface V'))
    if value < 0:
        raise ContractError('energy balance cannot reach specified surface')
    return value


def flux_from_corrected_current(j_a_m2, fractions, charges, basis='particle'):
    """Only corrected positive-ion current. Returns species particle fluxes.
    fractions must be full charged population; unknown neutrals do not enter here.
    """
    j = finite(j_a_m2, 'corrected current', 0)
    f = np.asarray(fractions, dtype=float)
    if f.ndim != 1 or len(f) == 0 or len(f) != len(charges) or not np.all(np.isfinite(f)) or np.any(f < 0) or not math.isclose(float(f.sum()), 1, rel_tol=0, abs_tol=1e-12):
        raise ContractError('fractions must be finite nonnegative, normalized, matching charges')
    if any(isinstance(z, bool) or not isinstance(z, int) or z < 1 for z in charges):
        raise ContractError('positive integer charges required')
    z = np.asarray(charges, dtype=float)
    if basis == 'particle':
        return f * j / (E_CHARGE * float(f @ z))
    if basis == 'current':
        return f * j / (E_CHARGE * z)
    raise ContractError('fraction basis must be particle or current')


def correct_collector_current(raw_a_m2, offset_a_m2, electron_arrival_m2_s,
                              mean_charge, secondary_escape_per_ion):
    """Positive-ion electrical-current convention. Raw = e*(zbar+gamma)*G-e*Ge+b.
    gamma must be net escaping secondaries per ion (not total emitted yield).
    Requires a calibrated full-collection aperture; acceptance is NOT corrected here.
    """
    raw = finite(raw_a_m2, 'raw current')
    offset = finite(offset_a_m2, 'offset')
    ge = finite(electron_arrival_m2_s, 'electron arrival', 0)
    z = finite(mean_charge, 'mean charge', 1)
    gamma = finite(secondary_escape_per_ion, 'escaping secondaries', 0)
    gamma_i = (raw - offset + E_CHARGE * ge) / (E_CHARGE * (z + gamma))
    if gamma_i < 0:
        raise ContractError('negative corrected ion flux: baseline/model inconsistent')
    return {'charged_particle_flux_m2_s': gamma_i,
            'corrected_ion_current_a_m2': E_CHARGE * z * gamma_i}


def moments(cells: Sequence[Cell], neutral_coverage='unknown'):
    if neutral_coverage not in {'complete_conditional', 'unknown'}:
        raise ContractError('neutral_coverage must be explicit')
    j = sum(E_CHARGE * c.charge_z * c.flux_m2_s for c in cells)
    g = sum(c.flux_m2_s for c in cells if c.charge_z > 0)
    charged_q = sum(E_CHARGE*c.energy_ev_particle*c.flux_m2_s for c in cells if c.charge_z > 0)
    q = sum(E_CHARGE*c.energy_ev_particle*c.flux_m2_s for c in cells)
    p = sum(c.flux_m2_s*math.sqrt(2*c.mass_kg*E_CHARGE*c.energy_ev_particle)*math.cos(c.theta_rad) for c in cells)
    return {'ion_current_a_m2': j, 'charged_flux_m2_s': g,
            'charged_kinetic_flux_w_m2': charged_q,
            'observed_kinetic_flux_w_m2': q,
            'total_kinetic_flux_w_m2': q if neutral_coverage == 'complete_conditional' else None,
            'observed_normal_momentum_flux_pa': p,
            'nuclei_flux_m2_s': sum(c.nuclei_per_particle*c.flux_m2_s for c in cells),
            'thermal_power_w_m2': None}


def kinetic_flux_from_charge_spectrum(current_bins_a_m2, total_energy_per_charge_v):
    """q_ch = integral (E/(ze)) dj; bins are integrated corrected current.
    Total E/q is required. Planar RFEA E*cos(theta)^2/q cannot be substituted.
    Cell centers give a quadrature approximation unless bins contain exact means.
    """
    if len(current_bins_a_m2) != len(total_energy_per_charge_v) or not len(current_bins_a_m2):
        raise ContractError('matching nonempty charge spectrum required')
    return sum(finite(j,'current bin',0)*finite(u,'total energy/charge',0)
               for j,u in zip(current_bins_a_m2,total_energy_per_charge_v))


def rfea_matrix(cells: Sequence[Cell], barriers_v, transmission):
    """Ideal planar step-response forward matrix, NOT a universal analyzer model.
    A[i,c]*flux[c] -> current density referenced to declared aperture surface.
    energy/angle transmission matrix [barrier,cell] calibrated independently.
    At equality H=1/2 (declared quadrature convention).
    """
    v = np.asarray([finite(x,'barrier',0) for x in barriers_v])
    t = np.asarray(transmission, dtype=float)
    if v.size == 0 or t.shape != (v.size, len(cells)) or not np.all(np.isfinite(t)) or np.any(t < 0) or np.any(t > 1):
        raise ContractError('transmission matrix must be bounded [0,1] and match dimensions')
    a = np.zeros_like(t)
    for c, cell in enumerate(cells):
        if cell.charge_z == 0:
            continue
        u_n = cell.energy_ev_particle * math.cos(cell.theta_rad)**2 / cell.charge_z
        equal = np.isclose(v, u_n, rtol=0, atol=1e-12)
        h = np.where(equal, .5, np.where(v < u_n, 1., 0.))
        a[:,c] = E_CHARGE * cell.charge_z * t[:,c] * h
    return a


def response_rank(matrix):
    a = np.asarray(matrix, dtype=float)
    if a.ndim != 2 or not a.size or not np.all(np.isfinite(a)):
        raise ContractError('finite nonempty response matrix required')
    norms = np.linalg.norm(a, axis=0)
    scaled = a / np.where(norms > 0, norms, 1)
    s = np.linalg.svd(scaled, compute_uv=False)
    rank = int(np.linalg.matrix_rank(scaled))
    return {'rows': a.shape[0], 'columns': a.shape[1], 'rank': rank,
            'full_column_rank': rank == a.shape[1],
            'scaled_singular_values': s.tolist(),
            'scaled_condition_number': float(s[0]/s[-1]) if rank == a.shape[1] else None}


def whiten(matrix, data, covariance):
    a = np.asarray(matrix, dtype=float); y = np.asarray(data, dtype=float); cov = np.asarray(covariance,dtype=float)
    if a.ndim != 2 or y.shape != (a.shape[0],) or cov.shape != (len(y),len(y)) or not all(np.all(np.isfinite(x)) for x in [a,y,cov]):
        raise ContractError('data/covariance shape or finite check failed')
    if not np.allclose(cov,cov.T,rtol=1e-12,atol=0):
        raise ContractError('covariance not symmetric')
    try:
        l = np.linalg.cholesky(cov)
    except np.linalg.LinAlgError as e:
        raise ContractError('strictly positive definite covariance required') from e
    return np.linalg.solve(l,a), np.linalg.solve(l,y)


def invert_nonnegative(matrix, current, covariance, max_iter=100, flux_scale=1e18):
    """Bounded reference linear inverse; rank deficiency blocks spectral inference.
    Known covariance only. No silent regularization, pseudo-inverse uniqueness,
    negative-current clipping or failure-to-success conversion.
    """
    finite(flux_scale,'flux scale',0,True)
    if isinstance(max_iter,bool) or not isinstance(max_iter,int) or max_iter < 1:
        raise ContractError('positive integer max_iter required')
    a,y = whiten(matrix,current,covariance)
    report=response_rank(a)
    if not report['full_column_rank']:
        return {'status':'unidentifiable','flux_m2_s':None,'covariance':None,'rank':report,'iterations':0}
    a_scaled=a*flux_scale
    solution=lsq_linear(a_scaled,y,bounds=(0,np.inf),tol=1e-12,max_iter=max_iter,method='trf')
    if not solution.success:
        return {'status':'budget_exhausted' if solution.status==0 else 'solver_failure', 'flux_m2_s':None,'covariance':None,'rank':report,'iterations':solution.nit}
    x=solution.x*flux_scale
    interior=bool(np.all(solution.active_mask==0) and np.all(solution.x>1e-10))
    cov=np.linalg.inv(a_scaled.T@a_scaled)*flux_scale**2 if interior else None
    return {'status':'converged_conditional','flux_m2_s':x.tolist(),
            'covariance':cov.tolist() if cov is not None else None,'rank':report,
            'iterations':solution.nit,'weighted_residual_norm':float(np.linalg.norm(a@x-y)),
            'covariance_scope':'known observational covariance only, fixed response matrix; no model/calibration errors' if interior else 'boundary solution: linear covariance withheld'}


def aperture_average(local_values, weights, complete_support):
    """Known finite-aperture convolution. No inference outside measured support."""
    x=np.asarray(local_values,float); w=np.asarray(weights,float)
    if x.ndim!=1 or x.shape!=w.shape or not x.size or not np.all(np.isfinite(x)) or not np.all(np.isfinite(w)) or np.any(w<0):
        raise ContractError('invalid aperture input')
    if not complete_support or not math.isclose(float(w.sum()),1,rel_tol=0,abs_tol=1e-12):
        raise ContractError('incomplete spatial support; renormalization forbidden')
    return float(x@w)


def time_integrate(bins, field, start_s, end_s):
    """Piecewise-constant bin means; requires ordered contiguous exact coverage.
    No sorting over duplicated timestamps, interpolation across gaps or extrapolation.
    """
    finite(start_s,'start');finite(end_s,'end')
    if end_s <= start_s or not bins:
        raise ContractError('nonempty positive integration interval required')
    total=0.; cursor=float(start_s)
    for b in bins:
        a=finite(b['t0_s'],'bin start'); z=finite(b['t1_s'],'bin end')
        if z<=a or not math.isclose(a,cursor,abs_tol=1e-10,rel_tol=0):
            raise ContractError('time gap/overlap/unordered bin')
        if z>end_s+1e-10:
            raise ContractError('bin exceeds requested interval')
        total+=(z-a)*finite(b[field],field)
        cursor=z
    if not math.isclose(cursor,end_s,abs_tol=1e-10,rel_tol=0):
        raise ContractError('missing terminal coverage')
    return total


def net_normalization(charged_dose_m2, observed_energy_j_m2, total_energy_j_m2,
                      net_atoms_bounds, initial_inventory_bounds=None,
                      cumulative_element_bounds=None):
    """Interval denominator semantics; ratio bounds only account for denominator.
    Exposed charged dose and observed energy are not erased by missing net inventory.
    """
    d=finite(charged_dose_m2,'charged dose',0);uo=finite(observed_energy_j_m2,'observed U',0)
    u=None if total_energy_j_m2 is None else finite(total_energy_j_m2,'total U',0)
    if u is not None and u+abs(u)*1e-12 < uo:
        raise ContractError('total energy smaller than observed component energy')
    lo,hi=map(float,net_atoms_bounds)
    finite(lo,'N lower');finite(hi,'N upper')
    if lo>hi:
        raise ContractError('reversed net interval')
    base={'charged_dose_m2':d,'observed_energy_j_m2':uo,'total_energy_j_m2':u,'R':None,'epsilon_ev_net_atom':None,'denominator_only_bounds':None}
    if cumulative_element_bounds is not None:
        if initial_inventory_bounds is None or set(initial_inventory_bounds)!=set(cumulative_element_bounds):
            raise ContractError('complete matched element initial inventory required')
        for element, trajectory in cumulative_element_bounds.items():
            b=initial_inventory_bounds[element]
            if len(b)!=2 or finite(b[0],'inventory lower',0)>finite(b[1],'inventory upper',0):
                raise ContractError('invalid initial inventory')
            for step in trajectory:
                if len(step)!=2 or finite(step[0],'cumulative lower')>finite(step[1],'cumulative upper'):
                    raise ContractError('invalid cumulative interval')
                if b[0]+step[0] <= 0:
                    return dict(base,status='inventory_depletion_possible')
    if hi<0: return dict(base,status='net_erosion')
    if lo<=0: return dict(base,status='zero_or_crossing')
    bounds={'R':[d/hi,d/lo], 'epsilon_ev_net_atom':None if u is None else [u/E_CHARGE/hi,u/E_CHARGE/lo]}
    if hi-lo>=lo: return dict(base,status='ill_conditioned',denominator_only_bounds=bounds)
    mid=(lo+hi)/2
    return dict(base,status='positive_conditional',R=d/mid,
                epsilon_ev_net_atom=None if u is None else u/E_CHARGE/mid,denominator_only_bounds=bounds)


def inventory_thickness(net_atoms, nuclei_per_formula, molar_mass_kg_mol, film_density_kg_m3,
                        constant_state, composition_compatible, evidence_kind):
    if not constant_state or not composition_compatible or evidence_kind not in {'measured_film','synthetic_declared'}:
        return {'thickness_increment_m':None,'status':'blocked_film_state'}
    n=finite(net_atoms,'net atoms');nu=finite(nuclei_per_formula,'nu',0,True)
    m=finite(molar_mass_kg_mol,'molar mass',0,True);rho=finite(film_density_kg_m3,'film density',0,True)
    return {'thickness_increment_m':n*m/(nu*rho*AVOGADRO),'status':'signed_constant_state_conditional'}


def propagate_linear(jacobian, covariance):
    j=np.asarray(jacobian,float);c=np.asarray(covariance,float)
    if j.ndim!=2 or c.shape!=(j.shape[1],j.shape[1]) or not np.all(np.isfinite(j)) or not np.all(np.isfinite(c)) or not np.allclose(c,c.T,rtol=1e-12,atol=0):
        raise ContractError('invalid covariance propagation shapes/symmetry')
    if np.min(np.linalg.eigvalsh(c)) < -1e-12*max(float(np.linalg.norm(c,2)),np.finfo(float).tiny):
        raise ContractError('covariance not PSD')
    return j@c@j.T


def grouped_response_fit(rows, operator_id, material_state_id):
    """Fixed linear response basis, disjoint run groups. No candidate/model selection.
    rows: [1, epsilon, T, history] may be any externally frozen finite basis.
    Fit/selection/final groups cannot share a deposition run. Selection rows are
    reported but unused. Final is scored only after metadata declares frozen basis.
    This is NOT an optical forward model or causality estimator.
    """
    if not rows: raise ContractError('response rows required')
    groups={}; seen=set();p=None
    for r in rows:
        if r['sample_id'] in seen: raise ContractError('duplicate sample ID')
        seen.add(r['sample_id'])
        role=r['split']
        if role not in {'fit','selection','final'}: raise ContractError('invalid split')
        group=r['run_id']
        if group in groups and groups[group]!=role: raise ContractError('same deposition run crosses splits')
        groups[group]=role
        if r['operator_id']!=operator_id or r['material_state_id']!=material_state_id:
            raise ContractError('incompatible material state or optical measurement operator')
        x=r['features'];p=len(x) if p is None else p
        if len(x)!=p or p==0: raise ContractError('inconsistent fixed response basis')
        for v in x: finite(v,'feature')
        finite(r['value'],'response');finite(r['standard_uncertainty'],'response uncertainty',0,True)
    train=[r for r in rows if r['split']=='fit'];final=[r for r in rows if r['split']=='final']
    if not train or not final: raise ContractError('fit and final heldout groups required')
    x=np.array([r['features'] for r in train]);y=np.array([r['value'] for r in train]);s=np.array([r['standard_uncertainty'] for r in train]);a=x/s[:,None];b=y/s
    rank=response_rank(a)
    if not rank['full_column_rank']: return {'status':'unidentifiable_response','rank':rank,'coefficients':None}
    beta=np.linalg.lstsq(a,b,rcond=None)[0];cov=np.linalg.inv(a.T@a)
    pred=[]
    for r in final:
        xx=np.array(r['features']);v=float(xx@beta)
        pred.append({'sample_id':r['sample_id'],'run_id':r['run_id'],'prediction':v,'measured':r['value'],'residual':r['value']-v,'u_prediction_conditional':math.sqrt(float(xx@cov@xx)), 'u_comparison_independent_conditional':math.sqrt(float(xx@cov@xx)+r['standard_uncertainty']**2)})
    return {'status':'conditional_linear_fit','coefficients':beta.tolist(),'covariance':cov.tolist(),'rank':rank,'final_scores':pred,'qualification':'not_evaluated','scope':'known independent response noise, fixed features; no errors-in-variables or shared calibration uncertainty'}
