"""Complete recovered native recipe, unchanged product orchestration and CPU core."""
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
import argparse
import hashlib
import json
import math
import sys
import threading
import time

import numpy as np

HERE=Path(__file__).resolve().parent;FIRST=HERE.parent;WORKSPACE=HERE.parents[4]
sys.path.insert(0,str(FIRST/'engineeringgate'))
from run_gate import historical_identity,source_hashes
sys.path.insert(0,str(FIRST))
from evaluator import PRODUCT,clipped_cell_weights
sys.path.insert(0,str(FIRST/'convergence_followup'))
from run_followup import roi_weights
from coat_sim.core.input_snapshot import runtime_from_snapshot,canonical_json_bytes
from coat_sim.core.simulator import Settings,_simulate_on_backend,minimum_substrate_z,_mask_layers
from coat_sim.core.source_profiles import source_samples,effective_source_exponent,source_cover
from coat_sim.core import process_simulator,periodic_integration


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def old_identity():
    out=historical_identity();gate=FIRST/'engineeringgate';m=json.loads((gate/'artifact_manifest.json').read_text())
    for name,digest in m['files'].items():
        if sha(gate/name)!=digest:raise RuntimeError('Historical gate changed')
        out['gate/'+name]=digest
    out['gate/manifest']=sha(gate/'artifact_manifest.json');return out


def load_inputs(config):
    path=WORKSPACE/config['source_recovered_snapshot_relative']
    if sha(path)!=config['source_recovered_snapshot_sha256']:raise RuntimeError('Recovered input checksum mismatch')
    recovered=json.loads(path.read_text());snapshot=recovered['input_snapshot']
    runtime=runtime_from_snapshot(snapshot)
    if next(r['sha256'] for r in snapshot['files'] if r['kind']=='process')!=config['complete_process_canonical_sha256']:
        raise RuntimeError('Selected process identity mismatch')
    native=recovered['job_fingerprint_inputs']['settings']
    settings=Settings(**native)
    return snapshot,runtime,settings


def capped_timing(profile,dt):
    if not 0<dt<=.05:raise ValueError('Actual requested step must be<=.05 seconds')
    plan=process_simulator.process_timing(profile,time_step_s=dt)
    # Original global allocation may put an individual layer just over its cap.
    # Increase only the global count; never round an over-cap layer into a pass.
    while max(plan['step_time_step_s'])>dt:
        plan=process_simulator.process_timing(profile,time_steps=plan['time_steps']+1)
    return plan


class CoreObserver:
    def __init__(self,call_cap=None):self.records=[];self.active_cap=None;self.call_cap=call_cap;self.cancel_file=None
    def simulate(self,settings,mask=None,backend='CPU',cancel_event=None,source_profile=None,progress=None):
        if self.call_cap is not None and len(self.records)>=self.call_cap:raise RuntimeError('Actual core-call budget exhausted')
        settings.validate();layers=_mask_layers(mask)
        if any(m['z_mm']>=minimum_substrate_z(settings) for m in layers):raise ValueError('Invalid mask/substrate geometry')
        positions,weights=source_samples(settings,source_profile);exponent=effective_source_exponent(settings,source_profile)
        cover=source_cover(source_profile,settings)
        if cover and settings.source_z_mm+cover['cover_height_mm']+cover['cover_thickness_mm']>=minimum_substrate_z(settings):raise ValueError('Invalid source cover')
        if settings.duration_s/settings.time_steps>self.active_cap:raise RuntimeError('A core integration exceeds its actual time-step cap')
        fractions=[];start=time.perf_counter()
        record={'duration_s':settings.duration_s,'requested_time_steps':settings.time_steps,
            'actual_dt_s':settings.duration_s/settings.time_steps,'grid_size':settings.grid_size,
            'source_samples':len(weights),'mask_layers':len(layers),
            'carrier_phase_deg':settings.carrier_phase_deg,'planet_phase_deg':settings.planet_phase_deg,
            'source_xyz_mm':[settings.source_x_mm,settings.source_y_mm,settings.source_z_mm],
            'status':'attempted'}
        self.records.append(record)
        def report(f):
            fractions.append(f)
            if self.cancel_file is not None and self.cancel_file.exists() and cancel_event is not None:
                cancel_event.set()
            if progress:progress(f)
        try:
            result=_simulate_on_backend(settings,layers if layers else None,np,'CPU',cancel_event,
                positions,weights,progress=report,cover=cover,source_exponent=exponent)
            batch=result['time_batch_steps'];expected=[min(i+batch,settings.time_steps) for i in range(0,settings.time_steps,batch)]
            observed=[round(f*settings.time_steps) for f in fractions]
            if observed!=expected:raise RuntimeError('Missing/truncated core integration nodes')
            record.update(status='completed',actual_time_steps=observed[-1],time_batch_steps=batch,all_steps_observed=True)
            return result
        except Exception as exc:
            record.update(status='failed',error=f'{type(exc).__name__}: {exc}');raise
        finally:record['wall_s']=time.perf_counter()-start


def transform(runtime,probe=False,source_order=None):
    out=deepcopy(runtime)
    if probe:out['machine']['sources'][0]['x_mm']+=10.
    if source_order is not None:
        for source in out['machine']['sources']:source['profile']['sampling_order']=source_order
    return out


def metrics(result):
    field=result['field_nm'];valid=np.isfinite(field);radius=float(np.max(result['x']))
    weights,coverage=clipped_cell_weights(result['x'],valid,radius)
    iw,ic=roi_weights(result['x'],valid,.9*radius)
    def cv(w):
        h=field[valid];p=w[valid];mean=float(np.dot(p,h));return math.sqrt(float(np.dot(p,(h-mean)**2)))/mean*100.,mean
    cv_full,mu=cv(weights);cv_interior,imu=cv(iw)
    return {'cv_percent':cv_full,'area_mean_nm':mu,'represented_area_fraction':coverage,
        'interior135_cv_percent':cv_interior,'interior135_area_mean_nm':imu,'interior135_coverage':ic}


def run_one(runtime,native,dt,grid,mode,observer,wall_cancel_s=None,probe=False,source_order=None):
    runtime=transform(runtime,probe,source_order);timing=capped_timing(runtime['profile'],dt)
    settings=replace(native,time_steps=timing['time_steps'],grid_size=grid)
    cancel=threading.Event();timer=None
    if wall_cancel_s is not None:
        timer=threading.Timer(wall_cancel_s,cancel.set);timer.start()
    observer.active_cap=dt;offset=len(observer.records);start=time.perf_counter()
    old_process=process_simulator.simulate;old_periodic=periodic_integration.simulate
    # Temporary in-memory dependency injection, never source-file edits. It
    # avoids the public wrapper's backend-memory SQLite persistence.
    process_simulator.simulate=observer.simulate;periodic_integration.simulate=observer.simulate
    try:
        result=process_simulator.simulate_process(settings,runtime,backend='CPU',cancel_event=cancel,
            fast_cycle=False,finite_periodic=(mode=='finite_periodic'))
        out={'mode':mode,'grid':grid,'requested_dt_s':dt,'probe':probe,'source_order':source_order,
            'timing':timing,'wall_s':time.perf_counter()-start,'core_calls':len(observer.records)-offset,
            'core_audits':observer.records[offset:],'metrics':metrics(result),
            'total_duration_s':result['total_duration_s'],'total_target_nm':result['total_target_nm'],
            'computed_time_steps':result['computed_time_steps'],'step_results':result['step_results'],
            'status':'completed','field_nm':result['field_nm'],'x':result['x'],'y':result['y']}
        if result['total_duration_s']!=timing['total_duration_s'] or len(result['step_results'])!=len(runtime['profile']['steps']):raise RuntimeError('Process truncated')
        return out
    finally:
        process_simulator.simulate=old_process;periodic_integration.simulate=old_periodic
        if timer:timer.cancel()


def save_result(name,result):
    out=dict(result);arrays={k:out.pop(k) for k in ('field_nm','x','y')}
    np.savez(HERE/(name+'.npz'),**arrays)
    (HERE/(name+'.json')).write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')


def plan(config):
    snapshot,runtime,native=load_inputs(config)
    inventory=[]
    for path in sorted((PRODUCT/'data/processes').glob('*.json')):
        p=json.loads(path.read_text());dur=[s['target_nm']/s['rate_nm_s'] for s in p['steps']]
        inventory.append({'path':str(path.relative_to(WORKSPACE)),'sha256':sha(path),'name':p['name'],
            'layers':len(dur),'total_duration_s':math.fsum(dur),
            'classification':'demo/software-validation files; not substituted for recovered native input'})
    selected={'recovered_file':config['source_recovered_snapshot_relative'],'recovered_file_sha256':config['source_recovered_snapshot_sha256'],
        'process_canonical_sha256':config['complete_process_canonical_sha256'],
        'all_dependency_canonical_hashes_verified':True,'snapshot_files':[{k:r[k] for k in ('kind','path','sha256')} for r in snapshot['files']],
        'layer_durations_s':[s['target_nm']/s['rate_nm_s'] for s in runtime['profile']['steps']],
        'total_duration_s':sum(s['target_nm']/s['rate_nm_s'] for s in runtime['profile']['steps']),
        'native_settings':asdict(native),'machine_geometry':runtime['machine'],
        'sampling_plans':{str(dt):capped_timing(runtime['profile'],dt) for dt in [.05,.025,.0125]},
        'pre_pilot_estimate_s':{'grid21_direct_dt.05':[40,80],'native_grid300_direct_dt.05':'hours, to be refined from measured complete pilot'},
        'historical_identity':old_identity(),'product_python_identity':source_hashes()}
    (HERE/'selected_input_manifest.json').write_text(json.dumps(selected,indent=2)+'\n')
    (HERE/'input_inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    (HERE/'input_snapshot.json').write_bytes(canonical_json_bytes(snapshot))
    print(json.dumps({k:selected[k] for k in ('recovered_file_sha256','process_canonical_sha256','layer_durations_s','total_duration_s','sampling_plans','pre_pilot_estimate_s')},indent=2),flush=True)


def pilot(config):
    snapshot,runtime,native=load_inputs(config);observer=CoreObserver()
    try:
        result=run_one(runtime,native,.05,21,'direct',observer,config['pilot']['wall_cancel_s'])
        save_result('pilot_direct_005_g21',result)
        estimate={'complete_pilot_wall_s':result['wall_s'],'actual_core_calls':result['core_calls'],
            'native_grid300_direct_005_rough_s':result['wall_s']*(300/21)**2,
            'grid21_direct_0025_rough_s':result['wall_s']*2,
            'grid21_direct_00125_rough_s':result['wall_s']*4,
            'basis':'Whole measured process, square-grid/time linear-work extrapolation; planning only'}
        (HERE/'pilot_costs.json').write_text(json.dumps(estimate,indent=2)+'\n')
        print(json.dumps({'pilot_status':'complete','metrics':result['metrics'],**estimate},indent=2),flush=True)
    except Exception as exc:
        failed={'status':'failed_or_cancelled','error':f'{type(exc).__name__}: {exc}','core_audits':observer.records,
                'no_recipe_simplification':True}
        (HERE/'pilot_failure.json').write_text(json.dumps(failed,indent=2)+'\n');print(json.dumps(failed),flush=True);raise
    manifest=json.loads((HERE/'selected_input_manifest.json').read_text())
    assert old_identity()==manifest['historical_identity'] and source_hashes()==manifest['product_python_identity']


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--pilot',action='store_true');args=ap.parse_args()
    cfg=json.loads((HERE/'config.json').read_text());pilot(cfg) if args.pilot else plan(cfg)
