#!/usr/bin/env python3
"""Finite minimax/exchange and reflection-absorption tradeoff experiments."""
import json,time
from optimization_core import *

def main():
    seed=load_examples()[0]['E02'];results={};bands=[Band('AR',3.5,4.5,'R',0,.03)]
    w=np.linspace(3.5,4.5,9);trace=[];x=None
    mats=load_examples()[1];dense=np.linspace(3.5,4.5,2002);nn=[1]+[material(mats[v['material']],dense) for v in seed['layers']]+[material(mats[seed['substrate']],dense)]
    for stage in range(4):
        r=sampled_minimax_R(seed,w,[0,15,30],x0=x);add=[];maxv=0.
        for angle in [0,15,30]:
            for pol in ('s','p'):
                rr=optics.recursive(dense,nn,r['thickness_um'],angle,pol)['R']/.03;idx=np.argmax(rr)
                maxv=max(maxv,float(rr[idx]))
                if rr[idx]>r['t']+1e-6:add.append(float(dense[idx]))
        r['dense_sample_max']=maxv;r['added_wavelengths_um']=add;trace.append(r);x=r['x']
        if not add:break
        w=np.unique(np.r_[w,add])
    r['holdout']=evaluate_metrics(seed,r['thickness_um'],bands,1201,[0,7.5,15,22.5,30])
    results['finite_minimax']=dict(trace=trace,result=r,finite_grid_certified_only=True)
    trade=[]
    for wa in [0,.1,1,10]:
        bb=bands+[Band('absorption',3.5,4.5,'A',0,.005,wa)]
        pp=Problem(seed,bb,31,[0,30]);z=solve(pp,max_nfev=60);z['absorption_weight']=wa
        met=evaluate_metrics(seed,z['thickness_um'],bands,601,[0,15,30]);z['audit_R_mean']=float(np.mean([a['R_mean'] for a in met['rows']]));z['audit_A_mean']=float(np.mean([a['A_mean'] for a in met['rows']]));z['audit_T_mean']=float(np.mean([a['T_mean'] for a in met['rows']]));trade.append(z)
    results['reflection_absorption_tradeoff']=trade
    (ROOT/'data/extension_results.json').write_text(json.dumps(results,indent=2,allow_nan=False)+'\n')
    print(json.dumps(results,indent=2))
if __name__=='__main__':main()
