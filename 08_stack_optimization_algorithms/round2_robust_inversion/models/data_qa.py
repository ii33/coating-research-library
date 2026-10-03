"""Small static/data audit; no fitting, hardware or network actions."""
from pathlib import Path
import hashlib,json,re
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
class Links(HTMLParser):
 def __init__(self):super().__init__();self.refs=[];self.ids=set();self.remote_assets=[]
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if 'id' in d:self.ids.add(d['id'])
  for k in ['href','src']:
   if k in d:self.refs.append(d[k])
  if tag in ['script','img','link'] and any(d.get(k,'').startswith(('http:','https:')) for k in ['href','src']):self.remote_assets.append(d)
def run():
 errors=[];n=0
 for p in ROOT.rglob('*.json'):
  if 'originals' in p.parts:continue
  json.loads(p.read_text(),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)));n+=1
 for r in json.loads((ROOT/'data/frozen_dependencies.json').read_text()):
  if hashlib.sha256((ROOT/r['copy']).read_bytes()).hexdigest()!=r['sha256']:errors.append('changed vendor '+r['copy'])
 p=Links();p.feed((ROOT/'index.html').read_text())
 for ref in p.refs:
  if ref.startswith(('https:','http:','mailto:')):continue
  if ref.startswith('#'):
   if ref[1:] not in p.ids:errors.append('missing anchor '+ref)
  elif not (ROOT/ref).is_file():errors.append('missing local link '+ref)
  if 'sources/originals/' in ref:errors.append('original linked '+ref)
 if p.remote_assets:errors.append('remote runtime assets')
 plan=json.loads((ROOT/'verification/batch_plan_receipt.json').read_text())
 if plan['status']!='plan_only' or plan['fit_start_jobs']!=163584:errors.append('default plan invalid')
 receipt=json.loads((ROOT/'verification/tiny_final_receipt.json').read_text())
 if receipt['ledger']['vector_calls']>receipt['ledger']['cap']:errors.append('budget exceeded')
 diag=json.loads((ROOT/'verification/diagnostics.json').read_text())
 a=diag['local_rank2_global_alias']
 if a['local']['rank']!=2 or len(a['discovery']['clusters'])!=2 or a['max_alias_residual']>1e-12:errors.append('saved alias evidence inconsistent')
 if diag['precise_biased_candidate']['actual_mse']<=diag['precise_biased_candidate']['baseline_variance']:errors.append('saved bias counterexample inconsistent')
 result={'status':'passed' if not errors else 'failed','json_files_read':n,'relative_and_external_links':len(p.refs),'remote_runtime_assets':len(p.remote_assets),'errors':errors,'originals_linked':False,'heavy_run':False}
 if errors:raise ValueError(result)
 return result
if __name__=='__main__':
 r=run();(ROOT/'verification/data_qa.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
