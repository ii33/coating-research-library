#!/usr/bin/env python3
"""Fixed-domain, fixed-score local/global coating-search comparison.

Research only; independent of the product. exp(-i wt), tangential E,H.
Complex nk is either explicitly synthetic or interpolated from supplied data.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,platform,time
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import least_squares,differential_evolution
from scipy.stats import qmc

ROOT=Path(__file__).resolve().parent
LOWER,UPPER=0.005,2.5
WINDOWS=((3.,5.),(8.,12.))
TARGET_R=.01
METHODS=('classic_local','random_local','classic_de','de_local','local_de_local','probe_local')
SEEDS=(11,29,47,71,101)


def nk_values(material,wl):
    if material=='air': return np.ones_like(wl,dtype=complex)
    if material.startswith('synthetic_'):
        return np.full_like(wl,float(material.split('_')[-1]),dtype=complex)
    rows=np.loadtxt(ROOT/'data'/f'{material}.csv',delimiter=',',skiprows=1)
    if wl.min()<rows[0,0] or wl.max()>rows[-1,0]: raise ValueError('nk coverage missing; no extrapolation or zero filling')
    if np.any(rows[:,2]<0):raise ValueError('active or invalid material')
    return np.interp(wl,rows[:,0],rows[:,1])+1j*np.interp(wl,rows[:,0],rows[:,2])


def scenarios(angles):
    out=[]
    for a in angles:
        pols=('s',) if a==0 else ('s','p')
        for p in pols:out.append((float(a),p,1/len(angles)/len(pols)))
    return out


class OpticalModel:
    """Precompute angle-dependent longitudinal wavevector and admittance."""
    def __init__(self,wl,materials,substrate,angles):
        self.wl=np.asarray(wl,float);self.scenarios=scenarios(angles)
        self.materials=materials;self.substrate=substrate
        n=np.array([nk_values(m,self.wl) for m in ['air',*materials,substrate]])
        eta=[];qzs=[]
        for a,p,_ in self.scenarios:
            qz=np.sqrt(n*n-np.sin(np.deg2rad(a))**2+0j)
            qz=np.where((qz.imag<0)|((abs(qz.imag)<1e-14)&(qz.real<0)),-qz,qz)
            qzs.append(qz)
            eta.append(qz if p=='s' else n*n/qz)
        self.eta=np.array(eta);self.qz=np.array(qzs)
        self.phase_rate=2*np.pi*self.qz[:,1:-1,:]/self.wl
        self.rif=(self.eta[:,:-1]-self.eta[:,1:])/(self.eta[:,:-1]+self.eta[:,1:])
        self.tif=2*self.eta[:,:-1]/(self.eta[:,:-1]+self.eta[:,1:])
    def solve(self,ds):
        """Stable reflection/transmission recursion; forward exponential decays."""
        if len(ds)!=len(self.materials) or np.any(np.asarray(ds)<0):raise ValueError('invalid stack')
        r=self.rif[:,-1].copy();t=self.tif[:,-1].copy()
        for j in range(len(ds)-1,-1,-1):
            p=np.exp(1j*self.phase_rate[:,j]*ds[j]);rj=self.rif[:,j]
            den=1+rj*r*p*p
            t=self.tif[:,j]*t*p/den
            r=(rj+r*p*p)/den
        R=abs(r)**2
        P=self.eta[:,-1].real/self.eta[:,0].real*abs(t)**2
        if not np.isfinite(R).all() or not np.isfinite(P).all():raise FloatingPointError('nonfinite optics')
        return R,P
    def matrix(self,ds):
        """Independent E,H characteristic matrix, only for bounded optical QA."""
        sh=(len(self.scenarios),len(self.wl));a=np.ones(sh,complex);b=np.zeros(sh,complex);c=b.copy();d=a.copy()
        for j,dj in enumerate(ds):
            phase=self.phase_rate[:,j]*dj;co=np.cos(phase);si=np.sin(phase);e=self.eta[:,j+1]
            m01=-1j*si/e;m10=-1j*si*e
            a,b,c,d=a*co+b*m10,a*m01+b*co,c*co+d*m10,c*m01+d*co
        e0=self.eta[:,0];es=self.eta[:,-1];den=e0*(a+b*es)+c+d*es
        r=(e0*(a+b*es)-c-d*es)/den;t=2*e0/den
        return abs(r)**2,es.real/e0.real*abs(t)**2


def case_def(name):
    if name=='synthetic6_normal':return {'name':name,'layers':6,'angles':[0.],'real_nk':False,'min_entering_flux':None}
    if name=='synthetic6_multi':return {'name':name,'layers':6,'angles':[0.,30.,45.],'real_nk':False,'min_entering_flux':None}
    if name=='synthetic10_multi':return {'name':name,'layers':10,'angles':[0.,30.,45.],'real_nk':False,'min_entering_flux':None}
    if name=='tabulated6_multi':return {'name':name,'layers':6,'angles':[0.,30.,45.],'real_nk':True,'min_entering_flux':.90}
    raise ValueError(name)


def materials(case):
    pair=['MgF2_Franta','ZnSe_Querry'] if case['real_nk'] else ['synthetic_1.45','synthetic_2.35']
    return pair*(case['layers']//2),'Si_Franta-300K' if case['real_nk'] else 'synthetic_3.42'


def templates(case):
    mats,_=materials(case);cs=[math.sqrt(a*b) for a,b in WINDOWS];cm=math.sqrt(cs[0]*cs[-1]);N=case['layers']
    ns=np.array([nk_values(m,np.array([cm])).real[0] for m in mats]);out=[]
    for label,center in [('pair_short_qw',cs[0]),('pair_long_qw',cs[-1]),('pair_geomean_qw',cm)]:
        ds=np.full(N,LOWER);ds[:2]=center/(4*ns[:2]);out.append((label,np.clip(ds,LOWER,UPPER)))
    out.append(('alternating_qw',np.clip(cm/(4*ns),LOWER,UPPER)))
    out.append(('chirped_qw',np.clip(np.geomspace(cs[0],cs[-1],N)/(4*ns),LOWER,UPPER)))
    ds=np.full(N,LOWER);ds[:2]=cm/(4*ns[:2]);ds[2:4]=cm/(2*ns[2:4]);out.append(('pair_halfwave',np.clip(ds,LOWER,UPPER)))
    return out


class BudgetEnd(Exception):pass
class Objective:
    def __init__(self,case,budget,points=81):
        self.case=case;self.points=points;self.budget=int(budget);self.calls=0;self.limit=budget
        wl=np.concatenate([np.linspace(a,b,points) for a,b in WINDOWS]);mats,sub=materials(case)
        self.model=OpticalModel(wl,mats,sub,case['angles'])
        self.sqrtw=np.sqrt(np.array([s[2] for s in self.model.scenarios])[:,None]/len(wl))
        self.best_loss=math.inf;self.best_x=None;self.best_violation=math.inf;self.best_max_x=None;self.best_max_loss=math.inf
        self.records=[];self.stage='unset';self.stage_counts={}
    def residual(self,x):
        if self.calls>=min(self.budget,self.limit):raise BudgetEnd
        self.calls+=1;self.stage_counts[self.stage]=self.stage_counts.get(self.stage,0)+1
        R,P=self.model.solve(x);v=np.maximum(R/TARGET_R-1,0);viol=float(v.max())
        rs=[(v*v*self.sqrtw).ravel(),(.01*R/TARGET_R*self.sqrtw).ravel()]
        if self.case['min_entering_flux'] is not None:
            vp=np.maximum((self.case['min_entering_flux']-P)/.1,0);viol=max(viol,float(vp.max()));rs.append((vp*vp*self.sqrtw).ravel())
        r=np.concatenate(rs);loss=float(r@r)
        if loss<self.best_loss:self.best_loss=loss;self.best_x=np.array(x,copy=True)
        if (viol,loss)<(self.best_violation,self.best_max_loss):
            self.best_violation=viol;self.best_max_loss=loss;self.best_max_x=np.array(x,copy=True)
            self.records.append({'calls':self.calls,'loss':loss,'max_standardized_violation':viol,'max_R':float(R.max()),'stage':self.stage})
        return r
    def scalar(self,x):
        r=self.residual(x);return float(r@r)


def local(obj,x,quota,stage):
    start=obj.calls;obj.limit=min(obj.budget,start+int(quota));obj.stage=stage
    localbest=[math.inf,np.array(x,copy=True)]
    def res(z):
        r=obj.residual(z);v=float(r@r)
        if v<localbest[0]:localbest[:]=[v,np.array(z,copy=True)]
        return r
    try:
        least_squares(res,np.clip(x,LOWER,UPPER),bounds=(LOWER,UPPER),jac='2-point',x_scale='jac',max_nfev=max(2,int(quota)),ftol=1e-10,xtol=1e-10,gtol=1e-10)
    except BudgetEnd:pass
    obj.limit=obj.budget
    return localbest[1],obj.calls-start


def get_pop(case,seed,classic=True):
    N=case['layers'];size=max(48,6*N);pop=qmc.LatinHypercube(d=N,seed=seed).random(size)*(UPPER-LOWER)+LOWER
    if classic:
        for j,(_,x) in enumerate(templates(case)):pop[j]=x
    return pop


def de(obj,pop,seed,quota,stage):
    obj.stage=stage;obj.limit=min(obj.budget,obj.calls+int(quota));before=obj.calls
    try:
        differential_evolution(obj.scalar,[(LOWER,UPPER)]*obj.case['layers'],init=pop,rng=np.random.default_rng(seed),strategy='best1bin',maxiter=int(quota)//len(pop)+2,tol=0,atol=0,mutation=(.5,1),recombination=.7,polish=False,workers=1,updating='immediate')
    except BudgetEnd:pass
    obj.limit=obj.budget
    return obj.calls-before


def run(case,method,seed,budget,points=81):
    obj=Objective(case,budget,points);rng=np.random.default_rng(seed);temps=templates(case);pop=get_pop(case,seed)
    t=time.perf_counter();starts=[]
    if method in ('classic_local','random_local'):
        chunk=max(80,budget//6);k=0
        while obj.calls<budget:
            if method=='classic_local' and k<len(temps):
                x=temps[k][1].copy()
                if k:x=np.clip(x*rng.uniform(.9,1.1,len(x)),LOWER,UPPER)
                label=temps[k][0]
            else:x=rng.uniform(LOWER,UPPER,case['layers']);label='uniform_restart'
            _,used=local(obj,x,min(chunk,budget-obj.calls),'local_restarts');starts.append({'label':label,'calls':used});k+=1
    elif method=='classic_de':de(obj,pop,seed,budget,'de')
    elif method=='de_local':
        de(obj,pop,seed,int(.8*budget),'de')
        while obj.calls<budget:
            x=obj.best_x.copy();_,used=local(obj,x,budget-obj.calls,'final_local')
            if used==0:break
    elif method in ('local_de_local','probe_local'):
        # Six deliberately short basin probes, followed by globally dispersed DE.
        pre=int(.3*budget);quota=pre//len(temps)
        for j,(label,x) in enumerate(temps):
            if j:x=np.clip(x*rng.uniform(.9,1.1,len(x)),LOWER,UPPER)
            x,used=local(obj,x,quota,'template_probe');pop[j]=x;starts.append({'label':label,'calls':used})
        if method=='local_de_local':de(obj,pop,seed,int(.5*budget),'de')
        while obj.calls<budget:
            _,used=local(obj,obj.best_x.copy(),budget-obj.calls,'final_local')
            if used==0:break
    else:raise ValueError(method)
    elapsed=time.perf_counter()-t
    x=obj.best_max_x
    result={'case':case,'method':method,'seed':seed,'budget':budget,'actual_objective_calls':obj.calls,'train_points_per_window':points,'train_optical_points_per_call':len(obj.model.wl)*len(obj.model.scenarios),'actual_optical_point_solves':obj.calls*len(obj.model.wl)*len(obj.model.scenarios),'wall_seconds_optimization_only':elapsed,'stage_counts':obj.stage_counts,'starts':starts,'thickness_um':x.tolist(),'total_thickness_um':float(sum(x)),'selected_by':'training max standardized violation then fixed aggregate loss; dense audit does not select candidate','training_max_standardized_violation':obj.best_violation,'training_loss_of_selected':obj.best_max_loss,'best_aggregate_loss':obj.best_loss,'best_aggregate_thickness_um':obj.best_x.tolist(),'trace':obj.records}
    return result


def audit(result,points=4097,angle_step=5):
    case=result['case'];mats,sub=materials(case);angles=[0.] if len(case['angles'])==1 else np.arange(0,45+.1,angle_step).tolist();x=result['thickness_um'];rows=[];maxdiff=0.;maxenergy=0.;minabs=math.inf
    count=0;t=time.perf_counter()
    for lo,hi in WINDOWS:
        # Midpoint-shifted audit; with 4097 midpoint samples it shares the
        # window center with 81-point training, plus common endpoints. Not a disjoint holdout.
        wl=np.r_[lo,lo+(np.arange(points)+.5)*(hi-lo)/points,hi]
        model=OpticalModel(wl,mats,sub,angles);R,P=model.solve(x);Rm,Pm=model.matrix(x)
        maxdiff=max(maxdiff,float(abs(R-Rm).max()),float(abs(P-Pm).max()));A=1-R-P;minabs=min(minabs,float(A.min()))
        if not case['real_nk']:maxenergy=max(maxenergy,float(abs(A).max()))
        for j,(a,p,w) in enumerate(model.scenarios):
            idx=int(R[j].argmax());vR=max(0.,float(R[j].max()/TARGET_R-1));vP=0. if case['min_entering_flux'] is None else max(0.,float((case['min_entering_flux']-P[j].min())/.1))
            rows.append({'window_um':[lo,hi],'angle_deg':a,'polarization':p,'max_R':float(R[j].max()),'argmax_R_um':float(wl[idx]),'mean_R':float(R[j].mean()),'min_power_entering_substrate':float(P[j].min()),'max_coating_absorptance':float(A[j].max()),'max_standardized_violation':max(vR,vP),'pass':vR<=1e-12 and vP<=1e-12})
        count+=len(wl)*len(model.scenarios)*2
    trained=[q for q in rows if q['angle_deg'] in case['angles']]
    return {'rows':rows,'trained_angles_dense_worst_R':max(q['max_R'] for q in trained),'angle_envelope_dense_worst_R':max(q['max_R'] for q in rows),'trained_angles_dense_pass':all(q['pass'] for q in trained),'angle_envelope_dense_pass':all(q['pass'] for q in rows),'max_standardized_violation':max(q['max_standardized_violation'] for q in rows),'min_entering_flux':min(q['min_power_entering_substrate'] for q in rows),'independent_matrix_max_abs_error':maxdiff,'lossless_energy_max_abs_error':maxenergy if not case['real_nk'] else None,'min_coating_absorptance':minabs,'audit_point_solves_both_kernels':count,'audit_seconds':time.perf_counter()-t,'scope':'finite midpoint wavelength grid and 5-degree angle grid, not continuous certification; P is flux into semi-infinite substrate, not full-device transmittance'}


def physics_checks():
    rng=np.random.default_rng(20261020);err=energy=0.;minA=1.
    for real in (False,True):
        c=case_def('tabulated6_multi' if real else 'synthetic6_multi');mats,sub=materials(c);model=OpticalModel(np.linspace(3,12,153),mats,sub,c['angles'])
        for k in range(35):
            x=rng.uniform(LOWER,UPPER,6);R,P=model.solve(x);Rm,Pm=model.matrix(x);err=max(err,float(abs(R-Rm).max()),float(abs(P-Pm).max()));A=1-R-P;minA=min(minA,float(A.min()))
            if not real:energy=max(energy,float(abs(A).max()))
    wl=np.linspace(3,12,31);bare=OpticalModel(wl,[],'synthetic_3.42',[0.,30.,45.]);R,P=bare.solve([]);Rm,Pm=bare.matrix([]);bareerr=float(max(abs(R-Rm).max(),abs(P-Pm).max()))
    # Brewster zero, quarter-wave matching, zero-thickness reduction and full opacity.
    brew=OpticalModel(np.array([4.]),[],'synthetic_1.5',[np.rad2deg(np.arctan(1.5))]);br=float(brew.solve([])[0][1,0])
    n=math.sqrt(3.42);qw=OpticalModel(np.array([4.]),[f'synthetic_{n}'],'synthetic_3.42',[0.]);qr=float(qw.solve([4/(4*n)])[0][0,0])
    m=OpticalModel(wl,['synthetic_1.45','synthetic_2.35']*3,'synthetic_3.42',[0.,30.,45.]);zR,zP=m.solve(np.zeros(6));zero=float(max(abs(zR-R).max(),abs(zP-P).max()))
    # Lossy layer with hundreds of decay lengths: exponential recursion stays finite.
    opaque=OpticalModel(np.array([4.]),['synthetic_1.45'],'synthetic_3.42',[0.]);opaque.phase_rate[:]=2*np.pi*(2+2j)/4;opaque.eta[:,1]=2+2j;opaque.rif=(opaque.eta[:,:-1]-opaque.eta[:,1:])/(opaque.eta[:,:-1]+opaque.eta[:,1:]);opaque.tif=2*opaque.eta[:,:-1]/(opaque.eta[:,:-1]+opaque.eta[:,1:]);oR,oP=opaque.solve([1e3])
    result={'random_stacks':70,'recursion_vs_matrix_max_abs_error':err,'lossless_max_abs_R_plus_P_minus_1':energy,'minimum_passive_coating_absorptance':minA,'bare_matrix_recursion_max_error':bareerr,'brewster_p_R':br,'quarterwave_AR_R':qr,'zero_thickness_error':zero,'opaque_recursion_finite':bool(np.isfinite(oR).all() and np.isfinite(oP).all()),'opaque_R':float(oR[0,0]),'opaque_P':float(oP[0,0])}
    assert err<1e-11 and energy<1e-11 and minA>-1e-11 and br<1e-24 and qr<1e-24 and zero<1e-12 and result['opaque_recursion_finite']
    return result


def summarize(results):
    out=[]
    for case in sorted({x['case']['name'] for x in results}):
        for method in METHODS:
            xs=[r for r in results if r['case']['name']==case and r['method']==method]
            if not xs:continue
            out.append({'case':case,'method':method,'n':len(xs),'median_worst_R_percent':100*float(np.median([r['audit']['angle_envelope_dense_worst_R'] for r in xs])),'best_worst_R_percent':100*min(r['audit']['angle_envelope_dense_worst_R'] for r in xs),'worst_worst_R_percent':100*max(r['audit']['angle_envelope_dense_worst_R'] for r in xs),'pass_count':sum(r['audit']['angle_envelope_dense_pass'] for r in xs),'median_calls':float(np.median([r['actual_objective_calls'] for r in xs])),'median_wall_seconds':float(np.median([r['wall_seconds_optimization_only'] for r in xs])),'median_min_entering_flux':float(np.median([r['audit']['min_entering_flux'] for r in xs]))})
    return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--budget',type=int,default=6000);ap.add_argument('--seeds',nargs='+',type=int,default=SEEDS);ap.add_argument('--cases',nargs='+',default=['synthetic6_normal','synthetic6_multi','synthetic10_multi','tabulated6_multi']);ap.add_argument('--methods',nargs='+',default=METHODS);ap.add_argument('--output',default='results');ap.add_argument('--points',type=int,default=81);ap.add_argument('--audit-points',type=int,default=4097);ap.add_argument('--physics-only',action='store_true');args=ap.parse_args()
    out=ROOT/args.output;out.mkdir(parents=True,exist_ok=True);checks=physics_checks();(out/'physics_checks.json').write_text(json.dumps(checks,indent=2));print('physics',checks,flush=True)
    if args.physics_only:return
    results=[]
    for name in args.cases:
        case=case_def(name)
        for seed in args.seeds:
            methods=list(args.methods);np.random.default_rng(seed).shuffle(methods)
            for method in methods:
                r=run(case,method,seed,args.budget,args.points);r['audit']=audit(r,args.audit_points);results.append(r)
                (out/'results.json').write_text(json.dumps({'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},'args':vars(args),'results':results},indent=2))
                print(name,method,seed,r['actual_objective_calls'],round(r['wall_seconds_optimization_only'],3),'worstR%',round(100*r['audit']['angle_envelope_dense_worst_R'],6),'pass',r['audit']['angle_envelope_dense_pass'],flush=True)
    summary=summarize(results);(out/'summary.json').write_text(json.dumps(summary,indent=2));
    with (out/'summary.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
    print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':main()
