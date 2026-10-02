"""Freeze original deliverables only; omit originals, caches and local render QA."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
files=[]
for p in sorted(P.rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(P)
 if any(x in ('__pycache__','qa_render') for x in rel.parts) or str(rel).startswith('sources/originals/') or p.suffix=='.pyc' or str(rel)=='data/deliverable_manifest.json':continue
 b=p.read_bytes();files.append(dict(path=str(rel),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),original_project_artifact=True))
out=dict(version='T09-r1-v0.1.0',scope='T09 original reports/metadata/templates/code only',excluded=['sources/originals/**','qa_render/**','**/__pycache__/**','**/*.pyc'],files=files,file_count=len(files),total_bytes=sum(x['bytes'] for x in files))
(P/'data/deliverable_manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ['file_count','total_bytes']}))
