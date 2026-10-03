"""Complete batch, multi-band, multi-angle, sensitivity/uncertainty driver.
Default only inspects/plans; executing never silently selects GPU or device.
"""
from pathlib import Path
import argparse,copy,json
import numpy as np
from process_optics import evaluate,validate,ROOT
from inference import propagate

def build_grid(plan):
 chunks=[]
 for start,end,count in plan['bands_um']:
  if isinstance(count,bool) or int(count)!=count or count<2 or count>100000 or not 0<start<end:raise ValueError('bounded valid band grid required')
  chunks.append(np.linspace(start,end,int(count)))
 return np.unique(np.concatenate(chunks))
def run(plan,record,execute=False):
 validate(record);w=build_grid(plan)
 if not plan['angles_deg'] or not plan['polarizations']:raise ValueError('nonempty angle and polarization sets required')
 if any(p not in ['s','p','unpolarized'] for p in plan['polarizations']) or any(not 0<=a<89.9 for a in plan['angles_deg']):raise ValueError('invalid angular/polarization plan')
 count=len(w)*len(plan['angles_deg'])*len(plan['polarizations']);params=plan['parameters'];samples=plan['monte_carlo_samples']
 if not isinstance(samples,int) or samples<0:raise ValueError('invalid sample count')
 estimate=count*(1+2*len(params)+samples)
 info={'status':'plan_only','spectral_points_per_condition':len(w),'conditions':len(plan['angles_deg'])*len(plan['polarizations']),'nominal_channel_points':count,'approximate_forward_wavelength_evaluations':estimate,'estimate_excludes':'unpolarized split, bandpass/angle nodes, reverse/rear solves; not exact operation count','monte_carlo_samples':samples,'device_validation':'not_run','physical_experiment':'not_run','automatic_GPU':False,'command_to_opt_in':'python models/batch_driver.py --execute --output <local-json>','meaning':'execution requires a later user-arranged device run; no timing or performance claim'}
 if not execute:return info
 if estimate>50000000:raise ValueError('execution cap exceeded; split plan explicitly')
 runs=[]
 for angle in plan['angles_deg']:
  for pol in plan['polarizations']:
   r=copy.deepcopy(record);r['measurement'].update(wavelength_um=w.tolist(),angle_deg=angle,polarization=pol)
   out=evaluate(r)
   if out['status']=='conditional_calculation':
    out['uncertainty']=propagate(r,params,plan['channels'],plan['parameter_covariance'],samples,plan['seed'])
   runs.append({'angle_deg':angle,'polarization':pol,'result':out})
 info.update(status='executed_conditional_synthetic',runs=runs,device_validation='not_established_by_execution',note='This computation is not production material calibration')
 return info
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,default=ROOT/'data/batch_plan.json');p.add_argument('--record',type=Path,default=ROOT/'examples/synthetic_dielectric.json');p.add_argument('--execute',action='store_true');p.add_argument('--output',type=Path);a=p.parse_args()
 if a.execute and a.output is None:p.error('--execute requires explicit --output')
 out=run(json.loads(a.plan.read_text()),json.loads(a.record.read_text()),a.execute)
 text=json.dumps(out,indent=2,ensure_ascii=False,allow_nan=False)+'\n'
 if a.output:a.output.write_text(text)
 else:print(text,end='')
