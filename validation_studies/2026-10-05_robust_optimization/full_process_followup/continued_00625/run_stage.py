"""Next full native layer pair, with persistent progress checkpoints."""
from pathlib import Path
import json
import sys
import time
import numpy as np

HERE=Path(__file__).resolve().parent;PARENT=HERE.parent
sys.path.insert(0,str(PARENT))
from run_full_process import load_inputs,run_one,CoreObserver,old_identity,source_hashes
from run_convergence import load_result,compare,serial


def save(name,row):
    np.savez(HERE/(name+'.npz'),**{k:row[k] for k in ('field_nm','x','y')})
    (HERE/(name+'.json')).write_text(json.dumps(serial(row),indent=2)+'\n')


def main():
    cfg=json.loads((HERE/'config.json').read_text());parent_cfg=json.loads((PARENT/'config.json').read_text())
    snapshot,runtime,native=load_inputs(parent_cfg);old=old_identity();sources=source_hashes()
    observer=CoreObserver(cfg['max_actual_core_calls']);start=time.perf_counter();rows={};checks={}
    reference=json.loads((PARENT/'convergence_results.json').read_text())
    def checkpoint(status):
        out={'config':cfg,'status':status,'results':{k:serial(v) for k,v in rows.items()},
            'checks':checks,'actual_core_calls':len(observer.records),'core_audits':observer.records,
            'wall_s':time.perf_counter()-start,'historical_unchanged':old_identity()==old,
            'product_python_unchanged':source_hashes()==sources,'engineering_ranking_allowed':False}
        (HERE/'stage_results.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    checkpoint('planned_complete_dt.00625_pair')
    try:
        for probe in (False,True):
            name='direct_000625_g21'+('_probe' if probe else '')
            remaining=cfg['planning_wall_allowance_s']-(time.perf_counter()-start)
            row=run_one(runtime,native,cfg['requested_dt_s'],21,'direct',observer,remaining,probe)
            save(name,row);rows[name]=row
            prev=load_result('direct_00125_g21'+('_probe' if probe else ''))
            checks['time_00125_to_000625'+('_probe' if probe else '')]=compare(prev,row)
            checkpoint('complete_baseline' if not probe else 'complete_direct_pair')
            print(json.dumps({'completed':name,'complete_duration_s':row['total_duration_s'],
                'actual_layer_dt_s':row['timing']['step_time_step_s'],'actual_core_calls':row['core_calls'],
                'wall_s':row['wall_s'],'difference_from.0125':checks['time_00125_to_000625'+('_probe' if probe else '')]}),flush=True)
        for probe in (False,True):
            name='periodic_000625_g21'+('_probe' if probe else '')
            remaining=cfg['planning_wall_allowance_s']-(time.perf_counter()-start)
            row=run_one(runtime,native,cfg['requested_dt_s'],21,'finite_periodic',observer,remaining,probe)
            save(name,row);rows[name]=row
            direct=rows['direct_000625_g21'+('_probe' if probe else '')]
            checks['periodic_vs_direct_000625'+('_probe' if probe else '')]=compare(direct,row)
            checkpoint('periodic_pair_checked')
        tau=reference['checks']['tolerance_pp'];cv_tau=.1*reference['checks']['effect_probe']['cv_change_pp']
        checks['retained_shape_tolerance_pp']=tau;checks['additional_cv_sensitivity_tolerance_pp']=cv_tau
        checks['shape_screen_pass']=all(all(v[k]<tau for k in ('normalized_field_rms_pp','interior135_field_rms_pp','cv_change_pp','interior135_cv_change_pp')) for v in list(checks.values())[:4])
        checks['production_tolerance']='unknown_not_inferred'
        checkpoint('complete_next_refinement_no_engineering_rank')
    except Exception as exc:
        checks['blocker']=f'{type(exc).__name__}: {exc}';checkpoint('explicit_failure_not_truncated_success');raise
    print(json.dumps({'stage_calls':len(observer.records),'wall_s':time.perf_counter()-start,'checks':checks},indent=2),flush=True)


if __name__=='__main__':main()
