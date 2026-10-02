#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
files={}
for p in sorted(ROOT.rglob('*')):
 if not p.is_file() or '__pycache__' in p.parts or 'originals' in p.parts or 'reviews' in p.parts:continue
 if p.name=='deliverable_manifest.json':continue
 files[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
baseline=hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()
manifest=dict(schema_version='1.0',baseline=baseline,hashes=files,public_excludes=['sources/originals/** except README.md and .gitignore','__pycache__','*.pyc'],note='Third-party full text remains local only')
(ROOT/'data/deliverable_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
stage=dict(stage_id='T08',algorithmic=True,baseline=dict(kind='sha256_of_sorted_core_file_hashes',value=baseline),research_first_pass_status='ready_for_coordinator_acceptance_and_T09_handoff',actual_checks=dict(unit_tests=dict(result='pass',count=36,evidence='reviews/test_output.txt'),package=dict(result='pass',evidence='reviews/package_check_output.json'),clean_copy=dict(result='pass_smoke_not_full_benchmark',evidence='reviews/clean_copy_output.txt'),mathematical_spot_check=dict(result='completed_narrow_scope',executor='GPT-6 Luna',evidence='reviews/MATH_SPOT_CHECK.md'),production_measurements=dict(result='not_performed')),deepseek_self_review=dict(result='pending',evidence=[]),seed_review=dict(result='pending',findings=[]),sol_algorithm_review=dict(result='pending',findings=[]),final_status='awaiting_seed',assumptions=['isotropic passive planar media','fixed proxy material data, not measured','front finite stack only','all extrema sampled, no continuous guarantee'],open_issues='reviews/OPEN_ISSUES.md',core_sha256=files)
(ROOT/'reviews/ROUND1_STAGE_PACKAGE.json').write_text(json.dumps(stage,ensure_ascii=False,indent=2)+'\n');print(baseline,len(files))
