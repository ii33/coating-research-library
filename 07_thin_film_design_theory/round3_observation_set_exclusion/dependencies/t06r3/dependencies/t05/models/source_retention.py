"""SI, synthetic diagnostic model. Frozen T04 full-forward is only reached by
an explicit Lambert bridge. No instrument, remote, or real-material calibration.
"""
from dataclasses import dataclass,asdict,replace
from pathlib import Path
import hashlib,json,math,sys
import numpy as np
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'dependencies/t04/models'))
import bounded_response as t04

def digest(x):
 return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def finite(x):
 if isinstance(x,bool) or not isinstance(x,(int,float,np.floating)) or not math.isfinite(x):raise ValueError('finite numeric required')
 return float(x)
def positive(x):
 x=finite(x)
 if x<=0:raise ValueError('positive required')
 return x
def cosine(x):
 x=finite(x)
 if not -1<=x<=1:raise ValueError('cosine domain')
 return x

def angular_pdf(mu,phi,n,c=0.):
 """Per steradian, hemisphere-normalized; includes emission cosine if n=1."""
 mu=cosine(mu);phi=finite(phi);n=finite(n);c=finite(c)
 if n<0 or abs(c)>=1:raise ValueError('n>=0 and |c|<1 required')
 if mu<=0:return 0.
 return (n+1)/(2*math.pi)*mu**n*(1+c*(1-mu*mu)*math.cos(2*phi))

def retained_fraction(mu,s0,a):
 mu=cosine(mu);s0=finite(s0);a=finite(a)
 if not 0<=s0<=1 or not 0<=a<=1:raise ValueError('retention coefficients outside [0,1]')
 return s0*(1-a*(1-mu*mu)) if mu>0 else 0.

def point_incident(Q,mu_s,mu_i,r,phi,n,c=0.,visibility=1.):
 Q=finite(Q);r=positive(r);visibility=finite(visibility);mu_i=cosine(mu_i)
 if Q<0 or not 0<=visibility<=1:raise ValueError('nonnegative Q, visibility in [0,1]')
 return Q*angular_pdf(mu_s,phi,n,c)*max(mu_i,0)/r**2*visibility

def normalized_weights(weights):
 w=[finite(x) for x in weights]
 if not w or min(w)<0 or not math.isclose(math.fsum(w),1.,rel_tol=0,abs_tol=1e-12):raise ValueError('weights must be nonnegative normalized mass fractions; no area or pi folded in')
 return w

def finite_incident(Q,nodes,weights,target,target_normal,n,c=0.,visible=None):
 """Nodes: position, normal, tangent1. Weights already include source area.
 Positive mass quadrature only; visibility applied once, no renormalization.
 """
 w=normalized_weights(weights)
 if len(nodes)!=len(w):raise ValueError('paired nodes and weights')
 x=np.asarray(target,dtype=float);nx=np.asarray(target_normal,dtype=float)
 def unit(v):
  v=np.asarray(v,dtype=float)
  if v.shape!=(3,) or not np.all(np.isfinite(v)) or not np.isclose(np.linalg.norm(v),1.,atol=1e-12,rtol=0):raise ValueError('finite unit vectors required')
  return v
 nx=unit(nx)
 if x.shape!=(3,) or not np.all(np.isfinite(x)):raise ValueError('finite position')
 if visible is None:visible=[1.]*len(nodes)
 if len(visible)!=len(nodes):raise ValueError('visibility length')
 out=[]
 for node,wk,V in zip(nodes,w,visible):
  ns=unit(node['normal']);e1=unit(node['tangent1']);p=np.asarray(node['position'],dtype=float)
  if p.shape!=(3,) or not np.all(np.isfinite(p)) or abs(float(np.dot(ns,e1)))>1e-12:raise ValueError('node frame')
  u=x-p;r=positive(float(np.linalg.norm(u)));u=u/r;e2=np.cross(ns,e1)
  phi=math.atan2(float(np.dot(u,e2)),float(np.dot(u,e1)))
  out.append(wk*point_incident(Q,float(np.clip(np.dot(ns,u),-1,1)),float(np.clip(-np.dot(nx,u),-1,1)),r,phi,n,c,V))
 return math.fsum(out)

@dataclass(frozen=True)
class Parameters:
 Q_kg_s:float=2e-6
 n:float=1.7
 c:float=.2
 eta_q:float=.8
 s0:float=.7
 a:float=.4
 rho_kg_m3:float=2000.
 def validate(self):
  positive(self.Q_kg_s);positive(self.rho_kg_m3);angular_pdf(1.,0.,self.n,self.c)
  if not 0<finite(self.eta_q)<=1 or not 0<finite(self.s0)<=1:raise ValueError('positive eta and s0 in log model')
  retained_fraction(1.,self.s0,self.a)
  return self
 def vector(self):
  self.validate();return np.array([math.log(self.Q_kg_s),self.n,self.c,math.log(self.eta_q),math.log(self.s0),self.a,math.log(self.rho_kg_m3)])
 @classmethod
 def from_vector(cls,z):return cls(math.exp(z[0]),z[1],z[2],math.exp(z[3]),math.exp(z[4]),z[5],math.exp(z[6])).validate()

PARAMETER_NAMES=['log_Q','n','c','log_eta_q','log_s0','a','log_rho']
def prediction(row,p):
 p.validate();kind=row['kind']
 if kind=='source_mass_rate':return p.Q_kg_s
 if kind=='film_density':return p.rho_kg_m3
 if kind not in ('qcm_mass_rate','witness_mass_rate','witness_thickness_rate'):raise ValueError('unsupported observation')
 j=point_incident(p.Q_kg_s,row['mu_s'],row['mu_i'],row['r_m'],row['phi_rad'],p.n,p.c,row.get('visibility',1.))
 if kind=='qcm_mass_rate':return j*p.eta_q
 j*=retained_fraction(row['mu_i'],p.s0,p.a)
 return j/p.rho_kg_m3 if kind=='witness_thickness_rate' else j

def log_jacobian(rows,p):
 """Derivative log(observable)/d(logQ,n,c,logeta,logs0,a,logrho)."""
 p.validate();J=[]
 for row in rows:
  if prediction(row,p)<=0:raise ValueError('zero_or_negative_data_no_log_fit')
  kind=row['kind'];v=np.zeros(7)
  if kind=='source_mass_rate':v[0]=1
  elif kind=='film_density':v[6]=1
  else:
   ms=positive(row['mu_s']);mi=positive(row['mu_i']);b=(1-ms*ms)*math.cos(2*row['phi_rad'])
   v[0]=1;v[1]=1/(p.n+1)+math.log(ms);v[2]=b/(1+p.c*b)
   if kind=='qcm_mass_rate':v[3]=1
   else:
    v[4]=1;v[5]=-(1-mi*mi)/(1-p.a*(1-mi*mi))
    if kind=='witness_thickness_rate':v[6]=-1
  J.append(v)
 return np.asarray(J)

def rank_report(J,sigma_log=None,column_scales=None):
 J=np.asarray(J,dtype=float)
 if J.ndim!=2 or min(J.shape)==0 or not np.all(np.isfinite(J)):raise ValueError('finite nonempty matrix')
 s=np.ones(J.shape[0]) if sigma_log is None else np.asarray(sigma_log,dtype=float)
 c=np.ones(J.shape[1]) if column_scales is None else np.asarray(column_scales,dtype=float)
 if s.shape!=(J.shape[0],) or c.shape!=(J.shape[1],) or not np.all(np.isfinite(s)) or not np.all(np.isfinite(c)) or min(s)<=0 or min(c)<=0:raise ValueError('positive declared noise/scales')
 A=J/s[:,None]*c[None,:];sv=np.linalg.svd(A,compute_uv=False);tol=max(A.shape)*np.finfo(float).eps*sv[0];rank=int(sum(sv>tol))
 return {'rows':len(J),'columns':J.shape[1],'rank':rank,'singular_values':sv.tolist(),'svd_tolerance':tol,'full_column_rank':rank==J.shape[1],'condition_number':float(sv[0]/sv[-1]) if rank==J.shape[1] else None,'parameter_scales':c.tolist(),'sigma_log':s.tolist(),'scope':'local necessary diagnostic, not global or physical identification'}

def paired_retention_a(m1,m2,mu1,mu2,denominator_floor=1e-10):
 """Co-located/equal-source-direction mass observations, known projections.
 No sequential-state drift, finite-area spread, or density change is corrected.
 """
 m1=positive(m1);m2=positive(m2);mu1=positive(cosine(mu1));mu2=positive(cosine(mu2));floor=positive(denominator_floor)
 ratio=(m1/mu1)/(m2/mu2);den=(1-mu1*mu1)-ratio*(1-mu2*mu2)
 if abs(den)<=floor:raise ValueError('pair_retention_denominator_unresolved')
 a=(1-ratio)/den
 if not 0<=a<=1:raise ValueError('outside_retention_family')
 return {'a':a,'projection_corrected_ratio':ratio,'denominator':den,'status':'conditional_synthetic_family_only'}

def qualify_observation(row):
 reasons=[]
 for k in ('locked','actual_visibility_known','clock_mapping_known','material_snapshot_known'):
  if row.get(k) is not True:reasons.append(k+'_not_confirmed')
 if row.get('provenance') not in ('raw_frequency_derived_mass','independent_witness_measurement'):reasons.append('substitute_or_display_not_mass_evidence')
 if row.get('feedback_coordinate') not in ('crystal_model_rate','sample_display_rate','open_loop_recorded'):reasons.append('feedback_coordinate_unknown')
 if row.get('shared_source_window') is not True:reasons.append('source_windows_not_shared')
 return {'qualified_for_conditional_diagnostic':not reasons,'reasons':reasons,'physical_calibration':False}

def two_clocks(t_ref,source_offset_s,pose_offset_s,q0,q1,position0_m,velocity_m_s):
 vals=list(map(finite,[t_ref,source_offset_s,pose_offset_s,q0,q1,position0_m,velocity_m_s]));t,ds,dp,q0,q1,x0,v=vals
 q=q0+q1*(t+ds)
 if q<0:raise ValueError('negative_source_rate')
 return {'source_time_s':t+ds,'pose_time_s':t+dp,'relative_source_rate':q,'position_m':x0+v*(t+dp)}

def bridge_t04(scene,response,Q_total_bounds,n=1.,c=0.,nodes=(0.,),weights=(1.,),target_m=1e-9,panels=16):
 """Supported source is stationary normalized Lambert nodes with affine q(t).
 Upstream code is copied unchanged. Pass response source scale=None explicitly.
 """
 if response.source_scale_kg_s is not None:raise ValueError('bridge owns Q; remove duplicate response source scale')
 normalized_weights(weights)
 if scene.amplitude!=1.:raise ValueError('bridge requires amplitude 1; normalization must be explicit')
 h={x['copy']:x['sha256'] for x in json.loads((R/'data/frozen_dependencies.json').read_text())}
 for path,want in h.items():
  if hashlib.sha256((R/path).read_bytes()).hexdigest()!=want:raise ValueError('frozen_dependency_hash_mismatch:'+path)
 base={'source_contract':{'Q_total_bounds_kg_s':Q_total_bounds,'normalization':'pre_rim_hemisphere_total_mass_rate','n':n,'c':c,'nodes_m':list(nodes),'mass_weights':list(weights),'source_clock':'scene q0+q1*t_ref; pose offset affects pose only'},'copied_dependency_sha256':h,'point12':'partial_unchanged','point2':'conditional_non_strict_unchanged','physical_certification':False}
 if n is None or c is None:return dict(base,status='unknown_source_angular_law',t04_response=None)
 angular_pdf(1.,0.,n,c)
 if n!=1. or c!=0.:return dict(base,status='unsupported_non_lambert_frozen_bridge',t04_response=None)
 if Q_total_bounds is None:coef=None
 else:
  b=t04.bounds(Q_total_bounds,nonnegative=True);coef=tuple(x/math.pi for x in map(float,b))
 r=replace(response,source_scale_kg_s=coef)
 out=t04.forward(scene,r,nodes,weights,target_m,panels)
 base['t04_response']=out;base['status']=out['status'];base['bridge_contract_sha256']=digest({'source':base['source_contract'],'response_contract_sha256':out['response_contract_sha256'],'dependencies':h,'bridge_code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
 base['normalization_note']='Q_intensity=Q_total/pi exactly once in floating encoded input; inherited interval certificate is for those encoded floats, not a transcendental-pi enclosure'
 return base
