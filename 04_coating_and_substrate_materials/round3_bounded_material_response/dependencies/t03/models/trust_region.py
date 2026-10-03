"""Two-parameter, event-aware local steps. Encoded SI affine slab only.
No CAD, device I/O, continuous-source certificate or physical certification.
"""
from dataclasses import asdict, replace
from fractions import Fraction as F
from pathlib import Path
import hashlib, json, math
import numpy as np
from event_reference import Scene, evaluate, PARAMETERS
from frozen.intervals_v2 import Interval, rounded

DESIGN = ('plate_shift_m', 'half_width_m')
MODEL_VERSION = 'T03-r3-affine-trust-1'
R = Path(__file__).resolve().parents[1]


def frac(x):
    if isinstance(x, F): return x
    if isinstance(x, bool) or not math.isfinite(float(x)): raise ValueError('finite numeric input required')
    return F(float(x))


def digest(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def source_contract(nodes, weights):
    if not 1 <= len(nodes) <= 65 or len(nodes) != len(weights): raise ValueError('1..65 paired finite source nodes required')
    nodes = [float(frac(x)) for x in nodes]; weights = [float(frac(x)) for x in weights]
    if len(set(nodes)) != len(nodes) or min(weights) < 0 or sum(weights) <= 0: raise ValueError('unique nodes and nonnegative nonzero weights required')
    return nodes, weights


def exact_scene(sc):
    sc.validate()
    if sc.shadow_boundary_uncertainty_m: raise ValueError('geometry_unknown')
    if abs(frac(sc.velocity_m_s)) <= frac(sc.transverse_floor_m_s): raise ValueError('transversality_unresolved')
    p={k: frac(v) for k, v in asdict(sc).items()}
    if min(p['q0']+p['q1_per_s']*p['t0'],p['q0']+p['q1_per_s']*p['t1'])<0:raise ValueError('encoded_source_rate_negative')
    return p


def frozen_nondesign_equal(a, b):
    return all(getattr(a, k) == getattr(b, k) for k in asdict(a) if k not in DESIGN)


def exact_events(sc, node):
    """All arithmetic exact for encoded binary float inputs; event identity is face+boundary."""
    p = exact_scene(sc); s = frac(node) + p['source_shift_m']; H = p['height_m']; v = p['velocity_m_s']
    rows = []; faces = []
    for sign, label in [(-1, 'lower'), (1, 'upper')]:
        bs = []
        for zkey in ('z_near_m', 'z_far_m'):
            z = p[zkey]; b = s + (p['plate_shift_m'] + sign*p['half_width_m'] - s)*H/z
            bs.append((b, (H/z, sign*H/z), zkey))
        winner = min(range(2), key=lambda j:bs[j][0]) if sign == -1 else max(range(2), key=lambda j:bs[j][0])
        win, other = bs[winner], bs[1-winner]
        # lower: other-win; upper: win-other
        g = (win[0]-other[0])*sign - p['face_guard_m']
        dg = tuple((win[1][j]-other[1][j])*sign for j in range(2))
        faces.append({'id':f'face:{node.hex()}:{label}', 'h':g, 'grad':dg})
        b, jb, zkey = win
        t = (b-p['x0_m']-p['target_shift_m'])/v-p['clock_offset_s']
        rows.append({'id':f'{node.hex()}:{label}:{zkey}', 'time':t, 'grad':tuple(x/v for x in jb), 'zkey':zkey, 'boundary':label})
    return sorted(rows,key=lambda e:e['time']), faces


def guard_rows(sc, nodes):
    p = exact_scene(sc); guards = []; all_events = []
    for node in nodes:
        events, faces = exact_events(sc, float(node)); guards.extend(faces); all_events.extend(events)
        for e in events:
            for end in ('t0','t1'):
                raw=e['time']-p[end]; sign=1 if raw>0 else -1
                guards.append({'id':f'endpoint:{e["id"]}:{end}', 'h':abs(raw)-p['event_guard_s'], 'grad':tuple(sign*x for x in e['grad'])})
    all_events.sort(key=lambda e:e['time'])
    for a,b in zip(all_events[:-1],all_events[1:]):
        guards.append({'id':f'order:{a["id"]}:{b["id"]}', 'h':b['time']-a['time']-2*p['event_guard_s'], 'grad':tuple(b['grad'][j]-a['grad'][j] for j in range(2))})
    guards.append({'id':'positive_half_width','h':p['half_width_m'],'grad':(F(0),F(1))})
    if any(g['h']<=0 for g in guards): raise ValueError('topology_unresolved')
    # Angular cutoffs are invariant under DESIGN: H>z_far>0 and r finite => both cosines >0.
    return guards, all_events


def heuristic_limit(sc, nodes, direction, fraction=0.8):
    guards,_=guard_rows(sc,nodes); d=np.asarray(direction,dtype=float)
    if d.shape!=(2,) or not np.all(np.isfinite(d)) or not 0<fraction<1: raise ValueError('direction and fraction')
    crossings=[float(g['h'])/-float(np.dot([float(x) for x in g['grad']],d)) for g in guards if np.dot([float(x) for x in g['grad']],d)<0]
    return {'alpha':min([1.]+[fraction*x for x in crossings]),'claim':'first_order_screen_only_no_remainder_evidence'}


def certify_segment(base, candidate, nodes):
    if not frozen_nondesign_equal(base,candidate): raise ValueError('only plate shift and half width may change')
    candidate.validate(); guards, events=guard_rows(base,nodes)
    delta=[frac(getattr(candidate,k))-frac(getattr(base,k)) for k in DESIGN]
    rows=[]
    for g in guards:
        dh=sum((g['grad'][j]*delta[j] for j in range(2)),F(0)); lower=min(g['h'],g['h']+dh)
        rows.append({'id':g['id'],'minimum_margin_exact':str(lower),'minimum_margin_float_lower':rounded(lower,True),'positive':lower>0})
    ok=all(x['positive'] for x in rows)
    return {'status':'encoded_affine_segment_certified' if ok else 'reject_topology_crossing_or_guard',
            'scope':'all beta in [0,1] between encoded endpoints; no input uncertainty',
            'zero_remainder_reason':'only b,a vary; H,z,v,poses,source clock fixed',
            'angular_cutoff':'invariant_strict_positive_cosines_H_positive',
            'transversality':'fixed_nonzero_velocity_above_floor',
            'event_identities':[e['id'] for e in events],'guards':rows}


def clipped_candidate(sc,nodes,direction):
    guards,_=guard_rows(sc,nodes); d=[frac(x) for x in direction]
    if len(d)!=2:raise ValueError('two design increments required')
    bounds=[F(1)]
    for g in guards:
        dh=sum((g['grad'][j]*d[j] for j in range(2)),F(0))
        if dh<0:bounds.append(F(4,5)*g['h']/-dh)
    alpha=rounded(min(bounds),True)
    candidate=replace(sc,**{k:float(getattr(sc,k)+alpha*float(d[j])) for j,k in enumerate(DESIGN)})
    proof=certify_segment(sc,candidate,nodes)
    return candidate, {'alpha':alpha,'unclipped_increment_m':[float(x) for x in d],
        'actual_encoded_increment_m':[getattr(candidate,k)-getattr(sc,k) for k in DESIGN], 'certificate':proof}


def exact_visible_intervals(sc,node):
    p=exact_scene(sc);events,_=exact_events(sc,float(node));a,b=[e['time'] for e in events]
    out=[]
    if p['t0']<min(a,p['t1']):out.append((p['t0'],min(a,p['t1'])))
    if max(b,p['t0'])<p['t1']:out.append((max(b,p['t0']),p['t1']))
    return out


def rational_forward_interval(sc,nodes,weights,panels=64):
    """Positive-kernel Darboux bounds, exact rational panels and event endpoints.
    No fitted error bar. Finite encoded source sum only, no continuum/source error proof.
    """
    nodes,weights=source_contract(nodes,weights);p=exact_scene(sc)
    if type(panels) is not int or not 1<=panels<=4096:raise ValueError('1..4096 panels per visible segment')
    lower=F(0);upper=F(0);count=0;H2=p['height_m']**2
    for node,weight in zip(nodes,weights):
        s=frac(node)+p['source_shift_m'];d=p['x0_m']+p['target_shift_m']+p['velocity_m_s']*p['clock_offset_s']-s
        for a,b in exact_visible_intervals(sc,node):
            dt=(b-a)/panels
            for j in range(panels):
                ta=a+j*dt;tb=ta+dt;qa=p['q0']+p['q1_per_s']*ta;qb=p['q0']+p['q1_per_s']*tb
                ya=d+p['velocity_m_s']*ta;yb=d+p['velocity_m_s']*tb
                ymin=F(0) if ya*yb<=0 else min(ya*ya,yb*yb);ymax=max(ya*ya,yb*yb)
                lo=p['amplitude']*min(qa,qb)*H2/(H2+ymax)**2
                hi=p['amplitude']*max(qa,qb)*H2/(H2+ymin)**2
                lower+=frac(weight)*dt*lo;upper+=frac(weight)*dt*hi;count+=1
    return Interval(rounded(lower,True),rounded(upper,False)),count


def objective_interval(value,target,denominator_floor=1e-8):
    target=frac(target);floor=frac(denominator_floor)
    if floor<=0 or target<=floor:raise ValueError('pathological_objective_denominator')
    if not value.known:return Interval.unknown()
    a=(frac(value.lo)-target)/target;b=(frac(value.hi)-target)/target
    lo=F(0) if a<=0<=b else min(a*a,b*b)/2;hi=max(a*a,b*b)/2
    return Interval(rounded(lo,True),rounded(hi,False))


def code_hashes():
    return {str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((R/'models').rglob('*.py'))}


def common_contract(sc,nodes,weights,target,panels):
    scene=asdict(sc);design={k:scene.pop(k) for k in DESIGN}
    common={'model':MODEL_VERSION,'scene_fixed':scene,'source_nodes_m':nodes,'source_weights':weights,
       'units':{'time':'s','length':'m','angle':'rad','output':'s/m^2','objective':'1'},
       'source_frame':{'y_m':0.,'z_m':0.,'normal_lab':[0.,0.,1.],'rotation_lab':'identity'},
       'target_frame':{'y_m':0.,'normal_lab':[0.,0.,-1.],'rotation_lab':'fixed'},
       'plate_frame':{'y_m':0.,'normal_lab':[0.,0.,1.],'rotation_lab':'identity','solid':'finite_closed_rectangle'},
       'source_rate_clock':'reference_t_not_pose_shifted','objective':{'definition':'0.5*((D-target)/target)^2','target_s_m2':target,'denominator_floor':1e-8},
       'numerics':{'interval':'exact_rational_Darboux_outward_float','panels_per_visible_segment':panels,'smooth_derivative_GL_order':32},
       'input_uncertainty':'zero_only_otherwise_unknown','code_sha256':code_hashes()}
    return common,design


def full_forward(sc,nodes=(0.,),weights=(1.,),target=1.,panels=64):
    sc.validate();nodes,weights=source_contract(nodes,weights);objective_interval(Interval.unknown(),target)
    common,design=common_contract(sc,nodes,weights,target,panels)
    out={'contract_signature':digest(common),'objective_definition':common['objective'],'design':design,
         'geometry_status':'unknown','objective_status':'unknown','value_interval':Interval.unknown().to_dict(),
         'objective_interval':Interval.unknown().to_dict(),'value_estimate_s_m2':None,'objective_estimate':None,
         'total_gradient':None,'smooth_gradient':None,'event_gradient':None,'physical_certification':False,
         'continuous_source_certification':False,'input_uncertainty_qualified':sc.shadow_boundary_uncertainty_m==0}
    identities=[]
    try:
        guards,events=guard_rows(sc,nodes);identities=[e['id'] for e in events]
        vals=[evaluate(node,sc) for node in nodes]
        if any(x['sensitivity_status']!='differentiable_conditional' for x in vals):raise ValueError('float_reference_branch_unresolved')
        interval,count=rational_forward_interval(sc,nodes,weights,panels)
        value=math.fsum(w*x['value_s_m2'] for w,x in zip(weights,vals));obj=0.5*((value-target)/target)**2
        if not interval.lo<=value<=interval.hi:raise ValueError('closed_primitive_outside_rational_enclosure')
        oi=objective_interval(interval,target)
        out.update(geometry_status='differentiable_conditional',objective_status='bounded_encoded_discrete_source',
           value_interval=interval.to_dict(),objective_interval=oi.to_dict(),value_estimate_s_m2=value,objective_estimate=obj,
           panel_count=count,numerical_evidence='rational_enclosure_not_quadrature_difference',
           **{kind:np.sum([w*np.asarray(x[kind]) for w,x in zip(weights,vals)],axis=0).tolist() for kind in ('smooth_gradient','event_gradient')})
        out['total_gradient']=(np.array(out['smooth_gradient'])+np.array(out['event_gradient'])).tolist()
    except ValueError as e:out['reason']=str(e)
    out['event_identities']=identities
    out['cache_key']=digest({'contract':common,'design':design,'event_identities':identities,'evaluation_status':out['objective_status']})
    return out


def compare(a,b):
    if a['contract_signature']!=b['contract_signature']:raise ValueError('incompatible_objective_source_or_code_contract')
    if any(x['geometry_status']!='differentiable_conditional' or x['objective_status']!='bounded_encoded_discrete_source' or not x['input_uncertainty_qualified'] for x in (a,b)):
        return {'relation':'unresolved','reason':'unknown_geometry_input_or_error'}
    ia=Interval.from_dict(a['objective_interval']);ib=Interval.from_dict(b['objective_interval'])
    if not ia.known or not ib.known:return {'relation':'unresolved','reason':'unknown_objective_interval'}
    if ia.hi<ib.lo:return {'relation':'a_better','reason':'disjoint_qualified_objective_intervals'}
    if ib.hi<ia.lo:return {'relation':'b_better','reason':'disjoint_qualified_objective_intervals'}
    return {'relation':'unresolved','reason':'overlap_or_equal_objective_intervals'}


def reduction_ratio(base,candidate,predicted,eta=0.1,denominator_floor=1e-12):
    pred=Interval.from_dict(predicted);floor=frac(denominator_floor)
    if floor<=0 or not 0<eta<1:raise ValueError('positive denominator floor and 0<eta<1 required')
    if not pred.known or frac(pred.lo)<=floor:return {'decision':'reject','reason':'pathological_predicted_reduction_denominator','rho':None}
    relation=compare(base,candidate)
    if relation['relation']=='unresolved':return {'decision':'unresolved','reason':relation['reason'],'rho':None}
    a=Interval.from_dict(base['objective_interval']);b=Interval.from_dict(candidate['objective_interval'])
    actual=a+b.scale(-1);rho=actual.divide(pred)
    decision='accept' if rho.lo>=eta and relation['relation']=='b_better' else 'reject' if rho.hi<eta else 'unresolved'
    return {'decision':decision,'reason':'bounded_actual_reduction_over_encoded_positive_model_reduction','rho':rho.to_dict(),'actual_reduction':actual.to_dict()}


def local_trial(sc,nodes=(0.,),weights=(1.,),target=1.,panels=64,radius=1.,scales=(0.002,0.002),method='event_aware'):
    """Single Gauss-Newton Cauchy proposal; no convergence claim or automatic repeated run."""
    if method not in ('event_aware','omit_events'):raise ValueError('unknown model')
    if not math.isfinite(radius) or radius<=0 or len(scales)!=2 or any(not math.isfinite(x) or x<=0 for x in scales):raise ValueError('positive local scales and radius')
    base=full_forward(sc,nodes,weights,target,panels)
    if base['objective_status']!='bounded_encoded_discrete_source':return {'status':'unresolved_baseline','baseline':base}
    j=np.array(base['total_gradient'] if method=='event_aware' else base['smooth_gradient'])[[PARAMETERS.index(k) for k in DESIGN]]*np.array(scales)/target
    residual=(base['value_estimate_s_m2']-target)/target;g=residual*j;norm=float(np.linalg.norm(g))
    if norm==0:return {'status':'zero_model_gradient_not_stationarity_proof','method':method,'baseline':base,'trial':base,'encoded_increment_m':[0.,0.],'predicted_reduction':{'lo':0.,'hi':0.},'decision':{'decision':'reject','reason':'pathological_predicted_reduction_denominator','rho':None}}
    unit=-g/norm;curvature=float((j@unit)**2);length=min(radius,norm/curvature) if curvature>0 else radius
    direction=np.array(scales)*length*unit
    candidate,step=clipped_candidate(sc,nodes,direction)
    if step['certificate']['status']!='encoded_affine_segment_certified':return {'status':'topology_rejected','step':step,'baseline':base}
    delta=np.array(step['actual_encoded_increment_m'])/np.array(scales)
    # Model is an encoded rational linear-residual model. No claim that it encloses true Taylor reduction.
    rr=frac(residual);jd=sum((frac(j[k])*frac(delta[k]) for k in range(2)),F(0));pr=(rr*rr-(rr+jd)**2)/2
    predicted=Interval(rounded(pr,True),rounded(pr,False))
    trial=full_forward(candidate,nodes,weights,target,panels)
    decision=reduction_ratio(base,trial,predicted.to_dict())
    # Radius updates are proposals only, not a license to re-use the old branch or derivative.
    next_radius=radius/2 if decision['decision'] in ('reject','unresolved') else min(2*radius,2.) if decision['rho']['lo']>0.75 else radius
    return {'status':'single_trial_complete','method':method,'baseline':base,'trial':trial,'step':step,'predicted_reduction':predicted.to_dict(),
       'prediction_qualification':'exact_value_of_encoded_local_model_not_true_Taylor_bound','comparison':compare(base,trial),'decision':decision,
       'next_radius_proposal':next_radius,'next_iteration_requires_fresh_forward_jacobian_topology':True,'global_optimality_claim':False}
