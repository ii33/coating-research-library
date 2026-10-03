"""Budgeted 2-D synthetic set inversion. Only arithmetic inclusion excludes.
Coordinates are exact Fractions; the copied optical kernel rounds OUTWARD.
No physical, reachable-source, statistical or global-search certification.
"""
from pathlib import Path
from dataclasses import dataclass,asdict
import sys,json,hashlib,math
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'dependencies/t07r3/models'))
import set_exclusion as inherited
from exact_intervals import I,F,f,iv
bo=inherited.bo
_VERIFIED_SCREEN_DIGESTS=set()
_VERIFIED_WITNESS_DIGESTS=set() # Process-local provenance; persisted JSON must be replayed.

def digest(x):return bo.digest(x)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(rel,x):(ROOT/rel).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def verify_dependencies():
 rows=json.loads((ROOT/'data/frozen_dependencies.json').read_text())
 for row in rows:
  p=ROOT/row['copy']
  if p.is_symlink() or not p.is_file() or p.stat().st_size!=row['bytes'] or sha(p)!=row['sha256']:raise ValueError('dependency_mismatch:'+row['copy'])
 return len(rows)
def load():
 verify_dependencies();c=inherited.load_case();k=json.loads((ROOT/'data/candidate_contract.json').read_text());validate(c,k);return c,k

def validate(c,k):
 inherited.validate_case(c)
 if sha(ROOT/'dependencies/t07r3/data/case.json')!=k['parent_case_file_sha256']:raise ValueError('parent_case_file_mismatch')
 if digest(c)!=k['parent_case_payload_sha256']:raise ValueError('parent_case_payload_mismatch')
 if c['derived_observation_contract_sha256']!=k['derived_observation_contract_sha256']:raise ValueError('derived_operator_binding_mismatch')
 if digest(c['inherited_case']['measurement'])!=k['M0_parent_measurement_sha256']:raise ValueError('M0_binding_mismatch')
 if k['parameterization']!={'dimension':2,'coordinates':['z','outer_multiplier'],'vary_original_layer':6,'shared_z_all_layers_and_channels':True,'candidate_latents':'exists z separately for each candidate','batch_latents':'independent unless explicit shared evidence','source_domain':'positive_thickness_outer_envelope_not_joint_reachable_set'}:raise ValueError('unsupported_parameter_contract')
 if any(f(x)<=0 for x in k['v_domain']) or f(k['v_domain'][0])>=f(k['v_domain'][1]):raise ValueError('positive_v_domain')
 if k['objective']['kind']!='squared_distance_to_declared_v_target' or f(k['objective']['scale'])<=0:raise ValueError('unsupported_objective')
 if k['constraint']['kind']!='synthetic_outer_thickness_ratio_upper_bound' or f(k['constraint']['cap'])<=0:raise ValueError('unsupported_constraint')
 return True

@dataclass(frozen=True)
class Box:
 zlo:F;zhi:F;vlo:F;vhi:F
 def __post_init__(self):
  for a in ('zlo','zhi','vlo','vhi'):object.__setattr__(self,a,f(getattr(self,a)))
  if self.zlo<=0 or self.vlo<=0 or self.zlo>self.zhi or self.vlo>self.vhi:raise ValueError('invalid_box')
 def exact(self):return [[str(self.zlo),str(self.zhi)],[str(self.vlo),str(self.vhi)]]
 def floats(self):return [[float(self.zlo),float(self.zhi)],[float(self.vlo),float(self.vhi)]]
 def center(self):return ((self.zlo+self.zhi)/2,(self.vlo+self.vhi)/2)
 def widths(self):return (self.zhi-self.zlo,self.vhi-self.vlo)
 def split(self,axis):
  if axis==0:
   m=(self.zlo+self.zhi)/2;return Box(self.zlo,m,self.vlo,self.vhi),Box(m,self.zhi,self.vlo,self.vhi)
  m=(self.vlo+self.vhi)/2;return Box(self.zlo,self.zhi,self.vlo,m),Box(self.zlo,self.zhi,m,self.vhi)
 def contains(self,z,v):return self.zlo<=z<=self.zhi and self.vlo<=v<=self.vhi

def domain(c,k,v=None):
 z=inherited.z_domain(c);vv=k['v_domain'] if v is None else [v,v];return Box(z.lo,z.hi,*map(f,vv))
def from_exact(x):return Box(*x[0],*x[1])
def objective(k,b):return ((I(b.vlo,b.vhi)-f(k['objective']['target']))/f(k['objective']['scale'])).sq()
def constraint(k,b):return I(b.zlo,b.zhi)*I(b.vlo,b.vhi)-f(k['constraint']['cap'])
def constraint_status(g):return 'VIOLATED' if g.lo>0 else 'SATISFIED' if g.hi<=0 else 'UNKNOWN'

class BudgetStop(Exception):pass
@dataclass
class Ledger:
 max_nodes:int;max_interval_wavelengths:int;max_float_vectors:int
 nodes:int=0;interval_wavelengths:int=0;float_vectors:int=0;float_wavelengths:int=0;denominator_fallbacks:int=0;arithmetic_fallbacks:int=0
 def __post_init__(self):
  if any(type(x)is not int or x<0 for x in (self.max_nodes,self.max_interval_wavelengths,self.max_float_vectors)):raise ValueError('invalid_budget')
 def charge(self,kind):
  field,limit={'node':('nodes','max_nodes'),'interval':('interval_wavelengths','max_interval_wavelengths'),'float':('float_vectors','max_float_vectors')}[kind]
  if getattr(self,field)>=getattr(self,limit):raise BudgetStop(kind+'_budget')
  setattr(self,field,getattr(self,field)+1)
 def snapshot(self):return asdict(self)

def channel_interval(c,b,ch,ledger):
 """Shared z, shared v only for original outer layer 6; charge BEFORE kernel."""
 n,d,ids=bo.incident_stack(c['recipe']);z=I(b.zlo,b.zhi);v=I(b.vlo,b.vhi)
 D=[iv(a)*z*(v if j==6 else I(1)) for a,j in zip(d,ids)]
 ans=I(0)
 for w,lam in zip(ch['operator']['weights'],ch['operator']['wavelength_um']):
  ledger.charge('interval');ans+=f(w)*bo.reflectance(n,D,lam)
 return ans

def assess(c,b,selected,ledger):
 pred={};reason='overlap_not_witness';failed=False;rows=inherited.observation_boxes(c,selected)
 for ch,y in rows:
  try:r=channel_interval(c,b,ch,ledger)
  except BudgetStop as e:return 'UNKNOWN',str(e),pred,True
  except ZeroDivisionError:
   r=I(0,1);failed=True;ledger.denominator_fallbacks+=1;reason='optical_denominator_unresolved'
  except ArithmeticError:
   r=I(0,1);failed=True;ledger.arithmetic_fallbacks+=1;reason='arithmetic_unresolved'
  pred[ch['id']]=r
  if inherited.disjoint(r,y):return 'OUT','observation_disjoint_'+ch['id'],pred,False
 if not failed and all(inherited.contained(pred[ch['id']],y) for ch,y in rows):return 'IN','all_observation_inclusions_contained',pred,False
 return 'UNKNOWN',reason,pred,False

def leaf_record(k,b,node_id,state,reason,pred):
 j=objective(k,b);g=constraint(k,b)
 return {'id':node_id,'box_exact':b.exact(),'box':b.floats(),'data_class':state,'reason':reason,'R_exact':{key:x.exact() for key,x in pred.items()},'R':{key:x.floats() for key,x in pred.items()},'objective_exact':j.exact(),'objective':j.floats(),'constraint_exact':g.exact(),'constraint':g.floats(),'constraint_class':constraint_status(g),'source_realization':'not_established'}

def screen_fingerprint(run):
 return digest({key:run[key] for key in ('candidate_contract_sha256','parent_case_payload_sha256','derived_observation_contract_sha256','channels','domain_exact','leaves','splits')})

def screen(c,k,selected=('M0','M1'),max_nodes=127,min_width=('0.0004','0.002'),box=None,ledger=None):
 """Exact covering tree. Unprocessed children survive as UNKNOWN on any budget stop.
 Constraint and objective annotations never rewrite observation OUT/IN/UNKNOWN.
 """
 validate(c,k)
 if type(max_nodes)is not int or max_nodes<0 or len(min_width)!=2 or any(f(w)<=0 for w in min_width):raise ValueError('invalid_screen_budget')
 root=domain(c,k) if box is None else box;allowed=domain(c,k)
 if not (allowed.contains(root.zlo,root.vlo) and allowed.contains(root.zhi,root.vhi)):raise ValueError('screen_outside_contracted_domain')
 rows=inherited.observation_boxes(c,selected);ledger=ledger or Ledger(max_nodes,max_nodes*sum(len(c['operator']['wavelength_um']) for c,_ in rows),0)
 before=ledger.snapshot();stack=[('r',root,{})];leaves=[];splits=[];used=0
 while stack:
  node_id,b,parent_pred=stack.pop()
  try:
   if used>=max_nodes:raise BudgetStop('run_node_budget')
   ledger.charge('node');used+=1;state,reason,pred,stopped=assess(c,b,selected,ledger)
  except BudgetStop as e:state,reason,pred,stopped='UNKNOWN',str(e),parent_pred,True
  eligible=[i for i,w in enumerate(b.widths()) if w>f(min_width[i])]
  if state=='UNKNOWN' and not stopped and eligible and used<max_nodes and ledger.nodes<ledger.max_nodes and ledger.interval_wavelengths<ledger.max_interval_wavelengths:
   widths=b.widths();axis=max(eligible,key=lambda i:widths[i]/f(min_width[i]));left,right=b.split(axis)
   splits.append({'id':node_id,'box_exact':b.exact(),'axis':axis,'children':[node_id+'0',node_id+'1']});stack.extend([(node_id+'1',right,pred),(node_id+'0',left,pred)]);continue
  if state=='UNKNOWN' and reason=='overlap_not_witness':reason='width_limit' if not eligible else 'run_or_global_budget'
  leaves.append(leaf_record(k,b,node_id,state,reason,pred))
 counts={q:sum(x['data_class']==q for x in leaves) for q in ['OUT','IN','UNKNOWN']}
 result={'candidate_contract_sha256':digest(k),'parent_case_payload_sha256':digest(c),'derived_observation_contract_sha256':c['derived_observation_contract_sha256'],'channels':list(selected),'domain_exact':root.exact(),'counts':counts,'data_evidence_state':'excluded_by_covering_evidence' if counts['OUT']==len(leaves) else 'retained_with_proxy_IN_box' if counts['IN'] else 'retained_unknown','leaves':leaves,'splits':splits,'evaluated_nodes':used,'charged':{key:ledger.snapshot()[key]-before[key] for key in ['nodes','interval_wavelengths','float_vectors','float_wavelengths','denominator_fallbacks','arithmetic_fallbacks']},'min_width':list(min_width),'proof_scope':'arithmetic_inclusion_for_encoded_synthetic_model; implementation_not_formally_verified','physical_certification':False,'reachable_source_witness':False}
 verify_cover(result);_VERIFIED_SCREEN_DIGESTS.add(screen_fingerprint(result));return result

def verify_cover(run):
 """Verify recursive dyadic/rational partition, no holes, no detached nodes."""
 leaves={r['id']:r for r in run['leaves']};splits={r['id']:r for r in run['splits']};seen=set()
 if len(leaves)!=len(run['leaves']) or len(splits)!=len(run['splits']) or set(leaves)&set(splits):raise ValueError('duplicate_cover_node')
 def walk(key,expected):
  if key in seen:raise ValueError('cover_cycle')
  seen.add(key)
  if key in leaves:
   if leaves[key]['box_exact']!=expected.exact():raise ValueError('leaf_box_mismatch')
  elif key in splits:
   row=splits[key]
   if row['box_exact']!=expected.exact() or row['axis']not in (0,1) or row['children']!=[key+'0',key+'1']:raise ValueError('split_contract')
   for child,box in zip(row['children'],expected.split(row['axis'])):walk(child,box)
  else:raise ValueError('coverage_hole')
 walk('r',from_exact(run['domain_exact']))
 if seen!=set(leaves)|set(splits):raise ValueError('detached_cover_node')
 return True

def float_vector(c,z,v,ledger,selected):
 ledger.charge('float');h={'multipliers':[1.0]*5+[float(v)]};out={}
 for ch,y in inherited.observation_boxes(c,selected):
  ledger.float_wavelengths+=len(ch['operator']['wavelength_um']);out[ch['id']]=inherited.scalar_observation(c,h,float(z),ch)
 return out

def finite_search(c,k,start=('1','1'),max_calls=9,selected=('M0','M1'),ledger=None):
 """Deterministic finite pattern proposals; scalar values are DIAGNOSTIC only.
 The optimizer's feasible hint is NOT evidence until interval validation.
 """
 if type(max_calls)is not int or max_calls<0:raise ValueError('invalid_search_budget')
 ledger=ledger or Ledger(0,0,max_calls);dom=domain(c,k);z,v=map(f,start)
 if not dom.contains(z,v):raise ValueError('start_outside_domain')
 steps=[(dom.zhi-dom.zlo)/4,(dom.vhi-dom.vlo)/4];trace=[];best=None;best_hint=None;queue=[(z,v)];seen=set();termination='finite_budget'
 rows=inherited.observation_boxes(c,selected)
 while len(trace)<max_calls:
  if not queue:
   p=best['point_exact'];z,v=map(f,p)
   for axis in (0,1):
    for sign in (-1,1):
     q=[z,v];q[axis]+=sign*steps[axis];q=(min(max(q[0],dom.zlo),dom.zhi),min(max(q[1],dom.vlo),dom.vhi))
     if q not in seen:queue.append(q)
   steps=[x/2 for x in steps]
   if not queue:termination='proposal_resolution';break
  z,v=queue.pop(0)
  if (z,v) in seen:continue
  seen.add((z,v))
  try:R=float_vector(c,z,v,ledger,selected)
  except BudgetStop:termination='float_budget';break
  violation=sum((max(0.0,float(Y.lo)-R[ch['id']],R[ch['id']]-float(Y.hi))/float(ch['operator']['measurement_error_abs']))**2 for ch,Y in rows)
  g=float(z*v-f(k['constraint']['cap']));violation+=max(0,g)**2
  j=float(((v-f(k['objective']['target']))/f(k['objective']['scale']))**2)
  row={'point_exact':[str(z),str(v)],'R_float':R,'violation_float':violation,'objective_float':j,'constraint_float':g,'feasible_float_hint':violation==0,'arithmetic_certificate':False};trace.append(row)
  if best is None or (violation,j)<(best['violation_float'],best['objective_float']):best=row
  if row['feasible_float_hint'] and (best_hint is None or j<best_hint['objective_float']):best_hint=row
 return {'search_state':'float_feasible_hint_found' if best_hint else 'optimizer_not_found_within_budget','termination':termination,'calls':len(trace),'best':best,'best_hint':best_hint,'trace':trace,'finite_search_is_global_certificate':False,'evidence_effect':'none; failed search cannot set OUT'}

def validate_point(c,k,z,v,ledger,selected=('M0','M1')):
 validate(c,k)
 z,v=f(z),f(v)
 if not domain(c,k).contains(z,v):raise ValueError('point_outside_domain')
 b=Box(z,z,v,v);state,reason,pred,_=assess(c,b,selected,ledger);j=objective(k,b);g=constraint(k,b)
 result={'candidate_contract_sha256':digest(k),'parent_case_payload_sha256':digest(c),'derived_observation_contract_sha256':c['derived_observation_contract_sha256'],'point_exact':[str(z),str(v)],'channels':list(selected),'data_class':state,'constraint_class':constraint_status(g),'proxy_feasible':state=='IN' and g.hi<=0,'reason':reason,'R_exact':{key:x.exact() for key,x in pred.items()},'objective_exact':j.exact(),'objective':j.floats(),'source_realization':False,'meaning':'encoded outer-envelope witness only; not Q/rho/retention reachability'}
 _VERIFIED_WITNESS_DIGESTS.add(digest(result))
 return result

def optimize_bounds(k,run,witnesses):
 """UNKNOWN enters the relaxation. U is from interval-verified feasible witnesses.
 Strict J_lo > U screens optimality only; it NEVER changes data_class.
 """
 if run['candidate_contract_sha256']!=digest(k) or any(run[key]!=k[key] for key in ('parent_case_payload_sha256','derived_observation_contract_sha256')):raise ValueError('run_contract_mismatch')
 if screen_fingerprint(run) not in _VERIFIED_SCREEN_DIGESTS:raise ValueError('unverified_or_modified_screen_requires_budgeted_replay')
 verify_cover(run)
 for row in run['leaves']:
  b=from_exact(row['box_exact']);g=constraint(k,b)
  if row['objective_exact']!=objective(k,b).exact() or row['constraint_exact']!=g.exact() or row['constraint_class']!=constraint_status(g):raise ValueError('run_objective_constraint_mismatch')
 eligible=[r for r in run['leaves'] if r['data_class']!='OUT' and r['constraint_class']!='VIOLATED']
 valid=[]
 D=from_exact(run['domain_exact'])
 if run['candidate_contract_sha256']!=digest(k):raise ValueError('run_contract_mismatch')
 for w in witnesses:
  for key in ('candidate_contract_sha256','parent_case_payload_sha256','derived_observation_contract_sha256'):
   if w.get(key)!=run.get(key):raise ValueError('witness_contract_mismatch')
  if digest(w) not in _VERIFIED_WITNESS_DIGESTS:raise ValueError('unverified_or_modified_witness_requires_budgeted_replay')
  z,v=map(f,w['point_exact'])
  if objective(k,Box(z,z,v,v)).exact()!=w['objective_exact']:raise ValueError('witness_objective_mismatch')
  if w['proxy_feasible'] and w['channels']==run['channels'] and D.contains(*map(f,w['point_exact'])):valid.append(w)
 upper=min((f(w['objective_exact'][1]) for w in valid),default=None)
 lower=min((f(r['objective_exact'][0]) for r in eligible),default=None)
 if upper is not None and (lower is None or lower>upper):raise ArithmeticError('inconsistent_objective_bracket')
 annotations=[]
 for r in run['leaves']:
  disposition='DATA_EXCLUDED' if r['data_class']=='OUT' else 'CONSTRAINT_EXCLUDED' if r['constraint_class']=='VIOLATED' else 'PRUNED_OBJECTIVE_BOUND' if upper is not None and f(r['objective_exact'][0])>upper else 'RETAINED_FOR_OPTIMUM'
  annotations.append({'id':r['id'],'data_class':r['data_class'],'disposition':disposition})
 return {'eligible_leaf_ids':[r['id'] for r in eligible],'unknown_included':sum(r['data_class']=='UNKNOWN' for r in eligible),'objective_lower_exact':None if lower is None else str(lower),'verified_proxy_upper_exact':None if upper is None else str(upper),'objective_gap_upper':None if lower is None or upper is None else float(upper-lower),'existence':'verified_proxy_witness' if valid else 'not_established' if eligible else 'excluded_by_data_or_constraint_cover','status':'bounded_relaxation_with_unresolved_boxes' if eligible else 'empty_outer_feasible_set','global_optimizer_certificate':False,'physical_optimum_certificate':False,'annotations':annotations}

def project_retained_v(run):
 ranges=sorted((from_exact(r['box_exact']).vlo,from_exact(r['box_exact']).vhi) for r in run['leaves'] if r['data_class']!='OUT');merged=[]
 for lo,hi in ranges:
  if merged and lo<=merged[-1][1]:merged[-1][1]=max(merged[-1][1],hi)
  else:merged.append([lo,hi])
 return [[str(x),str(y)] for x,y in merged]
