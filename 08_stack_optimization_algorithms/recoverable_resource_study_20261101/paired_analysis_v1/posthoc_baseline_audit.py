"""Training diagnostic only: fresh audit of the old best coarse-grid candidates.

Does not revise baseline results or perform a new optimization.
"""
from pathlib import Path
import argparse,json,hashlib,sys,time


def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--baseline',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    root=Path(a.baseline);out=Path(a.out);out.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(root))
    from core_bridge import configure_core,request_from_dict,memory_service,audit_candidate,CORE_COMMIT
    from artifact_store import write_immutable_json
    configure_core(a.repo)
    class Limit:
        def __init__(self):self.start=time.monotonic()
        def is_set(self):return time.monotonic()-self.start>30.
    for case in ['train-41000-bandpass','train-41001-bandpass']:
        taskraw=(root/'cases'/case/'input.json').read_bytes();r=json.loads((root/'cases'/case/'result.json').read_text());task=json.loads(taskraw)
        trial=min(r['trials'],key=lambda x:(x['local_max_error'],x['layer_count'],x['label']))
        req=request_from_dict(task['request']);service=memory_service(req.frozen_material_snapshot['materials'])
        audit=audit_candidate(service,req,trial['candidate_design'],cancel_event=Limit())
        record=dict(schema='posthoc-baseline-training-diagnostic-v1',case_id=case,core_commit=CORE_COMMIT,
            input_sha256=hashlib.sha256(taskraw).hexdigest(),baseline_state=r['estimate_state'],
            selection_rule='minimum coarse-grid local_max_error; ties N then trial label; selected after observing baseline failure',
            selected_trial=trial,audit=audit,
            caveat='Additional evaluation, not an original baseline witness and not a blind test. A cancelled audit is inconclusive.')
        write_immutable_json(out,case+'.json',record)
        reports=audit['candidate_reports']
        print(case,'coarse_error',trial['local_max_error'],'N',trial['layer_count'],'new_audit',audit['state'],
            [(x['state'],x['targets_met'],x['max_normalized_error']) for x in reports],flush=True)

if __name__=='__main__':main()
