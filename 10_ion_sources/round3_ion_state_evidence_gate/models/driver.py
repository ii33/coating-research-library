"""Bounded offline reference driver. Default plan_only; no heavy/device mode."""
from pathlib import Path
import argparse,json,time,platform,copy,math
from evidence_gate import legacy,evaluate,equivalence,verify_dependencies
from state_physics import evolve,bounded_evolve,correlated_kernel,mass_closed_optical
ROOT=Path(__file__).resolve().parents[1]

def plan():return {'mode':'plan_only','executed':False,'tiny_limits':{'max_gate_cases':32,'max_model_bins':16,'max_joint_cells':8,'max_wall_s':20},'deferred':{'experimental_state_identification':'not_run_awaiting_device_and_authorization','full_state_response_optical_rebuild':'plan_only','large_sweep':'plan_only'},'hardware_calls':0,'upstream_optical_calls':0,'quota_bypass':False,'point12':'partial_unchanged','point2':'conditional_non_strict_unchanged','formal_review_chain':'pending'}

def run_tiny():
    t=time.monotonic();deps=verify_dependencies();cases=json.loads((ROOT/'data/gate_cases.json').read_text())
    if len(cases)>32:raise ValueError('gate_case_budget')
    results=[]
    for case in cases:
        if time.monotonic()-t>20:raise RuntimeError('tiny_wall_budget')
        r=evaluate(case['packet']);ok=(r['status']==case['expected_status']and r['reason']==case['expected_reason'])
        results.append({'case':case['id'],'passed':ok,'result':r})
    pulse={'a_s1':1,'b_s1':0,'c_s1':0,'duration_s':1};repair={'a_s1':0,'b_s1':1,'c_s1':0,'duration_s':1}
    histories={'pulse_then_repair':evolve(0,[pulse,repair]),'repair_then_pulse':evolve(0,[repair,pulse]),
      'concurrent_equal_integrals':evolve(0,[{'a_s1':.5,'b_s1':.5,'c_s1':0,'duration_s':2}]),
      'positive_burial':evolve(0,[{'a_s1':1,'b_s1':0,'c_s1':1,'duration_s':1}],1e19)}
    A=[{'dose_m2':.5,'energy_ev':50,'theta_deg':0},{'dose_m2':.5,'energy_ev':150,'theta_deg':60}]
    B=[{'dose_m2':.5,'energy_ev':50,'theta_deg':60},{'dose_m2':.5,'energy_ev':150,'theta_deg':0}]
    bounds={'finite_neutral_bound':bounded_evolve([0,0],[{'a_s1':[1,1.2],'b_s1':[.5,.5],'c_s1':[.5,.5],'duration_s':1}]),
      'unknown_neutral_bound':bounded_evolve([0,0],[{'a_s1':None,'b_s1':[.5,.5],'c_s1':[.5,.5],'duration_s':1}])}
    eq={k:equivalence(v,{'delta_n':.002,'delta_h_relative':.01})for k,v in {
      'inside':{'delta_n':[-.001,.001],'delta_h_relative':[-.005,.005]},
      'crossing':{'delta_n':[-.001,.003],'delta_h_relative':[-.005,.005]},
      'outside':{'delta_n':[.003,.004],'delta_h_relative':[-.005,.005]}}.items()}
    physical={'history':histories,'same_marginals':{'A':correlated_kernel(A),'B':correlated_kernel(B)},'neutral_bounds':bounds,'mass_closed_constitutive':mass_closed_optical(1.5,1.1),'equivalence':eq}
    if not all(r['passed'] for r in results):raise AssertionError('gate_expectation_mismatch')
    return {'mode':'tiny','executed':True,'origin':'synthetic_only','copied_dependencies':deps,'cases':results,'physics':physical,'resources':{'gate_cases':len(cases),'model_bins':8,'joint_cells':4,'upstream_optical_calls':0,'hardware_calls':0,'elapsed_s':time.monotonic()-t},'actual_nk':None,'actual_density':None,'new_optical_operator_executed':False,'formal_review_chain':'pending'}

def main():
    a=argparse.ArgumentParser();a.add_argument('--mode',choices=['plan_only','tiny','offline_packet'],default='plan_only');a.add_argument('--input',type=Path);a.add_argument('--output',type=Path);v=a.parse_args()
    if v.mode=='plan_only':r=plan()
    elif v.mode=='tiny':r=run_tiny()
    else:
        if not v.input:a.error('--input required')
        verify_dependencies();r={'mode':'offline_packet','result':evaluate(json.loads(v.input.read_text())),'advisory_only':True,'device_execution':False}
    r['python']=platform.python_version();s=json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if v.output:
        if v.output.exists():a.error('Output exists; preserve frozen evidence')
        v.output.parent.mkdir(parents=True,exist_ok=True);v.output.write_text(s)
    else:print(s,end='')
if __name__=='__main__':main()
