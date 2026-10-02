"""Scalable device validation driver. --plan is default; --run does real work.
No device access, remote submission, or cloud high-cost runs performed by author.
The admitted physical geometry remains the frozen synthetic D model.
"""
from pathlib import Path
import argparse,json,math,time,hashlib,os
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from scipy.integrate import quad
import shadow_integral as s
import legacy_adapter as legacy
from run_control import interval_summary,duration_enclosure
ROOT=Path(__file__).resolve().parents[1]

class Rate:
    """Dimensionless multiplier; geometry support and rate-zero support differ.
    Unknown arbitrary sampled rate cannot receive an accuracy certificate.
    """
    def __init__(self,c):
        self.c=c;self.kind=c['kind'];self.breaks=[];self.frequency=0.
        if self.kind=='constant':
            self.value=float(c.get('value',1.));
            if not math.isfinite(self.value) or self.value<0:raise ValueError('nonnegative finite constant rate required')
            self.strict_positive=self.value>0
        elif self.kind=='sinusoid':
            self.base=float(c.get('baseline',1.));self.amplitude=float(c['amplitude']);self.frequency=float(c['frequency_hz']);self.phase=float(c.get('phase_rad',0.))
            
            if not (all(math.isfinite(v) for v in [self.base,self.amplitude,self.frequency,self.phase]) and self.base>=abs(self.amplitude) and self.frequency>0):raise ValueError('invalid nonnegative analytic sinusoid')
            self.strict_positive=self.base>abs(self.amplitude)
        elif self.kind=='piecewise_linear':
            self.t=np.array(c['times_s'],float);self.v=np.array(c['values'],float)
            
            if not (len(self.t)==len(self.v)>=2 and np.isfinite(self.t).all() and np.isfinite(self.v).all() and np.all(np.diff(self.t)>0) and np.all(self.v>=0) and self.t[0]<=0 and self.t[-1]>=7.3):raise ValueError('invalid piecewise-linear rate contract')
            self.breaks=self.t.tolist();self.strict_positive=bool(np.all(self.v>0))
        else:raise ValueError('unknown rate regularity: refuse automatic accuracy claim')
    def __call__(self,t):
        if self.kind=='constant':return self.value
        if self.kind=='sinusoid':return self.base+self.amplitude*math.cos(2*math.pi*self.frequency*t+self.phase)
        return float(np.interp(t,self.t,self.v))
    def split_points(self,a,b,max_dt):
        if self.frequency:max_dt=min(max_dt,1/(8*self.frequency))
        n=math.ceil((b-a)/max_dt)
        return sorted(set([a,b]+np.linspace(a,b,n+1).tolist()+[t for t in self.breaks if a<t<b]))


def reference(model,control,rate,event_edges):
    a,b=model.c['clock'][model.channel+'_gate_s'];points=sorted(set(rate.split_points(a,b,control['max_time_panel_s'])+[x for x in event_edges if a<x<b]))
    # Integrate separately on panels: arbitrary bandwidth can increase panel
    # count without silently exhausting a global QUADPACK points/limit array.
    total=err=0.;evaluations=0;warnings=[];source_before=model.source_calls
    for left,right in zip(points[:-1],points[1:]):
        epsabs=control['time_epsabs_s_m2']*(right-left)/(b-a)
        r=quad(lambda t:rate(t)*model.source_flux(t,control['source_epsabs_m2'],control['source_epsrel'],control['source_limit']),left,right,epsabs=epsabs,epsrel=control['time_epsrel'],limit=control['time_limit'],full_output=1)
        total+=r[0];err+=r[1];evaluations+=r[2]['neval']
        if len(r)>3:warnings.append(r[3])
    warning_count=len(warnings)+len(model.source_quad_warnings)
    return {'transfer_integral_s_m2':total,'integral_SI':total*model.Qtotal,'outer_abserr_estimate_s_m2':err,'source_max_abserr_estimate_m2':model.max_source_abserr,'outer_evaluations':evaluations,'source_evaluations':model.source_calls-source_before,'initial_time_panels':len(points)-1,'warning_count':warning_count,'warning_first':warnings[0] if warnings else (model.source_quad_warnings[0] if model.source_quad_warnings else None),'accuracy_status':'warning_unresolved' if warning_count else 'estimated_not_certified','physical_certification':False}


def fixed_run(point,cfg,rate_cfg,budget):
    c=legacy.config();nr,na=cfg['radial_order'],cfg['azimuth_nodes'];family=cfg['family'];phase=cfg['phase'];panels=cfg['time_panels']
    sources={ch:legacy.emitter(c,ch,nr,na,family) for ch in ['vapor','ion']};rates={ch:Rate(rate_cfg[ch]) for ch in sources};mask=legacy.plates(c,'both')
    # Constant/piecewise/high-frequency controls use a union partition shared
    # across channels. It includes all gates, knots and bandwidth constraints.
    dt=7.3/panels;edges=sorted(set([0.,.55,6.55,7.3]+sum([rr.split_points(0,7.3,dt) for rr in rates.values()],[])))
    left=np.array(edges[:-1]);w=np.diff(edges);ts=left+phase*w;acc=np.zeros(3)
    for start in range(0,len(ts),cfg.get('time_chunk',16)):
        t=ts[start:start+cfg.get('time_chunk',16)];ww=w[start:start+len(t)];X,n=legacy.pose(c,t,[point]);fields={}
        for ch,src in sources.items():
            budget.add('ray_evaluations',len(t)*nr*na)
            total=c[ch]['total_atoms_s' if ch=='vapor' else 'total_ions_s'];gate=c['clock'][ch+'_gate_s']
            fields[ch]=total*legacy.t02.transfer_kernel(X,n,src,mask)[:,0]*np.array([rates[ch](float(z)) for z in t])*((t>=gate[0])&(t<gate[1]))
        acc+=np.array([ww@fields['vapor'],ww@fields['ion'],ww@((fields['ion']>0)&(fields['vapor']==0))])
    return {'N_atoms_m2':acc[0],'D_ions_m2':acc[1],'ion_only_s':acc[2],'time_nodes':len(ts),'source_nodes_each':nr*na,'warning':'legacy fixed source/ray kernel is a comparison only; not corrected or certified'}


def assess(out,config):
    levels=list(config['reference_levels']);tol=config['acceptance'];checks={};rows=[]
    for ch in ['vapor','ion']:
        vals=[out['reference'][ch+'_'+name] for name in levels];r=vals[-1];diff=max(abs(v['transfer_integral_s_m2']-r['transfer_integral_s_m2']) for v in vals[:-1])
        scale=abs(r['transfer_integral_s_m2']);threshold=max(tol['reference_disagreement_absolute_s_m2'],tol['reference_disagreement_relative']*scale)
        checks[ch]={'absolute_reference_spread_s_m2':diff,'relative_reference_spread':diff/scale if scale>0 else None,'threshold_s_m2':threshold,'agreement':len(vals)>=2 and diff<=threshold and all(v['warning_count']==0 for v in vals),'not_a_strict_error_bound':True}
    dur=out['duration'];dur_ok='width_ms' in dur and dur['width_ms']<=tol['event_width_ms']
    for name,v in out['fixed'].items():
        row={'method':name}
        for ch,key in [('vapor','N_atoms_m2'),('ion','D_ions_m2')]:
            ref=out['reference'][ch+'_'+levels[-1]]['integral_SI'];err=abs(v[key]-ref)
            row[key+'_absolute_difference']=err;row[key+'_relative_difference']=err/abs(ref) if ref else None
        row['duration_absolute_difference_ms']=abs(v['ion_only_s']-dur['midpoint_s'])*1000 if 'midpoint_s' in dur else None;rows.append(row)
    return {'reference_checks':checks,'duration_event_width_ok_conditional':dur_ok,'reference_agreement_estimated':all(v['agreement'] for v in checks.values()) and dur_ok,'fixed_comparisons':rows,'historical_global_status':'partial_unchanged','strict_certificate':False,'physical_certification':False}


def job(j,point,config):
    b=s.Budget(config['per_point_work_limit'],config['per_point_wall_seconds']);out={'point_id':j,'point_local_m':list(point),'support':{},'reference':{},'fixed':{},'status':'running'}
    try:
        rates={ch:Rate(config['rates'][ch]) for ch in ['vapor','ion']}
        for ch in ['vapor','ion']:
            model=s.Model(point,ch,b);sup=interval_summary(model.support_intervals(*model.c['clock'][ch+'_gate_s'],leaf_width=config['event_leaf_width_s']));out['support'][ch]=sup
            edges=[v for ab in sup['unknown'] for v in ab]
            for name,control in config['reference_levels'].items():out['reference'][ch+'_'+name]=reference(s.Model(point,ch,b),control,rates[ch],edges)
        if all(r.strict_positive for r in rates.values()):out['duration']=duration_enclosure(out['support']['vapor'],out['support']['ion'])
        else:out['duration']={'status':'unresolved_rate_zero_support_requires_additional_event_logic'}
        for name,cfg in config['fixed_comparisons'].items():out['fixed'][name]=fixed_run(point,cfg,config['rates'],b)
        out['assessment']=assess(out,config)
        out['status']='completed_estimates_only' if out['assessment']['reference_agreement_estimated'] else 'completed_with_unresolved_reference'
    except (RuntimeError,ValueError,AssertionError) as e:out['status']='partial_stopped';out['reason']=str(e)
    out['budget']=b.report();return out


def select_points(config):
    if config['point_set']=='selected':return [(i,legacy.diagnostic_points()[i].tolist()) for i in [2,12]]
    if config['point_set']=='diagnostic_13':return list(enumerate(legacy.diagnostic_points().tolist()))
    if config['point_set']=='area_236':return list(enumerate(legacy.grid(2)[0].tolist()))
    raise ValueError('unknown point set')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',default=str(ROOT/'verification/device_validation_plan.json'));ap.add_argument('--run',action='store_true');ap.add_argument('--output',default=str(ROOT/'device_results'));ap.add_argument('--workers',type=int,default=1);args=ap.parse_args()
    config=json.loads(Path(args.config).read_text());points=select_points(config)
    if args.workers<1:raise ValueError('positive worker count required')
    fixed_rays=sum(2*v['radial_order']*v['azimuth_nodes']*(v['time_panels']+3) for v in config['fixed_comparisons'].values())*len(points)
    plan={'status':'not_run_awaiting_device','points':len(points),'reference_jobs':len(points)*2*len(config['reference_levels']),'fixed_ray_nominal_estimate':fixed_rays,'work_unit_hard_cap':len(points)*config['per_point_work_limit'],'wall_hard_cap_serial_s':len(points)*config['per_point_wall_seconds'],'workers':args.workers,'memory':'streamed per-point/time chunk; measure peak RSS on device, not benchmarked','high_frequency_rates_can_increase_panels':True,'physical_certification':False}
    print(json.dumps(plan,indent=2))
    if not args.run:return
    dest=Path(args.output);dest.mkdir(parents=True,exist_ok=True)
    digest=hashlib.sha256(Path(args.config).read_bytes()).hexdigest()
    def save(result):
        result['configuration_sha256']=digest;p=dest/f"point_{result['point_id']:04}.json";tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');tmp.replace(p);print(result['point_id'],result['status'],flush=True)
    if args.workers==1:
        for j,p in points:save(job(j,p,config))
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            futures=[ex.submit(job,j,p,config) for j,p in points]
            for future in as_completed(futures):save(future.result())
    (dest/'run_manifest.json').write_text(json.dumps({'config_sha256':digest,'plan':plan,'status':'execution_finished_check_each_point_before_acceptance'},indent=2)+'\n')
if __name__=='__main__':main()
