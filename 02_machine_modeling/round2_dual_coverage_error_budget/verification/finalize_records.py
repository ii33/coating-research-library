"""Derive release status and error ledger from frozen synthetic results; no physics runs."""
from pathlib import Path
import json,csv,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def write(p,x):(ROOT/p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
r=json.loads((ROOT/'data/results.json').read_text());one=json.loads((ROOT/'verification/first_execution_summary.json').read_text());two=json.loads((ROOT/'verification/second_execution_summary.json').read_text())
review=json.loads((ROOT/'reviews/independent_narrow_results.json').read_text())
cumulative=one['reported_rays']+one['conservative_unmetered_case_A_B_allowance']+two['reported_rays']+r['budget']['ray_evaluations']
assert cumulative<150000000
write('verification/budget_ledger.json',{'main_executions':3,'first_reported':one['reported_rays'],'first_unmetered_A_B_conservative_allowance':one['conservative_unmetered_case_A_B_allowance'],'second_counted':two['reported_rays'],'final_counted':r['budget']['ray_evaluations'],'cumulative_conservative_total':cumulative,'main_limit':150000000,'passed':True,'independent_review_cumulative_rays':446166,'independent_review_limit':3000000,'stop_reason':'fixed four-case grid and review checklist completed; unaccepted errors retained, no extra refinement or candidate search'})
rows=[
 ['time_discretization','S1 T1 to T2 diagnostic set',.0008529628651882121,'relative integral difference',.003,'pass_for_integrals_only','ion-only difference 0.0100318281 s exceeds 0.01 s'],
 ['source_quadrature','S1 to S2 at T1 diagnostic set',.005354381866356135,'relative integral difference',.003,'not_met','empirical difference, not bound'],
 ['source_family_holdout','S2T2 to equal-area 203 nodes',.0020298900041413994,'relative integral difference',.003,'pass_for_integrals_only','ion-only difference 0.0142970612 s exceeds 0.01 s'],
 ['substrate_space','P1 to P2 at S1T1',.00016289782353978797,'relative area mean difference',.003,'pass_for_fixed_kernel','not continuous extrema or complete source/time accuracy'],
 ['substrate_space','P1 to P2 at S1T1',.0005923740553549217,'absolute normalized sample PV difference',.008,'pass_for_fixed_kernel','sample PV not continuous bound'],
 ['geometry_representation','both finite plates to thin plates',.15084043757460014,'max relative diagnostic difference','','model_sensitivity','not uncertainty distribution'],
 ['geometry_input','plate x displacement +/-0.001 m',.010291629187825642,'max relative diagnostic difference','','scenario_only','no measured distribution or confidence interval'],
 ['intersection_float','fixed 1e-14 m parallel cutoff','','near-sidewall counterexample','','known_limit','nondegenerate random agreement not universal certificate'],
 ['calibration','Q_v Q_i density retention cup response','','unknown','','unverified','no real machine calibration data'],
 ['model_form','ballistic ion lobe unit retention no resputtering','','unknown','','unverified','not CFD PIC beam optics or material response']]
with (ROOT/'data/error_budget.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['category','comparison','value','unit','tolerance','status','scientific_limit']);w.writerows(rows)
d=np.genfromtxt(ROOT/'data/C_main_map.csv',delimiter=',',names=True);A=np.pi*.06**2
N=float(A*np.sum(d['area_fraction']*d['net_atoms_m2']));D=float(A*np.sum(d['area_fraction']*d['ion_fluence_m2']));U=float(A*np.sum(d['area_fraction']*d['incident_energy_J_m2']))
write('data/area_totals.json',{'grid':'S1T1P2','numerical_status':r['status'],'disk_area_m2':A,'net_atoms':N,'positive_ions':D,'incident_kinetic_energy_J':U,'total_ions_per_total_net_atom':D/N,'area_mean_local_ratio':float(np.sum(d['area_fraction']*d['ion_to_net_atom_ratio'])),'note':'Not equal quantities; zero-area boundary witnesses are excluded from totals.'})
# Verify frozen copies against originals without modifying them.
project=ROOT.parents[1]
pairs={'models/frozen/t01_dual_coverage.py':'01_machine_structures/round2_topology_alignment/models/dual_coverage.py','models/frozen/t02_deposition_reference.py':'02_machine_modeling/models/deposition_reference.py','models/frozen/t05_source_reference.py':'05_evaporation_sources/models/source_reference.py','models/frozen/t10_ion_assist_reference.py':'10_ion_sources/models/ion_assist_reference.py','data/t01_contract.json':'01_machine_structures/round2_topology_alignment/data/synthetic_contract.json'}
checks={k:hashlib.sha256((ROOT/k).read_bytes()).hexdigest()==hashlib.sha256((project/v).read_bytes()).hexdigest() for k,v in pairs.items()}
assert all(checks.values());write('verification/frozen_origin_check.json',checks)
# The independent final check hashed the final adapter; check actual final bytes.
for rel,h in review['input_sha256'].items():
 p=ROOT/rel
 if p.exists():assert hashlib.sha256(p.read_bytes()).hexdigest()==h,rel
write('round2_stage.json',{'topic':'T02','round':2,'version':'0.1','status':'frozen_bounded_partial','numerical_status':r['status'],'date_utc':'2026-10-02','scope':'D conditional direct external gear baseline; dual finite sources and finite static rectangular solids','unit_tests':20,'independent_review':'one bounded narrow mathematical check, 60000 random rays plus analytic/deterministic checks; caveat retained','source_figure_C_I':'unsupported_not_revisited','real_machine_validation':'not_performed','production_qualification':'not_claimed','budget_ledger':'verification/budget_ledger.json','public_allowlist':'verification/public_allowlist.txt','handoff':'T03_ROUND2_HANDOFF.md','unmet':['source quadrature target at S1','ion-only indicator integral at finest checked levels','all P2 points at S2T2','continuous spatial extrema','fixed-epsilon extreme grazing robustness','real source calibration and material response']})
print(json.dumps({'main_cumulative_conservative':cumulative,'source_copies_unchanged':all(checks.values()),'stage':'frozen_bounded_partial'},indent=2))
