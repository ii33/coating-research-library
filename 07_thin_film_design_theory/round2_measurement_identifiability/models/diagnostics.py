"""Only small deterministic reference checks. No optical database or hardware required."""
from pathlib import Path
import json
import numpy as np
from measurement import *
from identifiability import *
from scenarios import *

def run():
    results={}
    for name,records in suite().items():
        f=function(records);J,schemes=jacobian(f,THETA,SCALES,BOUNDS)
        J2,_=jacobian(f,THETA,SCALES,BOUNDS,step=5e-5)
        J3,_=jacobian(f,THETA,SCALES,BOUNDS,step=2e-4)
        C=covariance(records)
        results[name]={'observations':f(THETA).tolist(),'scenarios_are_conditional':True,
                       'jacobian_scaled':J.tolist(),'covariance':C.tolist(),**rank_report(J,C),
                       'difference_schemes':schemes,'halved_step_max_abs_change':float(np.max(np.abs(J-J2))),
                       'doubled_step_max_abs_change':float(np.max(np.abs(J-J3)))}
    # Full-rank local two-parameter example with exact global monochromatic thickness alias.
    a=50.;w=.55;n=1.8;d=.1
    rec=[record('R',a=a,pol='s'),record('R',a=a,pol='p'),record('rho_reim',a=a)]
    f=lambda z:observe([z[0],0.,z[1]],rec)
    bounds=(np.array([1.1,.005]),np.array([3.,1.5]));sc=np.array([.2,.05])
    J,_=jacobian(f,[n,d],sc,bounds)
    period=w/(2*np.sqrt(n*n-np.sin(np.deg2rad(a))**2))
    global_alias={'theta_n_d_um':[n,d],'other_theta_n_d_um':[n,d+period],'period_um':float(period),
                  'same_condition_max_abs_difference':float(np.max(np.abs(f([n,d])-f([n,d+period])))),
                  'local':rank_report(J,covariance(rec)),
                  'heldout_65deg_Rs_difference':float(observe([n,0,d+period],[record('R',a=65)])[0]-observe([n,0,d],[record('R',a=65)])[0])}
    # Lossless fixed-k model: T is an algebraic complement, not a new derivative direction.
    frt=lambda z:observe([z[0],0,z[1]],[record('R'),record('T')])
    Jr,_=jacobian(frt,[n,d],sc,bounds)
    lossless=rank_report(Jr,np.eye(2)*.002**2)
    # d+b: unknown thickness offset destroys the standalone geometric-thickness direction.
    projected,meta=nuisance_project(np.array([[0.,0.,.05]]),np.array([[.05]]),np.array([[.002**2]]))
    recmix={'wavelength_um':.55,'angle_deg':60.,'convention':'opposed_reflected_p',
            'spectral_nodes':[[-.04,.5],[.04,.5]]}
    mix=coherency_diagnostic(THETA,recmix)
    return {'evidence':'synthetic_only','theta_n_k_d_um':THETA.tolist(),'parameter_scales':SCALES.tolist(),
            'cases':results,'global_alias':global_alias,'lossless_RT_rank':lossless,
            'unknown_thickness_offset':{'effective_norm':float(np.linalg.norm(projected)),**meta},
            'incoherent_ray_mixture':{'normalized_stokes':mix['normalized_stokes'].tolist(),'degree_of_polarization':mix['degree_of_polarization'],
                                    'rho_average_not_used':True},
            'device_validation':'not_run_awaiting_device','production_qualified':False}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);a=p.parse_args()
    text=json.dumps(run(),ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if a.output:a.output.write_text(text)
    else:print(text)
