"""Read-only package checks, except its own QA report. Not process qualification."""
from pathlib import Path
import hashlib,json,re,csv,sys,argparse
import jsonschema
P=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description='Check T10 package; reader releases intentionally exclude third-party originals.')
parser.add_argument('--reader',action='store_true',help='Validate the shareable reader package without requiring local-only source originals.')
args=parser.parse_args()
issues=[]
def fail(x):issues.append(x)
def load(n):return json.loads((P/n).read_text())
# Strict JSON including non-finite values
for f in P.rglob('*.json'):
 if 'originals' in f.parts:continue
 try:json.loads(f.read_text(),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
 except Exception as e:fail(f'JSON {f.relative_to(P)}: {e}')
reg=load('data/source_registry.json');ids={r['source_id'] for r in reg}
if len(ids)!=len(reg):fail('duplicate source ids')
for r in reg:
 if not r['url'].startswith('https://'):fail(f'non https source {r["source_id"]}')
 if r['release_original']:fail('source originals cannot be released')
 if not (P/'sources/summaries'/f'{r["source_id"]}.md').exists():fail('missing summary')
for row in load('data/material_response_matrix.json'):
 if not set(row['source_ids'])<=ids:fail('unresolved material source')
 if row['process_qualified'] or row['kaufman_production_current_A'] is not None or row['kaufman_production_voltage_V'] is not None:fail('unauthorized recipe/qualification')
# Local Markdown link checks. Fragments ignored, remote links are not crawled here.
checked_links=0
for f in P.rglob('*.md'):
 if 'originals' in f.parts:continue
 for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)',f.read_text()):
  if link.startswith(('https://','http://','#','mailto:')):continue
  target=link.split('#')[0]
  if not target:continue
  checked_links+=1
  if not (f.parent/target).resolve().exists():fail(f'broken link {f.relative_to(P)} -> {target}')
 for sid in re.findall(r'\bIS-\d\d\b',f.read_text()):
  if sid not in ids:fail(f'unknown source id {sid} in {f.relative_to(P)}')
jsonschema.validate(load('data/measurement_record_template.json'),load('data/ion_assist_record.schema.json'))
if not args.reader:
 for row in load('data/local_originals_manifest.json'):
  f=P/row['path']
  if not f.exists() or hashlib.sha256(f.read_bytes()).hexdigest()!=row['sha256']:fail('original integrity failure '+row['path'])
for row in load('data/frozen_dependencies.json'):
 f=P.parent/row['path']
 if not f.exists() or hashlib.sha256(f.read_bytes()).hexdigest()!=row['sha256']:fail('frozen dependency changed '+row['path'])
# Explicitly independent from any future product thresholds.
r=load('data/demo_results.json')
if abs(r['uncertainty']['monte_carlo_cv']/r['uncertainty']['exact_lognormal_cv']-1)>.02:fail('synthetic uncertainty consistency')
if not r['disclaimer'].startswith('SYNTHETIC ONLY'):fail('missing synthetic label')
report={'status':'passed' if not issues else 'failed','checked_on':'2026-10-02','mode':'reader' if args.reader else 'local_with_originals','original_integrity':'not_checked_by_design' if args.reader else 'checked','source_records':len(reg),'material_records':len(load('data/material_response_matrix.json')),'local_markdown_links_checked':checked_links,'issues':issues,'interpretation':'structure/source links and numerical consistency only; not independent physics review or qualification'}
(P/('reviews/reader_integrity_check.json' if args.reader else 'reviews/integrity_check.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2));sys.exit(bool(issues))
