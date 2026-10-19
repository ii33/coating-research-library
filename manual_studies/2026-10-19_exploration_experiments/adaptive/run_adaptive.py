#!/usr/bin/env python3
"""Finite wavelength-audit experiment. Synthetic constants only; no certificate.
Standalone cloud experiment; imports the unchanged previously verified TMM.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, os, platform, sys, time
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import minimize_scalar
ROOT=Path(__file__).resolve().parent
# Local provenance-preserved kernel makes the experiment self-contained.
_parser=argparse.ArgumentParser(description=__doc__)
_parser.add_argument('--kernel-root',type=Path,default=ROOT/'kernel')
_opts,_unknown=_parser.parse_known_args()
KERNEL=_opts.kernel_root.resolve()/'run_experiment.py'
sys.path.insert(0,str(KERNEL.parent))
from run_experiment import tmm_normal, reflection_recursion, validate_physics, LAYER_N, classical_templates
BAND=(.94,1.06)
SEEDS=[11,29,47]
TARGET_T=.5
AUDIT_BUDGET=129
class Deadline(Exception):pass
class Meter:
    def __init__(self,d,n,n0=1.,ns=1.,quantity='T'):
        self.d=np.array(d);self.n=np.array(n);self.n0=n0;self.ns=ns;self.quantity=quantity
        self.points=0;self.calls=0;self.wall=0.;self.cpu=0.;self.energy_error=0.;self.failures=[]
        self.w=[];self.y=[];self.deadline=None
    def __call__(self,w):
        if self.deadline is not None and time.perf_counter()>=self.deadline:raise Deadline()
        w=np.atleast_1d(w).astype(float);a=time.perf_counter();b=time.process_time()
        r,t=tmm_normal(w,self.d,self.n,self.n0,self.ns)
        self.wall+=time.perf_counter()-a;self.cpu+=time.process_time()-b
        self.points+=len(w);self.calls+=1
        e=float(np.max(np.abs(r+t-1)));self.energy_error=max(self.energy_error,e)
        if not np.all(np.isfinite(r+t)) or e>1e-9:
            self.failures.append({'type':'nonfinite_or_energy','error':e});raise FloatingPointError(self.failures[-1])
        y=t if self.quantity=='T' else r
        self.w.extend(w.tolist());self.y.extend(y.tolist());return y
    def summary(self):
        ix=int(np.argmax(self.y));return {'sampled_max':self.y[ix],'argmax_um':self.w[ix],
        'physical_points':self.points,'layer_point_work':self.points*max(1,len(self.d)),
        'forward_calls':self.calls,'kernel_wall_s':self.wall,'kernel_cpu_s':self.cpu,
        'max_energy_error':self.energy_error,'numerical_failures':self.failures}
def cavity(center,m=8,order=1):
    n=np.array([2.35,1.45]*m+[2.35]+[1.45,2.35]*m)
    d=1/(4*n);d[2*m]=order*center/(2*2.35)
    return d,n

def fixed_samples(lo,hi,count,offset=False):
    if not offset:return np.linspace(lo,hi,count)
    # Endpoints mandatory; remaining points lie at offset cell centers.
    return np.r_[lo,hi,lo+(np.arange(count-2)+.5)*(hi-lo)/(count-2)]

def adaptive(meter,lo,hi,budget=129,warm=None):
    """17 global anchors; bracket coarse maxima and optional extrapolated old peak;
    refine with true TMM; preserve global exploration using largest-gap midpoints.
    No response derivative bound and no peak-height oracle is supplied.
    """
    start= meter.points
    meter(np.linspace(lo,hi,min(17,budget)))
    brackets=[]
    if warm is not None and lo<warm<hi and meter.points-start<budget:
        half=(hi-lo)/64
        a,b=max(lo,warm-half),min(hi,warm+half)
        meter([warm]);brackets.append((a,b,'tracked'))
    ws=np.array(meter.w[-(meter.points-start):]);ys=np.array(meter.y[-(meter.points-start):])
    order=np.argsort(ws);ws=ws[order];ys=ys[order]
    peaks=[i for i in range(1,len(ws)-1) if ys[i]>=ys[i-1] and ys[i]>=ys[i+1]]
    peaks.sort(key=lambda i:ys[i],reverse=True)
    brackets += [(float(ws[i-1]),float(ws[i+1]),'coarse_local') for i in peaks]
    used=[]
    for a,b,label in brackets:
        remain=budget-(meter.points-start)
        if remain<8:break
        # Max 28 true calls per bracket; bounded golden/parabolic search is heuristic.
        q=min(28,remain)
        res=minimize_scalar(lambda w:-float(meter([w])[0]),bounds=(a,b),method='bounded',
             options={'xatol':1e-11,'maxiter':q})
        used.append({'a':a,'b':b,'source':label,'success':bool(res.success),'nfev':int(res.nfev)})
    # Spend exactly the remaining point budget on data-independent geometric coverage.
    # This avoids giving the adaptive method free cost or hiding unused allowance.
    while meter.points-start<budget:
        old=np.unique(np.array(meter.w[-(meter.points-start):]));gaps=np.diff(old)
        take=min(16,budget-(meter.points-start),len(gaps))
        ix=np.argsort(gaps)[-take:]
        meter((old[ix]+old[ix+1])/2)
    return used

def reference(d,n,windows,quantity='T',n0=1.,ns=1.,points=16385):
    """Independent frozen grid, disjoint interior offset grid, endpoints/local extrema.
    The local search is heuristic. No finite-grid result is a continuous certificate.
    """
    m=Meter(d,n,n0,ns,quantity);out=[];a=time.perf_counter()
    for lo,hi in windows:
        w=np.linspace(lo,hi,points);y=m(w)
        z=lo+(np.arange(points-1)+.5)*(hi-lo)/(points-1);v=m(z)
        j=np.argsort(np.r_[w,z]);ww=np.r_[w,z][j];yy=np.r_[y,v][j]
        inds=np.flatnonzero((yy[1:-1]>=yy[:-2])&(yy[1:-1]>=yy[2:]))+1
        # All local maxima are refined; not merely those reported by the tested method.
        refinement=[];refinement_failures=[]
        for i in inds:
            mid=(ww[i-1]+ww[i+1])/2;half=(ww[i+1]-ww[i-1])/2
            # Dimensionless coordinate prevents scipy's sqrt(eps)*abs(lambda) stopping
            # floor from hiding ultra-narrow resonances in the reference itself.
            res=minimize_scalar(lambda u:-float(m([mid+half*u])[0]),bounds=(-1.,1.),method='bounded',options={'xatol':1e-12,'maxiter':100})
            refinement.append((float(mid+half*res.x),float(-res.fun)))
            if not res.success:refinement_failures.append({'bracket_um':[float(ww[i-1]),float(ww[i+1])],'nfev':int(res.nfev),'message':str(res.message)})
        candidates=[(float(w[np.argmax(y)]),float(y.max())),(float(z[np.argmax(v)]),float(v.max()))]+refinement
        loc,mx=max(candidates,key=lambda p:p[1])
        out.append({'window_um':[lo,hi],'max':mx,'argmax_um':loc,'grid_max':float(y.max()),'offset_max':float(v.max()),
                    'integral_mean':float(np.trapezoid(y,w)/(hi-lo)),
                    'upper_for_integral_violation':(.5 if quantity=='T' else .01),
                    'integral_mean_upper_violation':float(np.trapezoid(np.maximum(y-(.5 if quantity=='T' else .01),0),w)/(hi-lo)),
                    'local_extrema_locations_um':[q[0] for q in refinement],'local_extrema_refined':len(inds),'local_extrema_search_failures':refinement_failures})
    s=m.summary();s['total_wall_s']=time.perf_counter()-a
    # Independent Fresnel recursion for R at a random subset of all reference points.
    probe=np.unique(np.r_[np.linspace(windows[0][0],windows[-1][1],501),[q for z in out for q in z['local_extrema_locations_um']]])
    r,_=tmm_normal(probe,d,n,n0,ns)
    s['crosscheck_points_excluded_from_reference_meter']={'matrix_forward_points':len(probe),'independent_recursion_points':len(probe),'extra_layer_point_work':2*len(probe)*max(1,len(d))}
    s['matrix_recursion_R_max_abs_error']=float(np.max(abs(r-reflection_recursion(probe,d,n,n0,ns))))
    return {'windows':out,'max':max(x['max'] for x in out),'meter':s}

def detection_suite():
    rng=np.random.default_rng(20261019);centers=rng.uniform(.985,1.015,12)
    cases=[('engineered_hidden_resonance',i,float(c),1,8) for i,c in enumerate(centers)]
    # Small continuous changes, a jump, then higher longitudinal-order candidates.
    moving=list(np.linspace(.985,1.015,13))+[.994,1.006,1.009,.991]
    cases += [('changing_candidate',i,float(c),1 if i<13 else (20 if i<15 else 100),8) for i,c in enumerate(moving)]
    cases += [('ultranarrow_stress',i,c,100,16) for i,c in enumerate([.98713,1.0037,1.01273])]
    cases += [('clean_stopband_pass',i,c,0,8) for i,c in enumerate([.99,1.,1.01])]
    history={};rows=[];details=[]
    for group,i,center,order,mirrors in cases:
        if group=='clean_stopband_pass':
            n=np.array([2.35,1.45]*16);d=center/(4*n)
        else:d,n=cavity(center,mirrors,order)
        ref=reference(d,n,[BAND],points=16385)
        details.append({'group':group,'candidate':i,'thickness_um':d.tolist(),'layer_n':n.tolist(),'independent_reference':ref})
        for method in ['sparse17','fixed129','offset129','adaptive129','tracked_adaptive129']:
            m=Meter(d,n);t=time.perf_counter();brackets=[]
            if method=='sparse17':m(fixed_samples(*BAND,17))
            elif method=='fixed129':m(fixed_samples(*BAND,129))
            elif method=='offset129':m(fixed_samples(*BAND,129,offset=True))
            else:
                hist=history.get((group,method),[]) if group=='changing_candidate' else []
                # Wavelength extrapolation only, not an implicit-function/curvature implementation.
                warm=(hist[-1]+(hist[-1]-hist[-2]) if len(hist)>=2 else hist[-1] if hist else None) if method.startswith('tracked') else None
                brackets=adaptive(m,*BAND,budget=129,warm=warm)
            s=m.summary();s['total_wall_s']=time.perf_counter()-t
            history.setdefault((group,method),[]).append(s['argmax_um'])
            row={'group':group,'candidate':i,'method':method,'cavity_center_parameter_um':center,
                 'longitudinal_order':order,'layers':len(n),'total_thickness_um':float(d.sum()),'reference_max':ref['max'],
                 'reference_argmax_um':max(ref['windows'],key=lambda p:p['max'])['argmax_um'],
                 'target_upper_T':TARGET_T,'false_pass':bool(s['sampled_max']<=TARGET_T and ref['max']>TARGET_T),
                 'false_alarm':bool(s['sampled_max']>TARGET_T and ref['max']<=TARGET_T),
                 'absolute_max_underestimate':float(ref['max']-s['sampled_max']),**s}
            rows.append(row);details.append({'group':group,'candidate':i,'method':method,'brackets':brackets})
        print(f"audit {group} {i}: reference {ref['max']:.8f}",flush=True)
    return rows,details

def wall_suite():
    rows=[];cap=.050;rng=np.random.default_rng(20261019)
    for center in [.98713,1.0037,1.01273]:
        d,n=cavity(center,8);ref=reference(d,n,[BAND],points=8193)
        for repeat in range(3):
            methods=rng.permutation(['fixed_dyadic_wall','offset_dyadic_wall','adaptive_wall'])
            for method in methods:
                # Equal 129-point warmup, separately disclosed and excluded from timed work.
                tmm_normal(np.linspace(*BAND,129),d,n,1.,1.)
                m=Meter(d,n);start=time.perf_counter();m.deadline=start+cap;level=0;last_batch=0.
                while time.perf_counter()-start<cap:
                    before=time.perf_counter()
                    try:
                        if method=='adaptive_wall':adaptive(m,*BAND,129,warm=m.summary()['argmax_um'] if m.points else None)
                        else:
                            if level==0:vals=np.array(BAND)
                            else:
                                den=2**level
                                vals=BAND[0]+(np.arange(1,den,2)+(.123 if method.startswith('offset') else 0))*(BAND[1]-BAND[0])/den
                            for part in range(0,len(vals),129):
                                m(vals[part:part+129])
                                if time.perf_counter()-start>=cap:break
                            level+=1
                    except Deadline:break
                    last_batch=time.perf_counter()-before
                elapsed=time.perf_counter()-start
                rows.append({'method':str(method),'center':center,'repeat':repeat,'soft_wall_limit_s':cap,
                    'actual_wall_s':elapsed,'overshoot_s':max(0,elapsed-cap),'last_outer_batch_s':last_batch,
                    'reference_max':ref['max'],'warmup_points_outside_timed_work':129,
                    'warmup_layer_point_work':129*len(n),**m.summary()})
    return rows

class DesignMeter:
    def __init__(self,budget):self.budget=budget;self.points=0;self.calls=0;self.wall=0.;self.energy=0.
    def eval(self,x,w):
        if self.points+len(w)>self.budget:raise RuntimeError('budget would be exceeded')
        t=time.perf_counter();r,tr=tmm_normal(w,x,LAYER_N);self.wall+=time.perf_counter()-t
        self.points+=len(w);self.calls+=1;self.energy=max(self.energy,float(np.max(abs(r+tr-1))))
        if not np.all(np.isfinite(r)) or self.energy>1e-9:raise FloatingPointError('design physics failure')
        return r

def optimization_suite():
    windows=[(3.,5.),(8.,12.)];base=[np.linspace(a,b,9) for a,b in windows]
    rows=[];budget=40000
    for seed in SEEDS:
        initial=np.random.default_rng(seed).uniform(.005,2.5,6)
        for method in ['fixed_sparse18','fixed_dense26','fixed_offset26','exchange26']:
            rng=np.random.default_rng(seed+1000);m=DesignMeter(budget)
            if method=='fixed_sparse18':w=np.concatenate(base)
            elif method=='fixed_offset26':w=np.concatenate([fixed_samples(a,b,13,True) for a,b in windows])
            elif method=='fixed_dense26':w=np.concatenate([np.linspace(a,b,13) for a,b in windows])
            else:w=np.concatenate([np.r_[q,a+(np.arange(4)*4+1)*(b-a)/16] for q,(a,b) in zip(base,windows)])
            x=initial.copy();r=m.eval(x,w);score=float(r.max());xscore=score
            accepted=0;refreshes=0;steps=0;counterexamples=0;history=[];t=time.perf_counter()
            while m.points+len(w)<=budget:
                if method=='exchange26' and steps%64==0 and m.points+2*129+len(w)<=budget:
                    slots=[]
                    for a,b in windows:
                        # Fixed 129-point adversarial scan; independent final grids remain unseen.
                        scan=np.linspace(a,b,129);rr=m.eval(x,scan)
                        inds=np.flatnonzero((rr[1:-1]>=rr[:-2])&(rr[1:-1]>=rr[2:]))+1
                        cand=sorted(inds,key=lambda j:rr[j],reverse=True)
                        pool=[float(scan[j]) for j in cand]+[float(scan[j]) for j in np.argsort(rr)[::-1]]
                        chosen=[]
                        for v in pool:
                            if all(abs(v-q)>(b-a)/512 for q in chosen) and all(abs(v-q)>(b-a)/1024 for q in np.linspace(a,b,9)):chosen.append(v)
                            if len(chosen)==4:break
                        slots.append(chosen)
                    neww=np.concatenate([np.r_[q,s] for q,s in zip(base,slots)])
                    oldscore=score;r=m.eval(x,neww);score=float(r.max());w=neww
                    counterexamples+=int(score>oldscore+1e-10);refreshes+=1
                    history.append({'step':steps,'score_before':oldscore,'score_after':score,'witnesses':slots})
                # Identical proposal law, schedule and initial seed across methods.
                scale=.2*(.997**steps)+.003
                trial=np.clip(x+rng.normal(0,scale,6),.005,2.5)
                rr=m.eval(trial,w);s=float(rr.max())
                if s<score:x=trial;score=s;accepted+=1
                steps+=1
            # Any remainder < one objective evaluation is logged as final diagnostic work,
            # not an extra partial objective or hidden optimization improvement.
            remainder=budget-m.points
            if remainder:m.eval(x,np.linspace(3,5,remainder))
            wall=time.perf_counter()-t
            ref=reference(x,LAYER_N,windows,'R',1.,3.42,points=8193)
            per=[]
            for q in ref['windows']:
                per.append({**q,'target_upper_R':.01,'max_violation_R':max(q['max']-.01,0),'passed':q['max']<=.01})
            rows.append({'seed':seed,'method':method,'initial_thickness_um':initial.tolist(),'final_thickness_um':x.tolist(),
              'layers':6,'total_thickness_um':float(x.sum()),'minimum_layer_um':float(x.min()),'material_switches':5,
              'target_R':.01,'working_sample_max_R':score,'reference_max_R':ref['max'],'max_violation_R':max(ref['max']-.01,0),
              'max_normalized_violation':max(ref['max']/.01-1,0),'window_equal_integral_mean_R':float(np.mean([q['integral_mean'] for q in per])),
              'window_equal_integral_mean_violation_R':float(np.mean([q['integral_mean_upper_violation'] for q in per])),
              'per_window':per,'finite_audit_pass':all(q['passed'] for q in per),'steps':steps,'accepted':accepted,'refreshes':refreshes,
              'counterexample_rounds':counterexamples,'physical_points':m.points,'layer_point_work':m.points*6,'forward_calls':m.calls,
              'kernel_wall_s':m.wall,'total_search_wall_s':wall,'remainder_diagnostic_points':remainder,'max_energy_error':m.energy,
              'final_reference':ref,'exchange_history':history,'numerical_failures':[]})
            print(f"design seed={seed} {method}: audited maxR={ref['max']:.8f}, steps={steps}, wall={wall:.3f}s",flush=True)
    return rows

def write_csv(path,rows):
    if not rows:return
    keys=list(dict.fromkeys(k for r in rows for k,v in r.items() if not isinstance(v,(dict,list))))
    with open(path,'w',newline='') as f:
        w=csv.DictWriter(f,keys,extrasaction='ignore');w.writeheader();w.writerows(rows)
def main():
    start=time.perf_counter();physics=validate_physics()
    detections,details=detection_suite();wall=wall_suite();designs=optimization_suite()
    summary={}
    for group in ['engineered_hidden_resonance','changing_candidate','ultranarrow_stress','clean_stopband_pass']:
        summary[group]={}
        for method in sorted({r['method'] for r in detections}):
            rs=[r for r in detections if r['group']==group and r['method']==method]
            summary[group][method]={'n':len(rs),'false_passes':sum(r['false_pass'] for r in rs),'false_alarms':sum(r['false_alarm'] for r in rs),'mean_max_underestimate':float(np.mean([r['absolute_max_underestimate'] for r in rs])),
               'total_points':sum(r['physical_points'] for r in rs),'total_layer_point_work':sum(r['layer_point_work'] for r in rs),'total_wall_s':sum(r['total_wall_s'] for r in rs)}
    result={'schema':1,'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'environment':{'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'platform':platform.platform(),'kernel_sha256':hashlib.sha256(KERNEL.read_bytes()).hexdigest()},
       'configuration':{'all_materials':'synthetic constant n, k explicitly zero; no measured material claims','preserved_preliminary_failure':'failure_history.md records invalid duplicate baseline wavelengths; final artifact contains only corrected current implementation','history_policy':'reset on every independent constructed candidate; peak extrapolation only in changing_candidate sequence','search_failure_policy':'all 12 failed AR designs retained; ultra-narrow misses retained; scalar maxiter failures retained in adaptive_brackets; final reference local-search failures retained per window','scope':'normal incidence, coherent isotropic layers, real semi-infinite exteriors, no backside','cavity':{'incident_n':1,'substrate_n':1,'high_n':2.35,'low_n':1.45,'target_upper_T':.5,'band_um':BAND,'mirror_pairs_each_side':8},
       'audit_budget':129,'sparse_diagnostic_budget':17,'detection_rng_seed':20261019,'optimizer_seeds':SEEDS,'optimizer_budget_points':40000,
       'design_problem':{'n0':1,'ns':3.42,'layer_n':LAYER_N.tolist(),'all_k':0,'windows_um':[[3,5],[8,12]],'gap':'unconstrained','R_upper':.01,'bounds_um':[.005,2.5]},
       'design_objective':'minimize sampled max R; final integral mean R uses fixed equal-window wavelength measure only','guarantee':'finite grids plus heuristic local extrema; never continuous certificate',
       'cost':'work-matched detection 129 actual points times same candidate layer count; design 40000 actual points and 6 layers including exchange scans/remainders. Sparse17 diagnostic is not work matched. Separate same wall-limit runs record differing actual work and overshoot.',
       'setup_checks_cost':'validate_physics setup regression is outside comparison work/timing; independent final reference has its own counts, plus separately disclosed matrix and independent-recursion crosschecks at 501 anchors plus all refined local extrema',
       'timing_note':'serial within this worker; shared host may have other processes. Total search timings include Python/controller overhead; final reference cost separate; no backward or derivative calls'},
       'physics_validation':physics,'detection_rows':detections,'adaptive_brackets':details,'wall_limit_rows':wall,'design_rows':designs,'summary':summary,
       'total_wall_s':time.perf_counter()-start,'failures':{'numerical':[],'search_nonpassing_runs':sum(not r['finite_audit_pass'] for r in designs),'detection_false_passes':sum(r['false_pass'] for r in detections)}}
    (ROOT/'results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
    write_csv(ROOT/'detection.csv',detections);write_csv(ROOT/'wall_limit.csv',wall);write_csv(ROOT/'optimization.csv',designs)
    (ROOT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));print('TOTAL',result['total_wall_s'])
if __name__=='__main__':main()
