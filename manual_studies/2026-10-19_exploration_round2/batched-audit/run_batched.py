#!/usr/bin/env python3
"""Second-round standalone batched wavelength audit; synthetic lossless optics only."""
from __future__ import annotations
import csv, hashlib, json, platform, time
from pathlib import Path
import numpy as np
import scipy
import prior_adaptive as p
ROOT=Path(__file__).resolve().parent
BAND=p.BAND
METHODS=['uniform129','offset129','scalar_prior129','batched_top1_129','batched_top2_129']
TARGET=.5
BUDGET=129
class Meter(p.Meter):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.batch_sizes=[]
    def __call__(self,w):
        y=super().__call__(w);self.batch_sizes.append(len(y));return y

def samples(lo,hi,count,offset=False):return p.fixed_samples(lo,hi,count,offset)

def choose_brackets(w,y,k):
    """Only the current coarse observations are available to selection."""
    w=np.asarray(w);y=np.asarray(y);idx=np.argsort(w);w=w[idx];y=y[idx]
    peaks=[i for i in range(1,len(w)-1) if y[i]>=y[i-1] and y[i]>=y[i+1]]
    # Endpoint maxima remain admissible. A flat spectrum has deterministic tie-breaks.
    if y[0]>=y[1]:peaks.append(0)
    if y[-1]>=y[-2]:peaks.append(len(w)-1)
    peaks.sort(key=lambda i:(-y[i],w[i]))
    selected=[]
    for i in peaks:
        a,b=max(0,i-1),min(len(w)-1,i+1)
        if any(not(w[b]<=z['a'] or w[a]>=z['b']) for z in selected):continue
        selected.append({'a':float(w[a]),'b':float(w[b]),'x':float(w[i]),'y':float(y[i])})
        if len(selected)==k:break
    if not selected:raise RuntimeError('no bracket')
    return selected

def batched(meter,budget=129,k=1,wall=False):
    """17 global anchors, then seven 16-point batches at budget=129.
    One/two highest coarse local-max intervals, equal allocation per live bracket.
    Each bracket retains its best observed point; refine around the best point's
    immediate neighbours. No fitted height, derivative, resonance centre or oracle.
    In wall mode, finite-precision brackets retire; later batches fill widest gaps.
    """
    start=meter.points;meter(np.linspace(*BAND,min(17,budget)))
    brackets=choose_brackets(meter.w,meter.y,k);trace=[]
    while meter.points-start<budget:
        remain=budget-(meter.points-start);count=min(16,remain)
        live=[b for b in brackets if b['b']-b['a']>128*np.spacing(b['x'])]
        if not live:
            w=np.unique(meter.w);ix=np.argsort(np.diff(w))[-count:]
            xs=(w[ix]+w[ix+1])/2;meter(xs);continue
        parts=[];sizes=[]
        for j,b in enumerate(live):
            q=count//len(live)+int(j<count%len(live));sizes.append(q)
            parts.append(np.linspace(b['a'],b['b'],q+2)[1:-1])
        # Filter exact cached coordinates without counting them as newly evaluated.
        # Replacement uses the midpoint of the largest uncovered global gap.
        xs=np.concatenate(parts);old=set(meter.w);seen=set();duplicate=0
        for j,x in enumerate(xs):
            if x in old or x in seen:
                known=np.unique(np.r_[meter.w,xs[:j]]);ix=int(np.argmax(np.diff(known)))
                xs[j]=(known[ix]+known[ix+1])/2;duplicate+=1
            seen.add(float(xs[j]))
        ys=meter(xs);offset=0
        for b,q in zip(live,sizes):
            if not q:continue
            x=np.r_[b['a'],b['x'],b['b'],xs[offset:offset+q]]
            # Boundary values may be older, but are always real previously measured values.
            vals=[]
            for xx in x[:3]:
                matches=np.flatnonzero(np.asarray(meter.w)==xx)
                vals.append(meter.y[int(matches[-1])])
            yy=np.r_[vals,ys[offset:offset+q]];offset+=q
            mask=(x>=b['a'])&(x<=b['b']);x=x[mask];yy=yy[mask]
            order=np.argsort(x);x=x[order];yy=yy[order];best=int(np.argmax(yy))
            # Stable ties choose smallest coordinate, as in coarse selection.
            b.update(a=float(x[max(0,best-1)]),b=float(x[min(len(x)-1,best+1)]),x=float(x[best]),y=float(yy[best]))
        trace.append({'points':meter.points-start,'live_brackets':len(live),'duplicates_replaced':duplicate})
    return {'initial_bracket_count':len(brackets),'final_brackets':brackets,'rounds':trace}

def run_method(name,m,budget=129):
    if name.startswith('uniform'):m(samples(*BAND,budget))
    elif name.startswith('offset'):m(samples(*BAND,budget,True))
    elif name.startswith('scalar_prior'):return p.adaptive(m,*BAND,budget)
    else:return batched(m,budget,int('top2' in name)+1)
    return None

def make_cases():
    rng=np.random.default_rng(20261019)
    cases=[]
    def add(group,i,d,n,**kw):cases.append({'group':group,'case':int(i),'d':np.asarray(d),'n':np.asarray(n),**kw})
    for i,c in enumerate(rng.uniform(.985,1.015,12)):add('prior_hidden',i,*p.cavity(c,8,1),center_parameter=float(c))
    moving=list(np.linspace(.985,1.015,13))+[.994,1.006,1.009,.991]
    for i,c in enumerate(moving):add('prior_changing',i,*p.cavity(c,8,1 if i<13 else 20 if i<15 else 100),center_parameter=float(c))
    for i,c in enumerate([.98713,1.0037,1.01273]):add('prior_ultranarrow',i,*p.cavity(c,16,100),center_parameter=c)
    for i,c in enumerate([.99,1.,1.01]):
        n=np.array([2.35,1.45]*16);add('prior_clean',i,c/(4*n),n,center_parameter=c)
    # Held-out construction fixed before looking at results: low-index spacer,
    # mirrors terminated in H on both sides, detuned optical thickness, and a
    # cascaded pair. No previous candidate results or true peak positions used.
    hrng=np.random.default_rng(902761)
    for i,c in enumerate(hrng.uniform(.97,1.03,6)):
        ml=6+i%3;mr=ml if i<4 else ml+1
        n=np.array([2.12,1.38]*ml+[1.38]+[1.38,2.12]*mr)
        d=1/(4*n);d[2*ml]=c/(2*1.38)
        if i%2:d*=1+.012*np.sin(np.arange(len(n))*1.731)
        add('heldout_low_spacer',i,d,n,center_parameter=float(c))
    for i,c in enumerate([.978,1.007,1.023]):
        n=np.array([2.2,1.42]*5+[2.2]+[1.42,2.2]*4+[1.42]+[2.2,1.42]*5)
        d=1/(4*n);d[10]=c/(2*2.2);d[19]=(2-c)/(2*1.42)
        add('heldout_double_defect',i,d,n,center_parameter=c)
    # Smooth, clearly violating thin single-layer controls supplement narrow peaks.
    for i in range(3):
        n=np.array([1.1+.03*i]);d=np.array([.10+.02*i]);add('heldout_smooth',i,d,n)
    return cases

def write_csv(name,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with (ROOT/name).open('w',newline='') as f:
        out=csv.DictWriter(f,keys);out.writeheader()
        for r in rows:out.writerow({k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in r.items()})

def classification(s,ref):return {'false_pass':bool(s['sampled_max']<=TARGET and ref['max']>TARGET),'false_alarm':bool(s['sampled_max']>TARGET and ref['max']<=TARGET),'underestimate':ref['max']-s['sampled_max']}

def main():
    start=time.perf_counter();cases=make_cases();refs=[];rows=[];timings=[]
    # Shared setup physics validation is outside per-method budget and recorded.
    a=time.perf_counter();physics=p.validate_physics();setup_wall=time.perf_counter()-a
    for c in cases:
        ref=p.reference(c['d'],c['n'],[BAND],points=16385)
        c['reference']=ref;refs.append({k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in c.items()})
        for name in METHODS:
            m=Meter(c['d'],c['n']);a=time.perf_counter();trace=run_method(name,m);elapsed=time.perf_counter()-a;s=m.summary()
            rows.append({'group':c['group'],'case':c['case'],'method':name,'layers':len(c['n']),'reference_max':ref['max'],'threshold_T':TARGET,'total_wall_s':elapsed,'controller_plus_meter_s':elapsed-s['kernel_wall_s'],'batch_sizes':m.batch_sizes,'trace':trace,**classification(s,ref),**s})
        print(c['group'],c['case'],'ref',round(ref['max'],8),flush=True)
    write_csv('fixed_budget.csv',rows)
    # Repeated warmed time for the same completed 129-point task, random order.
    # Seven rounds and all 47 cases; warmups equal points per method and separately charged.
    rng=np.random.default_rng(47609)
    for repeat in range(7):
        for ci in rng.permutation(len(cases)):
            c=cases[int(ci)]
            for name in rng.permutation(METHODS):
                wm=Meter(c['d'],c['n']);a=time.perf_counter();wm(samples(*BAND,129));warm=time.perf_counter()-a
                m=Meter(c['d'],c['n']);a=time.perf_counter();run_method(str(name),m);elapsed=time.perf_counter()-a;s=m.summary()
                timings.append({'group':c['group'],'case':c['case'],'method':str(name),'repeat':repeat,'layers':len(c['n']),'total_wall_s':elapsed,'controller_plus_meter_s':elapsed-s['kernel_wall_s'],'warmup_wall_s':warm,'warmup_points':129,'warmup_layer_point_work':129*len(c['n']),**classification(s,c['reference']),**s})
    write_csv('warmed_task_timing.csv',timings)
    # Paired 5ms and 50ms caps, representative same-family and held-out cases.
    selected=[c for c in cases if (c['group']=='prior_hidden' and c['case'] in [0,5]) or c['group']=='prior_ultranarrow' or (c['group']=='heldout_low_spacer' and c['case'] in [0,5]) or (c['group']=='heldout_double_defect' and c['case']==0) or (c['group']=='prior_clean' and c['case']==0)]
    wall=[]
    for cap in [.005,.05]:
        for repeat in range(5):
            for ci in rng.permutation(len(selected)):
                c=selected[int(ci)]
                for name in rng.permutation(METHODS):
                    wm=Meter(c['d'],c['n']);a=time.perf_counter();wm(samples(*BAND,129));warm=time.perf_counter()-a
                    m=Meter(c['d'],c['n']);a=time.perf_counter();m.deadline=a+cap
                    try:
                        if str(name).startswith('batched'):batched(m,10**8,int('top2' in str(name))+1,True)
                        elif str(name).startswith('scalar'):
                            while True:p.adaptive(m,*BAND,129,warm=m.summary()['argmax_um'] if m.points else None)
                        else:
                            level=0
                            while True:
                                if level==0:x=np.array(BAND)
                                else:
                                    den=2**level;x=BAND[0]+(np.arange(1,den,2)+(.123 if str(name).startswith('offset') else 0))*(BAND[1]-BAND[0])/den
                                for pos in range(0,len(x),129):m(x[pos:pos+129])
                                level+=1
                    except p.Deadline:pass
                    elapsed=time.perf_counter()-a;s=m.summary()
                    wall.append({'group':c['group'],'case':c['case'],'method':str(name),'repeat':repeat,'wall_cap_s':cap,'total_wall_s':elapsed,'overshoot_s':max(0,elapsed-cap),'controller_plus_meter_s':elapsed-s['kernel_wall_s'],'warmup_wall_s':warm,'warmup_points':129,'warmup_layer_point_work':129*len(c['n']),**classification(s,c['reference']),**s})
        print('wall cap',cap,'finished',flush=True)
    write_csv('wall_budget.csv',wall)
    summary={'fixed':[],'timing':[],'wall':[]}
    for group in sorted(set(c['group'] for c in cases)):
        for name in METHODS:
            rr=[r for r in rows if r['group']==group and r['method']==name]
            tt=[r['total_wall_s'] for r in timings if r['group']==group and r['method']==name]
            summary['fixed'].append({'group':group,'method':name,'n':len(rr),'false_passes':sum(r['false_pass'] for r in rr),'false_alarms':sum(r['false_alarm'] for r in rr),'median_underestimate':float(np.median([r['underestimate'] for r in rr])),'total_points':sum(r['physical_points'] for r in rr),'total_layer_point_work':sum(r['layer_point_work'] for r in rr)})
            summary['timing'].append({'group':group,'method':name,'n':len(tt),'median_s':float(np.median(tt)),'p10_s':float(np.quantile(tt,.1)),'p90_s':float(np.quantile(tt,.9)),'min_s':float(min(tt)),'max_s':float(max(tt))})
    for cap in [.005,.05]:
        for group in sorted(set(c['group'] for c in selected)):
            for name in METHODS:
                rr=[r for r in wall if r['group']==group and r['method']==name and r['wall_cap_s']==cap]
                summary['wall'].append({'group':group,'method':name,'cap_s':cap,'n':len(rr),'false_passes':sum(r['false_pass'] for r in rr),'false_alarms':sum(r['false_alarm'] for r in rr),'median_points':float(np.median([r['physical_points'] for r in rr])),'median_elapsed_s':float(np.median([r['total_wall_s'] for r in rr])),'max_overshoot_s':max(r['overshoot_s'] for r in rr),'median_underestimate':float(np.median([r['underestimate'] for r in rr]))})
    result={'scope':'standalone cloud synthetic lossless normal-incidence coherent audit; no optimization or main software changes','config':{'band_um':BAND,'threshold_T':TARGET,'point_budget':BUDGET,'methods':METHODS,'fixed_timing_repeats':7,'wall_repeats':5,'heldout_policy':'construction frozen in source before run; no post-hoc tuning; structurally related synthetic holdout is not external validation'},'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'platform':platform.platform()},'physics_validation':physics,'shared_setup_wall_s':setup_wall,'references':refs,'fixed_rows':rows,'timing_rows':timings,'wall_rows':wall,'summary':summary,'total_run_wall_s':time.perf_counter()-start}
    (ROOT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));(ROOT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print('DONE',result['total_run_wall_s'],flush=True)
if __name__=='__main__':main()
