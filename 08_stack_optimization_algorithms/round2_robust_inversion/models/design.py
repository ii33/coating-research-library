"""Conditional Gaussian local information, explicitly not nonlinear/global utility.
Correlated new observations are conditioned on existing observations before addition.
Interest information is re-profiled on the SAME nuisance space before/after addition.
"""
import numpy as np
from scipy.linalg import solve_triangular
from vendor.identifiability import jacobian,whitening

def conditional_increment(J0,J1,C0,C1,C10):
    J0,J1,C0,C1,C10=map(lambda x:np.asarray(x,float),(J0,J1,C0,C1,C10))
    whitening(C0)
    joint=np.block([[C0,C10.T],[C10,C1]]);whitening(joint)
    G=J1-C10@np.linalg.solve(C0,J0)
    S=C1-C10@np.linalg.solve(C0,C10.T)
    A0=solve_triangular(whitening(C0),J0,lower=True)
    Ac=solve_triangular(whitening(S),G,lower=True)
    return A0,Ac,{'conditional_covariance':S.tolist(),'conditional_derivative':G.tolist(),
      'full_parameter_information_increment':(Ac.T@Ac).tolist()}

def profile_information(A,interest_count=3,rtol=1e-7,atol=1e-8):
    A=np.asarray(A,float);U=A[:,:interest_count];N=A[:,interest_count:]
    if N.shape[1]:
        q,s,_=np.linalg.svd(N,full_matrices=False);threshold=max(atol,rtol*s[0]) if len(s) else atol
        rank=int(np.sum(s>threshold));U=U-q[:,:rank]@(q[:,:rank].T@U)
    else:rank=0
    return U.T@U,rank

def information_difference(A0,Ac,extra_rows,interest_count=3):
    base=np.vstack([A0,extra_rows]);joint=np.vstack([base,Ac])
    I0,r0=profile_information(base,interest_count);I1,r1=profile_information(joint,interest_count)
    delta=(I1-I0);delta=.5*(delta+delta.T)
    e0=np.linalg.eigvalsh(I0);e1=np.linalg.eigvalsh(I1);ed=np.linalg.eigvalsh(delta)
    threshold=max(1e-8,1e-7*max(np.linalg.svd(joint,compute_uv=False)[0],1.))
    # rank is evaluated on projected singular values, not a mismatched absolute eigenvalue tolerance.
    rk0=int(np.sum(np.sqrt(np.maximum(e0,0))>threshold));rk1=int(np.sum(np.sqrt(np.maximum(e1,0))>threshold))
    metric=None
    if rk0==interest_count and rk1==interest_count:
        metric=float(.5*(np.linalg.slogdet(I1)[1]-np.linalg.slogdet(I0)[1]))
    return {'interest_information_before':I0.tolist(),'interest_information_after':I1.tolist(),'interest_increment':delta.tolist(),
      'increment_eigenvalues':ed.tolist(),'interest_rank_before':rk0,'interest_rank_after':rk1,
      'nuisance_rank_before':r0,'nuisance_rank_after':r1,'singular_value_threshold':threshold,
      'half_logdet_precision_ratio_if_nonsingular':metric,'confidence_or_global_certificate':False}

def auxiliary_rows(problem,items,extra_dim=0):
    rows=[]
    for q in items:
        r=np.zeros(len(problem.names)+extra_dim);r[q['index']]=problem.scales[q['index']]/q['sigma'];rows.append(r)
    return np.asarray(rows).reshape((-1,len(problem.names)+extra_dim))

def assess_candidates(problem,x,candidates,steps,ledger):
    from scenarios import noise_covariance,discrepancy_features
    result=[]
    for step in steps:
        J0,scheme=jacobian(lambda z:problem.predict(z,problem.records,ledger,'design'),x,problem.scales,problem.bounds,step)
        for candidate in candidates:
            rr=candidate['records'];J1,s1=jacobian(lambda z:problem.predict(z,rr,ledger,'design'),x,problem.scales,problem.bounds,step)
            C1=noise_covariance(rr);cross=np.zeros((len(C1),len(problem.y)))
            if problem.model=='constant_correlated_discrepancy':
                F0=discrepancy_features(problem.records);F1=discrepancy_features(rr)
                C1+=F1@F1.T;cross=F1@F0.T
            extra=int(candidate['new_nuisance']);a,b=J0,J1
            if extra:
                # A new uncalibrated d bias, physical scale 0.05 um, acts only on new thickness row.
                a=np.c_[a,np.zeros(len(a))];b=np.c_[b,np.full(len(b),.05)]
            A0,Ac,condition=conditional_increment(a,b,problem.V,C1,cross)
            empty=np.empty((0,A0.shape[1]));cal=auxiliary_rows(problem,problem.calibration,extra);prior=auxiliary_rows(problem,problem.priors,extra)
            layers={'data_only':information_difference(A0,Ac,empty),
              'with_calibration':information_difference(A0,Ac,cal),
              'with_calibration_and_prior':information_difference(A0,Ac,np.vstack([cal,prior]))}
            result.append({'candidate':candidate,'step_scaled':step,'derivative_schemes':{'existing':scheme,'new':s1},
              'conditional':condition,'information_layers':layers,
              'interpretation':'fixed-covariance Gaussian first-order surrogate even if the fitted objective is Huber',
              'cost_is_synthetic':True,'known_model_at_fixed_parameter_only':True})
    return result
