"""Finite-case, event-aware reference: convex shadow projection, analytic y.
Binary64 + QUADPACK estimates, not certified interval arithmetic.
Only the two geometries from the frozen synthetic contract are admitted.
"""
import math,time
from functools import lru_cache
from itertools import product
import numpy as np
from scipy.integrate import quad
import legacy_adapter as legacy

class Budget:
    def __init__(self,limit=30_000_000,seconds=900):
        self.limit=limit;self.seconds=seconds;self.start=time.monotonic()
        self.counts={'source_slice_evaluations':0,'analytic_endpoint_evaluations':0,'ray_evaluations':0,'projection_evaluations':0,'oracle_evaluations':0}
    def add(self,key,n=1):
        self.counts[key]+=int(n)
        if sum(self.counts.values())>self.limit:raise RuntimeError('work budget exhausted')
        if time.monotonic()-self.start>self.seconds:raise RuntimeError('wall budget exhausted')
    def report(self):return dict(self.counts,total_work_units=sum(self.counts.values()),limit=self.limit,wall_seconds=time.monotonic()-self.start,wall_limit_seconds=self.seconds)

def hull(points):
    pts=sorted(set(tuple(p) for p in points))
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo=[];hi=[]
    for p in pts:
        while len(lo)>=2 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi)>=2 and cross(hi[-2],hi[-1],p)<=0:hi.pop()
        hi.append(p)
    return np.array(lo[:-1]+hi[:-1])

def cross2(a,b):return a[...,0]*b[...,1]-a[...,1]*b[...,0]

class Model:
    def __init__(self,point,channel,budget=None):
        c=legacy.config();self.c=c;self.point=np.array(point,dtype=float);self.channel=channel;self.budget=budget
        if channel not in ('vapor','ion') or self.point.shape!=(3,) or not np.isfinite(self.point).all() or self.point[2]!=0 or np.linalg.norm(self.point[:2])>.06+1e-14:
            raise ValueError('only frozen D flat disk points within radius 0.06m admitted')
        q=c[channel];self.a=q['radius_m'];self.exponent=q['exponent'];self.Qtotal=q['total_atoms_s' if channel=='vapor' else 'total_ions_s']
        self.center=np.array(q['position_L_m' if channel=='vapor' else 'origin_L_m'])
        self.Q=np.eye(3) if channel=='vapor' else np.column_stack([q['basis_u_L'],q['basis_v_L'],q['direction_L']])
        self.mask=legacy.plates(c,'both')[0 if channel=='vapor' else 1]
        p=self.mask;half=np.array([p.half_width_m,p.half_height_m,p.thickness_m/2])
        self.vertices=np.array([p.center_m+np.array(sign)*half for sign in product([-1,1],repeat=3)])
        self.slope_limit=.5 if channel=='vapor' else 6.
        self.source_quad_warnings=[];self.max_source_abserr=0.;self.source_calls=0
    def position(self,t):
        # Independent direct formula matching the frozen parallel D contract.
        phi=math.pi*t/2;psi=13*math.pi*t/6;x,y,z=self.point
        return np.array([.312*math.cos(phi)+x*math.cos(psi)-y*math.sin(psi),.312*math.sin(phi)+x*math.sin(psi)+y*math.cos(psi),.6+z])
    def projected(self,t):
        if self.budget:self.budget.add('projection_evaluations')
        X=self.position(t);n=self.Q[:,2];dX=(X-self.center)@n;dv=(self.vertices-self.center)@n
        if np.any(dv<=0) or np.any(dv>=dX):raise ValueError('source-plane projection contract not satisfied')
        projected=X+(dX/(dX-dv))[:,None]*(self.vertices-X)
        return X,hull((projected-self.center)@self.Q[:,:2])
    def cover_slack(self,t):
        _,P=self.projected(t);E=np.roll(P,-1,axis=0)-P
        distances=cross2(E,-P)/np.linalg.norm(E,axis=1)
        if np.all(distances>=0):return float(distances.min()-self.a)
        # min support over all unit directions = -distance(0, polygon) outside.
        u=np.clip(-np.sum(P*E,axis=1)/np.sum(E*E,axis=1),0,1)
        nearest=np.min(np.linalg.norm(P+u[:,None]*E,axis=1))
        return float(-nearest-self.a)
    def support_intervals(self,t0,t1,leaf_width=2e-6):
        if not (0<=t0<t1<=7.3) or not math.isfinite(leaf_width) or leaf_width<=0:
            raise ValueError('invalid support interval or leaf width')
        # g(t) is Lipschitz. Floating guard is deliberately disclosed, not a
        # proof of correctly-rounded trig/hull arithmetic. Results conditional.
        todo=[(t0,t1)];covered=[];visible=[];unknown=[]
        while todo:
            a,b=todo.pop();mid=(a+b)/2;g=self.cover_slack(mid);bound=self.slope_limit*(b-a)/2+1e-11
            if g>bound:covered.append((a,b))
            elif g < -bound:visible.append((a,b))
            elif b-a<=leaf_width:unknown.append((a,b))
            else:todo.extend([(a,mid),(mid,b)])
        return {'covered':sorted(covered),'visible':sorted(visible),'unknown':sorted(unknown),'covered_s':sum(b-a for a,b in covered),'unknown_s':sum(b-a for a,b in unknown),'slope_limit_m_s':self.slope_limit,'floating_guard_m':1e-11,'status':'conditional_lipschitz_enclosure_not_validated_float'}
    def source_flux(self,t,epsabs=2e-8,epsrel=2e-7,limit=100):
        if not (0<=t<=7.3) or epsabs<=0 or epsrel<=0 or limit<8:
            raise ValueError('invalid source integration control')
        X,P=self.projected(t);a=self.a;edges=np.roll(P,-1,axis=0)-P
        distances=cross2(edges,-P)/np.linalg.norm(edges,axis=1)
        if np.all(distances>=a):return 0.
        breaks=[-a,a]
        breaks.extend(v[0] for v in P if -a<v[0]<a)
        # Circle/edge intersections are the exact locations at which clipped
        # integration limits change topology (up to binary64 construction).
        for v,e in zip(P,edges):
            A=e@e;B=2*(v@e);C=v@v-a*a;disc=B*B-4*A*C
            if disc>=0:
                for u in [(-B-math.sqrt(disc))/(2*A),(-B+math.sqrt(disc))/(2*A)]:
                    if 0<u<1:breaks.append(float((v+u*e)[0]))
        breaks=sorted(set(max(-a,min(a,float(v))) for v in breaks))
        local=(X-self.center)@self.Q
        def anti(y,x):
            z=y-local[1];A=local[2]**2+(x-local[0])**2
            if self.exponent==1:
                I=z/(2*A*(A+z*z))+math.atan(z/math.sqrt(A))/(2*A**1.5)
            elif self.exponent==12:
                I=z/(A*math.sqrt(A+z*z))
                for s in [2.5,3.5,4.5,5.5,6.5,7.5]:I=z/(2*A*(s-1)*(A+z*z)**(s-1))+(2*s-3)/(2*A*(s-1))*I
            else:raise ValueError('only pre-registered emission exponents 1 and 12')
            if self.budget:self.budget.add('analytic_endpoint_evaluations')
            source_z=self.center[2]+self.Q[2,0]*x # Q[2,1]==0 fixed contract
            return (self.exponent+1)/(2*math.pi)*local[2]**self.exponent*(X[2]-source_z)*I/(math.pi*a*a)
        def slice_integral(x):
            if self.budget:self.budget.add('source_slice_evaluations')
            y=math.sqrt(max(0.,a*a-x*x));lo=-y;hi=y;bl=-math.inf;bh=math.inf
            for v,e in zip(P,edges):
                # ccw inside: e.x*(y-v.y)-e.y*(x-v.x)>=0
                if e[0]>0:bl=max(bl,v[1]+e[1]*(x-v[0])/e[0])
                elif e[0]<0:bh=min(bh,v[1]+e[1]*(x-v[0])/e[0])
                elif -e[1]*(x-v[0])<0:bl=math.inf;bh=-math.inf;break
            bl=max(lo,bl);bh=min(hi,bh)
            if bl>=bh:return anti(hi,x)-anti(lo,x)
            # Integrate only visible intervals, avoiding full-minus-blocked
            # cancellation close to total eclipse.
            return (anti(bl,x)-anti(lo,x) if bl>lo else 0.)+(anti(hi,x)-anti(bh,x) if hi>bh else 0.)
        out=quad(slice_integral,-a,a,epsabs=epsabs,epsrel=epsrel,points=breaks[1:-1],limit=limit,full_output=1)
        self.source_calls+=1;self.max_source_abserr=max(self.max_source_abserr,float(out[1]))
        if len(out)>3:self.source_quad_warnings.append(str(out[3]))
        return float(out[0])
    def integrate(self,tight=False,event_edges=()):
        ta,tb=self.c['clock'][self.channel+'_gate_s'];scale=.1 if tight else 1.
        points=sorted(set([ta,tb]+[float(x) for x in np.arange(0,7.301,.25) if ta<x<tb]+[float(x) for x in event_edges if ta<x<tb]))
        out=quad(lambda t:self.source_flux(t,2e-8*scale,2e-7*scale),ta,tb,epsabs=2e-7*scale,epsrel=2e-6*scale,points=points[1:-1],limit=100,full_output=1)
        return {'transfer_integral_s_m2':float(out[0]),'integral_SI':float(out[0])*self.Qtotal,'outer_abserr_estimate_s_m2':float(out[1]),'source_max_abserr_estimate_m2':self.max_source_abserr,'source_evaluations':self.source_calls,'outer_evaluations':int(out[2]['neval']),'outer_subintervals':int(out[2]['last']),'outer_warning':str(out[3]) if len(out)>3 else None,'source_warning_count':len(self.source_quad_warnings),'source_warning_first':self.source_quad_warnings[0] if self.source_quad_warnings else None,'status':'reference_estimated_not_strict_bound'}
