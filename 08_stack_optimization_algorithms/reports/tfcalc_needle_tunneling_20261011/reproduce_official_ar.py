"""Independent read-only reproduction of TFCalc's public Ge AR layer table.
No TFCalc software or proprietary code is used. Python + NumPy only.
Source: https://www.hulinks.co.jp/en/tfcalc/examples/list-of-coating-design/growing-antireflection/
The source's 13 layer thicknesses are listed substrate -> air. Constant real
indices are the source's demonstration assumptions, not measured optical data.
The dense sample is not a certified bound over the wavelength continuum.
"""
from pathlib import Path
import json
import numpy as np

THICKNESS_NM_SUBSTRATE_FIRST = np.array([
    157.14, 285.97, 563.34, 84.60, 1827.50, 81.75, 2590.54,
    1142.59, 1234.92, 131.55, 457.49, 629.03, 1076.97,
])
INDEX_SUBSTRATE_FIRST = np.array([2.2 if j % 2 == 0 else 4.2 for j in range(13)])

def airy_r(wavelength_nm, indices_incident_first, thickness_nm_incident_first):
    """Normal-incidence lossless Airy recursion, exp(-i omega t) convention."""
    w = np.asarray(wavelength_nm, float)
    n = np.asarray(indices_incident_first, float)
    d = np.asarray(thickness_nm_incident_first, float)
    if len(n) != len(d) + 2 or np.any(w <= 0) or np.any(d < 0):
        raise ValueError("invalid layer data")
    r = np.full(w.shape, (n[-2] - n[-1]) / (n[-2] + n[-1]), dtype=complex)
    for j in range(len(d) - 1, -1, -1):
        fresnel = (n[j] - n[j + 1]) / (n[j] + n[j + 1])
        round_trip = np.exp(4j * np.pi * n[j + 1] * d[j] / w)
        r = (fresnel + r * round_trip) / (1 + fresnel * r * round_trip)
    return r

def main():
    w = np.linspace(7700.0, 12300.0, 20001)
    n = np.r_[1.0, INDEX_SUBSTRATE_FIRST[::-1], 4.0]
    d = THICKNESS_NM_SUBSTRATE_FIRST[::-1]
    R = abs(airy_r(w, n, d)) ** 2
    # Control: exact zero-thickness neutral layer; no coating gives bare Ge R=0.36.
    neutral = abs(airy_r(w, [1.0, 2.2, 4.0], [0.0])) ** 2
    assert np.max(abs(neutral - 0.36)) < 2e-15
    assert np.max(R) < 0.01
    result = {
        "retrieval_date_utc": "2026-10-11",
        "source": "https://www.hulinks.co.jp/en/tfcalc/examples/list-of-coating-design/growing-antireflection/",
        "source_model": "lossless constant indices air=1, H=4.2, L=2.2, bulk Ge=4.0; normal incidence",
        "layer_order_in_source": "substrate_to_air",
        "number_of_layers": 13,
        "total_physical_thickness_nm": float(d.sum()),
        "source_tunneling_trigger_thickness_nm": 10000.0,
        "excess_over_source_tunneling_trigger_thickness_nm": float(d.sum() - 10000),
        "wavelength_nm": [7700, 12300],
        "dense_points": len(w),
        "max_sampled_R": float(R.max()),
        "max_sampled_R_percent": float(100 * R.max()),
        "wavelength_at_max_nm": float(w[R.argmax()]),
        "mean_integral_R": float(np.trapezoid(R, w) / (w[-1] - w[0])),
        "R_at_endpoints": [float(R[0]), float(R[-1])],
        "bare_Ge_control_R": float(neutral[0]),
        "claim": "reproduction of final public layer table, not of TFCalc's proprietary synthesis path or runtime",
        "limitations": "dense-sample check only; rounded thickness table; constant lossless index assumptions; no measured process qualification",
    }
    out = Path(__file__).with_name("official_ar_reproduction.json")
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
