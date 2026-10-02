"""Explicit public allowlist packaging and offline hash verification.
--check --reader validates extracted/GitHub reader files without requiring ZIP.
--check alone additionally validates ZIP if it exists; never writes in check mode.
"""
from pathlib import Path
import hashlib,json,zipfile,sys
ROOT=Path(__file__).resolve().parents[1]
ZIP=ROOT/'deliverables/T02_round2_dual_coverage_error_budget_v0.1_reader.zip'
LIST=ROOT/'verification/public_allowlist.txt'
MANIFEST='verification/reader_manifest.json'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    check='--check' in sys.argv;reader='--reader' in sys.argv
    if reader and not check:raise SystemExit('--reader requires --check')
    names=[x.strip() for x in LIST.read_text().splitlines() if x.strip() and not x.startswith('#')]
    assert len(names)==len(set(names))
    assert MANIFEST in names
    for n in names:
        p=Path(n)
        assert not p.is_absolute() and '..' not in p.parts
        if n!=MANIFEST or check:assert (ROOT/p).is_file(),n
        assert not any(x in n.lower() for x in ['sources/originals/','__pycache__','.pyc','credentials','secrets']),n
        assert not n.startswith('deliverables/'),n
    if not check:
        manifest={'schema':'T02R2-reader-sha256-1','allowlist_file_count':len(names),'manifest_self_exclusion':MANIFEST,'self_exclusion_reason':'A file cannot contain its own ordinary SHA-256 digest. External release_checks.json hashes this manifest and the ZIP. These are integrity hashes, not authenticity signatures.','file_sha256':{n:digest(ROOT/n) for n in names if n!=MANIFEST}}
        (ROOT/MANIFEST).write_text(json.dumps(manifest,indent=2)+'\n')
        ZIP.parent.mkdir(exist_ok=True)
        with zipfile.ZipFile(ZIP,'w',zipfile.ZIP_DEFLATED) as z:
            for n in names:z.write(ROOT/n,n)
    manifest=json.loads((ROOT/MANIFEST).read_text())
    assert manifest['allowlist_file_count']==len(names)
    assert manifest['manifest_self_exclusion']==MANIFEST
    assert set(manifest['file_sha256'])==set(names)-{MANIFEST}
    for n,h in manifest['file_sha256'].items():assert digest(ROOT/n)==h,n
    mode='reader_files_only'
    if ZIP.exists() and not reader:
        with zipfile.ZipFile(ZIP) as z:
            assert sorted(z.namelist())==sorted(names)
            for n in names:assert z.read(n)==(ROOT/n).read_bytes(),n
        mode='reader_files_and_zip'
    payload={'status':'pass','mode':mode,'explicit_file_count':len(names),'reader_hashed_file_count':len(manifest['file_sha256']),'no_third_party_originals':True}
    if mode=='reader_files_and_zip':payload.update(archive_bytes=ZIP.stat().st_size,archive_sha256=digest(ZIP))
    if not check:
        payload['file_sha256']={n:digest(ROOT/n) for n in names}
        (ROOT/'verification/release_checks.json').write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps({k:v for k,v in payload.items() if k!='file_sha256'},indent=2))
if __name__=='__main__':main()
