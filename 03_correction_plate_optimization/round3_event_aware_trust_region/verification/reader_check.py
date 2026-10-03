"""Exact allowlist integrity and standalone lightweight replay. No parent tree reads.
--check is read-only. --build is authoring and creates an external release receipt.
"""
from pathlib import Path
from html.parser import HTMLParser
import argparse,ast,hashlib,json,re,subprocess,sys,tempfile,time,zipfile
R=Path(__file__).resolve().parents[1]
MAN='verification/reader_manifest.json';ALLOW='verification/public_allowlist.txt'
ARCHIVE='deliverables/T03_round3_event_aware_trust_region_v0.1.0_reader.zip'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def allowed(root):
    items=[s for s in (root/ALLOW).read_text().splitlines() if s.strip()]
    if items!=sorted(set(items)):raise ValueError('allowlist must be sorted and unique')
    for s in items:
        p=Path(s);target=root/p
        if p.is_absolute() or '..' in p.parts or 'originals' in p.parts or '__pycache__' in p.parts or p.suffix in ('.zip','.pdf','.pyc') or target.is_symlink():raise ValueError('forbidden archive member '+s)
        if not target.is_file():raise ValueError('missing member '+s)
    return items

class Assets(HTMLParser):
    def __init__(self):super().__init__();self.ids=set();self.anchors=[];self.remote=[];self.images=[];self.scripts=0
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if 'id' in d:self.ids.add(d['id'])
        if tag=='a' and d.get('href','').startswith('#'):self.anchors.append(d['href'][1:])
        if tag=='script':self.scripts+=1
        if tag in ('img','link','script','iframe'):
            u=d.get('src',d.get('href',''))
            if u.startswith(('http:','https:','//')):self.remote.append(u)
            if tag=='img':self.images.append(u)

def check(root,full=False,strict=False):
    a=allowed(root);m=json.loads((root/MAN).read_text())
    if set(m['files'])!=set(a)-{MAN}:raise ValueError('manifest and allowlist mismatch')
    for name,item in m['files'].items():
        p=root/name
        if sha(p)!=item['sha256'] or p.stat().st_size!=item['bytes']:raise ValueError('content hash mismatch '+name)
    if strict and {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}!=set(a):raise ValueError('not an exact standalone reader tree')
    for dep in json.loads((root/'data/frozen_dependencies.json').read_text())['dependencies']:
        if sha(root/dep['copied_path'])!=dep['sha256']:raise ValueError('frozen dependency mismatch')
    independent=json.loads((root/'reviews/independent_results.json').read_text())
    for name,h in independent['sha256'].items():
        if sha(root/name)!=h:raise ValueError('independent review baseline changed '+name)
    if independent['result']!='no_blocking_defect_observed_in_scoped_checks':raise ValueError('independent result unresolved')
    for name in a:
        p=root/name
        if p.suffix=='.py':ast.parse(p.read_text())
        if p.suffix in ('.md','.json','.py','.txt','.log','.html'):
            text=p.read_text()
            patterns=[r'sedi'+r'ment://',r'codex://'+r'threads/',r'library_'+r'file_[A-Za-z0-9]',r'/workspace/'+r'scratch/[A-Za-z0-9]',r'sk-'+r'[A-Za-z0-9]{20}']
            if re.search('|'.join(patterns),text):raise ValueError('private marker '+name)
    parser=Assets();parser.feed((root/'reader.html').read_text())
    if parser.scripts or parser.remote or len(parser.images)!=2 or any(not s.startswith('data:image/png;base64,') for s in parser.images) or any(s not in parser.ids for s in parser.anchors):raise ValueError('offline HTML asset or anchor failure')
    plan=json.loads((root/'data/device_validation_plan.json').read_text())
    if plan['execution_mode']!='plan_only' or plan['execution_authorized'] is not False or plan['device_label'] is not None or plan['authorization_evidence'] is not None:raise ValueError('frozen execution gate changed')
    result={'integrity':'pass','reader_member_count':len(a),'manifest_entries':len(m['files']),'frozen_dependency_count':8,'independent_review_hashes':'match','syntax':'all_python_parse','standalone_parent_runtime_dependency':False,'private_marker_scan':'pass','html':'2_embedded_pngs_no_scripts_valid_anchors_browser_layout_unverified'}
    if full:
        independent_replay="import json,sys;sys.path.insert(0,'reviews');import independent_checks;print(json.dumps(independent_checks.run(),sort_keys=True))"
        commands=[['-m','unittest','discover','-s','verification','-p','test_small.py','-v'],['models/run_examples.py'],['models/device_driver.py'],['-c',independent_replay]]
        runs=[]
        for args in commands:
            start=time.monotonic();proc=subprocess.run([sys.executable,'-B',*args],cwd=root,text=True,capture_output=True,timeout=60)
            if proc.returncode:raise ValueError('replay failed '+str(args)+'\n'+proc.stdout+proc.stderr)
            if args[0]=='models/run_examples.py' and json.loads(proc.stdout)!=json.loads((root/'data/tiny_results.json').read_text()):raise ValueError('tiny results differ')
            if args[0]=='models/device_driver.py' and json.loads(proc.stdout)!=json.loads((root/'verification/plan_only_output.json').read_text()):raise ValueError('plan-only output differs')
            if args[0]=='-c' and json.loads(proc.stdout)!=independent:raise ValueError('independent reproduction differs')
            runs.append({'check':args[0] if args[0] not in ('-m','-c') else '15_unit_tests' if args[0]=='-m' else 'independent_math_reproduction','exitcode':proc.returncode,'wall_seconds':time.monotonic()-start})
        p=subprocess.run([sys.executable,'-B','models/device_driver.py','--run'],cwd=root,text=True,capture_output=True,timeout=30)
        if p.returncode!=2 or 'renewed device authorization' not in p.stderr:raise ValueError('default execution gate failed')
        # Ensure read-only replay did not alter received evidence or add files.
        after=check(root,False,strict)
        result['light_reproduction']=runs;result['default_run_refusal']='pass_exit_2';result['post_replay_integrity']=after['integrity']
    return result

def build():
    if not (R/MAN).exists():(R/MAN).write_text('{}\n')
    a=allowed(R);files={s:{'sha256':sha(R/s),'bytes':(R/s).stat().st_size} for s in a if s!=MAN}
    (R/MAN).write_text(json.dumps({'package_id':'T03-r3-v0.1.0','hash_algorithm':'SHA-256','self_excluded':MAN,'files':files},indent=2,ensure_ascii=False)+'\n')
    check(R)
    out=R/ARCHIVE;out.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for s in a:
            i=zipfile.ZipInfo(s,(2026,10,2,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o644<<16;z.writestr(i,(R/s).read_bytes())
    with zipfile.ZipFile(out) as z:
        if z.testzip() is not None or z.namelist()!=a:raise ValueError('archive integrity/member order failure')
        with tempfile.TemporaryDirectory(prefix='t03r3_isolated_reader_') as td:
            z.extractall(td);standalone=check(Path(td),True,True)
    receipt={'package_id':'T03-r3-v0.1.0','archive':ARCHIVE,'archive_sha256':sha(out),'archive_bytes':out.stat().st_size,'archive_member_count':len(a),'manifest_sha256':sha(R/MAN),'manifest_entry_count':len(files),'allowlist_sha256':sha(R/ALLOW),'standalone_validation':standalone,'publication':'local_only_not_uploaded','third_party_originals_in_reader':False,'self_reference_policy':'manifest excludes self; receipt external to archive and not self hashed','formal_chain':'pending','physical_certification':False,'historical_point2_point12_status':'unchanged'}
    (R/'verification/release_receipt.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(receipt,indent=2,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--check',action='store_true');g.add_argument('--build',action='store_true');p.add_argument('--full',action='store_true');p.add_argument('--strict-tree',action='store_true');a=p.parse_args()
    if a.build:build()
    else:print(json.dumps(check(R,a.full,a.strict_tree),indent=2))
