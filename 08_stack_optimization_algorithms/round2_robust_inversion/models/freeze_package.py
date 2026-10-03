"""Author-only freeze; no push, upload, deploy, hardware action or heavy computation."""
from pathlib import Path
import json
from reader import payload_paths,digest,verify,LOCAL
ROOT=Path(__file__).resolve().parents[1]
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def outside_check():
 P=ROOT.parents[1];before=json.loads((ROOT/'verification/outside_before.json').read_text())
 now={p.relative_to(P).as_posix():digest(p) for p in P.rglob('*') if p.is_file() and ROOT not in p.parents and '__pycache__' not in p.parts and p.suffix!='.pyc'}
 changed=[{'path':k,'before_sha256':v,'current_sha256':now.get(k)} for k,v in before.items() if now.get(k)!=v]
 added=[{'path':k,'current_sha256':v} for k,v in now.items() if k not in before]
 result={'status':'passed' if not changed and not added else 'changed_unattributed','before_files':len(before),'after_files':len(now),'changed':changed,'added':added,'original_snapshot_preserved':True}
 if changed or added:
  ack=ROOT/'verification/concurrent_changes.json'
  if ack.exists():
   approved=json.loads(ack.read_text())
   if approved['changed']==changed and approved['added']==added and approved.get('coordinator_confirmed') is True:result['status']='passed_with_attributed_concurrent_changes'
 write(ROOT/'verification/outside_scope_check.json',result)
 if result['status']=='changed_unattributed':raise ValueError('outside changes need exact attribution, never rebaseline')
 return result
if __name__=='__main__':
 outside=outside_check();names=payload_paths(ROOT)
 allowed=json.loads((ROOT/'data/reader_allowlist.json').read_text())['paths']
 if names!=allowed:raise ValueError('explicit allowlist must match before freeze')
 original=json.loads((ROOT/'data/local_originals_manifest.json').read_text())['files']
 manifest={'format':'T08-R2-local-reader-v1','version':'T08-r2-v0.1.0','hash_algorithm':'SHA256','signature':'none','publication_authorized':False,
   'files':[{'path':n,'bytes':(ROOT/n).stat().st_size,'sha256':digest(ROOT/n)} for n in names],
   'local_only_originals':original,'local_only_originals_in_reader':False,'excluded_paths':sorted(LOCAL),'excluded_patterns':['sources/originals/**','**/__pycache__/**','**/*.pyc']}
 write(ROOT/'freeze_manifest.json',manifest);r=verify(ROOT,True);r.update(outside_scope_status=outside['status'],unchanged_outside_files=len(json.loads((ROOT/'verification/outside_before.json').read_text()))-len(outside['changed']))
 write(ROOT/'verification/freeze_receipt.json',r);print(json.dumps(r,indent=2))
