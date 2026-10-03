"""Freeze exact local payload and independently unpack/check. No publication."""
from pathlib import Path
import json,hashlib,zipfile,tempfile,subprocess,sys,os,platform
from reader import eligible,sha,verify
ROOT=Path(__file__).resolve().parents[1]
def js(rel,x):(ROOT/rel).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def run(args,cwd):
 env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'};r=subprocess.run([sys.executable,*args],cwd=cwd,env=env,text=True,capture_output=True,timeout=60)
 if r.returncode:raise RuntimeError(r.stderr or r.stdout)
 return r.stdout
files=[]
for p in sorted(ROOT.rglob('*')):
 if p.is_file()and eligible(str(p.relative_to(ROOT))):
  if p.is_symlink():raise ValueError('symlink_not_allowed')
  files.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)})
manifest={'version':'T09R3-0.1.0','scope':'original_reports_reference_code_figures_synthetic_data_and_hash_copied_dependencies','exclusions':sorted(__import__('reader').CONTROL)+['deliverables/','__pycache__/','*.pyc'],'files':files}
js('verification/reader_manifest.json',manifest);local=verify(ROOT);js('verification/reader_check.json',local)
archive=ROOT/'deliverables/T09_round3_unresolved_evidence_acceptance_v0.1.0_reader.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED)as z:
 for row in files:z.write(ROOT/row['path'],row['path'])
 z.write(ROOT/'verification/reader_manifest.json','verification/reader_manifest.json')
with tempfile.TemporaryDirectory(prefix='t09r3-isolated-')as t:
 d=Path(t)
 with zipfile.ZipFile(archive)as z:
  for name in z.namelist():
   if Path(name).is_absolute()or'..'in Path(name).parts:raise ValueError('unsafe_zip')
  z.extractall(d)
 output=run(['models/reader.py'],d);isolated=json.loads(output)
 plan=json.loads(run(['models/driver.py'],d))
 if plan['executed']is not False or plan['mode']!='plan_only':raise ValueError('driver_default_executed')
 chain=run(['-c',"import sys,json;sys.path.insert(0,'models');import acceptance as a;n=a.verify_dependencies();c,k=a.cs.load();print(json.dumps({'copied_dependencies':n,'fixed_channels':k['supported_channels'],'point12':k['point12'],'point2':k['point2']}))"],d)
 negatives=[]
 def reject(label):
  r=subprocess.run([sys.executable,'models/reader.py'],cwd=d,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=60)
  if r.returncode==0:raise ValueError('negative_test_not_rejected:'+label)
  negatives.append({'case':label,'rejected':True,'last_error':r.stderr.strip().splitlines()[-1]})
 q=d/'README.md';orig=q.read_bytes();q.write_bytes(orig+b'\nchanged');reject('altered_payload');q.write_bytes(orig)
 q=d/'unlisted_extra.txt';q.write_text('extra');reject('extra_file');q.unlink()
 q=d/'dependencies/t08r3/data/candidate_contract.json';orig=q.read_bytes();q.unlink();reject('missing_copied_dependency');q.write_bytes(orig)
 q=d/'verification/reader_manifest.json';orig=q.read_bytes();m=json.loads(orig);m['files'].append(m['files'][0]);q.write_text(json.dumps(m));reject('duplicate_manifest_path');q.write_bytes(orig)
 final=json.loads(run(['models/reader.py'],d))
 js('verification/isolated_reader_check.json',{'result':'passed','independent_subprocess':True,'extracted_payload':isolated,'default_plan_only':plan['executed']is False,'dependency_chain_load':json.loads(chain),'post_negative_restore':final,'numeric_replay_performed':False,'network_used':False,'sibling_roots_available_to_payload':False})
 js('verification/integrity_negative_checks.json',{'result':'passed','checks':negatives,'independent_temp_copy':True})
receipt={'stage':'T09R3','status':'local_freeze','archive':str(archive.relative_to(ROOT)),'archive_bytes':archive.stat().st_size,'archive_sha256':sha(archive),'manifest':'verification/reader_manifest.json','manifest_sha256':sha(ROOT/'verification/reader_manifest.json'),'payload_files':len(files),'payload_bytes':sum(x['bytes']for x in files),'copied_dependencies':local['copied_dependencies'],'isolated_check_sha256':sha(ROOT/'verification/isolated_reader_check.json'),'negative_check_sha256':sha(ROOT/'verification/integrity_negative_checks.json'),'outside_scope_check_sha256':sha(ROOT/'verification/outside_scope_check.json'),'formal_stage_acceptance':'pending','physical_certification':False,'production_qualified':False,'publication':'not_run','next_stage_started':False,'control_files_not_self_hashed':'reader_manifest and verification receipts intentionally excluded; receipt binds the manifest and archive; not a signature'}
js('verification/freeze_receipt.json',receipt)
final={'result':'passed','live_payload':verify(ROOT),'receipt_sha256':sha(ROOT/'verification/freeze_receipt.json'),'archive_sha256_matches':sha(archive)==receipt['archive_sha256'],'manifest_sha256_matches':sha(ROOT/'verification/reader_manifest.json')==receipt['manifest_sha256'],'state':'local_freeze','publication':'not_run'}
js('verification/final_receipt_check.json',final);print(json.dumps(receipt,indent=2))
