#!/usr/bin/env python3
"""Recompute the public 43-physical-layer TFCalc example's lossless baseline.

Requirements: Python 3 and NumPy. Run from this directory:
  python recompute_tfcalc43_public_case.py
This computes a fixed-geometry forward model only. It does not optimize a coating.
The table is physical nanometres, ordered from substrate outward in the source;
this program reverses it for air-to-glass illumination. It must not be QWOT-scaled.
"""
import csv
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
CSV = HERE / 'prescription_tfcalc43.csv'
OUT = HERE / 'tfcalc43_lossless_reproduction.json'

# Published lossless reference indices and geometry.
N_AIR, N_H, N_L, N_GLASS = 1.0, 2.35, 1.45, 1.52
ANGLE_DEG = 50.0


def load_stack():
    with CSV.open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    # Source order: first layer nearest substrate. Solver order is reversed.
    rows.sort(key=lambda r: int(r['solver_incident_to_substrate_index']))
    labels = [r['material'] for r in rows]
    d_nm = np.array([float(r['physical_thickness_nm']) for r in rows])
    assert len(labels) == 43 and labels.count('H') == 22 and labels.count('L') == 21
    assert abs(float(d_nm.sum()) - 3943.75) < 1e-9
    return labels, d_nm


def rta(wavelength_nm, labels, thicknesses_nm, pol):
    beta = N_AIR * np.sin(np.deg2rad(ANGLE_DEG))
    layer_indices = np.array([N_H if m == 'H' else N_L for m in labels], dtype=complex)
    n = np.r_[N_AIR, layer_indices, N_GLASS].astype(complex)
    q = np.sqrt(n * n - beta * beta + 0j)
    q = np.where((q.imag < 0) | ((q.imag == 0) & (q.real < 0)), -q, q)
    y = q if pol == 's' else n * n / q
    mtx = np.eye(2, dtype=complex)
    for j, d in enumerate(thicknesses_nm, start=1):
        phase = 2 * np.pi * q[j] * d / wavelength_nm
        c, s = np.cos(phase), np.sin(phase)
        mtx = mtx @ np.array([[c, -1j * s / y[j]], [-1j * y[j] * s, c]])
    v = mtx @ np.array([1.0, y[-1]])
    yin = v[1] / v[0]
    refl = (y[0] - yin) / (y[0] + yin)
    den = y[0] * mtx[0, 0] + y[0] * y[-1] * mtx[0, 1] + mtx[1, 0] + y[-1] * mtx[1, 1]
    R = float(abs(refl) ** 2)
    T = float(4 * y[0].real * y[-1].real / abs(den) ** 2)
    return R, T, 1.0 - R - T


def summarize(labels, d_nm, pol, waves):
    vals = np.array([rta(float(w), labels, d_nm, pol) for w in waves])
    idx = int(np.argmin(vals[:, 0]))
    mean = np.sum((vals[:-1] + vals[1:]) * 0.5 * np.diff(waves)[:, None], axis=0) / (waves[-1] - waves[0])
    return {
        'polarization': pol,
        'uniform_wavelength_trapezoid_mean_R': float(mean[0]),
        'uniform_wavelength_trapezoid_mean_T': float(mean[1]),
        'uniform_wavelength_trapezoid_mean_A': float(mean[2]),
        'grid_min_R': float(vals[idx, 0]),
        'grid_min_wavelength_nm': float(waves[idx]),
        'grid_step_nm': float(waves[1] - waves[0]),
        'grid_points': int(len(waves)),
    }


def main():
    labels, d_nm = load_stack()
    waves_01 = np.arange(4000, 8001, dtype=float) / 10.0
    waves_union = np.arange(8000, 16001, dtype=float) / 20.0
    result = {
        'scope': 'fixed-geometry forward reproduction only; no optimization',
        'source_table': 'Hulinks TFCalc broadband high-reflection example',
        'layer_count': len(labels),
        'H_count': labels.count('H'),
        'L_count': labels.count('L'),
        'total_thickness_nm': float(d_nm.sum()),
        'angle_deg': ANGLE_DEG,
        'wavelength_range_nm': [400.0, 800.0],
        'indices': {'air': N_AIR, 'H': N_H, 'L': N_L, 'glass': N_GLASS},
        'results': {
            'p_0p1nm_grid': summarize(labels, d_nm, 'p', waves_01),
            'p_0p05nm_grid': summarize(labels, d_nm, 'p', waves_union),
            's_0p1nm_grid': summarize(labels, d_nm, 's', waves_01),
            's_0p05nm_grid': summarize(labels, d_nm, 's', waves_union),
        },
        'caveat': 'The source describes approximately 98% AVERAGE p reflectance, not a 98% minimum. The 0.05 nm grid is not an interval-arithmetic proof.',
    }
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(result['results']['p_0p05nm_grid'], indent=2))


if __name__ == '__main__':
    main()
