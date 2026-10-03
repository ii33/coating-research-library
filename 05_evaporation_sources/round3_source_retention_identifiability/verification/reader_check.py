"""Exact local reader payload/dependency/HTML check. No network or layout claim."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib,json,sys
R=Path(__file__).resolve().parents[1]
EXCLUDED={'verification/origin_snapshot_local.json','verification/origin_integrity_check.json','verification/reader_manifest.json','verification/release_receipt.json','verification/freeze_record.json','verification/public_allowlist.txt','verification/detached_reader_verification.json','verification/detached_reader_test.log','verification/integrity_negative_checks.json'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def excluded(rel):return str(rel) in EXCLUDED or any(x in rel.parts for x in ['originals_local','deliverables','__pycache__']) or rel.suffix=='.pyc'
def check(root=R):
 errors=[];root=root.resolve();m=json.loads((root/'verification/reader_manifest.json').read_text());rows=m['files'];expected={x['path'] for x in rows}
 if len(expected)!=len(rows):errors.append('duplicate_manifest_paths')
 canonical=json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
 if hashlib.sha256(canonical).hexdigest()!=m['payload_sha256']:errors.append('manifest_payload_digest')
 actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and not excluded(p.relative_to(root))}
 for path in sorted(actual-expected):errors.append('unexpected_payload:'+path)
 for row in rows:
  p=(root/row['path']).resolve()
  if not p.is_relative_to(root) or not p.is_file():errors.append('missing_or_outside:'+row['path']);continue
  if p.stat().st_size!=row['bytes'] or sha(p)!=row['sha256']:errors.append('hash_or_size:'+row['path'])
 deps=json.loads((root/'data/frozen_dependencies.json').read_text())
 for row in deps:
  p=(root/row['copy']).resolve()
  if not p.is_relative_to(root) or not p.is_file() or sha(p)!=row['sha256']:errors.append('dependency:'+row['copy'])
 class Parser(HTMLParser):
  def __init__(self):super().__init__();self.ids=set();self.urls=[]
  def handle_starttag(self,tag,attrs):
   a=dict(attrs)
   if 'id'in a:self.ids.add(a['id'])
   for k in ['src','href']:
    if k in a:self.urls.append(a[k])
 p=Parser();p.feed((root/'reader.html').read_text())
 for u in p.urls:
  if u.startswith(('https://','http://','mailto:')):continue
  if u.startswith('#'):
   if u[1:] not in p.ids:errors.append('missing_anchor:'+u)
  else:
   x=(root/u.split('#')[0]).resolve()
   if not x.is_relative_to(root) or not x.is_file():errors.append('missing_asset:'+u)
 out={'status':'integrity_passed' if not errors else 'integrity_failed','payload_files':len(rows),'copied_dependencies':len(deps),'html_local_references_checked':True,'browser_layout':'unverified_known_socket_permission_boundary','errors':errors,'scientific_certification':False};return out
if __name__=='__main__':
 out=check();print(json.dumps(out,indent=2));raise SystemExit(0 if not out['errors'] else 1)
