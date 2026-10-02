"""Complete synthetic multistation/time-series validation, default PLAN ONLY.
No physical device, external API, cloud jobs or paid computation. Heavy run is not executed.
Resume uses config hash and deterministic replicate RNG; atomic per-replicate checkpoints.
"""
from pathlib import Path
import argparse,json,hashlib,time,os
import numpy as np
from qcm_flux import point_kernel, frequency_from_mass,rate_from_frequency,fit_source
R=Path(__file__).resolve().parents[1]
DEFAULT={'replicates':1000,'windows':120,'monitors':12,'samples_per_window':11,'window_seconds':20.,'seed':73051,
         'cases':['nominal','correlated_drift','sensor_obscuration','single_outlier'],
         'noise_hz':.05,'drift_error_std_hz_s':.08,'production_validation':False}

def write_atomic(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n');os.replace(tmp,p)

def plan(cfg):
 # Conservative planning proxy, NOT timed device benchmark or reservation.
 fits=cfg['replicates']*cfg['windows']*len(cfg['cases']);samples=fits*cfg['monitors']*cfg['samples_per_window']
 return {'status':'plan_only','device_validation':'not_run','config':cfg,'fit_count':fits,'qcm_sample_count':samples,
         'planning_bounds':{'cpu_seconds_assumed_per_window_fit_and_qcm': [.02,2.],
          'single_core_hours_interval':[fits*.02/3600,fits*2/3600],
          'peak_memory_bytes_estimate':int(max(64e6,cfg['monitors']*cfg['samples_per_window']**2*8*20)),
          'checkpoint_disk_bytes_estimate':int(cfg['replicates']*cfg['windows']*len(cfg['cases'])*2000)},
         'estimate_basis':'algorithmic workload + explicit unmeasured time/memory allowances; not hardware sampling',
         'resume':'one deterministic replicate file per case; skip only matching configuration + qcm_flux/driver source hash completed file',
         'acceptance':'synthetic implementation diagnostics only; independent actual flux/species/geometry calibration remains absent'}

def positions(count):
 theta=np.linspace(.08,.68,count);phi=np.arange(count)*2.399963229728653
 x=np.c_[.5*np.tan(theta)*np.cos(phi),.5*np.tan(theta)*np.sin(phi),np.full(count,.5)]
 return x,np.tile([0.,0.,-1.],(count,1))

def run_replicate(cfg,rep,case):
 rng=np.random.default_rng(cfg['seed']+rep*100+cfg['cases'].index(case));x,norm=positions(cfg['monitors']);
 hold=np.array([[.18,.24,.65],[-.30,.1,.65]]);hn=np.tile([0,0,-1],(2,1)); eta=.92; f0=6045000.;z=1.08
 frames=[];cum=np.full(len(x),1e-5);integrated_true=np.zeros(2);integrated_pred=np.zeros(2)
 for w in range(cfg['windows']):
  phase=2*np.pi*w/max(cfg['windows'],1);Q=2e-6*(1+.15*np.sin(phase)); n=2.4+.3*np.cos(phase);a=.25+.1*np.sin(phase)
  vis=np.ones(len(x));
  if case=='sensor_obscuration':vis[0]=.15 # deliberately unmodeled shadow counterexample
  rate=Q*point_kernel(x,norm,n,a,vis)*eta;t=np.linspace(0,cfg['window_seconds'],cfg['samples_per_window']);slopes=[];sds=[]
  common_error=rng.normal(0,cfg['drift_error_std_hz_s']) if case=='correlated_drift' else 0.
  for j in range(len(x)):
   m=cum[j]+rate[j]*t;known_drift=.15*t
   raw=frequency_from_mass(m,f0,z)+known_drift+common_error*t+rng.normal(0,cfg['noise_hz'],len(t))
   r=rate_from_frequency(t,raw,f0,drift_hz=known_drift,frequency_covariance_hz2=np.eye(len(t))*cfg['noise_hz']**2,z_ratio=z)
   slopes.append(r['slope_kg_m2_s']);sds.append(r['slope_std_kg_m2_s']);cum[j]=m[-1]
  y=np.array(slopes);sd=np.array(sds)/y
  if case=='single_outlier':y[0]*=1.2
  if np.any(y<=0):
   frames.append({'window':w,'status':'blocked_nonpositive_mass_slope'});continue
  loss='linear' if case=='nominal' else 'soft_l1'
  fit=fit_source(x,norm,y,sd,capture=eta,loss=loss)
  pred=fit['Q_kg_s']*point_kernel(hold,hn,fit['n'],fit['a']);true=Q*point_kernel(hold,hn,n,a)
  integrated_pred+=pred*cfg['window_seconds'];integrated_true+=true*cfg['window_seconds']
  cov=fit['covariance'];inside=None
  if cov is not None:
   p=np.array(fit['parameters_logQ_n_a_logeta']);truth=np.array([np.log(Q),n,a]);inside=(np.abs(p-truth)<=1.96*np.sqrt(np.diag(cov))).tolist()
  frames.append({'window':w,'status':'computed','truth':[Q,n,a],'fit':[fit['Q_kg_s'],fit['n'],fit['a']],
                 'holdout_relative_error':(pred/true-1).tolist(),'conditional_95pct_parameter_coverage':inside,'rank':fit['rank'],'active_bound':fit['active_bound']})
 valid=[f for f in frames if f['status']=='computed']
 err=np.array([f['holdout_relative_error'] for f in valid])
 coverage=[f['conditional_95pct_parameter_coverage'] for f in valid if f['conditional_95pct_parameter_coverage'] is not None]
 return {'replicate':rep,'case':case,'status':'completed','frames':frames,
         'summary':{'valid_windows':len(valid),'total_windows':cfg['windows'],'max_abs_holdout_relative_error':None if not len(valid) else float(np.max(np.abs(err))),
                    'integrated_mass_holdout_relative_error':None if not len(valid) else (integrated_pred/integrated_true-1).tolist(),
                    'conditional_coverage_mean':None if not coverage else np.mean(coverage,axis=0).tolist()},
         'model_error_warning':'challenge cases deliberately violate modeled drift/visibility/noise; intervals cannot absorb unmodeled bias'}

def execute(cfg,out,resume=True,max_replicates=None):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);implementation={name:hashlib.sha256((R/'models'/name).read_bytes()).hexdigest() for name in ['qcm_flux.py','validation_driver.py']};digest=hashlib.sha256(json.dumps({'config':cfg,'implementation':implementation},sort_keys=True).encode()).hexdigest(); summaries=[];parameter_samples={case:[] for case in cfg['cases']};started=time.monotonic()
 for case in cfg['cases']:
  for rep in range(cfg['replicates'] if max_replicates is None else min(cfg['replicates'],max_replicates)):
   p=out/f'{case}_{rep:06d}.json'
   if p.exists() and resume:
    result=json.loads(p.read_text())
    if result.get('config_sha256')!=digest or result.get('status')!='completed':raise ValueError('checkpoint/config mismatch; choose separate output directory')
   else:
    result=run_replicate(cfg,rep,case);result['config_sha256']=digest;write_atomic(p,result)
   parameter_samples[case].append([f['fit'] for f in result['frames'] if f['status']=='computed'])
   summaries.append({'case':case,'replicate':rep,**result['summary']})
   write_atomic(out/'progress.json',{'status':'running','completed_case_replicates':len(summaries),'config_sha256':digest,'last_file':p.name})
 # Quantiles of repeated noisy estimates, conditional on a synthetic scenario, not real calibrated posterior.
 quantiles={}
 for case in cfg['cases']:
  vals=[s['max_abs_holdout_relative_error'] for s in summaries if s['case']==case and s['max_abs_holdout_relative_error'] is not None]
  quantiles[case]=None if not vals else np.quantile(vals,[.025,.5,.975]).tolist()
 parameter_quantiles={}
 for case,values in parameter_samples.items():
  complete=[v for v in values if len(v)==cfg['windows']]
  parameter_quantiles[case]=None if not complete else np.quantile(np.array(complete),[.025,.5,.975],axis=0).tolist()
 result={'status':'completed','config_sha256':digest,'implementation_sha256':implementation,'config':cfg,'elapsed_seconds':time.monotonic()-started,
         'summaries':summaries,'max_error_empirical_quantiles':quantiles,'parameter_Q_n_a_quantiles_by_window':parameter_quantiles,'quantile_warning':'empirical across synthetic noisy repetitions; no coverage or actual-calibration guarantee, especially with one light repetition','heavy_device_validation':'not_run','actual_calibration':'not_run'}
 write_atomic(out/'progress.json',result);return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=['plan','light','heavy'],default='plan');p.add_argument('--output',type=Path);p.add_argument('--execute',action='store_true');p.add_argument('--acknowledge-synthetic-only',action='store_true');args=p.parse_args();cfg=dict(DEFAULT)
 if args.mode=='plan':
  result=plan(cfg)
  if args.output:write_atomic(args.output,result)
 elif args.mode=='light':
  cfg.update(replicates=1,windows=3,monitors=8);result=execute(cfg,args.output or R/'verification/light_driver')
 else:
  if not(args.execute and args.acknowledge_synthetic_only):p.error('heavy needs --execute --acknowledge-synthetic-only and separate resource authorization')
  if args.output is None:p.error('heavy requires explicit checkpoint directory')
  result=execute(cfg,args.output)
 print(json.dumps(result,indent=2,allow_nan=False))
