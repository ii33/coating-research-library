"""Tiny deterministic enclosure demonstration, not the batch/device plan."""
from bounded_optics import *
def run(cells=8):
    c=load_case();recipes=json.loads((ROOT/'data/legacy_selection.json').read_text())['records'];r=next(x for x in recipes if x['id']==c['recipe_id'])
    cases={key:propagate(r,c['bridge'],c['material'],c['measurement'],v,cells) for key,v in c['variants'].items()}
    return {'dataset_kind':'synthetic_only','target':'R of declared 3-node MIR operator <=0.05','outcomes':cases,'A_vs_B':distinguish(cases['A'],cases['B'],c['measurement']['measurement_error_abs']),'A_vs_C':distinguish(cases['A'],cases['C'],c['measurement']['measurement_error_abs']),'paired_A_vs_C':paired_difference(r,c['bridge'],c['material'],c['measurement'],'1','1.002',cells),'budget':{'latent_cells_per_variant':cells,'variants':3,'spectral_nodes':3,'layers':6,'monte_carlo_draws':0,'devices':0},'production_qualified':False}
if __name__=='__main__':
    result=run();(ROOT/'verification/tiny_results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
