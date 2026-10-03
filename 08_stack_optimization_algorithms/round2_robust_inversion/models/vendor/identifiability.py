"""Finite-dimensional local diagnostics. SVD rank is a numerical first-order diagnostic.
Full rank at a regular interior point is sufficient for local uniqueness, not global.
A singular derivative at an isolated point does not prove nonidentifiability (x**3).
"""
import numpy as np
from scipy.optimize import least_squares
from scipy.linalg import solve_triangular


def whitening(covariance):
    C=np.asarray(covariance,float)
    if C.ndim!=2 or C.shape[0]!=C.shape[1] or not np.isfinite(C).all() or not np.allclose(C,C.T,rtol=1e-12,atol=1e-14):
        raise ValueError('finite symmetric observation covariance required')
    try:return np.linalg.cholesky(C)
    except np.linalg.LinAlgError as e:raise ValueError('positive definite independent-coordinate covariance required; remove redundant derived data') from e


def jacobian(function, theta, scales, bounds, step=1e-4):
    """Differentiate with respect to z, theta=theta0+diag(scales) z.
    Second-order central or one-sided differences; no complex-step on |r|^2/conjugates.
    No clipping at bounds. Returns units of observation per dimensionless z.
    """
    t,s=np.asarray(theta,float),np.asarray(scales,float)
    low,high=map(lambda x:np.asarray(x,float),bounds)
    if t.ndim!=1 or s.shape!=t.shape or low.shape!=t.shape or high.shape!=t.shape or not np.isfinite(np.r_[t,s,low,high]).all() or np.any(s<=0) or np.any(low>=high) or np.any(t<low) or np.any(t>high) or not step>0:
        raise ValueError('finite compatible theta, positive scales, ordered bounds and positive step required')
    y=np.asarray(function(t),float);J=np.empty((len(y),len(t)));schemes=[]
    for j in range(len(t)):
        h=step*s[j];e=np.zeros_like(t);e[j]=h
        if t[j]-h>=low[j] and t[j]+h<=high[j]:
            J[:,j]=(function(t+e)-function(t-e))/(2*step);schemes.append('central_second_order')
        elif t[j]+2*h<=high[j]:
            J[:,j]=(-3*y+4*function(t+e)-function(t+2*e))/(2*step);schemes.append('forward_second_order')
        elif t[j]-2*h>=low[j]:
            J[:,j]=(3*y-4*function(t-e)+function(t-2*e))/(2*step);schemes.append('backward_second_order')
        else:raise ValueError('difference step incompatible with parameter bounds')
    if not np.isfinite(J).all():raise ValueError('nonfinite Jacobian')
    return J,schemes


def rank_report(J_scaled, covariance, rtol=1e-7, atol=1e-8):
    J=np.asarray(J_scaled,float);L=whitening(covariance)
    if J.ndim!=2 or J.shape[0]!=len(L) or not np.isfinite(J).all():raise ValueError('finite compatible Jacobian required')
    B=solve_triangular(L,J,lower=True)
    _,sv,Vh=np.linalg.svd(B,full_matrices=True)
    threshold=max(atol,rtol*sv[0]) if len(sv) else atol
    rank=int(np.count_nonzero(sv>threshold));p=J.shape[1]
    padded=np.zeros(p);padded[:len(sv)]=sv
    cov_z=None
    if rank==p:cov_z=(Vh.T/(sv*sv))@Vh
    return {'rank':rank,'parameter_count':p,'row_count':len(J),'singular_values':padded.tolist(),
            'rank_threshold':float(threshold),'rtol':rtol,'atol':atol,
            'condition_number':float(sv[0]/sv[-1]) if rank==p else None,
            'null_directions_scaled':Vh[rank:].tolist(),'covariance_scaled_local_if_full_rank':None if cov_z is None else cov_z.tolist(),
            'full_rank_is_not_global_certificate':True}


def nuisance_project(J_interest,J_nuisance,covariance,rtol=1e-7):
    """Profile first-order unconstrained nuisance without priors, including singular nuisance."""
    L=whitening(covariance);A=solve_triangular(L,J_interest,lower=True);N=solve_triangular(L,J_nuisance,lower=True)
    if N.ndim!=2 or A.ndim!=2 or len(N)!=len(A):raise ValueError('compatible derivative blocks required')
    U,s,_=np.linalg.svd(N,full_matrices=False)
    rank=int(np.sum(s>rtol*s[0])) if len(s) and s[0]>0 else 0
    P=U[:,:rank];effective=A-P@(P.T@A)
    return effective,{'nuisance_rank':rank,'interest_information':(effective.T@effective).tolist()}


def fit_multistart(function,y,covariance,starts,bounds,scales,max_nfev=300):
    y=np.asarray(y,float);L=whitening(covariance);rows=[]
    for index,start in enumerate(starts):
        try:
            f=least_squares(lambda t:solve_triangular(L,function(t)-y,lower=True),start,bounds=bounds,
                            x_scale=scales,max_nfev=max_nfev,ftol=1e-10,xtol=1e-10,gtol=1e-10)
            rows.append({'start_index':index,'theta':f.x.tolist(),'chi2':float(f.fun@f.fun),
                         'converged':bool(f.success),'status':int(f.status),'nfev':int(f.nfev),
                         'active_mask':f.active_mask.tolist(),'message':f.message})
        except (ValueError,FloatingPointError,np.linalg.LinAlgError) as e:
            rows.append({'start_index':index,'converged':False,'error':str(e)})
    valid=[r for r in rows if r.get('converged') and 'chi2' in r]
    return {'best':min(valid,key=lambda r:r['chi2']) if valid else None,'attempts':rows,
            'global_minimum_certified':False}


def profile_parameter(function,y,covariance,starts,bounds,scales,index,grid,max_nfev=300):
    """Refit every other parameter at every fixed grid value. No frozen-nuisance shortcut."""
    starts=np.asarray(starts,float);low,high=map(np.asarray,bounds);scales=np.asarray(scales)
    if starts.ndim!=2 or not 0<=index<len(low):raise ValueError('start matrix and valid index required')
    keep=np.arange(len(low))!=index;rows=[]
    for value in grid:
        if not low[index]<=value<=high[index]:raise ValueError('profile grid outside domain')
        def reduced(z):
            t=np.empty(len(low));t[index]=value;t[keep]=z;return function(t)
        result=fit_multistart(reduced,y,covariance,starts[:,keep],(low[keep],high[keep]),scales[keep],max_nfev)
        if result['best'] is not None:
            t=np.empty(len(low));t[index]=value;t[keep]=result['best']['theta'];result['best']['theta_full']=t.tolist()
        rows.append({'fixed_value':float(value),**result})
    return {'parameter_index':index,'rows':rows,'confidence_interval':None,
            'meaning':'finite-grid best-of-starts upper-bound approximation to profile minimum; no confidence coverage/global proof'}
