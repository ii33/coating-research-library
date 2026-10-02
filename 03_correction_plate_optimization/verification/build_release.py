#!/usr/bin/env python3
"""Freeze the research package and build a reader ZIP without original sources."""
import json,hashlib,datetime,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def included(p):
 rel=p.relative_to(R)
 return p.is_file() and 'deliverables' not in rel.parts and '__pycache__' not in rel.parts and not str(rel).startswith('sources/originals/') and str(rel)!='verification/frozen_manifest.json'
files=[]
for p in sorted(R.rglob('*')):
 if included(p):files.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
identity=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
manifest=dict(version='T03-0.1',created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Theory and synthetic numerical verification only; designated formal review chain pending; no physical validation',content_id=identity,file_count=len(files),files=files)
(R/'verification/frozen_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
out=R/'deliverables/T03_mask_optimization_v0.1_reader.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for item in files:z.write(R/item['path'],R.name+'/'+item['path'])
 z.write(R/'verification/frozen_manifest.json',R.name+'/verification/frozen_manifest.json')
 dep=R.parent/'02_machine_modeling/models/deposition_reference.py';z.write(dep,'02_machine_modeling/models/deposition_reference.py')
 z.writestr('READ_FIRST.txt','T03 synthetic correction-mask design research. Start with 03_correction_plate_optimization/README.md. The minimal frozen T02 model is included for reproduction. Raw source HTML/PDF files are intentionally excluded. All polygons are synthetic and NOT released for fabrication. Run check_release.py --reader for package checks.\n')
print(json.dumps(dict(content_id=identity,file_count=len(files),zip=str(out),bytes=out.stat().st_size),indent=2))
