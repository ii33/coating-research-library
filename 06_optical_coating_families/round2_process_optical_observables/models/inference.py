"""Bounded synthetic identification, local sensitivities and covariance propagation.
No optimizer result is validation. No implicit missing-parameter defaults.
"""
import copy
import numpy as np
from scipy.optimize import least_squares
from jsonschema.exceptions import ValidationError
from process_optics import evaluate, set_parameter, Blocked

def predicted(record,names,values,channels):
 r=copy.deepcopy(record)
 for n,v in zip(names,values):r=set_parameter(r,n,float(v))
 out=evaluate(r)
 if out['status']!='conditional_calculation':raise Blocked(out['reason'])
 return np.concatenate([out['observables'][c] for c in channels])

def sensitivity(record,parameters,channels):
 names=[p['name'] for p in parameters]; x=np.array([p['nominal'] for p in parameters]);steps=np.array([p['step'] for p in parameters])
 if not np.all(np.isfinite(steps)) or np.any(steps<=0):raise ValueError('positive finite finite-difference steps required')
 y=predicted(record,names,x,channels); J=np.empty((len(y),len(x)))
 for j,h in enumerate(steps):
  xp=x.copy();xm=x.copy();xp[j]+=h;xm[j]-=h
  J[:,j]=(predicted(record,names,xp,channels)-predicted(record,names,xm,channels))/(2*h)
 # Dimensionless coordinates: derivatives wrt log-scale-like fractional perturbations.
 scales=np.array([max(abs(p['nominal']),p['step']) for p in parameters])
 scaled=J*scales
 sv=np.linalg.svd(scaled,compute_uv=False)
 tol=max(scaled.shape)*np.finfo(float).eps*(sv[0] if len(sv) else 0)
 rank=int(sum(sv>tol))
 return {'nominal':y.tolist(),'jacobian':J.tolist(),'column_scales':scales.tolist(),'scaled_singular_values':sv.tolist(),'rank':rank,'parameter_count':len(x),'nullity_at_least':len(x)-rank,'condition_number':None if rank<len(x) else float(sv[0]/sv[-1]),'scope':'local derivative rank only; neither global uniqueness nor practical noise identifiability'}

def covariance_check(cov,n):
 cov=np.array(cov,float)
 if cov.shape!=(n,n) or np.any(~np.isfinite(cov)) or not np.allclose(cov,cov.T,atol=1e-14,rtol=0):raise ValueError('finite symmetric covariance required')
 if np.min(np.linalg.eigvalsh(cov)) < -1e-13:raise ValueError('covariance must be PSD')
 return cov

def propagate(record,parameters,channels,covariance,samples=0,seed=31):
 s=sensitivity(record,parameters,channels);cov=covariance_check(covariance,len(parameters));J=np.array(s['jacobian']); outcov=J@cov@J.T
 result={'local':s,'linear_output_covariance':outcov.tolist(),'linear_standard_uncertainty':np.sqrt(np.maximum(np.diag(outcov),0)).tolist(),'covariance_scope':'supplied parameter uncertainty only; excludes unknown source, process, model and calibration errors','monte_carlo':{'status':'not_run'}}
 if samples:
  if not isinstance(samples,int) or samples<2:raise ValueError('at least two Monte Carlo samples required')
  rng=np.random.default_rng(seed);x=[p['nominal'] for p in parameters];names=[p['name'] for p in parameters]
  draws=rng.multivariate_normal(x,cov,size=samples);ys=[];fail=[]
  for i,v in enumerate(draws):
   try:ys.append(predicted(record,names,v,channels))
   except (ValueError,Blocked,ValidationError) as e:fail.append({'draw':i,'reason':str(e)})
  result['monte_carlo']={'status':'completed_with_domain_failures' if fail else 'completed','requested':samples,'valid':len(ys),'failures':fail,'mean_conditional_on_valid':np.mean(ys,axis=0).tolist() if ys else None,'covariance_conditional_on_valid':np.atleast_2d(np.cov(np.array(ys),rowvar=False)).tolist() if len(ys)>1 else None,'warning':'invalid draws are reported, never silently clipped; conditional statistics not full uncertainty if any fail'}
 return result

def fit_synthetic(record,channels,observed,sigma,names,x0,lower,upper):
 """Small bounded demonstration. Real calibration requires user-supplied measured
 data and independent state/domain evidence; this API deliberately refuses it.
 """
 if record['evidence_kind']!='synthetic':raise Blocked('fit_synthetic cannot calibrate literature or production films')
 if record['optical_model']['kind']!='synthetic_cauchy':raise Blocked('only explicit synthetic Cauchy model fitted')
 y=np.asarray(observed,float);sig=np.asarray(sigma,float)
 if y.ndim!=1 or sig.shape!=y.shape or np.any(sig<=0) or np.any(~np.isfinite(y)) or np.any(~np.isfinite(sig)):raise ValueError('finite observations and positive sigma per channel required')
 lo=np.asarray(lower,float);hi=np.asarray(upper,float)
 if len(names)!=len(lo) or len(lo)!=len(hi) or np.any(~np.isfinite(lo)) or np.any(~np.isfinite(hi)) or np.any(lo>=hi):raise ValueError('strict finite parameter bounds required')
 def fun(x):return (predicted(record,names,x,channels)-y)/sig
 fit=least_squares(fun,x0,bounds=(lo,hi),max_nfev=120,xtol=1e-12,ftol=1e-12,gtol=1e-12)
 sv=np.linalg.svd(fit.jac,compute_uv=False);rank=int(np.linalg.matrix_rank(fit.jac))
 return {'success':bool(fit.success),'parameters':dict(zip(names,fit.x.tolist())),'weighted_residual_norm':float(np.linalg.norm(fit.fun)),'unweighted_rms':float(np.sqrt(np.mean((fit.fun*sig)**2))),'jacobian_rank':rank,'nullity_at_least':len(names)-rank,'singular_values':sv.tolist(),'evaluations':fit.nfev,'source_domain_id':record['optical_model']['valid_state_id'],'wavelength_domain_um':record['optical_model']['wavelength_range_um'],'validated_on_independent_measurements':False,'meaning':'fit is conditional description, not proof of process response, uniqueness or model correctness'}
