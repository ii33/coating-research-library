"""Read-only payload integrity plus optional isolated SMALL checks. Never heavy run."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
LOCAL={'freeze_manifest.json','verification/freeze_receipt.json','verification/outside_before.json','verification/outside_scope_check.json','verification/isolated_reader_receipt.json','verification/concurrent_changes.json'}
def payload_paths(root):
 return sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.relative_to(root).as_posix() not in LOCAL and not p.relative_to(root).as_posix().startswith('sources/originals/') and '__pycache__' not in p.parts and p.suffix!='.pyc')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def verify(root,local=False):
 root=Path(root).resolve();m=json.loads((root/'freeze_manifest.json').read_text());expected={r['path']:r for r in m['files']}
 allowed=json.loads((root/'data/reader_allowlist.json').read_text())['paths']
 if sorted(expected)!=sorted(allowed):raise ValueError('allowlist differs from manifest')
 actual=payload_paths(root)
 if sorted(expected)!=actual:raise ValueError('missing/extra payload paths: '+repr(set(expected)^set(actual)))
 for name,r in expected.items():
  p=root/name
  if p.is_symlink() or not p.resolve().is_relative_to(root):raise ValueError('symlink/path escape')
  if p.stat().st_size!=r['bytes'] or digest(p)!=r['sha256']:raise ValueError('changed bytes: '+name)
 if local:
  originals=m['local_only_originals'];actual_orig=sorted(p.relative_to(root).as_posix() for p in (root/'sources/originals').glob('*') if p.is_file())
  if actual_orig!=sorted(x['path'] for x in originals):raise ValueError('original archive paths differ')
  for q in originals:
   if digest(root/q['path'])!=q['sha256']:raise ValueError('local original bytes changed')
 return {'status':'passed','payload_files':len(expected),'payload_bytes':sum(r['bytes'] for r in expected.values()),'manifest_sha256':digest(root/'freeze_manifest.json'),'source_originals_in_payload':False,'heavy_run':False}
def isolated(root):
 root=Path(root).resolve();first=verify(root)
 with tempfile.TemporaryDirectory(prefix='t08-reader-') as td:
  dst=Path(td)
  for name in payload_paths(root)+['freeze_manifest.json']:
   (dst/name).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/name,dst/name)
  copycheck=verify(dst);env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(dst/'models')}
  commands=[]
  for cmd in [['python','-m','unittest','discover','-s','tests','-v'],['python','models/batch_driver.py']]:
   r=subprocess.run(cmd,cwd=dst,env=env,capture_output=True,text=True);commands.append({'command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
   if r.returncode:raise RuntimeError('isolated small check failed: '+r.stderr)
  # No fixtures regenerated, no tiny/full execution. Verify copied bytes stayed exact.
  verify(dst)
 return {'status':'passed','copy':copycheck,'checks':commands,'before':first,'originals_copied':False,'isolated_tests_only':True}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,default=ROOT);p.add_argument('--isolated',action='store_true');a=p.parse_args()
 print(json.dumps(isolated(a.directory) if a.isolated else verify(a.directory),ensure_ascii=False,indent=2))
