#!/usr/bin/env python3
"""Read-only independent replay of frozen exploratory artifacts.
This audit is finite-grid plus local numerical refinement, not a certificate.
Run after the experiment workers have finished writing results.
"""
from __future__ import annotations
import hashlib, importlib.util, json, math, platform, sys, time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize_scalar
import scipy
ROOT=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location('audit_verified_kernel',ROOT/'projection'/'verified_power_kernel.py')
K=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(K)
COUNTS={'recursion_calls':0,'wavelengths':0,'literal_layer_updates':0}

def independent_R(w,ds,nn,n0=1.,ns=3.42,quantity='R'):
    """Independent scalar Fresnel recursion; do not call the power kernel."""
    w=np.atleast_1d(np.asarray(w,float));nn=np.asarray(nn,complex);ds=np.asarray(ds,float)
    mm=np.r_[complex(n0),nn,complex(ns)]
    rr=np.full(w.shape,(mm[-2]-mm[-1])/(mm[-2]+mm[-1]),complex)
    tt=np.full(w.shape,2*mm[-2]/(mm[-2]+mm[-1]),complex)
    for j in range(len(ds)-1,-1,-1):
        a=(mm[j]-mm[j+1])/(mm[j]+mm[j+1]);delta=2*np.pi*mm[j+1]*ds[j]/w;e=np.exp(2j*delta);den=1+a*rr*e
        tt=(2*mm[j]/(mm[j]+mm[j+1]))*tt*np.exp(1j*delta)/den
        rr=(a+rr*e)/den
    COUNTS['recursion_calls']+=1;COUNTS['wavelengths']+=len(w);COUNTS['literal_layer_updates']+=len(w)*len(ds)
    return np.abs(rr)**2 if quantity=='R' else float(ns/n0)*np.abs(tt)**2

def finite_extrema(ds,nn,windows,quantity='R',n0=1.,ns=3.42,intervals=16384):
    out=[]
    for lo,hi in windows:
        # Deliberately offset grid; endpoints always included. Values are never fed to search.
        w=np.r_[lo,lo+(np.arange(intervals)+.5)*(hi-lo)/intervals,hi]
        def value(x):
            return independent_R(x,ds,nn,n0,ns,quantity)
        y=value(w);ix=np.flatnonzero((y[1:-1]>y[:-2])&(y[1:-1]>y[2:]))+1
        peaks=[(float(w[int(np.argmax(y))]),float(np.max(y)))]
        for j in ix:
            mid=(w[j-1]+w[j+1])/2;half=(w[j+1]-w[j-1])/2
            q=minimize_scalar(lambda u:-float(value([mid+half*u])[0]),bounds=(-1.,1.),method='bounded',options={'xatol':1e-12,'maxiter':100})
            peaks.append((float(mid+half*q.x),float(-q.fun)))
        loc,mx=max(peaks,key=lambda p:p[1]);details={'window_um':[lo,hi],'max':mx,'argmax_um':loc,'offset_intervals':intervals,'local_maxima_refined':len(ix)}
        if quantity=='T':
            ri=float(independent_R([loc],ds,nn,n0,ns)[0]);rk,tk=K.tmm_normal([loc],ds,nn,n0,ns)
            details.update(lossless_T_from_independent_R=1-ri,recursion_RT_closure_abs_error=abs(ri+mx-1),matrix_T_at_replay_peak=float(tk[0]),matrix_RT_closure_abs_error=abs(float(rk[0]+tk[0]-1)))
        out.append(details)
    return {'max':max(v['max'] for v in out),'windows':out}

def main():
    started=time.perf_counter();issues=[];hashes={}
    for p in sorted(ROOT.rglob('*.py')):
        if '__pycache__' not in str(p):hashes[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
    physics=K.validate_physics()
    # Independent check over lossless random stacks, not only saved experiment candidates.
    rng=np.random.default_rng(778103);maxerr=0.;uniterr=0.
    for _ in range(30):
        count=int(rng.integers(0,13));ds=rng.uniform(.005,2.5,count);nn=rng.uniform(1.2,3.5,count);w=rng.uniform(.5,14.,127)
        r,t=K.tmm_normal(w,ds,nn);ri=independent_R(w,ds,nn)
        maxerr=max(maxerr,float(np.max(abs(r-ri))))
        rn,tn=K.tmm_normal(w*1000,ds*1000,nn);uniterr=max(uniterr,float(np.max(abs(r-rn))),float(np.max(abs(t-tn))))
    if maxerr>1e-11 or uniterr>1e-11:issues.append('physics regression failed')
    adaptive=json.loads((ROOT/'adaptive'/'results.json').read_text());ad={'detection':[],'design':[],'cost_checks':[]}
    cases=[x for x in adaptive['adaptive_brackets'] if 'thickness_um' in x]
    for c in cases:
        rows=[r for r in adaptive['detection_rows'] if r['group']==c['group'] and r['candidate']==c['candidate']]
        ref=finite_extrema(c['thickness_um'],c['layer_n'],[adaptive['configuration']['cavity']['band_um']],'T',1.,1.,65536)
        print('detection replay',c['group'],c['candidate'],flush=True)
        item={'group':c['group'],'candidate':c['candidate'],'independent_replay':ref,'reported_reference_max':rows[0]['reference_max']}
        for r in rows:
            fp=bool(r['sampled_max']<=r['target_upper_T'] and ref['max']>r['target_upper_T'])
            if fp!=r['false_pass']:issues.append(f"detection false-pass mismatch {c['group']} {c['candidate']} {r['method']}")
            targetpoints=17 if r['method']=='sparse17' else 129
            ok=r['physical_points']==targetpoints and r['layer_point_work']==r['physical_points']*len(c['layer_n'])
            ad['cost_checks'].append({'group':c['group'],'candidate':c['candidate'],'method':r['method'],'valid':ok})
            if not ok:issues.append('detection cost mismatch')
        ad['detection'].append(item)
    for r in adaptive['design_rows']:
        ref=finite_extrema(r['final_thickness_um'],[1.45,2.35]*3,[(3,5),(8,12)])
        fp=r['working_sample_max_R']<=.01 and ref['max']>.01
        ad['design'].append({'seed':r['seed'],'method':r['method'],'independent_replay':ref,'reported_reference_max_R':r['reference_max_R'],'false_pass':fp})
        ok=r['physical_points']==40000 and r['layer_point_work']==240000
        ad['cost_checks'].append({'seed':r['seed'],'method':r['method'],'valid':ok})
        if not ok:issues.append('adaptive design cost mismatch')
        if bool(ref['max']<=.01)!=r['finite_audit_pass']:issues.append('adaptive design pass mismatch')
    projection=json.loads((ROOT/'projection'/'results.json').read_text());pr=[]
    for c in projection['results']:
        worsterr=0.;falsepasses=0;rows=[]
        for r in c['candidates']:
            ref=finite_extrema(r['repaired_d'],r['n'],[(3,5)],intervals=8192)
            reported=r.get('repaired_audited_max_R',r['repaired_dense_max_R'])
            worsterr=max(worsterr,abs(reported-ref['max']))
            fp=bool(r['repaired_max_R']<=.01 and ref['max']>.01);falsepasses+=fp
            rows.append({'label':r['label'],'max_R':ref['max'],'false_pass':fp})
        pr.append({'case':c['case'],'candidate_count':len(rows),'max_abs_audit_replay_difference':worsterr,'false_pass_count':falsepasses,'raw_projected_score_max_abs_difference':c['max_raw_projected_inner_error'],'candidates':rows})
        if worsterr>1e-7:issues.append(f"projection replay discrepancy {c['case']} {worsterr}")
    lp=json.loads((ROOT/'layer-packs'/'results'/'results.json').read_text());packs=[]
    for r in lp['runs']:
        item={'case':r['case'],'seed':r['seed'],'method':r['method']}
        pool=lp['pools'][f"{r['case']}:{r['seed']}"]
        base=lp['bases'][r['case']]
        pw=np.r_[3+(np.arange(8192)+.5)*2/8192,8+(np.arange(8192)+.5)*4/8192,3,5,8,12]
        pbase=independent_R(pw,base['d'],base['n']);pmask=pbase<=.008
        expected=162*sum(len(p['d']) for p in pool)+sum(x['calls']*162*len(x['final_d']) for x in r['refinements'])
        item['charged_cost_matches']=expected==r['total_search_wavelength_layer_updates_charged']
        if not item['charged_cost_matches']:issues.append('layer-pack point×layer cost mismatch')
        for key in ['best_global','best_protected']:
            cand=r[key];ref=finite_extrema(cand['d'],cand['n'],[(3,5),(8,12)],intervals=8192);reported=r[key+'_audit']
            canonical_d=r[key+'_canonical_d'];canonical_n=r[key+'_canonical_n']
            wc=np.r_[np.linspace(3,5,8193),np.linspace(8,12,8193)]
            canon_error=float(np.max(abs(independent_R(wc,cand['d'],cand['n'])-independent_R(wc,canonical_d,canonical_n))))
            if canon_error>1e-11:issues.append('layer-pack canonicalization replay discrepancy')
            pcurr=independent_R(pw,cand['d'],cand['n']);pmax=float(np.max(pcurr[pmask]));pfail=bool(cand['score'][0]<=1e-12 and pmax>.01+1e-12)
            if key=='best_protected' and pfail:issues.append('layer-pack frozen-P false pass')
            item[key]={'shifted_frozen_P_max_R':pmax,'frozen_P_false_pass':pfail,'canonicalization_replay_max_abs_R_difference':canon_error,'canonical_layer_count':len(canonical_d),'replay_max_R':ref['max'],'reported_max_R':reported['worst_R'],'false_pass':bool(cand['score'][1]<=1e-12 and ref['max']>.01+1e-12),'nominal_layer_count':len(cand['d'])}
            if abs(ref['max']-reported['worst_R'])>1e-7:issues.append('layer-pack replay discrepancy')
            if bool(ref['max']<=.01+1e-12)!=reported['all_targets_pass']:issues.append('layer-pack pass mismatch')
        packs.append(item)
    out={'audit_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'source_sha256':hashes,'input_result_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'adaptive'/'results.json',ROOT/'projection'/'results.json',ROOT/'layer-packs'/'results'/'results.json']},'physics':physics,'independent_random_kernel_max_abs_R_error':maxerr,'um_nm_kernel_max_abs_error':uniterr,'adaptive':ad,'projection':pr,'layer_packs':packs,'replay_cost':COUNTS,'issues':issues,'wall_seconds':time.perf_counter()-started,'scope':'Independent scalar recursion; offset finite grids, endpoints and heuristic local extrema. No continuous guarantee. Read-only replay; no optimization was guided by these points.'}
    (ROOT/'independent-replay.json').write_text(json.dumps(out,indent=2,ensure_ascii=False,allow_nan=False))
    print(json.dumps({'issues':issues,'kernel_R_error':maxerr,'unit_error':uniterr,'detection_cases':len(ad['detection']),'adaptive_designs':len(ad['design']),'projection_catalogs':len(pr),'pack_runs':len(packs),'cost':COUNTS,'wall_seconds':out['wall_seconds']},indent=2))
if __name__=='__main__':main()
