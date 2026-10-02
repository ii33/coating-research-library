#!/usr/bin/env python3
"""Local package/data checks. Does not claim link HTTP availability or production qualification."""
from pathlib import Path
import json,csv,re,hashlib,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
checks=[]
def check(name,condition,detail=''):
 checks.append(dict(check=name,passed=bool(condition),detail=detail))
sources=json.loads((ROOT/'data/source_registry.json').read_text())['sources'];ids=[s['id'] for s in sources]
check('24 unique source identifiers',len(ids)==24 and len(set(ids))==24)
check('all source summaries exist',all((ROOT/s['summary_path']).is_file() for s in sources))
check('source locators and limitations explicit',all(s['locator'] and s['limitations'] and s['original_archival_status'] for s in sources))
examples=json.loads((ROOT/'data/starter_stacks.json').read_text())['examples'];m=json.loads((ROOT/'data/material_proxies.json').read_text())['materials']
check('6 complete synthetic examples',len(examples)==6 and all(e['evidence']=='synthetic_reference_calculation_not_measured' and e['production_ready'] is False for e in examples))
check('all layers reference known proxies',all(d['material'] in m for e in examples for d in e['layers']))
check('every proxy carries source and uncertainty',all(v['anchor_records'] and v['assumptions'] and v['uncertainty'] and v['design_ready'] is False for v in m.values()))
check('back surface and absorption explicit',all('rear' in e and 'bulk_alpha_status' in e and e['substrate_mm']>0 for e in examples))
valid_csv=True
for e in examples:
 with (ROOT/'data/spectra'/f'{e["id"]}_spectrum.csv').open() as f:
  reader=csv.DictReader(f);rows=list(reader)
 valid_csv &= len(rows)==e['wavelength_grid_um'][2] and '0_s_front_R' in reader.fieldnames and '0_p_T' in reader.fieldnames
check('CSV counts and columns match definitions',valid_csv)
metrics=json.loads((ROOT/'data/finite_band_metrics.json').read_text())
check('metrics cover every angle and band',all(len(v['metrics'])==len(e['angles_deg'])*len(e['polarizations'])*len(e['bands_um']) for e,v in zip(examples,metrics)))
check('8 narrative chapters exist',len([p for p in (ROOT/'reports').glob('*.md') if re.match(r'^0[1-8]_',p.name)])==8)
bad=[]
for file in ROOT.rglob('*.md'):
 for link in re.findall(r'\]\(([^)]+)\)',file.read_text()):
  if '://' in link or link.startswith('#') or link.startswith('mailto:'):continue
  target=link.split('#')[0]
  if target and not (file.parent/target).exists():bad.append((str(file.relative_to(ROOT)),target))
check('local Markdown targets exist',not bad,str(bad))
found=set()
for file in (ROOT/'reports').glob('*.md'):found.update(re.findall(r'\bF\d{2}\b',file.read_text()))
check('all F citations registered',found<=set(ids),str(sorted(found-set(ids))))
for f in (ROOT/'figures').glob('*.svg'):ET.parse(f)
check('2 SVG files parse',len(list((ROOT/'figures').glob('*.svg')))==2)
originals_dir=ROOT/'sources/originals'
originals=[p for p in originals_dir.iterdir() if p.name not in ['README.md','.gitignore']] if originals_dir.exists() else []
check('no originals in this topic',not originals)
check('T07 interface and handoff exist',(ROOT/'T07_HANDOFF.md').exists() and (ROOT/'data/design_request_template.json').exists())
result=dict(passed=all(c['passed'] for c in checks),checks=checks,scope='local structural and provenance checks only',files_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'models').glob('*.py'))})
(ROOT/'reviews/package_check_output.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(0 if result['passed'] else 1)
