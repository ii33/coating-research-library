"""Write explicitly synthetic spectra and summary. No measured process data."""
import csv
import json
from pathlib import Path

from model import (DrudeLorentz, Lorentz, cm3_to_m3, cm2_vs_to_m2_vs,
                   nm_to_m, ev_to_rad_s, dc_conductivity, sheet_resistance,
                   incoherent_substrate_rt, weighted_mean)


def main():
    out = Path(__file__).resolve().parent / 'results'
    out.mkdir(exist_ok=True)
    cases = [
        {'name': 'synthetic_baseline', 'N_cm3': 3e20, 'mu_opt_cm2_Vs': 35,
         'mu_transport_cm2_Vs': 25, 'thickness_nm': 100},
        {'name': 'synthetic_higher_N', 'N_cm3': 6e20, 'mu_opt_cm2_Vs': 25,
         'mu_transport_cm2_Vs': 18, 'thickness_nm': 100},
        {'name': 'synthetic_thicker', 'N_cm3': 3e20, 'mu_opt_cm2_Vs': 35,
         'mu_transport_cm2_Vs': 25, 'thickness_nm': 200},
    ]
    summary = {
        'status': 'SIMULATED_SYNTHETIC_NOT_MEASURED_NOT_PROCESS_CALIBRATED',
        'spectral_domain_nm': [400, 2500],
        'geometry': 'normal air/coherent isotropic ITO/lossless incoherent glass/air',
        'glass_index': 1.5,
        'shared_assumptions': {'effective_mass_me': 0.35, 'epsilon_inf': 3.9,
                               'lorentz_strength': 0.3, 'resonance_eV': 4.0,
                               'damping_eV': 0.4},
        'averaging': 'uniform wavelength weighting; NOT luminous or solar transmittance',
        'cases': [],
    }
    rows = []
    for case in cases:
        m = DrudeLorentz(cm3_to_m3(case['N_cm3']),
                        cm2_vs_to_m2_vs(case['mu_opt_cm2_Vs']), 0.35, 3.9,
                        (Lorentz(0.3, ev_to_rad_s(4), ev_to_rad_s(0.4)),))
        sigma = dc_conductivity(cm3_to_m3(case['N_cm3']),
                               cm2_vs_to_m2_vs(case['mu_transport_cm2_Vs']))
        spectrum = []
        for nm in range(400, 2501, 10):
            wl = nm_to_m(nm)
            nk = m.nk(wl)
            result = incoherent_substrate_rt(wl, [(nk, nm_to_m(case['thickness_nm']))])
            row = {'status': 'synthetic', 'case': case['name'], 'wavelength_nm': nm,
                   'n': nk.real, 'k': nk.imag, 'R': result.R, 'T': result.T, 'A': result.A}
            rows.append(row)
            spectrum.append(row)
        result_case = dict(case)
        result_case['R_sheet_ohm_square'] = sheet_resistance([(sigma, nm_to_m(case['thickness_nm']))])
        result_case['rho_parallel_ohm_m'] = 1 / sigma
        for lo, hi, label in [(400, 700, '400_700_nm'), (700, 2500, '700_2500_nm')]:
            sel = [r for r in spectrum if lo <= r['wavelength_nm'] <= hi]
            x = [r['wavelength_nm'] for r in sel]
            for quantity in ('R', 'T', 'A'):
                result_case[f'mean_{quantity}_{label}_flat_wavelength'] = weighted_mean(
                    x, [r[quantity] for r in sel], [1] * len(sel))
        summary['cases'].append(result_case)
    with (out / 'synthetic_spectra.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (out / 'synthetic_summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
