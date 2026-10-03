"""Small deterministic examples only. All response numbers synthetic."""
from bounded_response import *
from dataclasses import replace
from trust_region import certify_segment

def examples(panels=32):
    A=Scene(half_width_m=.08);B=Scene(half_width_m=.09)
    cases={
      'unit_response':Response(),
      'angular_response':Response(angular_a=(1.,1.)),
      'angular_uncertain':Response(angular_a=(0.,1.)),
      'scalar_fixed_target':Response(sticking_s0=(.9,.9)),
      'scalar_correlated_target':Response(sticking_s0=(.9,.9)),
      'density_uncertain':Response(density_kg_m3=(1800.,2200.)),
      'energy_temperature_response':Response(energy_b=(.2,.2),temperature_c=(.3,.3)),
      'unknown_retention':Response(sticking_s0=None),
      'negative_net':Response(erosion_mass_kg_m2=(1e-5,1e-5)),
      'cross_zero_net':Response(erosion_mass_kg_m2=(0.,3e-6)),
      'inventory_unresolved':Response(initial_inventory_kg_m2=(0.,0.),erosion_mass_kg_m2=(1e-8,1e-8)),
      'real_YbF3_Ge_template':Response(dataset_kind='unmeasured_template',material_id='YbF3',substrate_id='Ge_grade_unknown',density_basis='unknown_actual_film',model_transfer_status='unknown',source_scale_kg_s=None,density_kg_m3=None,sticking_s0=None,angular_a=None,energy_b=None,temperature_c=None,energy_history_eV=None,temperature_history_K=None,erosion_mass_kg_m2=None,initial_inventory_kg_m2=None)
    }
    result={'dataset_kind':'synthetic_counterexamples_not_material_fits','panels_per_visible_segment':panels,'frozen_scene_A':asdict(A),'frozen_scene_B':asdict(B),'upstream_segment_certificate':certify_segment(A,B,[0.]),'cases':{}}
    for name,r in cases.items():
        target=.9e-9 if name=='scalar_correlated_target' else 1e-9
        a=forward(A,r,target_m=target,panels=panels);b=forward(B,r,target_m=target,panels=panels)
        result['cases'][name]={'target_m':target,'response':asdict(r),'A':a,'B':b,'comparison':compare(a,b)}
    # Information-loss example: same unweighted D, different arrival-angle distributions.
    result['same_D_different_response']={'synthetic':True,'angle_deg':[0.,60.],'transfer_bins_A_s_m2':[1.,0.],'transfer_bins_B_s_m2':[0.,1.],'unweighted_D':[1.,1.],'retention_bins':[1.,.25],'retained_D':[1.,.25]}
    # Exact rational identity eliminates shared scale before interval evaluation.
    result['shared_positive_scale_identity']={'scale_interval_m3_s':[.5e-9,2e-9],'D_target_s_m2':1.,'symbolic':'((c*D-c*Dstar)/(c*Dstar))^2/2 = ((D-Dstar)/Dstar)^2/2 for every common c>0','relative_objective_preserved':True,'independent_box_target_forbidden':True}
    result['denominator_examples']={k:normalize_positive(n,d,1e-12) for k,n,d in [('positive',[2.,2.],[4.,4.]),('zero',[2.,2.],[0.,0.]),('negative',[2.,2.],[-2.,-1.]),('cross_zero',[2.,2.],[-1.,1.]),('near_zero',[2.,2.],[1e-14,2e-14]),('unknown',None,[1.,1.])]}
    return result

if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--output',required=True);p=a.parse_args()
    out=Path(p.output);out.write_text(json.dumps(examples(),ensure_ascii=False,indent=2,allow_nan=False)+'\n');print(out)
