"""Re-audit a published synthetic witness, not the missing 64-group experiment."""
from pathlib import Path
from dataclasses import asdict
import argparse
import hashlib
import json
import platform
import time
import numpy as np
import scipy
from core_bridge import CORE_COMMIT, configure_core, memory_service, request_from_dict, freeze_request, audit_candidate


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',required=True)
    parser.add_argument('--case',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    out=Path(args.output)
    if out.exists():
        raise ValueError('refuse overwrite an existing replay record')
    configure_core(args.repo)
    path=Path(args.case);raw=path.read_bytes();case=json.loads(raw)
    service=memory_service(case['material_source']['materials'])
    # The public summary reported 513 dense points per 17-point window.
    # (17-1)*32+1=513. This explicitly selects the new replay's audit profile;
    # it does not pretend the abbreviated public request stored every option.
    request=request_from_dict(case['original_request'],validation_samples_multiplier=32)
    frozen=freeze_request(service,request)
    started=time.perf_counter();results={}
    for label in ('old_witness','new_witness'):
        audit=audit_candidate(service,frozen,case[label]['design'])
        witness=audit['pareto_witnesses']
        if not witness:
            raise ValueError(label+' did not pass the fresh audit')
        assert witness[0]['layer_count']==case[label]['layer_count']
        assert np.isclose(witness[0]['total_thickness_nm'],case[label]['total_thickness_nm'],rtol=0,atol=1e-8)
        results[label]=audit
        print(label,witness[0]['layer_count'],witness[0]['total_thickness_nm'],flush=True)
    result=dict(schema='published-single-case-replay-v1',core_commit=CORE_COMMIT,
        source_sha256=hashlib.sha256(raw).hexdigest(),source_scope=case['scope'],
        profile_note='Fresh audit at multiplier32, selected from published dense-grid statistics; not reconstruction of missing training data',
        versions=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),
        frozen_request=asdict(frozen),audits=results,elapsed_seconds=time.perf_counter()-started)
    payload=json.dumps(result,ensure_ascii=False,allow_nan=False,indent=2)
    out.parent.mkdir(parents=True,exist_ok=True)
    temporary=out.with_suffix('.tmp');temporary.write_text(payload);temporary.replace(out)
    print('replay complete',result['elapsed_seconds'],flush=True)

if __name__=='__main__':
    main()
