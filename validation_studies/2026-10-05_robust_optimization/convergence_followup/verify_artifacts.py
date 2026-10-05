"""Verify new artifacts, and preserve the first round and canonical Python."""
import hashlib
import json
from run_followup import HERE, first_round_identity, source_hashes, digest


def main():
    manifest=json.loads((HERE/'artifact_manifest.json').read_text())
    errors=[]
    for name,expected in manifest['files'].items():
        p=(HERE/name).resolve()
        if not p.is_relative_to(HERE) or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:
            errors.append(f'Missing or changed follow-up artifact: {name}')
    pilot=json.loads((HERE/'pilot_results.json').read_text())
    if first_round_identity()!=pilot['first_round_identity']:
        errors.append('First-round artifact changed')
    if source_hashes()!=pilot['product_python_identity']:
        errors.append('Canonical product Python changed')
    if digest(HERE/'config.json')!=pilot['config_sha256']:
        errors.append('Pilot config changed')
    result=json.loads((HERE/'followup_results.json').read_text())
    calls=sum(v['actual_forward_calls'] for v in result['levels'].values())
    if calls!=result['actual_forward_calls'] or calls>600:
        errors.append('Actual-call budget mismatch')
    if any(v['actual_forward_calls']!=40 for v in result['levels'].values()):
        errors.append('Unexpected per-level call count')
    print(json.dumps({'followup_files_checked':len(manifest['files']),
        'first_round_files_checked':len(pilot['first_round_identity']),
        'product_python_files_checked':len(pilot['product_python_identity']),
        'pilot_calls':pilot['actual_forward_calls'],'main_calls':calls,
        'errors':errors,'status':'passed' if not errors else 'failed'},indent=2))
    if errors:
        raise SystemExit(1)


if __name__=='__main__':
    main()
