"""Exact-allowlist reader integrity QA. --check does not write or run integrals."""
from pathlib import Path
import argparse,json,hashlib,sys
ROOT=Path(__file__).resolve().parents[1]
ALLOW=ROOT/'verification/public_allowlist.txt';MANIFEST=ROOT/'verification/reader_manifest.json'

def files():
    out=[x.strip() for x in ALLOW.read_text().splitlines() if x.strip() and not x.startswith('#')]
    if len(out)!=len(set(out)):raise ValueError('duplicate allowlist entry')
    for x in out:
        p=Path(x)
        if p.is_absolute() or '..' in p.parts or '\\' in x or not (ROOT/p).is_file() or (ROOT/p).is_symlink():raise ValueError('invalid/missing allowlist path: '+x)
        if p.suffix in ['.zip','.pyc'] or any(y in p.parts for y in ['__pycache__','archives','cache']):raise ValueError('forbidden artifact')
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');p.add_argument('--check',action='store_true');p.add_argument('--reader',action='store_true');a=p.parse_args();ff=files()
    expected={x:hashlib.sha256((ROOT/x).read_bytes()).hexdigest() for x in ff if x!='verification/reader_manifest.json'}
    if a.build:
        if a.check:raise ValueError('build and check are distinct')
        MANIFEST.write_text(json.dumps({'schema':'exact-allowlist-sha256-v1','file_count_including_manifest':len(ff),'files':expected,'self_hash_omitted':True,'author_authenticity_signature':False},indent=2)+'\n')
        print(json.dumps({'built':len(expected),'manifest_self_omitted':True}));return
    received=json.loads(MANIFEST.read_text());assert received['files']==expected,'manifest mismatch'
    assert received['file_count_including_manifest']==len(ff)
    # No original/parent/ZIP inputs are accessed here.
    print(json.dumps({'status':'pass','allowlisted_files':len(ff),'hashed_files':len(expected),'parent_or_originals_required':False,'zip_required':False,'mode':'read_only'}))
if __name__=='__main__':main()
