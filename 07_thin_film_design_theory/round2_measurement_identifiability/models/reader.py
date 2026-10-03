"""Verify an exact local reader payload, then reproduce only tiny checks in isolation.
Local-only licensed PDF archives can be present at author source; they are never copied.
Hashes detect accidental byte changes, not authenticated origin or malicious replacement.
"""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,os,shutil,subprocess,sys,tempfile
EXCLUDED={'freeze_manifest.json','verification/freeze_receipt.json','verification/outside_before.json','verification/outside_scope_check.json'}

def safe(name):
    p=PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or '\\' in name or not name:raise ValueError('unsafe relative path')
    return p

def archive_entries(root):
    entries=json.loads((root/'data/local_source_archive_manifest.json').read_text())['files']
    names=[]
    for x in entries:
        p=safe(x['path'])
        if not x['path'].startswith('sources/originals/') or p.suffix.lower()!='.pdf':raise ValueError('invalid local-only archive path')
        names.append(x['path'])
    if len(names)!=len(set(names)):raise ValueError('duplicate archive paths')
    return entries

def paths(root):
    archive={x['path'] for x in archive_entries(root)};out=[]
    for p in root.rglob('*'):
        if p.is_symlink():raise ValueError('symlinks forbidden')
        if not p.is_file():continue
        name=p.relative_to(root).as_posix();safe(name)
        if '__pycache__' in p.parts or p.suffix=='.pyc' or name in EXCLUDED:continue
        if name in archive:continue
        if 'originals' in p.parts or p.suffix.lower() in ('.pdf','.zip','.yml','.yaml'):raise ValueError('unregistered original/archive file')
        out.append(name)
    return sorted(out)

def match_file(root,item):
    safe(item['path']);p=(root/item['path']).resolve()
    if not p.is_relative_to(root):raise ValueError('escaped root')
    b=p.read_bytes()
    if len(b)!=item['bytes'] or hashlib.sha256(b).hexdigest()!=item['sha256']:raise ValueError('hash mismatch: '+item['path'])

def verify(root,recompute=True):
    root=Path(root).resolve();m=json.loads((root/'freeze_manifest.json').read_text())
    if set(m['excluded_paths'])!=EXCLUDED:raise ValueError('unexpected exclusions')
    entries=m['files'];names=[x['path'] for x in entries];allow=json.loads((root/'data/reader_allowlist.json').read_text())['paths']
    if len(names)!=len(set(names)) or len(allow)!=len(set(allow)):raise ValueError('duplicate payload paths')
    if sorted(names)!=sorted(allow) or sorted(names)!=paths(root):raise ValueError('exact payload/allowlist set mismatch')
    for item in entries:match_file(root,item)
    local=archive_entries(root)
    if m['local_only_originals']!=local:raise ValueError('archive metadata mismatch')
    present=[x for x in local if (root/x['path']).exists()]
    if present and len(present)!=len(local):raise ValueError('incomplete local archive set')
    for item in present:match_file(root,item)
    report={'status':'passed','payload_files':len(entries),'payload_bytes':sum(x['bytes'] for x in entries),
      'manifest_sha256':hashlib.sha256((root/'freeze_manifest.json').read_bytes()).hexdigest(),
      'local_only_originals_present':len(present),'local_only_original_bytes':sum(x['bytes'] for x in present),
      'raw_primary_sources_in_reader':False,'sibling_dependency':False,'network_access':False,
      'heavy_run':False,'real_device_validation':'not_run_awaiting_device','authenticated_signature':False}
    if recompute:
        with tempfile.TemporaryDirectory(prefix='t07-reader-') as td:
            dst=Path(td)
            for name in names:
                target=dst/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/name,target)
            shutil.copyfile(root/'freeze_manifest.json',dst/'freeze_manifest.json')
            if list(dst.rglob('*.pdf')):raise ValueError('local-only original copied by mistake')
            env={**os.environ,'PYTHONPATH':str(dst/'models'),'PYTHONDONTWRITEBYTECODE':'1'}
            for label,cmd in [('unit_tests',[sys.executable,'-m','unittest','discover','-s','tests','-v']),
                              ('data_qa',[sys.executable,'models/data_qa.py']),
                              ('batch_default',[sys.executable,'models/batch_driver.py']),
                              ('clean_reader_hash_check',[sys.executable,'models/reader.py','--hash-only'])]:
                p=subprocess.run(cmd,cwd=dst,env=env,capture_output=True,text=True,timeout=120)
                if p.returncode:raise ValueError(label+' failed: '+p.stdout+p.stderr)
                report[label]='passed'
                if label=='unit_tests':report['test_summary']=p.stderr.strip().splitlines()[-3:]
                if label=='batch_default' and json.loads(p.stdout)['status']!='plan_only':raise ValueError('batch executed unexpectedly')
            code="""import json,numpy as np
from diagnostics import run
from pathlib import Path
a=run();b=json.loads(Path('verification/diagnostics.json').read_text())
def cmp(a,b):
 if isinstance(a,dict):
  assert set(a)==set(b)
  for k in a:cmp(a[k],b[k])
 elif isinstance(a,list):
  assert len(a)==len(b)
  for x,y in zip(a,b):cmp(x,y)
 elif isinstance(a,(float,int)) and not isinstance(a,bool):assert np.isclose(a,b,rtol=2e-6,atol=1e-10),(a,b)
 else:assert a==b,(a,b)
cmp(a,b)
print('small saved diagnostics reproduced')
"""
            p=subprocess.run([sys.executable,'-c',code],cwd=dst,env=env,capture_output=True,text=True,timeout=120)
            if p.returncode:raise ValueError('isolated diagnostics mismatch: '+p.stdout+p.stderr)
            report['isolated_diagnostics']='passed';report['isolated_original_count']=0
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--hash-only',action='store_true');a=p.parse_args()
    print(json.dumps(verify(a.directory,not a.hash_only),ensure_ascii=False,indent=2))
