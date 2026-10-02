"""Bounded two-parameter synthetic calibration and future resampling driver.
Local toy balance only: g=eta*F-Y*Gamma. No optical/stress/adhesion response model.
Heavy mode is opt-in and is NOT executed in this release.
"""
import argparse,json,math,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def fit(rows):
    # Predictor fluxes and response normalized by 1e18; units remain explicit in data.
    aa=ab=bb=ay=by=0.
    for r in rows:
        F,G,y,s=r['arrival'],r['energetic'],r['net'],r['sigma']
        if not all(math.isfinite(v) for v in (F,G,y,s)) or F<0 or G<0 or s<=0:raise ValueError('invalid observation')
        a,b,w=F,-G,1/s**2;aa+=w*a*a;ab+=w*a*b;bb+=w*b*b;ay+=w*a*y;by+=w*b*y
    trace=aa+bb;disc=math.hypot(aa-bb,2*ab);lmax=(trace+disc)/2
    det=aa*bb-ab*ab;lmin=det/lmax if lmax else 0.
    if len(rows)<3 or lmax<=0 or lmin<=1e-10*lmax:
        return {'status':'unidentifiable','eta':None,'yield_atoms_per_particle':None,'covariance':None,'condition_number':None,
         'reason':'Rank deficient or ill-conditioned weighted design; retain nulls, do not use pseudoinverse as calibration'}
    eta=(bb*ay-ab*by)/det;Y=(-ab*ay+aa*by)/det
    residual=[r['net']-eta*r['arrival']+Y*r['energetic'] for r in rows]
    return {'status':'synthetic_identifiable' if 0<=eta<=1 and Y>=0 else 'outside_toy_parameter_domain',
      'eta':eta,'yield_atoms_per_particle':Y,'covariance':[[bb/det,-ab/det],[-ab/det,aa/det]],
      'condition_number':lmax/lmin,'residuals':residual,'weighted_chi2':sum((e/r['sigma'])**2 for e,r in zip(residual,rows)),
      'degrees_of_freedom':len(rows)-2,'limits':'Known independent Gaussian observation sigma; predictors treated exact. Errors-in-variables, drift, composition evolution and sample transfer not identified.'}
def synthetic_data():
    design=[(1.,.2),(1.,.7),(2.,.2),(2.,.7),(1.5,.4),(1.2,.6),(1.8,.3),(1.4,.5)]
    noise=[.008,-.012,.004,.011,-.003,.005,-.007,-.006]
    return [{'arrival':F,'energetic':G,'net':.84*F-.32*G+e,'sigma':.02} for (F,G),e in zip(design,noise)]
def plan(replicates=100000):
    return {'status':'plan_only','execution':'not_run','jobs':[{'job_id':'future_calibration_resampling','bootstrap_replicates':replicates,'fit_parameters':2,
       'device':'user-selected device later, not selected or sampled','work_units':'one eight-row weighted fit per replicate',
       'resource_measurements':None,'inputs':'synthetic dataset by default; approved calibrated campaign required for physical inference',
       'exit_conditions':['all requested replicates written with exact seed and input hashes','validation failures retained','no production qualification']}],
       'prerequisites':['explicit approval for heavy execution and chosen resources','state/temperature/spectrum/history matched calibration data','full input covariance or errors-in-variables model where required'],
       'no_machine_sampling':True,'no_paid_compute':True,'physical_experiments':'plan_only/not_run'}
def bootstrap(rows,n,seed):
    # Parametric noise bootstrap conditional on exact predictors and known independent sigma.
    rng=random.Random(seed);base=fit(rows)
    if base['status']!='synthetic_identifiable':return {'status':'blocked','fit':base}
    vals=[];failures=0
    for _ in range(n):
        sim=[{**r,'net':base['eta']*r['arrival']-base['yield_atoms_per_particle']*r['energetic']+rng.gauss(0,r['sigma'])} for r in rows]
        f=fit(sim)
        if f['status']=='synthetic_identifiable':vals.append((f['eta'],f['yield_atoms_per_particle']))
        else:failures+=1
    def qs(a):
        a=sorted(a)
        return [a[int((len(a)-1)*p)] for p in (.025,.5,.975)] if a else [None]*3
    return {'status':'executed_synthetic_only','replicates':n,'seed':seed,'failed_fits':failures,
      'eta_quantiles':qs([v[0] for v in vals]),'yield_quantiles':qs([v[1] for v in vals]),'meaning':'conditional toy sampling; not actual material uncertainty'}
def light():
    rows=synthetic_data();fail=[{'arrival':float(i),'energetic':.5*i,'net':.68*i,'sigma':.02} for i in range(1,7)]
    return {'all_numbers_synthetic':True,'normalization':{'arrival':'1e18 atoms/m2/s','energetic':'1e18 particles/m2/s','net':'1e18 atoms/m2/s'},
     'rows':rows,'fit':fit(rows),'unidentifiable_rows':fail,'unidentifiable_fit':fit(fail),
     'truth':{'eta':.84,'yield_atoms_per_particle':.32},'not_inferred':['n','k','stress','adhesion','production_window'],
     'bootstrap_status':'not_run','heavy_plan':plan()}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['plan','light','heavy'],default='plan');p.add_argument('--replicates',type=int,default=100000);p.add_argument('--seed',type=int,default=1042026);p.add_argument('--execute-heavy',action='store_true');p.add_argument('--input');p.add_argument('--output');a=p.parse_args()
    if a.replicates<1:raise SystemExit('positive replicates required')
    if a.mode=='heavy' and not a.execute_heavy:raise SystemExit('Heavy execution requires explicit --execute-heavy; release mode is plan_only')
    rows=json.loads(Path(a.input).read_text()) if a.input else synthetic_data()
    result=plan(a.replicates) if a.mode=='plan' else light() if a.mode=='light' else bootstrap(rows,a.replicates,a.seed)
    text=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if a.output:Path(a.output).write_text(text)
    else:print(text)
