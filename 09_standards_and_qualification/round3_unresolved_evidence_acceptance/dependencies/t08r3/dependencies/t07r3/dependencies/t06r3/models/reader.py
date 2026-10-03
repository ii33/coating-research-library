"""Offline exact payload verifier. No sibling imports, network, or browser.
Freeze controls/receipts and local archive are explicitly outside payload.
"""
from pathlib import Path
from html.parser import HTMLParser
import argparse,json,hashlib,re
from urllib.parse import urlsplit,unquote
CONTROL={'verification/reader_manifest.json','verification/freeze_receipt.json','verification/isolated_reader_check.json','verification/integrity_negative_checks.json','verification/reader_check.json','verification/final_receipt_check.json'}
def eligible(rel):return rel not in CONTROL and not rel.startswith('deliverables/') and '__pycache__' not in rel.split('/') and not rel.endswith('.pyc')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.resources=[];self.ids=[];self.scripts=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id'in a:self.ids.append(a['id'])
        if tag=='a' and 'href'in a:self.links.append(a['href'])
        if 'src'in a:self.resources.append(a['src'])
        if tag=='link' and 'href'in a:self.resources.append(a['href'])
        if tag=='script':self.scripts.append(a)
def static_check(root):
    text=(root/'reader.html').read_text();p=Links();p.feed(text);p.close()
    if p.scripts:raise ValueError('reader_scripts_not_allowed')
    if len(set(p.ids))!=len(p.ids):raise ValueError('duplicate_html_ids')
    for uri in p.links+p.resources:
        u=urlsplit(uri)
        if u.scheme or u.netloc:
            if uri in p.resources or u.scheme not in ('https','http'):raise ValueError('external_resource_or_unsafe_scheme')
            continue
        if u.path:
            target=(root/unquote(u.path)).resolve()
            if root.resolve() not in target.parents or not target.is_file():raise ValueError('missing_or_escaped_local_link:'+uri)
        elif u.fragment and u.fragment not in p.ids:raise ValueError('missing_anchor:'+uri)
    if re.search(r'@import|url\(',text,re.I):raise ValueError('css_external_or_unreviewed_resource')
    return {'local_links_and_anchors':len(p.links),'local_image_resources':len(p.resources),'external_assets':0,'scripts':0,'html_layout':'unverified_existing_browser_socket_restriction_not_retried'}
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
        if sha(root/row['copy'])!=row['sha256']:raise ValueError('dependency_hash_mismatch')
    report={'result':'passed','payload_files':len(seen),'payload_bytes':sum(row['bytes'] for row in m['files']),'manifest_sha256':sha(root/'verification/reader_manifest.json'),'copied_dependencies':len(deps),'sibling_dependencies':False,'network_needed':False};report.update(static_check(root));return report
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--directory',default=str(Path(__file__).resolve().parents[1]));a=ap.parse_args();print(json.dumps(verify(a.directory),indent=2))
