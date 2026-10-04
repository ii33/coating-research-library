import json,hashlib,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
d=json.loads((HERE/'researched_materials.json').read_text())
materials=d['materials'];by={m['id']:m for m in materials}
assert len(materials)==len(by)==28
assert by['H4_film']['formula'] is None
assert by['ITO_film']['formula'] is None
assert by['YbF3_film']['formula']=='YbF3'
assert by['ZnS_film']['roles']==['film'] and by['ZnS_substrate']['roles']==['substrate']
def collect_refs(obj):
 refs=set()
 if isinstance(obj,dict):
  for key,value in obj.items():
   if key=='source_ref' and isinstance(value,str):refs.add(value)
   elif key=='evidence_refs' and isinstance(value,list):refs.update(value)
   refs.update(collect_refs(value))
 elif isinstance(obj,list):
  for value in obj:refs.update(collect_refs(value))
 return refs
ids=set()
for m in materials:
 assert re.fullmatch(r'[A-Za-z0-9_-]+',m['id']) and len('builtin_research_'+m['id'])<=80
 sources={s['id'] for s in m['sources']}
 assert not m.get('unresolved_evidence_refs'),m['id']
 assert collect_refs(m.get('response_contract',{}))<=set(m['resolved_evidence']),m['id']
 if 'fields' in m.get('response_contract',{}):
  for f in m['response_contract']['fields'].values():
   assert set(f.get('evidence_refs',[]))<=set(m['resolved_evidence']),m['id']
 assert m['provenance_input_files']==d['input_files'],m['id']
 for p in m['properties']:
  assert p['id'] not in ids,p['id'];ids.add(p['id'])
  assert p['unit'] and p['conditions'] and p['status'] in ['verified','conditional','unknown','quarantined'],p['id']
  if p['status']=='unknown':assert p['value'] is None,p['id']
  if p['status'] in ['verified','conditional']:assert p['source_ids'] and set(p['source_ids'])<=sources,(m['id'],p['id'])
  assert all(s in sources for s in p['source_ids']),(m['id'],p['id'])
 if 'boat'in m['roles']:assert 'film' not in m['roles']
for path,info in d['input_files'].items():
 b=(ROOT/path).read_bytes();assert len(b)==info['bytes'] and hashlib.sha256(b).hexdigest()==info['sha256'],path
original=json.loads((ROOT/'04_coating_and_substrate_materials/data/property_records.json').read_text())['records']
for r in original:
 p=next(p for p in by[r['material_id']]['properties'] if p['id']==r['record_id'])
 assert p['original_record']==r and p['value']==r['value']
 if r.get('status')=='quarantined':assert p['status']=='quarantined'
assert len(original)==207
ito=by['ITO_film']['properties'];assert len({p['conditions']['observation_id'] for p in ito if 'observation_id'in p['conditions']})==30
assert all(p['status']=='quarantined' for p in ito if p['id'].startswith('ITO-O029-'))
for p in by['ZnS_film']['properties']:
 if p['name'].startswith('vapor_pressure_anchor'):assert p['source_ids']==['IR02'] and 'temperature_degC'in p['conditions']
report={'passed':True,'materials':len(materials),'properties':len(ids),'input_files_hash_verified':len(d['input_files']),'original_t04_rows_losslessly_preserved':len(original),'ito_samples_preserved':30,'dataset_sha256':hashlib.sha256((HERE/'researched_materials.json').read_bytes()).hexdigest()}
(HERE/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
