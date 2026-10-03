"""Representative conditions only, not inventory or recommendations of real equipment."""
import numpy as np
from measurement import observe
THETA=np.array([1.8,.02,.1])
SCALES=np.array([.2,.02,.05])
BOUNDS=(np.array([1.1,0.,.005]),np.array([3.,.3,1.5]))

def record(kind,w=.55,a=0.,pol='s'):
    return {'kind':'d_geo','independent':True} if kind=='d_geo' else ({'kind':kind,'wavelength_um':w,'angle_deg':a,'convention':'opposed_reflected_p'} if kind=='rho_reim' else {'kind':kind,'wavelength_um':w,'angle_deg':a,'polarization':pol})

def covariance(records):
    # Numerical teaching noise only: 0.2 percentage-point R/T, 0.005 complex-rho components, 2 nm d.
    sigma=[]
    for r in records:sigma.extend([.005,.005] if r['kind']=='rho_reim' else [.002])
    return np.diag(np.asarray(sigma)**2)

def suite():
    R=[record('R')];RT=[record('R'),record('T')];E=[record('rho_reim',a=60)]
    return {'single_R':R,'single_RT':RT,'RT_plus_independent_d':RT+[record('d_geo')],
            'angle_resolved_RT':[record(k,a=a,pol=p) for a in [0,45,65] for p in ['s','p'] for k in ['R','T']],
            'single_ellipsometric_ratio':E,'ellipsometry_plus_independent_d':E+[record('d_geo')],
            'RT_plus_ellipsometry':RT+E,
            'three_wavelength_R':[record('R',w=w) for w in [.45,.55,.75]],
            'normal_incidence_ratio':[record('rho_reim',a=0)]}

def function(records):return lambda theta:observe(theta,records)
