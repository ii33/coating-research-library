"""Complete bounded job driver. Default is read-only plan_only; never starts hardware.
A future full plan needs explicit mode, plan, sufficient budgets and a NEW output path.
"""
import argparse,json,sys,time
from candidate_sets import *

def make_plan(name='tiny'):
 if name not in ('tiny','full'):raise ValueError('unknown_plan')
 jobs=[]
 if name=='tiny':
  jobs=[{'id':'plane_M0_63','channels':['M0'],'max_nodes':63,'v':None},{'id':'plane_joint_255','channels':['M0','M1'],'max_nodes':255,'v':None},{'id':'outer10_joint_31','channels':['M0','M1'],'max_nodes':31,'v':'1.1'},{'id':'zero_budget','channels':['M0','M1'],'max_nodes':0,'v':None}]
 else:
  jobs=[{'id':f'plane_{label}_{n}','channels':chs,'max_nodes':n,'v':None} for label,chs in [('M0',['M0']),('joint',['M0','M1'])] for n in [127,511,2047,8191]]
 nodes=sum(q['max_nodes'] for q in jobs);interval=sum(q['max_nodes']*(3 if q['channels']==['M0'] else 4) for q in jobs)+4
 return {'stage':'T08R3','plan':name,'jobs':jobs,'min_width':['0.0004','0.002'],'required_caps':{'max_nodes':nodes,'max_interval_wavelengths':interval,'max_float_vectors':10},'searches':[{'id':'nominal_start','calls':9},{'id':'deliberate_miss','calls':1}],'point_validation_count':1,'default_mode':'plan_only','devices':0,'monte_carlo_draws':0,'infinite_dimensional_extension':False,'quota_bypass':False,'resume':'not_implemented; fresh output only','full_execution_status':'not_run'}

def run_plan(c,k,plan,ledger,out):
 out=Path(out).resolve()
 if ROOT not in out.parents or out.exists():raise ValueError('new_output_directory_inside_package_required')
 out.mkdir(parents=True);start=time.monotonic();runs=[]
 def save(name,v):(out/name).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
 save('plan.json',plan)
 good=finite_search(c,k,max_calls=9,ledger=ledger);bad=finite_search(c,k,start=(str(domain(c,k).zlo),'0.9'),max_calls=1,ledger=ledger)
 save('searches.json',{'nominal_start':good,'deliberate_miss':bad})
 hint=good['best_hint'];witnesses=[]
 if hint:witnesses.append(validate_point(c,k,*hint['point_exact'],ledger=ledger))
 save('witnesses.json',witnesses)
 for job in plan['jobs']:
  result=screen(c,k,selected=job['channels'],max_nodes=job['max_nodes'],min_width=plan['min_width'],box=domain(c,k,job['v']),ledger=ledger)
  result['job_id']=job['id'];result['retained_v_projection_exact']=project_retained_v(result);result['optimization']=optimize_bounds(k,result,witnesses)
  save(job['id']+'.json',result);runs.append(result);save('progress.json',{'completed_jobs':[r['job_id'] for r in runs],'ledger':ledger.snapshot(),'state':'running'})
 summary={'stage':'T08R3','plan':plan['plan'],'candidate_contract_sha256':digest(k),'parent_case_payload_sha256':digest(c),'derived_observation_contract_sha256':c['derived_observation_contract_sha256'],'runs':[{key:r[key] for key in ['job_id','channels','counts','data_evidence_state','evaluated_nodes','charged','retained_v_projection_exact','optimization']} for r in runs],'search_states':{'nominal_start':good['search_state'],'deliberate_miss':bad['search_state']},'witnesses':witnesses,'ledger':ledger.snapshot(),'elapsed_seconds':time.monotonic()-start,'complete_job_loop':True,'full_run':plan['plan']=='full','physical_certification':False,'point12':'partial_unchanged','point2':'conditional_non_strict_unchanged','formal_model_chain':'pending'}
 save('summary.json',summary);save('progress.json',{'completed_jobs':[r['job_id'] for r in runs],'ledger':ledger.snapshot(),'state':'completed'});return summary

def main():
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=['plan_only','execute'],default='plan_only');p.add_argument('--plan',choices=['tiny','full'],default='full');p.add_argument('--max-nodes',type=int);p.add_argument('--max-interval-wavelengths',type=int);p.add_argument('--max-float-vectors',type=int);p.add_argument('--output');a=p.parse_args();c,k=load();plan=make_plan(a.plan)
 if a.mode=='plan_only':print(json.dumps({'mode':'plan_only','executed':False,'contract_sha256':digest(k),'plan':plan},indent=2));return
 supplied={'max_nodes':a.max_nodes,'max_interval_wavelengths':a.max_interval_wavelengths,'max_float_vectors':a.max_float_vectors}
 if not a.output or any(supplied[key] is None or supplied[key]<n for key,n in plan['required_caps'].items()):p.error('Execution needs a new output directory and all explicit caps >= required worst-case counts')
 ledger=Ledger(**supplied);summary=run_plan(c,k,plan,ledger,a.output);print(json.dumps({key:summary[key] for key in ['plan','ledger','elapsed_seconds','search_states']},indent=2))
if __name__=='__main__':main()
