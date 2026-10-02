"""Portable file-protocol device runner. Plan only by default; no remote/GPU claims.

Actual high-fidelity bundles must be produced and validated on the device. The
runner never labels T02's old fixed kernel as the corrected continuous oracle.
"""
from pathlib import Path
from dataclasses import asdict
import argparse,json,hashlib,math
from geometry import Design,Manufacturing,digest
from contracts import ErrorSource
from oracle import Ray,RayBundle,RayOracle
from chunked_oracle import ChunkedRayOracle
from optimizer import Search,Limits,atomic_json,WORK_KEYS
ROOT=Path(__file__).resolve().parents[1]


def estimate_job(job):
    w=job['work_shape']; ints=('candidate_count','point_count','time_panels','vapor_source_nodes','ion_source_nodes','max_opaque_cells')
    if any(type(w[k]) is not int or w[k]<1 for k in ints): raise ValueError('positive integer work shape required')
    rays=w['candidate_count']*w['point_count']*w['time_panels']*(w['vapor_source_nodes']+w['ion_source_nodes'])
    # Bundle list is materialized; no unsupported streaming/memory promise.
    # Python object overhead is environment-dependent, so byte range is a plan.
    chunk_size=w.get('point_chunk_size',w['point_count'])
    if type(chunk_size) is not int or not 1<=chunk_size<=w['point_count']: raise ValueError('valid point chunk size required')
    chunks=math.ceil(w['point_count']/chunk_size)
    bundle_rays=chunk_size*w['time_panels']*(w['vapor_source_nodes']+w['ion_source_nodes']);low=bundle_rays*192;high=bundle_rays*768
    return {'evaluations':w['candidate_count'],'rays':rays,'source_samples':rays,'point_time_samples':w['candidate_count']*w['point_count']*w['time_panels'],'time_panels':w['candidate_count']*w['time_panels']*chunks,'plate_tests':rays*w['max_opaque_cells'],'largest_chunk_base_bytes_estimate_range':[low,high],'point_chunks':chunks,'parse_copy_cache_peak_multiplier_unmeasured':[2,6], 'visibility_cache_note':'cache is per-oracle in memory, LRU default 16 geometry entries; plan peak must include up to min(candidate_count,16) visibility object lists; lower max_entries for constrained RAM', 'wall_seconds':'unknown_until_device_benchmark','gpu_speedup':'not_measured'}


def plan(config,workers):
    if type(workers) is not int or not 1<=workers<=4: raise ValueError('1..4 local workers required')
    jobs=[{'job_id':j['job_id'],'fidelity':j['fidelity'],'status':'not_run_awaiting_device','work':estimate_job(j),'required_inputs':j['inputs'],'acceptance':j['acceptance']} for j in config['jobs']]
    if len({j['job_id'] for j in jobs})!=len(jobs): raise ValueError('unique job IDs required')
    return {'schema':'T03-device-plan-v1','status':'plan_only','config_sha256':digest(config),'jobs':jobs,'total_nominal_rays':sum(j['work']['rays'] for j in jobs),'workers':workers,'execution_backend':'Python serial or bounded ThreadPoolExecutor; no GPU implementation claimed','prerequisites':config['prerequisites'],'physical_certification':False}


def checked_json(base,entry):
    if not entry.get('path') or not entry.get('sha256'): raise ValueError('device input path and exact SHA-256 required; no placeholder execution')
    p=(base/entry['path']).resolve()
    if not p.is_relative_to(base.resolve()): raise ValueError('input must remain within approved device input directory')
    raw=p.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=entry['sha256']: raise ValueError('input digest mismatch')
    return json.loads(raw)


def bundle_from_dict(b):
    errors=tuple(ErrorSource(**{**e,'points':tuple(e.get('points',[])),'time_window_s':tuple(e['time_window_s']) if e.get('time_window_s') else None}) for e in b['errors'])
    rays=tuple(Ray(**{**r,'source':tuple(r['source']),'target':tuple(r['target'])}) for r in b['rays'])
    return RayBundle(**{**b,'rays':rays,'errors':errors,'area_weights':tuple(b['area_weights']),'time_weights_s':tuple(b['time_weights_s'])})


def import_t02_evidence(data):
    """Read T02 device point JSON. Evidence only, not interchangeable objective data."""
    return {'point_id':data.get('point_id'),'status':data.get('status','unknown'),'reference_checks':data.get('assessment',{}).get('reference_checks',{}),'strict_certificate':False,'global_status':'partial_unchanged','usable_as_certified_optimizer_oracle':False,'reason':'T02 estimated reference/event agreement cannot upgrade candidate-local certified error bounds'}


def validate_source_counts(bundle,shape):
    counts={(ch,pt,ti):0 for ch in ('vapor','ion') for pt in range(len(bundle.area_weights)) for ti in range(len(bundle.time_weights_s))}
    for r in bundle.rays: counts[r.channel,r.point,r.time]+=1
    if any(v!=shape[ch+'_source_nodes'] for (ch,pt,ti),v in counts.items()): raise ValueError('source node count changed')


def execute(config,input_root,output,workers=1,allow_parallel=False,resume=False,cancel_file=None):
    p=plan(config,workers)
    if workers>1 and not allow_parallel: raise ValueError('parallel execution requires --allow-parallel')
    if p['total_nominal_rays']>config['global_ray_reservation_limit']: raise ValueError('planned total exceeds global ray reservation limit')
    base=Path(input_root);dest=Path(output);dest.mkdir(parents=True,exist_ok=True);completed=[]
    cancel=(lambda:Path(cancel_file).exists()) if cancel_file else (lambda:False)
    for job in config['jobs']:
        if cancel(): break
        if not job.get('device_ready',False): raise ValueError(job['job_id']+': inputs not marked device_ready')
        if not job['job_id'].replace('_','').replace('-','').isalnum(): raise ValueError('safe job_id required')
        dd=checked_json(base,job['inputs']['designs']);designs=[Design.from_dict(d) for d in dd]
        shape=job['work_shape']
        chunk_entries=job['inputs'].get('ray_bundle_chunks')
        if chunk_entries:
            if sum(e['point_count'] for e in chunk_entries)!=shape['point_count'] or any(e['point_count']>shape.get('point_chunk_size',shape['point_count']) or e['time_panels']!=shape['time_panels'] or e['ray_count']!=e['point_count']*e['time_panels']*(shape['vapor_source_nodes']+shape['ion_source_nodes']) for e in chunk_entries): raise ValueError('chunk metadata does not match planned shape')
            def load_chunk(index):
                bundle=bundle_from_dict(checked_json(base,chunk_entries[index]))
                validate_source_counts(bundle,shape)
                return bundle
            oracle=ChunkedRayOracle(chunk_entries,load_chunk,job['objectives'])
        else:
            bd=checked_json(base,job['inputs']['ray_bundle']);bundle=bundle_from_dict(bd)
            if len(bundle.area_weights)!=shape['point_count'] or len(bundle.time_weights_s)!=shape['time_panels']: raise ValueError('actual bundle does not match shape')
            validate_source_counts(bundle,shape)
            oracle=RayOracle(bundle,**job['objectives'])
        if len(designs)!=shape['candidate_count']: raise ValueError('candidate count changed')
        if any(sum(sum(p.bits) for p in d.plates)>shape['max_opaque_cells'] for d in designs): raise ValueError('plate test estimate exceeded')
        mfg=Manufacturing(**job.get('manufacturing',{}));limits=Limits(**job['limits'])
        estimated=estimate_job(job)
        if any(estimated[k]>getattr(limits,k) for k in WORK_KEYS): raise ValueError('job workload exceeds configured limits')
        checkpoint=dest/job['job_id']/'checkpoint.json'
        search=Search(designs,oracle,mfg,limits,checkpoint,lambda e:print(json.dumps({'job_id':job['job_id'],**e}),flush=True),cancel,workers,allow_parallel)
        if resume and checkpoint.exists(): search.restore()
        result=search.run();result['device_job_id']=job['job_id'];result['fidelity_label']=job['fidelity'];result['device_protocol_config_sha256']=digest(config)
        atomic_json(dest/job['job_id']/'results.json',result);completed.append({'job_id':job['job_id'],'status':result['execution_status'],'decision':result['decision_status']})
        atomic_json(dest/'execution_manifest.json',{'schema':'T03-device-results-v1','jobs':completed,'requested_jobs':len(config['jobs']),'config_sha256':digest(config),'gpu_executed':False,'physical_certification':False})
    return completed


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',default=str(ROOT/'verification/device_validation_plan.json'));ap.add_argument('--execute',action='store_true');ap.add_argument('--input-root',default=str(ROOT/'device_inputs'));ap.add_argument('--output',default=str(ROOT/'device_results'));ap.add_argument('--workers',type=int,default=1);ap.add_argument('--allow-parallel',action='store_true');ap.add_argument('--resume',action='store_true');ap.add_argument('--cancel-file');args=ap.parse_args()
    config=json.loads(Path(args.config).read_text());print(json.dumps(plan(config,args.workers),indent=2))
    if args.execute: execute(config,args.input_root,args.output,args.workers,args.allow_parallel,args.resume,args.cancel_file)
if __name__=='__main__': main()
