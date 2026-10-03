"""Read-only static package checks; no browser or heavy calculations."""
from pathlib import Path
from html.parser import HTMLParser
import json,re,sys
ROOT=Path(__file__).resolve().parents[1]
class ReaderParser(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.links=[];self.resources=[];self.article_count=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.append(a['id'])
  if tag=='a' and 'href' in a:self.links.append(a['href'])
  if tag in {'script','img','iframe','source','video','audio'} and a.get('src'):self.resources.append(a['src'])
  if tag=='link' and a.get('href'):self.resources.append(a['href'])
  if tag=='article':self.article_count+=1
p=ReaderParser();p.feed((ROOT/'index.html').read_text())
errors=[]
if len(p.ids)!=len(set(p.ids)):errors.append('duplicate_html_ids')
for href in p.links:
 if href.startswith('#'):
  if href[1:] not in p.ids:errors.append('missing_anchor:'+href)
 elif not href.startswith('https://'):
  if href not in {'freeze_manifest.json','reader_manifest.json'} and not (ROOT/href).is_file():errors.append('missing_local_link:'+href)
if p.resources:errors.append('external_or_nonembedded_resources:'+repr(p.resources))
if p.article_count!=10:errors.append('wrong_chapter_count')
if re.search(r'url\s*\(', (ROOT/'index.html').read_text(),re.I):errors.append('css_url_dependency')
for file in ROOT.rglob('*.json'):
 if '__pycache__' not in file.parts:
  try:json.loads(file.read_text())
  except Exception as e:errors.append(str(file.relative_to(ROOT))+':'+str(e))
source_ids={s['source_id'] for s in json.loads((ROOT/'sources/source_registry.json').read_text())['sources']}
for sid in source_ids:
 if not (ROOT/'sources/summaries'/f'{sid}.md').is_file():errors.append('source_summary_missing:'+sid)
result={'static_ok':not errors,'errors':errors,'chapters':p.article_count,'source_count':len(source_ids),'local_links_checked':len([h for h in p.links if not h.startswith(('https://','#'))]),'no_external_resources':not p.resources,'browser_visual_or_interaction_verified':False,'manifest_links':'expected to exist after freeze; exempt only at prefreeze check','note':'No proof of layout, JavaScript runtime, source truth or normative compliance'}
print(json.dumps(result,ensure_ascii=False,indent=2));sys.exit(bool(errors))
