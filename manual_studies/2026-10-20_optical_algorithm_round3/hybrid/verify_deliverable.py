#!/usr/bin/env python3
"""Recompute checks and write results/deliverable_consistency.json."""
import json
from pathlib import Path
import numpy as np
import run_hybrid as h

def main():
    d=h.ROOT/'results';raw=json.loads((d/'results.json').read_text());rs=raw['results'];checks={}
    checks['120_unique_main_runs']=len(rs)==120 and len({(r['case']['name'],r['method'],r['seed']) for r in rs})==120
    checks['all_actual_calls_6000']=all(r['actual_objective_calls']==6000 for r in rs)
    checks['stage_counts_sum_to_actual_calls']=all(sum(r['stage_counts'].values())==r['actual_objective_calls'] for r in rs)
    checks['point_counts_consistent']=all(r['actual_optical_point_solves']==r['actual_objective_calls']*r['train_optical_points_per_call'] for r in rs)
    checks['all_thickness_within_bounds']=all(np.all((np.array(r['thickness_um'])>=h.LOWER)&(np.array(r['thickness_um'])<=h.UPPER)) for r in rs)
    maxlossdiff=maxviodiff=0.
    for r in rs:
        o=h.Objective(r['case'],1,r['train_points_per_window']);o.scalar(r['thickness_um']);maxlossdiff=max(maxlossdiff,abs(o.best_loss-r['training_loss_of_selected']));maxviodiff=max(maxviodiff,abs(o.best_violation-r['training_max_standardized_violation']))
    checks['all_stored_selected_training_metrics_recomputed_exactly']=maxlossdiff==0 and maxviodiff==0
    checks['summary_exactly_recomputed']=h.summarize(rs)==json.loads((d/'summary.json').read_text())
    replays=json.loads((d/'replay.json').read_text());checks['24_replays_bitwise_equal']=len(replays)==24 and all(r['thickness_bitwise_equal'] and r['training_loss_bitwise_equal'] and r['counts_equal'] and r['stage_counts_equal'] for r in replays)
    # Store grid overlap honestly. These audit grids are independent evaluations,
    # not disjoint statistical holdouts or continuous-domain certificates.
    train=np.linspace(0,1,81);overlaps={}
    for n in [1025,4097]:
        mid=(np.arange(n)+.5)/n;overlaps[n]=int(sum(np.any(np.isclose(train,z,rtol=0,atol=1e-13)) for z in mid))
    checks['documented_midpoint_overlap_counts']=overlaps=={1025:5,4097:1}
    result={'all_checks_passed':all(checks.values()),'checks':checks,'max_selected_training_loss_abs_difference':maxlossdiff,'max_selected_training_violation_abs_difference':maxviodiff,'interior_audit_training_overlap_points_per_window':overlaps,'common_endpoints_per_window':2}
    (d/'deliverable_consistency.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));assert result['all_checks_passed']
if __name__=='__main__':main()
