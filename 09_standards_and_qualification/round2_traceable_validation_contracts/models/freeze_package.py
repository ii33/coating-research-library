"""Exact local manifest and outside-tree preservation receipt. No network writes."""
from pathlib import Path
import argparse,datetime,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
LIBRARY=ROOT.parents[1]
EXCLUDE={'freeze_manifest.json','reviews/freeze_receipt.json','reviews/freeze_verify.json'}
LOCAL_ONLY={'data/preexisting_baseline.json','reviews/outside_changes.json','data/read_provenance.json','reviews/reader_desktop.png','reviews/reader_mobile.png'}
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def record(p):return {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p)}
def files():return [p for p in sorted(ROOT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and p.relative_to(ROOT).as_posix() not in EXCLUDE]
def outside_changes():
    baseline=json.loads((ROOT/'data/preexisting_baseline.json').read_text())
    before={r['path']:r for r in baseline['files']}; changed=[];missing=[];added=[]
    for name,r in before.items():
        p=LIBRARY/name
        if not p.exists():missing.append(r)
        elif digest(p)!=r['sha256']:
            changed.append({'path':name,'before_sha256':r['sha256'],'after_sha256':digest(p),'attribution':'outside_this_task; requires coordinator attribution'})
    for p in sorted(LIBRARY.rglob('*')):
        if p.is_file() and ROOT not in p.parents and '.git' not in p.parts:
            name=p.relative_to(LIBRARY).as_posix()
            if name not in before:added.append({'path':name,'bytes':p.stat().st_size,'sha256':digest(p),'attribution':'parallel_addition_not_this_task'})
    return {'baseline_files':len(before),'changed':changed,'missing':missing,'parallel_additions':added,'all_preexisting_bytes_unchanged':not changed and not missing}
def verify():
    m=json.loads((ROOT/'freeze_manifest.json').read_text()); expected={r['path']:r for r in m['files']}; actual={r['path']:r for r in map(record,files())}
    missing=sorted(set(expected)-set(actual));extra=sorted(set(actual)-set(expected));changed=[p for p in expected.keys()&actual.keys() if expected[p]!=actual[p]]
    receipt=json.loads((ROOT/'reviews/freeze_receipt.json').read_text())
    receipt_matches=receipt['manifest_sha256']==digest(ROOT/'freeze_manifest.json')
    result={'verified_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exact_manifest_ok':not(missing or extra or changed),'receipt_manifest_hash_matches':receipt_matches,'missing':missing,'extra':extra,'changed':sorted(changed),'payload_count':len(actual),'note':'Read-only verification; receipt and verification output excluded to avoid recursion. Does not prove source truth or signatures.'}
    print(json.dumps(result,ensure_ascii=False,indent=2));return result
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    if args.verify:
        r=verify();raise SystemExit(0 if r['exact_manifest_ok'] and r['receipt_manifest_hash_matches'] else 1)
    if not args.freeze:parser.error('choose --freeze or --verify')
    if (ROOT/'freeze_manifest.json').exists():raise SystemExit('Refusing to overwrite existing freeze; frozen package must be immutable')
    outside=outside_changes();(ROOT/'reviews/outside_changes.json').write_text(json.dumps(outside,ensure_ascii=False,indent=2)+'\n')
    # Exact reader allowlist is project-original content. Local integrity records excluded.
    allow=[p.relative_to(ROOT).as_posix() for p in files() if p.relative_to(ROOT).as_posix() not in LOCAL_ONLY and p.name not in {'reader_allowlist.json','reader_manifest.json'}]
    allow.extend(['data/reader_allowlist.json','reader_manifest.json']);allow=sorted(allow)
    (ROOT/'data/reader_allowlist.json').write_text(json.dumps({'paths':allow,'no_third_party_originals':True,'publication_authorized':False,'local_only_exclusions':sorted(LOCAL_ONLY|EXCLUDE)},ensure_ascii=False,indent=2)+'\n')
    reader_manifest={'package':'T09R2-1.0-reader','files':[record(p) for p in files() if p.relative_to(ROOT).as_posix() in allow and p.name!='reader_manifest.json'],'self_excluded':'reader_manifest.json','third_party_originals':False,'publication_authorized':False}
    (ROOT/'reader_manifest.json').write_text(json.dumps(reader_manifest,ensure_ascii=False,indent=2)+'\n')
    manifest={'package':'T09R2-1.0','frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':[record(p) for p in files()],'excluded_self_referential':sorted(EXCLUDE),'ignored_runtime_cache':['__pycache__','*.pyc'],'reader_allowlist_path':'data/reader_allowlist.json','third_party_originals_included':False,'publication_authorized':False}
    (ROOT/'freeze_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    receipt={'package':'T09R2-1.0','status':'local_frozen_research_contract_ready_real_validation_pending','manifest_sha256':digest(ROOT/'freeze_manifest.json'),'file_count':len(manifest['files']),'reader_allowlist_count':len(allow),'preexisting_integrity':outside,'all_hardware_tests':'not_run','T08_heavy_batch':'not_run_awaiting_device','full_designated_review_chain':'pending_not_run','independent_review':'one_narrow_check; author_corrections_afterwards; no_second_review','uploads_push_deploy_external_sharing':False,'user_computer_edits':False,'stopping_condition':'local_freeze_reached'}
    (ROOT/'reviews/freeze_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'files':len(manifest['files']),'reader':len(allow),'manifest_sha256':receipt['manifest_sha256'],'outside_summary':{k:len(v) if isinstance(v,list) else v for k,v in outside.items()}},ensure_ascii=False,indent=2))
