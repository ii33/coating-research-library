"""Finite-parameter optical families, not material databases or instrument inventory."""
import copy
import numpy as np
from vendor.measurement import observe,node_arrays,Contract
from inversion import Problem
CONTRACT=Contract()

def record(kind,w=.55,a=0.,pol='s'):
    if kind=='d_geo':return {'kind':kind,'independent':True}
    r={'kind':kind,'wavelength_um':w,'angle_deg':a}
    r.update({'convention':'opposed_reflected_p'} if kind=='rho_reim' else {'polarization':pol})
    return r

def operator(model):
    linear=model=='linear_n'
    if model not in ['constant','linear_n','constant_correlated_discrepancy']:raise ValueError('unknown model candidate')
    def f(x,records):
        if len(x)!=(6 if linear else 5):raise ValueError('candidate parameter dimension')
        n,k,d,gain,angle=x[:5];slope=x[5] if linear else 0.
        result=[]
        for r in records:
            if r['kind']=='d_geo':result.extend(observe([n,k,d],[r],CONTRACT));continue
            nodes=node_arrays(r['wavelength_um'],r['angle_deg'],r.get('spectral_nodes',[(0,1)]),r.get('angle_nodes',[(0,1)]))
            if r['kind']=='rho_reim' and len(nodes)!=1:raise ValueError('mixed-ray rho unsupported')
            value=None
            for w,a,weight in nodes:
                local={z:v for z,v in r.items() if z not in ['spectral_nodes','angle_nodes']};local.update(wavelength_um=w,angle_deg=a+angle)
                y=observe([n+slope*(w-.6),k,d],[local],CONTRACT)
                if r['kind'] in ['R','T']:y=y*gain
                value=weight*y if value is None else value+weight*y
            result.extend(value)
        return np.asarray(result)
    return f

def noise_covariance(records):
    sigma=[]
    for r in records:sigma.extend([.005,.005] if r['kind']=='rho_reim' else [.002])
    return np.diag(np.asarray(sigma)**2)

def discrepancy_features(records):
    rows=[]
    for r in records:
        if r['kind']=='rho_reim':rows.extend([[0.,0.],[0.,0.]])
        elif r['kind']=='d_geo':rows.append([0.,0.])
        else:rows.append([.003,.005*(r['wavelength_um']-.6)])
    return np.asarray(rows)

def measurement_candidates():
    return [{'name':'off_axis_complex_ratio','records':[record('rho_reim',.55,60)],'new_nuisance':False,'cost_units':3.},
            {'name':'independent_geometric_d_calibrated','records':[record('d_geo')],'new_nuisance':False,'cost_units':2.},
            {'name':'independent_geometric_d_unknown_bias','records':[record('d_geo')],'new_nuisance':True,'cost_units':2.}]

def build_case(truth,scenario,c,ledger,rng):
    if scenario not in ['clean','single_outlier','dispersion_mismatch']:raise ValueError('unknown truth scenario')
    fit=[record(k,w,a,p) for w in c['fit_wavelengths_um'] for a in c['angles_deg'] for p in ['s','p'] for k in ['R','T']]
    hold=[record(k,w,55.,p) for w in c['heldout_wavelengths_um'] for p in ['s','p'] for k in ['R','T']]
    truth_model='linear_n' if scenario=='dispersion_mismatch' else 'constant'
    x=np.r_[truth,1.,0.,.35] if truth_model=='linear_n' else np.r_[truth,1.,0.]
    f=operator(truth_model)
    means=[]
    for rr in [fit,hold]:
        ledger.consume(2*len(rr),'generate');means.append(f(x,rr))
    if scenario=='single_outlier':means[0][0]+=.04
    C=noise_covariance(fit);H=noise_covariance(hold)
    yy=means[0]+np.linalg.cholesky(C)@rng.standard_normal(len(fit));yh=means[1]+np.linalg.cholesky(H)@rng.standard_normal(len(hold))
    return {'truth':list(truth),'truth_model':truth_model,'scenario':scenario,'fit_records':fit,'heldout_records':hold,
      'fit_mean':means[0].tolist(),'heldout_mean':means[1].tolist(),'fit_y':yy.tolist(),'heldout_y':yh.tolist(),
      'noise_covariance':C.tolist(),'split_declared_before_fit':True,'actual_hardware':None,
      'conditional_synthetic':True,'outlier_units':'absolute R/T fraction','sloped_n_unit':'um^-1'}

def make_problem(case,candidate,loss):
    if case.get('conditional_synthetic') is not True or case.get('actual_hardware') is not None:
        raise ValueError('synthetic-only adapter: actual measurements require a separately verified contract')
    p=6 if candidate=='linear_n' else 5
    names=['n0','k','d_um','RT_gain','angle_bias_deg']+(['dn_dlambda_um_inv'] if p==6 else [])
    low=[1.1,0.,.005,.9,-.5]+([-.5] if p==6 else [])
    high=[3.,.3,1.5,1.1,.5]+([.5] if p==6 else [])
    scales=np.array([.2,.02,.05,.01,.1]+([.2] if p==6 else []))
    rr=case['fit_records'];C=np.asarray(case['noise_covariance']);F=discrepancy_features(rr)
    D=F@F.T if candidate=='constant_correlated_discrepancy' else np.zeros_like(C)
    cal=[{'name':'independent_gain_calibration','index':3,'mean':1.,'sigma':.005,'evidence':'synthetic_condition'},
         {'name':'independent_angle_calibration','index':4,'mean':0.,'sigma':.1,'evidence':'synthetic_condition'}]
    return Problem(candidate,names,(low,high),scales,rr,np.asarray(case['fit_y']),C,D,operator(candidate),cal,[],loss)
