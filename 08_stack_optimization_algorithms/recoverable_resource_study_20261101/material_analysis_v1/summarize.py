"""Read completed material tests without rerunning or rewriting their labels."""
from pathlib import Path
import argparse,json,csv,hashlib

def main():
    p=argparse.ArgumentParser();p.add_argument('--pilot',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    pilot=Path(a.pilot);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    plan=json.loads((pilot/'plan.json').read_text());rows=[]
    for case in plan['case_ids']:
        folder=pilot/'cases'/case;t=json.loads((folder/'input.json').read_text());r=json.loads((folder/'result.json').read_text())
        assert r['case_id']==case
        row=dict(case_id=case,group=t['group'],family=t['family'],state=r['state'],estimate_state=r['estimate_state'],
          layers=r['layer_count'],thickness_nm=r['total_thickness_nm'],selected_hash=r['selected_hash'],
          witness_count=len(r['retained_witness_hashes']),elapsed_seconds=r['elapsed_seconds'],
          min_fit_error=min((x['local_max_error'] for x in r['trials']),default=None),
          unknown_k_materials=';'.join(x['material_id'] for x in t['optical_domain_checks'] if x['unknown_k_assumed']),
          max_known_film_k=max(x['k_max'] for x in t['optical_domain_checks'][:2] if not x['unknown_k_assumed']),
          result_sha256=hashlib.sha256((folder/'result.json').read_bytes()).hexdigest())
        if r['selected_hash']:
            w=json.loads((folder/'witnesses'/f"{r['selected_hash']}.json").read_text())
            assert (w['layer_count'],w['total_thickness_nm'])==(row['layers'],row['thickness_nm'])
        else:assert row['layers'] is None and row['thickness_nm'] is None and row['witness_count']==0
        rows.append(row)
    (out/'results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    with (out/'results.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    for group in plan['groups']:
        print(group,[(r['family'],r['estimate_state'],r['layers'],None if r['thickness_nm'] is None else round(r['thickness_nm'],2)) for r in rows if r['group']==group])
if __name__=='__main__':main()
