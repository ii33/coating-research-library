"""Complete resumable local finite-enclosure job driver; default plan_only.
No remote process, credential, hardware, network, scheduler or quota bypass.
Execution requires a reviewed --execute flag, explicit output and max jobs.
"""
import argparse,json,platform,time
from bounded_optics import *
def plan():
    c=load_case()
    jobs=[{'variant':v,'scale':s,'cells':n} for n in [8,32,128,512] for v,s in c['variants'].items()]
    return {'mode':'plan_only','algorithm':'shared-latent interval subdivision, not Monte Carlo','jobs':jobs,'maximum_leaf_optical_calls':sum(j['cells']*3 for j in jobs),'target':'one synthetic MIR 3-node operator, no spectrum sweep','prerequisites':['explicit device/compute authorization','actual film data needed for any physical claim','formal DeepSeek / Seed / Sol reviews pending'],'heavy_run':'not_run','checkpoint_binding':digest({'case':c,'jobs':jobs}),'host':platform.node(),'external_execution':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--output');p.add_argument('--max-jobs',type=int);a=p.parse_args();cfg=plan()
    if not a.execute:
        print(json.dumps(cfg,indent=2));return
    if not a.output or a.max_jobs is None or not 1<=a.max_jobs<=len(cfg['jobs']):p.error('execution needs --output and --max-jobs 1..12')
    target=Path(a.output).resolve()
    if ROOT not in target.parents:raise ValueError('output_must_stay_inside_package')
    c=load_case();r=next(x for x in json.loads((ROOT/'data/legacy_selection.json').read_text())['records'] if x['id']==c['recipe_id'])
    done={'checkpoint_binding':cfg['checkpoint_binding'],'mode':'executed_conditional_only','jobs':[]}
    if target.exists():
        done=json.loads(target.read_text())
        if done['checkpoint_binding']!=cfg['checkpoint_binding']:raise ValueError('incompatible_resume')
    for i,j in enumerate(cfg['jobs'][:a.max_jobs]):
        if i<len(done['jobs']):continue
        t=time.monotonic();out=propagate(r,c['bridge'],c['material'],c['measurement'],j['scale'],j['cells'])
        done['jobs'].append({'plan':j,'seconds':time.monotonic()-t,'result':out});target.write_text(json.dumps(done,indent=2)+'\n')
    print(json.dumps({'completed_jobs':len(done['jobs']),'physical_certification':False}))
if __name__=='__main__':main()
