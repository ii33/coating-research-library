from pathlib import Path
import json
import sys
import time
import numpy as np

HERE=Path(__file__).resolve().parent;STAGE=HERE.parent;BASE=STAGE.parent
sys.path.insert(0,str(BASE))
from run_full_process import load_inputs,run_one,CoreObserver,old_identity,source_hashes
from run_convergence import compare,serial


def reference(probe):
    name='direct_000625_g21'+('_probe' if probe else '')
    row=json.loads((STAGE/(name+'.json')).read_text())
    with np.load(STAGE/(name+'.npz')) as f:row.update({k:f[k].copy() for k in ('field_nm','x','y')})
    return row


def main():
    cfg=json.loads((HERE/'config.json').read_text());base_cfg=json.loads((BASE/'config.json').read_text())
    stage=json.loads((STAGE/'stage_results.json').read_text());tau=stage['checks']['retained_shape_tolerance_pp'];cv_tau=stage['checks']['additional_cv_sensitivity_tolerance_pp']
    snapshot,runtime,native=load_inputs(base_cfg);observer=CoreObserver(cfg['max_actual_core_calls'])
    before=old_identity();sources=source_hashes();start=time.perf_counter();levels=[];accepted_dt=None
    for dt in cfg['periodic_dt_ladder_s']:
        rows=[]
        for probe in (False,True):
            result=run_one(runtime,native,dt,21,'finite_periodic',observer,cfg['planning_wall_allowance_s']-(time.perf_counter()-start),probe)
            name=f'periodic_{dt}_{int(probe)}';np.savez(HERE/(name+'.npz'),**{k:result[k] for k in ('field_nm','x','y')})
            (HERE/(name+'.json')).write_text(json.dumps(serial(result),indent=2)+'\n')
            mismatch=compare(reference(probe),result)
            direct_delta=stage['checks']['time_00125_to_000625'+('_probe' if probe else '')]
            sum_screen={k:mismatch[k]+direct_delta[k] for k in ('normalized_field_rms_pp','interior135_field_rms_pp','cv_change_pp','interior135_cv_change_pp')}
            shape_ok=all(sum_screen[k]<tau for k in ('normalized_field_rms_pp','interior135_field_rms_pp'))
            cv_ok=all(sum_screen[k]<cv_tau for k in ('cv_change_pp','interior135_cv_change_pp'))
            rows.append({'probe':probe,'periodic_result':serial(result),'mismatch':mismatch,
                'observed_change_sum':sum_screen,'shape_sum_screen_pass':shape_ok,'cv_sum_screen_pass':cv_ok})
        passed=all(r['shape_sum_screen_pass'] and r['cv_sum_screen_pass'] for r in rows)
        levels.append({'requested_periodic_dt_s':dt,'cases':rows,'passed_fixed_grid21_screen':passed})
        print(json.dumps({'dt_s':dt,'passed_fixed_grid21_screen':passed,'cases':[{k:r[k] for k in ('probe','mismatch','observed_change_sum','shape_sum_screen_pass','cv_sum_screen_pass')} for r in rows]},indent=2),flush=True)
        if passed:accepted_dt=dt;break
    output={'config':cfg,'levels':levels,'accepted_periodic_dt_s_for_fixed_grid21_cases':accepted_dt,
        'actual_core_calls':len(observer.records),'core_audits':observer.records,'wall_s':time.perf_counter()-start,
        'full_process_preserved':True,'historical_unchanged':old_identity()==before,'product_python_unchanged':source_hashes()==sources,
        'qualification':'Only the two fixed grid21,legacy12/16-source cases; not transferred to denser grids or source quadrature',
        'combined_final_resolution_direct_check':'not_run','engineering_ranking_allowed':False}
    (HERE/'finer_results.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({'accepted_dt_s':accepted_dt,'calls':len(observer.records),'wall_s':output['wall_s']},indent=2),flush=True)


if __name__=='__main__':main()
