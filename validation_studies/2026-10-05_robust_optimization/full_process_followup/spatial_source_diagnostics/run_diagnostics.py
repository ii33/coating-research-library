from pathlib import Path
import argparse
import json
import sys
import time
import numpy as np

HERE=Path(__file__).resolve().parent;BASE=HERE.parent
sys.path.insert(0,str(BASE))
from run_full_process import load_inputs,run_one,CoreObserver,old_identity,source_hashes
from run_convergence import compare,serial


def save(name,row):
    np.savez(HERE/(name+'.npz'),**{k:row[k] for k in ('field_nm','x','y')})
    (HERE/(name+'.json')).write_text(json.dumps(serial(row),indent=2)+'\n')


def load_at(root,name):
    out=json.loads((root/(name+'.json')).read_text())
    with np.load(root/(name+'.npz')) as f:out.update({k:f[k].copy() for k in ('field_nm','x','y')})
    return out


def pilot(cfg):
    base=json.loads((BASE/'config.json').read_text());snapshot,runtime,native=load_inputs(base)
    old=old_identity();sources=source_hashes();obs=CoreObserver(cfg['pilot_call_cap'])
    row=run_one(runtime,native,cfg['requested_periodic_dt_s'],41,'finite_periodic',obs,90.)
    save('pilot_g41',row)
    # Source ray-work uses the actual two physical layer durations as weights.
    # This is a cost model, not accuracy evidence or a promised duration.
    ratio={5:(21*7000+25*3888.888888889)/(12*7000+16*3888.888888889),
           7:(37*7000+49*3888.888888889)/(12*7000+16*3888.888888889),
           9:(69*7000+81*3888.888888889)/(12*7000+16*3888.888888889)}
    grid_remaining=row['wall_s']*(1+2*(61/41)**2)
    source_estimate=row['wall_s']*2*sum(ratio.values())
    plan={'pilot_complete_wall_s':row['wall_s'],'pilot_actual_calls':row['core_calls'],
          'estimated_remaining_wall_s':grid_remaining+source_estimate,
          'estimated_remaining_actual_calls':36,
          'cost_basis':'Actual complete grid41 periodic pilot; squared-grid and duration-weighted source-node work scaling, approximate only',
          'source_work_ratios':ratio,'historical_identity':old,'product_python_identity':sources}
    assert old_identity()==old and source_hashes()==sources
    (HERE/'pilot_plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps(plan,indent=2),flush=True)


def main(cfg):
    plan=json.loads((HERE/'pilot_plan.json').read_text())
    if plan['estimated_remaining_wall_s']>cfg['main_soft_wall_allowance_s']:
        raise RuntimeError('Measured pilot does not justify this whole bounded ladder')
    base=json.loads((BASE/'config.json').read_text());snapshot,runtime,native=load_inputs(base)
    old=old_identity();sources=source_hashes();prior_audits=[];prior_wall=0.;results={}
    saved=HERE/'diagnostic_results.json'
    if saved.exists():
        previous=json.loads(saved.read_text())
        prior_audits=previous.get('core_audits',[]);prior_wall=previous.get('wall_s',0.)
        results={name:load_at(HERE,name) for name in previous.get('results',{})}
    observer=CoreObserver(cfg['main_call_cap']-len(prior_audits));start=time.perf_counter();rows={};checks=[]
    observer.cancel_file=HERE/'cancel_on_input_change.flag'
    def checkpoint(status):
        out={'config':cfg,'status':status,'results':{k:serial(v) for k,v in results.items()},'checks':checks,
            'actual_core_calls':len(prior_audits)+len(observer.records),'core_audits':prior_audits+observer.records,'wall_s':prior_wall+time.perf_counter()-start,
            'resumed_completed_core_calls':len(prior_audits),'postprocessing_resume_preserves_saved_fields':True,
            'historical_unchanged':old_identity()==old,'product_python_unchanged':source_hashes()==sources,
            'joint_direct_gate':'not_run','engineering_ranking_allowed':False}
        (HERE/'diagnostic_results.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    def run(name,grid,probe,order=None):
        if name in results:return results[name]
        row=run_one(runtime,native,cfg['requested_periodic_dt_s'],grid,'finite_periodic',observer,
            cfg['main_soft_wall_allowance_s']-prior_wall-(time.perf_counter()-start),probe,order)
        save(name,row);results[name]=row;checkpoint('running_complete_process_diagnostics')
        print(json.dumps({'name':name,'wall_s':row['wall_s'],'calls':row['core_calls'],
            'full_duration_s':row['total_duration_s'],'cv_percent':row['metrics']['cv_percent']}),flush=True)
        return row
    finer=BASE/'continued_00625/periodic_finer'
    try:
        for probe in (False,True):
            chain=[load_at(finer,'periodic_0.0015625_'+str(int(probe)))]
            chain.append(load_at(HERE,'pilot_g41') if not probe else run('grid41_probe',41,True))
            chain.append(run(f'grid61_{int(probe)}',61,probe))
            rows['grid_'+str(int(probe))]=chain
            for a,b in zip(chain[:-1],chain[1:]):checks.append({'axis':'grid','probe':probe,'levels':[a['grid'],b['grid']],**compare(a,b)})
        for probe in (False,True):
            chain=[run(f'source_q{q}_{int(probe)}',41,probe,q) for q in cfg['source_ladder']]
            rows['source_'+str(int(probe))]=chain
            for a,b in zip(chain[:-1],chain[1:]):checks.append({'axis':'source','probe':probe,'levels':[a['source_order'],b['source_order']],**compare(a,b)})
        for row in checks:
            row['map_screen_pass']=all(row[k]<cfg['metric_screens']['normalized_map_rms_pp'] for k in ('normalized_field_rms_pp','interior135_field_rms_pp'))
            row['cv_screen_pass']=all(row[k]<cfg['metric_screens']['cv_sensitivity_pp'] for k in ('cv_change_pp','interior135_cv_change_pp'))
        checkpoint('bounded_complete_process_grid_source_diagnostics_complete')
    except Exception as exc:
        checks.append({'blocker':f'{type(exc).__name__}: {exc}'});checkpoint('explicit_failure_no_recipe_simplification');raise
    print(json.dumps({'calls':len(prior_audits)+len(observer.records),'wall_s':prior_wall+time.perf_counter()-start,'checks':checks},indent=2),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--pilot',action='store_true');args=ap.parse_args()
    cfg=json.loads((HERE/'config.json').read_text());pilot(cfg) if args.pilot else main(cfg)
