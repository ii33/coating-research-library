"""Research-only QCM/source/element transfer in SI. No hardware, credentials or I/O API.
Dependencies: numpy, scipy. Data must identify crystal fundamental/branch and model limits.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.optimize import least_squares, brentq

N_A = 6.02214076e23  # exact mol^-1
K_B = 1.380649e-23   # exact J K^-1
MOLAR_MASS = {'Al': 0.0269815384, 'O': 0.015999}  # kg/mol; O conventional example
QUARTZ_RHO = 2649.0 # kg/m3; INFICON SQM-160 manual constant, not sample density
QUARTZ_N = 1661.0   # Hz*m, manual 1.661e5 Hz*cm


def finite(x, name='input'):
    a = np.asarray(x, dtype=float)
    if not np.all(np.isfinite(a)):
        raise ValueError(f'{name} must be finite')
    return a


def positive(x, name):
    a = finite(x, name)
    if np.any(a <= 0): raise ValueError(f'{name} must be positive')
    return a


def covariance(c, n):
    c = finite(c, 'covariance')
    if c.shape != (n,n) or not np.allclose(c,c.T,atol=1e-14,rtol=1e-10):
        raise ValueError('covariance must be symmetric N by N')
    if np.min(np.linalg.eigvalsh(c)) < -1e-12 * max(np.max(np.abs(c)),1e-100):
        raise ValueError('covariance must be positive semidefinite')
    return c


def mass_areal(f_hz, f0_hz, z_ratio=1., method='zmatch', *, rigid=True,
               fundamental=True, rho_q=QUARTZ_RHO, n_q=QUARTZ_N):
    """kg/m2 relative to unloaded fundamental f0. Principal acoustic branch only.
    z=Z_quartz/Z_film. Zmatch assumes real elastic impedance; NOT viscoelastic inversion.
    Numerical branch f0/2 < f <= f0 is not a physical validation threshold.
    """
    if not rigid or not fundamental:
        raise ValueError('rigid bonded film and fundamental mode required by this implementation')
    f = positive(f_hz, 'frequency'); f0 = float(positive(f0_hz,'unloaded frequency'))
    z = float(positive(z_ratio,'Z ratio')); rq=float(positive(rho_q,'quartz density')); nq=float(positive(n_q,'quartz frequency constant'))
    if np.any(f > f0) or np.any(f <= f0/2):
        raise ValueError('mass inversion outside nonnegative principal load branch')
    if method == 'sauerbrey': return rq*nq*(f0-f)/(f0*f0)
    if method != 'zmatch': raise ValueError('unknown acoustic model')
    x=np.pi*(f0-f)/f0
    return rq*nq/(np.pi*f*z)*np.arctan(z*np.tan(x))


def mass_frequency_derivative(f_hz, f0_hz, z_ratio=1., method='zmatch'):
    f=finite(f_hz); f0=float(f0_hz); z=float(z_ratio)
    mass_areal(f,f0,z,method)
    if method=='sauerbrey': return np.full_like(f,-QUARTZ_RHO*QUARTZ_N/f0**2)
    x=np.pi*(f0-f)/f0; tx=np.tan(x); a=np.arctan(z*tx)
    return -QUARTZ_RHO*QUARTZ_N/(np.pi*z)*(a/f**2+z*np.pi/f0*(1+tx*tx)/(1+z*z*tx*tx)/f)


def frequency_from_mass(m_kg_m2, f0_hz, z_ratio=1., method='zmatch'):
    m=finite(m_kg_m2,'areal mass'); f0=float(positive(f0_hz,'f0'))
    if np.any(m<0): raise ValueError('negative cumulative load')
    def inv(x):
        if x==0: return f0
        if method=='sauerbrey':
            f=f0-x*f0*f0/(QUARTZ_RHO*QUARTZ_N)
            mass_areal(f,f0,z_ratio,method); return f
        return brentq(lambda f: float(mass_areal(f,f0,z_ratio,method))-x,
                      f0*(.5+1e-10),f0,xtol=1e-8)
    return np.array([inv(x) for x in m.ravel()]).reshape(m.shape)


def rate_from_frequency(times_s, raw_f_hz, f0_hz, *, drift_hz=None,
                        frequency_covariance_hz2=None, z_ratio=1., method='zmatch'):
    """GLS slope of cumulative mass. Drift is relative to the f0 reference and external.
    covariance must already include drift-estimate uncertainty/cross-correlations.
    Negative slopes are returned as net loss, not reinterpreted as positive arrival.
    f0/Z uncertainty is handled separately in propagate_covariance, not silently omitted.
    """
    t=finite(times_s,'time'); raw=finite(raw_f_hz,'frequency')
    if t.ndim!=1 or raw.shape!=t.shape or len(t)<3 or np.any(np.diff(t)<=0):
        raise ValueError('at least 3 strictly increasing, paired samples required')
    if drift_hz is None: raise ValueError('explicit independently estimated drift or justified zero required')
    d=np.broadcast_to(finite(drift_hz,'drift'),raw.shape); f=raw-d
    m=mass_areal(f,f0_hz,z_ratio,method)
    x=np.column_stack([np.ones(len(t)),t-t.mean()])
    if frequency_covariance_hz2 is None:
        # No invented measurement error bar; OLS point estimate only.
        beta=np.linalg.lstsq(x,m,rcond=None)[0]; cb=None
    else:
        cf=covariance(frequency_covariance_hz2,len(t)); derivative=mass_frequency_derivative(f,f0_hz,z_ratio,method)
        cm=derivative[:,None]*cf*derivative[None,:]
        l=np.linalg.cholesky(cm); a=np.linalg.solve(l,x); b=np.linalg.solve(l,m)
        beta=np.linalg.lstsq(a,b,rcond=None)[0]; cb=np.linalg.inv(a.T@a)
    return {'slope_kg_m2_s':float(beta[1]),'slope_std_kg_m2_s':None if cb is None else float(np.sqrt(cb[1,1])),
            'mass_kg_m2':m.tolist(),'corrected_f_hz':f.tolist(),
            'net_state':'positive' if beta[1]>0 else 'zero_or_loss',
            'residual_kg_m2':(m-x@beta).tolist(), 'uncertainty':'conditional_on_f0_Z_model_drift'}


def source_incident_from_qcm(net_mass_rate, capture, reactive_retained=0., outgoing=0.):
    """Single-source mass balance y=eta*j_source+reaction_retained-outgoing."""
    y=float(finite(net_mass_rate)); c=float(finite(capture)); r=float(finite(reactive_retained)); o=float(finite(outgoing))
    if not 0<c<=1 or r<0 or o<0: raise ValueError('known 0<capture<=1 and nonnegative side terms required')
    incoming=(y-r+o)/c
    if incoming<0: raise ValueError('negative inferred arrival: inconsistent side-term balance')
    return incoming


def geometry_terms(positions_m, normals, center_m=(0,0,0), source_normal=(0,0,1), azimuth_axis=(1,0,0)):
    x=finite(positions_m); normals=finite(normals); c=finite(center_m); ns=finite(source_normal); ax=finite(azimuth_axis)
    if x.ndim!=2 or x.shape[1]!=3 or normals.shape!=x.shape or c.shape!=(3,) or ns.shape!=(3,) or ax.shape!=(3,):
        raise ValueError('invalid geometry dimensions')
    if not np.allclose(np.linalg.norm(normals,axis=1),1,atol=1e-10,rtol=0) or not np.isclose(np.linalg.norm(ns),1,atol=1e-10,rtol=0) or not np.isclose(np.linalg.norm(ax),1,atol=1e-10,rtol=0) or abs(ax@ns)>1e-10:
        raise ValueError('unit normals and perpendicular unit azimuth axis required')
    v=x-c; r=positive(np.linalg.norm(v,axis=1),'distance'); u=v/r[:,None]; ay=np.cross(ns,ax)
    return r,u@ns,-np.sum(u*normals,axis=1),(u@ax)**2-(u@ay)**2


def point_kernel(positions_m,normals,n,a=0.,visibility=None,**geometry):
    """m^-2 for total pre-occlusion hemispherical emitted MASS rate.
    f=(n+1)/(2pi)*mu_s^n*[1+a*(u_x^2-u_y^2)], n>=0, |a|<1.
    The azimuth term integrates to zero and vanishes at the pole.
    """
    n=float(finite(n)); a=float(finite(a))
    if n<0 or abs(a)>=1: raise ValueError('n>=0, |anisotropy|<1 required')
    r,mu,mi,h=geometry_terms(positions_m,normals,**geometry)
    vis=np.ones_like(r) if visibility is None else np.broadcast_to(finite(visibility),r.shape)
    if np.any((vis<0)|(vis>1)): raise ValueError('visibility must lie in [0,1]')
    k=np.zeros_like(r); active=(mu>0)&(mi>0)&(vis>0)
    k[active]=(n+1)/(2*np.pi)*mu[active]**n*(1+a*h[active])*mi[active]*vis[active]/r[active]**2
    return k


def transfer_qcm_to_workpiece(net_mass_rate,capture_q,k_q,k_w,reactive_retained=0.,outgoing=0.):
    qinc=source_incident_from_qcm(net_mass_rate,capture_q,reactive_retained,outgoing)
    kq=float(positive(k_q,'QCM transfer kernel')); kw=finite(k_w,'workpiece kernel')
    if np.any(kw<0): raise ValueError('negative kernel')
    return {'source_rate_kg_s':qinc/kq,'incident_workpiece_kg_m2_s':qinc*kw/kq}


def species_elements(particle_fluxes,stoichiometries,molar_mass=MOLAR_MASS):
    """Particle count (atoms, molecules OR clusters) -> nuclei/element and mass.
    Stoichiometry is explicit integer nuclei per particle; formulas are never guessed.
    """
    if set(particle_fluxes)!=set(stoichiometries): raise ValueError('species keys mismatch')
    elements={}; mass=0.
    for s,flux in particle_fluxes.items():
        flux=float(finite(flux)); sto=stoichiometries[s]
        if flux<0 or not sto: raise ValueError('nonnegative particle flux and nonempty stoichiometry required')
        for e,count in sto.items():
            if isinstance(count,bool) or not isinstance(count,int) or count<1 or e not in molar_mass:
                raise ValueError('explicit positive integer atom counts and molar masses required')
            mm=float(positive(molar_mass[e],'molar mass'))
            elements[e]=elements.get(e,0.)+count*flux
            mass+=count*flux*mm/N_A
    return {'element_flux_atoms_m2_s':elements,'total_atomic_flux_atoms_m2_s':sum(elements.values()),'mass_flux_kg_m2_s':mass}


def mixture_from_mass(mass_flux,species_number_fractions,stoichiometries,molar_mass=MOLAR_MASS):
    """Fractions are by particle NUMBER, not mass; all species share local mixture only."""
    f={s:float(finite(x)) for s,x in species_number_fractions.items()}
    if any(x<0 for x in f.values()) or not np.isclose(sum(f.values()),1.,rtol=0,atol=1e-12): raise ValueError('number fractions must sum to 1')
    unit=species_elements(f,stoichiometries,molar_mass)['mass_flux_kg_m2_s']
    j=float(finite(mass_flux))
    if j<0: raise ValueError('negative incident mass')
    particles={s:j*x/unit for s,x in f.items()}
    return {'particle_fluxes_m2_s':particles,**species_elements(particles,stoichiometries,molar_mass)}


def gas_impingement(pressure_pa,temperature_k,molar_mass_kg_mol):
    """Ideal equilibrium one-sided molecular impingement; no sticking/reaction assumed."""
    p=float(finite(pressure_pa)); t=float(positive(temperature_k,'temperature')); m=float(positive(molar_mass_kg_mol,'molar mass'))/N_A
    if p<0: raise ValueError('negative partial pressure')
    return p/math.sqrt(2*math.pi*m*K_B*t)


def retained_elements(incident_by_species,stoichiometries,captures,outgoing_element_flux=None):
    if set(incident_by_species)!=set(captures): raise ValueError('each species needs a capture')
    for x in captures.values():
        if not 0<=float(finite(x))<=1: raise ValueError('capture outside [0,1]')
    out=species_elements({s:f*captures[s] for s,f in incident_by_species.items()},stoichiometries)
    elements=dict(out['element_flux_atoms_m2_s'])
    for e,x in (outgoing_element_flux or {}).items():
        x=float(finite(x))
        if e not in MOLAR_MASS or x<0: raise ValueError('invalid outgoing element flux')
        elements[e]=elements.get(e,0.)-x
    return {'net_element_flux_atoms_m2_s':elements,'net_mass_flux_kg_m2_s':sum(v*MOLAR_MASS[e]/N_A for e,v in elements.items()),'thickness_prediction':'requires_independent_composition_and_actual_film_density'}


def propagate_covariance(function,mean,cov,relative_step=1e-5,scales=None):
    """First-order correlated propagation; no confidence claim under unknown model error."""
    x=finite(mean); c=covariance(cov,len(x)); scale=np.maximum(np.abs(x),1.) if scales is None else positive(scales,'scales')
    if x.ndim!=1 or scale.shape!=x.shape: raise ValueError('mean/scales shape mismatch')
    y=np.atleast_1d(finite(function(x))); jac=np.empty((len(y),len(x)))
    for i in range(len(x)):
        h=relative_step*scale[i]; xp=x.copy(); xm=x.copy(); xp[i]+=h; xm[i]-=h
        jac[:,i]=(np.atleast_1d(function(xp))-np.atleast_1d(function(xm)))/(2*h)
    cy=jac@c@jac.T
    return {'mean':y.tolist(),'jacobian':jac.tolist(),'covariance':cy.tolist(),'std':np.sqrt(np.maximum(0,np.diag(cy))).tolist(),'kind':'local_first_order_conditional'}


def design_matrix(positions_m,normals,n,a=0.,*,fit_capture=False,independent_source_count=0,**geometry):
    _,mu,mi,h=geometry_terms(positions_m,normals,**geometry)
    if np.any(mu<=0) or np.any(mi<=0): raise ValueError('design requires active front-side points')
    if n<0 or abs(a)>=1: raise ValueError('invalid shape')
    x=np.column_stack([np.ones(len(mu)),1/(n+1)+np.log(mu),h/(1+a*h)])
    if fit_capture: x=np.column_stack([x,np.ones(len(mu))])
    for _ in range(independent_source_count):
        row=np.zeros(x.shape[1]);row[0]=1;x=np.vstack([x,row])
    return x


def rank_report(x):
    x=finite(x); norms=np.linalg.norm(x,axis=0); scaled=x/np.where(norms>0,norms,1)
    sv=np.linalg.svd(scaled,compute_uv=False); rank=int(np.linalg.matrix_rank(scaled))
    return {'rank':rank,'columns':x.shape[1],'rows':x.shape[0],'column_normalized_singular_values':sv.tolist(),
            'condition_column_normalized':None if rank<x.shape[1] else float(sv[0]/sv[-1]),'identifiable':rank==x.shape[1]}


def fit_source(positions_m,normals,observed_qcm_flux,sigma_log,*,capture=1.,visibility=None,
               initial=(1e-6,2.,0.),q_bounds=(1e-12,1e-2),n_bounds=(0.,12.),a_bounds=(-.95,.95),
               fit_capture=False,capture_bounds=(.05,1.),independent_source=None,loss='soft_l1',**geometry):
    """Bounded robust log-space fit of Q,n,a; optional common eta with independent Q.
    independent_source=(Q_observed_kg_s, known_log_std). Nonzero visible data only.
    Zero/occluded observations must be declared missing/censored, never floored.
    Covariance only linear loss + interior full-rank solution. Robust uncertainty needs bootstrap.
    """
    y=positive(observed_qcm_flux,'QCM mass rate'); x=finite(positions_m); ns=finite(normals)
    sd=np.broadcast_to(positive(sigma_log,'log standard deviation'),y.shape)
    cap=np.broadcast_to(positive(capture,'capture'),y.shape)
    if np.any(cap>1): raise ValueError('capture must not exceed 1')
    vis=np.ones_like(y) if visibility is None else np.broadcast_to(finite(visibility),y.shape)
    if y.ndim!=1 or len(y)!=len(x) or np.any(vis<=0) or np.any(vis>1): raise ValueError('nonzero known visibility paired observations required')
    if fit_capture and not np.allclose(cap,cap[0]): raise ValueError('fitted common capture must have scalar initial value')
    nsrc=0 if independent_source is None else 1
    d=design_matrix(x,ns,initial[1],initial[2],fit_capture=fit_capture,independent_source_count=nsrc,**geometry)
    if not rank_report(d)['identifiable']: raise ValueError('rank deficient: source/shape/capture not independently identifiable')
    if independent_source is not None: positive(independent_source,'independent source and uncertainty')
    p0=[math.log(initial[0]),initial[1],initial[2]];lo=[math.log(q_bounds[0]),n_bounds[0],a_bounds[0]];hi=[math.log(q_bounds[1]),n_bounds[1],a_bounds[1]]
    if fit_capture:p0+=[math.log(cap[0])];lo+=[math.log(capture_bounds[0])];hi+=[math.log(capture_bounds[1])]
    def residual(p):
        k=point_kernel(x,ns,p[1],p[2],vis,**geometry)
        if np.any(k<=0): raise ValueError('nonpositive modeled transfer')
        eta=np.exp(p[3]) if fit_capture else cap
        r=(p[0]+np.log(k)+np.log(eta)-np.log(y))/sd
        if independent_source is not None:r=np.r_[r,(p[0]-math.log(independent_source[0]))/independent_source[1]]
        return r
    fit=least_squares(residual,p0,bounds=(lo,hi),loss=loss,xtol=1e-11,ftol=1e-11,gtol=1e-11,max_nfev=1000)
    if not fit.success: raise RuntimeError('bounded fit did not converge: '+fit.message)
    p=fit.x; design=design_matrix(x,ns,p[1],p[2],fit_capture=fit_capture,independent_source_count=nsrc,**geometry)
    scales=np.r_[sd,independent_source[1]] if independent_source is not None else sd
    j=design/scales[:,None]; rr=rank_report(j)
    if not rr['identifiable']: raise ValueError('fitted design rank deficient')
    active=bool(np.any(fit.active_mask)); cov=None
    if loss=='linear' and not active: cov=np.linalg.inv(j.T@j).tolist()
    return {'Q_kg_s':float(np.exp(p[0])),'n':float(p[1]),'a':float(p[2]),
            'capture':float(np.exp(p[3])) if fit_capture else cap.tolist(),
            'parameters_logQ_n_a_logeta':p.tolist(),'covariance':cov,'rank':rr,'active_bound':active,
            'standardized_residuals':residual(p).tolist(),'cost':float(fit.cost),'loss':loss,
            'uncertainty_note':'conditional known log noise; robust or boundary fits require bootstrap/profile',
            'nfev':fit.nfev}
