"""Local-only exact reader archive. No upload or publication."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,zipfile
from reader_check import R,EXCLUDED,excluded,sha
if __name__=='__main__':
 rows=[{'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(R.rglob('*')) if p.is_file() and not excluded(p.relative_to(R))]
 canonical=json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
 m={'schema_version':'T05-r3-reader-payload-1','hash_algorithm':'sha256','scope':'payload only, no originals or circular metadata','excluded_metadata':sorted(EXCLUDED),'excluded_directories':['originals_local','deliverables','__pycache__'],'files':rows,'payload_sha256':hashlib.sha256(canonical).hexdigest()}
 mp=R/'verification/reader_manifest.json';mp.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
 names=sorted([x['path'] for x in rows]+['verification/reader_manifest.json']);(R/'verification/public_allowlist.txt').write_text('\n'.join(names)+'\n')
 archive=R/'deliverables/T05_round3_source_retention_identifiability_v0.1.0_reader.zip'
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name in names:
   info=zipfile.ZipInfo(name,date_time=(2026,10,2,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,(R/name).read_bytes())
 rec={'stage_id':'T05-round3','version':'0.1.0','created_utc':datetime.now(timezone.utc).isoformat(),'archive':str(archive.relative_to(R)),'archive_bytes':archive.stat().st_size,'archive_sha256':sha(archive),'archive_entry_count':len(names),'payload_file_count':len(rows),'manifest_path':str(mp.relative_to(R)),'manifest_sha256':sha(mp),'payload_sha256':m['payload_sha256'],'standalone_dependency_count':len(json.loads((R/'data/frozen_dependencies.json').read_text())),'source_originals_in_archive':False,'receipt_inside_archive':False,'publication_upload_push':False}
 (R/'verification/release_receipt.json').write_text(json.dumps(rec,indent=2)+'\n')
 (R/'verification/freeze_record.json').write_text(json.dumps({'state':'local_freeze','payload_sha256':m['payload_sha256'],'manifest_sha256':sha(mp),'archive_sha256':sha(archive),'formal_model_chain':'pending','production_qualified':False,'point12':'partial_unchanged','point2':'conditional_non_strict_unchanged','next_stage_started':False},indent=2)+'\n');print(json.dumps(rec,indent=2))
