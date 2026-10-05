from pathlib import Path
import hashlib
import json
from run_full_process import HERE,old_identity,source_hashes,load_inputs


def main():
    m=json.loads((HERE/'artifact_manifest.json').read_text());errors=[]
    for name,digest in m['files'].items():
        p=(HERE/name).resolve()
        if not p.is_relative_to(HERE) or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:errors.append(name)
    selected=json.loads((HERE/'selected_input_manifest.json').read_text())
    if old_identity()!=selected['historical_identity']:errors.append('historical artifacts changed')
    if source_hashes()!=selected['product_python_identity']:errors.append('canonical Python changed')
    cfg=json.loads((HERE/'config.json').read_text());load_inputs(cfg)
    p=json.loads((HERE/'convergence_results.json').read_text())
    for result in p['results'].values():
        if result['total_duration_s']!=10888.888888888889 or len(result['step_results'])!=2:errors.append('process truncation')
        for audit in result['core_audits']:
            if not audit.get('all_steps_observed') or audit['actual_dt_s']>.05:errors.append('node audit failed')
    print(json.dumps({'checkpoint_files_checked':len(m['files']),'historical_files_preserved':len(selected['historical_identity']),
        'product_python_files_preserved':len(selected['product_python_identity']),'errors':errors,'status':'passed' if not errors else 'failed'},indent=2))
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
