"""Small synthetic two-channel reference, not a machine digital twin.

NumPy only. Geometry uses metre/radian/second. Fluxes are particles m^-2 s^-1.
All plates are opaque to BOTH channels: separated paths cause channel selectivity.
"""
from __future__ import annotations
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
import json, math
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
E_CHARGE = 1.602176634e-19
METRICS = ('net_atoms_m2','ion_fluence_m2','incident_energy_J_m2','ion_only_s')


def load_config():
    return json.loads((ROOT/'data/synthetic_contract.json').read_text())


def rates(config, topology):
    c = Fraction(config['geometry']['carrier_rps'])
    q = config['topologies'][topology]
    if topology == 'D':
        w = c * (1 + Fraction(q['sun_teeth'], q['planet_teeth']))
        return {'carrier': c, 'sun': Fraction(0), 'output': w}
    if topology == 'C':
        # Three independent ideal constraints in the carrier frame.
        b = c - Fraction(q['ring_teeth'],q['lower_teeth'])*c
        a = b
        inp = c - Fraction(q['upper_teeth'],q['input_teeth'])*(a-c)
        w = c - Fraction(q['lower_teeth'],q['output_teeth'])*(b-c)
        return {'carrier':c,'ring':Fraction(0),'compound':b,'input':inp,'output':w}
    return {'carrier':c,'output':Fraction(q['output_rps'])}


def rational_period(rate_values):
    """Minimum T>0 with f_j*T integer for every specified exact rational rate."""
    f = [Fraction(v) for v in rate_values if v != 0]
    if not f:
        return None  # stationary: every T works, no least positive period
    den = math.lcm(*(x.denominator for x in f))
    gcd = math.gcd(*(abs(x.numerator)*(den//x.denominator) for x in f))
    return Fraction(den,gcd)


def pose(config, topology, times, local_points, normals=None):
    """Parallel axes only. Shapes: times T, local points P3 -> T,P,3."""
    g = config['geometry']; rr = rates(config, topology)
    t = np.atleast_1d(times).astype(float)
    p = np.atleast_2d(local_points).astype(float)
    phi = g['carrier_phase_rad']+2*np.pi*float(rr['carrier'])*t
    psi = g['workpiece_phase_rad']+2*np.pi*float(rr['output'])*t
    cp,sp = np.cos(psi)[:,None], np.sin(psi)[:,None]
    out = np.empty((len(t),len(p),3))
    out[:,:,0] = g['orbit_radius_m']*np.cos(phi)[:,None]+cp*p[:,0]-sp*p[:,1]
    out[:,:,1] = g['orbit_radius_m']*np.sin(phi)[:,None]+sp*p[:,0]+cp*p[:,1]
    out[:,:,2] = g['height_m']+p[:,2]
    n = np.tile([0.,0.,-1.],(len(p),1)) if normals is None else np.atleast_2d(normals)
    if len(n)==1: n = np.tile(n,(len(p),1))
    no = np.empty_like(out)
    no[:,:,0] = cp*n[:,0]-sp*n[:,1]
    no[:,:,1] = sp*n[:,0]+cp*n[:,1]
    no[:,:,2] = n[:,2]
    return out,no


def blocked(origin, destination, plate):
    """Segment/actual 3D thin rectangle intersection, open segment, closed edge."""
    a,b = np.asarray(origin),np.asarray(destination)
    m = np.asarray(plate['origin_L_m']); n=np.asarray(plate['normal_L'])
    u=np.asarray(plate['basis_u_L']); v=np.asarray(plate['basis_v_L'])
    d=b-a; den=np.einsum('...i,i->...',d,n)
    num=np.einsum('...i,i->...',m-a,n)
    lam=np.divide(num,den,out=np.full_like(den,np.inf),where=np.abs(den)>1e-14)
    hit=a+np.where(np.isfinite(lam),lam,0)[...,None]*d-m
    hu=np.einsum('...i,i->...',hit,u); hv=np.einsum('...i,i->...',hit,v)
    return (lam>0)&(lam<1)&(np.abs(hu)<=plate['half_width_m'][0])&(np.abs(hv)<=plate['half_width_m'][1])


def flux_at(config, times, x, n, case, uniform_vapor=False):
    """Returns net-atom flux, positive-ion flux, and ion-alone indicator."""
    t=np.asarray(times)[:,None]
    v=config['vapor']; i=config['ion']; clock=config['clock']
    sv=np.asarray(v['position_L_m']); ns=np.asarray(v['normal_L'])
    r=x-sv; dist=np.linalg.norm(r,axis=-1); ray=r/dist[...,None]
    mu_s=np.maximum(np.einsum('...i,i->...',ray,ns),0)
    mu_w=np.maximum(-np.sum(n*ray,axis=-1),0)
    if uniform_vapor:
        # An explicitly different, uniform parallel-vapor synthetic field.
        vapor_axial=np.einsum('...i,i->...',x-sv,ns)
        gv=v['reference_atom_flux_m2_s']*np.maximum(-np.einsum('...i,i->...',n,ns),0)*(vapor_axial>0)
        vapor_entry=x-vapor_axial[...,None]*ns
    else:
        gv=v['reference_atom_flux_m2_s']*v['reference_distance_m']**2*mu_s*mu_w/dist**2
        vapor_entry=sv
    d=np.asarray(i['direction_L']); si=np.asarray(i['origin_L_m'])
    u=np.asarray(i['basis_u_L']); vv=np.asarray(i['basis_v_L'])
    ri=x-si; axial=np.einsum('...i,i->...',ri,d)
    transverse_u=np.einsum('...i,i->...',ri,u); transverse_v=np.einsum('...i,i->...',ri,vv)
    gi=i['peak_beam_normal_flux_m2_s']*np.exp(-(transverse_u**2+transverse_v**2)/(2*i['sigma_m']**2))
    gi*=np.maximum(-np.einsum('...i,i->...',n,d),0)*(axial>0)
    beam_entry=x-axial[...,None]*d
    for name in config['cases'][case]:
        plate=config['plates'][name]
        gv*=~blocked(vapor_entry,x,plate)
        gi*=~blocked(beam_entry,x,plate)
    vg=clock['vapor_gate_s']; ig=clock['ion_gate_s']
    gv*=((t>=vg[0])&(t<vg[1]))
    gi*=((t>=ig[0])&(t<ig[1]))
    # Unit retention and zero resputtering, explicitly fixed in contract.
    return gv,gi,(gi>0)&(gv==0)


def fields(config, topology, times, points, case, uniform_vapor=False):
    x,n=pose(config,topology,times,points)
    gv,gi,alone=flux_at(config,times,x,n,case,uniform_vapor)
    return np.stack((gv,gi,gi*config['ion']['energy_per_ion_eV']*E_CHARGE,alone.astype(float)),axis=-1)


def disk_grid(radius,nr,na,edge_count):
    """Gauss in u=r²/a² and equally spaced midpoint azimuth; edges zero weight."""
    q,w=np.polynomial.legendre.leggauss(nr)
    r=radius*np.sqrt((q+1)/2)
    th=2*np.pi*(np.arange(na)+.5)/na
    pts=np.stack((np.repeat(r,na)*np.tile(np.cos(th),nr),np.repeat(r,na)*np.tile(np.sin(th),nr),np.zeros(nr*na)),axis=1)
    weights=np.repeat(w/2/na,na)
    et=2*np.pi*np.arange(edge_count)/edge_count
    edges=np.stack((radius*np.cos(et),radius*np.sin(et),np.zeros(edge_count)),axis=1)
    return np.concatenate((pts,edges,[[0,0,0]])),np.r_[weights,np.zeros(edge_count+1)]


def diagnostic_grid(radius):
    pts=[[0,0,0]]
    for r,n in [(radius/2,8),(radius,12)]:
        pts.extend([[r*np.cos(a),r*np.sin(a),0] for a in 2*np.pi*np.arange(n)/n])
    return np.array(pts),np.ones(len(pts))/len(pts)


def output_values(config,integrals):
    a=np.asarray(integrals,dtype=float); net=a[...,0]; ion=a[...,1]
    rat=np.divide(ion,net,out=np.full_like(net,np.nan),where=net>0)
    return {'h_nm':net/config['vapor']['net_atomic_density_m3']*1e9,
            'net_atoms_m2':net,'ion_fluence_m2':ion,'incident_energy_J_m2':a[...,2],
            'ion_to_net_atom_ratio':rat,'eV_per_net_atom':rat*config['ion']['energy_per_ion_eV'],
            'ion_only_s':a[...,3]}


def statistics(values,weights):
    z=np.asarray(values); w=np.asarray(weights); valid=(w>0)&np.isfinite(z)
    if not np.any(valid): return {'mean':None,'cv':None,'sample_pv':None,'minimum':None,'maximum':None}
    w=w[valid]/w[valid].sum(); mean=float(w@z[valid]); variance=float(w@((z[valid]-mean)**2))
    allz=z[np.isfinite(z)]
    return {'mean':mean,'cv':math.sqrt(variance)/mean if mean>0 else None,
            'sample_pv':float((allz.max()-allz.min())/mean) if mean>0 else None,
            'minimum':float(allz.min()),'maximum':float(allz.max())}


def midpoint(config,topology,points,steps,cases=None,uniform_vapor=False):
    cases=list(config['cases']) if cases is None else cases
    end=config['clock']['layer_end_s']; start=config['clock']['layer_start_s']
    step=(end-start)/steps; sums={c:np.zeros((len(points),4)) for c in cases}
    for j in range(0,steps,256):
        t=start+(np.arange(j,min(j+256,steps))+.5)*step
        for case in cases:
            sums[case]+=np.sum(fields(config,topology,t,points,case,uniform_vapor),axis=0)*step
    return sums


def event_thresholds(config):
    """Exact world x/y thresholds at substrate z, derived from 3D ray geometry.

    Only for the horizontal thin-plate/flat-workpiece synthetic contract.
    Full 3D segment intersection is still used to compute visibility.
    """
    H=config['geometry']['height_m']; sv=np.array(config['vapor']['position_L_m']); d=np.array(config['ion']['direction_L'])
    out=[]
    for plate in config['plates'].values():
        m=np.array(plate['origin_L_m']); half=plate['half_width_m']
        lam=(m[2]-sv[2])/(H-sv[2])
        if 0<lam<1:
            for axis in (0,1):
                for sign in (-1,1): out.append((axis,float(sv[axis]+(m[axis]+sign*half[axis]-sv[axis])/lam)))
        if 0 < m[2] < H:
            for axis in (0,1):
                for sign in (-1,1): out.append((axis,float(m[axis]+sign*half[axis]+(H-m[2])*d[axis]/d[2])))
    return sorted(set(out))


class EventIntegrator:
    """Fixed scan plus second-derivative empty-interval/monotonicity checks.

    No Monte Carlo. Sign-changing brackets with certified nonzero derivative are
    bisected. Same-sign brackets are discarded only when the linear interpolation
    error bound excludes zero. Ambiguous tiny brackets are retained and reported.
    Arithmetic is floating point; this is NOT outward-rounded interval arithmetic.
    """
    def __init__(self,config,topology,scan=8192,root_tol=1e-10):
        self.config=config; self.topology=topology; self.root_tol=root_tol
        self.start=config['clock']['layer_start_s']; self.end=config['clock']['layer_end_s']
        rr=rates(config,topology); g=config['geometry']
        self.wc=2*np.pi*float(rr['carrier']); self.ww=2*np.pi*float(rr['output'])
        self.pc=g['carrier_phase_rad'];self.pw=g['workpiece_phase_rad'];self.R=g['orbit_radius_m']
        self.scan=scan;self.ts=np.linspace(self.start,self.end,scan+1)
        self.cs=np.cos(self.pc+self.wc*self.ts);self.ss=np.sin(self.pc+self.wc*self.ts)
        self.cw=np.cos(self.pw+self.ww*self.ts);self.sw=np.sin(self.pw+self.ww*self.ts)
        self.thresholds=event_thresholds(config)
        self.root_count=0;self.ambiguous_count=0;self.width_sum=0.;self.max_width_sum=0.
        self.pose_scan_evaluations=0;self.flux_evaluations=0;self.subdivision_count=0

    def roots(self,p,axis,threshold,grid_values):
        u,v=p[:2];radius=math.hypot(u,v)
        if abs(threshold)>self.R+radius+1e-14: return [],0.,0
        M=self.R*self.wc**2+radius*self.ww**2
        if M == 0:
            return [],0.,0  # Constant path, even identically on an opaque edge.
        def f(t):
            a=self.pc+self.wc*t;b=self.pw+self.ww*t
            return (self.R*math.cos(a)+u*math.cos(b)-v*math.sin(b) if axis==0 else self.R*math.sin(a)+u*math.sin(b)+v*math.cos(b))-threshold
        def df(t):
            a=self.pc+self.wc*t;b=self.pw+self.ww*t
            return (-self.R*self.wc*math.sin(a)-self.ww*(u*math.sin(b)+v*math.cos(b)) if axis==0 else self.R*self.wc*math.cos(a)+self.ww*(u*math.cos(b)-v*math.sin(b)))
        y=grid_values-threshold;h=self.ts[1]-self.ts[0]
        # All intervals that are not excluded by a same-sign interpolation bound.
        same=(y[:-1]*y[1:]>0)
        certified=same&(np.minimum(np.abs(y[:-1]),np.abs(y[1:]))>M*h*h/8+1e-14)
        ids=np.flatnonzero(~certified); found=[];width=0.;ambiguous=0
        stack=[(self.ts[k],self.ts[k+1],y[k],y[k+1]) for k in ids]
        while stack:
            a,b,fa,fb=stack.pop();dt=b-a;mid=(a+b)/2
            if fa*fb>0 and min(abs(fa),abs(fb))>M*dt*dt/8+1e-14: continue
            mono=abs(df(mid))>M*dt/2+1e-14
            if mono and fa*fb>0: continue  # monotone and both endpoints one sign
            if dt<=self.root_tol:
                found.append(mid);width+=dt
                ambiguous+=int(not mono)
                continue
            if mono and fa*fb<=0:
                # Bisection of a unique monotone root, including exact endpoints.
                while b-a>self.root_tol:
                    mid=(a+b)/2;fm=f(mid)
                    if fa*fm<=0: b=mid;fb=fm
                    else: a=mid;fa=fm
                found.append((a+b)/2);width+=b-a
                continue
            fm=f(mid);self.subdivision_count+=1
            stack.extend(((a,mid,fa,fm),(mid,b,fm,fb)))
            if self.subdivision_count>200000: raise RuntimeError('fixed event subdivision budget exceeded')
        return found,width,ambiguous

    def point_events(self,p):
        if abs(p[2])>1e-14: raise ValueError('event solver requires flat z=0 local points')
        x=self.R*self.cs+p[0]*self.cw-p[1]*self.sw
        y=self.R*self.ss+p[0]*self.sw+p[1]*self.cw
        self.pose_scan_evaluations+=len(self.ts)
        events=[self.start,self.end]
        for gate in ('vapor_gate_s','ion_gate_s'):
            events.extend(t for t in self.config['clock'][gate] if self.start<t<self.end)
        width=0.;count=0;amb=0
        for axis,threshold in self.thresholds:
            rr,ww,aa=self.roots(p,axis,threshold,(x,y)[axis]);events.extend(rr);width+=ww;count+=len(rr);amb+=aa
        events=sorted(t for t in events if self.start<=t<=self.end)
        unique=[events[0]]
        for t in events[1:]:
            if t-unique[-1]>self.root_tol/4: unique.append(t)
        self.root_count+=count;self.ambiguous_count+=amb;self.width_sum+=width;self.max_width_sum=max(width,self.max_width_sum)
        return np.array(unique)

    def integrate(self,points,order=16,cases=None,uniform_vapor=False,split=1):
        cases=list(self.config['cases']) if cases is None else cases
        if uniform_vapor and any(self.config['cases'][case] for case in cases):
            raise NotImplementedError('uniform parallel-vapor event solver supports no-plate cases only; instantaneous flux handles its rays')
        res={case:np.zeros((len(points),4)) for case in cases}
        z,w=np.polynomial.legendre.leggauss(order)
        for k,p in enumerate(points):
            e=self.point_events(p)
            if split>1: e=np.unique(np.concatenate([np.linspace(a,b,split+1) for a,b in zip(e[:-1],e[1:])]))
            mid=(e[:-1]+e[1:])/2;half=(e[1:]-e[:-1])/2
            ts=(mid[:,None]+half[:,None]*z).reshape(-1);ws=(half[:,None]*w).reshape(-1)
            for case in cases:
                val=fields(self.config,self.topology,ts,p[None,:],case,uniform_vapor)[:,0,:]
                res[case][k]=ws@val;self.flux_evaluations+=2*len(ts)
        return res

    def report(self):
        return {'scan_intervals':self.scan,'root_count':self.root_count,'ambiguous_tiny_brackets':self.ambiguous_count,'root_tol_s':self.root_tol,'max_point_root_bracket_total_s':self.max_width_sum,'pose_scan_evaluations':self.pose_scan_evaluations,'channel_flux_evaluations':self.flux_evaluations,'subdivision_count':self.subdivision_count,'bound_status':'analytic exact-arithmetic root bracketing bounds; floating-point implementation not interval-certified'}


def transformed_scene(config,Q,a):
    c=deepcopy(config)
    def point(x): return (Q@np.asarray(x)+a).tolist()
    def vector(x): return (Q@np.asarray(x)).tolist()
    c['vapor']['position_L_m']=point(c['vapor']['position_L_m']);c['vapor']['normal_L']=vector(c['vapor']['normal_L'])
    c['ion']['origin_L_m']=point(c['ion']['origin_L_m'])
    for key in ('direction_L','basis_u_L','basis_v_L'): c['ion'][key]=vector(c['ion'][key])
    for plate in c['plates'].values():
        plate['origin_L_m']=point(plate['origin_L_m'])
        for key in ('basis_u_L','basis_v_L','normal_L'): plate[key]=vector(plate[key])
    return c
