"""Necessary bounded examples, stdout only. Does not change frozen evidence."""
from dataclasses import replace
import json
from trust_region import *
from event_reference import evaluate


def examples():
    s=Scene();event=local_trial(s);omitted=local_trial(s,method='omit_events')
    base=evaluate(0.,s);eps=1e-4
    shift=[]
    for method,direction in [('event_aware',-eps),('omit_events',eps)]:
        value=evaluate(0.,replace(s,target_shift_m=s.target_shift_m+direction))['value_s_m2']
        shift.append({'method':method,'target_shift_increment_m':direction,'forward_value_s_m2':value,'same_objective_value':0.5*(value-1.)**2,'ranking':'diagnostic_float_only_not_interval_resolved'})
    far,clipped=clipped_candidate(s,[0.],[0.2,0.])
    unsafe=certify_segment(s,replace(s,plate_shift_m=0.2),[0.])
    overlap=compare(event['baseline'],event['baseline'])
    unknown=full_forward(replace(s,shadow_boundary_uncertainty_m=1e-5))
    unknown_comparison=compare(unknown,unknown)
    bad_denominators=[reduction_ratio(event['baseline'],event['trial'],d) for d in ({'lo':0.,'hi':0.},{'lo':-1e-9,'hi':1e-9},{'lo':1e-15,'hi':1e-15})]
    # Generic guard counterexample, not a new coating dataset: first order omits known curvature.
    alpha=0.8;h=1-alpha-4*alpha*alpha
    return {'dataset':'inherited_T02_finite_thickness_affine_slice','new_physical_dataset':False,
       'baseline_derivative_decomposition':{'target_shift_total':base['gradient'][0],'target_shift_smooth_only':base['smooth_gradient'][0],'half_width_total':base['gradient'][5],'half_width_smooth_only':base['smooth_gradient'][5]},
       'event_aware_local_trial':event,'omitted_event_local_trial':omitted,'target_shift_sign_counterexample':shift,
       'half_width_pure_event':{'smooth_derivative':base['smooth_gradient'][5],'event_derivative':base['event_gradient'][5]},
       'unsafe_unclipped_step':unsafe,'clipped_step':clipped,'clipped_plate_shift_m':far.plate_shift_m,
       'heuristic_only':heuristic_limit(s,[0.],[0.2,0.]),
       'nonlinear_guard_counterexample':{'guard':'1-alpha-4*alpha^2','first_order_limit_with_0.8_margin':alpha,'actual_guard':h,'positive_root':(-1+math.sqrt(17))/8,'conclusion':'first_order_screen_is_not_general_safety_certificate'},
       'overlap_decision':overlap,'unknown_geometry_decision':unknown_comparison,'pathological_predicted_denominators':bad_denominators,
       'inherited_status':{'point12':'partial_unchanged','point2':'conditional_envelope_not_strict','continuous_source_validation':'not_run','formal_model_chain':'pending'}}

if __name__=='__main__': print(json.dumps(examples(),indent=2,allow_nan=False))
