#!/usr/bin/env python3
"""Post-first-pass diagnostic only: disentangle local-coordinate precision from batching.
Not a preregistered method ranking and does not replace the primary comparison.
"""
import json,time
import numpy as np
from scipy.optimize import minimize_scalar
import run_batched as b

def scalar_scaled(meter,lo,hi,budget=129,warm=None):
    start=meter.points;meter(np.linspace(lo,hi,min(17,budget)));brackets=[]
    if warm is not None and lo<warm<hi and meter.points-start<budget:
        half=(hi-lo)/64;a,z=max(lo,warm-half),min(hi,warm+half)
        meter([warm]);brackets.append((a,z,'tracked'))
    w=np.array(meter.w[-(meter.points-start):]);y=np.array(meter.y[-(meter.points-start):]);idx=np.argsort(w);w=w[idx];y=y[idx]
    inds=[i for i in range(1,len(w)-1) if y[i]>=y[i-1] and y[i]>=y[i+1]];inds.sort(key=lambda i:y[i],reverse=True)
    brackets += [(float(w[i-1]),float(w[i+1]),'coarse') for i in inds]
    used=[]
    for lo,hi,label in brackets:
        remain=budget-(meter.points-start)
        if remain<8:break
        mid=(hi+lo)/2;half=(hi-lo)/2
        r=minimize_scalar(lambda u:-float(meter([mid+half*u])[0]),bounds=(-1.,1.),method='bounded',options={'xatol':1e-11,'maxiter':min(28,remain)})
        used.append({'source':label,'success':bool(r.success),'nfev':int(r.nfev)})
    while meter.points-start<budget:
        old=np.unique(meter.w[-(meter.points-start):]);gaps=np.diff(old);take=min(16,budget-(meter.points-start),len(gaps));ix=np.argsort(gaps)[-take:];meter((old[ix]+old[ix+1])/2)
    return used

def main():
    primary=json.loads((b.ROOT/'results.json').read_text());cases=[c for c in primary['references'] if c['group']=='prior_ultranarrow'];rows=[];rng=np.random.default_rng(7109)
    for repeat in range(5):
        for c in cases:
            for name in rng.permutation(['scalar_prior','scalar_scaled','batched_top2']):
                for mode in ['points129','wall50ms']:
                    wm=b.Meter(c['d'],c['n']);t=time.perf_counter();wm(b.samples(*b.BAND,129));warm=time.perf_counter()-t
                    m=b.Meter(c['d'],c['n']);start=time.perf_counter();trace=[]
                    if mode=='wall50ms':m.deadline=start+.05
                    try:
                        while True:
                            if name=='batched_top2':trace=b.batched(m,129 if mode=='points129' else 10**8,2)
                            elif name=='scalar_scaled':trace=scalar_scaled(m,*b.BAND,129,warm=m.summary()['argmax_um'] if m.points and mode=='wall50ms' else None)
                            else:trace=b.p.adaptive(m,*b.BAND,129,warm=m.summary()['argmax_um'] if m.points and mode=='wall50ms' else None)
                            if mode=='points129':break
                    except b.p.Deadline:pass
                    elapsed=time.perf_counter()-start;s=m.summary()
                    rows.append({'case':c['case'],'layers':len(c['n']),'repeat':repeat,'method':str(name),'mode':mode,'total_wall_s':elapsed,'warmup_wall_s':warm,'warmup_points':129,'warmup_layer_point_work':129*len(c['n']),'trace':trace,**s,**b.classification(s,c['reference'])})
    summary=[]
    for mode in ['points129','wall50ms']:
        for method in ['scalar_prior','scalar_scaled','batched_top2']:
            rr=[r for r in rows if r['mode']==mode and r['method']==method]
            summary.append({'method':method,'mode':mode,'n':len(rr),'false_passes':sum(r['false_pass'] for r in rr),'false_alarms':sum(r['false_alarm'] for r in rr),'median_wall_s':float(np.median([r['total_wall_s'] for r in rr])),'p10_wall_s':float(np.quantile([r['total_wall_s'] for r in rr],.1)),'p90_wall_s':float(np.quantile([r['total_wall_s'] for r in rr],.9)),'median_points':float(np.median([r['physical_points'] for r in rr]))})
    out={'purpose':'Post-primary diagnostic isolates scalar local coordinate choice; explicitly exploratory, no primary batch retuning','rows':rows,'summary':summary};(b.ROOT/'scaled_scalar_diagnostic.json').write_text(json.dumps(out,indent=2));b.write_csv('scaled_scalar_diagnostic.csv',rows);print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
