"""Read-only local integrity/asset/dependency check. No network or scientific certification."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib,json,sys
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check():
 m=json.loads((R/'verification/reader_manifest.json').read_text());errors=[]
 for row in m['files']:
  p=(R/row['path']).resolve()
  if not p.is_relative_to(R.resolve()) or not p.is_file():errors.append('missing_or_outside:'+row['path']);continue
  if p.stat().st_size!=row['bytes'] or sha(p)!=row['sha256']:errors.append('hash_or_size:'+row['path'])
 deps=json.loads((R/'data/frozen_dependencies.json').read_text())
 for row in deps:
  p=R/row['copy']
  if not p.is_file() or sha(p)!=row['sha256']:errors.append('dependency:'+row['copy'])
 class Parser(HTMLParser):
  def __init__(self):super().__init__();self.ids=set();self.urls=[]
  def handle_starttag(self,tag,attrs):
   a=dict(attrs)
   if 'id'in a:self.ids.add(a['id'])
   for k in ['src','href']:
    if k in a:self.urls.append(a[k])
 p=Parser();p.feed((R/'reader.html').read_text())
 for u in p.urls:
  if u.startswith(('https://','http://','mailto:')):continue
  if u.startswith('#'):
   if u[1:] not in p.ids:errors.append('missing_anchor:'+u)
  elif not (R/u.split('#')[0]).is_file():errors.append('missing_asset:'+u)
 result={'status':'integrity_passed' if not errors else 'integrity_failed','payload_files':len(m['files']),'copied_dependencies':len(deps),'html_local_references_checked':True,'browser_layout':'unverified_known_socket_permission_boundary','errors':errors,'scientific_certification':False}
 print(json.dumps(result,indent=2));return not errors
if __name__=='__main__':raise SystemExit(0 if check() else 1)
