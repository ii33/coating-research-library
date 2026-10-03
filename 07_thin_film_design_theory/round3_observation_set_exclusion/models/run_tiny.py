"""One bounded toy study. No fitting, device, sweep, or 37-recipe optimization."""
from set_exclusion import *
import time

def run():
 c=load_case();start=time.monotonic();hyps=c['parameterization']['hypotheses'];budget=c['tiny_budget'];runs=[]
 for h in hyps:
  for selected in budget['datasets']:
   runs.append(branch_exclude(c,h,selected,budget['max_nodes_per_run'],budget['min_width_z']))
 witnesses=[point_witness(c,hyps[0],'1',['M0','M1']),point_witness(c,hyps[1],'1.006',['M0']),point_witness(c,hyps[2],F(500,501),['M0','M1'])]
 alias={'H0_z':'1','H_global002_z':'500/501','uniform_multiplier':'501/500','exact_product_identity':F(500,501)*F(501,500)==1,'all_six_thicknesses_identical':True,'valid_for_any_optical_observation_of_same_stack_under_fixed_material_state':True,'not_a_Q_density_retention_separation':True}
 # Only local direction diagnostics. No SVD, rank test, or global certificate.
 chs=c['derived_observation_contract']['channels'];loc=[]
 for ch in chs:
  ds=[]
  for step in [1e-4,5e-5]:ds.append((scalar_observation(c,hyps[0],1+step,ch)-scalar_observation(c,hyps[0],1-step,ch))/(2*step))
  loc.append({'channel':ch['id'],'dR_dz_central_difference':ds,'steps_z':[1e-4,5e-5],'scope':'non_rigorous_local_sensitivity_only'})
 return {'stage':'T07R3','dataset_kind':'synthetic_not_acquired','case_payload_sha256':digest(c),'derived_contract_sha256':c['derived_observation_contract_sha256'],'runs':runs,'witnesses':witnesses,'structural_alias':alias,'local_direction_diagnostic':loc,'budget':{'runs':len(runs),'evaluated_nodes':sum(r['evaluated_nodes'] for r in runs),'scalar_wavelength_enclosures':sum(r['scalar_wavelength_enclosures'] for r in runs),'max_total_nodes':len(runs)*budget['max_nodes_per_run'],'monte_carlo_draws':0,'optimizer_calls':0,'devices':0},'elapsed_seconds':time.monotonic()-start,'physical_certification':False,'point12':'partial_unchanged','point2':'conditional_non_strict_unchanged','formal_review':'pending'}
if __name__=='__main__':
 result=run();(ROOT/'verification/tiny_results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'runs':[{k:r[k] for k in ['hypothesis','channels','status','counts','evaluated_nodes']} for r in result['runs']],'witnesses':result['witnesses'],'budget':result['budget'],'elapsed_seconds':result['elapsed_seconds']},indent=2))
