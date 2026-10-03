"""Tiny offline evidence contract. Research diagnostics only, never production release.

Schema checking is separate from semantic checking. Metadata truth, metrological
adequacy, certificates, signatures, and real hardware are not validated here.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from decimal import Decimal, InvalidOperation, localcontext
import json
import math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def interval_decision(y: str, U: str, lower: str | None = None,
                      upper: str | None = None) -> dict:
    """Closed-interval containment/disjointness, exact decimal supplied strings.
    No probabilistic claim; U must already have a justified interpretation.
    """
    values = [y, U, lower, upper]
    if any(v is not None and not isinstance(v, str) for v in values):
        raise ValueError('decimal_string_required')
    try:
        a, u = Decimal(y), Decimal(U)
        lo = Decimal(lower) if lower is not None else None
        hi = Decimal(upper) if upper is not None else None
    except InvalidOperation as exc:
        raise ValueError('invalid_decimal') from exc
    if not a.is_finite() or not u.is_finite() or any(v is not None and not v.is_finite() for v in [lo, hi]):
        raise ValueError('nonfinite_value')
    if u < 0 or (lo is None and hi is None) or (lo is not None and hi is not None and lo > hi):
        raise ValueError('invalid_interval')
    # Bound input resources, then derive enough precision for exact addition
    # at the finest input decimal quantum (ambient context is not trusted).
    decimals=[v for v in [a,u,lo,hi] if v is not None]
    if any(len(v.as_tuple().digits)>1000 or abs(v.as_tuple().exponent)>1000 for v in decimals):
        raise ValueError('decimal_precision_limit')
    precision=max(1,max(v.adjusted() for v in decimals)-min(v.as_tuple().exponent for v in decimals)+3)
    with localcontext() as ctx:
        ctx.prec=precision
        left, right = a-u, a+u
    if (lo is None or left >= lo) and (hi is None or right <= hi):
        decision='accept_under_rule'
    elif (lo is not None and right < lo) or (hi is not None and left > hi):
        decision='reject_under_rule'
    else:
        decision='indeterminate'
    return {'decision':decision, 'interval':[str(left),str(right)],
            'rule':'project_closed_interval_v1', 'qualification_claim':False}


def fraction(value: str, unit: str) -> str:
    if not isinstance(value,str): raise ValueError('decimal_string_required')
    try: x=Decimal(value)
    except InvalidOperation as exc: raise ValueError('invalid_decimal') from exc
    if not x.is_finite(): raise ValueError('nonfinite_value')
    if unit == '1': return str(x)
    if unit == 'percent':
        sign,digits,exponent=x.as_tuple()
        return str(Decimal((sign,digits,exponent-2)))
    raise ValueError('unsupported_unit')


def mean_u(shared_u, repeat_u, n):
    if not all(finite(v) and v >= 0 for v in [shared_u,repeat_u]) or type(n) is not int or n<1:
        raise ValueError('invalid_uncertainty_input')
    return math.sqrt(shared_u**2+repeat_u**2/n)


def difference_u(ua, ub, covariance):
    if not all(finite(v) for v in [ua,ub,covariance]) or ua<0 or ub<0:
        raise ValueError('invalid_uncertainty_input')
    bound=ua*ub
    if abs(covariance)>bound: raise ValueError('non_psd_pair_covariance')
    return math.sqrt(max(0.,ua*ua+ub*ub-2*covariance))


def conditional_scalar(vff, vhh, vhf, residual):
    if not all(finite(v) for v in [vff,vhh,vhf,residual]) or vff<=0 or vhh<=0:
        raise ValueError('invalid_covariance')
    s=vhh-vhf*vhf/vff
    if s<=0: raise ValueError('non_positive_definite_joint_covariance')
    return {'mean_shift':vhf/vff*residual,'innovation_variance':s,
            'conditions':'fixed parameters; known joint Gaussian covariance'}


def signed_and_clipped_integrals(rates, durations):
    if len(rates)!=len(durations) or not rates: raise ValueError('length_mismatch')
    if not all(finite(v) for v in rates+durations) or any(t<0 for t in durations):
        raise ValueError('invalid_integral_input')
    return {'signed_nm':sum(r*t for r,t in zip(rates,durations)),
            'max_zero_clipped_nm':sum(max(r,0)*t for r,t in zip(rates,durations)),
            'device_algorithm_claim':False}


def validate(packet: dict) -> dict:
    """Selected semantic gates, not an exhaustive normative or JSON Schema validator.
    Reject malformed outer structures early; JSON Schema should also be applied.
    All conclusions here are research-only even when metadata would be complete.
    """
    errors=[]
    def add(code, detail): errors.append({'code':code,'detail':detail})
    if not isinstance(packet,dict):
        return {'semantic_ready':False,'errors':[{'code':'SHAPE','detail':'object required'}], 'production_qualified':False}
    required={'packet_id':str,'evidence_mode':str,'requested_claim':str,
              'observations':list,'datasets':list,'parameter_snapshots':list,
              'events':list,'calibrations':list,'numerics':list,
              'cross_split_correlation':dict,'decision_rule':dict,
              'source_visibility':list}
    for k, typ in required.items():
        if k not in packet or not isinstance(packet[k],typ): add('SHAPE',f'{k}: expected {typ.__name__}')
    if errors: return {'semantic_ready':False,'errors':errors,'production_qualified':False}
    if packet['evidence_mode'] != 'synthetic_demo': add('REAL_EVIDENCE_UNSUPPORTED','This reference implementation only accepts synthetic_demo')
    if packet['requested_claim'] != 'research_diagnostic': add('CLAIM_ESCALATION','Production, hardware, environmental and damage qualification are unsupported')
    lists=['observations','datasets','parameter_snapshots','events','calibrations','numerics','source_visibility']
    for k in lists:
        if any(not isinstance(x,dict) for x in packet[k]): add('SHAPE',f'{k} elements must be objects')
    if errors and any(e['code']=='SHAPE' for e in errors):
        return {'semantic_ready':False,'errors':errors,'production_qualified':False}
    for key in ['observations','datasets','parameter_snapshots','events','calibrations','numerics']:
        ids=[x.get('id') for x in packet[key]]
        if any(not isinstance(i,str) or not i for i in ids) or len(set(i for i in ids if isinstance(i,str)))!=len(ids):
            add('ID_INVALID',key)
    if any(e['code']=='ID_INVALID' for e in errors):
        return {'semantic_ready':False,'errors':errors,'production_qualified':False}
    obs={o['id']:o for o in packet['observations']}
    snaps={s['id']:s for s in packet['parameter_snapshots']}
    evs={e['id']:e for e in packet['events']}
    cals={c['id']:c for c in packet['calibrations']}
    final_groups=set(); dev_groups=set(); final_observations=set(); dev_observations=set()
    by_cal={}
    roles={'fit','selection','heldout_final','calibration','process_estimate'}
    for ds in packet['datasets']:
        role=ds.get('role')
        if role not in roles: add('ROLE_UNKNOWN',ds['id']);continue
        ids=ds.get('observation_ids',[])
        if not isinstance(ids,list) or any(not isinstance(x,str) for x in ids): add('SHAPE',ds['id']+' observation_ids');continue
        for oid in ids:
            if oid not in obs: add('OBS_REF_MISSING',oid);continue
            o=obs[oid]
            if role in {'fit','selection','heldout_final','calibration'}:
                if o.get('reading_origin') not in {'measured','derived_from_measurement'}:
                    add('NOT_MEASURED',oid+' in '+role)
                if o.get('requires_lock') is True and o.get('lock_state')!='locked': add('LOCK_UNRESOLVED',oid)
                if not o.get('raw_ref'): add('RAW_MISSING',oid)
            if role in {'fit','selection','heldout_final'}:
                group=o.get('run_id')
                if not isinstance(group,str) or not group: add('GROUP_MISSING',oid)
                elif role=='heldout_final': final_groups.add(group);final_observations.add(oid)
                else: dev_groups.add(group);dev_observations.add(oid)
                groupcal=o.get('calibration_id')
                if groupcal: by_cal.setdefault(groupcal,set()).add(role)
    if final_observations & dev_observations or final_groups & dev_groups:
        add('HELDOUT_LEAKAGE','Final validation and development share observation or run group')
    shared=[c for c,roleset in by_cal.items() if 'heldout_final' in roleset and roleset&{'fit','selection'}]
    corr=packet['cross_split_correlation']
    if shared and (corr.get('status') not in {'known_synthetic','modelled_with_evidence'} or not corr.get('basis_ref')):
        add('CORRELATION_UNRESOLVED',','.join(shared))
    if any(ds.get('role')=='heldout_final' and ds.get('used_to_update_model') is not False for ds in packet['datasets']):
        add('HELDOUT_CONSUMED','Missing/true used_to_update_model on final heldout')
    for o in obs.values():
        if o.get('unit') not in {'nm','nm/s','Hz','1','percent'}: add('UNIT_UNSUPPORTED',o['id'])
        if not o.get('quantity_kind') or not o.get('coordinate'): add('MEASURAND_MISSING',o['id'])
        if not finite(o.get('t_s')) or not finite(o.get('value')): add('VALUE_INVALID',o['id'])
        if o.get('controller_mode')=='time_power' and o.get('reading_origin') in {'measured','derived_from_measurement'}:
            add('TIME_POWER_MISLABELLED',o['id'])
        sid=o.get('parameter_snapshot_id')
        if sid not in snaps: add('PARAMETER_SNAPSHOT_MISSING',o['id'])
        if o.get('parameter_switched'):
            eid=o.get('parameter_event_id'); e=evs.get(eid,{})
            if e.get('kind')!='parameter_change' or e.get('snapshot_id')!=sid or not finite(e.get('t_s')) or not finite(o.get('t_s')) or e['t_s']>o['t_s']:
                add('PARAMETER_EVENT_MISSING',o['id'])
        if o.get('negative_clip_mode')!='none' and (not o.get('raw_ref') or not o.get('transformation_ref')):
            add('CLIPPED_LINEAGE_MISSING',o['id'])
        if o.get('reading_origin')=='derived_from_measurement' and not o.get('transformation_ref'):
            add('DERIVATION_MISSING',o['id'])
        cid=o.get('calibration_id')
        if cid not in cals: add('CALIBRATION_MISSING',o['id'])
        elif cals[cid].get('within_scope') is not True or not cals[cid].get('basis_ref'):
            add('CALIBRATION_DOMAIN_UNRESOLVED',o['id'])
    for s in packet['source_visibility']:
        if s.get('zero_flux_verified') is True:
            if s.get('workpiece_visibility')!='closed_verified' or not s.get('position_evidence_ref') or not s.get('zero_flux_basis_ref'):
                add('ZERO_FLUX_UNSUPPORTED',s.get('source_id','unknown'))
        # closed_verified describes the visibility, not temperature or total material transport.
    for stage in packet['numerics']:
        status=stage.get('status')
        if stage.get('required_for_claim') is True and status not in {'converged_local','validated_analytic'}:
            add('NUMERIC_INCOMPLETE',stage['id']+':'+str(status))
        calls,budget=stage.get('calls'),stage.get('budget')
        if type(calls) is not int or type(budget) is not int or calls<0 or budget<0 or calls>budget:
            add('BUDGET_INVALID',stage['id'])
        if not stage.get('stop_reason'): add('STOP_REASON_MISSING',stage['id'])
    rule=packet['decision_rule']
    if rule.get('preagreed') is not True or not rule.get('approval_ref'):
        add('RULE_NOT_PREAGREED','Synthetic rule must be frozen before the constructed data')
    if rule.get('rule_id')!='project_closed_interval_v1': add('RULE_UNSUPPORTED',str(rule.get('rule_id')))
    return {'semantic_ready':not errors,'errors':errors,
            'meaning':'Selected research evidence gates only; metadata truth and normative compliance unverified',
            'production_qualified':False,'hardware_validated':False}


def baseline():
    o={'id':'O_F','value':0.95,'unit':'1','quantity_kind':'regular_transmittance',
       'coordinate':'finite_sample_external','t_s':10.,'run_id':'run_fit',
       'sample_id':'synthetic_fit_sample','reading_origin':'measured','raw_ref':'synthetic://F',
       'requires_lock':False,'lock_state':'not_applicable','controller_mode':'measurement',
       'parameter_snapshot_id':'P1','parameter_switched':False,'parameter_event_id':None,
       'negative_clip_mode':'none','transformation_ref':None,'calibration_id':'C1'}
    h=deepcopy(o);h.update(id='O_H',run_id='run_heldout',sample_id='synthetic_heldout_sample',raw_ref='synthetic://H',value=0.949)
    return {'packet_id':'synthetic_baseline','evidence_mode':'synthetic_demo','requested_claim':'research_diagnostic',
            'observations':[o,h],
            'datasets':[{'id':'D_F','role':'fit','observation_ids':['O_F'],'used_to_update_model':True},
                        {'id':'D_H','role':'heldout_final','observation_ids':['O_H'],'used_to_update_model':False}],
            'parameter_snapshots':[{'id':'P1','material_id':'synthetic_film','density_kg_m3':5000.,'z_factor':1.,
                                    'tooling_fraction':1.,'feedback_coordinate':'qcm_equivalent','display_coordinate':'sample_estimate'}],
            'events':[],
            'calibrations':[{'id':'C1','within_scope':True,'basis_ref':'synthetic://calibration_domain'}],
            'numerics':[{'id':'analytic','status':'validated_analytic','required_for_claim':True,'calls':1,'budget':1,'stop_reason':'exact_demo_formula'}],
            'cross_split_correlation':{'status':'known_synthetic','basis_ref':'synthetic://shared_reference_covariance'},
            'decision_rule':{'rule_id':'project_closed_interval_v1','preagreed':True,'approval_ref':'synthetic://preregistered_rule'},
            'source_visibility':[{'source_id':'old_source','workpiece_visibility':'unknown','position_evidence_ref':None,
                                  'thermal_state':'unknown','zero_flux_verified':False,'zero_flux_basis_ref':None}]}


def examples():
    cases=[]
    def case(name, edit, expected):
        p=baseline();p['packet_id']=name;edit(p)
        result=validate(p);actual={e['code'] for e in result['errors']}
        cases.append({'name':name,'packet':p,'expected_codes':sorted(expected),'actual_codes':sorted(actual),
                      'matches_expectation':actual==set(expected),'result':result})
    case('baseline_research_only',lambda p:None,[])
    case('production_claim_blocked',lambda p:p.update(requested_claim='production_acceptance'),['CLAIM_ESCALATION'])
    case('time_power_mislabelled',lambda p:p['observations'][0].update(controller_mode='time_power'),['TIME_POWER_MISLABELLED'])
    case('substitution_in_fit',lambda p:p['observations'][0].update(controller_mode='time_power',reading_origin='substituted_setpoint'),['NOT_MEASURED'])
    case('substitution_retained_as_estimate',lambda p:(p['observations'][0].update(controller_mode='time_power',reading_origin='substituted_setpoint'),p['datasets'][0].update(role='process_estimate')),[])
    case('parameter_switch_no_event',lambda p:p['observations'][0].update(parameter_switched=True),['PARAMETER_EVENT_MISSING'])
    case('negative_clip_without_raw',lambda p:p['observations'][0].update(negative_clip_mode='project_max_zero_demo',raw_ref=None),['CLIPPED_LINEAGE_MISSING','RAW_MISSING'])
    case('unknown_shutter_claims_zero',lambda p:p['source_visibility'][0].update(zero_flux_verified=True),['ZERO_FLUX_UNSUPPORTED'])
    case('shared_calibration_ignored',lambda p:p['cross_split_correlation'].update(status='unknown',basis_ref=None),['CORRELATION_UNRESOLVED'])
    case('run_group_leakage',lambda p:p['observations'][1].update(run_id='run_fit'),['HELDOUT_LEAKAGE'])
    case('heldout_used_to_tune',lambda p:p['datasets'][1].update(used_to_update_model=True),['HELDOUT_CONSUMED'])
    case('profile_budget_exhausted',lambda p:p['numerics'].append({'id':'profile_high','status':'budget_exhausted','required_for_claim':True,'calls':45,'budget':45,'stop_reason':'max_calls'}),['NUMERIC_INCOMPLETE'])
    case('calibration_domain_unknown',lambda p:p['calibrations'][0].update(within_scope=None),['CALIBRATION_DOMAIN_UNRESOLVED'])
    case('qcm_lock_unknown',lambda p:p['observations'][0].update(requires_lock=True,lock_state='unknown'),['LOCK_UNRESOLVED'])
    case('rule_after_measurement',lambda p:p['decision_rule'].update(preagreed=False),['RULE_NOT_PREAGREED'])
    ub,ur,n=.003,.001,25
    u=math.sqrt(ub*ub+ur*ur)
    math_examples={
      'all_synthetic':True,
      'shared_reference_mean':{'shared_u':ub,'repeat_u':ur,'n':n,'correct_u':mean_u(ub,ur,n),
          'wrong_independence_u':u/math.sqrt(n),'understatement_factor':mean_u(ub,ur,n)/(u/math.sqrt(n))},
      'paired_change':{'each_total_u':u,'covariance':ub*ub,'u_delta':difference_u(u,u,ub*ub),'wrong_independence_u_delta':math.sqrt(2)*u},
      'conditional_innovation':conditional_scalar(4.,9.,3.,2.),
      'nonlinear_square':{'sigma_x':.2,'plugin_estimate':0.,'first_order_u':0.,'analytic_expectation':.2**2,'analytic_u':math.sqrt(2)*.2**2},
      'negative_clipping':signed_and_clipped_integrals([-1.,2.,-1.,2.],[1.,1.,1.,1.]),
      'density_switch_normalized':{'equivalent_areal_increment':1.,'rho_before':5.,'rho_after':1.,'display_before':.2,'display_after':1.,'ratio':5.,'physical_mass_inference':False},
      'tooling_feedback':{'c_before':1.,'c_after':1.1,'constant_display_target':1.,'qcm_target_after':1/1.1,'user_device_measurement':False},
      'known_old_source_residual':{'synthetic_visible_rate_nm_s':.2,'duration_s':5.,'thickness_nm':1.,'unknown_visibility_thickness_nm':None},
      'interval_cases':{v:interval_decision(v,'0.004','0.94') for v in ['0.950','0.942','0.930','0.944','0.936']}}
    return {'cases':cases,'mathematics':math_examples,
            'all_expected':all(c['matches_expectation'] for c in cases),
            'hardware_validated':False,'production_qualified':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--examples',action='store_true');parser.add_argument('--packet',type=Path)
    args=parser.parse_args()
    if args.examples: result=examples()
    elif args.packet: result=validate(json.loads(args.packet.read_text()))
    else: parser.error('choose --examples or --packet')
    print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
