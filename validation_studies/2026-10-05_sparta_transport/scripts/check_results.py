#!/usr/bin/env python3
"""Read-only artifact audit; never simulates particles or alters solver state."""
from pathlib import Path
import csv, hashlib, json, math, sys
import numpy as np
from scipy import stats
from scipy.integrate import quad
import study

ROOT=study.ROOT
def load(path):return json.loads(path.read_text())

def validate():
    findings=[]; cases={}
    for path in sorted((ROOT/'results').glob('*/checked_results.json')):
        directory=path.parent;name=directory.name;result=load(path)
        contract=load(directory/'input_contract.json');execution=load(directory/'execution.json')
        assert execution['returncode']==0,(name,'not executed successfully')
        assert contract['data_origin']=='synthetic'
        assert (directory/'log.sparta').read_text().startswith('SPARTA (27 Aug 2026)')
        if name=='injection':
            assert result['emission_distribution_pass']
            assert result['emitted']==result['inventory_final']==50000
            assert result['flux_balance_residual_particles']==0
        elif name.startswith('geometry'):
            assert result['geometry_pass'],name
            assert result['flux_balance_residual_particles']==0,name
            assert result['emitted']==result['capture']+result['other_surface_loss']+result['open_boundary_escape']+result['inventory_final']
            rows=study.statrows(directory/'log.sparta')
            assert len(rows)==contract['emit_steps']+contract['drain_steps']
            assert sum(r[5] for r in rows)==result['emitted']
            assert sum(r[2] for r in rows)==result['open_boundary_escape']
            assert sum(r[3] for r in rows)==result['capture']+result['other_surface_loss']
            assert sum(len(d) for _,_,d in study.frames(directory/'surface.tally'))==result['surface_tally_events']
            if contract['emission_mode']=='mixture_flux':assert result['emission_flux_pass']
        elif name.startswith('bath'):
            assert result['survival_pass'],name
            assert result['tracer_ids_unique'] and result['tracer_ids_conserved'] and result['collision_tracer_ids_subset_initial']
            assert result['collision_tally_matches_global_count']
            assert result['collision_tally_frames']==contract['steps']+1
            assert result['bath_particles_initial']==result['bath_particles_final']
            assert sum(result['tracer_collision_count_histogram'].values())==result['tracer_count']
            assert result['uncollided_count']==result['tracer_collision_count_histogram']['0']
        else:raise AssertionError(name)
        cases[name]={'contract':contract,'result':result,'execution':execution}
        findings.append({'case':name,'passed':True})

    refs={str(n):study.reference(n) for n in [12,24,40]}
    assert max(refs.values())-min(refs.values())<1e-12
    assert abs(refs['40']-.2376441865228383)<1e-13
    # Independent reduced convolution integral; split at the overlap kink.
    def overlap(d):return .02 if d<=.04 else .06-d
    total=0.
    for xa,xb in [(0,.04),(.04,.06)]:
        for ya,yb in [(0,.04),(.04,.06)]:
            total+=quad(lambda x:quad(lambda y:overlap(x)*overlap(y)/(.1**2+x*x+y*y)**2,ya,yb,epsabs=1e-12,epsrel=1e-12)[0],xa,xb,epsabs=1e-12,epsrel=1e-12)[0]
    convolution=4*.1**2/(math.pi*.02**2)*total
    assert abs(convolution-refs['40'])<1e-13
    refs['independent_2D_convolution']=convolution

    convergences=[]
    groups=[('geometry_mesh',['geometry_base','geometry_mesh20','geometry_mesh40'],'capture_fraction','emitted'),('geometry_dt',['geometry_base','geometry_dt_half','geometry_dt_quarter'],'capture_fraction','emitted'),('geometry_weight',['geometry_base','geometry_weight_half','geometry_weight_quarter'],'capture_fraction','emitted'),('geometry_surface',['geometry_base','geometry_surface2','geometry_surface4'],'capture_fraction','emitted'),('static_mesh',['bath_static_tau01','bath_static_mesh20','bath_static_mesh40'],'uncollided_fraction','tracer_count'),('static_dt',['bath_static_tau01','bath_static_dt_half','bath_static_dt_quarter'],'uncollided_fraction','tracer_count'),('static_weight',['bath_static_tau01','bath_static_weight_half','bath_static_weight_quarter'],'uncollided_fraction','tracer_count'),('thermal_mesh',['bath_thermal','bath_thermal_mesh20','bath_thermal_mesh40'],'uncollided_fraction','tracer_count'),('thermal_dt',['bath_thermal','bath_thermal_dt_half','bath_thermal_dt_quarter'],'uncollided_fraction','tracer_count'),('thermal_weight',['bath_thermal','bath_thermal_weight_half','bath_thermal_weight_quarter'],'uncollided_fraction','tracer_count')]
    for label,names,key,nkey in groups:
        differences=[]
        for a,b in zip(names[:-1],names[1:]):
            ra,rb=cases[a]['result'],cases[b]['result'];p=ra.get('expected_fraction',ra.get('reference_capture_fraction'))
            sigma=math.sqrt(p*(1-p)*(1/ra[nkey]+1/rb[nkey]))
            difference=abs(ra[key]-rb[key]);budget=.01 if label.startswith('geometry') else .02
            # Absolute fraction budget; stochastic consistency independently checked.
            differences.append({'from':a,'to':b,'difference_absolute_fraction':difference,'z_difference_independent_approximation':difference/sigma,'budget_absolute_fraction':budget,'passed':bool(difference<=budget and difference<=4*sigma)})
        convergences.append({'group':label,'two_refinements':differences,'passed':all(d['passed'] for d in differences),'interpretation':'MC-resolution-limited refinement consistency, not deterministic 1% accuracy proof'})
    assert all(c['passed'] for c in convergences),convergences

    replications={}
    for mode,base in [('static','bath_static_tau01'),('thermal','bath_thermal')]:
        names=[base]+[f'bath_{mode}_seed{s}' for s in [18631,47389,81761,124679]]
        values=np.array([cases[n]['result']['uncollided_fraction'] for n in names]);mean=float(values.mean());se=float(values.std(ddof=1)/math.sqrt(len(values)));margin=float(stats.t.ppf(.975,len(values)-1)*se)
        replications[mode]={'names':names,'independent_seeds':len(names),'mean_uncollided_fraction':mean,'between_run_standard_error':se,'student_t_95_interval':[mean-margin,mean+margin],'analytic_expected':cases[base]['result']['expected_fraction'],'interval_model':'Independent run means; five replicates give imprecise variance estimate'}

    with (ROOT/'results'/'comparison.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['case','kind','observed_fraction','expected_fraction','CI95_low','CI95_high','z_error','elapsed_seconds','passed'])
        for name,c in cases.items():
            r=c['result'];key='capture_fraction' if name.startswith('geometry') else 'uncollided_fraction'
            if key in r:writer.writerow([name,c['contract']['kind'],r[key],r.get('expected_fraction',r.get('reference_capture_fraction')),*r['confidence_interval_95'],r['z_error'],c['execution']['elapsed_seconds'],r.get('geometry_pass',r.get('survival_pass'))])
    summary={'study_date_UTC':'2026-10-05','solver':'unmodified official SPARTA serial','case_count':len(cases),'case_checks':findings,'references':refs,'convergence':convergences,'replication_uncertainty':replications,'all_checks_passed':True,'physical_equipment_prediction_validated':False,'finite_geometry_gas_scattering_deposition_run':False,'full_double_mask_planetary_geometry_run':False,'cross_sections':'synthetic constant hard sphere; no real vapor-background-gas cross sections','total_final_case_CPU_wall_seconds':sum(c['execution']['elapsed_seconds'] for c in cases.values()),'case_results':{n:c['result'] for n,c in cases.items()}}
    study.save(ROOT/'results'/'validation_summary.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k not in ['case_results','convergence','case_checks']},indent=2))
    return summary

if __name__=='__main__':validate()
