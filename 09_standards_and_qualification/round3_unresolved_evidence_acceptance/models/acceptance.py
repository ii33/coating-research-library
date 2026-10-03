"""Claim-specific conservative decisions over replayed, fixed synthetic evidence.
No measurements, customer limits, probabilities, manufacturing or device control.
"""
from pathlib import Path
from fractions import Fraction as F
from dataclasses import dataclass
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/'dependencies/t08r3'
sys.path.insert(0,str(UP/'models'))
import candidate_sets as cs
_SESSIONS={}
STATE='synthetic_shared_relative_density_v1'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def exact(x):
 if not isinstance(x,str) or len(x)>1024:raise ValueError('bounded_exact_string_required')
 q=F(x)
 if max(q.numerator.bit_length(),q.denominator.bit_length())>4096:raise ValueError('exact_input_size_limit')
 return q

def verify_dependencies():
 rows=json.loads((ROOT/'data/frozen_dependencies.json').read_text())
 for r in rows:
  p=ROOT/r['copy']
  if p.is_symlink() or ROOT not in p.resolve().parents or not p.is_file() or p.stat().st_size!=r['bytes'] or sha(p)!=r['sha256']:raise ValueError('dependency_hash_mismatch:'+r['copy'])
 return len(rows)

def plan():
 return {'mode':'plan_only','executed':False,'tiny_replay':{'joint_nodes':255,'slice_nodes_cap':31,'witnesses':1,'max_nodes':286,'max_interval_wavelengths':1148,'max_float_vectors':0},'heavy_plan_only':{'purpose':'future bounded refinement of claim-crossing retained boxes under unchanged contracts','max_nodes':8191,'max_interval_wavelengths':32768,'max_float_vectors':0,'execution_implemented':False},'devices':0,'new_channels':0,'new_recipes':0,'quota_bypass':False}

@dataclass
class Session:
 payload:dict

def replay_tiny():
 """Only public evidence-construction path. Explicit fixed cap, charged kernel calls."""
 verify_dependencies();c,k=cs.load();L=cs.Ledger(286,1148,0)
 joint=cs.screen(c,k,max_nodes=255,min_width=('0.0004','0.002'),ledger=L)
 slice_=cs.screen(c,k,max_nodes=31,min_width=('0.0004','0.002'),box=cs.domain(c,k,'1.1'),ledger=L)
 w=cs.validate_point(c,k,'1','1',ledger=L)
 opt=cs.optimize_bounds(k,joint,[w])
 # Stored results are comparison inputs, never passed to optimize_bounds as proof.
 matches={}
 for name,run in [('plane_joint_255',joint),('outer10_joint_31',slice_)]:
  saved=json.loads((UP/'verification/tiny_final'/f'{name}.json').read_text())
  matches[name]=cs.screen_fingerprint(run)==cs.screen_fingerprint(saved)
 saved_w=json.loads((UP/'verification/tiny_final/witnesses.json').read_text())[0]
 matches['witness']=digest(w)==digest(saved_w)
 if not all(matches.values()):raise ValueError('frozen_replay_disagrees')
 payload={'joint':joint,'slice':slice_,'witness':w,'optimization':opt,'ledger':L.snapshot(),'frozen_replay_matches':matches,'contract':k,'case':c,'proof_kind':'arithmetic_containment_encoded_synthetic_only'}
 s=Session(payload);_SESSIONS[id(s)]=(s,digest(payload));return s

def _proof(s):
 entry=_SESSIONS.get(id(s))
 if entry is None or entry[0]is not s or not isinstance(s,Session) or digest(s.payload)!=entry[1]:raise ValueError('fresh_budgeted_replay_required_or_session_modified')
 return s.payload

def claim(kind,**kwargs):
 k=json.loads((UP/'data/candidate_contract.json').read_text())
 return {'kind':kind,'scope':'encoded_synthetic_model','channels':['M0','M1'],'sample_state_id':STATE,'derived_observation_contract_sha256':k['derived_observation_contract_sha256'],'criterion_origin':'project_illustration_not_customer_spec','interval_semantics':'hard_bound_not_probability','same_batch_latent':'one_shared_z','error_joint_set':'cartesian_outer_no_independence_assertion','guard_status':'inherited_synthetic_positive_domain_only',**kwargs}

def result(status,reason,requests=(),**extra):
 return {'status':status,'reason':reason,'required_evidence':list(requests),'production_release':False,'physical_certification':False,'customer_criteria':'unknown','formal_stage_acceptance':'pending',**extra}

def evaluate(s,q):
 p=_proof(s);k=p['contract'];w=p['witness'];joint=p['joint'];o=p['optimization']
 if q.get('scope')!='encoded_synthetic_model':return result('blocked_evidence','actual_measurement_or_production_not_supported',('REQ-REAL','REQ-RULE'))
 if q.get('channels')!=['M0','M1'] or q.get('sample_state_id')!=STATE or q.get('derived_observation_contract_sha256')!=k['derived_observation_contract_sha256']:return result('blocked_evidence','new_operator_or_state_requires_new_contract',('REQ-OPERATOR',))
 if q.get('same_batch_latent')!='one_shared_z':return result('blocked_evidence','same_specimen_correlation_contract_broken',('REQ-CORRELATION',))
 if q.get('error_joint_set')!='cartesian_outer_no_independence_assertion':return result('blocked_evidence','joint_error_claim_not_supported',('REQ-CORRELATION',))
 if q.get('interval_semantics')!='hard_bound_not_probability':return result('blocked_evidence','arithmetic_bound_is_not_coverage_probability',('REQ-UNCERTAINTY',))
 if q.get('guard_status')!='inherited_synthetic_positive_domain_only':return result('blocked_evidence','negative_cross_zero_near_zero_inventory_or_source_guard_unresolved',('REQ-GUARDS',))
 if q.get('criterion_origin')!='project_illustration_not_customer_spec':return result('blocked_evidence','actual_customer_rule_unknown',('REQ-RULE',))
 kind=q.get('kind');ret=[x for x in joint['leaves'] if x['data_class']!='OUT' and x['constraint_class']!='VIOLATED']
 common={'retained_unknown_count':sum(x['data_class']=='UNKNOWN'for x in ret),'objective_pruned_still_data_unknown':sum(a['disposition']=='PRUNED_OBJECTIVE_BOUND' and a['data_class']=='UNKNOWN'for a in o['annotations'])}
 if kind=='proxy_exists':return result('conditional_accept' if w['proxy_feasible'] else 'retain_unknown','interval_verified_outer_envelope_witness_not_source_reachability',**common)
 if kind=='slice_exists':
  if q.get('v')!='1.1':return result('retain_unknown','slice_not_replayed',('REQ-COMPUTE',))
  r=p['slice'];out=all(x['data_class']=='OUT'for x in r['leaves'])
  return result('reject_claim' if out else 'retain_unknown','entire_shared_z_slice_out' if out else 'slice_unresolved',proof_leaf_count=len(r['leaves']))
 if kind=='source_exists':return result('blocked_evidence','proxy_IN_does_not_establish_joint_Q_rho_retention_reachability',('REQ-SOURCE','REQ-GUARDS'))
 if kind=='optimizer_failure_means_empty':return result('reject_claim','finite_search_failure_has_no_exclusion_force_and_verified_counterexample_exists')
 if kind in ('all_v_in','all_J_in'):
  lo,hi=map(exact,q['range']);
  if lo>hi:raise ValueError('reversed_criterion')
  # Keep ALL data-retained boxes, including objective-pruned boxes.
  intervals=[list(map(F,x['box_exact'][1] if kind=='all_v_in' else x['objective_exact']))for x in ret]
  wiv=[F(w['point_exact'][1])]*2 if kind=='all_v_in' else list(map(F,w['objective_exact']))
  if not intervals:return result('retain_unknown','empty_support_no_nonvacuous_acceptance',('REQ-COMPUTE',))
  hull=[min(x[0]for x in intervals),max(x[1]for x in intervals)]
  crossing=[x['id']for x,z in zip(ret,intervals) if z[0]<lo or z[1]>hi]
  if w['proxy_feasible'] and (wiv[1]<lo or wiv[0]>hi):return result('reject_claim','verified_proxy_counterexample',witness_interval=list(map(str,wiv)),**common)
  if w['proxy_feasible'] and lo<=hull[0] and hull[1]<=hi:return result('conditional_accept','all_retained_outer_boxes_contained_in_criterion',outer_hull=list(map(str,hull)),**common)
  return result('retain_unknown','retained_outer_boxes_cross_criterion_without_verified_counterexample',('REQ-COMPUTE',),outer_hull=list(map(str,hull)),claim_crossing_leaf_ids=crossing,**common)
 if kind=='minimum_J_le':
  t=exact(q['threshold']);lo=F(o['objective_lower_exact']);hi=F(o['verified_proxy_upper_exact'])
  st='conditional_accept' if hi<=t else 'reject_claim' if lo>t else 'retain_unknown'
  return result(st,'existential_optimization_bracket_not_universal_performance',('REQ-COMPUTE',)if st=='retain_unknown'else(),minimum_bracket=[str(lo),str(hi)],**common)
 if kind=='gap_le':
  t=exact(q['threshold']);gap=F(o['verified_proxy_upper_exact'])-F(o['objective_lower_exact'])
  # A wide enclosure cannot refute a true narrow optimum gap: retain UNKNOWN.
  st='conditional_accept'if gap<=t else 'retain_unknown'
  return result(st,'certified_upper_gap_sufficient_not_necessary',('REQ-COMPUTE',)if st=='retain_unknown'else(),gap_upper=str(gap),**common)
 if kind=='point_M0_in':
  lo,hi=map(exact,q['range']);a,b=map(F,w['R_exact']['M0'])
  if lo>hi:raise ValueError('reversed_criterion')
  st='conditional_accept'if lo<=a and b<=hi else 'reject_claim'if b<lo or a>hi else 'retain_unknown'
  return result(st,'conditional_forward_response_at_verified_point_not_measured_result',point_exact=w['point_exact'],response_interval=[str(a),str(b)])
 if kind=='observation_M0_in':
  lo,hi=map(exact,q['range']);dc=p['case']['derived_observation_contract'];y=F(dc['measurement_centers_R'][0]);e=F(dc['error_abs_R'][0]);a,b=y-e,y+e
  if lo>hi:raise ValueError('reversed_criterion')
  st='conditional_accept'if lo<=a and b<=hi else 'reject_claim'if b<lo or a>hi else 'retain_unknown'
  return result(st,'synthetic_readout_hard_interval_rule_not_actual_measurement',('REQ-SAME-CHANNEL',)if st=='retain_unknown'else(),observation_interval=[str(a),str(b)],not_95_percent=True)
 if kind=='all_spectrum_or_95pct':return result('blocked_evidence','two_discrete_channels_do_not_certify_continuous_spectrum_or_probability',('REQ-OPERATOR','REQ-UNCERTAINTY'))
 return result('blocked_evidence','unsupported_claim_kind')

def summary(s):
 p=_proof(s);r=p['joint'];o=p['optimization'];ret=[x for x in r['leaves']if x['data_class']!='OUT'];ann={a['id']:a['disposition']for a in o['annotations']}
 optret=[x for x in ret if ann[x['id']]=='RETAINED_FOR_OPTIMUM']
 def hull(rows):return [str(min(F(x['box_exact'][1][0])for x in rows)),str(max(F(x['box_exact'][1][1])for x in rows))]
 return {'joint_counts':r['counts'],'slice_counts':p['slice']['counts'],'all_data_retained_v_hull':hull(ret),'incorrect_if_used_as_all_feasible_optimum_only_v_hull':hull(optret),'unknown_in_optimization':o['unknown_included'],'objective_pruned_unknown_count':sum(a['disposition']=='PRUNED_OBJECTIVE_BOUND'for a in o['annotations']),'minimum_bracket':[o['objective_lower_exact'],o['verified_proxy_upper_exact']],'ledger':p['ledger'],'frozen_replay_matches':p['frozen_replay_matches'],'saved_record_is_live_proof':False}
