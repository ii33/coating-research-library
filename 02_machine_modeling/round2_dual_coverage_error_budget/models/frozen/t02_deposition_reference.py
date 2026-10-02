#!/usr/bin/env python3
"""T02 v0.1 educational ballistic deposition reference. SI throughout.
Not a calibrated machine model; NumPy only. See chapters for scope/derivation.
"""
from dataclasses import dataclass
from math import pi
from typing import Callable, Sequence
import numpy as np

VERSION = 'T02-reference-0.1'


def rotation_z(a):
    a = np.asarray(a, dtype=float)
    out = np.zeros(a.shape + (3, 3))
    c, s = np.cos(a), np.sin(a)
    out[..., 0, 0] = out[..., 1, 1] = c
    out[..., 0, 1], out[..., 1, 0] = -s, s
    out[..., 2, 2] = 1.
    return out


def rotation_y(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0., s], [0., 1., 0.], [-s, 0., c]])


def unit_vectors(a, name='normals'):
    a = np.asarray(a, dtype=float)
    norm = np.linalg.norm(a, axis=-1)
    if not np.all(np.isfinite(a)) or np.any(norm <= 0):
        raise ValueError(f'{name}: finite nonzero vectors required')
    return a / norm[..., None]


@dataclass
class Source:
    positions_m: np.ndarray
    normals: np.ndarray
    fractions: np.ndarray
    exponent: float = 1.

    def __post_init__(self):
        self.positions_m = np.atleast_2d(np.asarray(self.positions_m, dtype=float))
        self.normals = unit_vectors(np.atleast_2d(self.normals), 'source normals')
        self.fractions = np.asarray(self.fractions, dtype=float)
        n = len(self.positions_m)
        if self.positions_m.shape != (n, 3) or self.normals.shape != (n, 3):
            raise ValueError('Source positions/normals must have shape (S,3)')
        if not np.all(np.isfinite(self.positions_m)) or self.fractions.shape != (n,):
            raise ValueError('Invalid source nodes')
        if not np.isfinite(self.exponent) or self.exponent < 0:
            raise ValueError('Emission exponent must be finite and nonnegative')
        if np.any(self.fractions < 0) or not np.isclose(self.fractions.sum(), 1., rtol=0, atol=1e-12):
            raise ValueError('Nonnegative source mass-rate fractions must sum to one')
        # Zero-mass quadrature nodes contribute nothing and must not create a
        # false singularity if a target coincides with such an inactive node.
        active = self.fractions > 0
        self.positions_m = self.positions_m[active]
        self.normals = self.normals[active]
        self.fractions = self.fractions[active]


def point_source(position=(0., 0., 0.), normal=(0., 0., 1.), exponent=1.):
    return Source(np.array([position]), np.array([normal]), np.ones(1), exponent)


def disk_source(radius_m, radial_order=8, azimuth_nodes=32,
                center=(0., 0., 0.), orientation=np.eye(3), exponent=1.):
    """Uniform mass rate over disk, Gauss in u=(r/a)^2, uniform azimuth.
    Weights are fractions of total emitted kg/s, NOT areas or radiance.
    """
    if radius_m <= 0 or radial_order < 1 or azimuth_nodes < 1:
        raise ValueError('Positive disk radius and quadrature orders required')
    Q = np.asarray(orientation, dtype=float)
    if Q.shape != (3, 3) or not np.allclose(Q.T @ Q, np.eye(3), rtol=0, atol=1e-12) or np.linalg.det(Q) < 0:
        raise ValueError('Disk orientation must be a proper orthogonal matrix')
    u, w = np.polynomial.legendre.leggauss(radial_order)
    r = radius_m * np.sqrt((u + 1) / 2)
    theta = 2 * pi * (np.arange(azimuth_nodes) + .5) / azimuth_nodes
    xx, yy = r[:, None] * np.cos(theta), r[:, None] * np.sin(theta)
    local = np.stack((xx, yy, np.zeros_like(xx)), axis=-1).reshape(-1, 3)
    nodes = local @ Q.T + np.asarray(center)
    normals = np.broadcast_to(Q[:, 2], nodes.shape).copy()
    fractions = np.repeat(w / (2 * azimuth_nodes), azimuth_nodes)
    return Source(nodes, normals, fractions, exponent)


@dataclass
class PlanetaryPose:
    orbit_radius_m: float
    height_m: float
    carrier_rpm: float
    spin_ratio_absolute: float
    phase_carrier_rad: float = 0.
    phase_relative_rad: float = 0.
    tilt_rad: float = 0.

    def evaluate(self, t_s, local_points_m, local_normals):
        """Q=Rz(phi) Ry(tilt) Rz(alpha); spin_ratio_absolute only for tilt=0.
        For tilt!=0, ratio-1 defines relative actuator rotation about tilted axis.
        """
        t = np.atleast_1d(t_s)
        omega = self.carrier_rpm * 2 * pi / 60
        phi = self.phase_carrier_rad + omega * t
        alpha = self.phase_relative_rad + (self.spin_ratio_absolute - 1) * omega * t
        Q = rotation_z(phi) @ rotation_y(self.tilt_rad) @ rotation_z(alpha)
        c = np.stack((self.orbit_radius_m * np.cos(phi),
                      self.orbit_radius_m * np.sin(phi), np.full_like(phi, self.height_m)), axis=-1)
        x = np.einsum('tij,pj->tpi', Q, np.asarray(local_points_m)) + c[:, None, :]
        normals = unit_vectors(np.asarray(local_normals), 'surface normals')
        n = np.einsum('tij,pj->tpi', Q, normals)
        return x, n


@dataclass
class RectangleMask:
    center_m: np.ndarray
    orientation: np.ndarray  # columns = local u, v, w in laboratory frame
    half_width_m: float
    half_height_m: float
    thickness_m: float = 0.

    def __post_init__(self):
        self.center_m = np.asarray(self.center_m, dtype=float)
        self.orientation = np.asarray(self.orientation, dtype=float)
        if self.center_m.shape != (3,) or self.orientation.shape != (3, 3):
            raise ValueError('Mask center/orientation shape invalid')
        if not np.allclose(self.orientation.T @ self.orientation, np.eye(3), rtol=0, atol=1e-12) or np.linalg.det(self.orientation) < 0:
            raise ValueError('Mask orientation must be a proper orthogonal matrix')
        if not np.all(np.isfinite(self.center_m)) or not np.all(np.isfinite([self.half_width_m, self.half_height_m, self.thickness_m])):
            raise ValueError('Mask geometry must be finite')
        if min(self.half_width_m, self.half_height_m) <= 0 or self.thickness_m < 0:
            raise ValueError('Mask widths positive, thickness nonnegative')

    def blocked(self, source_xyz, target_xyz):
        """Vectorized open-segment vs opaque rectangle or finite rectangular solid.
        Broadcastable (...,3) inputs. Boundary contact counts blocked. A ray
        coplanar with an ideal zero-thickness mask is excluded (measure-zero case).
        """
        a = (np.asarray(source_xyz) - self.center_m) @ self.orientation
        b = (np.asarray(target_xyz) - self.center_m) @ self.orientation
        d = b - a
        eps = 1e-14  # m, only protects parallel-ray division in this SI demo
        if self.thickness_m == 0:
            denom = d[..., 2]
            valid = np.abs(denom) > eps
            lam = np.divide(-a[..., 2], denom, out=np.zeros_like(denom), where=valid)
            hit = a + lam[..., None] * d
            return valid & (lam > 0) & (lam < 1) & (np.abs(hit[..., 0]) <= self.half_width_m) & (np.abs(hit[..., 1]) <= self.half_height_m)
        bounds = np.array([self.half_width_m, self.half_height_m, self.thickness_m / 2])
        parallel = np.abs(d) <= eps
        outside_parallel = parallel & (np.abs(a) > bounds)
        lo = np.divide(-bounds - a, d, out=np.zeros_like(d), where=~parallel)
        hi = np.divide(bounds - a, d, out=np.zeros_like(d), where=~parallel)
        enter = np.where(parallel, -np.inf, np.minimum(lo, hi)).max(axis=-1)
        leave = np.where(parallel, np.inf, np.maximum(lo, hi)).min(axis=-1)
        return (~outside_parallel.any(axis=-1)) & (np.maximum(enter, 0) <= np.minimum(leave, 1)) & (leave > 0) & (enter < 1)


def transfer_kernel(points_m, normals, source: Source, masks: Sequence[RectangleMask] = ()):
    """Mass-capture kernel [1/m^2], incl. incidence and node-rate fractions.
    Shape input (..., P,3), output (...,P). Unit incoming-facing normals expected.
    Sticking and film density are deliberately excluded.
    """
    x = np.asarray(points_m, dtype=float)
    n = np.asarray(normals, dtype=float)
    delta = x[..., None, :] - source.positions_m
    r2 = np.sum(delta * delta, axis=-1)
    if np.any(r2 <= 0):
        raise ValueError('Target coincides with source node')
    u = delta / np.sqrt(r2)[..., None]
    cs = np.sum(u * source.normals, axis=-1)
    ci = np.sum(-u * n[..., None, :], axis=-1)
    # Explicit hemisphere gate matters for p=0: 0**0 must not emit backwards.
    f = np.where(cs > 0, (source.exponent + 1) / (2 * pi) * np.maximum(cs, 0) ** source.exponent, 0.)
    kernel = f * np.maximum(ci, 0) / r2
    for mask in masks:
        kernel *= ~mask.blocked(source.positions_m, x[..., None, :])
    return np.sum(kernel * source.fractions, axis=-1)


def time_quadrature(t0_s, t1_s, panels, order=1, breakpoints=()):
    """Composite Gauss-Legendre. Order 1 = midpoint; splits all known events.
    panels is a global target; each interval receives ceil(duration / target_dt).
    Returned nodes do not hit integration endpoints.
    """
    if t1_s <= t0_s or panels < 1 or order < 1:
        raise ValueError('Positive duration, panels and order required')
    events = sorted(set([float(t0_s), float(t1_s)] + [float(x) for x in breakpoints if t0_s < x < t1_s]))
    q, w = np.polynomial.legendre.leggauss(order)
    t, weights = [], []
    max_dt = (t1_s - t0_s) / panels
    for a, b in zip(events[:-1], events[1:]):
        n = max(1, int(np.ceil((b - a) / max_dt)))
        edges = np.linspace(a, b, n + 1)
        h = np.diff(edges)
        t.append((edges[:-1, None] + h[:, None] * (q + 1) / 2).ravel())
        weights.append(np.broadcast_to(h[:, None] * w / 2, (n, order)).ravel())
    return np.concatenate(t), np.concatenate(weights)


def deposit(pose: PlanetaryPose, local_points_m, local_normals, source: Source,
            total_rate_kg_s: Callable, density_kg_m3, t0_s, t1_s,
            panels=256, order=4, sticking=1., masks=(), breakpoints=(), time_chunk=32):
    """Return normal thickness in m, numerical node counts and kg emitted.
    masks may be static sequence or callable(t_scalar)->sequence.
    This implementation supports scalar sticking only; no re-evaporation.
    """
    if not np.isfinite(density_kg_m3) or density_kg_m3 <= 0 or not 0 <= sticking <= 1:
        raise ValueError('Positive finite density and sticking in [0,1] required')
    if time_chunk < 1:
        raise ValueError('time_chunk must be positive')
    ts, ws = time_quadrature(t0_s, t1_s, panels, order, breakpoints)
    rates = np.broadcast_to(np.asarray(total_rate_kg_s(ts), dtype=float), ts.shape)
    if np.any(~np.isfinite(rates)) or np.any(rates < 0):
        raise ValueError('Mass emission rates must be finite and nonnegative')
    out = np.zeros(len(local_points_m))
    for k in range(0, len(ts), time_chunk):
        tt, ww, rr = ts[k:k+time_chunk], ws[k:k+time_chunk], rates[k:k+time_chunk]
        x, n = pose.evaluate(tt, local_points_m, local_normals)
        if callable(masks):
            kern = np.stack([transfer_kernel(x[i], n[i], source, masks(float(t))) for i, t in enumerate(tt)])
        else:
            kern = transfer_kernel(x, n, source, masks)
        out += np.sum(kern * (ww * rr)[:, None], axis=0)
    return {'thickness_m': out * sticking / density_kg_m3,
            'retained_areal_mass_kg_m2': out * sticking,
            'time_nodes': len(ts), 'source_nodes': len(source.fractions),
            'emitted_mass_kg': float(ws @ rates)}


def ring_points(radius_m, count=72):
    a = 2 * pi * np.arange(count) / count
    p = np.stack((radius_m * np.cos(a), radius_m * np.sin(a), np.zeros(count)), axis=-1)
    return p, np.tile([0., 0., -1.], (count, 1))


def disk_surface(radius_m, radial_order=8, azimuth_nodes=32, curvature_radius_m=None):
    """Projected-area disk sampling; weights converted to actual curved area.
    Spherical graph z=R-sqrt(R^2-r^2), downward-facing normal.
    """
    src = disk_source(radius_m, radial_order, azimuth_nodes)
    p = src.positions_m.copy()
    n = np.tile([0., 0., -1.], (len(p), 1))
    area = src.fractions * pi * radius_m ** 2
    if curvature_radius_m is not None:
        if curvature_radius_m <= radius_m:
            raise ValueError('Curvature radius must exceed aperture radius')
        r2 = np.sum(p[:, :2] ** 2, axis=1)
        root = np.sqrt(curvature_radius_m ** 2 - r2)
        p[:, 2] = curvature_radius_m - root
        n[:, :2], n[:, 2] = p[:, :2] / curvature_radius_m, -root / curvature_radius_m
        area *= curvature_radius_m / root
    return p, n, area


def thickness_metrics(h_m, area_weights=None):
    h = np.asarray(h_m)
    w = np.ones_like(h) if area_weights is None else np.asarray(area_weights)
    mean = np.sum(w * h) / np.sum(w)
    if mean <= 0:
        raise ValueError('Positive mean thickness required for relative metrics')
    cv = np.sqrt(np.sum(w * (h-mean)**2) / np.sum(w)) / mean
    return {'mean_m': float(mean), 'min_m': float(h.min()), 'max_m': float(h.max()),
            'peak_to_valley_over_mean': float((h.max()-h.min())/mean),
            'max_absolute_deviation_over_mean': float(np.max(np.abs(h-mean))/mean),
            'coefficient_of_variation': float(cv)}
