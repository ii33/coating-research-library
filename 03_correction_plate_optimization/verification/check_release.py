#!/usr/bin/env python3
"""Research package integrity; no machine or formal-review certification."""
import json,hashlib,sys,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
checks=[]
def ck(name,value):
 checks.append(dict(name=name,passed=bool(value)))
 if not value:raise AssertionError(name)
for p in R.rglob('*.json'):
 if '__pycache__' in p.parts:continue
 json.loads(p.read_text())
ck('JSON files parse',True)
for p in R.rglob('*.py'):compile(p.read_text(),str(p),'exec')
ck('Python source syntax',True)
v=json.loads((R/'verification/verification_results.json').read_text());ck('hard checks all pass',v['passed'] and all(x['passed'] for x in v['checks']))
s=json.loads((R/'benchmarks/results/benchmark_summary.json').read_text())
ck('benchmark belongs to final T03 model',s['model_sha256']==hashlib.sha256((R/'models/mask_design.py').read_bytes()).hexdigest())
ck('frozen T02 dependency unchanged',s['t02_model_sha256']==hashlib.sha256((R.parent/'02_machine_modeling/models/deposition_reference.py').read_bytes()).hexdigest())
ck('heldout synthetic improvement gate',all(s['synthetic_gate'].values()))
ck('counterexample preserved',s['failure_case_cv_worsens'])
ck('opacity validation independent samples exists','opacity_validation_metrics' in s)
ck('reported convex solver converged',s['opacity_solver']['converged'])
ck('scenario throughput constraints checked',s['tested_scenario_throughput_min']>=.80)
for src in json.loads((R/'sources/source_registry.json').read_text()):
 if src['original_path']:
  p=R/src['original_path']
  if '--reader' in sys.argv and not p.exists():
   checks.append(dict(name=src['source_id']+' raw original omitted from reader package',passed=True,status='not_applicable_to_reader'))
  else:ck(src['source_id']+' original hash',hashlib.sha256(p.read_bytes()).hexdigest()==src['original_sha256'])
for p in R.rglob('*.md'):
 for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
  if '://' not in target and not target.startswith('#'):
   ck('local link '+str(p.relative_to(R))+' -> '+target,(p.parent/target.split('#')[0]).exists())
required=['reports/01_forward_operator.md','reports/02_objectives_and_constraints.md','reports/03_algorithms_and_linear_algebra.md','reports/04_robustness_and_calibration.md','reports/05_benchmark_results.md','reports/06_reproducibility_and_limits.md','T04_HANDOFF.md','reviews/ROUND1_ACCEPTANCE.md','reviews/OPEN_ISSUES.md','reviews/independent_math_check.md','benchmarks/results/numerical_evidence.png','data/measurement_template.json']
for p in required:ck('required artifact '+p,(R/p).exists())
result=dict(scope='bounded research release checks, not formal model-review sign-off',passed=True,count=len(checks),checks=checks)
(R/'verification/release_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(passed=True,count=len(checks))))
