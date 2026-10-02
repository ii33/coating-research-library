"""Local no-ZIP reader/checker. No network; verify bytes then re-run only light checks.
No installation. Tests execute in an isolated copy built from exactly the manifest payload.
"""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,sys,tempfile,shutil,subprocess,os
EXCLUDED={'freeze_manifest.json','verification/freeze_receipt.json','verification/outside_before.json','verification/outside_scope_check.json'}
def payload_paths(root):
 out=[]
 for p in root.rglob('*'):
  if p.is_symlink():raise ValueError('symlink not permitted: '+str(p))
  if p.is_file():
   rel=p.relative_to(root).as_posix()
   if '__pycache__' in p.parts or p.suffix=='.pyc' or rel in EXCLUDED:continue
   out.append(rel)
 return sorted(out)
def verify(root,recompute=True):
 root=Path(root).resolve();man=json.loads((root/'freeze_manifest.json').read_text())
 if set(man['excluded_paths'])!=EXCLUDED:raise ValueError('unexpected manifest exclusion policy')
 paths=[x['path'] for x in man['files']]
 if len(paths)!=len(set(paths)):raise ValueError('duplicate manifest path')
 if sorted(paths)!=payload_paths(root):raise ValueError('exact payload path-set mismatch')
 for item in man['files']:
  path=PurePosixPath(item['path'])
  if path.is_absolute() or '..' in path.parts or '\\' in item['path']:raise ValueError('unsafe relative path')
  p=(root/item['path']).resolve()
  if not p.is_relative_to(root):raise ValueError('path escapes root')
  data=p.read_bytes()
  if len(data)!=item['bytes'] or hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('content mismatch: '+str(path))
 result={'status':'passed','format':'plain_directory_no_zip','exact_payload_files':len(paths),
         'payload_bytes':sum(x['bytes'] for x in man['files']),'manifest_sha256':hashlib.sha256((root/'freeze_manifest.json').read_bytes()).hexdigest(),
         'raw_primary_sources_included':False,'heavy_run':False,'external_network':False}
 if recompute:
  with tempfile.TemporaryDirectory(prefix='t05-reader-') as td:
   copy=Path(td)
   for rel in paths:
    dest=copy/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/rel,dest)
   env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(copy/'models')}
   checks=[('unit_tests',[sys.executable,'-m','unittest','discover','-s','tests','-v']),('data_qa',[sys.executable,'models/data_qa.py']),
           ('default_heavy_plan',[sys.executable,'models/validation_driver.py'])]
   for name,cmd in checks:
    proc=subprocess.run(cmd,cwd=copy,env=env,text=True,capture_output=True,timeout=120)
    if proc.returncode:raise ValueError(name+' failed:\n'+proc.stdout+proc.stderr)
    result[name]='passed'
    if name=='unit_tests':result['test_summary']=proc.stderr.strip().splitlines()[-3:]
    if name=='default_heavy_plan' and json.loads(proc.stdout)['status']!='plan_only':raise ValueError('default unexpectedly ran heavy')
   script="""import json,numpy as np\nfrom diagnostics import run\nfrom pathlib import Path\na=run();b=json.loads(Path('verification/diagnostics.json').read_text())\ndef compare(x,y):\n if isinstance(x,dict):\n  assert set(x)==set(y)\n  for k in x:compare(x[k],y[k])\n elif isinstance(x,list):\n  assert len(x)==len(y)\n  for p,q in zip(x,y):compare(p,q)\n elif isinstance(x,(int,float)) and not isinstance(x,bool):assert np.isclose(x,y,rtol=2e-7,atol=1e-12), (x,y)\n else:assert x==y,(x,y)\ncompare(a,b)\nprint('deterministic diagnostics reproduced without sibling directories')\n"""
   proc=subprocess.run([sys.executable,'-c',script],cwd=copy,env=env,text=True,capture_output=True,timeout=120)
   if proc.returncode:raise ValueError('diagnostics mismatch:\n'+proc.stdout+proc.stderr)
   result['isolated_diagnostics']='passed'
 result['meaning']='implementation integrity and tiny synthetic checks; not physical validation or trusted-signature authentication'
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--hash-only',action='store_true');a=p.parse_args()
 print(json.dumps(verify(a.directory,not a.hash_only),indent=2,ensure_ascii=False))
