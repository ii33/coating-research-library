"""Full conditional synthetic driver. Plan-only unless --execute plus budgets and new output.
No hardware/network access. Forward call budgets include numerical finite differences.
Results are per-model/per-loss; no automated winner or global uniqueness certificate.
"""
from pathlib import Path
import argparse,itertools,json,platform
import numpy as np
from inversion import Problem,Ledger,multistart,profile,heldout
from scenarios import build_case,make_problem,measurement_candidates
from design import assess_candidates
ROOT=Path(__file__).resolve().parents[1]


def configuration(tiny=False):
    return {'schema':'T08-R2-driver-v1','seed':20261002,'tiny_routing_only':tiny,
      'truths':[[1.8,.02,.1]] if tiny else [[1.6,.005,.06],[1.8,.02,.1],[2.2,.08,.3],[2.,0.,.8]],
      'scenarios':['clean'] if tiny else ['clean','single_outlier','dispersion_mismatch'],
      'candidates':['constant'] if tiny else ['constant','linear_n','constant_correlated_discrepancy'],
      'losses':['gaussian'] if tiny else ['gaussian','huber'],
      'starts':1 if tiny else 16,'profile_points':2 if tiny else 41,'replicates':0 if tiny else 100,
      'max_calls_per_start':45 if tiny else 1200,'max_nfev':10 if tiny else 300,
      'cluster_distance_scaled':.2,'retained_clusters':1 if tiny else 8,
      'profile_parameter':'d_um','jacobian_steps':[1e-4] if tiny else [5e-5,1e-4,2e-4],
      'fit_wavelengths_um':[.5,.65] if tiny else np.linspace(.42,.78,13).tolist(),
      'heldout_wavelengths_um':[.57] if tiny else [.455,.535,.615,.695,.85,.95],
      'angles_deg':[45.] if tiny else [10.,45.,65.],
      'actual_hardware':None,'data_evidence':'synthetic_only','heavy_run':'not_run_awaiting_device'}


def plan(c):
    cases=len(c['truths'])*len(c['scenarios']);variants=len(c['candidates'])*len(c['losses'])
    jobs=cases*variants*c['starts']*(1+c['profile_points']+c['replicates'])
    # Each retained representative: train/holdout calls + each h times central Jacobian (1+2p)
    # for training and 3 candidate sets. p<=6. Plus one generating call per case/split.
    diagnostic_ceiling=cases*(2+variants*c['retained_clusters']*(2+len(c['jacobian_steps'])*4*13))
    return {'status':'plan_only','configuration':c,'fit_start_jobs':jobs,
      'fit_forward_call_ceiling':jobs*c['max_calls_per_start'],
      'diagnostic_forward_call_ceiling':diagnostic_ceiling,
      'total_forward_call_ceiling':jobs*c['max_calls_per_start']+diagnostic_ceiling,
      'budget_unit':'one complete observation-vector prediction; optical node count also recorded',
      'coverage':'all truth/scenario/model/loss combinations, multistart, d profile, repeat-noise fits, heldout and conditional design',
      'global_minimum_certified':False,'formal_coverage_or_hardware_acceptance':False,
      'heavy_execution':'not_run_awaiting_device'}


def save(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def execute(c,output,max_jobs,max_forward_calls):
    output=Path(output).resolve();p=plan(c)
    if not output.is_relative_to(ROOT):raise ValueError('output must remain in this increment')
    if output.exists():raise ValueError('new output directory required; overwrite/resume not implicit')
    if max_jobs<p['fit_start_jobs'] or max_forward_calls<p['total_forward_call_ceiling']:
        raise ValueError('explicit budgets must cover declared worst-case plan')
    output.mkdir(parents=True);save(output/'execution_plan.json',p)
    ledger=Ledger(max_forward_calls);receipts=[];rng=np.random.default_rng(c['seed'])
    for case_index,(truth,scenario) in enumerate(itertools.product(c['truths'],c['scenarios'])):
        case=build_case(truth,scenario,c,ledger,rng);save(output/f'case_{case_index:03d}_observations.json',case)
        for candidate,loss in itertools.product(c['candidates'],c['losses']):
            problem=make_problem(case,candidate,loss)
            lo,hi=problem.bounds
            starts=rng.uniform(lo,hi,size=(c['starts'],len(lo)))
            # Only the explicitly tiny routing fixture uses truth seeding. Never infer recovery.
            if c['tiny_routing_only']:starts[0]=problem.default_point(np.asarray(truth))
            fit=multistart(problem,starts,c['max_calls_per_start'],c['max_nfev'],ledger,c['cluster_distance_scaled'])
            prof=profile(problem,starts,2,np.linspace(lo[2],hi[2],c['profile_points']),c,ledger)
            repeated=[]
            for draw in range(c['replicates']):
                # Repeated measurement noise; fixed discrepancy/outlier remains scenario-conditional.
                yy=np.asarray(case['fit_mean'])+np.linalg.cholesky(case['noise_covariance'])@rng.standard_normal(len(case['fit_y']))
                pp=make_problem({**case,'fit_y':yy.tolist()},candidate,loss)
                repeated.append({'draw':draw,**multistart(pp,starts,c['max_calls_per_start'],c['max_nfev'],ledger,c['cluster_distance_scaled'])})
            reps=[x['representative'] for x in fit['clusters'][:c['retained_clusters']]]
            validation=[]
            for representative in reps:
                x=np.asarray(representative['x'])
                validation.append({'x':x.tolist(),'optimizer_converged':representative['converged'],
                    'heldout':heldout(problem,x,case,ledger),
                    'conditional_measurement_design':assess_candidates(problem,x,measurement_candidates(),c['jacobian_steps'],ledger)})
            result={'case_index':case_index,'candidate':candidate,'loss':loss,'problem':problem.metadata(),
              'fit':fit,'profile':prof,'repeat_noise_fits':repeated,'validation':validation,
              'validation_not_used_to_select_model':True,'global_certificate':False}
            name=f'case_{case_index:03d}_{candidate}_{loss}.json';save(output/name,result)
            receipts.append({'file':name,'attempts':len(fit['attempts']),'discovered_clusters':len(fit['clusters']),
              'all_attempts_converged':all(a['converged'] for a in fit['attempts'])})
            save(output/'progress.json',{'completed':receipts,'ledger':ledger.as_dict(),'status':'running'})
    receipt={'status':'conditional_synthetic_execution_completed','tiny_routing_only':c['tiny_routing_only'],
      'jobs_planned':p['fit_start_jobs'],'jobs_attempted':ledger.starts,'ledger':ledger.as_dict(),'outputs':receipts,
      'real_hardware':'not_run_awaiting_device','heavy_run':not c['tiny_routing_only'],
      'production_qualified':False,'global_certificate':False,'python':platform.python_version()}
    save(output/'run_receipt.json',receipt);return receipt

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--execute',action='store_true');a.add_argument('--tiny',action='store_true')
    a.add_argument('--output',type=Path);a.add_argument('--max-jobs',type=int,default=0);a.add_argument('--max-forward-calls',type=int,default=0)
    args=a.parse_args();c=configuration(args.tiny)
    if args.execute and args.output is None:a.error('--execute requires --output')
    print(json.dumps(execute(c,args.output,args.max_jobs,args.max_forward_calls) if args.execute else plan(c),indent=2,allow_nan=False))
