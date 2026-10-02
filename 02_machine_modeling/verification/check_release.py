#!/usr/bin/env python3
"""Local integrity and reproducibility checks, distinct from physical validation."""
from pathlib import Path
import hashlib
import json
import re
import sys
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[1]
checks=[]
def check(name,passed,detail): checks.append({'name':name,'passed':bool(passed),'detail':detail})
required=['README.md','T03_HANDOFF.md','stage_status.json','data/synthetic_case.json','data/measurement_template.json',
          'models/deposition_reference.py','models/run_case.py','verification/verification_results.json',
          'reviews/ROUND1_ACCEPTANCE.md','reviews/OPEN_ISSUES.md','reviews/independent_math_check.md',
          'sources/source_registry.json','sources/RIGHTS_AND_ACCESS.md','sources/summaries/source_summaries.md',
          'benchmarks/results/benchmark_summary.json','benchmarks/results/example.json','benchmarks/results/example.csv']
check('required_files',all((ROOT/p).is_file() for p in required),required)
ch=list((ROOT/'chapters').glob('*.md'));check('six_substantive_chapters',len(ch)==6 and all(p.stat().st_size>4000 for p in ch),[p.name for p in ch])
errors=[]
for p in ROOT.rglob('*.json'):
    try:json.loads(p.read_text())
    except Exception as e: errors.append(f'{p.relative_to(ROOT)}: {e}')
check('json_parse',not errors,errors)
v=json.loads((ROOT/'verification/verification_results.json').read_text())
check('numerical_checks_34_pass',v['passed'] and v['passed_count']==34 and v['total_count']==34,'Hard assertions executed separately')
h=hashlib.sha256((ROOT/'models/deposition_reference.py').read_bytes()).hexdigest()
for name in ['verification/verification_results.json','benchmarks/results/benchmark_summary.json','benchmarks/results/example.json']:
    check('model_hash_'+name,json.loads((ROOT/name).read_text())['model_sha256']==h,h)
ex=json.loads((ROOT/'benchmarks/results/example.json').read_text())
check('input_hash',ex['input_sha256']==hashlib.sha256((ROOT/'data/synthetic_case.json').read_bytes()).hexdigest(),'JSON run uses current input')
reg=json.loads((ROOT/'sources/source_registry.json').read_text())
check('eight_source_records',len(reg)==8 and len({x['source_id'] for x in reg})==8,[x['source_id'] for x in reg])
for s in reg:
    if s.get('original_path'):
        p=ROOT/s['original_path']
        if p.is_file():
            check('original_hash_'+s['source_id'],hashlib.sha256(p.read_bytes()).hexdigest()==s['original_sha256'],s['original_path'])
        else:
            check('permitted_archive_omission_'+s['source_id'],not s['rights']['redistribution_allowed'],'Original hash not checked: restricted raw archive intentionally absent from reader/public copy')
links=[]
for p in ROOT.rglob('*.md'):
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if re.match(r'^[a-zA-Z]+:',target) or target.startswith('#'):continue
        local=unquote(target.split('#')[0])
        if local and not (p.parent/local).exists():links.append([str(p.relative_to(ROOT)),target])
check('local_markdown_links',not links,links)
status=json.loads((ROOT/'stage_status.json').read_text())
check('physical_validation_unverified',status['physical_validation']=='not_performed','No device data claimed')
check('next_topic_is_t03',status['next_topic']=='T03','Serial roadmap preserved')
selected=[p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'originals' not in p.parts and 'deliverables' not in p.parts]
check('no_pyc_in_publish_selection',all(p.suffix!='.pyc' for p in selected),'Publication excludes __pycache__, sources/originals, deliverables and temporary files')
result={'scope':'artifact_integrity_only','passed':all(x['passed'] for x in checks),'passed_count':sum(x['passed'] for x in checks),'total_count':len(checks),'checks':checks}
(ROOT/'verification/release_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
if not result['passed']:sys.exit(1)
