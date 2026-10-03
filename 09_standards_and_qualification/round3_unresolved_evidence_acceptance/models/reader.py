"""Portable exact payload/dependency/link checker. No solving or network."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,hashlib,re,argparse
CONTROL={'verification/reader_manifest.json','verification/freeze_receipt.json','verification/isolated_reader_check.json','verification/integrity_negative_checks.json','verification/reader_check.json','verification/final_receipt_check.json','verification/outside_before.json'}
def eligible(rel):return rel not in CONTROL and not rel.startswith('deliverables/') and '__pycache__'not in rel.split('/') and not rel.endswith('.pyc')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.assets=[];self.ids=[];self.active=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id'in a:self.ids.append(a['id'])
  if tag=='a'and'href'in a:self.links.append(a['href'])
  if 'src'in a:self.assets.append(a['src'])
  if tag=='link'and'href'in a:self.assets.append(a['href'])
  if tag in ('script','iframe','object','embed'):self.active.append(tag)
def static_check(root):
 t=(root/'reader.html').read_text();p=Links();p.feed(t);p.close()
 if p.active or len(p.ids)!=len(set(p.ids)):raise ValueError('active_or_duplicate')
 if re.search(r'@import|url\(',t,re.I):raise ValueError('unreviewed_css_resource')
 for uri in p.links+p.assets:
  u=urlsplit(uri)
  if u.scheme or u.netloc:
   if uri in p.assets or u.scheme not in ('https','http'):raise ValueError('external_asset_or_unsafe_scheme')
   continue
  if u.path:
   path=(root/unquote(u.path)).resolve()
   if root not in path.parents or not path.is_file():raise ValueError('missing_or_escaped_link:'+uri)
  elif u.fragment and u.fragment not in p.ids:raise ValueError('missing_anchor')
 return {'local_links':sum(not urlsplit(x).scheme for x in p.links),'primary_links':sum(bool(urlsplit(x).scheme)for x in p.links),'images':len(p.assets),'external_assets':0,'active_content':0,'html_layout':'unverified_existing_restriction_not_retried'}
def verify(directory):
 root=Path(directory).resolve();m=json.loads((root/'verification/reader_manifest.json').read_text());seen=set()
 for row in m['files']:
  rel=row['path'];p=root/rel
  if rel in seen or not eligible(rel) or p.is_symlink() or root not in p.resolve().parents:raise ValueError('unsafe_manifest_path')
  seen.add(rel)
  if not p.is_file() or p.stat().st_size!=row['bytes']or sha(p)!=row['sha256']:raise ValueError('payload_hash_mismatch:'+rel)
 actual={str(p.relative_to(root))for p in root.rglob('*')if p.is_file() and eligible(str(p.relative_to(root)))}
 if seen!=actual:raise ValueError('payload_file_set_mismatch:'+str(sorted(seen^actual)))
 deps=json.loads((root/'data/frozen_dependencies.json').read_text())
 for row in deps:
  p=root/row['copy']
  if p.stat().st_size!=row['bytes']or sha(p)!=row['sha256']:raise ValueError('dependency_hash_mismatch')
 return {'result':'passed','payload_files':len(seen),'payload_bytes':sum(r['bytes']for r in m['files']),'manifest_sha256':sha(root/'verification/reader_manifest.json'),'copied_dependencies':len(deps),'sibling_dependency':False,'network_needed':False,'numeric_replay_performed':False,**static_check(root)}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--directory',default=str(Path(__file__).resolve().parents[1]));a=p.parse_args();print(json.dumps(verify(a.directory),indent=2))
