"""Reproduce the bounded study. Writes only data/ and verification/ in this increment."""
from pathlib import Path
from copy import deepcopy
import csv, hashlib, json, time, platform
import numpy as np
import dual_coverage as m

ROOT=m.ROOT

def save_json(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def summarize(config,values,weights):
    return {case:{key:m.statistics(val,weights) for key,val in m.output_values(config,arr).items()} for case,arr in values.items()}

def compare_points(a,b,weights):
    out={}
    for case in a:
        aa,bb=a[case],b[case];vals=[]
        for j,name in enumerate(m.METRICS):
            scale=float(weights@bb[:,j]);delta=np.abs(aa[:,j]-bb[:,j]);worst=int(np.argmax(delta))
            if j==3:
                vals.append({'quantity':name,'max_abs_error_s':float(delta[worst]),'worst_point_index':worst,'pass':bool(delta[worst]<=.003)})
            else:
                mx=float(delta[worst]/scale) if scale>0 else None
                av=float(abs(weights@(aa[:,j]-bb[:,j]))/scale) if scale>0 else None
                vals.append({'quantity':name,'max_error_over_reference_mean':mx,'mean_error_over_reference_mean':av,'worst_point_index':worst,'pass':bool(mx is not None and mx<=.003 and av<=.001)})
        out[case]=vals
    return out

def pass_point(comparison): return all(v['pass'] for values in comparison.values() for v in values)

def compare_space(a,b):
    results=[]
    for case in a:
        for key in a[case]:
            aa,bb=a[case][key],b[case][key]
            mean=abs(aa['mean']-bb['mean'])/abs(bb['mean']) if bb['mean'] else abs(aa['mean']-bb['mean'])
            cv=abs(aa['cv']-bb['cv']) if aa['cv'] is not None and bb['cv'] is not None else None
            pv=abs(aa['sample_pv']-bb['sample_pv']) if aa['sample_pv'] is not None and bb['sample_pv'] is not None else None
            results.append({'case':case,'quantity':key,'relative_mean_delta':mean,'absolute_cv_delta':cv,'absolute_sample_pv_delta':pv,'pass':mean<=.003 and cv is not None and cv<=.003 and pv is not None and pv<=.005})
    return results

def write_map(top,points,weights,values,config):
    path=ROOT/'data'/f'map_{top}.csv';cols=['topology','case','point_index','u_m','v_m','area_weight']+list(m.output_values(config,next(iter(values.values()))))
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,cols);writer.writeheader()
        for case,arr in values.items():
            vv=m.output_values(config,arr)
            for j,p in enumerate(points):
                row=dict(topology=top,case=case,point_index=j,u_m=p[0],v_m=p[1],area_weight=weights[j])
                row.update({key:float(v[j]) if np.isfinite(v[j]) else '' for key,v in vv.items()});writer.writerow(row)

def main():
    start=time.monotonic();cfg=m.load_config();summary={};num={};counts=[];space={};main_results={}
    pts,weights=m.diagnostic_grid(cfg['geometry']['substrate_radius_m'])
    save_json(ROOT/'data/diagnostic_points.json',{'points_local_m':pts.tolist(),'note':'21 equal-weight diagnostic points, NOT disk-area quadrature'})
    for top in cfg['topologies']:
        print('Numerical controls',top,flush=True)
        ei=m.EventIntegrator(cfg,top,8192);r8=ei.integrate(pts,order=8);counts.append(ei.report())
        ei=m.EventIntegrator(cfg,top,8192);ref=ei.integrate(pts,order=16);counts.append(ei.report())
        ei=m.EventIntegrator(cfg,top,16384);rscan=ei.integrate(pts,order=16);counts.append(ei.report())
        order_cmp=compare_points(r8,ref,weights);scan_cmp=compare_points(ref,rscan,weights)
        midpoint_records=[]
        for steps in [2048,8192,32771,131071]:
            candidate=m.midpoint(cfg,top,pts,steps)
            comp=compare_points(candidate,rscan,weights)
            midpoint_records.append({'steps':steps,'comparison':comp,'pass':pass_point(comp)})
            counts.append({'midpoint_channel_flux_evaluations':steps*len(pts)*2*len(cfg['cases'])})
            if steps>=8192 and pass_point(comp): break
        num[top]={'order8_vs16':order_cmp,'scan8192_vs16384':scan_cmp,'midpoint':midpoint_records,'time_status':'converged' if pass_point(order_cmp) and pass_point(scan_cmp) and midpoint_records[-1]['pass'] else 'not_converged'}
        oldstats=None;changes=[]
        for nr,na,ne in [(12,48,72),(18,73,145),(24,97,289)]:
            pp,ww=m.disk_grid(cfg['geometry']['substrate_radius_m'],nr,na,ne)
            print('Spatial grid',top,nr,na,ne,flush=True)
            ei=m.EventIntegrator(cfg,top,8192);val=ei.integrate(pp,order=16);counts.append(ei.report())
            stats=summarize(cfg,val,ww)
            if oldstats is not None:
                comp=compare_space(oldstats,stats);changes.append({'from_grid':oldgrid,'to_grid':[nr,na,ne],'comparison':comp,'pass':all(q['pass'] for q in comp)})
                if changes[-1]['pass']: break
            oldstats=stats;oldgrid=[nr,na,ne]
        space[top]={'selected_grid':[nr,na,ne],'total_points':len(pp),'area_points':nr*na,'changes':changes,'status':'converged_on_sampled_metrics' if changes[-1]['pass'] else 'not_converged_within_budget','continuous_extrema':'not certified'}
        summary[top]=stats;main_results[top]=(pp,ww,val);write_map(top,pp,ww,val,cfg)
        save_json(ROOT/'data/main_summary.json',summary)
        save_json(ROOT/'verification/numerical_checks.json',{'time':num,'space':space,'counts':counts})
    # One factor at a time, D only: scope set before viewing results.
    sensitivity={}
    sp,sw=m.disk_grid(cfg['geometry']['substrate_radius_m'],12,48,72)
    for name in ['short_layer_1p3s','carrier_phase_plus_pi_over_3','ion_sigma_0p18m']:
        cc=deepcopy(cfg)
        if name.startswith('short'): cc['clock']['layer_end_s']=1.3
        elif name.startswith('carrier'): cc['geometry']['carrier_phase_rad']=np.pi/3
        else: cc['ion']['sigma_m']=.18
        print('Single factor',name,flush=True)
        ei=m.EventIntegrator(cc,'D',8192);val=ei.integrate(sp,order=16);counts.append(ei.report())
        sensitivity[name]={'topology':'D','grid':[12,48,72],'results':summarize(cc,val,sw),'status':'fixed-grid sensitivity only; separate spatial convergence not performed'}
    # Analytic logical counterexample: same ion field and motion, vapor field only changes.
    pp,ww,mainD=main_results['D']
    ei=m.EventIntegrator(cfg,'D',8192);uniform=ei.integrate(pp,order=16,cases=['none'],uniform_vapor=True);counts.append(ei.report())
    ub=summarize(cfg,uniform,ww)['none'];db=summary['D']['none']
    counter={'change':'point cosine vapor -> uniform parallel vapor only; no plates; identical ion beam, motion, finite layer and gates','point_cosine':db,'uniform_vapor':ub,'exact_uniform_h_nm':cfg['vapor']['reference_atom_flux_m2_s']*6/cfg['vapor']['net_atomic_density_m3']*1e9,'max_ion_integral_difference':float(np.max(np.abs(uniform['none'][:,1]-mainD['none'][:,1]))),'logical_test_pass':ub['h_nm']['cv']<1e-12 and ub['ion_fluence_m2']['cv']>1e-3 and ub['h_nm']['cv']<db['h_nm']['cv'],'interpretation':'source-field counterexample, not a topology superiority claim or a correction-plate optimization'}
    # Fixed diagnostics are not substrate-average readings.
    probes={}
    tt=np.linspace(.7,6.4,7)
    for pr in cfg['diagnostics']:
        x=np.broadcast_to(np.array(pr['position_L_m']),(len(tt),1,3));n=np.broadcast_to(np.array(pr['normal_L']),(len(tt),1,3))
        probes[pr['id']]={}
        for case in cfg['cases']:
            gv,gi,_=m.flux_at(cfg,tt,x,n,case)
            probes[pr['id']][case]={'time_s':tt.tolist(),'net_atom_flux_m2_s':gv[:,0].tolist(),'positive_ion_flux_per_probe_area_m2_s':gi[:,0].tolist(),'scope':pr['reads']}
    closures={}
    for top in cfg['topologies']:
        rr=m.rates(cfg,top);closures[top]={'rps':{k:str(v) for k,v in rr.items()},'marked_workpiece_pose_period_s':str(m.rational_period([rr['carrier'],rr['output']])),'modeled_geared_axes_period_s':str(m.rational_period(rr.values())),'does_not_claim':'unmodeled support idlers, motor rotors, source modulation or material state closure'}
    total=sum(r.get('pose_scan_evaluations',0)+r.get('channel_flux_evaluations',0)+r.get('midpoint_channel_flux_evaluations',0) for r in counts)
    limits={'budget_work_units':150000000,'actual_counted_work_units':total,'definition':'one point-time pose scan plus one flux evaluation per channel; bisection scalar trig evaluations are separately counted as subdivisions, not hidden large arrays','within_budget':total<=150000000,'elapsed_s':time.monotonic()-start,'numpy':np.__version__,'python':platform.python_version(),'platform':platform.platform(),'time_all_pass':all(x['time_status']=='converged' for x in num.values()),'space_all_pass':all(x['status']=='converged_on_sampled_metrics' for x in space.values()),'source_figure_gate':'C/I unsupported, see sources/access_status.json'}
    area=np.pi*cfg['geometry']['substrate_radius_m']**2
    totals={top:{case:{'area_m2':area,'net_atoms_total':st['net_atoms_m2']['mean']*area,'positive_ions_total':st['ion_fluence_m2']['mean']*area,'incident_ion_energy_total_J':st['incident_energy_J_m2']['mean']*area,'area_global_ion_to_net_atom_ratio':st['ion_fluence_m2']['mean']/st['net_atoms_m2']['mean'],'area_mean_of_local_integral_ratios':st['ion_to_net_atom_ratio']['mean']} for case,st in cases.items()} for top,cases in summary.items()}
    save_json(ROOT/'data/area_totals.json',totals)
    save_json(ROOT/'data/closure_periods.json',closures)
    save_json(ROOT/'data/single_factor_comparisons.json',sensitivity)
    save_json(ROOT/'data/uniform_thickness_counterexample.json',counter)
    save_json(ROOT/'data/diagnostic_readings.json',probes)
    save_json(ROOT/'verification/numerical_checks.json',{'time':num,'space':space,'counts':counts,'run':limits})
    print(json.dumps(limits,ensure_ascii=False,indent=2),flush=True)
    print('Counterexample pass:',counter['logical_test_pass'],flush=True)

if __name__=='__main__': main()
