#!/usr/bin/env python3
"""CPU-bounded deterministic study. Output: synthetic evidence, never validation."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time
from types import SimpleNamespace
import numpy as np
import scipy
from calibration import (FixedGeometry, fit_source, predict_fitted,
                         geometry_from_production_source, validate_actual_input,
                         STUDY, PROJECTS, REFERENCE_PATH, _ref)
from condition_surrogate import QCMConditionGP


def geometry(angles_deg, azimuth_deg=None, *, height_m=.6, configuration_id='synthetic_point_v1', source=None):
    angles = np.deg2rad(np.asarray(angles_deg, float))
    azimuth = np.zeros(len(angles)) if azimuth_deg is None else np.deg2rad(azimuth_deg)
    radius = height_m * np.tan(angles)
    xyz = np.column_stack((radius * np.cos(azimuth), radius * np.sin(azimuth), np.full(len(angles), height_m)))
    if source is None:
        source = _ref.disk_source(0)
    return FixedGeometry(source.nodes_m, source.normals, source.fractions, xyz,
                         np.tile([0., 0., -1.], (len(xyz), 1)),
                         np.full(len(xyz), 1e-4), configuration_id)


def compact_fit(result):
    return {k: v for k, v in result.items() if not k.startswith('profile_') or k in
            ['profile_reference_region', 'profile_open_at_n0', 'profile_open_at_cap', 'profile_note']}


def percent_rms(prediction, truth):
    return float(100 * np.sqrt(np.mean(((prediction - truth) / truth)**2)))


def process_truth(condition):
    power, pressure = condition
    return 2e-6 * power / 100 * (1 + .012 * (pressure - 10)), 1 + .04 * pressure


def run(output_dir, repetitions):
    start = time.perf_counter()
    output_dir.mkdir(parents=True, exist_ok=True)
    train = geometry([8, 30, 55], [0, 120, 240])
    withheld = geometry([0, 18, 40, 65], [0, 45, 165, 280])
    A = 2e-6
    trials = []
    representative = {}
    for n_true in [0., 1., 4.]:
        truth = train.predict(A, n_true)
        truth_withheld = withheld.predict(A, n_true)
        for noise_fraction in [0., .01, .05]:
            for repeat in range(repetitions):
                seed = 20261005 + 10000 * int(n_true) + 100 * int(noise_fraction * 100) + repeat
                rng = np.random.default_rng(seed)
                sd = noise_fraction * truth
                observed = truth + rng.normal(size=len(truth)) * sd
                result = fit_source(train, observed, sd, noise_floor_kg_m2_s=1e-12)
                predicted = predict_fitted(result, withheld, configuration_id=train.configuration_id)
                trials.append({'truth_n': n_true, 'noise_percent': 100 * noise_fraction,
                               'seed': seed, 'A_true_kg_s': A, 'A_fit_kg_s': result['A_kg_s'],
                               'A_error_percent': 100 * (result['A_kg_s'] / A - 1),
                               'n_fit': result['n'], 'n_error': result['n'] - n_true,
                               'train_QCM_rms_error_percent': percent_rms(np.asarray(result['predicted_qcm_mass_flux_kg_m2_s']), truth),
                               'withheld_spatial_rms_error_percent': percent_rms(predicted, truth_withheld),
                               'rank': result['jacobian_rank'], 'condition': result['jacobian_condition'],
                               'boundary': result['boundary_solution'], 'chi2': result['chi2']})
                if repeat == 0:
                    representative[f'n{int(n_true)}_noise{int(noise_fraction * 100)}'] = result
    groups = []
    for n_true in [0., 1., 4.]:
        for noise_percent in [0., 1., 5.]:
            group = [row for row in trials if row['truth_n'] == n_true and row['noise_percent'] == noise_percent]
            metric = np.array([row['withheld_spatial_rms_error_percent'] for row in group])
            groups.append({'truth_n': n_true, 'noise_percent': noise_percent, 'repetitions': len(group),
                           'mean_A_error_percent': float(np.mean([row['A_error_percent'] for row in group])),
                           'mean_n_error': float(np.mean([row['n_error'] for row in group])),
                           'withheld_spatial_rms_error_percent_median': float(np.median(metric)),
                           'withheld_spatial_rms_error_percent_max': float(metric.max()),
                           'full_rank_count': sum(row['rank'] == 2 for row in group),
                           'boundary_count': sum(row['boundary'] for row in group)})
    # Exact same-ring degeneracy: any n can be compensated by A at one angle.
    same_ring = geometry([30] * 6, np.arange(6) * 60)
    ring_truth = same_ring.predict(A, 4)
    ring = fit_source(same_ring, ring_truth, .01 * ring_truth)
    alternatives = []
    for n_alternative in [0., 1., 4., 10., 20.]:
        kernel = same_ring.kernel(n_alternative)
        A_alternative = float(np.mean(ring_truth / kernel))
        alternatives.append({'n': n_alternative, 'A_kg_s': A_alternative,
                             'same_ring_max_relative_residual': float(np.max(np.abs(same_ring.predict(A_alternative, n_alternative) / ring_truth - 1))),
                             'withheld_spatial_rms_error_percent': percent_rms(withheld.predict(A_alternative, n_alternative), withheld.predict(A, 4))})
    blocked_ring = False
    try:
        predict_fitted(ring, withheld, configuration_id=same_ring.configuration_id)
    except ValueError:
        blocked_ring = True
    near_axis = geometry([1, 2, 3])
    near_truth = near_axis.predict(A, 4)
    narrow = fit_source(near_axis, near_truth, .01 * near_truth)
    # Misspecified finite source with only near-axis QCMs: good fit != spatial truth.
    disk_source = _ref.disk_source(.18, nr=12, nphi=48, exponent=4)
    disk_train = geometry([1, 5, 10], height_m=.4, source=disk_source)
    point_train = geometry([1, 5, 10], height_m=.4)
    disk_withheld = geometry([20, 40, 60, 70], height_m=.4, source=disk_source)
    point_withheld = geometry([20, 40, 60, 70], height_m=.4)
    disk_truth = disk_train.predict(A, 4)
    mismatch = fit_source(point_train, disk_truth, .01 * disk_truth)
    mismatch_train_error = percent_rms(np.asarray(mismatch['predicted_qcm_mass_flux_kg_m2_s']), disk_truth)
    mismatch_predictions = point_withheld.predict(mismatch['A_kg_s'], mismatch['n'])
    mismatch_spatial_truth = disk_withheld.predict(A, 4)
    mismatch_withheld_error = percent_rms(mismatch_predictions, mismatch_spatial_truth)
    mismatch_absolute_rmse = float(np.sqrt(np.mean((mismatch_predictions - mismatch_spatial_truth)**2)))
    mismatch_pointwise_percent = 100 * np.abs(mismatch_predictions / mismatch_spatial_truth - 1)
    low_signal_threshold = .05 * np.max(mismatch_spatial_truth)
    above_low_signal = mismatch_spatial_truth >= low_signal_threshold
    # Read-only actual production source geometry adapter, SI-reference round trip.
    settings = SimpleNamespace(source_x_mm=100., source_y_mm=-20., source_z_mm=0.)
    adapted = geometry_from_production_source(settings, {'kind': 'disk', 'radius_mm': 25., 'sampling_order': 9},
                    train.qcm_coords_m, train.qcm_normals, train.qcm_area_m2, 'synthetic_production_geometry_adapter_v1')
    adapter_response = adapted.predict(A, 4)
    adapter_fitted = fit_source(adapted, adapter_response, .01 * adapter_response)
    # Condition holdouts are entire power/pressure conditions, not mixed into train.
    all_conditions = np.array([(P, p) for P in [40, 55, 70, 85, 100] for p in [5, 10, 15, 20, 25]], float)
    holdout_indices = [6, 8, 12, 16, 18]
    train_indices = [i for i in range(len(all_conditions)) if i not in holdout_indices]
    qcm_truth = np.array([train.predict(*process_truth(c)) for c in all_conditions])
    gp_sd = .01 * qcm_truth[train_indices]
    rng = np.random.default_rng(20261105)
    gp_observed = qcm_truth[train_indices] + rng.normal(size=gp_sd.shape) * gp_sd
    gp = QCMConditionGP(all_conditions[train_indices], gp_observed, gp_sd,
                        configuration_id=train.configuration_id)
    gp_mean, gp_latent_sd = gp.predict(all_conditions[holdout_indices], configuration_id=train.configuration_id)
    process_holdouts = []
    for idx, mean, latent_sd in zip(holdout_indices, gp_mean, gp_latent_sd):
        fit = fit_source(train, mean, latent_sd, noise_floor_kg_m2_s=1e-12)
        true_A, true_n = process_truth(all_conditions[idx])
        process_holdouts.append({'condition_W_mTorr': all_conditions[idx].tolist(),
                                  'true_A_kg_s': true_A, 'true_n': true_n,
                                  'fit_A_kg_s': fit['A_kg_s'], 'fit_n': fit['n'],
                                  'QCM_prediction_rms_error_percent': percent_rms(mean, qcm_truth[idx]),
                                  'withheld_spatial_rms_error_percent': percent_rms(withheld.predict(fit['A_kg_s'], fit['n']), withheld.predict(true_A, true_n)),
                                  'GP_latent_sd_kg_m2_s': latent_sd.tolist(),
                                  'jacobian_rank': fit['jacobian_rank']})
    rejected = {}
    for name, condition, configuration in [('outside_power', [110, 15], train.configuration_id),
                                           ('outside_pressure', [70, 30], train.configuration_id),
                                           ('changed_geometry', [70, 15], 'changed_fixture')]:
        try:
            gp.predict(condition, configuration_id=configuration)
            rejected[name] = False
        except ValueError as exc:
            rejected[name] = str(exc)
    actual = json.loads((STUDY / 'data/actual_unknown.json').read_text())
    try:
        validate_actual_input(actual)
        actual_blocker = None
    except ValueError as exc:
        actual_blocker = str(exc)
    # Conditional thickness scale confound demonstration only: A*c/rho.
    confounds = [{'A_kg_s': 2e-6, 'capture_fraction': 1., 'density_kg_m3': 4000.},
                 {'A_kg_s': 4e-6, 'capture_fraction': .5, 'density_kg_m3': 4000.},
                 {'A_kg_s': 4e-6, 'capture_fraction': 1., 'density_kg_m3': 8000.}]
    for row in confounds:
        row['observable_thickness_scale_A_capture_over_density'] = row['A_kg_s'] * row['capture_fraction'] / row['density_kg_m3']
    result = {'evidence_type': 'synthetic numerical study',
              'physical_validation': 'not performed: no real QCM/geometry/density/sticking observations supplied',
              'study_configuration': {'A_truth_kg_s': A, 'n_truth': [0, 1, 4], 'noise_percent': [0, 1, 5],
                                      'repetitions_per_cell': repetitions, 'seed_formula': '20261005 + 10000*n_true + 100*noise_percent + repeat',
                                      'noise_model': 'independent Gaussian absolute flux sd = noise_fraction * noiseless QCM flux',
                                      'absolute_noise_floor_kg_m2_s': 1e-12,
                                      'train_geometry': train.contract(), 'withheld_spatial_geometry': withheld.contract()},
              'recovery_summary': groups,
              'identifiability': {'same_ring': compact_fit(ring), 'same_ring_map_blocked': blocked_ring,
                                  'same_ring_alternative_solutions': alternatives,
                                  'near_axis': compact_fit(narrow)},
              'finite_source_mismatch': {'truth_radius_m': .18, 'truth_height_m': .4, 'truth_n': 4,
                                        'model': 'misspecified point source', 'fitted': compact_fit(mismatch),
                                        'train_QCM_rms_error_percent': mismatch_train_error,
                                        'withheld_spatial_rms_error_percent': mismatch_withheld_error,
                                        'withheld_spatial_truth_kg_m2_s': mismatch_spatial_truth.tolist(),
                                        'withheld_spatial_prediction_kg_m2_s': mismatch_predictions.tolist(),
                                        'withheld_absolute_rmse_kg_m2_s': mismatch_absolute_rmse,
                                        'withheld_rmse_over_mean_truth_percent': float(100 * mismatch_absolute_rmse / np.mean(mismatch_spatial_truth)),
                                        'withheld_rmse_over_peak_truth_percent': float(100 * mismatch_absolute_rmse / np.max(mismatch_spatial_truth)),
                                        'withheld_coords_m': disk_withheld.qcm_coords_m.tolist(),
                                        'withheld_angles_deg': [20, 40, 60, 70],
                                        'pointwise_absolute_error_percent': mismatch_pointwise_percent.tolist(),
                                        'error_percentiles_50_90_100': np.percentile(mismatch_pointwise_percent, [50, 90, 100]).tolist(),
                                        'low_signal_threshold_fraction_of_peak': .05,
                                        'low_signal_threshold_kg_m2_s': float(low_signal_threshold),
                                        'retained_above_threshold_count': int(np.sum(above_low_signal)),
                                        'above_threshold_relative_rms_error_percent': percent_rms(mismatch_predictions[above_low_signal], mismatch_spatial_truth[above_low_signal]),
                                        'low_signal_note': '5% of peak is a disclosed exploratory reporting diagnostic, not preregistered physical acceptance or a production threshold',
                                        'metric_note': 'pointwise relative RMS is sensitive to small high-angle truth values; absolute and mean-normalized errors also reported',
                                        'status': 'counterexample, not finite-source validation'},
              'production_geometry_adapter': {'source_interface': 'coat_sim.core.source_profiles.source_samples',
                                               'source_nodes_count': len(adapted.source_fractions),
                                               'A_recovered_kg_s': adapter_fitted['A_kg_s'], 'n_recovered': adapter_fitted['n'],
                                               'geometry_units': 'installed mm coordinates converted to SI m',
                                               'kernel_interface': str(REFERENCE_PATH.relative_to(PROJECTS.parent)),
                                               'production_normalization_used': False,
                                               'status': 'geometry adapter integration check only'},
              'condition_surrogate': {'model': 'fixed RBF GP, independent QCM outputs, no acquisition or hyperparameter optimization',
                                      'training_count': len(train_indices), 'withheld_condition_count': len(holdout_indices),
                                      'training_conditions_W_mTorr': all_conditions[train_indices].tolist(),
                                      'withheld_results': process_holdouts, 'rejection_checks': rejected,
                                      'uncertainty_scope': 'conditional latent GP std only; no model discrepancy, cross-QCM covariance, geometry or batch uncertainty'},
              'density_sticking_confound': confounds,
              'actual_input_blocker': actual_blocker,
              'unrun': ['real QCM experiment', 'finite-area QCM convergence', 'geometry calibration',
                        'finite-source planetary dual-mask physical validation', 'GP active learning and hyperparameter calibration',
                        'requested DeepSeek/Seed/Sol model-specific review chain'],
              'environment': {'python': sys.version, 'numpy': np.__version__, 'scipy': scipy.__version__,
                              'platform': platform.platform(), 'hostname': platform.node(),
                              'CPU_threads_requested': 1, 'GPU_used': False,
                              'elapsed_seconds': time.perf_counter() - start}}
    (output_dir / 'study_results.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    (output_dir / 'representative_profiles.json').write_text(json.dumps(representative, indent=2, allow_nan=False) + '\n')
    with (output_dir / 'recovery_trials.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(trials[0]))
        writer.writeheader(); writer.writerows(trials)
    (output_dir / 'synthetic_input_contract.json').write_text(json.dumps({**train.contract(),
             'reading_type': 'areal_mass_flux', 'mass_flux_kg_m2_s': train.predict(A, 4).tolist(),
             'sd_kg_m2_s': (.01 * train.predict(A, 4)).tolist(), 'noise_floor_kg_m2_s': 1e-12,
             'data_origin': 'synthetic'}, indent=2) + '\n')
    # Verify immutable external runtime sources without rewriting baseline.
    baseline = json.loads((STUDY / 'results/runtime_sources_before.json').read_text())
    changes = [path for path, digest in baseline.items()
               if not (PROJECTS.parent / path).is_file() or hashlib.sha256((PROJECTS.parent / path).read_bytes()).hexdigest() != digest]
    source_check = {'checked_file_count': len(baseline), 'unchanged': not changes,
                    'changes': changes, 'baseline_preserved': True}
    (output_dir / 'runtime_source_check.json').write_text(json.dumps(source_check, indent=2) + '\n')
    if changes:
        raise RuntimeError('External source hash change detected: ' + ', '.join(changes))
    # Durable readback checks, not just reliance on in-memory objects.
    readback = json.loads((output_dir / 'study_results.json').read_text())
    assert readback['physical_validation'].startswith('not performed')
    assert readback['identifiability']['same_ring_map_blocked']
    assert readback['actual_input_blocker'] is not None
    print(json.dumps({'output': str(output_dir), 'trials': len(trials),
                      'same_ring_rank': ring['jacobian_rank'], 'near_axis_condition': narrow['jacobian_condition'],
                      'mismatch_train_percent': mismatch_train_error, 'mismatch_withheld_percent': mismatch_withheld_error,
                      'runtime_sources_unchanged': not changes, 'elapsed_seconds': result['environment']['elapsed_seconds']}, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, default=STUDY / 'results')
    parser.add_argument('--repetitions', type=int, default=20)
    args = parser.parse_args()
    if not 1 <= args.repetitions <= 100:
        parser.error('repetitions must be 1..100; no silent large workloads')
    run(args.output_dir.resolve(), args.repetitions)
