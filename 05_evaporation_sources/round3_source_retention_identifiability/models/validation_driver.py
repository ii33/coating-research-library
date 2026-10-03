"""Bounded synthetic repeated-design validation. Default plan_only. No remote I/O.
Running requires a fresh externally authorized plan and fresh output directory.
"""
from source_retention import *
from diagnostics import design
from scipy.optimize import least_squares
import argparse,time,platform
LOW=np.array([math.log(1e-10),0.,-.95,math.log(.01),math.log(.01),0.,math.log(100.)])
HIGH=np.array([math.log(1e-2),12.,.95,0.,0.,1.,math.log(20000.)])

def fit(rows,observed,sigma_log,initial):
 observed=np.asarray(observed,dtype=float);sig=np.asarray(sigma_log,dtype=float)
 if observed.shape!=(len(rows),) or sig.shape!=observed.shape or not np.all(np.isfinite(observed)) or not np.all(np.isfinite(sig)) or min(observed)<=0 or min(sig)<=0:raise ValueError('positive finite observations and log sigma required')
 J=log_jacobian(rows,initial)
 if not rank_report(J,sig)['full_column_rank']:raise ValueError('rank_deficient_do_not_fit')
 z0=initial.vector()
 if np.any(z0<=LOW) or np.any(z0>=HIGH):raise ValueError('strict interior initial required')
 def residual(z):return (np.log([prediction(x,Parameters.from_vector(z)) for x in rows])-np.log(observed))/sig
 def jac(z):return log_jacobian(rows,Parameters.from_vector(z))/sig[:,None]
 sol=least_squares(residual,z0,jac=jac,bounds=(LOW,HIGH),loss='linear',max_nfev=100,ftol=1e-10,xtol=1e-10,gtol=1e-10)
 out=Parameters.from_vector(sol.x);rr=rank_report(log_jacobian(rows,out),sig);cov=None
 if sol.success and rr['full_column_rank'] and not any(sol.active_mask):cov=np.linalg.inv(sol.jac.T@sol.jac).tolist()
 return {'parameters':asdict(out),'success':bool(sol.success),'nfev':int(sol.nfev),'active_mask':sol.active_mask.tolist(),'weighted_residuals':sol.fun.tolist(),'rank':rr,'local_log_parameter_covariance':cov,'covariance_scope':'known independent synthetic log noise; interior local linear approximation only','production_qualified':False}

def load(path):
 p=json.loads(Path(path).read_text());wanted={'schema_version','mode','authorized','authorization_evidence','host_access_confirmed','device_label','input_sha256','replicates','noise_log_sigma','seed','max_fits','max_wall_seconds'}
 if set(p)!=wanted or p['schema_version']!='T05-r3-source-retention-plan-1':raise ValueError('exact plan keys')
 if p['mode'] not in ('plan_only','explicit_authorized_run'):raise ValueError('mode')
 for k in ('authorized','host_access_confirmed'):
  if type(p[k]) is not bool:raise ValueError('strict bool')
 for k in ('authorization_evidence','device_label'):
  if not isinstance(p[k],str):raise ValueError('string')
 for k in ('replicates','max_fits','seed'):
  if type(p[k]) is not int or p[k]<(0 if k=='seed' else 1):raise ValueError('integer budget')
 if p['replicates']>p['max_fits'] or p['replicates']>10000:raise ValueError('fit budget exceeded')
 positive(p['noise_log_sigma']);positive(p['max_wall_seconds'])
 inp=json.loads((R/'data/driver_inputs.json').read_text())
 if p['input_sha256']!=digest(inp):raise ValueError('input hash mismatch')
 if inp.get('dataset_kind')!='synthetic' or set(inp)!={'dataset_kind','truth','initial','observations'}:raise ValueError('synthetic frozen input only')
 return p,inp

def execute(p,inp,output):
 if p['mode']!='explicit_authorized_run' or not p['authorized'] or not p['authorization_evidence'].strip() or not p['host_access_confirmed'] or not p['device_label'].strip():raise ValueError('renewed_authorization_and_restored_host_access_required')
 if not output:raise ValueError('fresh external output required')
 dest=Path(output).resolve()
 if dest.is_relative_to(R):raise ValueError('do_not_mutate_frozen_package')
 dest.mkdir(parents=True,exist_ok=False);start=time.monotonic();rng=np.random.default_rng(p['seed']);records=[];status='running'
 def checkpoint():
  x={'status':status,'plan_sha256':digest(p),'input_sha256':digest(inp),'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'model_sha256':hashlib.sha256((R/'models/source_retention.py').read_bytes()).hexdigest(),'python':platform.python_version(),'completed_fits':len(records),'elapsed_seconds':time.monotonic()-start,'records':records,'formal_model_chain':'pending','real_data':'not_used','heavy_geometry':'not_executed','point12':'partial_unchanged','point2':'conditional_non_strict_unchanged','wall_enforcement':'between bounded fits; each fit max_nfev=100; not hard realtime'}
  tmp=dest/'checkpoint.tmp';tmp.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');tmp.replace(dest/'checkpoint.json');return x
 (dest/'run_plan.json').write_text(json.dumps(p,indent=2)+'\n')
 try:
  truth=Parameters(**inp['truth']);initial=Parameters(**inp['initial']);rows=inp['observations'];clean=np.array([prediction(x,truth) for x in rows]);sig=np.full(len(rows),p['noise_log_sigma'])
  for i in range(p['replicates']):
   if (dest/'CANCEL').exists():status='cancelled_partial';break
   if time.monotonic()-start>=p['max_wall_seconds']:status='wall_budget_partial';break
   obs=clean*np.exp(rng.normal(0,sig));records.append({'replicate':i,'observations':obs.tolist(),'fit':fit(rows,obs,sig,initial)});checkpoint()
  else:status='synthetic_replicates_complete' if all(x['fit']['success'] for x in records) else 'completed_with_fit_failures'
 except (ValueError,OverflowError,np.linalg.LinAlgError) as e:status='blocked_partial:'+str(e)
 x=checkpoint();(dest/'results.json').write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');return x

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--plan',default=str(R/'data/device_validation_plan.json'));a.add_argument('--run',action='store_true');a.add_argument('--output');args=a.parse_args()
 try:
  p,inp=load(args.plan);result=execute(p,inp,args.output) if args.run else {'status':'plan_only_no_execution','plan':p,'planned_fit_count':p['replicates'],'observation_count':len(inp['observations']),'upper_objective_evaluations':100*p['replicates'],'host_permissions':'unrestored_not_probed','formal_model_chain':'pending'}
  print(json.dumps(result,indent=2,allow_nan=False))
 except (ValueError,OSError) as e:print(json.dumps({'status':'blocked','reason':str(e)}));raise SystemExit(2)
