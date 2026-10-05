"""Fixed-known-geometry source calibration; research only, SI throughout.

Fits emitted hemispherical mass rate A >= 0 and angular exponent n >= 0.
Forward evaluations reuse the existing T05 research Source/flux interface.
There is no production kernel modification, experiment, or hardware control.
"""
from __future__ import annotations
from dataclasses import dataclass
import importlib.util
from pathlib import Path
import sys
import numpy as np
from scipy.optimize import least_squares

sys.dont_write_bytecode = True
STUDY = Path(__file__).resolve().parent
LIBRARY = STUDY.parents[1]
PROJECTS = LIBRARY.parent
REFERENCE_PATH = LIBRARY / '05_evaporation_sources/models/source_reference.py'
_spec = importlib.util.spec_from_file_location('_source_calibration_t05', REFERENCE_PATH)
_ref = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _ref
_spec.loader.exec_module(_ref)


def _finite(value, name):
    result = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(result)):
        raise ValueError(name + ' must contain finite values; unknowns are not zero')
    return result


@dataclass
class FixedGeometry:
    source_nodes_m: np.ndarray
    source_normals: np.ndarray
    source_fractions: np.ndarray
    qcm_coords_m: np.ndarray
    qcm_normals: np.ndarray
    qcm_area_m2: np.ndarray
    configuration_id: str
    capture_fraction: np.ndarray | None = None

    def __post_init__(self):
        self.source_nodes_m, self.source_normals, self.source_fractions = _ref.Source(
            self.source_nodes_m, self.source_normals, self.source_fractions, 0).validate()
        self.qcm_coords_m = _finite(self.qcm_coords_m, 'QCM coordinates')
        self.qcm_normals = _ref.unit_rows(self.qcm_normals, 'QCM normals')
        self.qcm_area_m2 = _finite(self.qcm_area_m2, 'QCM areas')
        if self.qcm_coords_m.ndim != 2 or self.qcm_coords_m.shape[1] != 3:
            raise ValueError('QCM coordinates must be N by 3')
        count = len(self.qcm_coords_m)
        if count < 1 or self.qcm_normals.shape != self.qcm_coords_m.shape:
            raise ValueError('QCM coordinates/normals disagree')
        if self.qcm_area_m2.shape != (count,) or np.any(self.qcm_area_m2 <= 0):
            raise ValueError('QCM effective areas must be explicit and positive')
        if not isinstance(self.configuration_id, str) or not self.configuration_id.strip():
            raise ValueError('configuration_id is required')
        self.capture_fraction = (np.ones(count) if self.capture_fraction is None
                                 else _finite(self.capture_fraction, 'capture fractions'))
        if self.capture_fraction.shape != (count,) or np.any(self.capture_fraction <= 0) or np.any(self.capture_fraction > 1):
            raise ValueError('known capture fractions must be in (0,1]')
        d = self.qcm_coords_m[:, None, :] - self.source_nodes_m[None, :, :]
        distance = np.linalg.norm(d, axis=2)
        if np.any(distance <= 0):
            raise ValueError('QCM cannot coincide with a source node')
        direction = d / distance[:, :, None]
        self._mu_s = np.einsum('ijk,jk->ij', direction, self.source_normals)
        self._mu_i = np.maximum(0, -np.einsum('ijk,ik->ij', direction, self.qcm_normals))
        self._distance2 = distance**2
        front = self._mu_s > 0
        self._logmu = np.zeros_like(self._mu_s)
        self._logmu[front] = np.log(np.minimum(1, self._mu_s[front]))
        self._front = front
        # Calibration needs positive response, not backface/fully blocked sensors.
        if np.any(self.kernel(0) <= 0):
            raise ValueError('every fitted QCM must have positive front-side response')

    def kernel(self, n):
        n = float(n)
        if not np.isfinite(n) or n < 0:
            raise ValueError('n must be finite and >= 0')
        source = _ref.Source(self.source_nodes_m, self.source_normals,
                             self.source_fractions, n)
        return self.capture_fraction * _ref.flux_kg_m2_s(
            source, self.qcm_coords_m, self.qcm_normals, 1.0)

    def kernel_derivative(self, n):
        if not np.isfinite(n) or n < 0:
            raise ValueError('n must be finite and >= 0')
        pdf = _ref.cosine_pdf(self._mu_s, n)
        term = pdf * self._mu_i / self._distance2 * self.source_fractions
        return self.capture_fraction * np.sum(
            term * (1 / (n + 1) + self._logmu), axis=1)

    def predict(self, A_kg_s, n):
        if not np.isfinite(A_kg_s) or A_kg_s < 0:
            raise ValueError('A must be finite and >= 0')
        return A_kg_s * self.kernel(n)

    def contract(self):
        return {'configuration_id': self.configuration_id,
                'source_nodes_m': self.source_nodes_m.tolist(),
                'source_normals': self.source_normals.tolist(),
                'source_fractions': self.source_fractions.tolist(),
                'qcm_coords_m': self.qcm_coords_m.tolist(),
                'qcm_normals': self.qcm_normals.tolist(),
                'qcm_area_m2': self.qcm_area_m2.tolist(),
                'capture_fraction': self.capture_fraction.tolist(),
                'receiver_model': 'point at QCM centre, not finite-area integration'}


def geometry_from_production_source(settings, source_profile, qcm_coords_m,
                                    qcm_normals, qcm_area_m2, configuration_id):
    """Read actual installed source_samples; convert its mm nodes to SI.

    Does not reuse the production relative thickness normalization or material
    rate_nm_s as absolute A. Current production source normals are fixed +z.
    No production simulation, source files, settings or masks are changed.
    """
    production = PROJECTS / 'deposition_sim'
    if str(production) not in sys.path:
        sys.path.insert(0, str(production))
    from coat_sim.core.source_profiles import source_samples
    nodes_mm, fractions = source_samples(settings, source_profile)
    return FixedGeometry(nodes_mm / 1000, np.tile([0., 0., 1.], (len(nodes_mm), 1)),
                         fractions, qcm_coords_m, qcm_normals, qcm_area_m2,
                         configuration_id)


def mass_rate_to_mass_flux(rate_kg_s, sd_kg_s, qcm_area_m2):
    """Only for TOTAL retained mass rate on explicitly known effective area.

    Sauerbrey/controller areal mass-rate exports must NOT be divided by area
    again. This prototype does not infer frequency-to-mass conversion constants.
    """
    rate, sd, area = [_finite(x, name) for x, name in
                      [(rate_kg_s, 'mass rates'), (sd_kg_s, 'mass rate sd'),
                       (qcm_area_m2, 'effective area')]]
    if rate.shape != sd.shape or area.shape != rate.shape or np.any(area <= 0) or np.any(sd < 0):
        raise ValueError('rates, uncertainties, areas must have matching shape')
    return rate / area, sd / area


def _best_amplitude(geometry, flux, sigma, n):
    kernel = geometry.kernel(n)
    weighted_kernel = kernel / sigma
    A = max(0., float(np.dot(weighted_kernel, flux / sigma) /
                      np.dot(weighted_kernel, weighted_kernel)))
    residual = (A * kernel - flux) / sigma
    return A, float(residual @ residual)


def fit_source(geometry, mass_flux_kg_m2_s, sd_kg_m2_s, *,
               noise_floor_kg_m2_s=1e-12, n_max=20., profile_points=401):
    """Bounded weighted nonlinear fit with analytic Jacobian and n profile.

    Independent Gaussian AREAL mass-flux errors are an explicit assumption.
    Absolute noise floor is required even for deterministic synthetic data.
    n_max is a declared search cap, never a measured physical upper bound.
    """
    y = _finite(mass_flux_kg_m2_s, 'mass flux')
    sd = _finite(sd_kg_m2_s, 'mass-flux uncertainties')
    if y.shape != (len(geometry.qcm_coords_m),) or sd.shape != y.shape or np.any(sd < 0):
        raise ValueError('observations and nonnegative sd must match QCM count')
    if len(y) < 2:
        raise ValueError('at least two positive-response QCM positions needed')
    if not np.isfinite(noise_floor_kg_m2_s) or noise_floor_kg_m2_s <= 0:
        raise ValueError('strictly positive finite absolute noise floor required')
    if not np.isfinite(n_max) or n_max <= 0 or type(profile_points) is not int or profile_points < 3:
        raise ValueError('positive finite n cap and profile_points >=3 required')
    sigma = np.maximum(sd, noise_floor_kg_m2_s)
    amplitude_scale = max(float(np.max(np.abs(y))), noise_floor_kg_m2_s) / max(geometry.kernel(1))
    def residual(params):
        return (geometry.predict(params[0] * amplitude_scale, params[1]) - y) / sigma
    def jacobian(params):
        return np.column_stack((amplitude_scale * geometry.kernel(params[1]),
                                params[0] * amplitude_scale * geometry.kernel_derivative(params[1]))) / sigma[:, None]
    solutions = []
    for initial_n in sorted(set([0., min(1., n_max), min(4., n_max), n_max / 2, n_max])):
        initial_A, _ = _best_amplitude(geometry, y, sigma, initial_n)
        solution = least_squares(residual, [max(initial_A / amplitude_scale, 1e-10), initial_n],
                                 jac=jacobian, bounds=([0., 0.], [np.inf, n_max]),
                                 method='trf', ftol=1e-12, xtol=1e-12, gtol=1e-12,
                                 max_nfev=500)
        exact_A, exact_chi2 = _best_amplitude(geometry, y, sigma, solution.x[1])
        solutions.append((exact_chi2, exact_A, float(solution.x[1]), bool(solution.success)))
    # Exact constrained endpoints prevent tiny numerical pseudo-interior n=0.
    for endpoint in (0., n_max):
        exact_A, exact_chi2 = _best_amplitude(geometry, y, sigma, endpoint)
        solutions.append((exact_chi2, exact_A, endpoint, True))
    chi2, A, n, success = min(solutions, key=lambda item: item[0])
    if n < 1e-7 or n > n_max - 1e-7:
        n = 0. if n < 1e-7 else n_max
        A, chi2 = _best_amplitude(geometry, y, sigma, n)
    pred = geometry.predict(A, n)
    J = np.column_stack((pred, A * geometry.kernel_derivative(n))) / sigma[:, None]
    singular = np.linalg.svd(J, compute_uv=False)
    rank = 0 if singular[0] == 0 else int(np.sum(singular > singular[0] * 1e-8))
    condition = None if rank < 2 else float(singular[0] / singular[-1])
    boundary = A == 0 or n <= 1e-7 or n >= n_max - 1e-7
    covariance = None
    correlation = None
    if rank == 2 and not boundary:
        # Conditional known absolute noise: DO NOT multiply by reduced chi2.
        inverse_s = 1 / singular
        _, _, Vt = np.linalg.svd(J, full_matrices=False)
        covariance = (Vt.T * inverse_s**2) @ Vt
        correlation = float(covariance[0, 1] / np.sqrt(covariance[0, 0] * covariance[1, 1]))
    grid = np.unique(np.r_[np.linspace(0., n_max, profile_points), n])
    profiles = [_best_amplitude(geometry, y, sigma, float(value)) for value in grid]
    profile_chi2 = np.array([pair[1] for pair in profiles])
    delta = np.maximum(0., profile_chi2 - chi2)
    accepted = delta <= 3.841458820694124
    informative = bool(np.max(pred / sigma) >= 3)
    warnings = []
    if rank < 2:
        warnings.append('A and n are not separately identifiable; no usable fitted source map')
    if not informative:
        warnings.append('signal below project 3-sigma diagnostic; source shape unsupported')
    if boundary:
        warnings.append('boundary solution: ordinary unconstrained Gaussian covariance withheld')
    if condition is not None and condition > 100:
        warnings.append('ill-conditioned local Jacobian (project diagnostic threshold 100)')
    if accepted[-1]:
        warnings.append('profile reaches declared n search cap; upper uncertainty is unresolved')
    return {
        'configuration_id': geometry.configuration_id,
        'A_kg_s': A, 'n': n, 'n_search_cap': n_max,
        'optimizer_success': success, 'chi2': chi2,
        'dof': None if boundary else len(y) - 2,
        'effective_sigma_kg_m2_s': sigma.tolist(),
        'predicted_qcm_mass_flux_kg_m2_s': pred.tolist(),
        'jacobian_parameterization': '[ln A, n], whitened by independent absolute sigma',
        'jacobian_rank': rank, 'jacobian_singular_values': singular.tolist(),
        'jacobian_condition': condition, 'correlation_lnA_n': correlation,
        'covariance_lnA_n': None if covariance is None else covariance.tolist(),
        'boundary_solution': bool(boundary), 'signal_informative': informative,
        'identifiable': bool(rank == 2 and informative),
        'profile_n': grid.tolist(), 'profile_A_kg_s': [pair[0] for pair in profiles],
        'profile_delta_chi2': delta.tolist(),
        'profile_reference_region': [float(grid[accepted][0]), float(grid[accepted][-1])],
        'profile_open_at_n0': bool(accepted[0]), 'profile_open_at_cap': bool(accepted[-1]),
        'profile_note': 'grid diagnostic using asymptotic interior chi2(1) 95% reference cutoff; not exact coverage, especially at boundary',
        'warnings': warnings,
        'physical_validation': 'not performed; all reported studies are synthetic'
    }


def predict_fitted(fit, geometry, *, configuration_id):
    if geometry.configuration_id != configuration_id or fit['configuration_id'] != configuration_id:
        raise ValueError('configuration mismatch: geometry/source state cannot be silently transferred')
    if not fit['identifiable']:
        raise ValueError('source parameters not identifiable; spatial source map is blocked')
    return geometry.predict(fit['A_kg_s'], fit['n'])


def validate_actual_input(contract):
    """Unknown geometry and historical unnamed rings are intentionally rejected."""
    required = ['configuration_id', 'source_nodes_m', 'source_normals', 'source_fractions',
                'qcm_coords_m', 'qcm_normals', 'qcm_area_m2',
                'mass_flux_kg_m2_s', 'sd_kg_m2_s', 'noise_floor_kg_m2_s',
                'capture_fraction']
    missing = [key for key in required if key not in contract or contract[key] is None]
    if missing:
        raise ValueError('actual calibration blocked: explicit measurements required for ' + ', '.join(missing))
    if contract.get('reading_type') != 'areal_mass_flux':
        raise ValueError('reading_type must explicitly be areal_mass_flux; thickness requires separately approved conversion')
    geometry = FixedGeometry(**{key: contract[key] for key in required[:7]},
                             capture_fraction=contract['capture_fraction'])
    flux = _finite(contract['mass_flux_kg_m2_s'], 'mass flux')
    sd = _finite(contract['sd_kg_m2_s'], 'mass flux sd')
    floor = contract['noise_floor_kg_m2_s']
    if flux.shape != (len(geometry.qcm_coords_m),) or sd.shape != flux.shape or np.any(sd < 0):
        raise ValueError('explicit areal mass flux and sd must match QCM count')
    if not np.isfinite(floor) or floor <= 0:
        raise ValueError('absolute noise floor must be finite and strictly positive')
    return geometry
