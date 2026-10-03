"""One narrow independent units/normalization check; no model edits or heavy run."""
from pathlib import Path
from dataclasses import replace
import datetime
import hashlib
import json
import math
import sys

sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'models'))
import numpy as np
import source_retention as sr

checks = []
def record(name, passed, **evidence):
    checks.append(dict(name=name, passed=bool(passed), **evidence))
def close(a, b, rtol=3e-13, atol=0.0):
    return math.isclose(a, b, rel_tol=rtol, abs_tol=atol)
def rejects(fn):
    try:
        fn()
    except ValueError:
        return True
    return False

# Independently integrate dOmega = dmu dphi. mu=t^2 is only a numerical
# endpoint-smoothing substitution; its Jacobian is 2t.
x, w = np.polynomial.legendre.leggauss(64)
errors = []
for n in (0., .5, 1., 1.7, 10.):
    for c in (-.8, 0., .8):
        terms = []
        for xi, wi in zip(x, w):
            t = (float(xi) + 1.) / 2.
            for j in range(16):
                phi = 2. * math.pi * (j + .5) / 16.
                terms.append(float(wi) / 2. * 2. * t *
                             sr.angular_pdf(t*t, phi, n, c) * 2. * math.pi / 16.)
        errors.append(abs(math.fsum(terms) - 1.))
record('hemisphere_normalization', max(errors) < 1e-10,
       cases=len(errors), max_absolute_error=max(errors), tolerance=1e-10,
       analytic='Integral_phi cos(2phi)=0; (n+1)*Integral_0^1 mu^n dmu=1 for all n>=0')
record('lambert_pdf_and_backface',
       close(sr.angular_pdf(.37, .91, 1., 0.), .37 / math.pi) and
       sr.angular_pdf(-.2, 0., 0.) == 0.,
       note='The n=0 value at exactly mu=0 has zero solid-angle measure')

# Q is kg/s. Source weights are dimensionless fractions of total mass.
# For the following plane geometry: mu_s=H/r, mu_i=0.8H/r.
Q, H = 2e-6, 2.
nodes = [dict(position=[s, 0., 0.], normal=[0., 0., 1.], tangent1=[1., 0., 0.])
         for s in (0., .5)]
weights = (.25, .75)
target = [1., 0., H]
normal = [0., -.6, -.8]
V = (1., .25)
expected = Q / math.pi * math.fsum(wk * vk * .8 * H*H / (H*H + (1.-s)**2)**2
                                  for wk, vk, s in zip(weights, V, (0., .5)))
actual = sr.finite_incident(Q, nodes, weights, target, normal, 1., visible=V)
record('finite_lambert_mass_weights_and_receiver_projection_once', close(actual, expected),
       expected_kg_m2_s=expected, actual_kg_m2_s=actual,
       hand_formula='Q/pi * sum(w_k V_k * 0.8 H^2 / (H^2+(1-s_k)^2)^2)')
expected_iso = Q / (2.*math.pi) * math.fsum(wk * vk * .8 * H / (H*H + (1.-s)**2)**1.5
                                        for wk, vk, s in zip(weights, V, (0., .5)))
actual_iso = sr.finite_incident(Q, nodes, weights, target, normal, 0., visible=V)
record('finite_isotropic_no_extra_emission_cosine', close(actual_iso, expected_iso),
       expected_kg_m2_s=expected_iso, actual_kg_m2_s=actual_iso)
split = sr.finite_incident(Q, [nodes[0], nodes[0], nodes[1]], (.125, .125, .75),
                          target, normal, 1., visible=(1., 1., .25))
scaled_nodes = [dict(nd, position=[2.*v for v in nd['position']]) for nd in nodes]
scaled = sr.finite_incident(Q, scaled_nodes, weights, [2.*v for v in target], normal, 1., visible=V)
record('finite_node_split_and_inverse_square_units', close(split, actual) and close(scaled, actual/4.),
       split_ratio=split/actual, doubled_length_ratio=scaled/actual)
all_visible = sr.finite_incident(Q, nodes, weights, target, normal, 1.)
half_visible = sr.finite_incident(Q, nodes, weights, target, normal, 1., visible=(.5, .5))
record('visibility_once_without_mass_renormalization', close(half_visible, all_visible/2.),
       visibility_half_ratio=half_visible/all_visible)
record('non_normalized_weights_rejected',
       rejects(lambda: sr.normalized_weights((.25, .5))) and
       rejects(lambda: sr.normalized_weights((.25/math.pi, .75/math.pi))))

# Check actual copied bytes before calling through the bridge. No origin or
# remote lookup is needed; the frozen local manifest is the bounded reference.
manifest = json.loads((R/'data/frozen_dependencies.json').read_text())
mismatches = [e['copy'] for e in manifest
              if hashlib.sha256((R/e['copy']).read_bytes()).hexdigest() != e['sha256']]
record('all_frozen_local_dependency_hashes_match', not mismatches,
       files_checked=len(manifest), mismatches=mismatches)

# One tiny event-bearing scene, two source nodes, four panels. Compare entire
# response and upstream dictionaries, not only a convenient scalar field.
scene = sr.t04.Scene()
response = sr.t04.Response(source_scale_kg_s=None)
bridge_nodes, bridge_weights = (0., .0625), (.25, .75)
bridge = sr.bridge_t04(scene, response, (Q, Q), nodes=bridge_nodes,
                       weights=bridge_weights, panels=4)
manual = sr.t04.forward(scene, replace(response, source_scale_kg_s=(Q/math.pi, Q/math.pi)),
                        nodes=bridge_nodes, weights=bridge_weights, panels=4)
upstream = sr.t04.full_forward(scene, nodes=bridge_nodes, weights=bridge_weights,
                              target=1., panels=4)
record('bridge_exactly_one_encoded_Q_over_pi', bridge['t04_response'] == manual,
       stored_scale_kg_s=bridge['t04_response']['response_definition']['source_scale_kg_s'],
       expected_encoded_scale=Q/math.pi)
record('complete_upstream_forward_preserved',
       bridge['t04_response']['upstream_full_forward'] == upstream,
       upstream_keys=sorted(upstream), event_count=len(upstream['event_identities']),
       geometry_status=upstream['geometry_status'], objective_status=upstream['objective_status'])
record('inherited_scope_not_upgraded',
       bridge['point12']=='partial_unchanged' and
       bridge['point2']=='conditional_non_strict_unchanged' and
       not bridge['physical_certification'] and not bridge['t04_response']['physical_certification'])
record('bridge_rejects_duplicate_Q_and_pi',
       rejects(lambda: sr.bridge_t04(scene, sr.t04.Response(), (Q,Q))) and
       rejects(lambda: sr.bridge_t04(replace(scene, amplitude=1./math.pi), response, (Q,Q))) and
       rejects(lambda: sr.bridge_t04(scene, response, (Q,Q), weights=(1./math.pi,))))

# Independent dimensional/absolute bridge oracle: unobstructed moving target,
# q(t)=1, unit retention and fixed density. The whole run is 0.5 seconds.
# Integral H^2/(H^2+y^2)^2 dy = y/[2(H^2+y^2)] + atan(y/H)/(2H).
free = replace(scene, t1=.5, plate_shift_m=3., x0_m=.1, target_shift_m=0.,
               velocity_m_s=.2, clock_offset_s=.1, q0=1., q1_per_s=0.)
free_out = sr.bridge_t04(free, response, (Q,Q), panels=4)['t04_response']
height = free.height_m
primitive = lambda y: y/(2.*(height*height+y*y)) + math.atan(y/height)/(2.*height)
y0 = free.x0_m + free.velocity_m_s*(free.t0+free.clock_offset_s)
y1 = free.x0_m + free.velocity_m_s*(free.t1+free.clock_offset_s)
transfer = (primitive(y1)-primitive(y0))/free.velocity_m_s
height_expected = Q/math.pi*transfer/response.density_kg_m3[0]
height_actual = free_out['height_estimate_m']
record('bridge_absolute_mass_to_thickness_units', close(height_actual, height_expected),
       expected_m=height_expected, actual_m=height_actual,
       hand_formula='(Q_total/pi)[kg/s] * transfer[s/m^2] / rho[kg/m^3] = thickness[m]')

result = dict(
    scope='one_narrow_independent_units_check_only',
    checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    reviewed_model_sha256=hashlib.sha256((R/'models/source_retention.py').read_bytes()).hexdigest(),
    checks=checks, check_count=len(checks), all_passed=all(c['passed'] for c in checks),
    formal_deepseek_seed_sol_review='pending_not_executed',
    literature_expansion=False, heavy_validation=False, remote_control=False,
    network_installation=False, model_edits=False,
    limitation='Normalized finite encoded source only; not a continuum quadrature or physical-material certificate. pi conversion is a floating input, not an outward pi enclosure.')
(R/'reviews/independent_unit_result.json').write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
print(json.dumps(dict(all_passed=result['all_passed'], checks=len(checks),
                     failures=[c['name'] for c in checks if not c['passed']],
                     max_normalization_error=max(errors),
                     actual_thickness_m=height_actual), ensure_ascii=False))
if not result['all_passed']:
    raise SystemExit(1)
