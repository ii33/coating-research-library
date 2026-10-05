"""Latest user dt ceiling, measured core step counts, unchanged historical files."""
from dataclasses import asdict
from pathlib import Path
import argparse
import hashlib
import json
import math
import sys
import time

import numpy as np

HERE=Path(__file__).resolve().parent
FIRST=HERE.parent
FOLLOW=FIRST/'convergence_followup'
sys.path.insert(0,str(FOLLOW))
from run_followup import FollowupEvaluator, get_cases, source_hashes, first_round_identity
from evaluator import _simulate_on_backend


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def historical_identity():
    out={}
    for prefix,root in (('first',FIRST),('followup',FOLLOW)):
        manifest=root/'results/artifact_manifest.json' if prefix=='first' else root/'artifact_manifest.json'
        m=json.loads(manifest.read_text())
        for n,digest in m['files'].items():
            if sha(root/n)!=digest:
                raise RuntimeError(f'Historical artifact changed: {prefix}/{n}')
            out[f'{prefix}/{n}']=digest
        out[f'{prefix}/manifest']=sha(manifest)
    return out


def steps_for_cap(duration_s,requested_dt_s,ceiling=.05):
    if not math.isfinite(requested_dt_s) or not 0<requested_dt_s<=ceiling:
        raise ValueError('Requested time step exceeds the user ceiling, or is invalid')
    if not math.isfinite(duration_s) or duration_s<=0:
        raise ValueError('Invalid duration')
    count=math.ceil(duration_s/requested_dt_s)
    actual=duration_s/count
    if actual>requested_dt_s*(1+1e-14) or actual>ceiling*(1+1e-14):
        raise RuntimeError('Actual step does not satisfy the ceiling')
    return count,actual


def observed_cpu(settings,mask,xp,device,cancel,positions,weights,**kwargs):
    progress=[]
    result=_simulate_on_backend(settings,mask,xp,device,cancel,positions,weights,
                                progress=progress.append,**kwargs)
    batch=result['time_batch_steps']
    expected=[min(start+batch,settings.time_steps) for start in range(0,settings.time_steps,batch)]
    observed=[round(f*settings.time_steps) for f in progress]
    if observed!=expected or observed[-1]!=settings.time_steps:
        raise RuntimeError('Core batch progress does not cover every requested time step')
    result['integration_audit']={'actual_time_steps':observed[-1],
        'duration_s':settings.duration_s,'actual_dt_s':settings.duration_s/observed[-1],
        'time_batch_steps':batch,'progress_batches':len(progress),
        'all_requested_steps_observed':True,'final_partial_batch_steps':expected[-1]-(expected[-2] if len(expected)>1 else 0)}
    return result


class GateEvaluator(FollowupEvaluator):
    def __init__(self,config,requested_dt):
        count,self.actual_dt=steps_for_cap(config['duration_s'],requested_dt,config['max_engineering_reference_time_step_s'])
        super().__init__({'grid_size':config['grid_size'],'time_steps':count,'source_order':config['source_order']})
        if self.settings.duration_s!=config['duration_s']:
            raise RuntimeError('Core duration and gate duration differ')
        self.forward=observed_cpu

    def evaluate(self,*args,**kwargs):
        row=super().evaluate(*args,**kwargs)
        if row['valid']:
            row['integration_audits']=[r['integration_audit'] for r in self.results]
            row['actual_dt_s']=self.actual_dt
            row['time_step_gate_pass']=all(a['actual_dt_s']<=.05 and a['all_requested_steps_observed'] for a in row['integration_audits'])
        return row


def inputs(config):
    first=json.loads((FIRST/'results/study_results.json').read_text())
    return get_cases(config,first)


def pilot(config):
    history=historical_identity();sources=source_hashes()
    case=inputs(config)[1]
    ev=GateEvaluator(config,config['pilot_requested_dt_s'])
    start=time.perf_counter();row=ev.evaluate(case['designs']['nominal'])
    output={'config_sha256':sha(HERE/'config.json'),'requested_dt_s':config['pilot_requested_dt_s'],
        'row':row,'counter':asdict(ev.counter),'wall_s':time.perf_counter()-start,
        'historical_identity':history,'product_python_identity':sources}
    assert historical_identity()==history and source_hashes()==sources
    (HERE/'pilot_results.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({'pilot_actual_calls':ev.counter.forward_calls,'wall_s':output['wall_s'],
        'actual_dt_s':row['actual_dt_s'],'actual_steps':row['integration_audits'][0]['actual_time_steps']},indent=2))


def main(config):
    pilot=json.loads((HERE/'pilot_results.json').read_text())
    history=historical_identity();sources=source_hashes()
    if history!=pilot['historical_identity'] or sources!=pilot['product_python_identity']:
        raise RuntimeError('Historical inputs changed after pilot')
    cases=inputs(config)
    count=len(cases)*2*(config['holdout_count']+1)
    estimate=pilot['wall_s']*sum(steps_for_cap(config['duration_s'],dt)[0]/960 for dt in config['requested_time_steps_s'])*count
    if estimate>config['main_soft_wall_allowance_s'] or len(config['requested_time_steps_s'])*count*2>config['main_actual_forward_call_cap']:
        raise RuntimeError('Pilot cannot justify the predeclared bounded check')
    start=time.perf_counter();levels=[];calls=0
    for dt in config['requested_time_steps_s']:
        data=[]
        for case in cases:
            methods={}
            for mode in ('nominal','robust'):
                ev=GateEvaluator(config,dt)
                nominal=ev.evaluate(case['designs'][mode])
                rows=[ev.evaluate(case['designs'][mode],z,case['level']) for z in case['holdout']]
                if not all(r['valid'] and r['time_step_gate_pass'] for r in [nominal]+rows):
                    raise RuntimeError('An actual forward or time-step gate failed')
                methods[mode]={'nominal':nominal,'rows':rows,
                    'mean_cv_percent':float(np.mean([r['cv_percent'] for r in rows])),
                    'mean_interior90_cv_percent':float(np.mean([r['interior90_cv_percent'] for r in rows])),
                    'counter':asdict(ev.counter),'failures':ev.failures}
                calls+=ev.counter.forward_calls
            data.append({'seed':case['seed'],'level':case['level'],
                'holdout_sha256':case['holdout_sha256'],'methods':methods})
        levels.append({'requested_dt_s':dt,'actual_dt_s':config['duration_s']/steps_for_cap(config['duration_s'],dt)[0],
            'actual_time_steps':steps_for_cap(config['duration_s'],dt)[0],'cases':data})
        print(json.dumps({'requested_dt_s':dt,'actual_time_steps':levels[-1]['actual_time_steps'],
            'actual_dt_s':levels[-1]['actual_dt_s'],'cumulative_actual_calls':calls}),flush=True)
    result={'config':config,'levels':levels,'pilot_actual_calls':pilot['counter']['forward_calls'],
        'main_actual_calls':calls,'wall_s':time.perf_counter()-start,
        'pilot_estimated_wall_s':estimate,'historical_unchanged':historical_identity()==history,
        'product_python_unchanged':source_hashes()==sources,'engineering_ranking_allowed':False,
        'status':'short_window_time_step_diagnostic_completed_not_engineering_comparison'}
    assert result['historical_unchanged'] and result['product_python_unchanged']
    (HERE/'gate_results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'main_actual_calls':calls,'wall_s':result['wall_s'],'engineering_ranking_allowed':False},indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--pilot',action='store_true');args=ap.parse_args()
    cfg=json.loads((HERE/'config.json').read_text());pilot(cfg) if args.pilot else main(cfg)
