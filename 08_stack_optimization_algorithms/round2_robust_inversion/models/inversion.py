"""Budgeted finite-domain inversion. Every numerical-Jacobian forward call is counted.
The only statistical likelihood implemented is fixed-covariance Gaussian. Huber is
an explicitly basis-dependent robust estimating criterion, not automatic evidence.
"""
from dataclasses import dataclass,field
import numpy as np
from scipy.linalg import solve_triangular
from scipy.optimize import least_squares
from vendor.identifiability import whitening

class BudgetExhausted(RuntimeError):pass
@dataclass
class Ledger:
    cap:int
    vector_calls:int=0
    optical_kernel_calls:int=0
    starts:int=0
    by_purpose:dict=field(default_factory=dict)
    def consume(self,nodes=0,purpose='fit'):
        if self.vector_calls>=self.cap:raise BudgetExhausted('global forward-vector cap')
        self.vector_calls+=1;self.optical_kernel_calls+=int(nodes)
        self.by_purpose[purpose]=self.by_purpose.get(purpose,0)+1
    def as_dict(self):return {'cap':self.cap,'vector_calls':self.vector_calls,'charged_optical_kernel_calls_upper_bound':self.optical_kernel_calls,'starts':self.starts,'by_purpose':self.by_purpose}

def huber_cost(r,delta=1.5):
    r=np.asarray(r,float)
    if delta<=0 or not np.isfinite(delta):raise ValueError('positive finite robust threshold')
    a=np.abs(r);return np.where(a<=delta,.5*r*r,delta*(a-.5*delta))

def robust_residual(r,loss,delta):
    if loss=='gaussian':return r
    if loss!='huber':raise ValueError('known loss required')
    return np.sign(r)*np.sqrt(2*huber_cost(r,delta))

@dataclass
class Problem:
    model:str
    names:list
    bounds:tuple
    scales:np.ndarray
    records:list
    y:np.ndarray
    noise_cov:np.ndarray
    discrepancy_cov:np.ndarray
    forward:object
    calibration:list=field(default_factory=list)
    priors:list=field(default_factory=list)
    loss:str='gaussian'
    delta:float=1.5
    candidate_penalty:float=0.
    def __post_init__(self):
        self.y=np.asarray(self.y,float);self.scales=np.asarray(self.scales,float)
        self.bounds=tuple(np.asarray(x,float) for x in self.bounds)
        p=len(self.names);lo,hi=self.bounds
        if any(x.shape!=(p,) for x in [lo,hi,self.scales]) or np.any(lo>=hi) or np.any(self.scales<=0) or not np.isfinite(np.r_[lo,hi,self.scales,self.y]).all():raise ValueError('invalid finite parameter/data contract')
        self.noise_cov=np.asarray(self.noise_cov,float);self.discrepancy_cov=np.asarray(self.discrepancy_cov,float)
        self.L_noise=whitening(self.noise_cov)
        D=self.discrepancy_cov
        if D.shape!=self.noise_cov.shape or not np.allclose(D,D.T) or np.linalg.eigvalsh(D).min() < -1e-12:raise ValueError('PSD discrepancy covariance required')
        self.V=self.noise_cov+D;self.L=whitening(self.V)
        if self.V.shape!=(len(self.y),len(self.y)):raise ValueError('observation/covariance mismatch')
        for item in self.calibration+self.priors:
            if not 0<=item['index']<p or item['sigma']<=0 or not np.isfinite([item['mean'],item['sigma']]).all():raise ValueError('invalid independent auxiliary term')
        self.logdet_half=float(np.log(np.diag(self.L)).sum())
    def default_point(self,truth):return np.r_[truth,1.,0.,0.] if len(self.names)==6 else np.r_[truth,1.,0.]
    def predict(self,x,records,ledger,purpose):
        # Each frozen observe call computes two polarization kernels per optical quadrature node.
        nodes=sum(0 if r['kind']=='d_geo' else 2*len(r.get('spectral_nodes',[(0,1)]))*len(r.get('angle_nodes',[(0,1)])) for r in records)
        ledger.consume(nodes,purpose);return self.forward(np.asarray(x,float),records)
    def evaluate(self,x,ledger,purpose='fit'):
        pred=self.predict(x,self.records,ledger,purpose);r=solve_triangular(self.L,pred-self.y,lower=True)
        rn=solve_triangular(self.L_noise,pred-self.y,lower=True)
        data=robust_residual(r,self.loss,self.delta)
        cal=np.array([(x[q['index']]-q['mean'])/q['sigma'] for q in self.calibration])
        prior=np.array([(x[q['index']]-q['mean'])/q['sigma'] for q in self.priors])
        parts={'data_loss':float(.5*data@data),'calibration_loss':float(.5*cal@cal),'prior_loss':float(.5*prior@prior),
          'candidate_model_penalty':float(self.candidate_penalty),'fixed_covariance_logdet_half':self.logdet_half,
          'raw_noise_only_chi2':float(rn@rn),'effective_covariance_chi2':float(r@r)}
        parts['optimized_objective']=parts['data_loss']+parts['calibration_loss']+parts['prior_loss']
        parts['declared_score']=parts['optimized_objective']+self.candidate_penalty+self.logdet_half
        return np.r_[data,cal,prior],parts
    def metadata(self):
        return {'model':self.model,'names':self.names,'bounds':[x.tolist() for x in self.bounds],'scales':self.scales.tolist(),
         'records':self.records,'noise_covariance':self.noise_cov.tolist(),'discrepancy_covariance':self.discrepancy_cov.tolist(),
         'calibration':self.calibration,'prior':self.priors,'loss':self.loss,'huber_delta':self.delta,
         'robust_basis':'ordered Cholesky-whitened coordinates','candidate_model_penalty':self.candidate_penalty,
         'gaussian_score_omits_common_m_log2pi_and_prior_normalizers':True,
         'score_is_not_Bayes_evidence_or_automatic_model_selection':True}

def fit_one(problem,start,max_calls,max_nfev,ledger,fixed=None,purpose='fit'):
    if max_calls<1 or max_nfev<1:raise ValueError('positive start budgets')
    ledger.starts+=1;initial=ledger.vector_calls;best=None
    start=np.asarray(start,float);lo,hi=problem.bounds;fixed=fixed or {}
    if start.shape!=lo.shape or np.any(start<lo) or np.any(start>hi):raise ValueError('start outside bounded domain')
    free=np.array([i for i in range(len(start)) if i not in fixed]);base=start.copy()
    for i,v in fixed.items():
        if not lo[i]<=v<=hi[i]:raise ValueError('fixed value outside domain')
        base[i]=v
    def residual(z):
        nonlocal best
        if ledger.vector_calls-initial>=max_calls:raise BudgetExhausted('per-start forward-vector cap')
        x=base.copy();x[free]=z
        r,parts=problem.evaluate(x,ledger,purpose)
        if best is None or parts['optimized_objective']<best['parts']['optimized_objective']:best={'x':x.tolist(),'parts':parts}
        return r
    try:
        f=least_squares(residual,base[free],bounds=(lo[free],hi[free]),x_scale=problem.scales[free],
           max_nfev=max_nfev,ftol=1e-9,xtol=1e-9,gtol=1e-9,loss='linear')
        # Stored solution is the best evaluated point, possibly a finite-difference probe.
        status={'converged':bool(f.success),'status':int(f.status),'message':f.message,'solver_nfev':int(f.nfev),'solver_endpoint':f.x.tolist(),'active_mask_free':f.active_mask.tolist()}
    except (BudgetExhausted,ValueError,FloatingPointError,np.linalg.LinAlgError) as e:
        status={'converged':False,'status':'budget_or_evaluation_failure','message':str(e),'solver_nfev':None}
    return {'start':start.tolist(),'fixed':{str(k):float(v) for k,v in fixed.items()},'forward_calls':ledger.vector_calls-initial,
      'max_forward_calls':max_calls,'best_evaluated':best,**status}

def clusters(attempts,scales,distance):
    if distance<=0:raise ValueError('positive cluster threshold')
    values=[{**a['best_evaluated'],'attempt_index':i,'converged':a['converged']} for i,a in enumerate(attempts) if a['best_evaluated'] is not None]
    result=[]
    for v in sorted(values,key=lambda x:x['parts']['optimized_objective']):
        near=next((c for c in result if np.linalg.norm((np.array(v['x'])-c['representative']['x'])/scales)<=distance),None)
        if near is None:result.append({'representative':v,'members':[v['attempt_index']]})
        else:near['members'].append(v['attempt_index'])
    return result

def multistart(problem,starts,max_calls,max_nfev,ledger,distance=.2,fixed=None,purpose='fit'):
    attempts=[fit_one(problem,s,max_calls,max_nfev,ledger,fixed,purpose) for s in starts]
    return {'attempts':attempts,'clusters':clusters(attempts,problem.scales,distance),
      'cluster_metric':'Euclidean distance after declared parameter scaling; greedy representative, not basin proof',
      'cluster_distance_scaled':distance,'global_minimum_certified':False,
      'unconverged_points_retained':True,'search_domain':[x.tolist() for x in problem.bounds]}

def profile(problem,starts,index,grid,config,ledger):
    rows=[]
    for value in grid:
        result=multistart(problem,starts,config['max_calls_per_start'],config['max_nfev'],ledger,config['cluster_distance_scaled'],{index:value},'profile')
        rows.append({'fixed_value':float(value),**result})
    return {'parameter_index':index,'rows':rows,'confidence_interval':None,
      'meaning':'finite-grid finite-budget upper estimates of penalized profile minima; all other parameters refit',
      'data_only_profile_requires_zero_calibration_and_priors':True}

def heldout(problem,x,case,ledger):
    from scenarios import discrepancy_features,noise_covariance
    train=problem.predict(x,problem.records,ledger,'validation')
    rr=case['heldout_records'];pred=problem.predict(x,rr,ledger,'validation')
    H=noise_covariance(rr);cross=np.zeros((len(pred),len(train)))
    if problem.model=='constant_correlated_discrepancy':
        Ft=discrepancy_features(problem.records);Fh=discrepancy_features(rr)
        cross=Fh@Ft.T;H+=Fh@Fh.T
    # Conditional fixed-parameter prediction for correlated discrepancy. No parameter-UQ claim.
    innovation=np.asarray(case['heldout_y'])-pred-cross@np.linalg.solve(problem.V,np.asarray(case['fit_y'])-train)
    S=H-cross@np.linalg.solve(problem.V,cross.T);L=whitening(S);z=solve_triangular(L,innovation,lower=True)
    return {'raw_prediction':pred.tolist(),'conditional_innovation':innovation.tolist(),'conditional_covariance':S.tolist(),
      'chi2_plugin':float(z@z),'negative_log_predictive_density_plugin':float(.5*z@z+np.log(np.diag(L)).sum()+.5*len(z)*np.log(2*np.pi)),
      'parameter_uncertainty_included':False,'coverage_certified':False,'same_sample_state_assumed':True}
