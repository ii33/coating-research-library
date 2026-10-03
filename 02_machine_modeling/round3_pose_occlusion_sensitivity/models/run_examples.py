"""Small deterministic formula examples. Prints by default; never fits data."""
from pathlib import Path
from dataclasses import replace
import argparse,json
import numpy as np
from event_reference import Scene,evaluate,grazing_duration,rate_kernel,visible_intervals,PARAMETERS
from analytic_oracle import exact_value_gradient

def examples():
    sc=Scene();base=evaluate(0.,sc);v,j=exact_value_gradient(sc)
    # Fixed-grid finite difference of H(t-theta), exact integral 1-theta.
    nodes=(np.arange(16)+.5)/16;theta=.431
    fd=[]
    for eps in (1e-1,1e-2,1e-3,1e-5,1e-7):
        val=lambda p:float(np.mean(nodes>p))
        fd.append({'step':eps,'fixed_grid_derivative':(val(theta+eps)-val(theta-eps))/(2*eps),'exact_derivative':-1.})
    grazing=[{'parameter':p,**grazing_duration(p)} for p in (-1e-4,0.,1e-8,1e-6,1e-4)]
    unknown=evaluate(0.,replace(sc,shadow_boundary_uncertainty_m=1e-3))
    zero=np.array([1.,1.,0.,0.,1.,0.,0.]);J=np.array(base['gradient'])
    return {'dataset_kind':'synthetic_analytic_only','scene':sc.__dict__,'base':base,
        'closed_primitive_oracle':{'value_s_m2':v,'gradient':j.tolist(),'max_abs_jacobian_difference':float(np.max(np.abs(J-j)))},
        'naive_finite_difference_counterexample':fd,'grazing_counterexample':grazing,'unknown_geometry':unknown,
        'confounding':{'clock_equals_velocity_times_target_column':float(J[2]-sc.velocity_m_s*J[0]),
            'joint_translation_null_direction':zero.tolist(),'joint_translation_residual':float(J@zero),
            'interpretation':'Source/target/plate translation gauge and constant-speed phase/clock ambiguity remain'},
        'inherited_status':{'point12':'partial_not_rerun','point2':'conditional_envelope_not_strict_certification','device_execution':'not_run'}}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output');a=p.parse_args();s=json.dumps(examples(),ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if a.output:Path(a.output).write_text(s)
    else:print(s,end='')
