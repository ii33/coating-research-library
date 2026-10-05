"""Separate small fixtures explain quadrature, not a shortened main benchmark."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import json
import math
import sys
import time

import numpy as np

HERE=Path(__file__).resolve().parent;PARENT=HERE.parent
sys.path.insert(0,str(PARENT))
from run_full_process import load_inputs,CoreObserver,run_one,old_identity,source_hashes,metrics
from run_convergence import compare
from coat_sim.core import process_simulator,periodic_integration


def adapted(result):
    out={'field_nm':result['field'],'x':result['x'],'y':result['y']}
    out['metrics']=metrics(out);return out


def main():
    cfg=json.loads((PARENT/'config.json').read_text());snapshot,runtime,native=load_inputs(cfg)
    before=old_identity();sources=source_hashes();start=time.perf_counter()
    machine=runtime['machine'];source=machine['sources'][1];mask=[machine['masks'][1]['profile']]
    geom={k:machine[k] for k in process_simulator._GEOMETRY_FIELDS}
    obs=CoreObserver(40);obs.active_cap=.025;rows=[]
    previous=periodic_integration.simulate;periodic_integration.simulate=obs.simulate
    try:
        for name,duration in [('under_period',4.383),('aligned_whole_periods',24.),('aligned_periods_plus_tail',24.375),('unaligned_periods_plus_tail',24.383)]:
            settings=replace(native,**geom,duration_s=duration,time_steps=math.ceil(duration/.025),grid_size=21,
                carrier_phase_deg=0.,planet_phase_deg=120.,source_x_mm=source['x_mm'],source_y_mm=source['y_mm'],
                source_z_mm=source['z_mm'],source_exponent=source['profile']['source_exponent'],source_rate_nm_s=.9)
            offset=len(obs.records)
            direct=obs.simulate(settings,mask=mask,source_profile=source['profile'])
            reduced,count,used=periodic_integration.simulate_finite_periodic(settings,mask=mask,
                source_profile=source['profile'],backend='CPU',cancel_event=None,period_s=12.,
                canonical_phases=(0.,0.),cache=periodic_integration.PeriodicCache(),identity=name)
            rows.append({'fixture':name,'classification':'Separate synthetic time-window fixture using unchanged source2/board2 geometry, not the user full-process benchmark',
                'duration_s':duration,'actual_direct_dt_s':duration/settings.time_steps,'periodic_used':used,
                'direct_periodic_map_difference':compare(adapted(direct),adapted(reduced)),
                'raw_mean_relative_difference_percent':abs(reduced['mean_raw']/direct['mean_raw']-1)*100,
                'core_calls':len(obs.records)-offset,'core_audits':obs.records[offset:]})
    finally:periodic_integration.simulate=previous
    thin=deepcopy(runtime);thin['profile']['steps']=[{'source_slot':2,'target_nm':4.383*.9,'rate_nm_s':.9,'target_mode':'mean','mask_slots':[1]} for _ in range(8)]
    thin['steps']=thin['profile']['steps'];offset=len(obs.records)
    direct=run_one(thin,native,.025,21,'direct',obs)
    periodic=run_one(thin,native,.025,21,'finite_periodic',obs)
    rows.append({'fixture':'eight_subperiod_layers','classification':'Eight synthetic4.383-second layers; main original recipe is untouched',
        'complete_fixture_duration_s':direct['total_duration_s'],
        'all_layers_under_return_period':True,'all_layers_fallback_to_full':not any(s['finite_periodic_integration'] for s in periodic['step_results']),
        'direct_periodic_map_difference':compare(direct,periodic),'core_calls':len(obs.records)-offset,
        'per_layer_actual_dt_s':direct['timing']['step_time_step_s']})
    out={'fixtures':rows,'actual_core_calls':len(obs.records),'wall_s':time.perf_counter()-start,
        'main_input_snapshot_untouched':True,'historical_unchanged':old_identity()==before,
        'product_python_unchanged':source_hashes()==sources,'production_tolerance':'unknown_not_inferred',
        'interpretation':'Correct full periods plus actual tails are a physical decomposition; sampled grids may differ. Under-period fallback uses identical full integration, so many short layers alone do not create periodic replacement error.'}
    (HERE/'mechanism_results.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print(json.dumps(out,indent=2),flush=True)


if __name__=='__main__':main()
