"""Complete bounded refinement driver; default plan_only. No remote/device operations.
Actual high-cost execution is NOT authorized by this package. A fresh external plan,
renewed authorization, restored host permissions and fresh external output are required.
"""
from pathlib import Path
from dataclasses import asdict
import argparse,json,math,platform,time
from bounded_response import R,Scene,Response,forward,compare,digest,code_hashes
KEYS={'schema_version','execution_mode','execution_authorized','authorization_evidence','host_access_confirmed','device_label','input_sha256','panel_levels','max_forward_calls','max_total_panels','max_wall_seconds','relative_thickness_tolerance','stop_when_resolved','purpose'}
def load(path):
 p=json.loads(Path(path).read_text())
 if set(p)!=KEYS or p['schema_version']!='T04-r3-response-validation-1':raise ValueError('exact plan fields required')
 if p['execution_mode'] not in ('plan_only','explicit_authorized_run'):raise ValueError('execution mode')
 for k in ['execution_authorized','host_access_confirmed','stop_when_resolved']:
  if type(p[k]) is not bool:raise ValueError('strict boolean required')
 for k in ['authorization_evidence','device_label','purpose']:
  if not isinstance(p[k],str):raise ValueError('text field')
 inp=json.loads((R/'data/driver_inputs.json').read_text())
 if p['input_sha256']!=digest(inp):raise ValueError('frozen input hash mismatch')
 levels=p['panel_levels']
 if not isinstance(levels,list) or not levels or levels!=sorted(set(levels)) or any(type(x) is not int or not 1<=x<=4096 for x in levels):raise ValueError('increasing panel levels 1..4096')
 for k in ['max_forward_calls','max_total_panels']:
  if type(p[k]) is not int or p[k]<=0:raise ValueError('positive resource ceilings')
 for k in ['max_wall_seconds','relative_thickness_tolerance']:
  if isinstance(p[k],bool) or not isinstance(p[k],(float,int)) or not math.isfinite(p[k]) or p[k]<=0:raise ValueError('positive finite tolerance/budget')
 return p,inp

def estimate(p,inp):
 c=len(inp['candidates']);s=len(inp['responses']);n=len(inp['source_nodes_m'])
 return {'forward_calls_upper':c*s*len(p['panel_levels']),'rational_panel_visits_upper':4*n*c*s*sum(p['panel_levels']),'upper_includes_upstream_and_response':True,'continuous_source_validation':False,'historical_point2_point12_run':False}

def execute(p,inp,output):
 if p['execution_mode']!='explicit_authorized_run' or not p['execution_authorized'] or not p['authorization_evidence'].strip() or not p['host_access_confirmed'] or not p['device_label'].strip():raise ValueError('renewed_authorization_and_restored_host_access_required')
 if not output:raise ValueError('fresh external output required')
 dest=Path(output).resolve()
 if dest.is_relative_to(R):raise ValueError('cannot overwrite frozen research package')
 e=estimate(p,inp)
 if e['forward_calls_upper']>p['max_forward_calls'] or e['rational_panel_visits_upper']>p['max_total_panels']:raise ValueError('preflight_resource_budget_exceeded')
 dest.mkdir(parents=True,exist_ok=False);start=time.monotonic();records=[];status='budget_exhausted_or_unresolved';calls=0
 (dest/'run_plan.json').write_text(json.dumps(p,indent=2)+'\n')
 def checkpoint():
  rec={'status':status,'plan_sha256':digest(p),'input_sha256':digest(inp),'code_sha256':code_hashes(),'python':platform.python_version(),'elapsed_seconds':time.monotonic()-start,'completed_forward_calls':calls,'records':records,'formal_model_chain':'pending','point12':'partial_unchanged','point2':'conditional_non_strict_unchanged','physical_qualification':False,'wall_enforcement':'between bounded calls; not hard realtime'}
  t=dest/'checkpoint.tmp';t.write_text(json.dumps(rec,indent=2,allow_nan=False)+'\n');t.replace(dest/'checkpoint.json');return rec
 try:
  for level in p['panel_levels']:
   row={'panels':level,'scenarios':{}};records.append(row);all_resolved=True
   for name,params in inp['responses'].items():
    outs=[];row['scenarios'][name]={'outputs':outs,'comparison':None,'criterion_met':False}
    for scene in inp['candidates']:
     if time.monotonic()-start>=p['max_wall_seconds']:raise InterruptedError('wall_budget_partial')
     if (dest/'CANCEL').exists():raise InterruptedError('cancelled_partial')
     outs.append(forward(Scene(**scene),Response(**params),inp['source_nodes_m'],inp['source_weights'],inp['target_m'],level));calls+=1;checkpoint()
    relation=compare(outs[0],outs[1]);width=[]
    for x in outs:
     h=x['signed_thickness_change_m'];width.append(None if h is None else (h[1]-h[0])/inp['target_m'])
    resolved=relation['relation']!='unresolved' and all(x is not None and x<=p['relative_thickness_tolerance'] for x in width)
    row['scenarios'][name]={'outputs':outs,'comparison':relation,'relative_interval_width':width,'criterion_met':resolved};all_resolved &= resolved
   checkpoint()
   if all_resolved and p['stop_when_resolved']:status='bounded_criteria_met';break
   if level==p['panel_levels'][-1] and all_resolved:status='bounded_criteria_met'
 except (InterruptedError,ValueError,OverflowError) as e:status=str(e)
 result=checkpoint();(dest/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');return result
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--plan',default=str(R/'data/device_validation_plan.json'));ap.add_argument('--run',action='store_true');ap.add_argument('--output');a=ap.parse_args()
 try:
  p,inp=load(a.plan)
  result=execute(p,inp,a.output) if a.run else {'status':'plan_only_no_execution','plan':p,'work_estimate':estimate(p,inp),'host_permission_state':'unrestored_not_probed','formal_model_chain':'pending'}
  print(json.dumps(result,indent=2,allow_nan=False))
 except (ValueError,OSError) as e:print(json.dumps({'status':'blocked','reason':str(e)}));raise SystemExit(2)
