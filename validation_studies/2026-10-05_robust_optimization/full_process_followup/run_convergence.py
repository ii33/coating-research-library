"""Measured-cost complete-process convergence, before any fresh optimization."""
from pathlib import Path
import json
import math
import time

import numpy as np
from run_full_process import (HERE,load_inputs,run_one,save_result,CoreObserver,
    old_identity,source_hashes,clipped_cell_weights,roi_weights)


def load_result(name):
    row=json.loads((HERE/(name+'.json')).read_text())
    with np.load(HERE/(name+'.npz')) as f:
        row.update({k:f[k].copy() for k in ('field_nm','x','y')})
    return row


def norm_field(row):
    return row['field_nm']/row['metrics']['area_mean_nm']


def compare(a,b):
    # Different grids are evaluated on their common physical sampling points.
    # The global area-CV check is separate, with coverage disclosed.
    if abs(float(a['x'][-1])-float(b['x'][-1]))>1e-8:
        raise ValueError('Comparison grid extents differ')
    common_count=math.gcd(len(a['x'])-1,len(b['x'])-1)+1
    if common_count<3:raise ValueError('Too few exact common nodes; interpolation would need a separate contract')
    axis=np.linspace(float(a['x'][0]),float(a['x'][-1]),common_count)
    def subset(row):
        ids=[int(np.argmin(abs(row['x']-x))) for x in axis]
        if any(abs(row['x'][i]-x)>1e-8 for i,x in zip(ids,axis)):
            raise ValueError('Non-nested comparison grids')
        return norm_field(row)[np.ix_(ids,ids)]
    x,y=subset(a),subset(b);valid=np.isfinite(x)&np.isfinite(y)
    w,coverage=clipped_cell_weights(axis,valid,float(np.max(axis)))
    iw,ic=roi_weights(axis,valid,.9*float(np.max(axis)))
    d=np.where(valid,x-y,0.)
    # Extra diagnostic: normalize both maps on the identical common inset
    # sample domain. The original inset RMS below retains each full-domain
    # mean, so across grids it is not an isolated interior discretization error.
    roi_mean_x=float(np.sum(iw*np.where(valid,x,0.)))
    roi_mean_y=float(np.sum(iw*np.where(valid,y,0.)))
    common_roi_delta=np.where(valid,x/roi_mean_x-y/roi_mean_y,0.)
    return {'normalized_field_rms_pp':math.sqrt(float(np.sum(w*d*d)))*100.,
        'interior135_field_rms_pp':math.sqrt(float(np.sum(iw*d*d)))*100.,
        'common_roi_normalized_field_rms_pp':math.sqrt(float(np.sum(iw*common_roi_delta*common_roi_delta)))*100.,
        'inset_original_rms_includes_full_domain_normalization':True,
        'cv_change_pp':abs(a['metrics']['cv_percent']-b['metrics']['cv_percent']),
        'interior135_cv_change_pp':abs(a['metrics']['interior135_cv_percent']-b['metrics']['interior135_cv_percent']),
        'common_grid':len(axis),'common_represented_area_fraction':coverage,
        'common_interior135_coverage':ic}


def passes(row,tolerance):
    return all(row[k]<tolerance for k in ('normalized_field_rms_pp','interior135_field_rms_pp','cv_change_pp','interior135_cv_change_pp'))


def serial(row):return {k:v for k,v in row.items() if k not in ('field_nm','x','y')}


def main():
    cfg=json.loads((HERE/'config.json').read_text());snapshot,runtime,native=load_inputs(cfg)
    identity=old_identity();sources=source_hashes();pilot=load_result('pilot_direct_005_g21')
    observer=CoreObserver(cfg['main_actual_core_call_cap']);start=time.perf_counter();results={};checks={};decisions=[]
    cost=json.loads((HERE/'pilot_costs.json').read_text())['complete_pilot_wall_s']
    def remaining():return cfg['main_soft_wall_allowance_s']-(time.perf_counter()-start)
    def run(name,dt,grid,mode,probe=False,order=None):
        if name in results:return results[name]
        # Admission is a planning guard. Kernel cancellation preserves a clear
        # incomplete result; it never quietly returns a shorter physical recipe.
        estimate=cost*(.05/dt)*(grid/21)**2 if mode=='direct' else max(2.,cost*.04*(.05/dt)*(grid/21)**2*((order or 4)/4)**2)
        if estimate>remaining():raise RuntimeError(f'Whole-run measured-cost guard blocks {name}: estimate{estimate:.1f}s,remaining{remaining():.1f}s')
        row=run_one(runtime,native,dt,grid,mode,observer,remaining(),probe,order)
        save_result(name,row);results[name]=row
        print(json.dumps({'completed':name,'full_duration_s':row['total_duration_s'],'wall_s':row['wall_s'],
            'actual_core_calls':row['core_calls'],'cv_percent':row['metrics']['cv_percent'],
            'actual_layer_dt_s':row['timing']['step_time_step_s']}),flush=True)
        return row
    try:
        baseline=run('direct_0025_g21',.025,21,'direct')
        probe=run('direct_0025_g21_probe',.025,21,'direct',True)
        effect=compare(baseline,probe)
        tolerance=cfg['convergence']['effect_fraction']*effect['normalized_field_rms_pp']
        checks['effect_probe']=effect;checks['tolerance_pp']=tolerance
        checks['time_direct_005_to_0025']=compare(pilot,baseline)
        p005=run('periodic_005_g21',.05,21,'finite_periodic')
        p025=run('periodic_0025_g21',.025,21,'finite_periodic')
        pp025=run('periodic_0025_g21_probe',.025,21,'finite_periodic',True)
        checks['periodic_vs_direct_005']=compare(pilot,p005)
        checks['periodic_vs_direct_0025']=compare(baseline,p025)
        checks['periodic_vs_direct_0025_probe']=compare(probe,pp025)
        verified_dt=.025
        initial_baseline_time_ok=passes(checks['time_direct_005_to_0025'],tolerance)
        # The probe defines the tolerance, so its own refinement cannot be
        # inferred from a baseline-only pass. Without an extra .05 probe run,
        # the complete .025→.0125 pair is needed to check both configurations.
        time_ok=False
        periodic_ok=passes(checks['periodic_vs_direct_0025'],tolerance) and passes(checks['periodic_vs_direct_0025_probe'],tolerance)
        if not(initial_baseline_time_ok and periodic_ok and time_ok):
            decisions.append({'action':'Refine complete direct time to.0125s','reason':'Time or periodic agreement exceeds effect-relative tolerance','not_an_optimizer':True})
            finer=run('direct_00125_g21',.0125,21,'direct')
            fprobe=run('direct_00125_g21_probe',.0125,21,'direct',True)
            pfine=run('periodic_00125_g21',.0125,21,'finite_periodic')
            pfprobe=run('periodic_00125_g21_probe',.0125,21,'finite_periodic',True)
            checks['time_direct_0025_to_00125']=compare(baseline,finer)
            checks['time_direct_0025_to_00125_probe']=compare(probe,fprobe)
            checks['periodic_vs_direct_00125']=compare(finer,pfine)
            checks['periodic_vs_direct_00125_probe']=compare(fprobe,pfprobe)
            time_ok=passes(checks['time_direct_0025_to_00125'],tolerance) and passes(checks['time_direct_0025_to_00125_probe'],tolerance)
            periodic_ok=passes(checks['periodic_vs_direct_00125'],tolerance) and passes(checks['periodic_vs_direct_00125_probe'],tolerance)
            verified_dt=.0125;p025=pfine;pp025=pfprobe
        gates={'time_convergence_screen':time_ok,'finite_periodic_direct_agreement_screen':periodic_ok,
               'grid_convergence_screen':False,'source_convergence_screen':False,
               'combined_resolution_direct_agreement_screen':False,
               'cv_objective_gap_resolved':False,
               'fresh_optimization_allowed':False,'engineering_ranking_allowed':False}
        if periodic_ok:
            grid_results={False:[p025],True:[pp025]}
            for grid in cfg['grid_sizes'][1:]:
                for isprobe in (False,True):
                    r=run(f'periodic_g{grid}_{verified_dt}_{int(isprobe)}',verified_dt,grid,'finite_periodic',isprobe)
                    grid_results[isprobe].append(r)
            grid_checks=[]
            for isprobe,rows in grid_results.items():
                for a,b in zip(rows[:-1],rows[1:]):grid_checks.append({'probe':isprobe,'grids':[a['grid'],b['grid']],**compare(a,b)})
            checks['grid']=grid_checks;gates['grid_convergence_screen']=all(passes(c,tolerance) for c in grid_checks)
            source_results={False:[],True:[]}
            for order in cfg['source_sampling_orders']:
                for isprobe in (False,True):
                    r=run(f'periodic_source_q{order}_{verified_dt}_{int(isprobe)}',verified_dt,41,'finite_periodic',isprobe,order)
                    source_results[isprobe].append(r)
            source_checks=[]
            for isprobe,rows in source_results.items():
                for a,b in zip(rows[:-1],rows[1:]):source_checks.append({'probe':isprobe,'orders':[a['source_order'],b['source_order']],**compare(a,b)})
            checks['source']=source_checks;gates['source_convergence_screen']=all(passes(c,tolerance) for c in source_checks)
        else:
            decisions.append({'action':'Do not use periodic acceleration for spatial/source certification','reason':'Whole direct agreement not established at bounded finest step'})
        # This milestone only determines whether a fresh comparison can be
        # planned; it never performs an unreviewed new optimization search.
        gates['fresh_optimization_planning_ready']=all(gates[k] for k in ('time_convergence_screen','finite_periodic_direct_agreement_screen','grid_convergence_screen','source_convergence_screen','combined_resolution_direct_agreement_screen','cv_objective_gap_resolved'))
        status='complete_process_numerical_milestone' if gates['fresh_optimization_planning_ready'] else 'complete_process_convergence_unresolved'
    except Exception as exc:
        gates=locals().get('gates',{'fresh_optimization_allowed':False,'engineering_ranking_allowed':False})
        decisions.append({'action':'Stop bounded stage without recipe simplification','reason':f'{type(exc).__name__}: {exc}'})
        status='complete_process_resource_or_numeric_blocker'
    report={'config':cfg,'status':status,'gates':gates,'checks':checks,'decisions':decisions,
        'result_files':list(results),'results':{k:serial(v) for k,v in results.items()},
        'main_core_audits':observer.records,'main_actual_core_calls':len(observer.records),
        'wall_s':time.perf_counter()-start,'historical_unchanged':old_identity()==identity,
        'product_python_unchanged':source_hashes()==sources,'complete_original_process_preserved':True}
    if not report['historical_unchanged'] or not report['product_python_unchanged']:raise RuntimeError('Read-only identity failed')
    (HERE/'convergence_results.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':status,'gates':gates,'checks':checks,'decisions':decisions,'calls':len(observer.records),'wall_s':report['wall_s']},indent=2),flush=True)


if __name__=='__main__':main()
