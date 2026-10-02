"""T08 small reproducible optimization reference. Units um; no production claim.
Frozen T07 S kernel plus explicit analytical forward tangent propagation.
No automatic-differentiation framework, remote model, or paid solver required.
"""
from pathlib import Path
import json, hashlib, time
from dataclasses import dataclass
import numpy as np
from scipy.optimize import least_squares, minimize
from vendor import t07_optics_kernel as optics
ROOT=Path(__file__).resolve().parents[1]


def material(model,w):
    w=np.asarray(w,float)
    lo,hi=model['calculation_bounds_um']
    if np.any((w<lo-1e-12)|(w>hi+1e-12)): raise ValueError('material extrapolation prohibited')
    if model['model']=='constant':return np.full_like(w,model['n'],complex)+1j*model['k']
    if model['model']=='linear_table':
        tab=np.array(model['table_wavelength_n_k']);return np.interp(w,tab[:,0],tab[:,1])+1j*np.interp(w,tab[:,0],tab[:,2])
    raise ValueError('unsupported material model')


def star_tangent(a,b,da,db):
    """d(a star b) using product/quotient rules. Tangent axis (P,M,2,2)."""
    den=1-a[:,1,1]*b[:,0,0]
    dd=-da[:,:,1,1]*b[None,:,0,0]-a[None,:,1,1]*db[:,:,0,0]
    def term(terms,dterms):
        v=np.prod(terms,axis=0)
        dv=sum(dterms[k]*np.prod([terms[i] for i in range(len(terms)) if i!=k],axis=0)
               for k in range(len(terms)))
        return dv/den[None,:]-v[None,:]*dd/den[None,:]**2
    out=np.empty_like(da)
    out[:,:,0,0]=da[:,:,0,0]+term([a[:,0,1],b[:,0,0],a[:,1,0]],[da[:,:,0,1],db[:,:,0,0],da[:,:,1,0]])
    out[:,:,0,1]=term([a[:,0,1],b[:,0,1]],[da[:,:,0,1],db[:,:,0,1]])
    out[:,:,1,0]=term([b[:,1,0],a[:,1,0]],[db[:,:,1,0],da[:,:,1,0]])
    out[:,:,1,1]=db[:,:,1,1]+term([b[:,1,0],a[:,1,1],b[:,0,1]],[db[:,:,1,0],da[:,:,1,1],db[:,:,0,1]])
    return optics.star(a,b),out


def spectrum_jacobian_forward(w,indices,d,angle=0,pol='s'):
    """R/T/A and thickness Jacobians (M,P), holding complex N(lambda) fixed.
    Complexity O(M L^2), tangent memory O(M L). Not adjoint optimized.
    """
    w,n,d,beta,kz,q=optics.prepare(w,indices,d,angle,pol)
    S=optics.identity_s(len(w)); D=np.zeros((len(d),len(w),2,2),complex)
    zero=np.zeros_like(D)
    for j in range(len(n)-1):
        S,D=star_tangent(S,optics.interface(q[j],q[j+1]),D,zero)
        if j<len(d):
            k=2*np.pi*kz[j+1]/w; P=optics.propagation(k*d[j]); dp=np.zeros_like(D)
            dp[j,:,0,1]=dp[j,:,1,0]=1j*k*P[:,0,1]
            S,D=star_tangent(S,P,D,dp)
    r=S[:,0,0];t=S[:,1,0]; dr=D[:,:,0,0].T;dt=D[:,:,1,0].T
    f=q[-1].real/q[0].real
    R=abs(r)**2;T=f*abs(t)**2;A=1-R-T
    JR=2*np.real(np.conj(r)[:,None]*dr);JT=2*f[:,None]*np.real(np.conj(t)[:,None]*dt)
    if np.any(A < -1e-9):raise FloatingPointError('passivity violation')
    return dict(R=R,T=T,A=A,r=r,t=t,JR=JR,JT=JT,JA=-JR-JT,dr=dr,dt=dt)


def spectrum_jacobian(w,indices,d,angle=0,pol='s'):
    """O(M L) exact amplitude derivatives via stable S prefixes/suffixes.
    Store O(M L) arrays. Each layer's local tangent is only a single direction.
    Holding indices and angle fixed; not a derivative of n/k/temperature.
    """
    w,n,d,beta,kz,q=optics.prepare(w,indices,d,angle,pol)
    seg=[]
    for j in range(len(n)-1):
        seg.append(optics.interface(q[j],q[j+1]))
        if j<len(d):seg.append(optics.propagation(2*np.pi*kz[j+1]*d[j]/w))
    pre=[optics.identity_s(len(w))]
    for ss in seg:pre.append(optics.star(pre[-1],ss))
    suf=[None]*(len(seg)+1);suf[-1]=optics.identity_s(len(w))
    for j in range(len(seg)-1,-1,-1):suf[j]=optics.star(seg[j],suf[j+1])
    dr=np.empty((len(w),len(d)),complex);dt=np.empty_like(dr)
    zero=np.zeros((1,len(w),2,2),complex)
    for j in range(len(d)):
        cut=2*j+1;dp=zero.copy();k=2*np.pi*kz[j+1]/w
        dp[0,:,0,1]=dp[0,:,1,0]=1j*k*seg[cut][:,0,1]
        mid,dm=star_tangent(pre[cut],seg[cut],zero,dp)
        _,df=star_tangent(mid,suf[cut+1],dm,zero)
        dr[:,j]=df[0,:,0,0];dt[:,j]=df[0,:,1,0]
    S=pre[-1];r=S[:,0,0];t=S[:,1,0];f=q[-1].real/q[0].real
    R=abs(r)**2;T=f*abs(t)**2;A=1-R-T
    JR=2*np.real(np.conj(r)[:,None]*dr);JT=2*f[:,None]*np.real(np.conj(t)[:,None]*dt)
    if np.any(A < -1e-9):raise FloatingPointError('passivity violation')
    return dict(R=R,T=T,A=A,r=r,t=t,JR=JR,JT=JT,JA=-JR-JT,dr=dr,dt=dt)


def trapezoid_weights(w):
    w=np.asarray(w,float)
    if len(w)==1:return np.ones(1)
    if np.any(np.diff(w)<=0):raise ValueError('grid must be strictly increasing')
    v=np.r_[w[1]-w[0],w[2:]-w[:-2],w[-1]-w[-2]]/2
    return v/v.sum()


@dataclass(frozen=True)
class Band:
    name:str
    lo:float
    hi:float
    observable:str
    target:float
    scale:float
    weight:float=1.
    sense:str='equality' # equality is target fitting; upper/lower are squared hinge


def load_examples():
    seeds=json.loads((ROOT/'data/t06_starter_stacks_frozen.json').read_text())['examples']
    return {x['id']:x for x in seeds},json.loads((ROOT/'data/material_proxies_frozen.json').read_text())['materials']


class Problem:
    """Scenario-averaged weighted least squares with immutable context cache.
    Cache is scoped to this instance; don't mutate any context after construction.
    """
    def __init__(self,seed,bands,points,angles,polarizations=('s','p'),factors=None,scale_d=None):
        self.seed=json.loads(json.dumps(seed));self.bands=tuple(bands);self.points=points
        self.angles=tuple(angles);self.polarizations=tuple(polarizations)
        self.d0=np.array([l['thickness_um'] for l in seed['layers']]);self.scale_d=self.d0.copy() if scale_d is None else np.array(scale_d)
        self.factors=np.ones((1,len(self.d0))) if factors is None else np.array(factors,float,copy=True)
        if not len(self.d0) or np.any(self.scale_d<=0) or not len(bands) or points<1 or not len(angles) or not len(polarizations):raise ValueError('nonempty positive design and sampling required')
        self.factors.setflags(write=False)
        if self.factors.ndim!=2 or self.factors.shape[1]!=len(self.d0) or np.any(self.factors<=0):raise ValueError('positive multiplicative scenarios required')
        self.materials=load_examples()[1];self.context=[]
        self.forward_calls=0;self.jacobian_calls=0;self.point_layer_work=0;self.cache_hits=0
        self._cache={};self._history=[]
        for band in self.bands:
            w=np.linspace(band.lo,band.hi,points)
            indices=[np.ones_like(w)]+[material(self.materials[x['material']],w) for x in seed['layers']]+[material(self.materials[seed['substrate']],w)]
            wt=np.sqrt(trapezoid_weights(w)*band.weight/(len(angles)*len(polarizations)*len(self.factors))) / band.scale
            for angle in angles:
                for pol in polarizations:self.context.append((band,w,indices,angle,pol,wt))
        payload=dict(seed=self.seed,scale_d=self.scale_d.tolist(),kernel_hash=hashlib.sha256((ROOT/'models/vendor/t07_optics_kernel.py').read_bytes()).hexdigest(),bands=[vars(b) for b in bands],points=points,angles=angles,pols=polarizations,factors=self.factors.tolist(),material_hash=hashlib.sha256((ROOT/'data/material_proxies_frozen.json').read_bytes()).hexdigest())
        self.fingerprint=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
    def evaluate(self,x,jac=False):
        x=np.asarray(x,float);key=(x.tobytes(),bool(jac))
        if key in self._cache:self.cache_hits+=1;return self._cache[key]
        # Derivative entry also supplies residual, without recomputing physics.
        if not jac and (x.tobytes(),True) in self._cache:
            self.cache_hits+=1;return self._cache[(x.tobytes(),True)][0]
        d=x*self.scale_d;rs=[];js=[]
        for factor in self.factors:
            for band,w,indices,angle,pol,wt in self.context:
                z=spectrum_jacobian(w,indices,d*factor,angle,pol) if jac else optics.scattering(w,indices,d*factor,angle,pol)
                self.forward_calls+=1;self.jacobian_calls+=int(jac);self.point_layer_work+=len(w)*len(d)
                v=z[band.observable]-band.target
                active=np.ones(len(w))
                if band.sense=='upper':active=(v>0).astype(float);v=np.maximum(v,0)
                elif band.sense=='lower':active=(v<0).astype(float);v=np.minimum(v,0)
                elif band.sense!='equality':raise ValueError('unknown band sense')
                rs.append(wt*v)
                if jac:js.append(wt[:,None]*active[:,None]*z['J'+band.observable]*(factor*self.scale_d)[None,:])
        r=np.concatenate(rs);out=(r,np.concatenate(js)) if jac else r
        # one-iterate cache avoids unbounded history and approximate-key aliasing
        if len(self._cache)>6:self._cache.clear()
        self._cache[key]=out;self._history.append(dict(x=x.tolist(),cost=float(.5*r@r),with_jac=bool(jac)))
        return out
    def fun(self,x):return self.evaluate(x,True)[0]
    def jac(self,x):return self.evaluate(x,True)[1]
    def forward_fun(self,x):return self.evaluate(x,False)
    def budget(self):return dict(spectrum_calls=self.forward_calls,jacobian_spectrum_calls=self.jacobian_calls,point_layer_work=self.point_layer_work,cache_hits=self.cache_hits)


def solve(problem,x0=None,bounds=(.4,1.6),mode='analytic',max_nfev=60):
    x0=np.ones_like(problem.d0) if x0 is None else np.array(x0,float)
    t=time.perf_counter()
    if mode in ('analytic','finite_difference'):
        r=least_squares(problem.fun if mode=='analytic' else problem.forward_fun,x0,
                        jac=problem.jac if mode=='analytic' else '3-point',bounds=bounds,
                        method='trf',x_scale=1.,ftol=1e-10,gtol=1e-10,xtol=1e-10,max_nfev=max_nfev)
        cost=float(r.cost);nfev=int(r.nfev);optimality=float(r.optimality)
    elif mode=='lbfgsb':
        def fg(x):
            v,j=problem.evaluate(x,True);return .5*v@v,j.T@v
        low=np.broadcast_to(bounds[0],x0.shape);high=np.broadcast_to(bounds[1],x0.shape)
        r=minimize(fg,x0,jac=True,bounds=list(zip(low,high)),method='L-BFGS-B',options=dict(maxiter=max_nfev,maxfun=3*max_nfev,ftol=1e-12,gtol=1e-9,maxls=20))
        cost=float(r.fun);nfev=int(r.nfev);optimality=float(np.max(abs(r.jac)))
    else:raise ValueError(mode)
    elapsed=time.perf_counter()-t
    return dict(x=r.x.tolist(),thickness_um=(r.x*problem.scale_d).tolist(),cost=cost,seconds=elapsed,
                nfev_solver=nfev,status=int(r.status),success=bool(r.success),message=str(r.message),optimality=optimality,
                mode=mode,context_fingerprint=problem.fingerprint,budget=problem.budget(),max_nfev_or_maxiter=max_nfev,
                bounds_scaled=[np.broadcast_to(b,x0.shape).tolist() for b in bounds])


def evaluate_metrics(seed,d,bands,points=601,angles=(0,15,30),pols=('s','p'),factors=None):
    """Independent mesh, independent Airy recursion, front stack only."""
    mats=load_examples()[1];rows=[];worst=0.;weighted=0.
    factors=np.ones((1,len(d))) if factors is None else np.asarray(factors)
    for b in bands:
        # dense grid includes endpoints and midpoints; optimizer never sees it
        w=np.linspace(b.lo,b.hi,points)
        n=[np.ones_like(w)]+[material(mats[x['material']],w) for x in seed['layers']]+[material(mats[seed['substrate']],w)]
        for fi,factor in enumerate(factors):
            for a in angles:
                for p in pols:
                    z=optics.recursive(w,n,np.asarray(d)*factor,a,p);v=z[b.observable]-b.target
                    if b.sense=='upper':v=np.maximum(v,0)
                    if b.sense=='lower':v=np.minimum(v,0)
                    # sample worst target error, NOT continuous bound
                    worst=max(worst,float(np.max(abs(v)/b.scale)))
                    cost=float(.5*b.weight*np.sum(trapezoid_weights(w)*(v/b.scale)**2))
                    weighted+=cost/(len(angles)*len(pols)*len(factors))
                    rows.append(dict(band=b.name,angle_deg=a,polarization=p,scenario=fi,
                        R_mean=float(np.sum(trapezoid_weights(w)*z['R'])),R_max=float(max(z['R'])),
                        T_mean=float(np.sum(trapezoid_weights(w)*z['T'])),T_min=float(min(z['T'])),
                        T_max=float(max(z['T'])),A_mean=float(np.sum(trapezoid_weights(w)*z['A'])),
                        normalized_sample_worst=float(max(abs(v)/b.scale))))
    return dict(cost=weighted,sample_worst_normalized_target_error=worst,points_per_band=points,angles_deg=list(angles),rows=rows)


def merge_identical_layers(seed,d):
    out=json.loads(json.dumps(seed));layers=[];ds=[]
    for layer,di in zip(seed['layers'],d):
        if layers and layers[-1]['material']==layer['material']:ds[-1]+=float(di)
        else:layers.append(dict(layer));ds.append(float(di))
    for l,di in zip(layers,ds):l['thickness_um']=di;l['thickness_nm']=1000*di
    out['layers']=layers;return out,np.array(ds)


def insert_layer(seed,d,host,position_fraction,material_id,thickness,mode='add'):
    """Split host and add a needle, or replace a centered host interval.
    This makes exact finite topology; manufacturability checked separately.
    """
    d=np.asarray(d,float)
    if not 0<=host<len(d) or not 0<position_fraction<1 or thickness<0:raise ValueError('invalid insertion')
    left=d[host]*position_fraction;right=d[host]-left
    if mode=='replace':left-=thickness/2;right-=thickness/2
    elif mode!='add':raise ValueError('add or replace required')
    if min(left,right)<0:raise ValueError('replacement exceeds host')
    layers=[dict(x) for x in seed['layers']];old=dict(layers[host])
    layers[host:host+1]=[dict(old),dict(material=material_id),dict(old)]
    ds=np.r_[d[:host],left,thickness,right,d[host+1:]]
    out=json.loads(json.dumps(seed));out['layers']=layers
    for l,di in zip(layers,ds):l['thickness_um']=float(di);l['thickness_nm']=float(1000*di)
    return out,ds


def manufacturing_violations(d,d_min=0.03,d_max=np.inf,total_max=np.inf,layer_max=30):
    d=np.asarray(d,float)
    return dict(min_thickness_um=max(0.,float(d_min-min(d))),max_thickness_um=max(0.,float(max(d)-d_max)),
                total_thickness_um=max(0.,float(sum(d)-total_max)),layer_count=max(0,len(d)-layer_max))


def trust_region_surrogate(problem,x0,bounds=(.4,1.6),steps=12,radius=.12):
    """Local linear residual surrogate, actual-model acceptance at EVERY trial.
    Exact tangent rebuild only after acceptance; this is not trained ML.
    Small dense unconstrained GN proposal then bounds/TR projection, not exact TR solve.
    """
    x=np.asarray(x0,float).copy();r,J=problem.evaluate(x,True);trace=[]
    start=time.perf_counter()
    for k in range(steps):
        delta=np.linalg.lstsq(np.vstack([J,1e-4*np.eye(len(x))]),np.r_[-r,np.zeros(len(x))],rcond=None)[0]
        delta*=min(1.,radius/max(np.linalg.norm(delta),1e-30));trial=np.clip(x+delta,*bounds);delta=trial-x
        pred=.5*(r@r-(r+J@delta)@(r+J@delta))
        rt=problem.forward_fun(trial);actual=.5*(r@r-rt@rt);rho=actual/pred if pred>1e-15 else -np.inf
        accepted=bool(rho>.1 and actual>0)
        trace.append(dict(iteration=k,radius=radius,predicted_reduction=float(pred),actual_reduction=float(actual),rho=float(rho) if np.isfinite(rho) else None,accepted=accepted))
        if accepted:x=trial;r,J=problem.evaluate(x,True)
        if rho<.25:radius*=.5
        elif rho>.75 and np.linalg.norm(delta)>.8*radius:radius=min(.5,radius*2)
        if radius<1e-5:break
    return dict(x=x.tolist(),thickness_um=(x*problem.scale_d).tolist(),cost=float(.5*r@r),seconds=time.perf_counter()-start,trace=trace,budget=problem.budget())


def solve_constrained(problem,x0,total_max_um,d_min_um=.03,d_max_um=2.,maxiter=80):
    """SLSQP refinement: actual linear total thickness cap, no post-hoc clipping."""
    def fg(x):
        r,j=problem.evaluate(x,True);return .5*r@r,j.T@r
    constraints=[dict(type='ineq',fun=lambda x:total_max_um-x@problem.scale_d,
                      jac=lambda x:-problem.scale_d)]
    start=time.perf_counter()
    r=minimize(fg,np.asarray(x0),jac=True,method='SLSQP',bounds=list(zip(d_min_um/problem.scale_d,d_max_um/problem.scale_d)),
               constraints=constraints,options=dict(maxiter=maxiter,ftol=1e-11))
    return dict(x=r.x.tolist(),thickness_um=(r.x*problem.scale_d).tolist(),cost=float(r.fun),seconds=time.perf_counter()-start,
                success=bool(r.success),status=int(r.status),message=str(r.message),budget=problem.budget(),
                violations=manufacturing_violations(r.x*problem.scale_d,d_min_um,d_max_um,total_max_um))


def sampled_minimax_R(seed,w,angles,scale=.03,bounds_scaled=(.4,1.6),x0=None,maxiter=80):
    """Finite sample epigraph min t subject R_i(d)/scale <= t. No continuum claim."""
    d0=np.array([v['thickness_um'] for v in seed['layers']]);mats=load_examples()[1]
    n=[1]+[material(mats[v['material']],w) for v in seed['layers']]+[material(mats[seed['substrate']],w)]
    calls=0;cache={}
    def vals(x):
        nonlocal calls
        key=np.asarray(x).tobytes()
        if key in cache:return cache[key]
        values=[];jacs=[]
        for a in angles:
            for p in ('s','p'):
                z=spectrum_jacobian(w,n,x*d0,a,p);calls+=1
                values.append(z['R']/scale);jacs.append(z['JR']*d0[None,:]/scale)
        v=np.concatenate(values);j=np.concatenate(jacs);cache.clear();cache[key]=(v,j);return v,j
    x=np.ones(len(d0)) if x0 is None else np.asarray(x0);v,_=vals(x);z0=np.r_[x,max(v)+1e-6]
    t0=time.perf_counter()
    res=minimize(lambda z:z[-1],z0,jac=lambda z:np.r_[np.zeros(len(d0)),1.],method='SLSQP',
        bounds=[bounds_scaled]*len(d0)+[(0,None)],
        constraints=[dict(type='ineq',fun=lambda z:z[-1]-vals(z[:-1])[0],jac=lambda z:np.c_[-vals(z[:-1])[1],np.ones(len(v))])],
        options=dict(maxiter=maxiter,ftol=1e-10))
    vv,_=vals(res.x[:-1])
    return dict(x=res.x[:-1].tolist(),thickness_um=(res.x[:-1]*d0).tolist(),t=float(res.x[-1]),actual_sample_max=float(max(vv)),
                constraint_violation=float(max(0,max(vv)-res.x[-1])),success=bool(res.success),status=int(res.status),message=str(res.message),
                seconds=time.perf_counter()-t0,spectrum_calls=calls,points=len(w),angles_deg=list(angles))
