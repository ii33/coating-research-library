from dataclasses import replace
from pathlib import Path
import json
import sys
import time
import numpy as np

HERE=Path(__file__).resolve().parent;BASE=HERE.parent
sys.path.insert(0,str(BASE))
from run_full_process import load_inputs,capped_timing,CoreObserver,metrics,old_identity,source_hashes
from run_convergence import load_result,compare,serial
from coat_sim.core import process_simulator,periodic_integration


def stage_reference(name):
    root=BASE/'continued_00625';row=json.loads((root/(name+'.json')).read_text())
    with np.load(root/(name+'.npz')) as f:row.update({k:f[k].copy() for k in ('field_nm','x','y')})
    return row


def main():
    cfg=json.loads((HERE/'config.json').read_text());base=json.loads((BASE/'config.json').read_text());snapshot,runtime,native=load_inputs(base)
    before=old_identity();sources=source_hashes();obs=CoreObserver(cfg['max_actual_core_calls']);start=time.perf_counter();rows=[]
    for dt in cfg['requested_dt_s']:
        timing=capped_timing(runtime['profile'],dt);settings=replace(native,time_steps=timing['time_steps'],grid_size=21)
        old=process_simulator.simulate;process_simulator.simulate=obs.simulate;obs.active_cap=dt;offset=len(obs.records);t=time.perf_counter()
        try:
            result=process_simulator.simulate_process(settings,runtime,backend='CPU',fast_cycle=True,
                fast_cycle_residual_percent=100.,finite_periodic=False)
        finally:process_simulator.simulate=old
        fast={'mode':'fast_cycle_mean','grid':21,'requested_dt_s':dt,'probe':False,
            'field_nm':result['field_nm'],'x':result['x'],'y':result['y'],'metrics':metrics(result),
            'timing':timing,'total_duration_s':result['total_duration_s'],'total_target_nm':result['total_target_nm'],
            'step_results':result['step_results'],'core_calls':len(obs.records)-offset,'core_audits':obs.records[offset:],'wall_s':time.perf_counter()-t}
        name=f'fast_cycle_{dt}';np.savez(HERE/(name+'.npz'),**{k:fast[k] for k in ('field_nm','x','y')})
        (HERE/(name+'.json')).write_text(json.dumps(serial(fast),indent=2)+'\n')
        direct=load_result('direct_0025_g21') if dt==.025 else stage_reference('direct_000625_g21')
        finite=load_result('periodic_0025_g21') if dt==.025 else stage_reference('periodic_000625_g21')
        counts_fast=[s['time_steps'] for s in fast['step_results']]
        cycles_finite=[a['requested_time_steps'] for a in finite['core_audits'] if abs(a['duration_s']-12.)<1e-10]
        matched=counts_fast==cycles_finite
        avg=[]
        for f,d in zip(fast['step_results'],direct['step_results']):
            avg.append({'layer':f['step_index'],'physical_duration_s':d['duration_s'],
                'fast_simulated_duration_s':f['simulated_duration_s'],'fast_samples':f['time_steps'],
                'actual_fast_dt_s':f['time_step_s'],'finite_periodic_flag':f['finite_periodic_integration'],
                'discarded_tail_s':f['residual_s'],'discarded_tail_fraction':f['residual_fraction'],
                'fast_cycle_mean_flux':f['mean_raw']/f['simulated_duration_s'],
                'direct_physical_mean_flux':d['mean_raw']/d['duration_s'],
                'mean_flux_relative_difference_percent':abs((f['mean_raw']/f['simulated_duration_s'])/(d['mean_raw']/d['duration_s'])-1)*100})
        rows.append({'requested_dt_s':dt,'fast_result':serial(fast),'fast_vs_direct':compare(fast,direct),
            'fast_vs_finite_periodic':compare(fast,finite),'cycle_sample_counts_fast':counts_fast,
            'cycle_sample_counts_finite':cycles_finite,'cycle_quadrature_matched':matched,
            'tail_treatment_isolation':matched,'layer_mean_flux_audit':avg})
    out={'config':cfg,'checks':rows,'actual_core_calls':len(obs.records),'wall_s':time.perf_counter()-start,
        'historical_unchanged':old_identity()==before,'product_python_unchanged':source_hashes()==sources,
        'interpretation':'Fast_cycle mean discards actual layer tails and normalizes each cycle map to its mean target. At matched cycle quadrature the difference from finite_periodic isolates this averaging approximation. Full direct comparisons also include distinct temporal quadrature errors.',
        'engineering_ranking_allowed':False}
    (HERE/'branch_results.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'checks':[{k:r[k] for k in ('requested_dt_s','fast_vs_direct','fast_vs_finite_periodic','cycle_sample_counts_fast','cycle_sample_counts_finite','cycle_quadrature_matched')} for r in rows],
                      'calls':len(obs.records),'wall_s':out['wall_s']},indent=2),flush=True)


if __name__=='__main__':main()
