"""T02-r3 bounded event-aware reference. No fitted machine data, no global CAD.
SI; column vectors, lab-frame left perturbations. See reports before use.
"""
from dataclasses import dataclass, asdict
import math
import numpy as np
from frozen.robust_mask_v02 import RectangleMask, Verdict
from frozen.t01_pose_reference import rigid_jacobians

PARAMETERS = ('target_shift_m','source_shift_m','clock_offset_s','amplitude',
              'plate_shift_m','half_width_m','height_m')
UNITS = ('m','m','s','1','m','m','m')


def finite(x,shape=None):
    a=np.asarray(x,dtype=float)
    if not np.all(np.isfinite(a)) or (shape is not None and a.shape!=shape):
        raise ValueError('finite value with declared shape required')
    return a


def flux_directional(x,n,s,ns,dx,dn,ds,dns,exponent=1.,amplitude=1.,d_amplitude=0.,angular_guard=1e-12):
    """Derivative of A (ns.u)^m (-n.u) / r^2 in strictly front-facing domain.
    Does not differentiate visibility. Normals must be unit, dn/dns tangent.
    Returns None at angular boundary; zero only in a strictly back-facing domain.
    """
    x,n,s,ns,dx,dn,ds,dns=[finite(z,(3,)) for z in (x,n,s,ns,dx,dn,ds,dns)]
    m,A,dA,guard=[float(finite(z,())) for z in (exponent,amplitude,d_amplitude,angular_guard)]
    if m<0 or A<0 or guard<0:raise ValueError('nonnegative exponent/amplitude/guard required')
    if any(abs(z@z-1)>1e-10 for z in (n,ns)) or abs(n@dn)>1e-10 or abs(ns@dns)>1e-10:
        raise ValueError('unit normals and tangent normal directions required')
    rvec=x-s;r=float(np.linalg.norm(rvec))
    if r<=0:raise ValueError('coincident source and target')
    u=rvec/r;drvec=dx-ds;dr=float(u@drvec);du=(drvec-u*dr)/r
    a=float(ns@u);b=float(-n@u)
    if a < -guard or b < -guard:return {'status':'smooth_zero_backface','value':0.,'directional':0.}
    if a<=guard or b<=guard:return {'status':'angular_boundary_unresolved','value':max(a,0)**m*max(b,0)*A/r**2 if a>0 else 0.,'directional':None}
    da=float(dns@u+ns@du);db=float(-dn@u-n@du)
    base=a**m*b/r**2
    derivative=dA*base+A/r**2*((m*a**(m-1)*da*b if m else 0.)+a**m*db)-2*A*base*dr/r
    return {'status':'smooth_front','value':A*base,'directional':derivative}


@dataclass(frozen=True)
class Scene:
    t0: float=0.
    t1: float=2.
    x0_m: float=-0.4
    velocity_m_s: float=0.4
    target_shift_m: float=0.03
    source_shift_m: float=0.
    clock_offset_s: float=0.
    amplitude: float=1.
    plate_shift_m: float=0.
    half_width_m: float=0.08
    height_m: float=1.
    z_near_m: float=0.4
    z_far_m: float=0.6
    half_y_m: float=0.15
    q0: float=1.
    q1_per_s: float=0.3
    event_guard_s: float=1e-10
    face_guard_m: float=1e-12
    transverse_floor_m_s: float=1e-10
    shadow_boundary_uncertainty_m: float=0.

    def validate(self):
        for k,v in asdict(self).items():float(finite(v,()))
        if not self.t0<self.t1 or not 0<self.z_near_m<self.z_far_m<self.height_m:
            raise ValueError('ordered times and source < near < far < target planes required')
        if self.half_width_m<=0 or self.half_y_m<=0 or self.amplitude<=0:
            raise ValueError('strictly positive sizes/amplitude required')
        if min(self.q0+self.q1_per_s*self.t0,self.q0+self.q1_per_s*self.t1)<0:
            raise ValueError('nonnegative reference-clock source rate required')
        if min(self.event_guard_s,self.face_guard_m,self.transverse_floor_m_s,self.shadow_boundary_uncertainty_m)<0:
            raise ValueError('nonnegative guards and uncertainty required')
        return self

    def mask(self):
        self.validate()
        return RectangleMask([self.plate_shift_m,0.,(self.z_near_m+self.z_far_m)/2],
            [[1,0,0],[0,1,0],[0,0,1]],self.half_width_m,self.half_y_m,self.z_far_m-self.z_near_m)


def x_at(t,sc):return sc.x0_m+sc.target_shift_m+sc.velocity_m_s*(np.asarray(t)+sc.clock_offset_s)


def rate_kernel(t,s_node,sc):
    """Point-source cosine/cosine geometry, normalized transfer in m^-2."""
    y=x_at(t,sc)-(s_node+sc.source_shift_m);H=sc.height_m
    q=sc.q0+sc.q1_per_s*np.asarray(t)
    return sc.amplitude*q*H**2/(H**2+y*y)**2


def kernel_jacobian(t,s_node,sc):
    t=np.asarray(t);y=x_at(t,sc)-(s_node+sc.source_shift_m);H=sc.height_m
    f=rate_kernel(t,s_node,sc);fx=-4*y*f/(H*H+y*y)
    return np.stack((fx,-fx,sc.velocity_m_s*fx,f/sc.amplitude,
                    np.zeros_like(f),np.zeros_like(f),f*(2/H-4*H/(H*H+y*y))),axis=-1)


def primitive(t,s_node,sc):
    """Closed primitive for affine reference-clock source rate. v != 0."""
    v=sc.velocity_m_s;H=sc.height_m
    if v==0:raise ValueError('use stationary branch for zero speed')
    d=sc.x0_m+sc.target_shift_m+v*sc.clock_offset_s-(s_node+sc.source_shift_m)
    y=v*np.asarray(t)+d
    p0=y/(2*(H*H+y*y))+np.arctan(y/H)/(2*H)
    p1=-H*H/(2*(H*H+y*y))
    return sc.amplitude/v*((sc.q0-sc.q1_per_s*d/v)*p0+sc.q1_per_s/v*p1)


def integral(a,b,s_node,sc):
    if b<=a:return 0.
    if sc.velocity_m_s==0:
        H=sc.height_m;y=float(x_at(0,sc))-(s_node+sc.source_shift_m)
        return sc.amplitude*H*H/(H*H+y*y)**2*(sc.q0*(b-a)+sc.q1_per_s*(b*b-a*a)/2)
    return float(primitive(b,s_node,sc)-primitive(a,s_node,sc))


def shadow_limits(s_node,sc):
    """Exact algebraic projection of this y=0 slab family, float evaluation.
    L=min near/far left; U=max near/far right. No sampling to discover events.
    """
    sc.validate();s=float(finite(s_node,()))+sc.source_shift_m;H=sc.height_m
    candidates=[]
    for sign in (-1,1):
        row=[]
        for z in (sc.z_near_m,sc.z_far_m):
            edge=sc.plate_shift_m+sign*sc.half_width_m
            b=s+(edge-s)*H/z
            j=np.array([0.,1-H/z,0.,0.,H/z,sign*H/z,(edge-s)/z])
            row.append((b,j,z))
        candidates.append(row)
    low=min(candidates[0],key=lambda a:a[0]);high=max(candidates[1],key=lambda a:a[0])
    tie=any(abs(row[0][0]-row[1][0])<=sc.face_guard_m for row in candidates)
    return low,high,tie


def event_map(s_node,sc):
    low,high,tie=shadow_limits(s_node,sc);v=sc.velocity_m_s
    if v==0:
        return {'status':'tangent_or_stationary_unresolved','events':[],'shadow_limits':[low[0],high[0]]}
    events=[]
    for label,bnd in [('lower',low),('upper',high)]:
        b,j,z=bnd;t=(b-sc.x0_m-sc.target_shift_m)/v-sc.clock_offset_s
        jt=j/v;jt[0]-=1/v;jt[2]-=1
        events.append({'time_s':float(t),'time_jacobian':jt,'boundary':label,'active_z_m':z,
                       'guard_speed_m_s':v,'jump_V':(-1 if label=='lower' else 1)*(1 if v>0 else -1)})
    events.sort(key=lambda a:a['time_s'])
    state=('topology_switch_unresolved' if tie else ('tangent_or_stationary_unresolved' if abs(v)<=sc.transverse_floor_m_s else 'differentiable_conditional'))
    if any(min(abs(e['time_s']-sc.t0),abs(e['time_s']-sc.t1))<=sc.event_guard_s for e in events):state='endpoint_event_unresolved'
    if events[1]['time_s']-events[0]['time_s']<=2*sc.event_guard_s:state='event_order_unresolved'
    if sc.shadow_boundary_uncertainty_m>0:state='geometry_unknown'
    return {'status':state,'events':events,'shadow_limits':[low[0],high[0]],'face_tie':tie}


def visible_intervals(s_node,sc):
    ev=event_map(s_node,sc)
    if not ev['events']:
        lo,hi=ev['shadow_limits'];x=float(x_at(0,sc))
        return ([] if lo<=x<=hi else [(sc.t0,sc.t1)]),ev
    a,b=[e['time_s'] for e in ev['events']]
    intervals=[]
    if sc.t0<min(a,sc.t1):intervals.append((sc.t0,min(a,sc.t1)))
    if max(b,sc.t0)<sc.t1:intervals.append((max(b,sc.t0),sc.t1))
    return intervals,ev


def conditional_unknown_envelope(s_node,sc):
    """External target-shadow boundary uncertainty, NOT a ray-local margin.
    Conditional algebraic envelope with ordinary float arithmetic, not interval proof.
    """
    intervals,ev=visible_intervals(s_node,sc)
    if not ev['events']:return {'lower':0.,'upper':integral(sc.t0,sc.t1,s_node,sc),'status':'unresolved_stationary_envelope'}
    a,b=[e['time_s'] for e in ev['events']];eps=sc.shadow_boundary_uncertainty_m/abs(sc.velocity_m_s)
    total=integral(sc.t0,sc.t1,s_node,sc)
    def blocked(l,r):return integral(max(sc.t0,l),min(sc.t1,r),s_node,sc)
    return {'lower':max(0.,total-blocked(a-eps,b+eps)),
            'upper':max(0.,total-blocked(a+eps,b-eps)),
            'status':'conditional_nonnegative_flux_envelope_not_strict_certificate',
            'event_radius_s':eps}


def evaluate(s_node,sc,order=32):
    sc.validate()
    if type(order) is not int or order<2 or order>4096:raise ValueError('quadrature order 2..4096 required')
    intervals,ev=visible_intervals(s_node,sc)
    value=math.fsum(integral(a,b,s_node,sc) for a,b in intervals)
    out={'value_s_m2':value,'sensitivity_status':ev['status'],'parameters':list(PARAMETERS),
         'gradient':None,'smooth_gradient':None,'event_gradient':None,
         'events':[{k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in e.items()} for e in ev['events']],
         'visible_intervals_s':intervals,'certificate':'conditional_float_algebra_not_strict_interval',
         'source_error':'not_assessed_for_continuous_source','time_error':'smooth_segment_quadrature_estimate_only'}
    if sc.shadow_boundary_uncertainty_m:out['uncertainty_envelope']=conditional_unknown_envelope(s_node,sc)
    if ev['status']!='differentiable_conditional':return out
    nodes,weights=np.polynomial.legendre.leggauss(order)
    smooth=np.zeros(7)
    for a,b in intervals:
        tt=(a+b)/2+(b-a)*nodes/2
        smooth+=(b-a)/2*np.sum(weights[:,None]*kernel_jacobian(tt,s_node,sc),axis=0)
    event=np.zeros(7)
    for e in ev['events']:
        if sc.t0<e['time_s']<sc.t1:
            # f^- - f^+ = - jump_V * unmasked_kernel
            event-=e['jump_V']*float(rate_kernel(e['time_s'],s_node,sc))*e['time_jacobian']
    out.update(gradient=(smooth+event).tolist(),smooth_gradient=smooth.tolist(),event_gradient=event.tolist())
    return out


def classify_ray(t,s_node,sc,local_margin_m=0.):
    """Independent rational encoded-ray predicate; never cast verdict to bool."""
    sc.validate()
    return sc.mask().classify([float(s_node+sc.source_shift_m),0.,0.],
              [float(x_at(float(finite(t,())),sc)),0.,sc.height_m],local_margin_m=local_margin_m)


def linear_output_variance(jac,covariance,status):
    if status!='differentiable_conditional':return {'variance':None,'status':'linearization_not_admitted'}
    J=finite(jac);C=finite(covariance)
    if J.ndim!=1 or C.shape!=(len(J),len(J)) or not np.allclose(C,C.T,atol=1e-14,rtol=0):raise ValueError('symmetric matching covariance required')
    e=np.linalg.eigvalsh(C)
    if np.min(e)<-1e-12*max(1e-300,float(np.linalg.norm(C,2))):raise ValueError('PSD covariance required')
    return {'variance':max(0.,float(J@C@J)),'status':'conditional_first_order_not_coverage_certificate'}


def grazing_duration(p,curvature=1.):
    p=float(finite(p,()));a=float(finite(curvature,()))
    if a<=0:raise ValueError('positive curvature required')
    # Infinite local parabola g=a*t^2-p; blocked g<=0.
    return {'blocked_duration_s':2*math.sqrt(p/a) if p>0 else 0.,
            'derivative':1/math.sqrt(a*p) if p>0 else (0. if p<0 else None),
            'status':'grazing_topology_unresolved' if p==0 else 'branch_conditional'}
