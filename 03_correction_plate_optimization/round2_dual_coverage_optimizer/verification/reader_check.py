"""Exact allowlist integrity and isolated reader checks. No publication or ZIP."""
from pathlib import Path
import argparse,json,hashlib,tempfile,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
MANIFEST='verification/reader_manifest.json'


def allowed():
    lines=[s.strip() for s in (ROOT/'verification/public_allowlist.txt').read_text().splitlines() if s.strip() and not s.startswith('#')]
    if len(lines)!=len(set(lines)): raise ValueError('duplicate allowlist path')
    for s in lines:
        p=Path(s)
        if p.is_absolute() or '..' in p.parts or p.as_posix()!=s or p.is_symlink() or not (ROOT/p).is_file() or (ROOT/p).is_symlink(): raise ValueError('invalid allowlist entry '+s)
        if any(x in p.parts for x in ('__pycache__','cache','checkpoints','device_results','originals','local_originals')) or p.suffix in ('.pyc','.zip'): raise ValueError('excluded data in publication allowlist')
    return lines


def build():
    paths=allowed();entries={p:{'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),'bytes':(ROOT/p).stat().st_size} for p in paths if p!=MANIFEST}
    (ROOT/MANIFEST).write_text(json.dumps({'schema':'T03-exact-reader-manifest-v1','entries':entries,'self_exclusion':MANIFEST,'integrity_not_identity_signature':True},indent=2,sort_keys=True)+'\n')


def check():
    paths=allowed();m=json.loads((ROOT/MANIFEST).read_text());expected=set(paths)-{MANIFEST}
    if set(m['entries'])!=expected: raise ValueError('manifest/allowlist mismatch')
    for p,v in m['entries'].items():
        b=(ROOT/p).read_bytes()
        if len(b)!=v['bytes'] or hashlib.sha256(b).hexdigest()!=v['sha256']: raise ValueError('integrity failure '+p)
    return {'status':'pass','allowlist_files':len(paths),'hashed_files':len(expected),'bytes':sum(v['bytes'] for v in m['entries'].values())}


def reader():
    with tempfile.TemporaryDirectory(prefix='t03-isolated-reader-') as tmp:
        dest=Path(tmp)
        for p in allowed():
            target=dest/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/p,target)
        commands=[['-m','unittest','discover','-s','verification','-p','test_small.py','-v'],['-m','unittest','discover','-s','reviews','-p','test_optimizer_counterexamples.py','-v'],['models/run_optimizer.py'],['models/device_runner.py']]
        records=[]
        for args in commands:
            r=subprocess.run([sys.executable,'-B',*args],cwd=dest,capture_output=True,text=True,timeout=30)
            records.append({'command':['python','-B',*args],'returncode':r.returncode,'tail':(r.stdout+r.stderr)[-300:]})
            if r.returncode: raise RuntimeError(json.dumps(records,indent=2))
        return {'status':'pass','copied_exact_allowlist_only':True,'parent_repository_required':False,'commands':records}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--build',action='store_true');ap.add_argument('--check',action='store_true');ap.add_argument('--reader',action='store_true');a=ap.parse_args()
    if a.build: build()
    result={}
    if a.check: result['integrity']=check()
    if a.reader: result['isolated_reader']=reader()
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
