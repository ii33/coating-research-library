"""Small falsifiable active-surface model. All example parameters are synthetic.
No real n/k, density, sputter yield, source voltage conversion, or device adapter.
"""
import math

def nonnegative(x,name):
    if type(x) not in (int,float) or not math.isfinite(x) or x<0:
        raise ValueError('finite_nonnegative_'+name)
    return float(x)

def interval(v,name):
    if not isinstance(v,list) or len(v)!=2:raise ValueError('interval_'+name)
    lo,hi=(nonnegative(x,name) for x in v)
    if lo>hi:raise ValueError('reversed_'+name)
    return lo,hi

def step(x,a,b,c,dt):
    """dx/dt=a(1-x)-(b+c)x; exact constant-bin solution and integral x dt.
    a,b,c: s^-1; dt:s. x: occupancy; c: positive-growth burial/dilution only.
    Integral uses expm1 and a series for small k*dt to avoid cancellation.
    """
    x=nonnegative(x,'x');a=nonnegative(a,'a');b=nonnegative(b,'b')
    c=nonnegative(c,'c');dt=nonnegative(dt,'dt')
    if x>1:raise ValueError('occupancy_above_one')
    k=a+b+c
    if not math.isfinite(k):raise ValueError('aggregate_rate_overflow')
    if k==0:return {'x':x,'integral_x_s':x*dt}
    u=k*dt
    if not math.isfinite(u):raise ValueError('dimensionless_time_overflow')
    one=-math.expm1(-u);ss=a/k
    # x_new convexly combines x and the equilibrium. Stable even for tiny u.
    xn=x*(1-one)+ss*one
    if abs(u)<1e-4:
        phi2=u/2-u*u/6+u**3/24-u**4/120
    else:phi2=1-one/u
    integ=dt*(x+(ss-x)*phi2)
    return {'x':xn,'integral_x_s':integ}

def evolve(x0,bins,active_sites_m2=1):
    L=nonnegative(active_sites_m2,'active_sites')
    if not L:raise ValueError('positive_active_sites')
    x=x0;buried=0;time=0;rows=[]
    for row in bins:
        s=step(x,row['a_s1'],row['b_s1'],row['c_s1'],row['duration_s'])
        buried+=L*row['c_s1']*s['integral_x_s'];time+=row['duration_s'];x=s['x']
        rows.append({'time_s':time,'x':x,'buried_defects_m2':buried})
    return {'final_occupancy':x,'buried_defects_m2':buried,'history':rows,
            'scope':'synthetic_const_bin_float_reference_not_physical_or_interval_certificate'}

def bounded_evolve(x_bounds,bins):
    """ODE comparison outer bounds, conditional on simultaneous rate bounds.
    Numeric endpoints are float-reference values, NOT rigorous outward intervals.
    Null a bounds means absent finite creation bound: retain support [0,1].
    Correlations are not asserted absent; the rectangle is an outer relaxation.
    """
    lo,hi=interval(x_bounds,'x')
    if hi>1:raise ValueError('occupancy_above_one')
    rows=[]
    for row in bins:
        dt=nonnegative(row['duration_s'],'duration')
        b0,b1=interval(row['b_s1'],'b');c0,c1=interval(row['c_s1'],'c')
        if row['a_s1'] is None:
            lo,hi=0.0,1.0;state='unknown_creation_support_only'
        else:
            a0,a1=interval(row['a_s1'],'a')
            lo=step(lo,a0,b1,c1,dt)['x'];hi=step(hi,a1,b0,c0,dt)['x'];state='conditional_rate_box_outer'
        rows.append({'x_bounds':[lo,hi],'status':state})
    return {'x_bounds':[lo,hi],'bins':rows,'numeric_status':'float_reference_not_rigorous_interval','nk':None,'density':None}

def correlated_kernel(cells):
    """Illustrative nonseparable response E*cos(theta)^2 per incident particle.
    Fluence is already per actual surface area; no extra cosine projection.
    This is NOT a universal defect/yield law or an actual RFEA inverse.
    """
    D=U=R=0
    for cell in cells:
        d=nonnegative(cell['dose_m2'],'dose');E=nonnegative(cell['energy_ev'],'energy')
        theta=nonnegative(cell['theta_deg'],'theta')
        if theta>90:raise ValueError('outgoing_cell')
        D+=d;U+=d*E;R+=d*E*math.cos(math.radians(theta))**2
    if not D:raise ValueError('positive_dose')
    return {'dose_m2':D,'mean_energy_ev':U/D,'mean_response_ev':R/D}

def mass_closed_optical(n0,rho_ratio):
    """Synthetic lossless fixed-polarizability Lorentz-Lorenz hypothesis only.
    L=(n²-1)/(n²+2)=C*rho, h/h0=1/rho_ratio, phase ∝ n*h.
    Invalid if stoichiometry, polarizability, porosity topology or k changes.
    """
    n0=nonnegative(n0,'n');r=nonnegative(rho_ratio,'rho_ratio')
    if n0<=1 or not r:raise ValueError('synthetic_dielectric_domain')
    l0=(n0*n0-1)/(n0*n0+2);l=l0*r
    if l>=1:raise ValueError('constitutive_singularity')
    n=math.sqrt((1+2*l)/(1-l));h=1/r
    alpha=(n0*n0-1)*(n0*n0+2)/(6*n0*n0)
    return {'n_ratio':n/n0,'h_ratio':h,'optical_thickness_ratio':n/n0*h,
            'd_log_nh_d_log_rho_at_baseline':alpha-1,'scope':'synthetic_hypothesis_not_material_calibration'}
