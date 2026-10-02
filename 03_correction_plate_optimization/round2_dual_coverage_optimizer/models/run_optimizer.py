"""Runnable serial fixture search. Always plan-only unless --execute is explicit."""
from pathlib import Path
import argparse,json
from geometry import Plate,Design,Manufacturing,neighborhood
from oracle import SyntheticOracle
from optimizer import Search,Limits,atomic_json
ROOT=Path(__file__).resolve().parents[1]


def fixture():
    seed=Design((Plate('vapor_side',(1,0,1,0),2,2,.02,(-.03,0,.35),.002),Plate('ion_side',(1,0,1,0),2,2,.02,(.03,0,.65),.002)))
    candidates=list(neighborhood(seed,[.002,.004],[(0,.005),(0,-.005)],24))
    values={}
    for d in candidates:
        a,b=d.plates
        # Deliberately competing response: more shadow reduces throughput and
        # redistributes the two channel objectives differently. Fully invented.
        x=sum(a.bits);y=sum(b.bits)
        values[d.id]=[abs(.1*x-.2)+abs(a.center_m[0]+.03),abs(.08*y-.24)+abs(b.center_m[0]-.03),.5-(1-.06*(x+y))]
    return candidates,SyntheticOracle(values,.015),Manufacturing()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');ap.add_argument('--output',default=str(ROOT/'device_results/fixture'));ap.add_argument('--resume',action='store_true');ap.add_argument('--workers',type=int,default=1);ap.add_argument('--allow-parallel',action='store_true');ap.add_argument('--max-evaluations',type=int,default=30);ap.add_argument('--max-rays',type=int,default=10000);ap.add_argument('--cancel-file');args=ap.parse_args()
    candidates,oracle,mfg=fixture()
    if not 1<=args.workers<=4 or (args.workers>1 and not args.allow_parallel): ap.error('workers>1 requires --allow-parallel; maximum 4')
    plan={'status':'plan_only','candidate_count':len(candidates),'fixture_only':True,'workers':args.workers,'nominal_ray_upper_estimate':sum(oracle.estimate(d)['rays'] for d in candidates),'gpu_execution':False,'execute_required':True}
    if not args.execute: print(json.dumps(plan,indent=2));return
    out=Path(args.output);limits=Limits(evaluations=args.max_evaluations,rays=args.max_rays)
    cancel=(lambda:Path(args.cancel_file).exists()) if args.cancel_file else None
    def progress(event): print(json.dumps(event),flush=True)
    search=Search(candidates,oracle,mfg,limits,out/'checkpoint.json',progress,cancel,args.workers,args.allow_parallel)
    if args.resume: search.restore()
    result=search.run();atomic_json(out/'results.json',result);print(json.dumps({'status':result['execution_status'],'decision':result['decision_status'],'output':str(out/'results.json')}))
if __name__=='__main__':main()
