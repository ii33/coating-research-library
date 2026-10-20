#!/usr/bin/env python3
"""Work-counted, fixed-measure local angle-constraint exchange pilot."""
from __future__ import annotations
import argparse,csv,json,math,platform,time
from pathlib import Path
from collections import OrderedDict
import numpy as np
import scipy
from scipy.optimize import minimize,minimize_scalar
import optics_base as h
ROOT=Path(__file__).resolve().parent
METHODS=('original_angles','fixed_dense_angles','angle_exchange')
class WorkEnd(Exception):pass


class PointModel:
    """Scattered wavelength/angle/polarization queries, same tangential E,H physics."""
    def __init__(self,case,wl,angles,pols):
        self.wl=np.asarray(wl,float);self.angles=np.asarray(angles,float);self.pols=np.asarray(pols);self.Q=len(wl)
        mats,sub=h.materials(case);n=np.array([h.nk_values(m,self.wl) for m in ['air',*mats,sub]])
        qz=np.sqrt(n*n-np.sin(np.deg2rad(self.angles))**2+0j);qz=np.where((qz.imag<0)|((abs(qz.imag)<1e-14)&(qz.real<0)),-qz,qz)
        self.eta=np.where(self.pols[None,:]=='s',qz,n*n/qz);self.phase=2*np.pi*qz[1:-1]/self.wl
        self.rif=(self.eta[:-1]-self.eta[1:])/(self.eta[:-1]+self.eta[1:]);self.tif=2*self.eta[:-1]/(self.eta[:-1]+self.eta[1:])
    def solve(self,x):
        r=self.rif[-1].copy();t=self.tif[-1].copy()
        for j in range(len(x)-1,-1,-1):
            p=np.exp(1j*self.phase[j]*x[j]);den=1+self.rif[j]*r*p*p;t=self.tif[j]*t*p/den;r=(self.rif[j]+r*p*p)/den
        return abs(r)**2,self.eta[-1].real/self.eta[0].real*abs(t)**2


def grid_queries(angles,points=81,midpoints=False):
    ws=[(a+(np.arange(points)+.5)*(b-a)/points if midpoints else np.linspace(a,b,points)) for a,b in h.WINDOWS]
    if midpoints:ws=[np.r_[a,w,b] for (a,b),w in zip(h.WINDOWS,ws)]
    wl=np.concatenate(ws);sc=h.scenarios(angles);qwl=np.tile(wl,len(sc));qa=np.repeat([a for a,p,w in sc],len(wl));qp=np.repeat([p for a,p,w in sc],len(wl));w=np.repeat([w for a,p,w in sc],len(wl))/len(wl)
    return qwl,qa,qp,w


def metric(case,R,P,weights=None):
    gs=[R/.01-1]
    if case['min_entering_flux'] is not None:gs.append((case['min_entering_flux']-P)/.1)
    g=np.concatenate(gs);v=max(0.,float(g.max()));loss=float(np.mean((R/.01)**2)) if weights is None else float(np.sum(weights*(R/.01)**2))
    return g,v,loss


class Work:
    def __init__(self,limit):self.limit=int(limit);self.points=0;self.calls=0;self.by_stage={};self.soft_limit=self.limit
    def solve(self,model,x,stage,final=False):
        if self.points+model.Q>min(self.limit,self.soft_limit):raise WorkEnd
        R,P=model.solve(x);self.points+=model.Q;self.calls+=1
        z=self.by_stage.setdefault(stage,{'calls':0,'points':0});z['calls']+=1;z['points']+=model.Q
        if not np.isfinite(R).all() or not np.isfinite(P).all():raise FloatingPointError('nonfinite optics')
        return R,P


def optimize_epoch(case,x,angles,extra,work,quota):
    wl,aa,pp,weights=grid_queries(angles)
    if extra:
        wl=np.r_[wl,[p['wavelength_um'] for p in extra]];aa=np.r_[aa,[p['angle_deg'] for p in extra]];pp=np.r_[pp,[p['pol'] for p in extra]]
    model=PointModel(case,wl,aa,pp)
    # Fixed secondary measure always uses only the original 0/30/45-degree grid.
    mask=np.isin(aa,[0.,30.,45.]);base_weights=np.zeros(len(wl));nwl=162
    for j,(a,p,w) in enumerate(h.scenarios([0.,30.,45.])):
        inds=np.where((aa==a)&(pp==p))[0][:nwl];base_weights[inds]=w/nwl
    cache=OrderedDict();best=[math.inf,math.inf,np.array(x,copy=True)];start=work.points;oldlimit=work.soft_limit;work.soft_limit=min(work.limit,start+int(quota));solver={'status':'work budget reached','success':False,'nit':None}
    def response(z):
        ds=np.clip(np.asarray(z[:-1])*(h.UPPER-h.LOWER)+h.LOWER,h.LOWER,h.UPPER);key=ds.tobytes()
        if key not in cache:
            R,P=work.solve(model,ds,'optimization');g,v,tie=metric(case,R,P,base_weights);cache[key]=(g,v,tie,R,P)
            if (v,tie)<(best[0],best[1]):best[:]=[v,tie,ds.copy()]
            if len(cache)>8*len(x)+16:cache.popitem(last=False)
        return cache[key]
    z0=np.r_[(np.array(x)-h.LOWER)/(h.UPPER-h.LOWER),0.]
    try:
        g,v,tie,_,_=response(z0);z0[-1]=max(0.,float(g.max()))+1e-7
        def fun(z):return float(z[-1]+1e-4*response(z)[2])
        def constraints(z):return z[-1]-response(z)[0]
        fit=minimize(fun,z0,method='SLSQP',bounds=[(0.,1.)]*len(x)+[(0.,1e5)],constraints=[{'type':'ineq','fun':constraints}],options={'ftol':1e-10,'maxiter':1000,'disp':False})
        solver={'status':str(fit.message),'success':bool(fit.success),'nit':int(fit.nit)}
    except WorkEnd:pass
    finally:work.soft_limit=oldlimit
    return best[2],{'calls_points_used':work.points-start,'active_query_points':model.Q,'best_active_max_violation':best[0],'solver':solver}


def discover_peaks(case,x,ref,refR,refP,work,existing,max_new=4):
    # Reference grid is an already charged, common checkpoint, not a new hidden grid.
    ws=np.concatenate([np.linspace(a,b,81) for a,b in h.WINDOWS]);angles=np.arange(0,46,5);sc=h.scenarios(angles);R=refR.reshape(len(sc),162);candidates=[];diagnostics=[]
    for wi in range(2):
        for pol in ('s','p'):
            rows=[]
            for a in angles:
                j=next(j for j,(ang,p,w) in enumerate(sc) if ang==a and (p==pol or a==0));rows.append(R[j,wi*81:(wi+1)*81])
            rows=np.array(rows);envelope=rows.max(axis=1)
            peaks=[i for i in range(1,len(angles)-1) if envelope[i]>=envelope[i-1] and envelope[i]>=envelope[i+1]]
            for i in peaks:
                iw=int(rows[i].argmax());wl=float(ws[wi*81+iw]);lo=float(angles[i-1]);hi=float(angles[i+1]);cost0=work.points
                def f(u):
                    model=PointModel(case,[wl],[lo+u*(hi-lo)],[pol]);rr,pp=work.solve(model,x,'angle_peak_oracle');return -float(rr[0])
                try:
                    fit=minimize_scalar(f,bounds=(0.,1.),method='bounded',options={'xatol':1e-11,'maxiter':60});a=lo+fit.x*(hi-lo);rr=-float(fit.fun)
                except WorkEnd:return [],diagnostics
                q={'wavelength_um':wl,'angle_deg':float(a),'pol':pol,'R_when_found':rr,'oracle_point_work':work.points-cost0};diagnostics.append(q)
                if rr>.01 and not any(abs(q['wavelength_um']-p['wavelength_um'])<1e-5 and abs(q['angle_deg']-p['angle_deg'])<1e-3 and q['pol']==p['pol'] for p in existing):candidates.append(q)
    candidates.sort(key=lambda p:p['R_when_found'],reverse=True)
    return candidates[:max_new],diagnostics


def run(source,method,limit=2_000_000,rounds=4):
    case=source['case'];x=np.array(source['thickness_um']);work=Work(limit);wl,aa,pp,w=grid_queries(np.arange(0,46,5));ref=PointModel(case,wl,aa,pp);archive=[math.inf,math.inf,x.copy()];trace=[];extra=[];epochs=[];t=time.perf_counter()
    def checkpoint(z,label):
        R,P=work.solve(ref,z,'common_reference');g,v,tie=metric(case,R,P,w)
        if (v,tie)<(archive[0],archive[1]):archive[:]=[v,tie,np.array(z,copy=True)]
        trace.append({'label':label,'points':work.points,'calls':work.calls,'candidate_max_violation':v,'candidate_max_R':float(R.max()),'archive_max_violation':archive[0],'archive_secondary_loss':archive[1]})
        return R,P
    R,P=checkpoint(x,'initial');initial_v=archive[0];initial_R=float(R.max())
    for k in range(rounds):
        remaining=limit-work.points;reserve=(rounds-k)*2*ref.Q+2000
        quota=max(0,(remaining-reserve)//(rounds-k));angles=np.arange(0,46,5).tolist() if method=='fixed_dense_angles' else [0.,30.,45.]
        activeQ=162*len(h.scenarios(angles))+len(extra)
        if quota<2*activeQ:break
        x,info=optimize_epoch(case,archive[2],angles,extra,work,quota);R,P=checkpoint(x,f'epoch{k+1}')
        # Discovery must use the retained candidate rather than an unretained trial.
        if not np.array_equal(x,archive[2]):R,P=checkpoint(archive[2],f'epoch{k+1}_archive')
        discovered=[];diagnostics=[]
        if method=='angle_exchange' and k<rounds-1:
            discovered,diagnostics=discover_peaks(case,archive[2],ref,R,P,work,extra);extra.extend(discovered)
        epochs.append({'round':k+1,'optimization':info,'discovered':discovered,'oracle_diagnostics':diagnostics,'active_extra_constraints_after_round':len(extra),'cumulative_points':work.points})
    return {'case':case,'source_method':source['source_method'],'seed':source['seed'],'method':method,'extra_point_budget':limit,'actual_extra_points':work.points,'actual_extra_optical_calls':work.calls,'cost_by_stage':work.by_stage,'optimization_and_reference_seconds':time.perf_counter()-t,'source_thickness_um':source['thickness_um'],'thickness_um':archive[2].tolist(),'initial_common_reference_max_violation':initial_v,'initial_common_reference_worst_R':initial_R,'final_common_reference_max_violation':archive[0],'final_common_secondary_loss':archive[1],'extra_constraints':extra,'epochs':epochs,'trace':trace,'selection':'lowest max normalized violation on fixed common 5-degree/81-wavelength reference; independent fine audit does not select'}


def final_audit(result,midpoints=2048,angle_step=.5):
    case=result['case'];x=result['thickness_um'];mats,sub=h.materials(case);rows=[];maxerr=0.;pointwork=0;t=time.perf_counter();worst_by=[]
    for lo,hi in h.WINDOWS:
        wl=np.r_[lo,lo+(np.arange(midpoints)+.5)*(hi-lo)/midpoints,hi]
        for angle in np.arange(0,45+angle_step/2,angle_step):
            model=h.OpticalModel(wl,mats,sub,[float(angle)]);R,P=model.solve(x);Rm,Pm=model.matrix(x);maxerr=max(maxerr,float(abs(R-Rm).max()),float(abs(P-Pm).max()));pointwork+=len(wl)*len(model.scenarios)*2
            for j,(a,p,w) in enumerate(model.scenarios):
                idx=int(R[j].argmax());_,v,tie=metric(case,R[j],P[j]);rows.append({'window_um':[lo,hi],'angle_deg':float(angle),'pol':p,'max_R':float(R[j,idx]),'argmax_R_um':float(wl[idx]),'min_entering_flux':float(P[j].min()),'max_normalized_violation':v})
        for pol in ('s','p'):
            # p at 0 degree equals s and is represented as s in the query grid.
            qs=[q for q in rows if q['window_um']==[lo,hi] and (q['pol']==pol or q['angle_deg']==0)]
            q=max(qs,key=lambda q:q['max_R']);worst_by.append(q)
    refine=[];refwork=0;refcalls=0
    for q in worst_by:
        lo,hi=q['window_um'];cell=(hi-lo)/midpoints;wl0=q['argmax_R_um'];a0=q['angle_deg'];wlo=max(lo,wl0-2*cell);whi=min(hi,wl0+2*cell);alo=max(0.,a0-1);ahi=min(45.,a0+1);pol=q['pol']
        def f(u):
            nonlocal refwork,refcalls
            model=PointModel(case,[wlo+u[0]*(whi-wlo)],[alo+u[1]*(ahi-alo)],[pol]);R,P=model.solve(x);refwork+=1;refcalls+=1;return -float(R[0])
        u0=np.array([(wl0-wlo)/(whi-wlo),(a0-alo)/(ahi-alo)]);simplex=np.array([u0,np.clip(u0+[.08 if u0[0]<.9 else -.08,0],0,1),np.clip(u0+[0,.08 if u0[1]<.9 else -.08],0,1)])
        fit=minimize(f,u0,method='Nelder-Mead',bounds=[(0.,1.),(0.,1.)],options={'xatol':1e-10,'fatol':1e-12,'maxiter':250,'initial_simplex':simplex});refine.append({'window_um':q['window_um'],'pol':pol,'R':-float(fit.fun),'wavelength_um':float(wlo+fit.x[0]*(whi-wlo)),'angle_deg':float(alo+fit.x[1]*(ahi-alo)),'success':bool(fit.success),'scope':'bounded local 2D refinement around one fine-grid peak'})
    fineR=max(q['max_R'] for q in rows);refR=max(q['R'] for q in refine);maxR=max(fineR,refR);minP=min(q['min_entering_flux'] for q in rows);violation=max(maxR/.01-1,0.,0. if case['min_entering_flux'] is None else (case['min_entering_flux']-minP)/.1)
    return {'fine_grid_worst_R':fineR,'refined_worst_R':maxR,'min_entering_flux_fine_grid':minP,'max_normalized_violation_after_refinement':violation,'pass':violation<=1e-10,'fine_grid_rows':rows,'local_refinements':refine,'grid_point_work_both_kernels':pointwork,'local_refinement_points':refwork,'local_refinement_calls':refcalls,'independent_matrix_max_abs_error':maxerr,'audit_seconds':time.perf_counter()-t,'scope':'finite independent midpoint wavelength grid with .5-degree angles and bounded local peak refinements, not continuous certification'}


def physics_tests():
    case=h.case_def('tabulated6_multi');wl,aa,pp,w=grid_queries([0.,30.,45.],17);m=PointModel(case,wl,aa,pp);x=np.linspace(.01,1.1,6);R,P=m.solve(x);mats,sub=h.materials(case);wl0=np.concatenate([np.linspace(a,b,17) for a,b in h.WINDOWS]);old=h.OpticalModel(wl0,mats,sub,[0.,30.,45.]);Ro,Po=old.solve(x);err=max(float(abs(R-Ro.ravel()).max()),float(abs(P-Po.ravel()).max()));assert err<1e-12
    wtest=Work(5);s=PointModel(case,[3.],[30.],['s']);wtest.solve(s,x,'test');assert wtest.points==1 and wtest.calls==1
    train=np.linspace(0,1,81);audit=(np.arange(2048)+.5)/2048;assert not any(np.any(np.isclose(train,v,atol=1e-13,rtol=0)) for v in audit)
    return {'scattered_vs_cartesian_kernel_max_abs_error':err,'budget_point_counter':True,'2048_midpoint_interiors_disjoint_from_81_training':True}


def summarize(rs):
    out=[]
    for case in sorted({r['case']['name'] for r in rs}):
        for method in METHODS:
            xs=[r for r in rs if r['case']['name']==case and r['method']==method]
            out.append({'case':case,'method':method,'n':len(xs),'median_refined_worst_R_percent':100*float(np.median([r['audit']['refined_worst_R'] for r in xs])),'best_refined_worst_R_percent':100*min(r['audit']['refined_worst_R'] for r in xs),'worst_refined_worst_R_percent':100*max(r['audit']['refined_worst_R'] for r in xs),'success_count':sum(r['audit']['pass'] for r in xs),'median_actual_extra_points':float(np.median([r['actual_extra_points'] for r in xs])),'median_actual_extra_calls':float(np.median([r['actual_extra_optical_calls'] for r in xs])),'median_wall_seconds':float(np.median([r['optimization_and_reference_seconds'] for r in xs]))})
    return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--budget-points',type=int,default=2_000_000);ap.add_argument('--output',default='results');ap.add_argument('--audit-midpoints',type=int,default=2048);ap.add_argument('--seeds',type=int,nargs='+',default=[11,29,47,71,101]);args=ap.parse_args();out=ROOT/args.output;out.mkdir(exist_ok=True,parents=True);tests=physics_tests();(out/'physics_checks.json').write_text(json.dumps(tests,indent=2));sources=json.loads((ROOT/'seed_sources.json').read_text())['sources'];results=[]
    for src in sources:
        if src['seed'] not in args.seeds:continue
        order=list(METHODS);np.random.default_rng(src['seed']).shuffle(order)
        for method in order:
            r=run(src,method,args.budget_points);r['audit']=final_audit(r,args.audit_midpoints);results.append(r);(out/'results.json').write_text(json.dumps({'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},'args':vars(args),'results':results},indent=2));print(src['case']['name'],src['seed'],method,'R%',round(100*r['audit']['refined_worst_R'],6),'work',r['actual_extra_points'],'calls',r['actual_extra_optical_calls'],'added',len(r['extra_constraints']),flush=True)
    summary=summarize(results);(out/'summary.json').write_text(json.dumps(summary,indent=2))
    with (out/'summary.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
    print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':main()
