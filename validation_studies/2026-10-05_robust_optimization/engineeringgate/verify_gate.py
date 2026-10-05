import hashlib
import json
from run_gate import HERE,historical_identity,source_hashes,sha


def main():
    manifest=json.loads((HERE/'artifact_manifest.json').read_text());errors=[]
    for name,digest in manifest['files'].items():
        p=(HERE/name).resolve()
        if not p.is_relative_to(HERE) or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
            errors.append(f'Gate artifact changed: {name}')
    pilot=json.loads((HERE/'pilot_results.json').read_text());result=json.loads((HERE/'gate_results.json').read_text())
    if historical_identity()!=pilot['historical_identity']:errors.append('Historical files changed')
    if source_hashes()!=pilot['product_python_identity']:errors.append('Canonical product changed')
    if sha(HERE/'config.json')!=pilot['config_sha256']:errors.append('Gate config changed')
    calls=0
    for level in result['levels']:
        if level['actual_dt_s']>.05:errors.append('Actual step too large')
        for case in level['cases']:
            for method in case['methods'].values():
                calls+=method['counter']['forward_calls']
                for row in [method['nominal']]+method['rows']:
                    if not row['valid'] or not row['time_step_gate_pass']:errors.append('Time-step row failed')
                    for audit in row['integration_audits']:
                        if audit['actual_time_steps']!=level['actual_time_steps'] or not audit['all_requested_steps_observed']:
                            errors.append('Missing or truncated nodes')
    if calls!=120 or result['main_actual_calls']!=calls:errors.append('Call budget mismatch')
    print(json.dumps({'new_files_checked':len(manifest['files']),'historical_files_preserved':len(pilot['historical_identity']),
        'product_python_files_preserved':len(pilot['product_python_identity']),'pilot_calls':pilot['counter']['forward_calls'],
        'main_calls':calls,'engineering_ranking_allowed':False,'errors':errors,'status':'passed' if not errors else 'failed'},indent=2))
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
