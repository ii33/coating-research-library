"""Build local-only reader and exact non-circular receipts. No upload/network."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,zipfile
R=Path(__file__).resolve().parents[1]
EXCLUDE={'verification/origin_snapshot_local.json','verification/reader_manifest.json','verification/release_receipt.json','verification/freeze_record.json','verification/detached_reader_verification.json','verification/detached_reader_test.log','verification/public_allowlist.txt'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def payloads():
 out=[]
 for p in sorted(R.rglob('*')):
  if not p.is_file():continue
  rel=str(p.relative_to(R))
  if rel in EXCLUDE or any(x in p.relative_to(R).parts for x in ['originals_local','__pycache__','deliverables','.detached_validation']) or p.suffix=='.pyc':continue
  out.append({'path':rel,'bytes':p.stat().st_size,'sha256':sha(p)})
 return out
if __name__=='__main__':
 rows=payloads();manifest={'schema_version':'T04-r3-reader-content-1','hash_algorithm':'sha256','scope':'payload only; manifest itself excluded; no originals','files':rows,'payload_sha256':hashlib.sha256(canonical(rows)).hexdigest()}
 mp=R/'verification/reader_manifest.json';mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 names=[x['path'] for x in rows]+['verification/reader_manifest.json']
 (R/'verification/public_allowlist.txt').write_text('\n'.join(sorted(names))+'\n')
 archive=R/'deliverables/T04_round3_bounded_material_response_v0.1.0_reader.zip'
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name in sorted(names):
   info=zipfile.ZipInfo(name,date_time=(2026,10,2,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,(R/name).read_bytes())
 receipt={'stage_id':'T04-round3','version':'0.1.0','created_utc':datetime.now(timezone.utc).isoformat(),'archive':str(archive.relative_to(R)),'archive_bytes':archive.stat().st_size,'archive_sha256':sha(archive),'archive_entry_count':len(names),'payload_file_count':len(rows),'manifest_path':str(mp.relative_to(R)),'manifest_sha256':sha(mp),'payload_sha256':manifest['payload_sha256'],'receipt_inside_archive':False,'source_originals_in_archive':False,'publication_upload_push':False,'standalone_dependency_count':len(json.loads((R/'data/frozen_dependencies.json').read_text()))}
 (R/'verification/release_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 (R/'verification/freeze_record.json').write_text(json.dumps({'state':'local_freeze','content_identity':manifest['payload_sha256'],'manifest_sha256':sha(mp),'archive_sha256':sha(archive),'formal_model_chain':'pending','production_qualified':False,'point12':'partial_unchanged','point2':'conditional_non_strict_unchanged','next_stage_started':False},indent=2)+'\n')
 print(json.dumps(receipt,indent=2))
