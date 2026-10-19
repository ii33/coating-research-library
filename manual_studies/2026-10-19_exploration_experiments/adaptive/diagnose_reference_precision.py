#!/usr/bin/env python3
"""Retain a failed reference-audit attempt: absolute-lambda bounded minimization.
The scipy stopping floor can itself miss ultra-narrow physical resonances.
This diagnostic is not part of the work-matched comparison.
"""
import json
import numpy as np
from scipy.optimize import minimize_scalar
import run_adaptive as a

def main():
    rows=[]
    for c in [.98713,1.0037,1.01273]:
        d,n=a.cavity(c,16,100);m=a.Meter(d,n);lo,hi=a.BAND
        w=np.linspace(lo,hi,16385);z=lo+(np.arange(16384)+.5)*(hi-lo)/16384
        xx=np.sort(np.r_[w,z]);yy=m(xx)
        inds=np.flatnonzero((yy[1:-1]>=yy[:-2])&(yy[1:-1]>=yy[2:]))+1
        old=float(yy.max());out=[]
        for i in inds:
            res=minimize_scalar(lambda x:-float(m([x])[0]),bounds=(xx[i-1],xx[i+1]),method='bounded',options={'xatol':1e-13,'maxiter':60})
            old=max(old,float(-res.fun));out.append({'success':bool(res.success),'max_T':float(-res.fun),'lambda_um':float(res.x),'nfev':res.nfev})
        new=a.reference(d,n,[a.BAND],points=16385)
        rows.append({'center':c,'old_absolute_lambda_reference_max_T':old,'old_reference_meter':m.summary(),
          'old_local_refinements':out,'scaled_coordinate_reference_max_T':new['max'],'scaled_coordinate_reference_meter':new['meter'],
          'diagnosis':'optimizer convergence flag is not a continuous peak certificate; dimensionless rescaling repairs this observed stopping-tolerance failure, not all possible missed peaks'})
    (a.ROOT/'reference_precision_diagnostic.json').write_text(json.dumps(rows,indent=2));print([(r['center'],r['old_absolute_lambda_reference_max_T'],r['scaled_coordinate_reference_max_T']) for r in rows])
if __name__=='__main__':main()
