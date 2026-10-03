"""Reconfigurable single-process validation driver. Default plan_only, no remote control.
Copied plan + renewed execution authorization required. Historical point2/12 not run here.
"""
from pathlib import Path
from dataclasses import replace
import argparse,hashlib,json,math,platform,sys,time
from trust_region import R, Scene, local_trial, digest, code_hashes

SCHEMA='T03-r3-bounded-device-plan-1'
KEYS={'schema_version','execution_mode','execution_authorized','authorization_evidence','device_label','input_contract_sha256','panels','radii','scales_m','target_s_m2','methods','max_trials','max_panels','max_wall_seconds','stop_on_unresolved','purpose'}


def load(path):
    p=json.loads(Path(path).read_text())
    if set(p)!=KEYS or p['schema_version']!=SCHEMA:raise ValueError('exact plan schema required')
    if p['execution_mode'] not in ('plan_only','explicit_authorized_run') or type(p['execution_authorized']) is not bool or type(p['stop_on_unresolved']) is not bool:raise ValueError('strict execution fields required')
    if p['input_contract_sha256']!=hashlib.sha256((R/'data/frozen_t02_contract.json').read_bytes()).hexdigest():raise ValueError('frozen input hash mismatch')
    if not isinstance(p['panels'],list) or not p['panels'] or any(type(x) is not int or not 1<=x<=4096 for x in p['panels']) or p['panels']!=sorted(set(p['panels'])):raise ValueError('increasing unique bounded panel levels required')
    if not isinstance(p['radii'],list) or not p['radii'] or any(isinstance(x,bool) or not math.isfinite(x) or not 0<x<=2 for x in p['radii']) or p['radii']!=sorted(set(p['radii'])):raise ValueError('increasing unique positive radii <=2 required')
    if p['methods']!=['event_aware','omit_events']:raise ValueError('matched methods required')
    if len(p['scales_m'])!=2 or any(not math.isfinite(x) or not 0<x<=.01 for x in p['scales_m']):raise ValueError('two bounded scales <=.01m required')
    if not math.isfinite(p['target_s_m2']) or p['target_s_m2']<=1e-8:raise ValueError('target denominator unsafe')
    for k in ('max_trials','max_panels'):
        if type(p[k]) is not int or p[k]<=0:raise ValueError('positive integer resource ceilings')
    if not math.isfinite(p['max_wall_seconds']) or p['max_wall_seconds']<=0:raise ValueError('finite positive wall budget')
    return p


def estimate(p):
    n=len(json.loads((R/'data/frozen_t02_contract.json').read_text())['source_nodes_m'])
    return {'trial_calls':len(p['radii'])*len(p['panels'])*2,'rational_panels_upper':8*n*sum(p['panels'])*len(p['radii']),
            'closed_primitive_forward_calls_upper':4*n*len(p['radii'])*len(p['panels']),
            'historical_point2_point12_reexecution':False,'continuous_source_validation':False}


def run(p,output):
    if p['execution_mode']!='explicit_authorized_run' or not p['execution_authorized'] or not p['authorization_evidence'] or not p['device_label']:
        raise ValueError('renewed device authorization and bounded external plan required')
    if not output:raise ValueError('fresh external output required')
    out=Path(output).resolve()
    if out.is_relative_to(R):raise ValueError('cannot write frozen package')
    e=estimate(p)
    if e['trial_calls']>p['max_trials'] or e['rational_panels_upper']>p['max_panels']:raise ValueError('plan exceeds declared budget')
    out.mkdir(parents=True,exist_ok=False)
    start=time.monotonic();records=[];status='complete_bounded_validation';contract=json.loads((R/'data/frozen_t02_contract.json').read_text());sc=Scene(**contract['scene'])
    (out/'run_plan.json').write_text(json.dumps(p,indent=2)+'\n')
    try:
        for panels in p['panels']:
            for radius in p['radii']:
                for method in p['methods']:
                    if time.monotonic()-start>=p['max_wall_seconds']:raise InterruptedError('wall_budget_stop_partial')
                    if (out/'CANCEL').exists():raise InterruptedError('cancelled_partial')
                    r=local_trial(sc,contract['source_nodes_m'],contract['source_weights'],p['target_s_m2'],panels,radius,p['scales_m'],method)
                    records.append({'panels':panels,'radius':radius,'method':method,'result':r})
                    tmp=out/'checkpoint.tmp';tmp.write_text(json.dumps({'plan_sha256':digest(p),'records':records},indent=2)+'\n');tmp.replace(out/'checkpoint.json')
                    if p['stop_on_unresolved'] and (r.get('decision',{}).get('decision')=='unresolved' or r['status'] in ('unresolved_baseline','topology_rejected')):raise InterruptedError('unresolved_stop_partial')
                    if time.monotonic()-start>=p['max_wall_seconds']:raise InterruptedError('wall_budget_stop_partial')
    except (InterruptedError,ValueError,OverflowError) as err:status=str(err)
    receipt={'status':status,'plan_sha256':digest(p),'code_sha256':code_hashes(),'python':platform.python_version(),
        'device_declaration':p['device_label'],'wall_seconds':time.monotonic()-start,'completed_trial_calls':len(records),'preflight_upper':e,
        'wall_enforcement':'between bounded trial calls; one in-progress cell can overrun, no hard real-time claim',
        'formal_chain':'pending','point12_status':'partial_unchanged','point2_status':'conditional_non_strict_unchanged','records':records}
    (out/'results.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n');return receipt

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--plan',default=str(R/'data/device_validation_plan.json'));ap.add_argument('--run',action='store_true');ap.add_argument('--output');a=ap.parse_args()
    try:
        p=load(a.plan)
        result=run(p,a.output) if a.run else {'status':'plan_only_no_execution','plan':p,'work_estimate':estimate(p),'execution':'not_run'}
        print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2,allow_nan=False))
    except (ValueError,KeyError,TypeError,FileExistsError) as err:print(str(err),file=sys.stderr);sys.exit(2)
