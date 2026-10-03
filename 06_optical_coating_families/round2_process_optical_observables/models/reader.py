"""Self-contained local reader integrity check; plain directory, no ZIP/network.
Hash validation is not trusted-signature authentication. Recompute only tiny checks.
"""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,os,shutil,subprocess,sys,tempfile
EXCLUDED={'freeze_manifest.json','verification/freeze_receipt.json','verification/outside_before.json','verification/outside_scope_check.json'}
def paths(root):
 out=[]
 for p in root.rglob('*'):
  if p.is_symlink():raise ValueError('symlink forbidden: '+str(p))
  if p.is_file():
   rel=p.relative_to(root).as_posix()
   if '__pycache__' in p.parts or p.suffix=='.pyc' or rel in EXCLUDED:continue
   if p.suffix.lower() in ('.zip','.pdf','.yml','.yaml') or 'originals' in p.parts:raise ValueError('raw sources/archive not permitted: '+rel)
   out.append(rel)
 return sorted(out)
def verify(root,recompute=True):
 root=Path(root).resolve();manifest=json.loads((root/'freeze_manifest.json').read_text());allow=json.loads((root/'data/reader_allowlist.json').read_text())['paths']
 if set(manifest['excluded_paths'])!=EXCLUDED:raise ValueError('unexpected exclusion policy')
 entries=manifest['files'];names=[a['path'] for a in entries]
 if len(names)!=len(set(names)) or len(allow)!=len(set(allow)):raise ValueError('duplicate paths')
 for name in names:
  p=PurePosixPath(name)
  if p.is_absolute() or '..' in p.parts or '\\' in name:raise ValueError('unsafe relative path')
 if sorted(names)!=sorted(allow) or sorted(names)!=paths(root):raise ValueError('exact allowlist/payload path-set mismatch')
 for item in entries:
  p=(root/item['path']).resolve()
  if not p.is_relative_to(root):raise ValueError('path escapes root')
  data=p.read_bytes()
  if len(data)!=item['bytes'] or hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('payload hash mismatch: '+item['path'])
 report={'status':'passed','format':'plain_directory_no_zip','exact_payload_files':len(names),'payload_bytes':sum(i['bytes'] for i in entries),'manifest_sha256':hashlib.sha256((root/'freeze_manifest.json').read_bytes()).hexdigest(),'raw_primary_sources_included':False,'sibling_directory_dependency':False,'network_access':False,'heavy_run':False,'device_validation':'not_run','meaning':'byte integrity plus tiny deterministic checks; not production calibration or authenticated signature'}
 if recompute:
  with tempfile.TemporaryDirectory(prefix='t06-reader-') as td:
   dst=Path(td)
   for name in names:
    p=dst/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/name,p)
   env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(dst/'models')}
   for label,cmd in [('unit_tests',[sys.executable,'-m','unittest','discover','-s','tests','-v']),('data_qa',[sys.executable,'models/data_qa.py']),('default_batch_plan',[sys.executable,'models/batch_driver.py'])]:
    p=subprocess.run(cmd,cwd=dst,env=env,capture_output=True,text=True,timeout=120)
    if p.returncode:raise ValueError(label+' failed\n'+p.stdout+p.stderr)
    report[label]='passed'
    if label=='unit_tests':report['test_summary']=p.stderr.strip().splitlines()[-3:]
    if label=='default_batch_plan' and json.loads(p.stdout)['status']!='plan_only':raise ValueError('default unexpectedly executed batch')
   code="""import json,numpy as np
from diagnostics import run
from pathlib import Path
fresh=run();saved=json.loads(Path('verification/diagnostics.json').read_text())
def cmp(a,b):
 if isinstance(a,dict):
  assert set(a)==set(b)
  for k in a:cmp(a[k],b[k])
 elif isinstance(a,list):
  assert len(a)==len(b)
  for x,y in zip(a,b):cmp(x,y)
 elif isinstance(a,(float,int)) and not isinstance(a,bool):assert np.isclose(a,b,rtol=2e-6,atol=1e-12),(a,b)
 else:assert a==b,(a,b)
cmp(fresh,saved)
print('isolated tiny diagnostics reproduced')
"""
   p=subprocess.run([sys.executable,'-c',code],cwd=dst,env=env,capture_output=True,text=True,timeout=120)
   if p.returncode:raise ValueError('isolated diagnostics failed\n'+p.stdout+p.stderr)
   report['isolated_diagnostics']='passed'
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--hash-only',action='store_true');a=p.parse_args();print(json.dumps(verify(a.directory,not a.hash_only),ensure_ascii=False,indent=2))
