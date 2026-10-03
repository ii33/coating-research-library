"""Author-only exact freeze. Never pushes, uploads, deploys, archives, or invokes devices."""
from pathlib import Path
import hashlib,json,platform,importlib.metadata
from reader import paths,archive_entries,verify,EXCLUDED
ROOT=Path(__file__).resolve().parents[1]
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def outside_check():
    project=ROOT.parents[1];before=json.loads((ROOT/'verification/outside_before.json').read_text())
    now={p.relative_to(project).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in project.rglob('*') if p.is_file() and ROOT not in p.parents and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    changed=[k for k in before if now.get(k)!=before[k]];added=sorted(set(now)-set(before));status='passed' if not changed and not added else 'changed_unattributed'
    acknowledgment=ROOT/'verification/concurrent_planning_changes.json'
    if status!='passed' and acknowledgment.exists():
        ack={x['path']:x for x in json.loads(acknowledgment.read_text())['files']}
        if not added and set(changed)==set(ack) and all(ack[k]['before_sha256']==before[k] and ack[k]['current_sha256']==now[k] for k in changed):status='passed_with_attributed_concurrent_changes'
    result={'status':status,'original_snapshot_preserved':True,'before_files':len(before),'after_files':len(now),'unchanged_outside_files':len(before)-len(changed),'changed_or_removed':changed,'added':added,'meaning':'byte snapshot, not a Git commit; no silent rebaseline'}
    write(ROOT/'verification/outside_scope_check.json',result)
    if status=='changed_unattributed':raise ValueError('outside changes need exact coordinator attribution')
    return result

def freeze():
    outside=outside_check()
    exact=paths(ROOT);allowed=json.loads((ROOT/'data/reader_allowlist.json').read_text())['paths']
    if exact!=sorted(allowed):raise ValueError('review explicit allowlist before freeze')
    entries=[]
    for name in exact:
        b=(ROOT/name).read_bytes();entries.append({'path':name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
    write(ROOT/'freeze_manifest.json',{'format':'T07-R2-local-reader-v1','version':'T07-r2-v0.1.0','hash_algorithm':'SHA256',
      'files':entries,'local_only_originals':archive_entries(ROOT),'local_only_originals_in_reader':False,
      'excluded_paths':sorted(EXCLUDED),'excluded_patterns':['**/__pycache__/**','**/*.pyc'],
      'publication_authorized':False,'signature':'none'})
    receipt=verify(ROOT,True);receipt['outside_scope_status']=outside['status'];receipt['unchanged_outside_files']=outside['unchanged_outside_files']
    write(ROOT/'verification/freeze_receipt.json',receipt);print(json.dumps(receipt,ensure_ascii=False,indent=2))
if __name__=='__main__':freeze()
