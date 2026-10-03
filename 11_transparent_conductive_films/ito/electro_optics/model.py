"""Offline ITO reference model, not a process predictor or fitted material library.

Python >=3.10, standard library only. SI internally; exp(-i omega t), n+ik.
Optics: isotropic planar passive layers, normal incidence, real boundary indices.
The stable Fresnel recursion is algebraically equivalent to a 2x2 coherent TMM.
Empirical epsilon tables and measured layer conductivity are first-class inputs.
See report.md and evidence_ledger.json for provenance and limitations.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
import cmath
import math
from typing import Sequence

Q = 1.602176634e-19          # C, exact SI elementary charge
C = 299792458.0             # m/s, exact SI speed of light
EPS0 = 8.8541878128e-12      # F/m, sufficient precision for this reference
ME = 9.1093837015e-31        # kg
HBAR = 1.054571817e-34       # J s


def _number(x: float, name: str, zero: bool = False) -> float:
    x = float(x)
    if not math.isfinite(x) or x < 0 or (not zero and x == 0):
        raise ValueError(f"{name} must be finite and {'nonnegative' if zero else 'positive'}")
    return x


def cm3_to_m3(value: float) -> float:
    """Carrier concentration: cm^-3 -> m^-3 (not geometric cm^3)."""
    return _number(value, 'N_cm3', True) * 1e6


def cm2_vs_to_m2_vs(value: float) -> float:
    return _number(value, 'mu_cm2_Vs', True) * 1e-4


def nm_to_m(value: float) -> float:
    return _number(value, 'length_nm', True) * 1e-9


def ohm_cm_to_ohm_m(value: float) -> float:
    return _number(value, 'rho_ohm_cm', True) * 1e-2


def ev_to_rad_s(energy_ev: float) -> float:
    """hbar*omega in eV -> angular frequency in rad/s (not Hz)."""
    return _number(energy_ev, 'energy_ev') * Q / HBAR


def omega_from_wavelength(wavelength_m: float) -> float:
    return 2 * math.pi * C / _number(wavelength_m, 'vacuum wavelength')


@dataclass(frozen=True)
class Lorentz:
    strength: float          # dimensionless static contribution Delta epsilon
    omega0_rad_s: float
    damping_rad_s: float

    def __post_init__(self):
        _number(self.strength, 'oscillator strength', True)
        _number(self.omega0_rad_s, 'resonance frequency')
        _number(self.damping_rad_s, 'oscillator damping')


@dataclass(frozen=True)
class DrudeLorentz:
    carrier_density_m3: float
    mobility_opt_m2_vs: float
    effective_mass_me: float
    epsilon_inf: float
    oscillators: tuple[Lorentz, ...] = ()
    wavelength_domain_m: tuple[float, float] = (400e-9, 2500e-9)

    def __post_init__(self):
        _number(self.carrier_density_m3, 'carrier density', True)
        _number(self.mobility_opt_m2_vs, 'optical mobility')
        _number(self.effective_mass_me, 'relative effective mass')
        _number(self.epsilon_inf, 'epsilon_inf')
        lo, hi = self.wavelength_domain_m
        _number(lo, 'domain lower wavelength')
        _number(hi, 'domain upper wavelength')
        if hi <= lo:
            raise ValueError('wavelength domain must increase')

    @property
    def plasma_frequency_squared(self) -> float:
        return self.carrier_density_m3 * Q * Q / (EPS0 * self.effective_mass_me * ME)

    @property
    def damping_rad_s(self) -> float:
        return Q / (self.effective_mass_me * ME * self.mobility_opt_m2_vs)

    def drude_conductivity(self, omega_rad_s: float) -> complex:
        """Optical Drude extrapolation, not a replacement for measured DC/Hall."""
        omega = _number(omega_rad_s, 'omega', True)
        return EPS0 * self.plasma_frequency_squared / (self.damping_rad_s - 1j * omega)

    def epsilon(self, wavelength_m: float) -> complex:
        wavelength = _number(wavelength_m, 'vacuum wavelength')
        lo, hi = self.wavelength_domain_m
        if not lo <= wavelength <= hi:
            raise ValueError('outside declared optical domain; extrapolation disabled')
        omega = omega_from_wavelength(wavelength)
        eps = complex(self.epsilon_inf) - self.plasma_frequency_squared / (
            omega * (omega + 1j * self.damping_rad_s))
        for o in self.oscillators:
            eps += o.strength * o.omega0_rad_s**2 / (
                o.omega0_rad_s**2 - omega**2 - 1j * o.damping_rad_s * omega)
        return eps

    def nk(self, wavelength_m: float) -> complex:
        return passive_nk(self.epsilon(wavelength_m))


def passive_nk(epsilon: complex) -> complex:
    """Nonmagnetic passive branch. Gain is rejected, not sign-flipped silently."""
    eps = complex(epsilon)
    if not math.isfinite(eps.real) or not math.isfinite(eps.imag) or eps.imag < 0:
        raise ValueError('epsilon must be finite and passive (imaginary part >= 0)')
    return cmath.sqrt(eps)


@dataclass(frozen=True)
class EmpiricalEpsilon:
    """Piecewise-linear measured/fitted epsilon in its finite tabulated domain.

    It does not impose global Kramers-Kronig consistency or infer N/mu.
    Samples must be increasing wavelength, nonmagnetic passive epsilon.
    """
    samples: tuple[tuple[float, complex], ...]

    def __post_init__(self):
        if len(self.samples) < 2:
            raise ValueError('at least two empirical samples required')
        previous = 0.0
        for wl, eps in self.samples:
            _number(wl, 'wavelength')
            passive_nk(eps)
            if wl <= previous:
                raise ValueError('wavelengths must be strictly increasing')
            previous = wl

    def epsilon(self, wavelength_m: float) -> complex:
        wl = _number(wavelength_m, 'wavelength')
        grid = [point[0] for point in self.samples]
        if not grid[0] <= wl <= grid[-1]:
            raise ValueError('outside empirical domain; extrapolation disabled')
        if wl == grid[-1]:
            return complex(self.samples[-1][1])
        i = bisect_right(grid, wl) - 1
        x0, y0 = self.samples[i]
        x1, y1 = self.samples[i + 1]
        return y0 + (y1 - y0) * (wl - x0) / (x1 - x0)

    def nk(self, wavelength_m: float) -> complex:
        return passive_nk(self.epsilon(wavelength_m))


def dc_conductivity(carrier_density_m3: float, mobility_transport_m2_vs: float) -> float:
    """q*N*mu_transport; do not silently substitute mu_opt or assume Hall factor=1."""
    return Q * _number(carrier_density_m3, 'N', True) * _number(
        mobility_transport_m2_vs, 'mu_transport', True)


def sheet_resistance(layers_sigma_thickness: Sequence[tuple[float, float]]) -> float:
    """R_sheet = 1/sum(sigma_parallel,j*d_j), in ohm/square.

    Layer tuples are (sigma_S_per_m, thickness_m). Parallel common in-plane
    electric field and connected conducting paths are assumed. Zero conductance
    returns infinity. Not cross-plane resistivity or a contact-resistance model.
    """
    conductance = math.fsum(_number(sigma, 'sigma', True) * _number(d, 'd', True)
                            for sigma, d in layers_sigma_thickness)
    return 1.0 / conductance if conductance else math.inf


@dataclass(frozen=True)
class OpticalResult:
    R: float
    T: float
    A: float
    r: complex | None = None
    t: complex | None = None


def _index(n: complex, boundary: bool = False) -> complex:
    n = complex(n)
    if not math.isfinite(n.real) or not math.isfinite(n.imag):
        raise ValueError('index must be finite')
    if n.real < 0 or n.imag < 0 or n == 0:
        raise ValueError('passive nonnegative-real index required, excluding zero')
    if boundary and (n.imag != 0 or n.real <= 0):
        raise ValueError('incident and exit boundary media must have real positive index')
    return n


def coherent_rt(wavelength_m: float, layers_n_d: Sequence[tuple[complex, float]],
                n_in: float = 1.0, n_out: float = 1.5) -> OpticalResult:
    """Normal-incidence, stable coherent TMM-equivalent scattering recursion.

    Inputs ordered from illuminated surface toward exit. Finite substrate can be
    appended as a layer. If n_out is glass, T is into semi-infinite glass, NOT
    through a finite glass plate into air. No scattering/roughness/anisotropy.
    """
    wl = _number(wavelength_m, 'vacuum wavelength')
    n = [_index(n_in, True)]
    d = [0.0]
    for nj, dj in layers_n_d:
        n.append(_index(nj))
        d.append(_number(dj, 'layer thickness', True))
    n.append(_index(n_out, True))
    d.append(0.0)
    r_eff, t_eff = 0j, 1 + 0j
    for j in range(len(n) - 2, -1, -1):
        rij = (n[j] - n[j + 1]) / (n[j] + n[j + 1])
        tij = 2 * n[j] / (n[j] + n[j + 1])
        p = cmath.exp(2j * math.pi * n[j + 1] * d[j + 1] / wl)
        den = 1 + rij * r_eff * p * p
        t_eff = tij * t_eff * p / den
        r_eff = (rij + r_eff * p * p) / den
    R = abs(r_eff)**2
    T = n[-1].real / n[0].real * abs(t_eff)**2
    return OpticalResult(R, T, 1 - R - T, r_eff, t_eff)


def incoherent_substrate_rt(wavelength_m: float,
                            front_layers_n_d: Sequence[tuple[complex, float]],
                            n_substrate: float = 1.5,
                            n_in: float = 1.0, n_out: float = 1.0) -> OpticalResult:
    """Coherent front coating + LOSSLESS incoherent substrate + bare back face.

    Fully phase-averaged multiple returns are summed in intensity. Substrate
    must be real positive index; no thickness argument is needed in this lossless
    limit. Absorbing substrates, rear coatings and partial coherence are NOT
    implemented. No meaningful net field r,t exists for an incoherent result.
    """
    ns = _index(n_substrate, True).real
    front = coherent_rt(wavelength_m, front_layers_n_d, n_in, ns)
    reverse = coherent_rt(wavelength_m, list(reversed(front_layers_n_d)), ns, n_in)
    back = coherent_rt(wavelength_m, [], ns, n_out)
    den = 1 - reverse.R * back.R
    T = front.T * back.T / den
    R = front.R + front.T * back.R * reverse.T / den
    return OpticalResult(R, T, 1 - R - T)


def weighted_mean(wavelengths: Sequence[float], values: Sequence[float],
                  weights: Sequence[float]) -> float:
    """Trapezoidal integral(value*weight)/integral(weight), same wavelength grid.

    Supply and identify illuminant/response data yourself. Flat weights produce
    a wavelength-band average, not luminous transmittance or a standard metric.
    """
    if len(wavelengths) < 2 or not (len(wavelengths) == len(values) == len(weights)):
        raise ValueError('matching arrays of at least two points required')
    for x in wavelengths:
        _number(x, 'wavelength')
    if any(not math.isfinite(v) for v in values):
        raise ValueError('finite values required')
    for w in weights:
        _number(w, 'weight', True)
    numerator = denominator = 0.0
    for i in range(len(wavelengths) - 1):
        dx = wavelengths[i + 1] - wavelengths[i]
        if dx <= 0:
            raise ValueError('wavelength grid must increase')
        numerator += dx * (values[i] * weights[i] + values[i + 1] * weights[i + 1]) / 2
        denominator += dx * (weights[i] + weights[i + 1]) / 2
    if denominator == 0:
        raise ValueError('integrated weight must be positive')
    return numerator / denominator
