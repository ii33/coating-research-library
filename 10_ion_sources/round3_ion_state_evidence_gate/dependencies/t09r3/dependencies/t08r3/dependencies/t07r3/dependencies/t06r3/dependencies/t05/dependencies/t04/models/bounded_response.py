"""T04-r3 finite encoded-source response; SI; synthetic law, not material calibration.
Geometry/events are the unmodified vendored T03 full-forward contract.
"""
from dataclasses import dataclass, asdict
from fractions import Fraction as F
from pathlib import Path
import hashlib,json,math,sys
import numpy as np
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'dependencies/t03/models'))
from trust_region import Scene, full_forward, exact_scene, exact_visible_intervals, exact_events, source_contract, digest
from event_reference import rate_kernel

def f(x):
    if isinstance(x,F):return x
    if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x):raise ValueError('finite real number required')
    return F(x)
def bounds(x,nonnegative=False,positive=False):
    if x is None:return None
    if not isinstance(x,(list,tuple)) or len(x)!=2:raise ValueError('ordered pair or null required')
    a,b=map(f,x)
    if a>b or (nonnegative and a<0) or (positive and a<=0):raise ValueError('invalid interval domain')
    return a,b

def add(a,b):return a[0]+b[0],a[1]+b[1]
def mul(a,b):
    q=[x*y for x in a for y in b];return min(q),max(q)
def div(a,b):
    if b[0]<=0<=b[1]:raise ValueError('denominator crosses zero')
    return mul(a,(1/b[1],1/b[0]))
def outward(q):
    if q is None:return None
    out=[]
    for v,low in zip(q,(True,False)):
        z=float(v)
        if not math.isfinite(z):raise ValueError('nonfinite output')
        if (low and F(z)>v) or (not low and F(z)<v):z=math.nextafter(z,-math.inf if low else math.inf)
        out.append(z)
    return out

def affine_range(t,pair):
    a,b=pair;z=[f(a)+f(b)*x for x in t];return min(z),max(z)

@dataclass(frozen=True)
class Response:
    dataset_kind: str='synthetic'
    material_id: str='SYNTHETIC_NO_MATERIAL_FIT'
    substrate_id: str='SYNTHETIC_NO_SUBSTRATE_FIT'
    law: str='separable_bounded_retention_v1'
    source_scale_kg_s: tuple=(2e-6,2e-6)
    density_kg_m3: tuple=(2000.,2000.)
    density_basis: str='synthetic_constant_effective_film'
    sticking_s0: tuple=(1.,1.)
    angular_a: tuple=(0.,0.)
    energy_b: tuple=(0.,0.)
    temperature_c: tuple=(0.,0.)
    energy_history_eV: tuple=(20.,10.)
    energy_domain_eV: tuple=(0.,100.)
    temperature_history_K: tuple=(300.,10.)
    temperature_domain_K: tuple=(300.,400.)
    erosion_mass_kg_m2: tuple=(0.,0.)
    initial_inventory_kg_m2: tuple=(1e-4,1e-4)
    model_transfer_status: str='synthetic_only'
    units: str='SI_mass_kernel_actual_substrate_area'

    def validate(self,sc):
        if self.dataset_kind not in ('synthetic','unmeasured_template'):raise ValueError('calibrated material prediction not implemented')
        if self.law!='separable_bounded_retention_v1' or self.units!='SI_mass_kernel_actual_substrate_area':raise ValueError('unsupported law or units')
        if self.density_basis not in ('synthetic_constant_effective_film','unknown_actual_film'):raise ValueError('bulk/QCM density cannot masquerade as effective film density')
        if self.dataset_kind=='unmeasured_template' and self.model_transfer_status!='unknown':raise ValueError('real template not qualified')
        if self.dataset_kind=='synthetic' and self.model_transfer_status!='synthetic_only':raise ValueError('synthetic must not masquerade as validated')
        for k in ('source_scale_kg_s','erosion_mass_kg_m2','initial_inventory_kg_m2'):bounds(getattr(self,k),nonnegative=True)
        bounds(self.density_kg_m3,positive=True)
        for k in ('sticking_s0','angular_a','energy_b','temperature_c'):
            q=bounds(getattr(self,k),nonnegative=True)
            if q and q[1]>1:raise ValueError('retention factor coefficient outside [0,1]')
        for name in ('energy','temperature'):
            dom=bounds(getattr(self,name+'_domain_'+('eV' if name=='energy' else 'K')))
            hist=getattr(self,name+'_history_'+('eV' if name=='energy' else 'K'))
            if dom is None or dom[0]>=dom[1]:raise ValueError('strict history domain required')
            if name=='energy' and dom[0]<0 or name=='temperature' and dom[0]<=0:raise ValueError('physical history domain')
            if hist is not None:
                if len(hist)!=2:raise ValueError('affine history intercept and slope')
                a,b=affine_range((f(sc.t0),f(sc.t1)),hist)
                if a<dom[0] or b>dom[1]:raise ValueError('history outside stated valid domain')
        return self

    def missing(self):
        needed=['source_scale_kg_s','density_kg_m3','sticking_s0','angular_a','energy_b','temperature_c','erosion_mass_kg_m2','initial_inventory_kg_m2']
        for n in ('energy','temperature'):
            c=getattr(self,'energy_b' if n=='energy' else 'temperature_c')
            if c is None or c[1]!=0:needed.append(n+'_history_'+('eV' if n=='energy' else 'K'))
        return [k for k in needed if getattr(self,k) is None]


def factor(coef,x):
    q=mul(bounds(coef),x);return F(1)-q[1],F(1)-q[0]
def response_range(sc,node,ta,tb,r):
    p=exact_scene(sc);s=f(node)+p['source_shift_m'];d=p['x0_m']+p['target_shift_m']+p['velocity_m_s']*p['clock_offset_s']-s
    ya=d+p['velocity_m_s']*ta;yb=d+p['velocity_m_s']*tb;H2=p['height_m']**2
    ys=(F(0) if ya*yb<=0 else min(ya*ya,yb*yb),max(ya*ya,yb*yb))
    u=(ys[0]/(H2+ys[0]),ys[1]/(H2+ys[1]))
    ans=mul(bounds(r.sticking_s0),factor(r.angular_a,u))
    for n,coef,unit in [('energy',r.energy_b,'eV'),('temperature',r.temperature_c,'K')]:
        if coef[1]==0:continue
        dom=bounds(getattr(r,n+'_domain_'+unit));h=affine_range((ta,tb),getattr(r,n+'_history_'+unit))
        x=((h[0]-dom[0])/(dom[1]-dom[0]),(h[1]-dom[0])/(dom[1]-dom[0]))
        ans=mul(ans,factor(coef,x))
    if ans[0]<0 or ans[1]>1:raise ValueError('retention range invalid')
    return ans

def retained_transfer(sc,nodes,weights,r,panels):
    """Exact rational Darboux integral enclosure for this encoded model only."""
    p=exact_scene(sc);total=(F(0),F(0));H2=p['height_m']**2;count=0
    for node,weight in zip(nodes,weights):
        s=f(node)+p['source_shift_m'];d=p['x0_m']+p['target_shift_m']+p['velocity_m_s']*p['clock_offset_s']-s
        for a,b in exact_visible_intervals(sc,node):
            dt=(b-a)/panels
            for j in range(panels):
                ta=a+j*dt;tb=ta+dt;qa=p['q0']+p['q1_per_s']*ta;qb=p['q0']+p['q1_per_s']*tb
                ya=d+p['velocity_m_s']*ta;yb=d+p['velocity_m_s']*tb
                ymin=F(0) if ya*yb<=0 else min(ya*ya,yb*yb);ymax=max(ya*ya,yb*yb)
                k=(p['amplitude']*min(qa,qb)*H2/(H2+ymax)**2,p['amplitude']*max(qa,qb)*H2/(H2+ymin)**2)
                total=add(total,mul((f(weight)*dt,)*2,mul(k,response_range(sc,node,ta,tb,r))));count+=1
    return total,count

def point_response(t,sc,node,r):
    y=sc.x0_m+sc.target_shift_m+sc.velocity_m_s*(np.asarray(t)+sc.clock_offset_s)-(node+sc.source_shift_m)
    ans=r.sticking_s0[0]*(1-r.angular_a[0]*y*y/(sc.height_m**2+y*y))
    for n,c,unit in [('energy',r.energy_b[0],'eV'),('temperature',r.temperature_c[0],'K')]:
        if c==0:continue
        h=getattr(r,n+'_history_'+unit);dom=getattr(r,n+'_domain_'+unit)
        ans=ans*(1-c*(h[0]+h[1]*np.asarray(t)-dom[0])/(dom[1]-dom[0]))
    return ans

def point_estimate_and_gradient(sc,nodes,weights,r):
    keys=['source_scale_kg_s','density_kg_m3','sticking_s0','angular_a','energy_b','temperature_c','erosion_mass_kg_m2']
    if any(getattr(r,k)[0]!=getattr(r,k)[1] for k in keys):return None,None
    tt,ww=np.polynomial.legendre.leggauss(32);sums=[];grad=np.zeros(2)
    for node,w in zip(nodes,weights):
        for a,b in exact_visible_intervals(sc,node):
            a,b=float(a),float(b);t=(a+b)/2+(b-a)*tt/2
            sums.append(w*(b-a)/2*float(np.dot(ww,rate_kernel(t,node,sc)*point_response(t,sc,node,r))))
        events,_=exact_events(sc,node)
        for e in events:
            if f(sc.t0)<e['time']<f(sc.t1):
                jump=(-1 if e['boundary']=='lower' else 1)*(1 if sc.velocity_m_s>0 else -1)
                t=float(e['time']);grad-=w*jump*float(rate_kernel(t,node,sc))*point_response(t,sc,node,r)*np.array([float(x) for x in e['grad']])
    Q=r.source_scale_kg_s[0];rho=r.density_kg_m3[0]
    return (Q*math.fsum(sums)-r.erosion_mass_kg_m2[0])/rho,(Q/rho*grad).tolist()

def objective(q,target,floor=1e-15):
    t=f(target);z=f(floor)
    if z<=0 or t<=z:raise ValueError('near_zero_target_denominator')
    if q is None:return None
    a=(q[0]-t)/t;b=(q[1]-t)/t
    return (F(0) if a<=0<=b else min(a*a,b*b)/2,max(a*a,b*b)/2)

def normalize_positive(numerator,net,floor):
    a=bounds(numerator,nonnegative=True);b=bounds(net);z=f(floor)
    if z<=0:raise ValueError('positive declared denominator floor')
    if a is None or b is None:return {'status':'unknown','value':None}
    if b[1]<0:return {'status':'negative_net','value':None}
    if b[0]<=0:return {'status':'zero_or_crossing','value':None}
    if b[0]<=z or b[1]-b[0]>=b[0]:return {'status':'ill_conditioned','value':None,'diagnostic_interval':outward(div(a,b))}
    return {'status':'conditional','value':outward(div(a,b))}

def code_hashes():
    return {str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('models','dependencies/t03/models') for p in sorted((R/folder).rglob('*.py'))}

def forward(sc,r,nodes=(0.,),weights=(1.,),target_m=1e-9,panels=64):
    sc.validate();nodes,weights=source_contract(nodes,weights);r.validate(sc);objective(None,target_m)
    if type(panels) is not int or not 1<=panels<=4096:raise ValueError('panels outside 1..4096')
    upstream=full_forward(sc,nodes,weights,target=1.,panels=panels)
    fixed=asdict(sc);design={k:fixed.pop(k) for k in ('plate_shift_m','half_width_m')}
    contract={'scene_fixed':fixed,'nodes':nodes,'weights':weights,'response':asdict(r),'target_m':target_m,'panels':panels,'code_sha256':code_hashes()}
    out={'upstream_full_forward':upstream,'response_contract_sha256':digest(contract),'response_definition':asdict(r),'design':design,'status':'unknown','retained_transfer_s_m2':None,'net_mass_kg_m2':None,'signed_thickness_change_m':None,'objective_interval':None,'height_estimate_m':None,'material_design_gradient_m_per_m':None,'physical_certification':False,'continuous_source_certification':False,'material_calibration':'not_performed','point12':'partial_unchanged','point2':'conditional_non_strict_unchanged'}
    if upstream['objective_status']!='bounded_encoded_discrete_source' or not upstream['input_uncertainty_qualified']:
        out['reason']='upstream_geometry_events_or_uncertainty_unqualified';return out
    missing=r.missing()
    if missing:out.update(reason='missing_response_inputs',missing=missing);return out
    if r.dataset_kind!='synthetic':out['reason']='real_material_transfer_not_qualified';return out
    inv=bounds(r.initial_inventory_kg_m2);erosion=bounds(r.erosion_mass_kg_m2)
    if inv[0]<erosion[1]:out.update(status='inventory_unresolved',reason='conservative_no_depletion_check_failed');return out
    D,count=retained_transfer(sc,nodes,weights,r,panels);mass=add(mul(bounds(r.source_scale_kg_s),D),(-erosion[1],-erosion[0]));h=div(mass,bounds(r.density_kg_m3))
    he,grad=point_estimate_and_gradient(sc,nodes,weights,r)
    if he is not None and not float(h[0])-1e-23<=he<=float(h[1])+1e-23:raise ValueError('point_estimate_outside_bounds')
    out.update(retained_transfer_s_m2=outward(D),net_mass_kg_m2=outward(mass),signed_thickness_change_m=outward(h),height_estimate_m=he,material_design_gradient_m_per_m=grad,panel_count=count,bound_scope='exact_encoded_synthetic_Darboux_not_material_or_continuum_certificate',gradient_scope='two_plate_parameters_only; smooth_term_zero; weighted_event_term_retained')
    if mass[1]<0:out.update(status='negative_net',reason='signed_change_recorded_not_growth_reward');return out
    if mass[0]<=0:out.update(status='zero_or_crossing_net',reason='not_positive_growth');return out
    if h[0]<=f(1e-15) or h[1]-h[0]>=h[0]:out.update(status='ill_conditioned_net',reason='growth_denominator_not_stable');return out
    out.update(status='bounded_synthetic_response',objective_interval=outward(objective(h,target_m)))
    return out

def compare(a,b):
    if a['response_contract_sha256']!=b['response_contract_sha256']:raise ValueError('incompatible_material_objective_or_frozen_contract')
    if a['status']!='bounded_synthetic_response' or b['status']!='bounded_synthetic_response':return {'relation':'unresolved','reason':'unknown_or_invalid_growth'}
    A=a['objective_interval'];B=b['objective_interval']
    if A[1]<B[0]:return {'relation':'a_better','reason':'disjoint_encoded_synthetic_objective_bounds'}
    if B[1]<A[0]:return {'relation':'b_better','reason':'disjoint_encoded_synthetic_objective_bounds'}
    return {'relation':'unresolved','reason':'overlap_or_equal_bounds'}
