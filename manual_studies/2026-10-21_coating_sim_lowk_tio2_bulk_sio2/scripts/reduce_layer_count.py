from tio2_research import *
start=time.monotonic();initial=json.load(open(OUT/'retained-best.json'));results=[];audits=[];lowest=None
protocol=dict(phase='B_layer_economy',reason='32-layer sourced-film target passed with margin. Test fewer layers via new multistack/chirped priors and full-thickness matching, not blind deletion or added layers.',layer_counts=[30,28,26],families=['two_stack_440_625','linear_chirp_420_695'],training_step_nm=1,search_cap_s=150,per_candidate_cap_s=12,maxiter_each_stage=180,stopping='Sweep 30/28/26 layers per parent direction; retain smallest successful tested count with margin, no global minimality claim.')
save('protocol-B-layer-economy.json',protocol)
for N in protocol['layer_counts']:
 countpass=False
 M=N//2;cs=[prior([440]*(M//2)+[625]*(M-M//2),name=f'economy{N}_two_stack'),prior(np.linspace(420,695,M),name=f'economy{N}_linear_chirp')]
 if N%2:
  for c in cs:c['labels'].append('H');c['d']=np.r_[c['d'],qwave('H',[695])[0]]
 countbest=None
 for c in cs:
  if time.monotonic()-start>150:break
  a=optimize(c,12,180);save('candidate-B-'+c['name']+'.json',a);row={k:a[k] for k in ['name','family','initial_worst','train_worst','elapsed_s','stages']};row.update(layer_count=len(a['d']),total_nm=float(sum(a['d'])));results.append(row);save('phase-B-search-summary.json',results);print('ECONOMY '+json.dumps(plain(row)),flush=True)
  if countbest is None or a['train_worst']['R']>countbest['train_worst']['R']:countbest=a
  if a['train_worst']['R']>=.98005:
   ar=audit(a,'B-'+c['name']);audits.append(ar);print('AUDIT '+json.dumps({k:ar[k] for k in ['name','worst','passed']}),flush=True)
   if ar['passed']:lowest=a;countpass=True;break
 if countbest is not None and not countpass:
  ar=audit(countbest,f'B-best-{N}layers');audits.append(ar);print('AUDIT '+json.dumps({k:ar[k] for k in ['name','worst','passed']}),flush=True)
 if time.monotonic()-start>150:break
if lowest is not None:save('lowest-qualified.json',lowest)
save('phase-B-result.json',dict(qualified_fewer_layers_exists=lowest is not None,lowest_tested_qualified_layers=len(lowest['d']) if lowest else None,not_global_minimum_proof=True,candidates=len(results),elapsed_s=time.monotonic()-start,audits=audits))
print('FINAL '+json.dumps(dict(lowest_qualified_layers=len(lowest['d']) if lowest else None,elapsed_s=time.monotonic()-start)),flush=True)
