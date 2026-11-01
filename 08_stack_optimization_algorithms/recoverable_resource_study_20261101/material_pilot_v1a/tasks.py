"""Fixed visible-band objectives across explicitly sourced material combinations."""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import hashlib
import json
import numpy as np
from artifact_store import canonical_json
from core_bridge import memory_service, freeze_request, CORE_COMMIT

GROUPS=('sio2_ta2o5','sio2_tio2','sio2_hfo2','mgf2_tio2','ybf3_zns','ybf3_zns_substrate')
FAMILIES=('ar','hr','mixed','bandpass','dual_ar','mean_mix')
PAIRS={
 'sio2_ta2o5':('sio2','ta2o5','silica'),
 'sio2_tio2':('sio2','tio2','silica'),
 'sio2_hfo2':('sio2','hfo2','silica'),
 'mgf2_tio2':('mgf2','tio2','silica'),
 'ybf3_zns':('ybf3','zns','silica'),
 'ybf3_zns_substrate':('ybf3','zns','zns_bulk'),
}
SOURCES={
 'sio2':('SiO2_film','ri_sio2_rodriguez_de_marcos'),
 'ta2o5':('Ta2O5_film','ri_ta2o5_rodriguez_de_marcos'),
 'tio2':('TiO2_film','ri_tio2_jolivet_amorphous'),
 'mgf2':('MgF2_film','ri_mgf2_rodriguez_de_marcos'),
 'ybf3':('YbF3_film','ri_ybf3_amotchkina_n'),
 'zns':('ZnS_film','ri_zns_amotchkina_nk'),
 'silica':('fused_silica_method_demonstrator','ri_sio2_malitson'),
 'zns_bulk':('ZnS_substrate','ri_zns_debenham_n'),
 'hfo2':('HfO2_film','rii_hfo2_bright'),
}


def source_records(group):
    import coat_sim
    repo=Path(coat_sim.__file__).resolve().parent.parent
    catalog_path=repo/'data/optical_catalog.json'
    materials=json.loads(catalog_path.read_text())['materials']
    records=[];provenance=[]
    for alias in PAIRS[group]:
        material,set_id=SOURCES[alias]
        path=catalog_path
        if alias=='hfo2':
            path=repo/'data/optical_catalog_sources/rii_optical_only_public_20261006_v1/provenance.json'
            candidate=next(c for c in json.loads(path.read_text())['candidates'] if c['active_optical_group']['id']==set_id)
            optical=deepcopy(candidate['active_optical_group'])
        else:
            row=next(r for r in materials if r['material_id']==material)
            optical=deepcopy(next(s for s in row['optical_constants'] if s['id']==set_id))
        records.append(dict(id=alias,name=material,design_ready=True,optical_sets=[optical]))
        provenance.append(dict(alias=alias,material_id=material,optical_set_id=set_id,
            core_commit=CORE_COMMIT,repository_path=path.relative_to(repo).as_posix(),
            source_file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            optical_group_sha256=hashlib.sha256(canonical_json(optical)).hexdigest(),
            unknown_k=optical.get('k') is None and optical.get('k_data') is None,
            limitation='Source-specific published model/table, not user process calibration. Missing k is explicitly assumed zero only for this conditional study.'))
    return records,provenance


def make_task(group,family):
    from coat_sim.core.film_design import new_design
    from coat_sim.core.film_auto_synthesis import FilmSynthesisRequest
    from coat_sim.core.film_optimization import FilmOptimizationObjective as Objective
    from coat_sim.core.film_objective_criteria import FilmObjectiveConstraint as Constraint
    from coat_sim.core.film_optimization_needle import FilmNeedleMaterialReference as Material
    from coat_sim.core.optical_constants import prepare_optical_set
    from coat_sim.core.film_synthesis_absorption import sample_synthesis_optical
    if group not in GROUPS or family not in FAMILIES:raise ValueError('undeclared task')
    records,provenance=source_records(group)
    def obj(lo,hi,metric,lower=None,upper=None,mean=False):
        criterion=Constraint(lower_bound=lower,upper_bound=upper)
        return Objective(lo,hi,17,angles_deg=(0.,30.),polarization='unpolarized',metric=metric,
            pointwise=Constraint(enabled=False) if mean else criterion,
            mean=criterion if mean else Constraint(enabled=False),
            normalization_scale=max(.001,upper if upper is not None else 1-lower))
    objectives={
      'ar':lambda:(obj(450,700,'R',upper=.015),),
      'hr':lambda:(obj(500,650,'R',lower=.95),),
      'mixed':lambda:(obj(420,500,'R',lower=.9),obj(650,780,'T',lower=.9)),
      'bandpass':lambda:(obj(420,480,'R',lower=.85),obj(550,620,'T',lower=.85),obj(700,780,'R',lower=.85)),
      'dual_ar':lambda:(obj(420,500,'R',upper=.02),obj(650,780,'R',upper=.02)),
      'mean_mix':lambda:(obj(420,500,'R',lower=.9,mean=True),obj(650,780,'T',lower=.92,mean=True)),
    }[family]()
    # Explicitly exercise strict source sampling at every declared audit grid point.
    # Native extrema may add points inside these intervals; no extrapolation allowed.
    optical_checks=[]
    for record in records:
        optical=record['optical_sets'][0];sampler=prepare_optical_set(optical,k_sampling_policy='source')
        samples=[sample_synthesis_optical(sampler,float(w),assume_unknown_k_zero=True)
            for o in objectives for w in np.linspace(o.wavelength_min_nm,o.wavelength_max_nm,513)]
        optical_checks.append(dict(material_id=record['id'],optical_set_id=optical['id'],
            n_min=min(s[0] for s in samples),n_max=max(s[0] for s in samples),
            k_min=min(s[1] for s in samples),k_max=max(s[1] for s in samples),
            unknown_k_assumed=any(not s[2].get('k_known') for s in samples)))
    environment=new_design(design_id=f'material-{group}-{family}')
    environment['name']='Published-material conditional visible-band research'
    environment['assume_lossless']=True  # Only missing k; never overwrites known extinction.
    substrate=records[2];environment['substrate'].update(material_id=substrate['id'],optical_set_id=substrate['optical_sets'][0]['id'])
    request=FilmSynthesisRequest(environment,objectives,
        tuple(Material(r['id'],r['optical_sets'][0]['id']) for r in records[:2]),
        validation_samples_multiplier=32,max_cycles=4,max_evaluations=300,search_strategy='legacy',
        cpu_workers=1,parallel_batch_size=1,max_working_set_bytes=256*1024*1024)
    frozen=freeze_request(memory_service(records),request)
    reference=float(np.exp(np.mean([np.log(np.sqrt(o.wavelength_min_nm*o.wavelength_max_nm)) for o in frozen.objectives])))
    task=dict(schema='published-material-conditional-pilot-v1',case_id=f'material-{group}-{family}',
        group=group,family=family,split='material_transfer_diagnostic_not_calibration_or_blind_test',synthetic=False,
        search_seed=20261101+FAMILIES.index(family),reference_wavelength_nm=reference,
        source_provenance=provenance,optical_domain_checks=optical_checks,request=asdict(frozen),
        source_note='Published material-specific model/table; unknown substrate k and YbF3 k assumed zero explicitly; known film k preserved. Not process qualification.')
    if family=='bandpass':
        from native_seeds import build_native_seed_bundle
        task['native_seed_bundle']=build_native_seed_bundle(frozen,reference)
    return task
