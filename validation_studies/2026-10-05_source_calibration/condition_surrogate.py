"""Minimal fixed-hyperparameter GP of three QCM rates over power/pressure.

Synthetic demonstration only. Uses installed NumPy/SciPy, no Botorch/GPU.
Do not confuse conditional latent GP standard deviation with total uncertainty.
"""
from __future__ import annotations
import numpy as np
from scipy.spatial import Delaunay


class QCMConditionGP:
    def __init__(self, conditions_W_mTorr, mass_flux, sd, *, configuration_id,
                 length_scale=0.65, noise_floor_fraction=1e-6):
        self.x = np.asarray(conditions_W_mTorr, float)
        y, sd = np.asarray(mass_flux, float), np.asarray(sd, float)
        if self.x.ndim != 2 or self.x.shape[1] != 2 or len(self.x) < 4:
            raise ValueError('at least four known 2D power/pressure conditions required')
        if y.ndim != 2 or y.shape[0] != len(self.x) or sd.shape != y.shape:
            raise ValueError('QCM observations and uncertainties must be Ncondition by Nsensor')
        if not all(np.all(np.isfinite(v)) for v in (self.x, y, sd)) or np.any(sd < 0):
            raise ValueError('finite GP conditions/data and nonnegative noise required')
        if len(np.unique(self.x, axis=0)) != len(self.x):
            raise ValueError('duplicate conditions require repeat/noise handling, not silent duplicate inputs')
        if not isinstance(configuration_id, str) or not configuration_id.strip():
            raise ValueError('configuration_id required')
        if not np.isfinite(length_scale) or length_scale <= 0 or not np.isfinite(noise_floor_fraction) or noise_floor_fraction <= 0:
            raise ValueError('positive fixed length scale and GP noise floor required')
        self.configuration_id = configuration_id
        self.origin = self.x.min(axis=0)
        self.span = self.x.max(axis=0) - self.origin
        if np.any(self.span == 0):
            raise ValueError('power and pressure must both vary')
        self.z = (self.x - self.origin) / self.span
        if np.linalg.matrix_rank(self.z - self.z.mean(axis=0)) < 2:
            raise ValueError('training conditions have degenerate 2D support')
        self.hull = Delaunay(self.z)
        self.length_scale = length_scale
        self.mean = y.mean(axis=0)
        self.scale = np.maximum(np.max(np.abs(y), axis=0), 1e-20)
        self.L, self.alpha = [], []
        covariance = self.kernel(self.z, self.z)
        for sensor in range(y.shape[1]):
            variance = np.maximum(sd[:, sensor] / self.scale[sensor], noise_floor_fraction)**2
            L = np.linalg.cholesky(covariance + np.diag(variance))
            standardized = (y[:, sensor] - self.mean[sensor]) / self.scale[sensor]
            self.L.append(L)
            self.alpha.append(np.linalg.solve(L.T, np.linalg.solve(L, standardized)))

    def kernel(self, x, y):
        distance2 = np.sum((x[:, None, :] - y[None, :, :])**2, axis=2)
        return np.exp(-0.5 * distance2 / self.length_scale**2)

    def predict(self, conditions_W_mTorr, *, configuration_id):
        if configuration_id != self.configuration_id:
            raise ValueError('GP source/material/geometry configuration changed')
        x = np.atleast_2d(np.asarray(conditions_W_mTorr, float))
        if x.shape[1] != 2 or not np.all(np.isfinite(x)):
            raise ValueError('prediction needs finite power/pressure pairs')
        z = (x - self.origin) / self.span
        if np.any(self.hull.find_simplex(z, tol=1e-10) < 0):
            raise ValueError('held-out condition outside training convex hull: extrapolation blocked')
        cross = self.kernel(z, self.z)
        mean, latent_sd = [], []
        for sensor, (L, alpha) in enumerate(zip(self.L, self.alpha)):
            mean.append(self.mean[sensor] + self.scale[sensor] * (cross @ alpha))
            projected = np.linalg.solve(L, cross.T)
            variance = np.maximum(0., 1 - np.sum(projected**2, axis=0))
            latent_sd.append(self.scale[sensor] * np.sqrt(variance))
        mean = np.column_stack(mean)
        if np.any(mean < 0):
            raise ValueError('negative GP rate prediction: do not silently clip before physical fit')
        return mean, np.column_stack(latent_sd)
