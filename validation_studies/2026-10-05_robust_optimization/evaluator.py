"""Read-only adapter to cub's unchanged planetary, finite-source, dual-mask CPU core.

Set PYTHONDONTWRITEBYTECODE=1 before importing this module. The public simulate
wrapper persists successful backend observations; this adapter deliberately calls
its unchanged integration kernel to avoid writes into the canonical project.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import hashlib
import json
import math
import sys
import time

import numpy as np

HERE = Path(__file__).resolve().parent
PRODUCT = HERE.parents[2] / "deposition_sim"
sys.dont_write_bytecode = True
sys.path.insert(0, str(PRODUCT))
from coat_sim.core.simulator import Settings, _simulate_on_backend
from coat_sim.core.source_profiles import source_samples, effective_source_exponent

BASE_SETTINGS = Settings(carrier_rpm=15., sun_teeth=120, planet_teeth=36,
    duration_s=12., time_steps=96, grid_size=21, substrate_radius_mm=100.,
    planet_offset_mm=250., substrate_z_mm=700., source_x_mm=100.,
    source_y_mm=0., source_z_mm=0., source_exponent=2.)
PARAMETERS = ("source_x", "source_y", "source_z", "mask1_x", "mask1_y",
    "mask1_z", "mask2_x", "mask2_y", "mask2_z", "source_A", "source_n",
    "carrier_rpm")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_hashes():
    """Freeze all importable product Python files, not only the two direct imports."""
    return {str(p.relative_to(PRODUCT)): sha256(p)
            for p in sorted((PRODUCT / "coat_sim").rglob("*.py"))}


def scenario_draws(seed, count, partition):
    if partition not in ("train", "holdout"):
        raise ValueError("Unknown scenario partition")
    offset = 10000 if partition == "train" else 90000
    return np.random.default_rng(offset + seed).normal(size=(count, len(PARAMETERS)))


def scenarios_hash(draws):
    return hashlib.sha256(np.asarray(draws, dtype="<f8").tobytes()).hexdigest()


def masks_for_design(design, perturbation):
    sx, w1, w2 = np.asarray(design, dtype=float)
    if not np.isfinite([sx, w1, w2]).all() or w1 <= 0 or w2 <= 0:
        raise ValueError("Nonfinite or degenerate design")
    masks = []
    for x0, width, half_y, z, shift in (
            (-70., w1, 100., 350., perturbation[3:6]),
            (160., w2, 80., 450., perturbation[6:9])):
        poly = np.array([[x0, -half_y], [x0 + width, -half_y],
                         [x0 + width, half_y], [x0, half_y]])
        masks.append({"z_mm": z + float(shift[2]),
                      "outer": poly + shift[:2], "holes": []})
    return masks


def geometric_screen(settings, masks):
    """Narrow synthetic screen, not a collision/manufacturing qualification."""
    settings.validate()
    for layer in masks:
        p = np.asarray(layer["outer"], dtype=float)
        if p.shape != (4, 2) or not np.isfinite(p).all():
            raise ValueError("Invalid rectangle")
        area2 = np.dot(p[:, 0], np.roll(p[:, 1], -1)) - np.dot(p[:, 1], np.roll(p[:, 0], -1))
        if abs(area2) <= 1e-9:
            raise ValueError("Zero-area mask")
        if not settings.source_z_mm < layer["z_mm"] < settings.substrate_z_mm:
            raise ValueError("Mask plane outside the source/substrate interval")
    if abs(masks[0]["z_mm"] - masks[1]["z_mm"]) < 10.:
        raise ValueError("Synthetic mask-plane separation less than 10 mm")


def clipped_cell_weights(axis, valid, radius):
    """Area of each disk-clipped Cartesian Voronoi cell, 64-node x quadrature.

    Only cells with a valid core sample are represented. Their union leaves small
    unsampled boundary slivers; the retained area fraction is explicitly returned.
    The remaining areas are normalized, with no invented outside-disk field.
    """
    a = np.asarray(axis)
    edges = np.r_[-radius, (a[:-1] + a[1:]) / 2, radius]
    nodes, wg = np.polynomial.legendre.leggauss(64)
    weights = np.zeros(valid.shape)
    for iy, ix in zip(*np.where(valid)):
        lo, hi = edges[ix:ix + 2]
        xx = (lo + hi) / 2 + (hi - lo) / 2 * nodes
        top = np.sqrt(np.maximum(0., radius ** 2 - xx ** 2))
        height = np.maximum(0., np.minimum(edges[iy + 1], top) - np.maximum(edges[iy], -top))
        weights[iy, ix] = (hi - lo) / 2 * np.dot(wg, height)
    area = float(weights.sum())
    if area <= 0:
        raise ValueError("No represented area")
    return weights / area, area / (math.pi * radius ** 2)


def weighted_metrics(result, weights, amplitude=1.):
    valid = np.isfinite(result["field"])
    h = result["field"][valid] * result["mean_raw"] * amplitude
    w = weights[valid]
    mu = float(np.dot(w, h))
    if not math.isfinite(mu) or mu <= 0 or not np.isfinite(h).all():
        raise ValueError("Zero or nonfinite deposition cannot have a CV")
    cv = math.sqrt(float(np.dot(w, (h - mu) ** 2))) / mu * 100.
    return {"cv_percent": cv, "area_mean_raw": mu,
            "pv_percent": float(np.ptp(h)) / mu * 100.}


@dataclass
class Counter:
    limit: int | None = None
    forward_calls: int = 0
    elapsed_s: float = 0.
    candidate_attempts: int = 0
    invalid_candidates: int = 0
    failed_forward_calls: int = 0

    def reserve(self, count):
        if self.limit is not None and self.forward_calls + count > self.limit:
            raise RuntimeError("Actual forward-call budget exhausted")


class Evaluator:
    def __init__(self, resolution=None, budget=None, forward=None):
        res = resolution or {"grid_size": 21, "time_steps": 96, "source_order": 3}
        self.settings = replace(BASE_SETTINGS, grid_size=int(res["grid_size"]),
                                time_steps=int(res["time_steps"]))
        self.source_order = int(res["source_order"])
        self.counter = Counter(limit=budget)
        self.forward = forward or _simulate_on_backend
        self.weights = None
        self.area_fraction = None
        self.failures = []

    def _call(self, settings, mask, source):
        self.counter.reserve(1)
        positions, weights = source_samples(settings, source)
        exponent = effective_source_exponent(settings, source)
        self.counter.forward_calls += 1  # Charge attempted calls, including errors.
        start = time.perf_counter()
        try:
            return self.forward(settings, mask, np, "CPU", None,
                                positions, weights, source_exponent=exponent)
        except Exception:
            self.counter.failed_forward_calls += 1
            raise
        finally:
            self.counter.elapsed_s += time.perf_counter() - start

    def evaluate(self, design, latent=None, level=0.):
        """Each valid scenario uses exactly two calls: masked and same-scenario bare.

        No caching, free throughput reference, early scenario exit, or hidden
        nominal evaluation. Invalid inputs are counted separately, without calls.
        """
        self.counter.candidate_attempts += 1
        try:
            d = np.asarray(design, dtype=float)
            z = np.zeros(len(PARAMETERS)) if latent is None else np.asarray(latent, dtype=float)
            if d.shape != (3,) or z.shape != (12,) or not np.isfinite(z).all() or not math.isfinite(level) or level < 0:
                raise ValueError("Invalid design/scenario shape or scale")
            shift = z.copy() * (level * 100.)
            amplitude = 1. + level * z[9]
            exponent = BASE_SETTINGS.source_exponent * (1. + level * z[10])
            rpm = BASE_SETTINGS.carrier_rpm * (1. + level * z[11])
            if amplitude <= 0:
                raise ValueError("Nonpositive source amplitude")
            settings = replace(self.settings, source_x_mm=d[0] + shift[0],
                source_y_mm=shift[1], source_z_mm=shift[2],
                source_exponent=exponent, carrier_rpm=rpm)
            masks = masks_for_design(d, shift)
            geometric_screen(settings, masks)
            source = {"kind": "rectangle", "device_type": "custom",
                "length_mm": 30., "width_mm": 10., "angle_deg": 0.,
                "source_exponent": exponent, "sampling_order": self.source_order}
        except (ValueError, TypeError, OverflowError) as exc:
            self.counter.invalid_candidates += 1
            self.failures.append({"stage": "input_geometry", "error": str(exc)})
            return {"valid": False, "error": str(exc)}
        self.counter.reserve(2)  # Atomic preflight: do not start half a scenario.
        try:
            masked = self._call(settings, masks, source)
            bare = self._call(settings, None, source)
            if self.weights is None:
                self.weights, self.area_fraction = clipped_cell_weights(masked["x"], np.isfinite(masked["field"]), settings.substrate_radius_mm)
            m = weighted_metrics(masked, self.weights, amplitude)
            u = weighted_metrics(bare, self.weights, amplitude)
            return {"valid": True, **m, "throughput": m["area_mean_raw"] / u["area_mean_raw"],
                    "unmasked_cv_percent": u["cv_percent"],
                    "source_samples": len(source_samples(settings, source)[1]),
                    "represented_area_fraction": self.area_fraction}
        except (ValueError, RuntimeError, FloatingPointError) as exc:
            self.failures.append({"stage": "forward_or_metric", "error": str(exc)})
            return {"valid": False, "error": str(exc)}


def objective(rows, mode, constraints, lambda_sd=1.):
    if mode not in ("nominal", "robust"):
        raise ValueError("Unknown objective mode")
    if not rows or any(not row["valid"] for row in rows):
        return (float("inf"), float("inf"))
    cv = np.array([r["cv_percent"] for r in rows])
    eta = np.array([r["throughput"] for r in rows])
    violation = float(np.max(np.maximum(0., cv / constraints["cv_max_percent"] - 1.) +
                                 np.maximum(0., 1. - eta / constraints["throughput_min"])))
    value = float(cv[0]) if mode == "nominal" else float(cv.mean() + lambda_sd * cv.std(ddof=0))
    return violation, value
