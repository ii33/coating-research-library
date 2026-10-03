"""Bounded high-work validation, disabled by default. No device control or remote I/O.
Runs only the NEW affine y=0 family. Never claims to rerun historical point 2/12.
"""
from pathlib import Path
import argparse,hashlib,itertools,json,math,os,platform,sys,time
from dataclasses import replace
import numpy as np
from event_reference import Scene,evaluate,rate_kernel,shadow_limits,x_at,PARAMETERS
R=Path(__file__).resolve().parents[1]


def read_plan(path):
    d=json.loads(Path(path).read_text());need={'schema_version','execution_mode','execution_authorized','device_label','source_halfwidth_m','source_levels','time_panels','segment_orders','witness_offsets_m','parameter_steps','max_evaluations','max_wall_seconds','time_chunk','acceptance','stop_rule'}
    if set(d)!=need or d['schema_version']!='t02-r3-device-plan-1':raise ValueError('exact plan schema required')
    if not isinstance(d['execution_authorized'],bool):raise ValueError('authorization must be boolean')
    for key in ('source_levels','time_panels','segment_orders'):
        a=d[key]
        if not isinstance(a,list) or len(a)<2 or any(type(x) is not int or x<2 for x in a) or a!=sorted(set(a)):raise ValueError('strictly increasing positive integer levels required')
    if max(d['segment_orders'])>4096 or max(d['source_levels'])>4096:raise ValueError('order cap exceeded')
    if set(d['parameter_steps'])!=set(PARAMETERS):raise ValueError('all parameter step scales required')
    if any(not math.isfinite(x) or x<=0 for x in d['parameter_steps'].values()):raise ValueError('positive finite diagnostic steps required')
    if not d['witness_offsets_m'] or any(not math.isfinite(x) for x in d['witness_offsets_m']):raise ValueError('finite nonempty witness list')
    for k in ('source_halfwidth_m','max_evaluations','max_wall_seconds','time_chunk'):
        if not isinstance(d[k],(float,int)) or not math.isfinite(d[k]) or d[k]<=0:raise ValueError('positive finite resources and source scale')
    if type(d['time_chunk']) is not int or d['time_chunk']>65536:raise ValueError('bounded integer chunk required')
    if d['execution_mode'] not in ('plan_only','explicit_authorized_run'):raise ValueError('invalid mode')
    return d


def estimate(d):
    # Each baseline plus +/- each axis gets fixed-grid values; baseline gets analytic sensitivities.
    scenarios=1+2*len(PARAMETERS);nw=len(d['witness_offsets_m'])
    grid=nw*2*sum(d['source_levels'])*sum(d['time_panels'])*scenarios
    smooth=nw*2*sum(d['source_levels'])*2*sum(d['segment_orders'])
    return {'fixed_grid_kernel_evaluations':grid,'smooth_segment_kernel_evaluations_upper':smooth,'total_kernel_evaluations_upper':grid+smooth,'scenario_count':scenarios,'witness_count':nw,'quadrature_families':['gauss_legendre','midpoint'],'historical_point2_point12_reexecution':False}

class Budget:
    def __init__(self,d):self.limit=d['max_evaluations'];self.wall=d['max_wall_seconds'];self.n=0;self.start=time.monotonic()
    def add(self,n):
        if self.n+n>self.limit or time.monotonic()-self.start>self.wall:raise RuntimeError('resource_budget_stop_unresolved')
        self.n+=n


def fixed_value(sc,s,w,nt,chunk,budget):
    total=0.;dt=(sc.t1-sc.t0)/nt
    for sj,wj in zip(s,w):
        lo,hi,_=shadow_limits(float(sj),sc)
        for start in range(0,nt,chunk):
            ids=np.arange(start,min(start+chunk,nt));budget.add(len(ids))
            tt=sc.t0+(ids+.5)*dt;xx=x_at(tt,sc)
            vis=(xx<lo[0])|(xx>hi[0])
            total+=float(wj)*dt*float(np.sum(rate_kernel(tt,sj,sc)*vis))
    return total


def run(d,out):
    if not d['execution_authorized'] or d['execution_mode']!='explicit_authorized_run' or not d['device_label']:
        raise ValueError('restored device authorization and explicit external run declaration required; frozen default remains plan_only')
    if not out or Path(out).resolve().is_relative_to(R):raise ValueError('fresh output directory outside frozen package required')
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    budget=Budget(d);status='complete_conditional_comparisons';rows=[];comparisons=[]
    input_hash=hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
    (out/'run_plan.json').write_text(json.dumps(d,indent=2)+'\n')
    try:
        for off in d['witness_offsets_m']:
            sc=replace(Scene(),target_shift_m=Scene().target_shift_m+off)
            for family in ('gauss_legendre','midpoint'):
                for ns in d['source_levels']:
                    if family=='gauss_legendre':ss,ww=np.polynomial.legendre.leggauss(ns);ss*=d['source_halfwidth_m'];ww/=2
                    else:ss=((np.arange(ns)+.5)/ns*2-1)*d['source_halfwidth_m'];ww=np.full(ns,1/ns)
                    for order in d['segment_orders']:
                        vals=[];grads=[];states=[]
                        for sj in ss:
                            budget.add(2*order);ev=evaluate(float(sj),sc,order);vals.append(ev['value_s_m2']);states.append(ev['sensitivity_status']);grads.append(ev['gradient'])
                        good=all(x=='differentiable_conditional' for x in states)
                        row={'witness_offset_m':off,'family':family,'source_nodes':ns,'segment_order':order,'value_s_m2':float(ww@vals),'gradient':(ww@np.asarray(grads)).tolist() if good else None,'status':'differentiable_conditional' if good else 'unresolved_node_topology'}
                        rows.append(row)
                    # Always retain event-aware baseline separately from sampled FD diagnostic.
                    for nt in d['time_panels']:
                        fv=fixed_value(sc,ss,ww,nt,d['time_chunk'],budget)
                        fd=[]
                        for name in PARAMETERS:
                            eps=d['parameter_steps'][name]
                            pp=replace(sc,**{name:getattr(sc,name)+eps}).validate();mm=replace(sc,**{name:getattr(sc,name)-eps}).validate()
                            fp=fixed_value(pp,ss,ww,nt,d['time_chunk'],budget);fm=fixed_value(mm,ss,ww,nt,d['time_chunk'],budget)
                            fd.append((fp-fm)/(2*eps))
                        comparisons.append({'witness_offset_m':off,'family':family,'source_nodes':ns,'time_panels':nt,'sampled_value_s_m2':fv,'naive_fd_diagnostic_only':fd,'trusted_gradient':False})
                    # Checkpoint a bounded complete source level, no silent overwrite of frozen data.
                    (out/'checkpoint.json').write_text(json.dumps({'rows':rows,'fixed_comparisons':comparisons},indent=2,allow_nan=False)+'\n')
    except (RuntimeError,ValueError,FloatingPointError) as e:status=str(e)
    # Differences are diagnostics, not certified bounds. Test gradients separately.
    scales=np.array([d['parameter_steps'][name] for name in PARAMETERS])
    def compare_pair(a,b,kind):
        dv=abs(a['value_s_m2']-b['value_s_m2'])
        dg=None if a['gradient'] is None or b['gradient'] is None else float(np.max(np.abs((np.array(a['gradient'])-b['gradient'])*scales)))
        comparisons.append({'kind':kind,'witness_offset_m':a['witness_offset_m'],
            'left':[a['family'],a['source_nodes'],a['segment_order']],
            'right':[b['family'],b['source_nodes'],b['segment_order']],
            'absolute_value_difference_s_m2':dv,'scaled_gradient_difference_s_m2':dg,
            'comparison_within_requested_tolerance':dv<=d['acceptance']['absolute_value_difference_s_m2'] and dg is not None and dg<=d['acceptance']['scaled_gradient_difference_s_m2'],
            'strict_error_bound':False})
    for off in d['witness_offsets_m']:
        lookup={(r['family'],r['source_nodes'],r['segment_order']):r for r in rows if r['witness_offset_m']==off}
        for family in ('gauss_legendre','midpoint'):
            for order in d['segment_orders']:
                for n0,n1 in zip(d['source_levels'][:-1],d['source_levels'][1:]):
                    a=lookup.get((family,n0,order));b=lookup.get((family,n1,order))
                    if a is not None and b is not None:compare_pair(a,b,'source_level')
            for ns in d['source_levels']:
                for o0,o1 in zip(d['segment_orders'][:-1],d['segment_orders'][1:]):
                    a=lookup.get((family,ns,o0));b=lookup.get((family,ns,o1))
                    if a is not None and b is not None:compare_pair(a,b,'smooth_segment_order')
        a=lookup.get(('gauss_legendre',max(d['source_levels']),max(d['segment_orders'])))
        b=lookup.get(('midpoint',max(d['source_levels']),max(d['segment_orders'])))
        if a is not None and b is not None:compare_pair(a,b,'finest_source_family')
    receipt={'status':status,'plan_sha256':input_hash,'input_hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((R/'models').rglob('*.py'))},'device_declaration':d['device_label'],'python':platform.python_version(),'numpy':np.__version__,'kernel_evaluations':budget.n,'wall_seconds':time.monotonic()-budget.start,'new_family_only':True,'point12_still_partial':True,'point2_not_strictly_certified':True,'physical_certification':False,'rows':rows,'comparisons':comparisons}
    (out/'results.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n');return receipt

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--plan',default=str(R/'data/device_validation_plan.json'));ap.add_argument('--run',action='store_true');ap.add_argument('--output');a=ap.parse_args()
    try:
        d=read_plan(a.plan)
        if a.run:r=run(d,a.output);print(json.dumps({k:v for k,v in r.items() if k not in ('rows','comparisons')},indent=2))
        else:print(json.dumps({'status':'plan_only_no_execution','plan':d,'work_estimate':estimate(d),'execution':'not_run'},indent=2))
    except (ValueError,TypeError,KeyError,FileExistsError) as e:print(str(e),file=sys.stderr);sys.exit(2)
