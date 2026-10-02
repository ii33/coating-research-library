"""Local integrity checks; not a scientific/conformity certification."""
import csv,json,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
errors=[]
for p in ROOT.rglob('*.json'):
 try: json.loads(p.read_text())
 except Exception as e: errors.append(f'{p.relative_to(ROOT)}: {e}')
for p in (ROOT/'templates').glob('*.csv'):
 rows=list(csv.reader(p.open()))
 if not rows or any(len(r)!=len(rows[0]) for r in rows):errors.append(f'CSV width {p.name}')
for p in ROOT.rglob('*.md'):
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if re.match(r'^[a-z]+://',link):continue
  target=link.split('#')[0]
  if target and not (p.parent/target).exists(): errors.append(f'broken link {p.relative_to(ROOT)} -> {link}')
reg=json.loads((ROOT/'data/source_registry.json').read_text())['sources']
std=json.loads((ROOT/'data/standards_map.json').read_text())['standards']
if len(reg)!=66: errors.append('unexpected source count')
if len(std)!=62: errors.append('unexpected standard record count')
for s in reg:
 if not (ROOT/s['summary_path']).exists():errors.append(f'missing summary {s["source_id"]}')
 if s['original_archived'] or s['redistribution_allowed']:errors.append('unexpected third-party original permission')
for s in std:
 if s['normative_clause'] is not None or s['acceptance_threshold'] is not None:errors.append('unexpected filled normative field')
orig=[p for p in (ROOT/'sources/originals').glob('*') if p.name!='README.md']
if orig:errors.append('third-party original exists; review exclusion')
result=dict(scope='JSON/CSV/links/source identity/unknown normative fields/archiving checks only',result='pass' if not errors else 'fail',errors=errors,sources=len(reg),standard_records=len(std),unit_tests_separate=True)
(ROOT/'reviews/integrity_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))
