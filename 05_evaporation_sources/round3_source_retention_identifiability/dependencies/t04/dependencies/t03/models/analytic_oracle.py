"""Forward-mode derivative of closed-form, piecewise integrated affine slice.
No AD through bool visibility. Independent expressions from segment quadrature.
For tests only; branch selection must be unambiguous and v nonzero.
"""
import numpy as np
from event_reference import PARAMETERS

class Dual:
    def __init__(self,v,d=None):self.v=float(v);self.d=np.zeros(7) if d is None else np.asarray(d,dtype=float)
    def __add__(self,o):o=dual(o);return Dual(self.v+o.v,self.d+o.d)
    __radd__=__add__
    def __neg__(self):return Dual(-self.v,-self.d)
    def __sub__(self,o):return self+-dual(o)
    def __rsub__(self,o):return dual(o)+-self
    def __mul__(self,o):o=dual(o);return Dual(self.v*o.v,self.d*o.v+self.v*o.d)
    __rmul__=__mul__
    def __truediv__(self,o):o=dual(o);return Dual(self.v/o.v,(self.d*o.v-self.v*o.d)/(o.v*o.v))
    def __rtruediv__(self,o):return dual(o)/self
    def atan(self):return Dual(np.arctan(self.v),self.d/(1+self.v*self.v))
def dual(x):return x if isinstance(x,Dual) else Dual(x)

def exact_value_gradient(sc,s_node=0.):
    sc.validate();v=sc.velocity_m_s
    if abs(v)<=sc.transverse_floor_m_s or sc.shadow_boundary_uncertainty_m:raise ValueError('ordinary differentiable branch required')
    P={k:Dual(getattr(sc,k),np.eye(7)[i]) for i,k in enumerate(PARAMETERS)}
    s=P['source_shift_m']+s_node;H=P['height_m'];b=P['plate_shift_m'];a=P['half_width_m']
    lower=[s+(b-a-s)*H/z for z in (sc.z_near_m,sc.z_far_m)]
    upper=[s+(b+a-s)*H/z for z in (sc.z_near_m,sc.z_far_m)]
    if min(abs(lower[0].v-lower[1].v),abs(upper[0].v-upper[1].v))<=sc.face_guard_m:raise ValueError('face tie')
    l=min(lower,key=lambda x:x.v);r=max(upper,key=lambda x:x.v)
    d=sc.x0_m+P['target_shift_m']+v*P['clock_offset_s']-s
    ts=sorted([(l-sc.x0_m-P['target_shift_m'])/v-P['clock_offset_s'],(r-sc.x0_m-P['target_shift_m'])/v-P['clock_offset_s']],key=lambda x:x.v)
    if any(min(abs(t.v-sc.t0),abs(t.v-sc.t1))<=sc.event_guard_s for t in ts):raise ValueError('endpoint tie')
    if ts[1].v-ts[0].v<=2*sc.event_guard_s:raise ValueError('event order unresolved')
    def F(t):
        y=v*t+d;den=H*H+y*y
        f0=y/(2*den)+(y/H).atan()/(2*H)
        f1=-H*H/(2*den)
        return P['amplitude']/v*((sc.q0-sc.q1_per_s*d/v)*f0+sc.q1_per_s/v*f1)
    total=F(sc.t1)-F(sc.t0)
    lo=ts[0] if ts[0].v>sc.t0 else dual(sc.t0)
    hi=ts[1] if ts[1].v<sc.t1 else dual(sc.t1)
    if hi.v>lo.v:total=total-(F(hi)-F(lo))
    return total.v,total.d
