"""Run four frozen synthetic cases; emits machine-readable diagnostics and CSV.
No adaptive candidate search. Budget failure writes partial results and is visible.
"""
from pathlib import Path
from copy import deepcopy
from itertools import product,combinations
import sys,json,csv,platform,hashlib,time
import numpy as np
import dual_finite as m
ROOT=m.ROOT

def dump(name,obj):
    (ROOT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def clean(x):
    if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [clean(v) for v in x]
    if isinstance(x,np.ndarray):return clean(x.tolist())
    if isinstance(x,(float,np.floating)):return float(x) if np.isfinite(x) else None
    if isinstance(x,np.integer):return int(x)
    return x

def csvwrite(name,rows):
    with (ROOT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def mapfile(name,c,p,w,a):
    z=m.t01.output_values(c,a);rows=[]
    for j in range(len(p)):
        rows.append(dict(point=j,x_local_m=p[j,0],y_local_m=p[j,1],area_fraction=w[j],**{k:(float(v[j]) if np.isfinite(v[j]) else '') for k,v in z.items()}))
    csvwrite(name,rows)

def case_a(budget):
    c=json.loads((ROOT/'data/t01_contract.json').read_text());pts=m.diagnostic_points()
    s=m.t02.point_source(c['vapor']['position_L_m']);Q=c['vapor']['reference_atom_flux_m2_s']*.6**2*np.pi
    times=np.array([.551,1.371,4.091,6.541]);x,n=m.t01.pose(c,'D',times,pts)
    out={}
    for case in c['cases']:
        ms=m.plates(c,case);v=Q*m.t02.transfer_kernel(x,n,s,ms)
        v0,i0,_=m.t01.flux_at(c,times,x,n,case)
        out[case]={'instant_vapor_relative':float(np.max(np.abs(v-v0))/v0.mean())}
    # T01 event reference is independent of fixed midpoint time discretization.
    event=m.t01.EventIntegrator(c,'D',scan=8192)
    ref=event.integrate(pts,order=16)
    budget.add(event.report()['channel_flux_evaluations']+len(times)*len(pts)*len(c['cases'])*3)
    for case in c['cases']:
        ts,ws=m.t02.time_quadrature(0,7.3,1531,1,c['clock']['vapor_gate_s']);acc=np.zeros((len(pts),4))
        ms=m.plates(c,case)
        for k in range(0,len(ts),32):
            t=ts[k:k+32];w=ws[k:k+32];xx,nn=m.t01.pose(c,'D',t,pts)
            budget.add(len(t)*len(pts)*2)
            gv=Q*m.t02.transfer_kernel(xx,nn,s,ms)
            _,gi,_=m.t01.flux_at(c,t,xx,nn,case)
            gv*=((t>=.55)&(t<6.55))[:,None]
            acc[:,0]+=w@gv;acc[:,1]+=w@gi;acc[:,2]+=w@gi*100*m.E_CHARGE
            acc[:,3]+=w@((gi>0)&(gv==0))
        out[case].update(m.compare(acc,ref[case]))
        out[case]['time_integral_pass']=out[case]['max_relative_integral_difference']<=.003
    return out

def case_b(budget):
    budget.add(2*(16+64+256)+3*101*12*64)
    H=.6;a=.12;Q=1.;exact=Q/(np.pi*(H*H+a*a));rows=[]
    for nr,na in [(2,8),(4,16),(8,32)]:
        s=m.t02.disk_source(a,nr,na);b=m.t02.RectangleMask([1,0,.3],np.eye(3),1,2,0)
        v=m.t02.transfer_kernel([[0,0,H]],[[0,0,-1]],s)[0]
        h=m.t02.transfer_kernel([[0,0,H]],[[0,0,-1]],s,[b])[0]
        rows.append(dict(source_nodes=nr*na,flux=v,exact=exact,relative_error=abs(v-exact)/exact,half_fraction=h/v,half_error=abs(h/v-.5)))
    # Spatial penumbra profile: no claim that this short plot is a convergence proof.
    s=m.t02.disk_source(a,12,64);b=m.t02.RectangleMask([1,0,.3],np.eye(3),1,2,0)
    x=np.linspace(-.25,.25,101);p=np.column_stack([x,np.zeros_like(x),np.full_like(x,H)]);n=np.tile([0,0,-1.],(len(x),1))
    full=m.t02.transfer_kernel(p,n,s);thin=m.t02.transfer_kernel(p,n,s,[b])
    b.thickness_m=.06;thick=m.t02.transfer_kernel(p,n,s,[b])
    csvwrite('data/B_penumbra.csv',[dict(x_m=xx,unmasked=f,thin=t,thick=k,thin_transmission=t/f,thick_transmission=k/f) for xx,f,t,k in zip(x,full,thin,thick)])
    return rows

def case_c(budget):
    c=m.config();diag=m.diagnostic_points();cache={};stats={};rows=[]
    for s,t,p in product(range(2),repeat=3):
        pts,w=m.grid(p);v,meta=m.integrate(c,pts,m.TIME_LEVELS[t],*m.SOURCE_LEVELS[s],budget=budget)
        name=f'S{s}T{t}P{p}';cache[name]=v;stats[name]=m.metrics(c,v,w)
        rows.append(dict(run=name,**meta,**{'mean_h_nm':stats[name]['h_nm']['mean'],'cv_h':stats[name]['h_nm']['cv'],'sample_pv_h':stats[name]['h_nm']['sample_pv'],'mean_D_m2':stats[name]['ion_fluence_m2']['mean'],'cv_D':stats[name]['ion_fluence_m2']['cv'],'sample_pv_D':stats[name]['ion_fluence_m2']['sample_pv']}))
        print(name,meta,flush=True)
    pts,w=m.grid(2);v,meta=m.integrate(c,pts,m.TIME_LEVELS[1],*m.SOURCE_LEVELS[1],budget=budget)
    stats['S1T1P2']=m.metrics(c,v,w);mapfile('data/C_main_map.csv',c,pts,w,v)
    # All 8 corner pairs and coarse-to-fine diagonal are reported, not only one favorable edge.
    comparisons=[]
    for name,other in combinations(stats,2):
        q=m.stats_compare(stats[name],stats[other]);q.update(first=name,second=other)
        q['pass']=q['mean_relative']<=.003 and q['cv_absolute']<=.003 and q['sample_pv_absolute']<=.008
        comparisons.append(q)
    diag_runs={};diag_rows=[]
    for s,t in [(0,1),(1,0),(1,1),(2,1),(1,2),(2,2)]:
        a,meta=m.integrate(c,diag,m.TIME_LEVELS[t],*m.SOURCE_LEVELS[s],budget=budget)
        diag_runs[f'S{s}T{t}']=a
    hold,meta=m.integrate(c,diag,m.TIME_LEVELS[2],7,29,family='equal_area',budget=budget)
    diag_runs['holdout_equal_area']=hold
    for name,a in diag_runs.items():
        if name=='holdout_equal_area':continue  # never label self-agreement as convergence
        q=m.compare(a,hold);q.update(run=name,reference='holdout_equal_area');q['pass']=q['max_relative_integral_difference']<=.003 and q['ion_only_max_difference_s']<=.01;diag_rows.append(q)
    # Explicit axis increments at fixed other coordinate, including third levels.
    axis=[]
    for x,y in [('S0T1','S1T1'),('S1T1','S2T1'),('S1T0','S1T1'),('S1T1','S1T2'),('S1T1','S2T2'),('S2T2','holdout_equal_area')]:
        q=m.compare(diag_runs[x],diag_runs[y]);q.update(first=x,second=y);q['pass']=q['max_relative_integral_difference']<=.003 and q['ion_only_max_difference_s']<=.01;axis.append(q)
    mapfile('data/C_diagnostic_holdout.csv',c,diag,np.ones(len(diag))/len(diag),hold)
    csvwrite('data/C_cross_runs.csv',rows);csvwrite('data/C_cross_comparisons.csv',comparisons);csvwrite('data/C_diagnostic_comparisons.csv',diag_rows);csvwrite('data/C_axis_comparisons.csv',axis)
    # Exact linear ion scaling yields unchanged h with doubled dose in this explicitly decoupled model.
    nominal=diag_runs['S1T1'];c2=deepcopy(c);c2['ion']['total_ions_s']*=2
    doubled,_=m.integrate(c2,diag,m.TIME_LEVELS[1],*m.SOURCE_LEVELS[1],budget=budget)
    equiv={'max_thickness_relative_change':float(np.max(np.abs(doubled[:,0]-nominal[:,0]))/nominal[:,0].mean()),'max_dose_doubling_residual':float(np.max(np.abs(doubled[:,1]-2*nominal[:,1]))/nominal[:,1].mean()),'physical_caveat':'unit retention, zero resputtering and fixed density; does not assert physical decoupling in a real ion-assisted film'}
    scenarios=[]
    for plate in ['vapor_plate','ion_plate']:
        for shift in [-.001,.001]:
            cc=deepcopy(c);cc['plates'][plate]['origin_L_m'][0]+=shift
            aa,_=m.integrate(cc,diag,m.TIME_LEVELS[1],*m.SOURCE_LEVELS[1],budget=budget)
            scenarios.append(dict(parameter=plate+'_x_m',perturbation=shift,**m.compare(aa,nominal)))
    cc=deepcopy(c)
    for pp in cc['plates'].values():pp['thickness_m']=0
    thin,_=m.integrate(cc,diag,m.TIME_LEVELS[1],*m.SOURCE_LEVELS[1],budget=budget)
    for j in range(13):
        scenarios.append(dict(parameter='both_plates_zero_thickness_point_'+str(j),perturbation=0,max_relative_integral_difference=float(np.max(np.abs(thin[j,:3]-nominal[j,:3])/np.mean(nominal[:,:3],axis=0))),ion_only_max_difference_s=float(abs(thin[j,3]-nominal[j,3]))))
    csvwrite('data/C_geometry_scenarios.csv',scenarios)
    return dict(statistics=stats,diagnostic_axis=axis,diagnostic_holdout=diag_rows,space_only=[q for q in comparisons if q['first']=='S1T1P1' and q['second']=='S1T1P2'],cross_all_pass=all(q['pass'] for q in comparisons),diagnostic_all_pass=all(q['pass'] for q in diag_rows+axis),same_h_different_dose=equiv,geometry_scenarios=scenarios)

def case_d():
    alias=[]
    for n in [127,254,509]:
        t=(np.arange(n)+.5)/n;est=float(np.mean(1+.8*np.cos(2*np.pi*1016*t)))
        alias.append(dict(nodes=n,estimate=est,exact=1.,error=abs(est-1)))
    # Illustrative near-zero denominator with a stated absolute perturbation.
    rows=[]
    for N,delta in [(1e19,1e15),(1e12,1e12),(0.,1e12)]:
        D=1e18;R=D/N if N>0 else None
        rows.append({'N_net_m2':N,'delta_N_m2':delta,'D_m2':D,'ratio':R,'condition':('undefined' if N<=0 else 'ill_conditioned' if delta/N>=.1 else 'well_conditioned_relative_to_stated_delta'),'ratio_error_bound':((1e14+R*delta)/(N-delta) if N>delta else None)})
    return {'alias':alias,'near_zero_denominator':rows,'interpretation':'127 and 254 agree on the wrong integral. Third nonresonant grid plus exact integral rejects false convergence. This is an analytic sampling counterexample, not a machine rate measurement.'}

def main():
    b=m.Budget();r={'protocol_sha256':hashlib.sha256((ROOT/'verification/PRE_REGISTERED_PROTOCOL.md').read_bytes()).hexdigest(),'runtime':{'python':platform.python_version(),'numpy':np.__version__},'status':'running'}
    dump('data/synthetic_contract.json',m.config())
    try:
        r['A']=case_a(b);r['B']=case_b(b);r['C']=case_c(b);r['D']=case_d()
        r['status']='partial_numerical_acceptance' if not r['C']['cross_all_pass'] or not r['C']['diagnostic_all_pass'] or not all(v['time_integral_pass'] for v in r['A'].values()) else 'limited_synthetic_observation_acceptance'
    except RuntimeError as e:r['status']='budget_stop_partial';r['stop_reason']=str(e)
    r['budget']=b.report();dump('data/results.json',clean(r));print(json.dumps({'status':r['status'],'budget':r['budget']},indent=2))
if __name__=='__main__':main()
