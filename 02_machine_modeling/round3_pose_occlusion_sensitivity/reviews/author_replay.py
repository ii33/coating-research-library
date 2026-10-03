"""Author's targeted replay after the one independent finding; read-only by default.
Does not repeat the independent review or overwrite its initial evidence.
"""
from pathlib import Path
import hashlib,json,sys
from dataclasses import replace
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'models'))
from event_reference import Scene,evaluate
from analytic_oracle import exact_value_gradient

def replay():
    sc=replace(Scene(),half_width_m=1e-11);r=evaluate(0.,sc)
    try:exact_value_gradient(sc);rejected=False
    except ValueError as e:rejected=str(e)=='event order unresolved'
    v,j=exact_value_gradient(Scene());base=evaluate(0.,Scene())
    return {'kind':'author_targeted_replay_not_second_review','finding':'oracle missing event-order gate',
        'initial_review_evidence_sha256':hashlib.sha256((R/'reviews/independent_results.json').read_bytes()).hexdigest(),
        'input_sha256':{p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in ('models/event_reference.py','models/analytic_oracle.py','verification/test_small.py')},
        'checks':{'reference_still_withholds':r['gradient'] is None,'oracle_now_rejects_event_order':rejected,'ordinary_branch_retained':bool(abs(v-base['value_s_m2'])<1e-12 and max(abs(a-b) for a,b in zip(j,base['gradient']))<1e-12)},
        'formal_model_chain':'pending'}
if __name__=='__main__':print(json.dumps(replay(),indent=2))
