"""One narrow independent unit/scale/sign check; not a full algorithm review."""
from fractions import Fraction as F
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'models'))
import bounded_response as implementation


def manual_objective(h, target):
    return ((h - target) / target) ** 2 / 2


def encode(x):
    return {'exact': str(x), 'decimal': float(x)}


def main():
    # Independent SI exponent bookkeeping: (kg/s)*(s/m^2)/(kg/m^3) = m.
    q_dims = (1, 0, -1)  # kg, m, s
    d_dims = (0, -2, 1)
    rho_dims = (1, -3, 0)
    h_dims = tuple(q + d - rho for q, d, rho in zip(q_dims, d_dims, rho_dims))
    assert h_dims == (0, 1, 0)
    Q, D, rho = F(2, 10**6), F(1), F(2000)
    h = Q * D / rho
    assert h == F(1, 10**9)
    encoded_h = implementation.div(implementation.mul((Q, Q), (D, D)), (rho, rho))
    assert encoded_h == (h, h)

    # Independently chosen exact values, with a nonzero positive target.
    ha, hb, target = F(4, 5), F(11, 10), F(1)
    baseline = (manual_objective(ha, target), manual_objective(hb, target))
    assert baseline == (F(1, 50), F(1, 200))
    common_scales = (F(1, 2), F(2))
    for scale in common_scales:
        correlated = (manual_objective(scale * ha, scale * target),
                      manual_objective(scale * hb, scale * target))
        assert correlated == baseline
        assert implementation.objective((scale * ha, scale * ha), scale * target) == (baseline[0], baseline[0])
        assert implementation.objective((scale * hb, scale * hb), scale * target) == (baseline[1], baseline[1])
    fixed_target = (manual_objective(2 * ha, target), manual_objective(2 * hb, target))
    assert fixed_target == (F(9, 50), F(18, 25))
    assert baseline[1] < baseline[0] and fixed_target[0] < fixed_target[1]
    assert implementation.objective((2 * ha, 2 * ha), target) == (fixed_target[0], fixed_target[0])
    assert implementation.objective((2 * hb, 2 * hb), target) == (fixed_target[1], fixed_target[1])

    erosion = F(3, 10**6)
    signed_mass = Q * D - erosion
    signed_h = signed_mass / rho
    assert signed_mass == -F(1, 10**6)
    assert signed_h == -F(1, 2 * 10**9)
    assert implementation.div((signed_mass, signed_mass), (rho, rho)) == (signed_h, signed_h)
    normalization = {
        'negative': implementation.normalize_positive((2, 2), (-2, -1), F(1, 10**12)),
        'zero': implementation.normalize_positive((2, 2), (0, 0), F(1, 10**12)),
        'crossing': implementation.normalize_positive((2, 2), (-1, 1), F(1, 10**12)),
    }
    assert normalization['negative']['status'] == 'negative_net'
    assert normalization['zero']['status'] == normalization['crossing']['status'] == 'zero_or_crossing'
    assert all(result['value'] is None for result in normalization.values())

    # Three small direct forward calls only, to check the public sign/status gate.
    scene = implementation.Scene()
    responses = {
        'negative': implementation.Response(erosion_mass_kg_m2=(1e-5, 1e-5)),
        'zero': implementation.Response(source_scale_kg_s=(0., 0.)),
        'crossing': implementation.Response(erosion_mass_kg_m2=(0., 3e-6)),
    }
    signed_forward = {}
    for name, response in responses.items():
        result = implementation.forward(scene, response, panels=8)
        signed_forward[name] = {key: result[key] for key in (
            'status', 'net_mass_kg_m2', 'signed_thickness_change_m', 'objective_interval')}
        assert result['objective_interval'] is None
    assert signed_forward['negative']['status'] == 'negative_net'
    assert signed_forward['negative']['signed_thickness_change_m'][1] < 0
    assert signed_forward['zero']['status'] == 'zero_or_crossing_net'
    assert signed_forward['zero']['signed_thickness_change_m'] == [0., 0.]
    crossing = signed_forward['crossing']
    assert crossing['status'] == 'zero_or_crossing_net'
    assert crossing['signed_thickness_change_m'][0] < 0 < crossing['signed_thickness_change_m'][1]

    result = {
        'status': 'passed_narrow_check',
        'checked_at_utc': datetime.now(timezone.utc).isoformat(),
        'reviewer_identity': 'Independent native OpenAI assistant subagent; exact model identifier not exposed to this subagent',
        'review_scope': 'One unit/positive-scale/fixed-target/signed-net check only; not designated external-model review, full algorithm review, literature review, or physical/material certification',
        'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in (ROOT/'models/bounded_response.py', ROOT/'models/run_examples.py')},
        'units': {'basis': ['kg', 'm', 's'], 'h_exponents': h_dims, 'manual_h_m': encode(h)},
        'common_positive_scaling': {'scales': list(map(encode, common_scales)), 'objective_A_B': list(map(encode, baseline)), 'preserved': True,
            'condition': 'The complete signed thickness and the positive target must share the same factor; multiplying deposition alone with fixed nonzero erosion does not meet this premise.'},
        'fixed_target_reversal': {'baseline_better': 'B', 'scaled_better': 'A', 'scaled_objective_A_B': list(map(encode, fixed_target))},
        'manual_signed_case': {'net_mass_kg_m2': encode(signed_mass), 'signed_h_m': encode(signed_h)},
        'normalization': normalization,
        'signed_forward_panels_per_visible_segment': 8,
        'signed_forward': signed_forward,
        'limitations': [
            'The general common-factor identity is algebraic; independent interval boxes for a correlated target were not used.',
            'No material calibration, continuum/source certificate, event/gradient verification, or full examples suite was run.',
            'run_examples.py was read, but its complete examples() function was not executed.',
        ],
    }
    output = ROOT/'reviews/independent_unit_result.json'
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status': result['status'], 'output': str(output), 'signed_statuses': {k: v['status'] for k, v in signed_forward.items()}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
