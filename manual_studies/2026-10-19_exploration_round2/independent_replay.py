#!/usr/bin/env python3
"""Read-only independent finite optical replay of the frozen round-two files.

Uses a separately implemented scalar Fresnel recursion. Shifted grids, endpoints
and local numerical extremum refinement are evidence, not a continuous proof.
No replay value is fed to an experiment's search or candidate selection.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import minimize_scalar

ROOT = Path(__file__).resolve().parent
COUNTS = dict(calls=0, wavelength_points=0, literal_layer_point_updates=0)


def package_fingerprint():
    result = {}
    for name in ['batched-audit', 'lookahead', 'phase-guide']:
        for p in sorted((ROOT/name).rglob('*')):
            relative = p.relative_to(ROOT)
            if p.is_file() and not any(x.startswith('.') or x == '__pycache__' for x in relative.parts):
                result[str(relative)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return result


def amplitudes(wavelength, thickness, indices, n0=1.0, ns=3.42, reference_z=None):
    """Independent scalar two-port recursion; exp(-iwt), forward exp(+ikz)."""
    w = np.atleast_1d(np.asarray(wavelength, dtype=float))
    d = np.asarray(thickness, dtype=float)
    n = np.asarray(indices, dtype=complex)
    if len(d) != len(n) or np.any(d < 0) or np.any(w <= 0):
        raise ValueError("invalid thickness, index or wavelength")
    media = np.r_[complex(n0), n, complex(ns)]
    r = np.full(w.shape, (media[-2]-media[-1])/(media[-2]+media[-1]), complex)
    t = np.full(w.shape, 2*media[-2]/(media[-2]+media[-1]), complex)
    for j in range(len(d)-1, -1, -1):
        delta = 2*np.pi*media[j+1]*d[j]/w
        rij = (media[j]-media[j+1])/(media[j]+media[j+1])
        denominator = 1+rij*r*np.exp(2j*delta)
        t = (2*media[j]/(media[j]+media[j+1]))*t*np.exp(1j*delta)/denominator
        r = (rij+r*np.exp(2j*delta))/denominator
    t *= np.sqrt(float(ns/n0))
    if reference_z is not None:
        distance = -float(np.sum(d))-reference_z
        r *= np.exp(4j*np.pi*n0*distance/w)
        t *= np.exp(2j*np.pi*n0*distance/w)
    COUNTS['calls'] += 1
    COUNTS['wavelength_points'] += len(w)
    COUNTS['literal_layer_point_updates'] += len(w)*len(d)
    return r, t


def power(w, d, n, n0=1., ns=3.42, quantity='R'):
    r, t = amplitudes(w, d, n, n0, ns)
    return abs(r if quantity == 'R' else t)**2


def extrema(d, n, windows, n0=1., ns=3.42, quantity='R', intervals=8192):
    rows = []
    for lo, hi in windows:
        # Irrational-looking shift differs from the search and published reference.
        shift = .3819660112501051
        w = np.r_[lo, lo+(np.arange(intervals)+shift)*(hi-lo)/intervals, hi]
        y = power(w, d, n, n0, ns, quantity)
        peaks = [(float(w[np.argmax(y)]), float(max(y)))]
        ix = np.flatnonzero((y[1:-1]>y[:-2]) & (y[1:-1]>y[2:]))+1
        failures = []
        for j in ix:
            mid = (w[j-1]+w[j+1])/2
            half = (w[j+1]-w[j-1])/2
            fit = minimize_scalar(lambda u: -float(power([mid+half*u], d, n, n0, ns, quantity)[0]),
                                  bounds=(-1., 1.), method='bounded',
                                  options=dict(xatol=1e-12, maxiter=120))
            peaks.append((float(mid+half*fit.x), float(-fit.fun)))
            if not fit.success:
                failures.append(str(fit.message))
        loc, worst = max(peaks, key=lambda x: x[1])
        r, t = amplitudes([loc], d, n, n0, ns)
        row = dict(window_um=[lo, hi], max=worst, argmax_um=loc,
                   shifted_grid_points=len(w), local_maxima_refined=len(ix),
                   local_search_failures=failures,
                   lossless_RT_closure_error=abs(float(abs(r[0])**2+abs(t[0])**2-1)))
        if quantity == 'T':
            row['lossless_T_from_independent_R_at_peak'] = 1-float(abs(r[0])**2)
        rows.append(row)
    return dict(max=max(x['max'] for x in rows), windows=rows)


def load_module(name, relative):
    path = ROOT/relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def physics_check():
    kernel = load_module('audit_round2_kernel', 'batched-audit/kernel/run_experiment.py')
    rng = np.random.default_rng(61019471)
    err = uniterr = phaseerr = closure = 0.
    for i in range(32):
        layers = int(rng.integers(0, 14))
        d = rng.uniform(.005, 1.8, layers)
        n = rng.uniform(1.2, 3.5, layers)
        if i % 2:
            n = n+1j*rng.uniform(0., .05, layers)
        w = rng.uniform(.55, 13., 139)
        r, t = amplitudes(w, d, n)
        kr, kt = kernel.tmm_normal(w, d, n)
        err = max(err, float(max(abs(abs(r)**2-kr))), float(max(abs(abs(t)**2-kt))))
        ru, tu = amplitudes(w*1000, d*1000, n, reference_z=-20000.)
        rf, tf = amplitudes(w, d, n, reference_z=-20.)
        uniterr = max(uniterr, float(max(abs(ru-rf))), float(max(abs(tu-tf))))
        ra, ta = amplitudes(w, np.r_[.31, d], np.r_[1., n], reference_z=-20.)
        phaseerr = max(phaseerr, float(max(abs(ra-rf))), float(max(abs(ta-tf))))
        if not i % 2:
            closure = max(closure, float(max(abs(abs(r)**2+abs(t)**2-1))))
    return dict(random_stacks=32, matrix_vs_independent_power_max_error=err,
                um_nm_common_reference_amplitude_error=uniterr,
                ambient_front_insertion_common_reference_error=phaseerr,
                random_lossless_RT_closure_max_error=closure)


def replay_batched(issues):
    result = json.loads((ROOT/'batched-audit/results.json').read_text())
    rows = []
    classification_errors = budget_errors = 0
    for candidate in result['references']:
        ref = extrema(candidate['d'], candidate['n'], [result['config']['band_um']],
                      n0=1., ns=1., quantity='T', intervals=65536)
        key = candidate['group'], candidate['case']
        matching = [x for x in result['fixed_rows'] if (x['group'], x['case']) == key]
        row = dict(group=key[0], case=key[1], independent=ref,
                   reported_reference_max=candidate['reference']['max'])
        for table in ['fixed_rows', 'timing_rows', 'wall_rows']:
            for x in result[table]:
                if (x['group'], x['case']) != key:
                    continue
                fp = x['sampled_max'] <= .5 and ref['max'] > .5
                fa = x['sampled_max'] > .5 and ref['max'] <= .5
                if fp != x['false_pass'] or fa != x['false_alarm']:
                    classification_errors += 1
                if x['layer_point_work'] != x['physical_points']*len(candidate['d']):
                    budget_errors += 1
                if table != 'wall_rows' and x['physical_points'] != 129:
                    budget_errors += 1
        row['fixed_methods'] = len(matching)
        rows.append(row)
        print('batched replay', *key, flush=True)
    if classification_errors:
        issues.append('batched classification differs from independent replay')
    if budget_errors:
        issues.append('batched point×layer budget inconsistency')
    diagnostic_path = ROOT/'batched-audit/scaled_scalar_diagnostic.json'
    diagnostic = None
    if diagnostic_path.exists():
        raw = json.loads(diagnostic_path.read_text())
        lookup = {(r['group'], r['case']): r['independent']['max'] for r in rows}
        diag_errors = 0
        for r in raw['rows']:
            refmax = lookup[('prior_ultranarrow', r['case'])]
            if r['false_pass'] != bool(r['sampled_max'] <= .5 and refmax > .5):
                diag_errors += 1
            if r['false_alarm'] != bool(r['sampled_max'] > .5 and refmax <= .5):
                diag_errors += 1
            if r['layer_point_work'] != r['physical_points']*r['layers']:
                diag_errors += 1
            if r['mode'] == 'points129' and r['physical_points'] != 129:
                diag_errors += 1
        if diag_errors:
            issues.append('scaled scalar diagnostic classification or cost inconsistency')
        diagnostic = dict(rows=len(raw['rows']), inconsistencies=diag_errors, summary=raw['summary'])
    return dict(candidates=rows, classification_errors=classification_errors,
                budget_errors=budget_errors,
                scaled_scalar_diagnostic=diagnostic,
                max_reference_difference=max(abs(x['independent']['max']-x['reported_reference_max']) for x in rows))


def replay_phase(issues):
    result = json.loads((ROOT/'phase-guide/results.json').read_text())
    rows = []
    budget_errors = pass_errors = 0
    labeled = [('main', r) for r in result['rows']]
    labeled += [('reference_ablation', r) for r in result.get('reference_ablation', [])]
    diagnostics_path = ROOT/'phase-guide/withdrawal_and_counterexamples.json'
    if diagnostics_path.exists():
        diagnostics = json.loads(diagnostics_path.read_text())
        source = {(r['case'], r['seed'], r['method']): r for r in result['rows']}
        for r in diagnostics['polished']:
            old = source[r['case'], r['seed'], r['original_method']]
            if r['combined_point_layers'] != old['total']['point_layers']+r['total']['point_layers']:
                budget_errors += 1
            if r['input_archive_origin_tau'] != old['selected_archive_tau']:
                issues.append('pure-power refinement lost source archive origin')
            if len(r['history']) != 12 or not all(h['tau'] == 1. and h['auxiliary_weight'] == 0. for h in r['history']):
                issues.append('pure-power refinement auxiliary withdrawal incomplete')
            if (r['V'], r['mean_R']) > (old['V'], old['mean_R']):
                issues.append('pure-power delivery regressed on common final audit')
            if r['retained_original_after_common_audit'] and (r['d_um'] != old['d_um'] or r['V'] != old['V']):
                issues.append('retained physical archive not preserved')
        labeled += [('zero_auxiliary_polish', r) for r in diagnostics['polished']]
        labeled += [('theta_sensitivity', r) for r in diagnostics['theta_sensitivity']]
        for r in diagnostics['polished']:
            if r.get('raw_polish_d_um') != r['d_um'] and 'raw_polish_d_um' in r:
                raw = dict(r, d_um=r['raw_polish_d_um'], V=r['raw_polish_V'])
                labeled.append(('raw_polish_replaced_by_original', raw))
    for group_name, candidate in labeled:
        n = [1.45, 2.35]*(len(candidate['d_um'])//2)
        windows = [x['window_um'] for x in candidate['per_window']]
        ref = extrema(candidate['d_um'], n, windows, intervals=16384)
        V = max(0., ref['max']/.01-1)
        actual = {k: sum(x[k] for x in candidate['counts'].values())
                  for k in ['calls', 'points', 'point_layers']}
        if actual != candidate['total']:
            budget_errors += 1
        for group in candidate['counts'].values():
            if group['point_layers'] != group['points']*len(n):
                budget_errors += 1
        if bool(V <= 1e-8) != candidate['pass_finite_grid']:
            pass_errors += 1
        rows.append(dict(group=group_name, case=candidate['case'], seed=candidate['seed'], method=candidate['method'],
                         original_method=candidate.get('original_method'),
                         input_archive_origin_tau=candidate.get('input_archive_origin_tau'),
                         theta_max=candidate.get('theta_max'),
                         plane_shift_um=candidate.get('plane_shift_um', 0.),
                         surface_reference_ablation=candidate.get('surface_reference_ablation', False),
                         independent=ref, independent_V=V, reported_V=candidate['V'],
                         reported_point_layers=candidate['total']['point_layers']))
    paired = []
    for case in sorted(set(r['case'] for r in result['rows'])):
        for seed in sorted(set(r['seed'] for r in result['rows'])):
            group = [r for r in result['rows'] if r['case'] == case and r['seed'] == seed
                     and r['method'] != 'direct_local']
            costs = {r['method']: r['total']['point_layers'] for r in group}
            equal = len(set(costs.values())) == 1
            paired.append(dict(case=case, seed=seed, equal_actual_point_layers=equal, costs=costs))
            if not equal:
                budget_errors += 1
    if budget_errors:
        issues.append('phase actual point×layer budget inconsistency')
    if pass_errors:
        issues.append('phase finite-pass classification changed in independent replay')
    # Check complex amplitudes, not only powers: reference-plane signs matter.
    sys.path.insert(0, str(ROOT/'phase-guide'))
    phase = load_module('audit_round2_phase', 'phase-guide/run_phase.py')
    sys.path.pop(0)
    rng = np.random.default_rng(751902)
    complex_error = 0.
    for _ in range(20):
        N = int(rng.integers(1, 9))
        dd = rng.uniform(.01, 2.3, N)
        nn = rng.uniform(1.2, 3.5, N)
        w = rng.uniform(.6, 13., 97)
        depth = N*2.5+1.713
        ri, ti = amplitudes(w, dd, nn, reference_z=-depth)
        rp, tp = phase.amplitudes(w, dd, nn, reference_depth=N*2.5, plane_shift=1.713)
        complex_error = max(complex_error, float(max(abs(ri-rp))), float(max(abs(ti-np.sqrt(3.42)*tp))))
    if complex_error > 1e-11:
        issues.append('phase common-reference complex amplitudes differ')
    return dict(candidates=rows, cost_pairs=paired, budget_errors=budget_errors,
                independent_complex_reference_max_error=complex_error,
                pass_errors=pass_errors,
                max_abs_V_replay_difference=max(abs(r['independent_V']-r['reported_V']) for r in rows))


def curve_extrema(function, windows, intervals=8192):
    values = []
    for lo, hi in windows:
        if lo == hi:
            values.append(dict(window_um=[lo, hi], max=float(function(np.array([lo]))[0]),
                               argmax_um=lo, grid_points=1, local_maxima_refined=0))
            continue
        w = np.r_[lo, lo+(np.arange(intervals)+.3819660112501051)*(hi-lo)/intervals, hi]
        y = function(w)
        peaks = [(float(w[np.argmax(y)]), float(max(y)))]
        ix = np.flatnonzero((y[1:-1]>y[:-2]) & (y[1:-1]>y[2:]))+1
        for j in ix:
            mid = (w[j-1]+w[j+1])/2
            half = (w[j+1]-w[j-1])/2
            fit = minimize_scalar(lambda u: -float(function(np.array([mid+half*u]))[0]),
                                  bounds=(-1., 1.), method='bounded',
                                  options=dict(xatol=1e-12, maxiter=120))
            peaks.append((float(mid+half*fit.x), float(-fit.fun)))
        loc, value = max(peaks, key=lambda x: x[1])
        values.append(dict(window_um=[lo, hi], max=value, argmax_um=loc,
                           grid_points=len(w), local_maxima_refined=len(ix)))
    return dict(max=max(x['max'] for x in values), windows=values)


def replay_lookahead(issues):
    result = json.loads((ROOT/'lookahead/results/results.json').read_text())
    cfg = result['config']
    materials = cfg['material_n']
    thicknesses = cfg['thickness_catalog_um']
    def decode(stack):
        return [thicknesses[j] for i, j in stack], [materials[i] for i, j in stack]
    actions = [(i, j) for i in range(len(materials)) for j in range(len(thicknesses))]
    catalog = [()]
    level = [()]
    for depth in range(cfg['max_layers']):
        level = [(a,)+s for s in level for a in actions if not s or a[0] != s[0][0]]
        catalog.extend(level)
    wl = np.array(cfg['train_wavelengths_um'])
    responses = np.array([power(wl, *decode(s)) for s in catalog])
    def score(response, target, case):
        mask = np.zeros(len(wl), bool)
        for lo, hi in case['windows']:
            mask |= (wl >= lo-1e-12) & (wl <= hi+1e-12)
        delta = response[mask] if case['kind'] == 'ar' else abs(response[mask]-target[mask])
        g = delta/case['tolerance']-1
        return (max(0., float(max(g))), float(np.mean(np.maximum(g, 0.)**2)), float(max(g)))
    lookup = {s: i for i, s in enumerate(catalog)}
    cases = {c['name']: c for c in cfg['cases']}
    oracles = []
    oracle_errors = 0
    for name, case in cases.items():
        planted = tuple(map(tuple, case.get('planted_stack', [])))
        target = responses[lookup[planted]] if case['kind'] == 'planted' else np.zeros(len(wl))
        scores = [score(R, target, case) for R in responses]
        minV = min(x[0] for x in scores)
        feasible = sum(x[0] <= 1e-12 for x in scores)
        reported = result['oracle'][name]
        reported_stack = tuple(map(tuple, reported['stack']))
        if abs(minV-reported['score'][0]) > 1e-10 or feasible != reported['feasible_count']:
            oracle_errors += 1
        oracles.append(dict(case=name, independent_min_V=minV, independent_feasible_count=feasible,
                            reported_best_stack_independent_score=scores[lookup[reported_stack]],
                            reported_min_V=reported['score'][0], catalog_size=len(catalog)))
    cache = {}
    budget_errors = pass_errors = 0
    for run in result['runs']:
        case = cases[run['case']]
        for snapshot in run['snapshots']:
            stack = tuple(map(tuple, snapshot['best_stack']))
            key = run['case'], stack
            if key not in cache:
                d, n = decode(stack)
                if case['kind'] == 'ar':
                    fn = lambda w: power(w, d, n)
                else:
                    td, tn = decode(case['planted_stack'])
                    fn = lambda w: abs(power(w, d, n)-power(w, td, tn))
                ref = curve_extrema(fn, case['windows'])
                V = max(0., ref['max']/case['tolerance']-1)
                cache[key] = dict(case=run['case'], stack=stack, independent=ref,
                                  independent_V=V, reported_dense_V=snapshot['dense_audit']['score'][0])
            expected = snapshot['budget']*len(wl)*2*cfg['max_layers']
            if snapshot['padded_wavelength_layer_updates'] != expected:
                budget_errors += 1
            if bool(cache[key]['independent_V'] <= 1e-12) != snapshot['dense_audit']['pass_sampled']:
                pass_errors += 1
    if oracle_errors:
        issues.append('lookahead independent finite-catalog oracle differs')
    if budget_errors:
        issues.append('lookahead actual padded point×layer budget inconsistency')
    if pass_errors:
        issues.append('lookahead finite-pass classification differs from independent replay')
    return dict(catalog_size=len(catalog), oracle=oracles, unique_snapshot_candidates=list(cache.values()),
                budget_errors=budget_errors, pass_errors=pass_errors, oracle_errors=oracle_errors,
                max_abs_V_replay_difference=max(abs(r['independent_V']-r['reported_dense_V']) for r in cache.values()))


def main():
    start = time.perf_counter()
    initial_fingerprint = package_fingerprint()
    issues = []
    physics = physics_check()
    if max(v for k, v in physics.items() if k != 'random_stacks') > 1e-11:
        issues.append('independent physics regression')
    out = dict(audit_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
               python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
               physics=physics, batched_audit=replay_batched(issues))
    if (ROOT/'phase-guide/results.json').exists():
        out['phase_guide'] = replay_phase(issues)
    if (ROOT/'lookahead/results/results.json').exists():
        out['lookahead'] = replay_lookahead(issues)
    final_fingerprint = package_fingerprint()
    changed = sorted(p for p in set(initial_fingerprint)|set(final_fingerprint)
                     if initial_fingerprint.get(p) != final_fingerprint.get(p))
    if changed:
        issues.append('experiment artifacts changed during replay; rerun after freeze')
    out.update(source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted(ROOT.rglob('*.py')) if '__pycache__' not in str(p)},
               result_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted(ROOT.rglob('*.json')) if p.name in ['results.json', 'scaled_scalar_diagnostic.json', 'withdrawal_and_counterexamples.json']},
               replay_cost=COUNTS, wall_seconds=time.perf_counter()-start, issues=issues,
               frozen_package_sha256=final_fingerprint, artifacts_changed_during_replay=changed,
               scope='Independent scalar recursion; shifted finite grids, endpoints and local numerical extrema. No continuous certification. No replay points fed to search.')
    (ROOT/'independent-replay.json').write_text(json.dumps(out, indent=2, ensure_ascii=False, allow_nan=False))
    print(json.dumps(dict(issues=issues, physics=physics, replay_cost=COUNTS,
                          wall_seconds=out['wall_seconds']), indent=2))


if __name__ == '__main__':
    main()
