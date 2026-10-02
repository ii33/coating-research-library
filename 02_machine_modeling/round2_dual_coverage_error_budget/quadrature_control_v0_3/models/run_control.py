"""Reproduce bounded v0.3 evidence; default stdout only, --record writes here.
Frozen originals never written. Suite is finite; no automatic grid escalation.
"""
from pathlib import Path
import sys,json,csv,time,hashlib,platform,argparse,resource,math
import numpy as np
import scipy
from scipy.integrate import quad
import shadow_integral as s
import legacy_adapter as legacy
from frozen import robust_mask_v02 as robust
ROOT=Path(__file__).resolve().parents[1]

def merge(intervals):
    out=[]
    for a,b in sorted(intervals):
        if out and a<=out[-1][1]+1e-14:out[-1][1]=max(b,out[-1][1])
        else:out.append([a,b])
    return out

def interval_summary(data):
    return {**{k:v for k,v in data.items() if k not in ['covered','visible','unknown']},**{k:merge(data[k]) for k in ['covered','visible','unknown']}}

def duration_enclosure(vap,ion):
    vv=[(a,b,'visible') for a,b in vap['visible']]+[(a,b,'covered') for a,b in vap['covered']]+[(a,b,'unknown') for a,b in vap['unknown']]+[(0.,.55,'covered'),(6.55,7.3,'covered')]
    ii=[(a,b,key) for key in ['visible','covered','unknown'] for a,b in ion[key]]
    edges=sorted(set([a for a,b,key in vv+ii]+[b for a,b,key in vv+ii]));lo=hi=0.
    for a,b in zip(edges[:-1],edges[1:]):
        t=(a+b)/2;v=next(key for l,h,key in vv if l<=t<=h);i=next(key for l,h,key in ii if l<=t<=h)
        if i=='visible' and v=='covered':lo+=b-a
        if i!='covered' and v!='visible':hi+=b-a
    return {'lower_s':lo,'upper_s':hi,'midpoint_s':(lo+hi)/2,'width_ms':(hi-lo)*1000,'status':'conditional_lipschitz_enclosure_not_validated_float'}

def discrete(point,panels,family='gauss',phase=.5,budget=None):
    c=legacy.config();nr,na=(5,23) if family=='gauss' else (7,29)
    sv=legacy.emitter(c,'vapor',nr,na,family);si=legacy.emitter(c,'ion',nr,na,family);masks=legacy.plates(c,'both')
    ts,ws=legacy.t02.time_quadrature(0,7.3,panels,1,[.55,6.55])
    ts=ts+(phase-.5)*ws;acc=np.zeros(4)
    for k in range(0,len(ts),32):
        t=ts[k:k+32];w=ws[k:k+32];x,n=legacy.pose(c,t,[point])
        budget.add('ray_evaluations',len(t)*nr*na*2)
        v=c['vapor']['total_atoms_s']*legacy.t02.transfer_kernel(x,n,sv,masks)[:,0]*((t>=.55)&(t<6.55))
        i=c['ion']['total_ions_s']*legacy.t02.transfer_kernel(x,n,si,masks)[:,0]
        acc+=np.array([w@v,w@i,w@i*100*legacy.E_CHARGE,w@((i>0)&(v==0))])
    return acc,dict(time_nodes=len(ts),source_nodes_each=nr*na,source_family=family,phase=phase,panels=panels,ray_evaluations=len(ts)*nr*na*2)

def case_a(b):
    loc=json.loads((ROOT/'data/localization.json').read_text());ids=sorted(set([loc['selection_integral_point'],loc['selection_duration_point']]))
    out={};rows=[];cost=[]
    for j in ids:
        point=legacy.diagnostic_points()[j];support={};ref={}
        for channel in ['vapor','ion']:
            model=s.Model(point,channel,b);gate=model.c['clock'][channel+'_gate_s']
            ss=interval_summary(model.support_intervals(*gate));support[channel]=ss
            events=[v for window in ss['unknown'] for v in window]
            for tight in [False,True]:
                before=b.report();model=s.Model(point,channel,b)
                r=model.integrate(tight,events);ref[channel+('_tight' if tight else '_base')]=r
                after=b.report();cost.append(dict(case='A',point=j,method='projected_analytic_y_'+('tight' if tight else 'base'),channel=channel,work_units=after['total_work_units']-before['total_work_units'],wall_seconds=after['wall_seconds']-before['wall_seconds'],value=r['integral_SI'],outer_error_estimate_SI=r['outer_abserr_estimate_s_m2']*model.Qtotal))
                print(j,channel,'tight' if tight else 'base',r,flush=True)
        dur=duration_enclosure(support['vapor'],support['ion'])
        for panels,family,phase in [(509,'gauss',.5),(1531,'gauss',.5),(1531,'equal_area',.5),(2017,'gauss',.5),(1531,'gauss',.271828)]:
            before=b.report()
            if panels==1531 and phase==.5:
                a=np.array(loc['s2t2' if family=='gauss' else 'holdout'][j]);meta={'time_nodes':1533,'source_nodes_each':115 if family=='gauss' else 203,'source_family':family,'phase':phase,'panels':panels,'ray_evaluations':0,'evidence':'reused frozen/localization result'}
            else:a,meta=discrete(point,panels,family,phase,b)
            after=b.report();method=f'{family}_{panels}_phase_{phase}'
            for ch,idx in [('vapor',0),('ion',1)]:
                truth=ref[ch+'_tight']['integral_SI'];err=abs(a[idx]-truth)
                rows.append(dict(point=j,method=method,quantity='N_atoms_m2' if idx==0 else 'D_ions_m2',estimate=a[idx],reference_estimate=truth,absolute_difference_SI=err,point_relative_difference=err/abs(truth),frozen_mean_normalized_difference=err/loc['frozen_mean_scales'][idx],duration_difference_ms='',reference_status='estimated_low_dimensional'))
            rows.append(dict(point=j,method=method,quantity='ion_only_s',estimate=a[3],reference_estimate=dur['midpoint_s'],absolute_difference_SI=abs(a[3]-dur['midpoint_s']),point_relative_difference='',frozen_mean_normalized_difference='',duration_difference_ms=1000*abs(a[3]-dur['midpoint_s']),reference_status=dur['status']))
            cost.append(dict(case='A',point=j,method=method,channel='both',work_units=after['total_work_units']-before['total_work_units'],wall_seconds=after['wall_seconds']-before['wall_seconds'],value='',outer_error_estimate_SI=''))
        out[str(j)]={'point_local_m':point.tolist(),'reference':ref,'support':support,'duration':dur,'reference_base_tight_relative':{ch:abs(ref[ch+'_base']['integral_SI']-ref[ch+'_tight']['integral_SI'])/abs(ref[ch+'_tight']['integral_SI']) for ch in ['vapor','ion']}}
    return out,rows,cost

def case_b(b):
    rows=[]
    for n,phase in [(127,.5),(254,.5),(509,.5),(127,.271828),(254,.271828)]:
        t=(np.arange(n)+phase)/n;val=float(np.mean(1+.8*np.cos(2*np.pi*1016*t)));b.add('ray_evaluations',n)
        rows.append(dict(method='uniform_phase',nodes=n,phase=phase,estimate=val,exact=1.,absolute_error=abs(val-1),smooth_midpoint_bound=.8*(2*math.pi*1016)**2/(24*n*n) if phase==.5 else None))
    calls=[0]
    def f(t):calls[0]+=1;return 1+.8*math.cos(2*math.pi*1016*t)
    q=quad(f,0,1,epsabs=1e-10,epsrel=1e-10,limit=100,full_output=1);b.add('ray_evaluations',calls[0])
    rows.append(dict(method='generic_adaptive_quad',nodes=calls[0],phase=None,estimate=q[0],exact=1.,absolute_error=abs(q[0]-1),smooth_midpoint_bound=None,reported_error_estimate=q[1],warning=q[3] if len(q)>3 else None))
    return {'rows':rows,'frequency_hz':1016,'amplitude':.8,'known_period_exact_integral':1.,'midpoint_nodes_sufficient_by_second_derivative_for_0_003':math.ceil(math.sqrt(.8*(2*math.pi*1016)**2/(24*.003))),'unknown_rate_bandwidth_status':'unresolved_no_sampling_certificate','note':'generic adaptive error estimate is not a bound; analytic exact integral supplies independent truth'}

def case_c(b):
    a=(.1+4e-15,0.,-.1);x=(.1-4e-15,0.,.1);Q=np.eye(3);mask=robust.RectangleMask((0.,0.,0.),Q.tolist(),.1,.2,.04)
    old=legacy.t02.RectangleMask(np.zeros(3),Q,.1,.2,.04)
    nominal=mask.classify(a,x);uncertain=mask.classify(a,x,local_margin_m=1e-14);b.add('oracle_evaluations',2)
    assert not bool(old.blocked(a,x)) and nominal.verdict is robust.Verdict.BLOCKED
    weight=1e-12;T=.2;kernel=1/(math.pi*.2**2);contribution=weight*T*kernel
    lo,hi=robust.transmitted_sum_interval([contribution],[uncertain])
    return {'encoded_source':a,'encoded_target':x,'legacy_blocked':False,'v02_nominal':nominal.verdict.value,'with_local_margin_1e_14':uncertain.verdict.value,'single_node_fraction':weight,'constant_interval_s':T,'total_rate_atoms_s':1.,'kernel_m_inverse2':kernel,'old_leaked_integral_atoms_m2':contribution,'nominal_transmitted_integral_atoms_m2':0.,'uncertain_discrete_integral_interval_atoms_m2':[lo,hi],'old_ion_only_s':0.,'nominal_ion_only_s':T,'uncertain_ion_only_interval_s':[0.,T],'status':'finite_discrete_toy_only_not_original_full_map_error','bound':'For nonnegative contributions c_j, changed visibility gives |delta I| <= sum_changed c_j. Duration has no bound proportional to flux error without a positive-threshold/margin assumption.'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--record',action='store_true');args=ap.parse_args()
    b=s.Budget();r={'protocol_sha256':hashlib.sha256((ROOT/'verification/PRE_REGISTERED_PROTOCOL.md').read_bytes()).hexdigest(),'runtime':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},'status':'in_progress'}
    try:
        r['A'],rows,cost=case_a(b);r['B']=case_b(b);r['C']=case_c(b);r['status']='bounded_reference_estimates_partial_global'
    except RuntimeError as e:
        r['status']='budget_stop_partial';r['stop_reason']=str(e);rows=[];cost=[]
    r['budget']=b.report();r['peak_rss_KiB']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if args.record:
        (ROOT/'data/results.json').write_text(json.dumps(r,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
        for name,rr in [('error_comparisons.csv',rows),('work_comparisons.csv',cost)]:
            if rr:
                with (ROOT/'data'/name).open('w',newline='') as f:
                    w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
    print(json.dumps({'status':r['status'],'budget':r['budget']},indent=2))
if __name__=='__main__':main()
