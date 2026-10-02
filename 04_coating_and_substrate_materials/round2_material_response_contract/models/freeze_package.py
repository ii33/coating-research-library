"""Local deterministic payload freeze; never uploads, pushes or runs heavy tasks."""
import hashlib,json,subprocess,sys,zipfile
from pathlib import Path
from reader import ROOT,ARCHIVE,paths,digest,verify_zip
# Check unchanged original tree only when freezing within the full project.
project=ROOT.parents[1];baseline=json.loads((ROOT/'verification/unchanged_baseline.json').read_text())
changed=[p for p,h in baseline.items() if not (project/p).is_file() or digest((project/p).read_bytes())!=h]
current={str(p.relative_to(project)) for p in project.rglob('*') if p.is_file() and not p.is_relative_to(ROOT) and '__pycache__' not in p.parts}
added=sorted(current-set(baseline))
check={'status':'pass' if not changed and not added else 'fail','baseline_files':len(baseline),'changed_or_missing':changed,'added_outside_target':added,'excluded':'runtime __pycache__; target directory only allowed changes'}
(ROOT/'verification/outside_scope_check.json').write_text(json.dumps(check,ensure_ascii=False,indent=2)+'\n')
if changed or added:raise SystemExit('outside-scope change detected; inspect result before freeze')
files=[{'path':p,'bytes':(ROOT/p).stat().st_size,'sha256':digest((ROOT/p).read_bytes())} for p in paths(ROOT)]
manifest={'manifest_version':'1.0','scope':'exact standalone reader payload, excluding manifest self and outer receipts/archive/baseline','publication':'local_only_not_uploaded',
 'exclusions':['freeze_manifest.json self-hash','reader ZIP','verification/freeze_receipt.json','verification/unchanged_baseline.json','__pycache__ and .pyc runtime files'],
 'file_count':len(files),'total_payload_bytes':sum(r['bytes'] for r in files),'files':files}
(ROOT/'freeze_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
archive=ROOT/ARCHIVE
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for name in sorted([r['path'] for r in files]+['freeze_manifest.json']):
        info=zipfile.ZipInfo(name,date_time=(2026,10,2,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,(ROOT/name).read_bytes())
reader=verify_zip(archive)
receipt={'status':'local_frozen_reader_verified','manifest_sha256':digest((ROOT/'freeze_manifest.json').read_bytes()),
 'archive':ARCHIVE,'archive_sha256':digest(archive.read_bytes()),'archive_bytes':archive.stat().st_size,
 'payload_file_count':len(files),'zip_entry_count':len(files)+1,'reader':reader,'no_upload':True,'no_push':True,'high_compute':'not_run'}
(ROOT/'verification/freeze_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(receipt,ensure_ascii=False,indent=2))
