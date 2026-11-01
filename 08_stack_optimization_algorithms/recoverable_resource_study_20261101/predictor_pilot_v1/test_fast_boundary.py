"""Contract checks for the online predictor; no training or optimizer run.

Run: PYTHONPATH=/path/to/pinned/coating-sim:$PYTHONPATH \
  python -m unittest -v test_fast_boundary
Fixtures are previously frozen, real research-pilot requests, not validation labels.
"""
from copy import deepcopy
import ast
import json
import math
import hashlib
import tempfile
from pathlib import Path
import sys
import os

import unittest
from functools import wraps
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if os.environ.get('COATING_CORE_REPOSITORY'):
    sys.path.insert(0, os.environ['COATING_CORE_REPOSITORY'])
sys.path.insert(0, str(HERE))

import features
import predictor


def fixture_request():
    return json.loads((ROOT / 'pilot_v4a/cases/train-41000-hr/input.json').read_text())['request']


def vector(request):
    result = features.extract_features(request)
    assert isinstance(result, dict)
    assert set(('values', 'names', 'reference_wavelength_nm', 'conditional_on_unknown_k')) <= result.keys()
    assert isinstance(result['values'], list)
    assert isinstance(result['names'], list)
    assert len(result['values']) == len(result['names']) > 0
    assert len(set(result['names'])) == len(result['names'])
    assert all(isinstance(x, (int, float)) and math.isfinite(x) for x in result['values'])
    assert math.isfinite(result['reference_wavelength_nm']) and result['reference_wavelength_nm'] > 0
    assert isinstance(result['conditional_on_unknown_k'], bool)
    return result




def parametrize(names, cases):
    keys = tuple(x.strip() for x in (names.split(',') if isinstance(names, str) else names))
    def decorate(fn):
        @wraps(fn)
        def run(self):
            for case in cases:
                args = case if isinstance(case, tuple) else (case,)
                with self.subTest(**dict(zip(keys, args))):
                    fn(self, *args)
        return run
    return decorate


class MonkeyPatch:
    def __init__(self, test):
        self.test = test
    def setattr(self, obj, name, value):
        p = patch.object(obj, name, value)
        p.start()
        self.test.addCleanup(p.stop)


def simple_model():
    f = vector(fixture_request())
    return dict(schema='joint-resource-forest-v1', feature_schema='resource-features-v1',
                feature_names=f['names'], feature_min=[-1e6]*len(f['names']),
                feature_max=[1e6]*len(f['names']),
                trees=[dict(left=[-1], right=[-1], feature=[-2], threshold=[-2.0],
                            value=[[math.log1p(8.25), math.log1p(0.5)]])])



class FastBoundaryTests(unittest.TestCase):
    def test_input_is_not_mutated(self):
        request = fixture_request()
        before = deepcopy(request)
        vector(request)
        assert request == before


    def test_case_metadata_and_labels_do_not_change_features(self):
        base = fixture_request()
        other = deepcopy(base)
        other.update(case_id='leak-check-id', family='leak-check-family', result={'layers': 999999},
                     native_seed_bundle={'leak': [987654321]}, seed=987654321, search_seed=123456)
        assert vector(other) == vector(base)


    def test_display_names_and_order_are_not_features(self):
        base = fixture_request()
        other = deepcopy(base)
        other['environment'].update(id='renamed-design', name='renamed display', note='different note')
        snap = other['frozen_material_snapshot']
        snap['design'].update(id='renamed-design', name='renamed display', note='different note')
        for row in snap['materials']:
            row['name'] = 'arbitrary display name'
            row['notes'] = 'different notes'
            for optical in row['optical_sets']:
                optical['name'] = 'arbitrary optical set display'
        assert vector(other) == vector(base)
        for kind in ('candidate_pool', 'material_records'):
            with self.subTest(permutation=kind):
                changed = deepcopy(base)
                if kind == 'candidate_pool':
                    changed['candidate_materials'].reverse()
                else:
                    changed['frozen_material_snapshot']['materials'].reverse()
                assert vector(changed) == vector(base)


    def test_known_k_changes_features(self):
        base = fixture_request()
        other = deepcopy(base)
        film_id = other['candidate_materials'][0]['material_id']
        film = next(r for r in other['frozen_material_snapshot']['materials'] if r['id'] == film_id)
        optical = film['optical_sets'][0]
        optical['k'] = [x + 0.02 for x in optical['k']]
        assert not vector(base)['conditional_on_unknown_k']
        assert vector(other)['values'] != vector(base)['values']


    def test_unknown_k_requires_explicit_lossless_assumption_and_is_reported(self):
        request = fixture_request()
        film_id = request['candidate_materials'][0]['material_id']
        film = next(r for r in request['frozen_material_snapshot']['materials'] if r['id'] == film_id)
        film['optical_sets'][0].pop('k', None)
        film['optical_sets'][0].pop('k_data', None)
        request['environment']['assume_lossless'] = False
        with self.assertRaises((ValueError, TypeError)):
            vector(request)
        request['environment']['assume_lossless'] = True
        assert vector(request)['conditional_on_unknown_k'] is True


    def test_substrate_optical_change_is_visible(self):
        base = fixture_request()
        other = deepcopy(base)
        substrate_id = other['environment']['substrate']['material_id']
        substrate = next(r for r in other['frozen_material_snapshot']['materials'] if r['id'] == substrate_id)
        optical = substrate['optical_sets'][0]
        optical['n'] = [x + 0.2 for x in optical['n']]
        assert vector(other)['values'] != vector(base)['values']


    @parametrize('mutation', ['point_vs_mean', 'angle', 'strict_lower', 'strict_upper'])
    def test_objective_semantics_are_retained(self, mutation):
        base = fixture_request()
        other = deepcopy(base)
        obj = other['objectives'][0]
        if mutation == 'point_vs_mean':
            obj['mean'] = deepcopy(obj['pointwise'])
            obj['pointwise']['enabled'] = False
        elif mutation == 'angle':
            obj['angles_deg'] = [0.0, 30.0, 50.0]
        elif mutation == 'strict_lower':
            obj['pointwise']['strict_lower'] = not obj['pointwise']['strict_lower']
        elif mutation == 'strict_upper':
            # Set an actual upper bound first, then toggle the corresponding flag.
            base['objectives'][0]['pointwise']['upper_bound'] = 0.98
            obj['pointwise']['upper_bound'] = 0.98
            obj['pointwise']['strict_upper'] = not obj['pointwise']['strict_upper']
        assert vector(other)['values'] != vector(base)['values']


    @parametrize(('key', 'value'), [
        ('max_layers', 12),
        ('max_total_thickness_nm', 500.0),
        ('max_layer_thickness_nm', 100.0),
        ('minimum_nonzero_thickness_nm', 2.0),
    ])
    def test_unsupported_design_constraints_rejected_not_silently_ignored(self, key, value):
        request = fixture_request()
        request[key] = value
        with self.assertRaises((ValueError, NotImplementedError)):
            features.extract_features(request)


    def test_online_modules_do_not_directly_call_search_audit_or_forward_solvers(self):
        # Inspect calls, not imports: optical-sampling helpers may import broader core
        # modules without executing their search/forward routines.
        forbidden = {'optimize_film_design', 'synthesize_film_design', 'estimate_film_resources',
                     'audit_candidate', 'calculate_spectrum', 'simulate_spectrum', 'tmm',
                     'coherent_rta', 'incoherent_plate_rta'}
        for path in (HERE / 'features.py', HERE / 'predictor.py'):
            tree = ast.parse(path.read_text(), filename=str(path))
            calls = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
                    if name in forbidden:
                        calls.append((node.lineno, name))
            assert not calls, f'{path.name} contains online calls to forbidden routines: {calls}'


    def test_feature_extraction_does_not_execute_core_search_or_audit(self):
        monkeypatch = MonkeyPatch(self)
        from coat_sim.core import film_auto_synthesis, film_optimization, film_resource_estimation, film_optics
        def forbidden(*args, **kwargs):
            raise AssertionError('online feature path executed search, optimizer, or audit')
        monkeypatch.setattr(film_auto_synthesis, 'synthesize_film_design', forbidden)
        monkeypatch.setattr(film_optimization, 'optimize_film_design', forbidden)
        monkeypatch.setattr(film_resource_estimation, 'estimate_film_resources', forbidden)
        monkeypatch.setattr(film_optics, 'coherent_rta', forbidden)
        monkeypatch.setattr(film_optics, 'incoherent_plate_rta', forbidden)
        vector(fixture_request())


    def test_predict_transforms_and_does_not_claim_calibration(self):
        request = fixture_request()
        before = deepcopy(request)
        model = simple_model()
        before_model = deepcopy(model)
        result = predictor.predict(model, request)
        assert result['state'] == 'research_uncalibrated'
        assert result['interval'] is None
        assert result['estimated_layers'] == 9
        self.assertAlmostEqual(result['estimated_layers_float'], 8.25)
        self.assertAlmostEqual(result['estimated_total_thickness_nm'], 0.5 * vector(request)['reference_wavelength_nm'])
        assert request == before and model == before_model
        assert result['feature_envelope_pass'] is True
        assert 'not' in result['warning'].lower()


    def test_envelope_extrapolation_is_warning_not_a_guarantee(self):
        model = simple_model()
        model['feature_min'][0] = 1e5
        result = predictor.predict(model, fixture_request())
        assert result['feature_envelope_pass'] is False
        assert 0 in result['outside_training_feature_indices']
        assert result['interval'] is None


    def test_predict_features_uses_float32_tree_threshold_and_averages_trees(self):
        model = simple_model()
        model['feature_names'] = ['one']
        model['trees'] = [dict(left=[1, -1, -1], right=[2, -1, -1], feature=[0, -2, -2],
                               threshold=[1.0, -2, -2], value=[[0, 0], [1, 2], [3, 4]]),
                          dict(left=[-1], right=[-1], feature=[-2], threshold=[-2], value=[[3, 4]])]
        assert predictor.predict_features(model, [1.0 + 1e-9]) == [2.0, 3.0]
        assert predictor.predict_features(model, [1.01]) == [3.0, 4.0]


    @parametrize('damage', [
        'unknown_schema', 'bad_feature_schema', 'empty_forest', 'too_many_trees',
        'mismatched_arrays', 'bad_leaf_shape', 'nonfinite_leaf', 'invalid_child',
        'invalid_feature', 'nonfinite_threshold', 'cycle', 'invalid_vector',
    ])
    def test_invalid_serialized_forest_is_rejected_without_search(self, damage):
        model = simple_model()
        values = [0.0] * len(model['feature_names'])
        tree = model['trees'][0]
        if damage == 'unknown_schema': model['schema'] = 'unexpected'
        elif damage == 'bad_feature_schema': model['feature_schema'] = 'unexpected'
        elif damage == 'empty_forest': model['trees'] = []
        elif damage == 'too_many_trees': model['trees'] *= 257
        elif damage == 'mismatched_arrays': tree['right'] = []
        elif damage == 'bad_leaf_shape': tree['value'] = [[1]]
        elif damage == 'nonfinite_leaf': tree['value'] = [[float('nan'), 0]]
        elif damage in ('invalid_child', 'invalid_feature', 'nonfinite_threshold', 'cycle'):
            tree.update(left=[0], right=[0], feature=[0], threshold=[0.0], value=[[0, 0]])
            if damage == 'invalid_child': tree['left'] = [1]
            elif damage == 'invalid_feature': tree['feature'] = [len(values)]
            elif damage == 'nonfinite_threshold': tree['threshold'] = [float('nan')]
        elif damage == 'invalid_vector': values[0] = float('inf')
        with self.assertRaises((ValueError, TypeError, KeyError)):
            predictor.predict_features(model, values)


    def test_predict_rejects_mismatched_feature_names_and_invalid_envelope(self):
        model = simple_model()
        model['feature_names'][0] = 'not-the-feature'
        with self.assertRaises(ValueError): predictor.predict(model, fixture_request())
        model = simple_model()
        model['feature_min'][0] = float('nan')
        with self.assertRaises(ValueError): predictor.predict(model, fixture_request())


    def test_acceptance_tolerance_is_explicit_and_invalid_values_rejected(self):
        base = fixture_request()
        other = deepcopy(base)
        other['acceptable_normalized_error'] = 0.2
        a, b = vector(base), vector(other)
        assert a['values'] != b['values']
        assert a['names'] == b['names']
        for invalid in (-0.1, float('nan'), float('inf'), 1.1):
            other['acceptable_normalized_error'] = invalid
            with self.assertRaises((ValueError, TypeError)):
                features.extract_features(other)


    def test_predict_does_not_execute_core_search_or_forward(self):
        monkeypatch = MonkeyPatch(self)
        from coat_sim.core import film_auto_synthesis, film_optimization, film_resource_estimation, film_optics
        model = simple_model()
        def forbidden(*args, **kwargs):
            raise AssertionError('online prediction executed search, optimizer, audit, or TMM')
        monkeypatch.setattr(film_auto_synthesis, 'synthesize_film_design', forbidden)
        monkeypatch.setattr(film_optimization, 'optimize_film_design', forbidden)
        monkeypatch.setattr(film_resource_estimation, 'estimate_film_resources', forbidden)
        monkeypatch.setattr(film_optics, 'coherent_rta', forbidden)
        monkeypatch.setattr(film_optics, 'incoherent_plate_rta', forbidden)
        assert predictor.predict(model, fixture_request())['state'] == 'research_uncalibrated'


    def test_validate_model_rejects_unvisited_corruption_cycle_and_orphans(self):
        model = simple_model()
        tree = dict(left=[1, -1, -1], right=[2, -1, -1], feature=[0, -2, -2],
                    threshold=[0.0, -2.0, -2.0], value=[[0, 0], [1, 2], [3, 4]])
        model['trees'] = [tree]
        self.assertIs(predictor.validate_model(model), model)
        values = [-1.0] * len(model['feature_names'])
        for damage in ('unvisited_nan', 'unvisited_cycle', 'orphan'):
            with self.subTest(damage=damage):
                bad = deepcopy(model)
                t = bad['trees'][0]
                if damage == 'unvisited_nan':
                    t['value'][2][0] = float('nan')
                elif damage == 'unvisited_cycle':
                    t['left'][2] = 2
                    t['right'][2] = 1
                    t['feature'][2] = 0
                else:
                    for key, value in [('left', -1), ('right', -1), ('feature', -2),
                                       ('threshold', -2.0), ('value', [5, 6])]:
                        t[key].append(value)
                # The queried left leaf stays valid, demonstrating this case
                # cannot be found by checking only the prediction path.
                self.assertEqual(predictor.predict_features(bad, values), [1.0, 2.0])
                with self.assertRaises(ValueError):
                    predictor.validate_model(bad)

    def test_load_model_verifies_sha256_then_validates_entire_graph(self):
        model = simple_model()
        raw = json.dumps(model, sort_keys=True, separators=(',', ':')).encode('utf-8')
        digest = hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'model.json'
            path.write_bytes(raw)
            self.assertEqual(predictor.load_model(path, digest), model)
            path.write_bytes(raw + b' ')
            with self.assertRaises(ValueError):
                predictor.load_model(path, digest)
            bad = deepcopy(model)
            bad['trees'][0]['value'][0][1] = float('nan')
            bad_raw = json.dumps(bad).encode('utf-8')
            path.write_bytes(bad_raw)
            with self.assertRaises(ValueError):
                predictor.load_model(path, hashlib.sha256(bad_raw).hexdigest())


    def test_double_threshold_is_not_rounded_to_float32(self):
        model = simple_model()
        model['trees'] = [dict(left=[1,-1,-1],right=[2,-1,-1],feature=[0,-2,-2],
            threshold=[0.9999999999,-2.,-2.],value=[[0.,0.],[1.,2.],[3.,4.]])]
        values = [0.] * len(model['feature_names'])
        values[0] = 1.
        self.assertEqual(predictor.predict_features(model, values), [3.,4.])

    def test_equal_window_sort_ignores_metadata_and_objective_order(self):
        request = fixture_request()
        a = deepcopy(request['objectives'][0])
        b = deepcopy(a)
        a['polarization'], b['polarization'] = 's', 'p'
        request['objectives'] = [a,b]
        expected = vector(request)['values']
        a['aaa_identity'], b['aaa_identity'] = 'zzz', 'aaa'
        a['family'], b['case_id'] = 'other family', 'secret label'
        self.assertEqual(vector(request)['values'], expected)
        request['objectives'].reverse()
        self.assertEqual(vector(request)['values'], expected)

    def test_unmodeled_reference_and_geometry_changes_are_rejected(self):
        changes = [('objective_samples', 33), ('substrate_mode', 'coherent'),
            ('substrate_thickness', 2.), ('exit_index', 1.5), ('seed_designs', [{}]),
            ('max_cycles', 8), ('max_evaluations', 600), ('max_seconds', 15.)]
        for key, value in changes:
            with self.subTest(key=key):
                r = fixture_request()
                if key == 'objective_samples': r['objectives'][0]['wavelength_samples'] = value
                elif key == 'substrate_mode': r['environment']['substrate']['mode'] = value
                elif key == 'substrate_thickness': r['environment']['substrate']['thickness']['value'] = value
                elif key == 'exit_index': r['environment']['exit_medium']['n'] = value
                else: r[key] = value
                with self.assertRaises(ValueError): vector(r)


if __name__ == "__main__":
    unittest.main()
