"""One bounded independent pass: 12 tiny checks, no driver or frozen-source reads.
Only the two authorized model modules and the synthetic contract are loaded.
Frozen imports are inert stubs: no mask/rigid implementation is exercised.
Run with PYTHONDONTWRITEBYTECODE=1. This never launches the high-cost driver.
"""
import sys, types, json, math, importlib.util, hashlib
from pathlib import Path
from dataclasses import replace
from fractions import Fraction
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
# Do not import/read the separately maintained frozen implementation.
frozen = types.ModuleType('frozen'); frozen.__path__ = []
mask = types.ModuleType('frozen.robust_mask_v02')
mask.RectangleMask = object; mask.Verdict = object
pose = types.ModuleType('frozen.t01_pose_reference'); pose.rigid_jacobians = None
sys.modules.update({'frozen': frozen, 'frozen.robust_mask_v02': mask,
                    'frozen.t01_pose_reference': pose})
def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module; spec.loader.exec_module(module)
    return module
E = load('event_reference', 'models/event_reference.py')
O = load('analytic_oracle', 'models/analytic_oracle.py')
contract = json.loads((ROOT / 'data/synthetic_contract.json').read_text())
S = E.Scene(**contract['scene'])
results = []

def record(name, fn):
    try:
        evidence = fn()
        results.append({'name': name, 'passed': True, 'evidence': evidence})
    except Exception as exc:
        results.append({'name': name, 'passed': False,
                        'exception_type': type(exc).__name__, 'evidence': str(exc)})
def close(actual, expected, tol=1e-9):
    if abs(actual-expected) > tol * max(1., abs(expected)):
        raise AssertionError(f'actual={actual!r}, expected={expected!r}, tolerance={tol}')
def rejects(sc):
    try: O.exact_value_gradient(sc)
    except ValueError as exc: return str(exc)
    raise AssertionError('analytic oracle emitted a gradient for an unresolved case')
def withheld(sc):
    r = E.evaluate(0., sc)
    assert r['gradient'] is None and r['smooth_gradient'] is None and r['event_gradient'] is None, r
    return r['sensitivity_status']

def projections():
    evidence = []
    for s in (Fraction(0), Fraction(3,10), Fraction(-3,10)):
        H = Fraction(1); a = Fraction(2,25); near = Fraction(2,5); far = Fraction(3,5)
        # The ray intersects the slab iff its projected target coordinate lies
        # in the connected union of intervals over all slab depths.
        low = min(s+(-a-s)*H/z for z in (near,far))
        high = max(s+(a-s)*H/z for z in (near,far))
        actual_low, actual_high, tie = E.shadow_limits(float(s), S)
        close(actual_low[0], float(low), 1e-14); close(actual_high[0], float(high), 1e-14)
        assert not tie
        evidence.append({'source_x_m': str(s), 'expected_exact': [str(low),str(high)],
                         'actual': [actual_low[0],actual_high[0]],
                         'active_depths_m': [actual_low[2],actual_high[2]]})
    return evidence

def own_projection(sc, source=0.):
    s=source+sc.source_shift_m
    ll=[(s+(sc.plate_shift_m-sc.half_width_m-s)*sc.height_m/z,z) for z in (sc.z_near_m,sc.z_far_m)]
    uu=[(s+(sc.plate_shift_m+sc.half_width_m-s)*sc.height_m/z,z) for z in (sc.z_near_m,sc.z_far_m)]
    return min(ll),max(uu)

def own_kernel(t,sc,source=0.):
    y=sc.x0_m+sc.target_shift_m+sc.velocity_m_s*(t+sc.clock_offset_s)-source-sc.source_shift_m
    return sc.amplitude*(sc.q0+sc.q1_per_s*t)*sc.height_m**2/(sc.height_m**2+y*y)**2

def event_sign(sc):
    limits=own_projection(sc); v=sc.velocity_m_s; s=sc.source_shift_m; H=sc.height_m
    expected=[0.]*7; entries=[]
    for side,(boundary,z) in zip((-1,1),limits):
        t=(boundary-sc.x0_m-sc.target_shift_m)/v-sc.clock_offset_s
        sign_jump=side*(1 if v>0 else -1)
        edge=sc.plate_shift_m+side*sc.half_width_m
        time_derivative=[-1/v,(1-H/z)/v,-1.,0.,H/z/v,side*H/z/v,(edge-s)/z/v]
        if sc.t0<t<sc.t1:
            for j in range(7): expected[j]-=sign_jump*own_kernel(t,sc)*time_derivative[j]
        entries.append({'t':t,'jump':sign_jump})
    entries.sort(key=lambda x:x['t'])
    assert [x['jump'] for x in entries]==[-1,1]
    actual=E.evaluate(0.,sc)
    for x,y in zip(actual['event_gradient'],expected): close(x,y,1e-12)
    assert expected[5]<0, 'increasing width must reduce visibility in this fixture'
    return {'velocity_m_s':v,'ordered_events':entries,'expected_event_gradient':expected,
            'actual_event_gradient':actual['event_gradient']}

def own_value(sc):
    # Integrate in the spatial variable y. These scalar expressions do not use
    # event_reference primitive/integral, its Jacobian, or Dual arithmetic.
    v=sc.velocity_m_s; H=sc.height_m
    d=sc.x0_m+sc.target_shift_m+v*sc.clock_offset_s-sc.source_shift_m
    def antiderivative(y):
        angular=math.atan2(y,H)/(2*H)
        rational=y/(2*(H*H+y*y))
        first_moment=-H*H/(2*(H*H+y*y))
        return sc.amplitude*((sc.q0-sc.q1_per_s*d/v)*(angular+rational)+sc.q1_per_s/v*first_moment)/v
    def segment(a,b):
        return 0. if b<=a else antiderivative(v*b+d)-antiderivative(v*a+d)
    boundaries=own_projection(sc)
    times=sorted((b-sc.x0_m-sc.target_shift_m)/v-sc.clock_offset_s for b,z in boundaries)
    return segment(sc.t0,sc.t1)-segment(max(sc.t0,times[0]),min(sc.t1,times[1]))

def full_gradients():
    evidence=[]
    for sc in (S,replace(S,velocity_m_s=-.4,x0_m=.4)):
        r=E.evaluate(0.,sc); oracle_v, oracle_g=O.exact_value_gradient(sc)
        expected=own_value(sc); close(r['value_s_m2'],expected,1e-12); close(oracle_v,expected,1e-12)
        fd=[]
        for p in E.PARAMETERS:
            h=1e-5
            # Fourth-order centered difference of independently integrated values.
            vals=[own_value(replace(sc,**{p:getattr(sc,p)+k*h})) for k in (-2,-1,1,2)]
            fd.append((vals[0]-8*vals[1]+8*vals[2]-vals[3])/(12*h))
        for actual,want in zip(r['gradient'],fd): close(actual,want,2e-8)
        for actual,want in zip(oracle_g,fd): close(float(actual),want,2e-8)
        evidence.append({'velocity_m_s':sc.velocity_m_s,'value':expected,
                         'independent_gradient':fd,'reference_gradient':r['gradient'],
                         'oracle_gradient':[float(x) for x in oracle_g]})
    return evidence

def stationary():
    sc=replace(S,velocity_m_s=0.)
    return {'reference':withheld(sc),'oracle_rejection':rejects(sc)}
def grazing():
    r=E.grazing_duration(0.)
    assert r['derivative'] is None and r['status']=='grazing_topology_unresolved',r
    return r

def endpoint(near=False):
    # Set the lower crossing at t0 (or half the endpoint guard after t0).
    lower=-.2
    x0=lower-S.target_shift_m
    if near:x0-=S.velocity_m_s*S.event_guard_s/2
    sc=replace(S,x0_m=x0)
    status=withheld(sc); assert status=='endpoint_event_unresolved',status
    return {'changes':{'x0_m':x0},'reference':status,'oracle_rejection':rejects(sc),
            'first_event_s':E.event_map(0.,sc)['events'][0]['time_s']}
def face_tie():
    sc=replace(S,source_shift_m=.08)
    return {'reference':withheld(sc),'oracle_rejection':rejects(sc)}
def unknown():
    sc=replace(S,shadow_boundary_uncertainty_m=1e-4)
    status=withheld(sc); assert status=='geometry_unknown'
    return {'reference':status,'oracle_rejection':rejects(sc)}
def clock_translation():
    delta=.13
    a=E.evaluate(0.,replace(S,clock_offset_s=delta))
    b=E.evaluate(0.,replace(S,target_shift_m=S.target_shift_m+S.velocity_m_s*delta))
    close(a['value_s_m2'],b['value_s_m2'],1e-14)
    close(a['gradient'][2],S.velocity_m_s*a['gradient'][0],1e-13)
    assert len(a['events'])==len(b['events'])
    for x,y in zip(a['events'],b['events']): close(x['time_s'],y['time_s'],1e-14)
    return {'clock_offset_s':delta,'equivalent_target_shift_m':S.target_shift_m+S.velocity_m_s*delta,
            'values':[a['value_s_m2'],b['value_s_m2']],
            'gradient_clock':a['gradient'][2],'v_times_gradient_translation':S.velocity_m_s*a['gradient'][0],
            'interpretation':'These two parameter columns are exactly dependent for the stated reference-clock source law.'}
def close_events():
    sc=replace(S,half_width_m=1e-11)
    reference=E.evaluate(0.,sc)
    assert reference['sensitivity_status']=='event_order_unresolved' and reference['gradient'] is None,reference
    try:
        v,g=O.exact_value_gradient(sc)
    except ValueError as exc:
        return {'reference_status':reference['sensitivity_status'],'oracle_rejection':str(exc)}
    evidence={'changes':{'half_width_m':1e-11},'reference_status':reference['sensitivity_status'],
              'reference_gradient':reference['gradient'],
              'event_times_s':[e['time_s'] for e in reference['events']],
              'separation_s':reference['events'][1]['time_s']-reference['events'][0]['time_s'],
              'required_separation_s':2*sc.event_guard_s,
              'oracle_value':v,'oracle_gradient':[float(x) for x in g]}
    raise AssertionError(json.dumps(evidence,sort_keys=True))

record('finite_thickness_projection_three_source_positions',projections)
record('event_sign_positive_velocity',lambda:event_sign(S))
record('event_sign_negative_velocity',lambda:event_sign(replace(S,velocity_m_s=-.4,x0_m=.4)))
record('independent_value_and_parameter_gradients_both_velocities',full_gradients)
record('stationary_gradient_withheld',stationary)
record('grazing_gradient_withheld',grazing)
record('exact_endpoint_gradient_withheld',endpoint)
record('near_endpoint_gradient_withheld',lambda:endpoint(True))
record('active_face_tie_gradient_withheld',face_tie)
record('unknown_geometry_gradient_withheld',unknown)
record('clock_translation_confounded',clock_translation)
record('close_event_order_gradient_withheld_by_oracle',close_events)
report={'run_kind':'single_initial_independent_pass',
        'authorized_source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in
            ('models/event_reference.py','models/analytic_oracle.py','data/synthetic_contract.json')},
        'constraints':{'top_level_checks':12,'external_research':False,'driver_run':False,
            'frozen_dependencies':'inert stubs; source not read and behavior not tested',
            'formal_DeepSeek_Seed_Sol_chain':'pending; this pass does not substitute for it'},
        'passed':sum(r['passed'] for r in results),'failed':sum(not r['passed'] for r in results),
        'results':results,
        'not_verified':['Driver default no-execution behavior: driver not among authorized files',
                        'Historical point 12/point 2 closure wording outside the three authorized source files']}
# Preserve the first pass. A later author replay needs a different output file.
with (ROOT/'reviews/independent_results.json').open('x') as out:
    out.write(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
