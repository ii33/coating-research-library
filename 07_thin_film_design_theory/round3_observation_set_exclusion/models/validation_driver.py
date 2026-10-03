"""Safe default plan-only driver. No heavy/device execution route exists."""
from set_exclusion import *
import argparse
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=['plan_only','tiny'],default='plan_only');a=p.parse_args();c=load_case()
 if a.mode=='tiny':
  from run_tiny import run
  result=run();(ROOT/'verification/tiny_results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'tiny_only','budget':result['budget']},indent=2))
 else:
  plan={'stage':'T07R3','mode':'plan_only','executed':False,'case_payload_sha256':digest(c),'derived_contract_sha256':c['derived_observation_contract_sha256'],'tasks':[{'id':'future_continuous_candidate_set','domain':'joint z and outer-layer multiplier, plus explicitly contracted nuisance variables','goal':'enclose feasible set with complete coverage and retain unresolved boxes','requires':['new parameter domain contract','error/model-discrepancy evidence','budget approval']},{'id':'future_real_observation','goal':'test candidate predictions with same-state measured nk and calibrated two-channel operator','requires':['actual specimen and state linkage','actual instrument adapter','real readout/calibration bounds','source reachable-set evidence','device authorization']}],'stopping_rule':'Every domain box classified or retained UNKNOWN at explicit width/node limits; never treat budget exhaustion as exclusion','unsupported_execution':['heavy','devices','multi_batch_fit','continuous_band_certificate'],'quota_bypass':False,'point12':'partial_unchanged','point2':'conditional_non_strict_unchanged','formal_review_chain':'pending'}
  (ROOT/'verification/batch_plan_receipt.json').write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps(plan,indent=2))
