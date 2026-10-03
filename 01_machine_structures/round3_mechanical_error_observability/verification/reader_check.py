"""Read-only integrity by default; explicit build is authoring, never validation.
Only fixed allowlist paths enter the reader. No parent or external source is read.
"""
from pathlib import Path
from html.parser import HTMLParser
import argparse,hashlib,json,re,subprocess,sys,tempfile,time,zipfile
R=Path(__file__).resolve().parents[1]
MAN='verification/reader_manifest.json'
ALLOW='verification/public_allowlist.txt'
ARCHIVE='deliverables/T01_round3_mechanical_error_observability_v0.1.0_reader.zip'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def allowed(root):
    a=(root/ALLOW).read_text().splitlines();a=[x.strip() for x in a if x.strip()]
    if len(a)!=len(set(a)):raise ValueError('duplicate allowlist')
    for name in a:
        p=Path(name)
        if p.is_absolute() or '..' in p.parts or 'originals' in p.parts or '__pycache__' in p.parts or p.suffix in ('.pdf','.zip','.pyc'):
            raise ValueError('forbidden path: '+name)
        if not (root/p).is_file():raise ValueError('missing: '+name)
    return a

class HtmlAssets(HTMLParser):
    def __init__(self):super().__init__();self.remote=[];self.ids=set();self.anchors=[];self.images=0
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if 'id' in d:self.ids.add(d['id'])
        if tag in ('script','link','img','iframe'):
            u=d.get('src',d.get('href',''))
            if u.startswith(('http:','https:','//')):self.remote.append(u)
        if tag=='a' and d.get('href','').startswith('#'):self.anchors.append(d['href'][1:])
        if tag=='img':self.images+=1

def check(root,full=False,strict_tree=False):
    a=allowed(root);m=json.loads((root/MAN).read_text()); expected=set(a)-{MAN}
    if set(m['files'])!=expected:raise ValueError('manifest/allowlist mismatch')
    for p,item in m['files'].items():
        if sha(root/p)!=item['sha256'] or (root/p).stat().st_size!=item['bytes']:raise ValueError('content mismatch '+p)
    if strict_tree:
        actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
        if actual!=set(a):raise ValueError('standalone tree not exact allowlist')
    parser=HtmlAssets();parser.feed((root/'reader.html').read_text())
    if parser.remote or any(x not in parser.ids for x in parser.anchors) or parser.images!=3:
        raise ValueError('reader asset/anchor check failed')
    for name in a:
        if name.endswith('.md'):
            text=(root/name).read_text()
            for link in re.findall(r'\]\(([^)]+)\)',text):
                link=link.split('#')[0]
                if link and '://' not in link and not ((root/name).parent/link).exists():raise ValueError('broken local link '+name+':'+link)
    replay=json.loads((root/'reviews/repair_replay_results.json').read_text())
    for p,h in replay['input_sha256'].items():
        if sha(root/p)!=h:raise ValueError('final replay baseline changed '+p)
    if replay['summary']['interface_counterexamples_accepted']!=0 or replay['summary']['nuisance_false_information_reproduced']:
        raise ValueError('replay defect not closed')
    if json.loads((root/'data/formal_calibration_plan.json').read_text())['execution_mode']!='plan_only':raise ValueError('execution state mismatch')
    result={'integrity':'pass','files':len(a),'html':'structure_assets_and_anchors_pass_browser_layout_unverified','reader_has_parent_dependencies':False}
    if full:
        commands=[['-m','unittest','discover','-s','verification','-v'],['models/run_examples.py'],['models/offline_read.py','data/synthetic_observations.json','--allow-synthetic'],['models/prepare_calibration_plan.py'],['reviews/independent_checks.py']]
        runs=[]
        for args in commands:
            start=time.monotonic();p=subprocess.run([sys.executable,'-B',*args],cwd=root,text=True,capture_output=True,timeout=60)
            if p.returncode:raise ValueError('command failed '+str(args)+'\n'+p.stdout+p.stderr)
            if args[0]=='reviews/independent_checks.py':
                current=json.loads(p.stdout)
                if current['summary']['interface_counterexamples_accepted'] or current['summary']['nuisance_false_information_reproduced']:raise ValueError('current review replay fails')
            runs.append({'command':'python -B '+' '.join(args),'returncode':p.returncode,'wall_seconds':time.monotonic()-start})
        # Templates and heavy execution must fail in their declared ways.
        for args in (['models/offline_read.py','data/measurement_template.json'],['models/prepare_calibration_plan.py','--execute']):
            p=subprocess.run([sys.executable,'-B',*args],cwd=root,text=True,capture_output=True,timeout=60)
            if p.returncode!=2:raise ValueError('required rejection failed '+str(args))
        result['light_reproduction']=runs;result['negative_cli_gates']='pass'
    return result

def build():
    # Manifest must exist as a declared self-reference; its bytes are deliberately excluded.
    mp=R/MAN
    if not mp.exists():mp.write_text('{}\n')
    a=allowed(R)
    files={p:{'sha256':sha(R/p),'bytes':(R/p).stat().st_size} for p in a if p!=MAN}
    m={'package_id':'T01-r3-v0.1.0','identity':'original derived reader; prior sources are provenance only','hash_algorithm':'SHA-256','self_excluded':MAN,'files':files}
    mp.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
    check(R,False)
    out=R/ARCHIVE;out.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for p in a:
            info=zipfile.ZipInfo(p,(2026,10,2,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            z.writestr(info,(R/p).read_bytes())
    with zipfile.ZipFile(out) as z:
        if z.testzip() is not None or z.namelist()!=a:raise ValueError('zip member mismatch')
        with tempfile.TemporaryDirectory(prefix='t01_r3_reader_') as temp:
            z.extractall(temp);isolated=check(Path(temp),full=True,strict_tree=True)
    receipt={'package_id':'T01-r3-v0.1.0','archive':ARCHIVE,'archive_sha256':sha(out),'archive_bytes':out.stat().st_size,'archive_members':len(a),'manifest_sha256':sha(mp),'manifest_entry_count':len(files),'self_reference_policy':'manifest excludes itself; receipt is outside reader and excludes itself','standalone_validation':isolated,'third_party_originals_in_reader':False,'publication':'local_only_not_uploaded','scope':'exact packaging and bounded math/interface reproduction; not physical or full-model-chain acceptance'}
    (R/'verification/release_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(receipt,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--check',action='store_true');g.add_argument('--build',action='store_true');p.add_argument('--full',action='store_true');p.add_argument('--strict-tree',action='store_true');a=p.parse_args()
    if a.build:build()
    else:print(json.dumps(check(R,a.full,a.strict_tree),ensure_ascii=False,indent=2))
