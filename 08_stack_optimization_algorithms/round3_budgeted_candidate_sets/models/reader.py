"""Offline payload, dependency and local-link verifier. No network or browser."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,hashlib,re,argparse
CONTROL={'verification/reader_manifest.json','verification/freeze_receipt.json','verification/isolated_reader_check.json','verification/integrity_negative_checks.json','verification/reader_check.json','verification/final_receipt_check.json','verification/outside_before.json','sources/local_archive_receipt.json'}
def eligible(rel):return rel not in CONTROL and not rel.startswith(('deliverables/','sources/originals/')) and '__pycache__' not in rel.split('/') and not rel.endswith('.pyc')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.assets=[];self.ids=[];self.scripts=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.append(a['id'])
  if tag=='a' and 'href'in a:self.links.append(a['href'])
  if 'src'in a:self.assets.append(a['src'])
  if tag=='link' and 'href'in a:self.assets.append(a['href'])
  if tag in ('script','iframe','object','embed'):self.scripts.append(tag)
def static_check(root):
 text=(root/'reader.html').read_text();p=Links();p.feed(text);p.close()
 if p.scripts or len(p.ids)!=len(set(p.ids)):raise ValueError('active_content_or_duplicate_ids')
 if re.search(r'@import|url\(',text,re.I):raise ValueError('unreviewed_css_resource')
 for uri in p.links+p.assets:
  u=urlsplit(uri)
  if u.scheme or u.netloc:
   if uri in p.assets or u.scheme not in ('https','http'):raise ValueError('external_asset_or_unsafe_scheme')
   continue
  if u.path:
   target=(root/unquote(u.path)).resolve()
   if root not in target.parents or not target.is_file():raise ValueError('missing_or_escaped_link:'+uri)
  elif u.fragment and u.fragment not in p.ids:raise ValueError('missing_anchor:'+uri)
 return {'local_links_and_anchors':sum(not urlsplit(x).scheme for x in p.links),'public_primary_source_links':sum(bool(urlsplit(x).scheme) for x in p.links),'local_image_assets':len(p.assets),'external_assets':0,'scripts':0,'html_layout':'unverified_existing_restriction_not_retried'}
def verify(root):
 root=Path(root).resolve();m=json.loads((root/'verification/reader_manifest.json').read_text());seen=set()
 for row in m['files']:
  rel=row['path'];p=root/rel
  if rel in seen or not eligible(rel) or p.is_symlink() or root not in p.resolve().parents:raise ValueError('unsafe_manifest_path')
  seen.add(rel)
  if not p.is_file() or p.stat().st_size!=row['bytes'] or sha(p)!=row['sha256']:raise ValueError('payload_hash_mismatch:'+rel)
 actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and eligible(str(p.relative_to(root)))}
 if seen!=actual:raise ValueError('payload_file_set_mismatch:'+str(sorted(seen^actual)))
 deps=json.loads((root/'data/frozen_dependencies.json').read_text())
 for row in deps:
  p=root/row['copy']
  if p.stat().st_size!=row['bytes'] or sha(p)!=row['sha256']:raise ValueError('dependency_hash_mismatch')
 result={'result':'passed','payload_files':len(seen),'payload_bytes':sum(x['bytes'] for x in m['files']),'manifest_sha256':sha(root/'verification/reader_manifest.json'),'copied_dependencies':len(deps),'sibling_dependencies':False,'network_needed':False,'original_papers_in_payload':False};result.update(static_check(root));return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--directory',default=str(Path(__file__).resolve().parents[1]));a=p.parse_args();print(json.dumps(verify(a.directory),indent=2))
