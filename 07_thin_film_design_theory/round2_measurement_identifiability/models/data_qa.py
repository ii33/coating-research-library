"""Self-contained source/contract/vendor checks; reads no upstream files."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
def run():
    for item in json.loads((ROOT/'data/frozen_dependencies.json').read_text()):
        assert hashlib.sha256((ROOT/item['copy']).read_bytes()).hexdigest()==item['sha256']
    s=json.loads((ROOT/'sources/source_registry.json').read_text())['sources'];assert len(s)==6
    assert len({r['id'] for r in s})==len(s)
    for r in s:
        assert r['url'].startswith('https://') and (ROOT/r['summary_path']).is_file()
        assert r['reader_redistribution'] is False
    c=json.loads((ROOT/'data/measurement_contract.json').read_text())
    assert c['actual_user_hardware'] is None and not c['production_qualified']
    d=json.loads((ROOT/'verification/diagnostics.json').read_text())
    assert d['global_alias']['local']['rank']==2
    assert d['global_alias']['same_condition_max_abs_difference']<1e-12
    assert d['cases']['normal_incidence_ratio']['rank']==0
    status=json.loads((ROOT/'stage_status.json').read_text())
    assert status['status']=='implementation_ready_validation_pending'
    assert status['heavy_run']=='not_run_awaiting_device'
    return {'status':'passed','source_records':len(s),'vendor_hash_match':True,'actual_hardware':None,
            'synthetic_only':True,'heavy_execution':'not_run_awaiting_device','sibling_reads':False}
if __name__=='__main__':print(json.dumps(run(),indent=2))
