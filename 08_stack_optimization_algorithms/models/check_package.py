#!/usr/bin/env python3
"""Offline structural and numerical-evidence audit; not production certification."""
from pathlib import Path
import json,hashlib,re,xml.etree.ElementTree as ET
import numpy as np
ROOT=Path(__file__).resolve().parents[1];checks=[]
def ck(k,ok,detail=''):checks.append(dict(check=k,passed=bool(ok),detail=detail))
r=json.loads((ROOT/'data/benchmark_results.json').read_text());e=json.loads((ROOT/'data/extension_results.json').read_text());src=json.loads((ROOT/'data/source_registry.json').read_text())['sources']
ck('3 frozen seed comparisons',set(r['cases'])=={'B01','B02','B03'} and [r['cases'][k]['seed'] for k in ['B01','B02','B03']]==['E02','E04','E05'])
ck('5 methods per case',all(len(v['runs'])==5 for v in r['cases'].values()))
ck('all results finite budgets and complete stop reasons',all(np.isfinite(z['cost']) and z['message'] and z['budget']['spectrum_calls']>0 for b in r['cases'].values() for z in b['runs'].values()))
ck('all 3 accurate routes improve independent mean from seed',all(b['runs']['accurate']['holdout']['cost']<b['initial_holdout']['cost'] for b in r['cases'].values()))
ck('B03 unsuccessful budget and specification failure retained',not r['cases']['B03']['runs']['accurate']['success'] and r['cases']['B03']['runs']['accurate']['holdout']['sample_worst_normalized_target_error']>1)
ck('extended B03 explicitly budgeted',r['extra']['extended_precision_B03']['max_nfev_or_maxiter']==240)
ck('independent dense and multiangle audits',all(z['holdout']['points_per_band']>=601 and len(z['holdout']['angles_deg'])==5 for b in r['cases'].values() for z in b['runs'].values()))
ck('derivative best-step relative error below 1e-6',all(min(z['relative_fro_error'] for z in r['extra']['gradient_check'] if z['case']==bid)<1e-6 for bid in r['cases']))
ck('under-sampling counterexample retained',r['extra']['undersampling']['train_max_R']<1e-25 and r['extra']['undersampling']['dense_max_R']>.72)
ck('harmful surrogate steps rejected',all(not z['accepted'] for z in r['extra']['surrogate']['trace'] if z['actual_reduction']<0) and any(z['actual_reduction']<0 for z in r['extra']['surrogate']['trace']))
ck('needle decline recorded honestly',r['extra']['needle']['accepted'] is False)
ck('robustness includes independent 64 scenario pairs and improved mean/tail',all(len(z['all_scenario_costs'])==64 for z in r['extra']['robustness']['comparison'].values()) and r['extra']['robustness']['comparison']['robust']['quantile95_cost']<r['extra']['robustness']['comparison']['nominal']['quantile95_cost'])
ck('manufacturing explicit cap feasible',all(max(z['violations'].values())<1e-7 for z in r['extra']['thickness_tradeoff']))
ck('minimax epigraph feasible on finite grid',e['finite_minimax']['result']['constraint_violation']<1e-6)
ck('R+A+T multiobjective output closure',all(abs(z['audit_R_mean']+z['audit_A_mean']+z['audit_T_mean']-1)<1e-10 for z in e['reflection_absorption_tradeoff']))
ck('nonidentifiability exact counterexample',r['extra']['nonidentifiability']['singular_values'][-1]<1e-12 and r['extra']['nonidentifiability']['spectrum_error_for_redistribution']<1e-12)
ck('7-repeat 2/10/17/80 layer performance',len(r['extra']['kernel_performance'])==8 and all(len(z['seconds_samples'])==7 for z in r['extra']['kernel_performance']))
ck('16 registered cards with limits and extent',len(src)==16 and all((ROOT/s['summary_path']).is_file() and s['limitations'] and s['read_extent'] for s in src))
local=[s for s in src if s['local_original']];present=[s for s in local if (ROOT/'sources/originals'/s['local_original']).exists()]
ck('optional local originals hashes',all(hashlib.sha256((ROOT/'sources/originals'/s['local_original']).read_bytes()).hexdigest()==s['sha256'] for s in present),f'{len(present)}/{len(local)} originals present; omitted publicly')
ck('9 narrative chapters',len([p for p in (ROOT/'reports').glob('*.md') if re.match(r'0[1-9]_',p.name)])==9)
ck('4 valid SVGs and PNG previews',len(list((ROOT/'figures').glob('*.svg')))==4 and all((ROOT/'reviews'/(p.stem+'_preview.png')).is_file() for p in (ROOT/'figures').glob('*.svg')))
for p in (ROOT/'figures').glob('*.svg'):ET.parse(p)
bad=[];ids={s['id'] for s in src};used=set()
for p in ROOT.rglob('*.md'):
 if 'originals' in p.parts and p.name!='README.md':continue
 txt=p.read_text();used.update(re.findall(r'\[(O\d{2})\]',txt))
 for u in re.findall(r'\]\(([^)]+)\)',txt):
  if '://' in u or u.startswith('#'):continue
  u=u.split('#')[0]
  if u and not (p.parent/u).exists():bad.append([str(p.relative_to(ROOT)),u])
ck('local links resolve',not bad,str(bad));ck('citations registered',used<=ids,str(sorted(used-ids)))
ck('36 tests logged pass','Ran 36 tests' in (ROOT/'reviews/test_output.txt').read_text() and (ROOT/'reviews/test_output.txt').read_text().rstrip().endswith('OK'))
ck('clean copy smoke recorded',(ROOT/'reviews/clean_copy_output.txt').exists() and 'CLEAN_COPY_PASS' in (ROOT/'reviews/clean_copy_output.txt').read_text())
ck('T09 handoff and contract',(ROOT/'T09_HANDOFF.md').is_file() and (ROOT/'data/optimization_contract.json').is_file())
ck('originals excluded','sources/originals/*' in (ROOT/'.gitignore').read_text())
deps=json.loads((ROOT/'data/frozen_dependencies.json').read_text());up=[]
for path,h in deps.items():
 f=ROOT.parent/path
 if f.exists():up.append(hashlib.sha256(f.read_bytes()).hexdigest()==h)
ck('available upstream frozen files unchanged',all(up),f'{len(up)} present; standalone copy needs only local snapshots')
result=dict(passed=all(z['passed'] for z in checks),scope='offline evidence consistency only; no production or full model-chain certification',checks=checks)
(ROOT/'reviews/package_check_output.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(0 if result['passed'] else 1)
