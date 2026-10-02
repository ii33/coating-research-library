"""T10 research-only normalization and diagnostics. No hardware control.
All inputs SI except explicit units. Synthetic calculations cannot qualify a process.
"""
from dataclasses import dataclass
from math import exp, expm1, isfinite, sqrt, cos, pi
from typing import Sequence
E_CHARGE = 1.602176634e-19
N_A = 6.02214076e23
K_B = 1.380649e-23


def nonnegative(x, name):
    if not isfinite(x) or x < 0:
        raise ValueError(f'{name} must be finite and nonnegative')
    return x


def positive(x, name):
    if not isfinite(x) or x <= 0:
        raise ValueError(f'{name} must be finite and positive')
    return x


@dataclass(frozen=True)
class Species:
    label: str
    particle_fraction: float
    charge_number: int
    mean_energy_eV: float
    nuclei_per_particle: int = 1


def beam_moments(current_density_A_m2: float, species: Sequence[Species]):
    """Corrected positive-ion current, species particle fractions at substrate plane.
    No electrons, secondary emission, slow charge-exchange ions or neutrals are inferred.
    Fractions must be number/particle fractions, NOT fractions of electric current.
    """
    nonnegative(current_density_A_m2, 'current density')
    if not species or abs(sum(s.particle_fraction for s in species)-1) > 1e-10:
        raise ValueError('particle fractions must sum to one')
    for s in species:
        nonnegative(s.particle_fraction, 'particle fraction')
        nonnegative(s.mean_energy_eV, 'energy')
        if type(s.charge_number) is not int or s.charge_number < 1:
            raise ValueError('positive integer charge number required')
        if type(s.nuclei_per_particle) is not int or s.nuclei_per_particle < 1:
            raise ValueError('positive integer nuclei count required')
    zbar=sum(s.particle_fraction*s.charge_number for s in species)
    ebar=sum(s.particle_fraction*s.mean_energy_eV for s in species)
    gamma=current_density_A_m2/(E_CHARGE*zbar)
    return {'mean_charge_number':zbar,'mean_energy_eV':ebar,
            'charged_particle_flux_m2_s':gamma,
            'charged_nuclei_flux_m2_s':gamma*sum(s.particle_fraction*s.nuclei_per_particle for s in species),
            'incident_kinetic_power_W_m2':gamma*ebar*E_CHARGE}


def impact_energy_eV(charge_number, creation_potential_V, surface_potential_V, initial_energy_eV=0):
    if type(charge_number) is not int or charge_number<1:
        raise ValueError('positive integer charge number required')
    for x in [creation_potential_V,surface_potential_V]:
        if not isfinite(x): raise ValueError('potential must be finite')
    nonnegative(initial_energy_eV,'initial energy')
    energy=initial_energy_eV+charge_number*(creation_potential_V-surface_potential_V)
    if energy<0: raise ValueError('ion cannot reach surface in this collisionless model')
    return energy


def atom_flux_from_net_growth(rate_nm_s, film_density_g_cm3, formula_mass_g_mol, atoms_per_formula):
    """Total atoms incorporated per area/time, not incident vapor arrival rate.
    Density is actual film density. Formula mass/composition must match that film.
    """
    nonnegative(rate_nm_s,'net growth rate');positive(film_density_g_cm3,'film density')
    positive(formula_mass_g_mol,'formula mass')
    if type(atoms_per_formula) is not int or atoms_per_formula<1: raise ValueError('integer atoms required')
    mass=rate_nm_s*1e-9*film_density_g_cm3*1000
    formula_flux=mass/(formula_mass_g_mol/1000)*N_A
    return {'net_mass_flux_kg_m2_s':mass,'net_formula_flux_m2_s':formula_flux,
            'net_atom_flux_m2_s':formula_flux*atoms_per_formula}


def normalize_assist(beam, net_atom_flux_m2_s, fast_neutral_flux_m2_s=0, fast_neutral_energy_eV=0):
    positive(net_atom_flux_m2_s,'net atom flux')
    nonnegative(fast_neutral_flux_m2_s,'neutral flux');nonnegative(fast_neutral_energy_eV,'neutral energy')
    energy_flux=beam['incident_kinetic_power_W_m2']+fast_neutral_flux_m2_s*fast_neutral_energy_eV*E_CHARGE
    return {'charged_ion_to_net_atom_ratio':beam['charged_particle_flux_m2_s']/net_atom_flux_m2_s,
            'energetic_particle_to_net_atom_ratio':(beam['charged_particle_flux_m2_s']+fast_neutral_flux_m2_s)/net_atom_flux_m2_s,
            'incident_eV_per_net_atom':energy_flux/(net_atom_flux_m2_s*E_CHARGE),
            'incident_kinetic_power_W_m2':energy_flux}


def simple_resputter_net_flux(arriving_atom_flux, energetic_particle_flux, effective_yield_atoms_per_particle):
    """Illustration only; full retention of incoming atoms; constant effective yield.
    Negative result denotes erosion. No chemistry or species-selective yield prediction.
    """
    for x,n in [(arriving_atom_flux,'arrival'),(energetic_particle_flux,'ion flux'),(effective_yield_atoms_per_particle,'yield')]:nonnegative(x,n)
    return arriving_atom_flux-energetic_particle_flux*effective_yield_atoms_per_particle


def charge_exchange_split(incident_particle_flux, pressure_Pa, temperature_K, path_m, cross_section_m2):
    """One-pass resonant charge-exchange demo; same forward energy per particle.
    Returns energetic components only. Does not model slow-ion collection or scattering.
    Cross section is a synthetic input, never inferred from ambient gas mean free path.
    """
    for x,n in [(incident_particle_flux,'flux'),(pressure_Pa,'pressure'),(path_m,'path'),(cross_section_m2,'cross section')]:nonnegative(x,n)
    positive(temperature_K,'gas temperature')
    tau=pressure_Pa/(K_B*temperature_K)*cross_section_m2*path_m
    s=exp(-tau)
    return {'optical_depth':tau,'energetic_ion_flux_m2_s':incident_particle_flux*s,
            'fast_neutral_flux_m2_s':incident_particle_flux*(-expm1(-tau))}


def integrate_samples(values, dt_s):
    """Piecewise constant bin averages, not endpoint samples."""
    if len(values)!=len(dt_s) or not values: raise ValueError('equal nonempty arrays required')
    for x in values: nonnegative(x,'value')
    for d in dt_s: positive(d,'duration')
    return sum(v*d for v,d in zip(values,dt_s))


def ratio_of_integrals(ion_flux, net_atom_flux, dt_s):
    denominator=integrate_samples(net_atom_flux,dt_s)
    positive(denominator,'integrated atom flux')
    return integrate_samples(ion_flux,dt_s)/denominator


def relative_ratio_uncertainty(u_j, u_rate, u_rho, u_zbar=0, corr_rate_rho=0):
    """First-order relative standard uncertainty, other covariance terms assumed zero.
    R is proportional to j/(rate*rho*zbar), so rate-density covariance enters PLUS.
    """
    for v in [u_j,u_rate,u_rho,u_zbar]:nonnegative(v,'relative standard uncertainty')
    if not isfinite(corr_rate_rho) or abs(corr_rate_rho)>1: raise ValueError('invalid correlation')
    return sqrt(max(0,u_j*u_j+u_rate*u_rate+u_rho*u_rho+u_zbar*u_zbar+2*corr_rate_rho*u_rate*u_rho))


def lumped_temperature_rise(absorbed_power_W, heat_capacity_J_K, conductance_W_K, duration_s):
    """Constant deposited heat, constant ambient, lumped body, no radiation.
    Input is absorbed total power, NOT automatically the incident ion kinetic power.
    """
    nonnegative(absorbed_power_W,'absorbed power');positive(heat_capacity_J_K,'capacity')
    nonnegative(conductance_W_K,'conductance');nonnegative(duration_s,'time')
    if conductance_W_K==0:return absorbed_power_W*duration_s/heat_capacity_J_K
    return absorbed_power_W/conductance_W_K*(-expm1(-conductance_W_K*duration_s/heat_capacity_J_K))


def projected_flux(beam_normal_flux, incidence_angle_deg):
    nonnegative(beam_normal_flux,'beam normal flux')
    if not isfinite(incidence_angle_deg) or not 0<=incidence_angle_deg<=180:raise ValueError('angle outside [0,180]')
    return beam_normal_flux*max(0.0,cos(incidence_angle_deg*pi/180)) if incidence_angle_deg<90 else 0.0
