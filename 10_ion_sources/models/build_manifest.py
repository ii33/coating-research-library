from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parents[1]
EXCLUDE={'release_manifest.json'}
files=[];excluded=[]
for p in sorted(P.rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(P).as_posix()
 if rel in EXCLUDE:continue
 if rel.startswith('sources/originals/') or '__pycache__' in p.parts or p.suffix=='.pyc':
  excluded.append(rel);continue
 b=p.read_bytes();files.append({'path':rel,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
d={'version':'T10-r1-v0.1.0','status':'ready_for_review','release_scope':'original reports/summaries/data/figures/offline code only','excluded_patterns':['sources/originals/**','**/__pycache__/**','**/*.pyc'],'excluded_files':excluded,'files':files,'file_count':len(files),'total_bytes':sum(r['bytes'] for r in files),'no_process_qualification':True}
(P/'release_manifest.json').write_text(json.dumps(d,ensure_ascii=False,indent=2));print('release files',len(files),'bytes',d['total_bytes'],'excluded',len(excluded))
