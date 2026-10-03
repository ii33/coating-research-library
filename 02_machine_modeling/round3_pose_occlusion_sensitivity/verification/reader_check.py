"""Fixed-allowlist standalone integrity and light reproduction. No parent reads.
Explicit --build is authoring; --check does not mutate received evidence.
"""
from pathlib import Path
from html.parser import HTMLParser
import argparse,hashlib,json,re,subprocess,sys,tempfile,time,zipfile
R=Path(__file__).resolve().parents[1]
MAN='verification/reader_manifest.json';ALLOW='verification/public_allowlist.txt'
ARCHIVE='deliverables/T02_round3_pose_occlusion_sensitivity_v0.1.0_reader.zip'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def allowed(root):
    a=[x.strip() for x in (root/ALLOW).read_text().splitlines() if x.strip()]
    if len(a)!=len(set(a)):raise ValueError('duplicate allowlist')
    for x in a:
        p=Path(x);target=root/p
        if p.is_absolute() or '..' in p.parts or 'originals' in p.parts or '__pycache__' in p.parts or p.suffix in ('.pdf','.zip','.pyc') or target.is_symlink():raise ValueError('forbidden reader member '+x)
        if not target.is_file():raise ValueError('missing '+x)
    return a

class Assets(HTMLParser):
    def __init__(self):super().__init__();self.remote=[];self.ids=set();self.anchors=[];self.images=0
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if 'id' in d:self.ids.add(d['id'])
        if tag in ('script','img','link','iframe'):
            u=d.get('src',d.get('href',''))
            if u.startswith(('http:','https:','//')):self.remote.append(u)
            if tag=='img':
                self.images+=1
                if not u.startswith('data:'):self.remote.append('nonembedded_image:'+u)
        if tag=='a' and d.get('href','').startswith('#'):self.anchors.append(d['href'][1:])

def check(root,full=False,strict_tree=False):
    a=allowed(root);m=json.loads((root/MAN).read_text())
    if set(m['files'])!=set(a)-{MAN}:raise ValueError('manifest/allowlist mismatch')
    for p,r in m['files'].items():
        if sha(root/p)!=r['sha256'] or (root/p).stat().st_size!=r['bytes']:raise ValueError('hash mismatch '+p)
    if strict_tree:
        actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
        if actual!=set(a):raise ValueError('not exact standalone tree')
    parser=Assets();parser.feed((root/'reader.html').read_text())
    if parser.remote or parser.images!=3 or any(x not in parser.ids for x in parser.anchors):raise ValueError('HTML embedded asset or anchor failure')
    for name in a:
        if name.endswith('.md'):
            for link in re.findall(r'\]\(([^)]+)\)',(root/name).read_text()):
                link=link.split('#')[0]
                if link and '://' not in link and not ((root/name).parent/link).is_file():raise ValueError('broken link '+name+':'+link)
        if Path(name).suffix in ('.md','.json','.py','.txt','.log','.html'):
            t=(root/name).read_text()
            patterns=[r'sedi'+r'ment://',r'codex://'+r'threads/',r'library_'+r'file_[A-Za-z0-9]',r'/workspace/'+r'scratch/[A-Za-z0-9]',r'sk-'+r'[A-Za-z0-9]{20}']
            if re.search('|'.join(patterns),t):raise ValueError('private marker '+name)
    for dep in json.loads((root/'data/frozen_dependencies.json').read_text())['dependencies']:
        if sha(root/dep['copied_path'])!=dep['sha256']:raise ValueError('frozen copy mismatch')
    replay=json.loads((root/'reviews/repair_replay_results.json').read_text())
    if not all(replay['checks'].values()):raise ValueError('repair replay fail')
    for p,h in replay['input_sha256'].items():
        if sha(root/p)!=h:raise ValueError('replay baseline mismatch '+p)
    if sha(root/'reviews/independent_results.json')!=replay['initial_review_evidence_sha256']:raise ValueError('initial evidence changed')
    d=json.loads((root/'data/device_validation_plan.json').read_text())
    if d['execution_mode']!='plan_only' or d['execution_authorized'] is not False or d['device_label'] is not None:raise ValueError('frozen execution gate changed')
    result={'integrity':'pass','member_count':len(a),'manifest_entries':len(m['files']),'html':'embedded_assets_and_internal_anchors_pass_browser_layout_unverified','parent_runtime_dependency':False,'private_marker_scan':'pass'}
    if full:
        commands=[['-m','unittest','discover','-s','verification','-p','test_small.py','-v'],['models/run_examples.py'],['models/offline_read.py','data/synthetic_contract.json','--allow-synthetic'],['models/device_driver.py'],['reviews/author_replay.py']]
        runs=[]
        for args in commands:
            start=time.monotonic();p=subprocess.run([sys.executable,'-B',*args],cwd=root,text=True,capture_output=True,timeout=60)
            if p.returncode:raise ValueError('light command failed '+str(args)+'\n'+p.stdout+p.stderr)
            if args[0]=='models/run_examples.py' and json.loads(p.stdout)!=json.loads((root/'data/algebraic_results.json').read_text()):raise ValueError('algebraic result differs')
            if args[0]=='reviews/author_replay.py' and not all(json.loads(p.stdout)['checks'].values()):raise ValueError('current replay differs')
            runs.append({'command':'python -B '+' '.join(args),'returncode':p.returncode,'wall_seconds':time.monotonic()-start})
        for args in (['models/offline_read.py','data/measurement_template.json'],['models/device_driver.py','--run']):
            p=subprocess.run([sys.executable,'-B',*args],cwd=root,text=True,capture_output=True,timeout=30)
            if p.returncode!=2:raise ValueError('required rejection failed')
        result['light_reproduction']=runs;result['negative_cli_gates']='pass'
    return result

def build():
    mp=R/MAN
    if not mp.exists():mp.write_text('{}\n')
    a=allowed(R);files={p:{'sha256':sha(R/p),'bytes':(R/p).stat().st_size} for p in a if p!=MAN}
    mp.write_text(json.dumps({'package_id':'T02-r3-v0.1.0','hash_algorithm':'SHA-256','self_excluded':MAN,'files':files},ensure_ascii=False,indent=2)+'\n')
    check(R)
    out=R/ARCHIVE;out.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for p in a:
            info=zipfile.ZipInfo(p,(2026,10,2,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16;z.writestr(info,(R/p).read_bytes())
    with zipfile.ZipFile(out) as z:
        if z.testzip() is not None or z.namelist()!=a:raise ValueError('archive mismatch')
        with tempfile.TemporaryDirectory(prefix='t02r3_standalone_') as td:
            z.extractall(td);standalone=check(Path(td),True,True)
    result={'package_id':'T02-r3-v0.1.0','archive':ARCHIVE,'archive_sha256':sha(out),'archive_bytes':out.stat().st_size,'archive_members':len(a),'manifest_sha256':sha(mp),'manifest_entry_count':len(files),'self_reference_policy':'manifest excludes own bytes; receipt is outside reader and excludes itself','standalone_validation':standalone,'third_party_originals_in_reader':False,'publication':'local_only_not_uploaded','acceptance':'bounded theoretical/interface freeze; no heavy/physical/formal-chain certification'}
    (R/'verification/release_receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--check',action='store_true');g.add_argument('--build',action='store_true');p.add_argument('--full',action='store_true');p.add_argument('--strict-tree',action='store_true');a=p.parse_args()
    if a.build:build()
    else:print(json.dumps(check(R,a.full,a.strict_tree),indent=2))
