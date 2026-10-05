"""Controlled complete-domain aggregate from existing fields only."""
from pathlib import Path
import json
import sys
import numpy as np
from full_disk_cells import aggregate

HERE=Path(__file__).resolve().parent;BASE=HERE.parent
sys.path.insert(0,str(BASE))
from run_convergence import compare


def read(root,name):
    row=json.loads((root/(name+'.json')).read_text())
    with np.load(root/(name+'.npz')) as f:row.update({k:f[k].copy() for k in ('field_nm','x','y')})
    return row


def main():
    cfg=json.loads((HERE/'config.json').read_text());data=[];checks=[]
    finer=BASE/'continued_00625/periodic_finer'
    groups={}
    for probe in (False,True):
        groups[('grid',probe)]=[
            read(finer,'periodic_0.0015625_'+str(int(probe))),
            read(HERE,'pilot_g41' if not probe else 'grid41_probe'),
            read(HERE,'grid61_'+str(int(probe)))]
        groups[('source',probe)]=[read(HERE,f'source_q{q}_{int(probe)}') for q in (5,7,9)]
    for (axis,probe),rows in groups.items():
        metrics=[]
        for row in rows:
            m=aggregate(row['field_nm'],row['x'],float(row['x'][-1]));metrics.append(m)
            data.append({'axis':axis,'probe':probe,'grid':row['grid'],'source_order':row['source_order'],
                'legacy_represented_cv_percent':row['metrics']['cv_percent'],
                'legacy_represented_area_fraction':row['metrics']['represented_area_fraction'],**m})
        for i in range(1,len(rows)):
            delta=abs(metrics[i]['controlled_full_disk_cv_percent']-metrics[i-1]['controlled_full_disk_cv_percent'])
            original=compare(rows[i-1],rows[i])
            checks.append({'axis':axis,'probe':probe,'levels':[r['grid'] if axis=='grid' else r['source_order'] for r in rows[i-1:i+1]],
                'controlled_full_disk_cv_change_pp':delta,
                'controlled_cv_screen_pass':delta<cfg['metric_screens']['cv_sensitivity_pp'],
                'same_physical_roi_normalized_map_rms_pp':original['common_roi_normalized_field_rms_pp'],
                'legacy_cv_change_pp':original['cv_change_pp']})
    out={'status':'supplemental_same_full_disk_domain_aggregate','actual_core_calls':0,'rows':data,'checks':checks,
        'method':'Exact circle intersection of nearest-valid-node Voronoi control cells; piecewise-constant field approximation. Full disk area is partitioned without inventing outside-aperture values.',
        'original_metrics_preserved':True,'criterion_not_retrospectively_replaced':True,
        'spatial_quadrature_error_bound':'not_established','periodic_agreement_transfer':'not_certified',
        'engineering_ranking_allowed':False}
    (HERE/'controlled_aggregate_results.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))


if __name__=='__main__':main()
