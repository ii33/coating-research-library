"""Bounded one-latent set inversion using the hash-bound T06 optical inclusion.
Exact/dyadic arithmetic classifies encoded synthetic boxes. Not a film certificate.
"""
from pathlib import Path
import sys,json,hashlib,cmath,math
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'dependencies/t06r3/models'))
import bounded_optics as bo
from exact_intervals import I,F,f,iv

def digest(x):return bo.digest(x)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify_dependencies():
 rows=json.loads((ROOT/'data/frozen_dependencies.json').read_text())
 for row in rows:
  p=ROOT/row['copy']
  if p.is_symlink() or not p.is_file() or p.stat().st_size!=row['bytes'] or sha(p)!=row['sha256']:raise ValueError('dependency_mismatch:'+row['copy'])
 return len(rows)
def load_case():
 verify_dependencies();c=json.loads((ROOT/'data/case.json').read_text());validate_case(c);return c

def validate_case(c):
 old=c['inherited_case'];bound=c['inherited_binding'];parent=json.loads((ROOT/'dependencies/t06r3/data/case.json').read_text())
 if old!=parent or sha(ROOT/'dependencies/t06r3/data/case.json')!=bound['case_file_sha256']:raise ValueError('inherited_case_changed')
 values={'full_bridge_payload_sha256':digest(old['bridge']),'bridge_contract_sha256':old['bridge']['bridge_contract_sha256'],'response_contract_sha256':old['bridge']['t04_response']['response_contract_sha256'],'measurement_contract_sha256':digest(old['measurement']),'material_contract_sha256':digest(old['material']),'recipe_payload_sha256':digest(c['recipe'])}
 if any(bound[k]!=v for k,v in values.items()):raise ValueError('inherited_contract_binding_mismatch')
 der=c['derived_observation_contract']
 if digest(der)!=c['derived_observation_contract_sha256']:raise ValueError('derived_contract_hash_mismatch')
 if der['parent_measurement_sha256']!=digest(old['measurement']) or der['channels'][0]['operator']!=old['measurement']:raise ValueError('silent_parent_operator_change')
 if der['material_extension']['parent_material_sha256']!=digest(old['material']) or der['material_extension']['sample_state_id']!=old['material']['sample_state_id']:raise ValueError('material_state_mismatch')
 if der['same_specimen_between_channels'] is not True or der['model_discrepancy']!='exact_zero_by_synthetic_definition_only; real discrepancy unknown is unsupported':raise ValueError('unsupported_joint_or_discrepancy_contract')
 if der['material_extension']['k']!='0':raise ValueError('absorption_not_supported')
 channels=der['channels'];y=der['measurement_centers_R'];err=der['error_abs_R']
 if len(channels)!=len(y) or len(y)!=len(err) or len(set(q['id'] for q in channels))!=len(channels):raise ValueError('observation_dimensions')
 for q,e in zip(channels,err):
  bo.validate_operator(q['operator'])
  if f(e)<0 or f(e)!=f(q['operator']['measurement_error_abs']):raise ValueError('error_contract_mismatch')
  if any(w not in der['material_extension']['domain_um'] for w in q['operator']['wavelength_um']):raise ValueError('nk_outside_explicit_domain')
 gate=bo.source_gate(old['bridge'],old['material'])
 if gate['bounds'] is None:raise ValueError('source_gate:'+gate['status'])
 if f(old['material']['normalization_h_ref_m'])<=0:raise ValueError('nonpositive_h_ref')
 for h in c['parameterization']['hypotheses']:
  if len(h['multipliers'])!=len(c['recipe']['layers']) or any(f(v)<=0 for v in h['multipliers']):raise ValueError('nonpositive_or_incomplete_layer_mapping')
 return gate

def z_domain(c):
 g=bo.source_gate(c['inherited_case']['bridge'],c['inherited_case']['material'])
 if g['bounds'] is None:raise ValueError('source_gate:'+g['status'])
 return g['bounds']/f(c['inherited_case']['material']['normalization_h_ref_m'])

def channel_box(c,h,z,channel):
 """One shared interval z maps to every layer; overestimation is safe."""
 bo.validate_operator(channel['operator']);n,d,ids=bo.incident_stack(c['recipe'])
 m=dict(zip([q['layer'] for q in c['recipe']['layers']],map(f,h['multipliers'])))
 D=[iv(x)*iv(z)*m[j] for x,j in zip(d,ids)]
 op=channel['operator']
 return sum((f(w)*bo.reflectance(n,D,lam) for w,lam in zip(op['weights'],op['wavelength_um'])),I(0))

def observation_boxes(c,selected):
 der=c['derived_observation_contract'];rows=[]
 for ch,y,e in zip(der['channels'],der['measurement_centers_R'],der['error_abs_R']):
  if ch['id'] in selected:rows.append((ch,I(f(y)-f(e),f(y)+f(e))))
 if len(rows)!=len(selected):raise ValueError('unknown_or_duplicate_channel')
 return rows

def disjoint(a,b):return a.hi<b.lo or b.hi<a.lo
def contained(a,b):return b.lo<=a.lo and a.hi<=b.hi

def branch_exclude(c,h,selected=('M0','M1'),max_nodes=127,min_width='0.0004',domain=None):
 """SIVIA-style covering tree. Budget/width-limited leaves remain UNKNOWN.
 OUT iff one inclusion interval is disjoint from its target. IN iff all
 inclusion intervals are contained. Queue always covers unclassified domain.
 """
 if type(max_nodes)is not int or max_nodes<1 or f(min_width)<=0:raise ValueError('invalid_budget')
 dom=z_domain(c) if domain is None else iv(domain)
 if dom.lo<=0:raise ValueError('nonpositive_latent')
 rows=observation_boxes(c,selected);queue=[(dom,0)];leaves=[];evaluated=0;optical_evaluations=0;denominator_fallbacks=0
 while queue:
  z,depth=queue.pop()
  if evaluated>=max_nodes:
   leaves.append({'z_exact':z.exact(),'z':z.floats(),'class':'UNKNOWN','reason':'node_budget','depth':depth,'R_exact':{},'R':{}});continue
  evaluated+=1;pred={};reason=None;failed=False
  for ch,Y in rows:
   try:R=channel_box(c,h,z,ch)
   except ZeroDivisionError:R=I(0,1);denominator_fallbacks+=1;failed=True
   pred[ch['id']]=R;optical_evaluations+=len(ch['operator']['wavelength_um'])
   if disjoint(R,Y):reason='disjoint_'+ch['id'];break
  state='OUT' if reason else ('IN' if not failed and all(contained(pred[ch['id']],Y) for ch,Y in rows) else 'UNKNOWN')
  if state=='UNKNOWN' and z.hi-z.lo>f(min_width) and evaluated<max_nodes:
   mid=(z.lo+z.hi)/2;queue.extend([(I(mid,z.hi),depth+1),(I(z.lo,mid),depth+1)]);continue
  leaves.append({'z_exact':z.exact(),'z':z.floats(),'class':state,'reason':reason or ('all_observations_contained' if state=='IN' else ('width_limit' if z.hi-z.lo<=f(min_width) else 'node_budget')),'depth':depth,'R_exact':{k:v.exact() for k,v in pred.items()},'R':{k:v.floats() for k,v in pred.items()}})
 counts={k:sum(x['class']==k for x in leaves) for k in ['OUT','IN','UNKNOWN']}
 status='excluded_encoded_model' if counts['OUT']==len(leaves) else 'feasible_witness_box' if counts['IN'] else 'unresolved_outer_overlap'
 return {'hypothesis':h['id'],'channels':list(selected),'status':status,'domain_exact':dom.exact(),'domain':dom.floats(),'counts':counts,'evaluated_nodes':evaluated,'scalar_wavelength_enclosures':optical_evaluations,'denominator_fallbacks':denominator_fallbacks,'max_nodes':max_nodes,'min_width':str(min_width),'leaves':sorted(leaves,key=lambda x:f(x['z_exact'][0])),'derived_observation_contract_sha256':c['derived_observation_contract_sha256'],'case_payload_sha256':digest(c),'physical_certification':False,'proof_scope':'conditional_encoded_model_interval_inclusion; implementation_not_formally_verified'}

def point_witness(c,h,z,selected):
 dom=z_domain(c);zz=f(z)
 if not dom.lo<=zz<=dom.hi:raise ValueError('witness_outside_prior')
 pred={ch['id']:channel_box(c,h,I(zz),ch) for ch,Y in observation_boxes(c,selected)}
 feasible=all(contained(pred[ch['id']],Y) for ch,Y in observation_boxes(c,selected))
 return {'hypothesis':h['id'],'z_exact':str(zz),'channels':list(selected),'all_point_enclosures_inside_data':feasible,'R':{k:v.floats() for k,v in pred.items()},'R_exact':{k:v.exact() for k,v in pred.items()},'meaning':'verified feasible point for declared hard box, not exact equality to central readings'}

def scalar_observation(c,h,z,channel):
 """Non-rigorous plotting/finite-difference helper. Never used to exclude."""
 n,d,ids=bo.incident_stack(c['recipe']);m=dict(zip([q['layer'] for q in c['recipe']['layers']],map(float,h['multipliers'])));n=list(map(float,n));D=[float(x)*float(z)*m[j] for x,j in zip(d,ids)];rr=[(a-b)/(a+b) for a,b in zip(n,n[1:])]
 def R(w):
  r=rr[-1]
  for j in reversed(range(len(D))):
   q=r*cmath.exp(4j*math.pi*n[j+1]*D[j]/float(w));r=(rr[j]+q)/(1+rr[j]*q)
  return abs(r)**2
 op=channel['operator'];return sum(float(f(a))*R(w) for a,w in zip(op['weights'],op['wavelength_um']))
