#!/usr/bin/env python3
"""Deterministic bounded synthetic comparison. Run with BLAS thread count 1."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import sys,json,csv,time,hashlib,platform
from pathlib import Path
from dataclasses import replace,asdict
import numpy as np
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'models'))
from mask_design import *
OUT=ROOT/'benchmarks/results';OUT.mkdir(exist_ok=True)
def js(value):
    if isinstance(value,np.ndarray):return value.tolist()
    if isinstance(value,(np.integer,np.floating)):return value.item()
    raise TypeError(type(value).__name__)
def save(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,default=js,allow_nan=False)+'\n')
def csvout(name,rows):
    with (OUT/name).open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def timed(fn):
    t=time.perf_counter();r=fn();return r,time.perf_counter()-t

def run():
    start=time.perf_counter();cfg=replace(Config(),duration_s=40.,rate_ripple=0.)
    specification=dict(scope='invented synthetic geometry; no machine calibration',config=asdict(cfg),train=dict(nr=4,na=16,panels=2048,source_nr=2,source_na=8,azimuth_offset=0),validation=dict(nr=6,na=24,panels=4096,source_nr=3,source_na=16,azimuth_offset=.137),shape_max_evaluations=480,robust_max_evaluations=160,min_throughput=.80,target_ratio=.90,success_gate='heldout CV and PV below no-mask baseline; all tested throughputs >= .80; geometric screen passes; this is not a production tolerance',nominal_scenario_policy='single cfg',robust_train_changes=[{},dict(source_x_m=.115,source_exponent=1.85),dict(source_x_m=.125,source_exponent=2.15)],uncertainty_status='hypothetical deterministic scenarios, no probability distribution')
    (ROOT/'data/synthetic_case.json').write_text(json.dumps(specification,ensure_ascii=False,indent=2)+'\n')
    train,build_s=timed(lambda:build_bundle(cfg,**specification['train']))
    relaxation,relax_s=timed(lambda:optimize_relaxation(train,max_iterations=15000))
    rounded=relaxation_to_band(relaxation)
    const=np.full(8,.025)
    nominal,nominal_s=timed(lambda:optimize_shape([train],const,max_evaluations=480))
    seeded,seeded_s=timed(lambda:optimize_shape([train],rounded,max_evaluations=480))
    robust_bundles=[train]+[build_bundle(replace(cfg,**x),**specification['train']) for x in specification['robust_train_changes'][1:]]
    robust,robust_s=timed(lambda:optimize_shape(robust_bundles,rounded,max_evaluations=160))
    shapes={'constant_band':const,'area_equivalent_rounding':rounded,'pattern_constant_seed':nominal['widths_m'],'pattern_relaxation_seed':seeded['widths_m'],'robust_pattern_equal_oracle_budget':robust['widths_m']}
    print('optimization finished',flush=True)
    opt_summary={name:{**result,'wall_s':secs,'scenario_oracle_evaluations':result['evaluations']*n} for name,result,secs,n in [('pattern_constant_seed',nominal,nominal_s,1),('pattern_relaxation_seed',seeded,seeded_s,1),('robust_pattern_equal_oracle_budget',robust,robust_s,3)]}
    relax_metrics=metric(train.base_nm-relaxation['matrix']@relaxation['opacity'],train.base_nm,train.area,train.rings)
    train_metrics={'no_mask':metric(train.base_nm,train.base_nm,train.area,train.rings),'opacity_relaxation':relax_metrics}
    for name,w in shapes.items():train_metrics[name]=metric(train.masked(w,0),train.base_nm,train.area,train.rings)
    results=[];validation={};validation_raw={}
    for name,w in {'no_mask':None,**shapes}.items():
        val,seconds=timed(lambda:evaluate_streaming(cfg,w,**specification['validation']))
        validation[name]=val['metrics'];validation_raw[name]=val
        results.append(dict(method=name,**val['metrics'],wall_validation_s=seconds))
        print('validation',name,val['metrics']['cv'],flush=True)
    opacity_validation=evaluate_streaming(cfg,None,thickness_m=0,opacity_grid=(relaxation['x_edges'],relaxation['y_edges'],relaxation['opacity']),**specification['validation'])['metrics']
    csvout('comparison.csv',results)
    # Candidate selection uses training objective only, never validation score.
    selected_name=min(('pattern_constant_seed','pattern_relaxation_seed'),key=lambda name:opt_summary[name]['objective'])
    selected=shapes[selected_name];save('optimization_traces.json',opt_summary)
    save('designs.json',dict(selected_by_training_objective=selected_name,x_knots_m=XKNOTS,shapes=shapes,polygons_m={name:export_polygon(w) for name,w in shapes.items()},geometric_checks={name:manufacturing(w) for name,w in shapes.items()},warning='synthetic 2D polygons; fixtures, tool radius, stress, temperature, cleanliness and collision not certified'))
    # Isolate time convergence on identical spatial and source grids.
    time_rows=[];last=None
    for panels in [512,1024,2048,4096,8192]:
        val=evaluate_streaming(cfg,selected,nr=4,na=16,panels=panels,source_nr=2,source_na=12,azimuth_offset=.137)
        h=val['thickness_nm'];mu=val['metrics']['mean_nm']
        row=dict(panels=panels,**val['metrics'],max_abs_delta_over_mean=None if last is None else float(max(abs(h-last))/mu));time_rows.append(row);last=h
    csvout('time_convergence.csv',time_rows)
    source_rows=[];last=None
    for nr,na in [(1,8),(2,12),(3,16),(4,24)]:
        val=evaluate_streaming(cfg,selected,nr=4,na=16,panels=4096,source_nr=nr,source_na=na,azimuth_offset=.137);h=val['thickness_nm'];mu=val['metrics']['mean_nm']
        source_rows.append(dict(source_nr=nr,source_na=na,source_nodes=nr*na,**val['metrics'],max_abs_delta_over_mean=None if last is None else float(max(abs(h-last))/mu)));last=h
    csvout('source_convergence.csv',source_rows)
    surface_rows=[]
    for nr,na in [(3,12),(4,16),(6,24),(8,32)]:
        val=evaluate_streaming(cfg,selected,nr=nr,na=na,panels=4096,source_nr=2,source_na=12,azimuth_offset=.137)
        surface_rows.append(dict(surface_nr=nr,surface_na=na,point_count=nr*na,**val['metrics']))
    csvout('surface_convergence.csv',surface_rows)
    # Edge is a separate diagnostic, never assigned fabricated area weights.
    theta=2*np.pi*(np.arange(96)+.371)/96
    probes=np.vstack(([0,0,0],np.column_stack((cfg.radius_m*np.cos(theta),cfg.radius_m*np.sin(theta),np.zeros(96)))))
    pv=evaluate_streaming(cfg,selected,panels=8192,source_nr=3,source_na=16,probe_points_m=probes)
    mu=validation[selected_name]['mean_nm'];save('edge_probes.json',dict(points_m=probes,thickness_nm=pv['thickness_nm'],base_nm=pv['base_nm'],reference_area_mean_nm=mu,max_deviation_from_area_mean=float(max(abs(pv['thickness_nm']-mu))/mu),warning='center + rim probes are not area integration and do not certify continuous supremum'))
    print('convergence finished',flush=True)
    changes=[('nominal',{}),('source_x_minus_5mm',dict(source_x_m=.115)),('source_x_plus_5mm',dict(source_x_m=.125)),('mask_z_minus_5mm',dict(mask_z_m=.495)),('mask_z_plus_5mm',dict(mask_z_m=.505)),('source_exponent_minus_015',dict(source_exponent=1.85)),('source_exponent_plus_015',dict(source_exponent=2.15)),('source_radius_plus_5mm',dict(source_radius_m=.020)),('combined_unseen',dict(source_x_m=.124,mask_z_m=.504,source_exponent=2.12,mask_y_shift_m=.001)),('phase_and_short_duration',dict(duration_s=38.7,carrier_phase=.41,relative_phase=.69))]
    scenario_rows=[]
    for scenario,change in changes:
        for name,w in [(selected_name,selected),('robust_pattern_equal_oracle_budget',shapes['robust_pattern_equal_oracle_budget'])]:
            val=evaluate_streaming(replace(cfg,**change),w,nr=4,na=16,panels=2048,source_nr=2,source_na=12,azimuth_offset=.137)
            scenario_rows.append(dict(scenario=scenario,method=name,geometric_screen_pass=manufacturing(w)['passed'],**val['metrics']))
    # Machining perturbation is hypothetical ±0.25 mm boundary, not machine specification.
    for sign in [-1,1]:
        w=selected+sign*.00025
        val=evaluate_streaming(cfg,w,nr=4,na=16,panels=2048,source_nr=2,source_na=12,azimuth_offset=.137)
        scenario_rows.append(dict(scenario='boundary_offset_'+str(sign*.00025)+'m',method=selected_name,geometric_screen_pass=manufacturing(w)['passed'],**val['metrics']))
    csvout('robustness_scenarios.csv',scenario_rows)
    # Deliberate failed case: short finite run and ripple. Same 480-evaluation cap.
    badcfg=Config();badtrain=build_bundle(badcfg,**specification['train']);br=optimize_relaxation(badtrain,max_iterations=15000);bs=optimize_shape([badtrain],relaxation_to_band(br),max_evaluations=480)
    badval=evaluate_streaming(badcfg,bs['widths_m'],**specification['validation'])
    failed=dict(config=asdict(badcfg),widths_m=bs['widths_m'],train_objective=bs['objective'],unmasked=badval['baseline_metrics'],binary_mask=badval['metrics'],cv_worsens=badval['metrics']['cv']>badval['baseline_metrics']['cv'],reason='finite-run angular structure and target-throughput term; radial flattening alone is not full-field uniformity')
    save('failure_case.json',failed)
    # Singular inverse and target that asks for added deposition.
    M=np.array([[1.,1.],[1.,1.]])
    inverse_diagnostic=dict(singular_matrix_rank=int(np.linalg.matrix_rank(M)),columns=2,unreachable_positive_target_nm=[1.1,1.1],baseline_nm=[1.,1.],reason='passive mask cannot add deposition; singular inverse is undefined; nonnegative bounded least squares cannot make this target feasible')
    save('infeasibility.json',inverse_diagnostic)
    chosen=validation[selected_name];base=validation['no_mask'];selection_gate=dict(cv_improved=chosen['cv']<base['cv'],pv_improved=chosen['pv_over_mean']<base['pv_over_mean'],throughput_pass=chosen['throughput_ratio']>=.8,geometry_pass=manufacturing(selected)['passed'])
    summary=dict(version=VERSION,selected=selected_name,synthetic_gate=selection_gate,train_metrics=train_metrics,validation_metrics=validation,opacity_validation_metrics=opacity_validation,opacity_solver={k:relaxation[k] for k in ['iterations','converged','projected_gradient_inf','objective','throughput_violation','matrix_rank','singular_values']},opacity_matrix_shape=list(relaxation['matrix'].shape),preprocessing_seconds=build_s,opacity_seconds=relax_s,optimizer_budget='nominal: <=480 one-scenario calls; robust <=160 three-scenario calls (=480 scenario calls); opacity optimization and seed overhead reported separately',time_convergence_last_delta=time_rows[-1]['max_abs_delta_over_mean'],source_convergence_last_delta=source_rows[-1]['max_abs_delta_over_mean'],failure_case_cv_worsens=failed['cv_worsens'],tested_scenario_throughput_min=min(x['throughput_ratio'] for x in scenario_rows),total_wall_seconds=time.perf_counter()-start,python=platform.python_version(),numpy=np.__version__,model_sha256=hashlib.sha256((ROOT/'models/mask_design.py').read_bytes()).hexdigest(),t02_model_sha256=hashlib.sha256((ROOT.parent/'02_machine_modeling/models/deposition_reference.py').read_bytes()).hexdigest(),claims='No physical verification, global shape optimum, certified numerical error bound, probability coverage, or fabrication release')
    save('benchmark_summary.json',summary)
    print(json.dumps({k:summary[k] for k in ['selected','synthetic_gate','time_convergence_last_delta','source_convergence_last_delta','failure_case_cv_worsens','total_wall_seconds']},indent=2))
if __name__=='__main__':run()
