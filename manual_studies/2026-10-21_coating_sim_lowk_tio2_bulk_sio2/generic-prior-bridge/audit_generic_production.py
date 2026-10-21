"""Fixed-candidate production audit after the no-answer-seed bridge has finished.
Reuse only frozen materials/environment/objectives; export the GENERATED PRIOR,
not the final answer, as the request seed. No search is launched here.
"""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
import sys,json,copy,time,hashlib,subprocess
from pathlib import Path
from dataclasses import replace,asdict
HERE=Path(__file__).resolve().parent;CORE=HERE.parent;root_env=os.environ.get('COATING_SIM_ROOT')
if not root_env: raise RuntimeError('Set COATING_SIM_ROOT to the clean coating-sim checkout at the recorded commit.')
ROOT=Path(root_env).expanduser().resolve()
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from coat_sim.core.film_synthesis_io import film_synthesis_request_from_payload,film_synthesis_request_to_payload,prepare_film_synthesis_payload
from coat_sim.core.film_auto_synthesis import freeze_film_synthesis_request
from coat_sim.core.film_synthesis_audit import audit_frozen_synthesis_candidate
from coat_sim.core.film_synthesis_absorption import synthesis_absorption_assumption
from coat_sim.core.film_design import validate_design
saved=json.load(open(HERE/'result.json'));assert saved['passed'];idx=saved['chosen_index']
# The preexisting payload is used only as a frozen MATERIAL/TARGET container.
# Its old seed_designs are explicitly removed before constructing this payload.
payload=json.load(open(CORE/'production/32layer-frozen-request.json'));payload['request']['seed_designs']=[]
_,request,_=film_synthesis_request_from_payload(payload)
refs={label:request.candidate_materials[i] for i,label in enumerate(['H','L'])}
def convert(candidate):
 design=copy.deepcopy(request.environment);design['name']='Generic source-stopband bridge '+candidate['name']
 design['front_layers']=[dict(id=f'generic-hr-{i:02d}',material_id=refs[l].material_id,optical_set_id=refs[l].optical_set_id,thickness=dict(value=float(d),unit='nm'),note='Generated-prior bridge, not a target lookup') for i,(l,d) in enumerate(zip(candidate['labels'][::-1],candidate['d'][::-1]),1)]
 return validate_design(design)
prior=convert(json.load(open(HERE/f'generated-prior-{idx}.json')));candidate=convert(json.load(open(HERE/f'candidate-{idx}.json')))
request=replace(request,seed_designs=(prior,),max_seconds=60)
request=freeze_film_synthesis_request(None,request)
p=film_synthesis_request_to_payload('generic-source-stopband-bridge',request);canonical,meta=prepare_film_synthesis_payload(None,p);assert p==canonical and not meta
for name,value in [('generated-prior-portable-request.json',p),('generated-prior-production-design.json',prior),('final-candidate-production-design.json',candidate)]:
 (HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
t=time.monotonic();a=audit_frozen_synthesis_candidate(request,candidate);worst=min(a['score']['errors'],key=lambda e:e.actual)
report=dict(passed=worst.actual>=.98,worst=asdict(worst),audit_metadata=a['audit'],absorption_assumption=synthesis_absorption_assumption(request,candidate),request_seed_is_generated_unoptimized_prior=True,old_answer_seed_removed_before_request_parse=True,snapshot_sha256=request.frozen_material_snapshot['sha256'],elapsed_audit_s=time.monotonic()-t,software_commit=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),software_git_clean=not subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain'],text=True).strip())
(HERE/'production-frozen-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report),flush=True)
