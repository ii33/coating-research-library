"""Summarize existing small evidence; performs no source/time integrals."""
from pathlib import Path
import csv,json,hashlib,ast
R=Path(__file__).resolve().parents[1]
s=json.loads((R/'data/small_checks.json').read_text());loc=json.loads((R/'data/localization.json').read_text());rows=[]
for j in [2,12]:
    duration=s['A_support'][str(j)]['duration']
    for family,key in [('S2_5x23','s2t2'),('holdout_7x29','holdout')]:
        val=loc[key][j][3]
        rows.append({'case':'A','point':j,'method':family,'quantity':'ion_only_duration','value':val,'reference':duration['midpoint_s'],'absolute_difference':abs(val-duration['midpoint_s']),'unit':'s','relative_difference':'','difference_ms':abs(val-duration['midpoint_s'])*1000,'reference_status':duration['status'],'strict_bound':False})
for idx,unit in [(0,'atoms/m2'),(1,'ions/m2')]:
    a=loc['s2t2'][12][idx];b=loc['holdout'][12][idx]
    rows.append({'case':'A','point':12,'method':'S2_vs_holdout','quantity':'N' if idx==0 else 'D','value':a,'reference':b,'absolute_difference':abs(a-b),'unit':unit,'relative_difference':abs(a-b)/loc['frozen_mean_scales'][idx],'difference_ms':'','reference_status':'estimator_difference_only_no_truth','strict_bound':False})
partial=ast.literal_eval((R/'verification/main_run_1.log').read_text().split('base ',1)[1].strip())
for family,key in [('S2_5x23','s2t2'),('holdout_7x29','holdout')]:
    a=loc[key][2][0];b=partial['integral_SI']
    rows.append({'case':'A','point':2,'method':family,'quantity':'N','value':a,'reference':b,'absolute_difference':abs(a-b),'unit':'atoms/m2','relative_difference':abs(a-b)/abs(b),'difference_ms':'','reference_status':'single_base_only_tight_not_run','strict_bound':False})
for b in s['B']['rows']:
    rows.append({'case':'B','point':'','method':b['method']+'_'+str(b['nodes'])+'_phase_'+str(b['phase']),'quantity':'unit_interval_integral','value':b['estimate'],'reference':1,'absolute_difference':b['absolute_error'],'unit':'dimensionless','relative_difference':b['absolute_error'],'difference_ms':'','reference_status':'analytic_exact_integral','strict_bound':False})
with (R/'data/error_comparisons.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
work=[{'operation':'one_13_point_S2_localization','measured_count':loc['budget']['ray_evaluations'],'work_kind':'legacy_ray','seconds':loc['budget']['wall_seconds'],'status':'completed'}, {'operation':'small_support_alias_sidewall_checks','measured_count':s['budget']['total_work_units'],'work_kind':'mixed_explicit_operations','seconds':s['budget']['wall_seconds'],'status':'completed'}, {'operation':'interrupted_nested_reference','measured_count':'','work_kind':'counter_not_flushed_upper_bound_30000000','seconds':'','status':'interrupted_not_complete'}, {'operation':'device_2_points_high_accuracy','measured_count':'','work_kind':'planned_fixed_rays_2450612480_plus_low_dim_reference','seconds':'','status':'not_run_awaiting_device'}]
with (R/'data/work_comparisons.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=work[0].keys());w.writeheader();w.writerows(work)
(R/'data/partial_reference.json').write_text(json.dumps({'point':2,'channel':'vapor','base':partial,'tight':{'status':'not_completed_interrupted'},'point12_ion_reference':{'status':'not_run_awaiting_device'},'reason':'execution scope amended by user before completion'},indent=2)+'\n')
ledger={'localization_measured':loc['budget'],'unmetered_smoke_conservative_allowance':10000,'interrupted_main_conservative_work_upper_bound':30000000,'interrupted_exit_code':130,'small_checks_measured':s['budget'],'main_cumulative_conservative_work_upper_bound':loc['budget']['ray_evaluations']+10000+30000000+s['budget']['total_work_units']+30000,'small_api_test_and_isolated_reader_conservative_allowance':30000,'main_original_cumulative_limit':60000000,'device_high_cost_work_executed':False,'note':'Mixed-operation counts are not FLOPs or performance comparisons. Original preserved holdout has zero new work. Independent review counted separately.'}
ledger['independent_narrow_review']={'smooth_samples':63808,'oracle_calls':256,'budget_samples':200000,'budget_oracle_calls':512,'status':'completed_one_narrow_check'}
(R/'verification/execution_ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
print(json.dumps({'duration_error_S2_ms':rows[0]['difference_ms'],'duration_error_holdout_ms':rows[1]['difference_ms'],'partial_reference_N':partial['integral_SI'],'ledger_upper':ledger['main_cumulative_conservative_work_upper_bound']},indent=2))
