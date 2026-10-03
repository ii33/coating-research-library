"""Fully implemented synthetic inverse-diagnostic driver; default plan_only.
Large execution is intentionally not run in this package. No GPU or device launch.
Outputs preserve convergence failures and all starts; never certify global uniqueness.
"""
from pathlib import Path
import argparse,itertools,json
import numpy as np
from measurement import observe
from identifiability import jacobian,rank_report,fit_multistart,profile_parameter
from scenarios import record,covariance,SCALES,BOUNDS
ROOT=Path(__file__).resolve().parents[1]

def configuration(small=False):
    return {'truth_n':[1.8] if small else [1.5,1.8,2.1],
            'truth_k':[.02] if small else [.001,.02,.1],
            'truth_d_um':[.1] if small else [.05,.1,.3],
            'wavelengths_um':[.55] if small else np.linspace(.42,.98,29).tolist(),
            'angles_deg':[60.] if small else [40.,55.,70.],
            'starts':1 if small else 12,'profile_points':2 if small else 61,
            'monte_carlo':1 if small else 200,'max_nfev':20 if small else 400,
            'seed':271828,'modes':['RT_plus_d'] if small else ['RT','ellipsometry','joint','RT_plus_d'],
            'data_evidence':'synthetic_only','actual_hardware':None}

def make_records(c,mode):
    if mode not in ['RT','ellipsometry','joint','RT_plus_d']:raise ValueError('unknown measurement mode')
    out=[]
    for w,a in itertools.product(c['wavelengths_um'],c['angles_deg']):
        if mode in ['RT','joint','RT_plus_d']:
            out.extend(record(k,w,a,p) for p in ['s','p'] for k in ['R','T'])
        if mode in ['ellipsometry','joint']:out.append(record('rho_reim',w,a))
    if mode=='RT_plus_d':out.append(record('d_geo'))
    return out

def plan(c):
    truths=len(c['truth_n'])*len(c['truth_k'])*len(c['truth_d_um'])
    jobs=truths*len(c['modes'])*c['starts']*(1+c['profile_points']+c['monte_carlo'])
    return {'status':'plan_only','execution_status':'not_run_awaiting_device','configuration':c,
            'truth_cases':truths,'least_squares_start_jobs':jobs,
            'estimated_max_nfev_total':jobs*c['max_nfev'],
            'estimate_caveat':'nfev is not exact optical-call count; finite-difference Jacobians add evaluations',
            'algorithms_implemented':['weighted_multistart_bounded_fit','conditional_finite_difference_SVD',
                                      'thickness_profile_with_nk_refit','fixed_seed_parametric_Monte_Carlo'],
            'global_certificate':False,'actual_device_or_measurements_used':False,'heavy_run':False}

def execute(c,output,max_jobs):
    output=Path(output).resolve()
    if not output.is_relative_to(ROOT):raise ValueError('output must stay inside this research increment')
    if output.exists():raise ValueError('refuse overwrite; choose a new run directory')
    if plan(c)['least_squares_start_jobs']>max_jobs:raise ValueError('explicit max_jobs budget is below planned work')
    output.mkdir(parents=True);rng=np.random.default_rng(c['seed']);summaries=[]
    for case_id,truth in enumerate(itertools.product(c['truth_n'],c['truth_k'],c['truth_d_um'])):
        for mode in c['modes']:
            rec=make_records(c,mode);f=lambda t:observe(t,rec);y=f(truth);C=covariance(rec);L=np.linalg.cholesky(C)
            starts=rng.uniform(BOUNDS[0],BOUNDS[1],size=(c['starts'],3))
            # Small routing fixture uses known truth only; large starts never receive truth as a seed.
            if c['starts']==1 and len(c['truth_n'])==1:starts[0]=truth
            fit=fit_multistart(f,y,C,starts,BOUNDS,SCALES,c['max_nfev'])
            profile=profile_parameter(f,y,C,starts,BOUNDS,SCALES,2,np.linspace(BOUNDS[0][2],BOUNDS[1][2],c['profile_points']),c['max_nfev'])
            mc=[]
            for draw in range(c['monte_carlo']):
                # Synthetic additive Gaussian coordinates; no clipping out-of-range noisy R/T.
                yy=y+L@rng.standard_normal(len(y))
                result=fit_multistart(f,yy,C,starts,BOUNDS,SCALES,c['max_nfev'])
                mc.append({'draw':draw,**result})
            J,scheme=jacobian(f,truth,SCALES,BOUNDS)
            result={'truth':list(truth),'mode':mode,'records':rec,'covariance':C.tolist(),'fit':fit,
                    'profile':profile,'monte_carlo':mc,'local_at_truth':rank_report(J,C),
                    'derivative_schemes':scheme,'synthetic_only':True,'production_qualified':False,
                    'model_misspecification_or_real_coverage_validated':False}
            name=f'case_{case_id:03d}_{mode}.json';(output/name).write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
            summaries.append({'path':name,'fit_converged':fit['best'] is not None,
                              'mc_converged':sum(x['best'] is not None for x in mc),'mc_total':len(mc)})
    receipt={'status':'synthetic_execution_completed','configuration':c,'cases':summaries,
             'real_device_validation':'not_run_awaiting_device','global_minimum_certified':False}
    (output/'run_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--tiny',action='store_true')
    p.add_argument('--output',type=Path);p.add_argument('--max-jobs',type=int,default=0);a=p.parse_args();c=configuration(a.tiny)
    if a.execute:
        if a.output is None:p.error('--execute requires an explicit new --output directory')
        result=execute(c,a.output,a.max_jobs)
    else:result=plan(c)
    print(json.dumps(result,indent=2,allow_nan=False))
