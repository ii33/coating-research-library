"""Freeze only this local package. Does not upload or modify sibling stages."""
from pathlib import Path
import json,hashlib,zipfile,sys,tempfile,subprocess,os
from reader import eligible,verify,sha
ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT.parents[1]
NAME='T06_round3_bounded_stack_response_v0.1.0_reader.zip'
def write(name,value):(ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def scope_check():
    before=json.loads((ROOT/'verification/outside_before.json').read_text())
    after={str(p.relative_to(PROJECT)):sha(p) for p in PROJECT.rglob('*') if p.is_file() and ROOT not in p.parents and '__pycache__' not in p.parts}
    changed=[k for k in before.keys()&after.keys() if before[k]!=after[k]]
    return {'result':'passed' if before==after else 'changes_detected','baseline_files':len(before),'after_files':len(after),'changed':sorted(changed),'added':sorted(after.keys()-before.keys()),'removed':sorted(before.keys()-after.keys()),'root_plan_and_products_modified_by_this_stage':False}
def main():
    scope=scope_check();write('verification/outside_scope_check.json',scope)
    if scope['result']!='passed':raise ValueError('outside_scope_change_requires_review')
    files=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(ROOT.rglob('*')) if p.is_file() and eligible(str(p.relative_to(ROOT)))]
    write('verification/reader_manifest.json',{'stage':'T06-round3','version':'0.1.0','identity_scope':'exact_local_payload_not_physical_certification','manifest_excludes_itself':True,'files':files})
    report=verify(ROOT);write('verification/reader_check.json',report)
    out=ROOT/'deliverables'/NAME
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for rel in [r['path'] for r in files]+['verification/reader_manifest.json']:
            info=zipfile.ZipInfo(rel,date_time=(2026,10,2,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16;z.writestr(info,(ROOT/rel).read_bytes())
    expected={r['path'] for r in files}|{'verification/reader_manifest.json'}
    with zipfile.ZipFile(out) as z:
        if set(z.namelist())!=expected or len(z.namelist())!=len(expected):raise ValueError('zip_members_do_not_match_manifest')
        if z.testzip() is not None:raise ValueError('zip_crc_error')
        with tempfile.TemporaryDirectory(prefix='t06-r3-isolated-') as td:
            root=Path(td)/'reader';z.extractall(root)
            isolated=verify(root)
            env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(root/'models')}
            tests=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=root,env=env,text=True,capture_output=True)
            if tests.returncode:raise ValueError('isolated_small_tests_failed:'+tests.stderr)
            # Import and hash-check the copied full chain on an unknown-source path.
            bridge_cmd="import sys;sys.path.insert(0,'dependencies/t05/models');import source_retention as s; b=s.bridge_t04(s.t04.Scene(),s.t04.Response(source_scale_kg_s=None),None,n=None); assert b['status']=='unknown_source_angular_law';print(b['status'])"
            bridge=subprocess.run([sys.executable,'-c',bridge_cmd],cwd=root,env=env,text=True,capture_output=True)
            if bridge.returncode:raise ValueError('isolated_upstream_import_failed:'+bridge.stderr)
            write('verification/isolated_reader_check.json',{'reader':isolated,'archive_exact_members':True,'small_tests_returncode':tests.returncode,'small_test_output':tests.stderr,'copied_full_chain_import_and_unknown_gate':bridge.stdout.strip(),'layout':'unverified','detached_from_sibling_directories':True})
            negatives={}
            cases=[('payload_tamper','models/exact_intervals.py','tamper'),('dependency_missing','dependencies/t05/models/source_retention.py','missing'),('unlisted_file','unexpected.json','extra')]
            for label,rel,kind in cases:
                p=root/rel;old=p.read_bytes() if p.exists() else None
                if kind=='tamper':p.write_bytes(old+b'\n# test corruption\n')
                elif kind=='missing':p.unlink()
                else:p.write_text('{}')
                try:verify(root);negatives[label]={'rejected':False}
                except ValueError as e:negatives[label]={'rejected':True,'reason':str(e)}
                if old is not None:p.write_bytes(old)
                else:p.unlink()
            if not all(v['rejected'] for v in negatives.values()):raise ValueError('negative_guard_failed')
            write('verification/integrity_negative_checks.json',negatives)
    receipt={'stage':'T06-round3','version':'0.1.0','status':'local_freeze','manifest_path':'verification/reader_manifest.json','manifest_sha256':sha(ROOT/'verification/reader_manifest.json'),'payload_files':len(files),'payload_bytes':sum(x['bytes'] for x in files),'archive':{'path':'deliverables/'+NAME,'bytes':out.stat().st_size,'sha256':sha(out),'members':len(expected)},'evidence_sha256':{x:sha(ROOT/x) for x in ['verification/outside_scope_check.json','verification/unit_tests.txt','verification/isolated_reader_check.json','verification/integrity_negative_checks.json','verification/visual_qa.json','reviews/narrow_optical_check.md']},'receipt_excludes_itself':True,'html_layout':'unverified_existing_restriction','point12':'partial_unchanged','point2':'conditional_non_strict_unchanged','formal_review':'pending','heavy_validation':'plan_only_not_run','uploads':0,'pushes':0,'next_stage_started':False}
    write('verification/freeze_receipt.json',receipt);print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
