"""Small exact/analytic counterexamples and tiny finite-difference optics checks."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
from vendor.measurement import observe
from vendor.identifiability import jacobian,rank_report
from scenarios import record,operator
from inversion import huber_cost,Problem,Ledger,multistart
from design import conditional_increment,information_difference
ROOT=Path(__file__).resolve().parents[1]

def run():
    # A repeated scalar measurement has rho correlation; increment=(1-rho)/(1+rho).
    repeat={}
    for rho in [0.,.9,.999]:
        A,B,c=conditional_increment([[1.]],[[1.]],[[1.]],[[1.]],[[rho]])
        repeat[str(rho)]=float((B.T@B)[0,0])
    # Unknown new thickness bias cannot add interest information, although raw derivative is large.
    A,B,c=conditional_increment([[1.,0.]],[[1.,1.]],[[1.]],[[.01]],[[0.]])
    uncal=information_difference(A,B,np.empty((0,2)),1)
    # Precision alone can favor a biased measurement and worsen mean squared error.
    v0=1.;v1=.01;b=2.;estimate=b/(1+v1)
    naive_variance=1/(1/v0+1/v1);actual_mse=naive_variance+estimate**2
    # Huber handles one isolated outlier but cannot identify a shared systematic shift.
    clean=np.zeros(20);outlier=np.r_[clean,20.]
    robust=least_squares(lambda z:np.sign(z[0]-outlier)*np.sqrt(2*huber_cost(z[0]-outlier)),[0.]).x[0]
    systematic=np.ones(20)*2.
    rs=least_squares(lambda z:np.sign(z[0]-systematic)*np.sqrt(2*huber_cost(z[0]-systematic)),[0.]).x[0]
    # Exact transparent-film normal-incidence thickness periodicity at one wavelength.
    n=1.8;w=.55;theta=np.array([n,0.,.1]);alias=theta.copy();alias[2]+=w/(2*n)
    rr=[record('R',w),record('T',w)];y=observe(theta,rr);ya=observe(alias,rr)
    f=lambda z:observe([z[0],0.,z[1]],rr)
    J,schemes=jacobian(f,theta[[0,2]],[.2,.05],([1.1,.005],[3.,1.5]))
    # Locally rank-two oblique measurements can retain exact thickness aliases.
    aa=50.;period=w/(2*np.sqrt(n*n-np.sin(np.deg2rad(aa))**2))
    ra=[record('R',w,aa,'s'),record('R',w,aa,'p'),record('rho_reim',w,aa)]
    fa=lambda z:observe([z[0],0.,z[1]],ra)
    ja,_=jacobian(fa,[n,.1],[.2,.05],([1.1,.005],[3.,1.5]))
    ca=np.diag(np.array([.002,.002,.005,.005])**2)
    pp=Problem('lossless_alias',['n','d_um'],([1.1,.005],[3.,1.5]),np.array([.2,.05]),ra,fa([n,.1]),ca,np.zeros((4,4)),lambda z,r:observe([z[0],0.,z[1]],r))
    ledger=Ledger(200)
    found=multistart(pp,[[1.79,.098],[1.81,.1+period+.002]],90,25,ledger,.2)
    rank2_alias={'period_um':float(period),'local':rank_report(ja,ca),'max_alias_residual':float(np.max(np.abs(fa([n,.1])-fa([n,.1+period])))),
      'discovery':found,'ledger':ledger.as_dict(),'starts_informed_by_analytic_alias':True,'global_certificate':False}
    # Realistic shared-n across wavelengths is a candidate assumption, not proof from many data.
    x=np.array([1.8,.02,.1,1.,0.]);train=[record('R',.6,45),record('T',.6,45)]
    hold=[record('R',.9,55),record('T',.9,55)]
    f0=operator('constant');f1=operator('linear_n')
    dr=(f1(np.r_[x,.35],hold)-f0(x,hold))/.002
    return {'correlated_repeat_information_increment':repeat,'uncalibrated_new_bias':uncal,
      'precise_biased_candidate':{'baseline_variance':v0,'naive_information_increment':1/v1,'reported_variance':naive_variance,'squared_bias':estimate**2,'actual_mse':actual_mse},
      'robust_location':{'isolated_outlier_gaussian_estimate':float(outlier.mean()),'isolated_outlier_huber_estimate':float(robust),'shared_bias_huber_estimate':float(rs),'true_location':0.},
      'optical_exact_alias':{'theta':theta.tolist(),'alias':alias.tolist(),'max_observation_difference':float(np.max(np.abs(y-ya))),'local_rank_n_d':rank_report(J,np.eye(2)*.002**2),'note':'lossless R+T=1, hence rank at most 1; global alias persists regardless'},
      'local_rank2_global_alias':rank2_alias,
      'optical_model_mismatch':{'training_max_difference_at_pivot':float(np.max(np.abs(f1(np.r_[x,.35],train)-f0(x,train)))),'heldout_residual_noise_units':dr.tolist(),'all_values_synthetic':True},
      'design_claim':'more local Gaussian information can coexist with worse bias/MSE under wrong model',
      'heavy_run':False}

if __name__=='__main__':
    value=run();(ROOT/'verification/diagnostics.json').write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');print(json.dumps(value,indent=2))
