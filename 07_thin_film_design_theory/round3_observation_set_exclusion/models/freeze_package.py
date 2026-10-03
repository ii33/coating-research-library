"""Local freeze with exact archive boundary and detached smoke reproduction."""
from pathlib import Path
import sys,json,zipfile,tempfile,subprocess,os
from reader import sha,eligible,verify
ROOT=Path(__file__).resolve().parents[1];PROJECT=ROOT.parents[1]
NAME='T07_round3_observation_set_exclusion_v0.1.0_reader.zip'
def write(name,v):(ROOT/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def scope_check():
 before=json.loads((ROOT/'verification/outside_before.json').read_text());after={str(p.relative_to(PROJECT)):sha(p) for p in PROJECT.rglob('*') if p.is_file() and ROOT not in p.parents and '__pycache__' not in p.parts}
 return {'result':'passed' if before==after else 'changes_detected','before_files':len(before),'after_files':len(after),'changed':sorted(k for k in before.keys()&after.keys() if before[k]!=after[k]),'added':sorted(after.keys()-before.keys()),'removed':sorted(before.keys()-after.keys()),'root_plans_old_freezes_products_modified':False}
def main():
 scope=scope_check();write('verification/outside_scope_check.json',scope)
 if scope['result']!='passed':raise ValueError('outside_scope_change_requires_review')
 files=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(ROOT.rglob('*')) if p.is_file() and eligible(str(p.relative_to(ROOT)))]
 write('verification/reader_manifest.json',{'stage':'T07-round3','version':'0.1.0','identity_scope':'exact_payload_not_physical_certificate','manifest_excludes_itself':True,'exclusions':sorted(__import__('reader').CONTROL)+['deliverables/**','sources/originals/**','**/__pycache__/**','**/*.pyc'],'files':files})
 report=verify(ROOT);write('verification/reader_check.json',report);out=ROOT/'deliverables'/NAME
 expected={x['path'] for x in files}|{'verification/reader_manifest.json'}
 with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for rel in sorted(expected):
   info=zipfile.ZipInfo(rel,date_time=(2026,10,2,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16;z.writestr(info,(ROOT/rel).read_bytes())
 with zipfile.ZipFile(out) as z:
  if set(z.namelist())!=expected or len(z.namelist())!=len(expected) or z.testzip() is not None:raise ValueError('archive_members_or_crc_failed')
  if any(x.startswith('sources/originals/') or x.endswith('.pdf') for x in z.namelist()):raise ValueError('original_paper_or_pdf_in_payload')
  with tempfile.TemporaryDirectory(prefix='t07-r3-isolated-') as td:
   root=Path(td)/'reader';z.extractall(root);isolated=verify(root);env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(root/'models')}
   test=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=root,env=env,text=True,capture_output=True)
   if test.returncode:raise ValueError('isolated_test_failed:'+test.stderr)
   cmd="import sys;sys.path.insert(0,'dependencies/t06r3/dependencies/t05/models');import source_retention as s;b=s.bridge_t04(s.t04.Scene(),s.t04.Response(source_scale_kg_s=None),None,n=None);assert b['status']=='unknown_source_angular_law';print(b['status'])"
   chain=subprocess.run([sys.executable,'-c',cmd],cwd=root,env=env,text=True,capture_output=True)
   if chain.returncode:raise ValueError('isolated_source_chain_failed:'+chain.stderr)
   write('verification/isolated_reader_check.json',{'reader':isolated,'archive_exact_members':True,'unit_tests_returncode':test.returncode,'unit_test_output':test.stderr,'recomputed':'decisive_13_node_exclusion_and_three_witnesses_in_tests','upstream_chain_import_unknown_gate':chain.stdout.strip(),'detached_from_siblings':True,'layout':'unverified'})
   negative={}
   for label,rel,action in [('payload_tamper','models/set_exclusion.py','tamper'),('dependency_missing','dependencies/t06r3/dependencies/t05/models/source_retention.py','missing'),('unlisted_payload','unexpected.json','extra')]:
    p=root/rel;old=p.read_bytes() if p.exists() else None
    if action=='tamper':p.write_bytes(old+b'\n# deliberate integrity test\n')
    elif action=='missing':p.unlink()
    else:p.write_text('{}')
    try:verify(root);negative[label]={'rejected':False}
    except ValueError as e:negative[label]={'rejected':True,'reason':str(e)}
    if old is None:p.unlink()
    else:p.write_bytes(old)
   if not all(x['rejected'] for x in negative.values()):raise ValueError('negative_integrity_failed')
   write('verification/integrity_negative_checks.json',negative)
 receipt={'stage':'T07-round3','version':'0.1.0','status':'local_freeze','manifest_path':'verification/reader_manifest.json','manifest_sha256':sha(ROOT/'verification/reader_manifest.json'),'payload_files':len(files),'payload_bytes':sum(x['bytes'] for x in files),'archive':{'path':'deliverables/'+NAME,'bytes':out.stat().st_size,'sha256':sha(out),'members':len(expected)},'evidence_sha256':{p:sha(ROOT/p) for p in ['verification/outside_scope_check.json','verification/unit_tests.txt','verification/isolated_reader_check.json','verification/integrity_negative_checks.json','verification/visual_qa.json','reviews/narrow_optical_unit_check.md','verification/content_safety_check.json']},'receipt_excludes_itself':True,'point12':'partial_unchanged','point2':'conditional_non_strict_unchanged','formal_model_chain':'pending','heavy_device':'plan_only_not_run','html_layout':'unverified_existing_restriction_not_retried','original_papers_packaged':False,'uploads':0,'pushes':0,'next_stage_started':False}
 write('verification/freeze_receipt.json',receipt)
 final={'result':'passed','manifest_count_matches':len(json.loads((ROOT/'verification/reader_manifest.json').read_text())['files'])==receipt['payload_files'],'manifest_bytes_matches':sum(x['bytes'] for x in files)==receipt['payload_bytes'],'archive_sha_matches':sha(out)==receipt['archive']['sha256'],'manifest_sha_matches':sha(ROOT/'verification/reader_manifest.json')==receipt['manifest_sha256'],'archive_exact_members':True,'evidence_hashes_match':all(sha(ROOT/p)==h for p,h in receipt['evidence_sha256'].items())}
 if not all(v for k,v in final.items() if k!='result'):raise ValueError('final_receipt_mismatch')
 write('verification/final_receipt_check.json',final);print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
