"""Machine-readable QA independent of output target thickness; no external sources needed."""
from pathlib import Path
import json,re
from contract import validate,convert
R=Path(__file__).resolve().parents[1]
def run():
 reg=json.loads((R/'sources/source_registry.json').read_text());ids=[s['source_id'] for s in reg]
 if len(ids)!=len(set(ids)):raise ValueError('duplicate source IDs')
 for s in reg:
  p=(R/s['summary_path']).resolve()
  if not p.is_relative_to(R) or not p.is_file():raise ValueError('invalid source summary path')
  if s['original_path'] is not None:raise ValueError('this package promises no redistributed originals')
 examples={}
 for p in sorted((R/'examples').glob('*.json')):
  r=json.loads(p.read_text());validate(r);examples[p.name]=convert(r)['status']
 found=set()
 for directory in ['reports','examples','data']:
  for p in (R/directory).rglob('*'):
   if p.is_file():found.update(re.findall(r'T05-R2-S\d+',p.read_text(errors='replace')))
 if found-set(ids):raise ValueError('unresolved source IDs: '+str(found-set(ids)))
 return {'status':'passed','source_count':len(ids),'source_ids_unique':True,'all_summaries_present':True,'local_primary_originals':0,
         'referenced_source_ids_resolve':True,'examples':examples,'actual_unknowns_imputed':False,'schema':'Draft202012 strict additionalProperties false',
         'not_checked':['actual instrument model or raw device logs','true vapor mixture','real geometry/capture/density','full Lu-Lewis paper','production tooling or optical performance']}
if __name__=='__main__':
 r=run();print(json.dumps(r,indent=2));(R/'verification/data_qa.json').write_text(json.dumps(r,indent=2)+'\n')
