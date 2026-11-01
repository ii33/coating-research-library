"""Freeze a complete pilot, then admit runs against operator-verified digests.

The commit and digests are records of the operator's external verification;
this offline worker cannot prove their association with a remote repository.
"""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import argparse
import hashlib
import json
import os
import platform
import re
import time
import numpy as np
import scipy
import scipy.linalg  # load both numerical runtimes before recording thread pools
import threadpoolctl
from artifact_store import write_immutable_json, canonical_json, _target
from core_bridge import CORE_COMMIT,configure_core
from tasks import GROUPS,FAMILIES,make_task
from reference import PROFILE,solve
ROOT=Path(__file__).resolve().parent
COMPONENT_RE=re.compile(r'[a-z0-9_]+')


def _case_set():
    # The explicit Cartesian product is the admission list, not merely a pattern.
    for name, values in (('groups', GROUPS), ('families', FAMILIES)):
        if not isinstance(values, (tuple, list)) or not values:
            raise ValueError('invalid '+name)
        if any(not isinstance(value,str) or not COMPONENT_RE.fullmatch(value) for value in values):
            raise ValueError('invalid '+name+' identifier')
        if len(values)!=len(set(values)):
            raise ValueError('duplicate '+name+' identifier')
    return {f'material-{g}-{f}' for g in GROUPS for f in FAMILIES}
HASH_RE=re.compile(r'[0-9a-f]{64}')
COMMIT_RE=re.compile(r'[0-9a-f]{40}')
DOCS=('README.md','docs/algorithms.html')


def case_id(value):
    if not isinstance(value,str) or value not in _case_set():raise ValueError('invalid case identity')
    return value


def digest(value):
    if not isinstance(value,str) or not HASH_RE.fullmatch(value):raise ValueError('invalid SHA-256 digest')
    return value


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def runtime_summary():
    # Deliberately select public technical values only: no paths, hostnames or usernames.
    pools=[]
    for pool in threadpoolctl.threadpool_info():
        pools.append({key:pool.get(key) for key in ('user_api','internal_api','num_threads','version','threading_layer','architecture')})
    pools.sort(key=lambda item:json.dumps(item,sort_keys=True))
    if not pools or any(p['user_api']=='blas' and (not p['version'] or not p['internal_api'] or not p['threading_layer'] or not isinstance(p['num_threads'],int)) for p in pools):
        raise ValueError('BLAS runtime/version/thread summary unavailable')
    if not any(p['user_api']=='blas' for p in pools):raise ValueError('BLAS runtime unavailable')
    envkeys=('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','BLIS_NUM_THREADS','NUMEXPR_NUM_THREADS')
    thread_env={k:os.environ.get(k) for k in envkeys}
    if any(v is not None and (not v.isascii() or not v.isdigit() or int(v)<1) for v in thread_env.values()):
        raise ValueError('thread settings must be positive integers or unset')
    return dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
        threadpoolctl=threadpoolctl.__version__,os=platform.system(),architecture=platform.machine(),
        blas_thread_pools=pools,thread_env=thread_env)


def _source_paths(plan):
    return sorted(set(plan['source_sha256']) | set(DOCS) | {'plan.json'} |
        {f'cases/{case_id(c)}/input.json' for c in plan['case_ids']})


def _file_entry(root,path):
    target=_target(root,path)
    data=target.read_bytes()
    return dict(path=path,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())


def _validate_plan(plan):
    expected=_case_set()
    ids=plan['case_ids']
    if not isinstance(ids,list) or ids!=sorted(expected):raise ValueError('invalid pilot case set')
    if plan['groups']!=list(GROUPS) or plan['families']!=list(FAMILIES):raise ValueError('invalid pilot grouping')
    if plan['core_commit']!=CORE_COMMIT or plan['reference_profile']!=PROFILE:raise ValueError('core or reference profile changed')
    if set(plan['case_input_sha256'])!=expected:raise ValueError('invalid case hashes')
    for c,h in plan['case_input_sha256'].items():case_id(c);digest(h)
    sources=plan['source_sha256']
    if not isinstance(sources,dict) or not sources:raise ValueError('invalid source hashes')
    for p,h in sources.items():
        if not re.fullmatch(r'[A-Za-z0-9_-]+\.py',p):raise ValueError('invalid source path')
        digest(h)


def _check_extras(root,plan,source_paths):
    allowed=set(source_paths)|{'source_manifest.json'}
    ids=set(plan['case_ids'])
    for base,dirs,files in os.walk(root,followlinks=False):
        base=Path(base)
        for name in dirs:
            if (base/name).is_symlink():raise ValueError('symlink directory in pilot')
        for name in files:
            path=base/name; rel=path.relative_to(root).as_posix()
            parts=rel.split('/')
            # Concurrent atomic publications can leave transient store temp files.
            # They are never inputs or executable sources and may vanish during walk.
            if (len(parts) in (3,4) and parts[0]=='cases' and parts[1] in ids and
                    (len(parts)==3 or parts[2]=='witnesses') and re.fullmatch(r'\.artifact-[A-Za-z0-9_-]+\.tmp',parts[-1])):
                if path.is_symlink():raise ValueError('symlink temporary artifact')
                continue
            if path.is_symlink() or not path.is_file():raise ValueError('non-regular pilot file')
            if rel in allowed:continue
            if len(parts)==2 and parts[0]=='__pycache__' and re.fullmatch(r'[A-Za-z0-9_-]+\.cpython-[0-9]+(?:\.opt-[0-9]+)?\.pyc',parts[1]):continue
            if len(parts)==2 and parts[0]=='batches' and re.fullmatch('[0-9a-f]{16}\\.json',parts[1]):continue
            if len(parts)==3 and parts[0]=='cases' and parts[1] in ids and parts[2] in ('result.json','run-admission.json'):continue
            if len(parts)==4 and parts[0]=='cases' and parts[1] in ids and parts[2]=='witnesses' and re.fullmatch('[0-9a-f]{64}\\.json',parts[3]):continue
            raise ValueError('unexpected pilot file: '+rel)


def verify_admission(root,plan_hash,manifest_hash,selected):
    # Validate all supplied identities and hashes before constructing/reading paths.
    digest(plan_hash);digest(manifest_hash)
    for c in selected:case_id(c)
    root=Path(root).resolve(strict=True)
    plan_path=_target(root,'plan.json'); manifest_path=_target(root,'source_manifest.json')
    if sha(plan_path)!=plan_hash:raise ValueError('plan SHA-256 mismatch')
    if sha(manifest_path)!=manifest_hash:raise ValueError('source manifest SHA-256 mismatch')
    plan=json.loads(plan_path.read_text());manifest=json.loads(manifest_path.read_text())
    _validate_plan(plan)
    if len(selected)!=len(set(selected)) or not set(selected)<=set(plan['case_ids']):raise ValueError('invalid case selection')
    expected=_source_paths(plan)
    if manifest.get('schema')!='immutable-pilot-source-manifest-v1' or set(manifest)!={'schema','files'}:
        raise ValueError('invalid source manifest')
    if manifest['files']!=[_file_entry(root,path) for path in expected]:raise ValueError('source manifest content mismatch')
    for p,h in plan['source_sha256'].items():
        if sha(_target(root,p))!=h:raise ValueError('source differs from plan')
    for c,h in plan['case_input_sha256'].items():
        path=_target(root,f'cases/{c}/input.json')
        if sha(path)!=h:raise ValueError('input differs from plan')
        task=json.loads(path.read_text())
        if task.get('case_id')!=c:raise ValueError('input identity differs from plan')
    _check_extras(root,plan,expected)
    if runtime_summary()!=plan['runtime']:raise ValueError('runtime or numerical thread settings differ from plan')
    return plan


def prepare():
    _case_set()  # Validate declared components before generating any input.
    tasks=[]
    for group in GROUPS:
        for family in FAMILIES:
            task=make_task(group,family)
            if not isinstance(task,dict) or task.get('case_id')!=f'material-{group}-{family}':
                raise ValueError('generated task identity differs from declared combination')
            tasks.append(task)
    case_hashes={}
    for task in tasks:
        c=case_id(task['case_id']);relative=f'cases/{c}/input.json'
        write_immutable_json(ROOT,relative,task);case_hashes[c]=sha(_target(ROOT,relative))
    sources={str(path.relative_to(ROOT)):sha(path) for path in sorted(ROOT.glob('*.py'))}
    plan=dict(schema='recoverable-reference-pilot-plan-v1',date='2026-11-01',core_commit=CORE_COMMIT,
        experiment='Follow-on diagnostic training expansion: eight explicitly simulated material groups across six common visible-band objective families',
        purpose='Extend diagnostic training data across simulated material combinations under common objectives; not a blind test or predictor validation',
        groups=list(GROUPS),families=list(FAMILIES),case_ids=sorted(case_hashes),case_input_sha256=case_hashes,
        source_sha256=sources,reference_profile=PROFILE,runtime=runtime_summary(),
        source_domain='Explicitly simulated optical material data, not measured material data; see frozen inputs for definitions and coverage',
        target_semantics='Original targets, strictness, pointwise/mean, angle and polarization retained in complete frozen inputs',
        exclusions='Not measured data, blind testing, process calibration, predictive validation, proof of minimum resources, or representation of all materials',
        reference_semantics='finite-budget audited design resource pair, not minimum; no witness means unknown',
        checkpoint_policy='Publish complete code, plan, source manifest and all inputs before first optical search; persist each audited witness immediately; publish full batch evidence and verify readback before next batch',
        online_boundary='Offline search only; no online synthesis, optimizer or audit fallback is added')
    _validate_plan(plan)
    write_immutable_json(ROOT,'plan.json',plan)
    source_paths=_source_paths(plan)
    write_immutable_json(ROOT,'source_manifest.json',dict(schema='immutable-pilot-source-manifest-v1',files=[_file_entry(ROOT,p) for p in source_paths]))
    plan_hash=sha(_target(ROOT,'plan.json'));manifest_hash=sha(_target(ROOT,'source_manifest.json'))
    verify_admission(ROOT,plan_hash,manifest_hash,plan['case_ids'])
    print('prepared',len(tasks),'complete tasks; no optical search performed')
    print('plan_sha256',plan_hash);print('source_manifest_sha256',manifest_hash)


def run_one(argument):
    c,checkpoint,plan_hash,manifest_hash=argument
    case_id(c);digest(plan_hash);digest(manifest_hash)
    if not isinstance(checkpoint,str) or not COMMIT_RE.fullmatch(checkpoint):raise ValueError('invalid checkpoint commit')
    plan=verify_admission(ROOT,plan_hash,manifest_hash,[c])
    path=_target(ROOT,f'cases/{c}/input.json')
    write_immutable_json(ROOT,f'cases/{c}/run-admission.json',dict(core_commit=CORE_COMMIT,
        verified_source_checkpoint=checkpoint,verified_plan_sha256=plan_hash,verified_source_manifest_sha256=manifest_hash,
        input_sha256=plan['case_input_sha256'][c],profile=PROFILE,runtime=plan['runtime']))
    result=solve(json.loads(path.read_text()),ROOT)
    print(c,result['estimate_state'],result['layer_count'],result['total_thickness_nm'],result['state'],flush=True)
    return dict(case_id=c,estimate_state=result['estimate_state'],state=result['state'],
        layer_count=result['layer_count'],total_thickness_nm=result['total_thickness_nm'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--repo',required=True)
    parser.add_argument('action',choices=['prepare','run']);parser.add_argument('--case',action='append',default=[])
    parser.add_argument('--verified-checkpoint');parser.add_argument('--verified-plan-sha256');parser.add_argument('--verified-source-manifest-sha256')
    parser.add_argument('--workers',type=int,default=1)
    args=parser.parse_args()
    if args.action=='prepare':configure_core(args.repo);prepare();return
    if not isinstance(args.verified_checkpoint,str) or not COMMIT_RE.fullmatch(args.verified_checkpoint):
        raise ValueError('a verified published source checkpoint is required before search')
    digest(args.verified_plan_sha256);digest(args.verified_source_manifest_sha256)
    for c in args.case:case_id(c)
    plan=verify_admission(ROOT,args.verified_plan_sha256,args.verified_source_manifest_sha256,args.case)
    selected=args.case or plan['case_ids']
    if args.workers not in (1,2):raise ValueError('pilot permits one or two workers')
    configure_core(args.repo)
    started=time.perf_counter()
    arguments=[(c,args.verified_checkpoint,args.verified_plan_sha256,args.verified_source_manifest_sha256) for c in selected]
    if args.workers==1:rows=[run_one(a) for a in arguments]
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:rows=list(pool.map(run_one,arguments))
    batch_hash=hashlib.sha256(canonical_json(sorted(selected))).hexdigest()[:16]
    write_immutable_json(ROOT,f'batches/{batch_hash}.json',dict(case_ids=sorted(selected),results=rows,
        note='immutable batch result; wall time is recorded in each case, not used as a quality metric'))
    print('batch complete',len(rows),'cases',round(time.perf_counter()-started,2),'seconds',flush=True)

if __name__=='__main__':main()
