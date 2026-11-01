"""Additional synthetic material groups; matched visible objectives, not measured sources."""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import hashlib
import json
import numpy as np
from artifact_store import canonical_json
from core_bridge import memory_service, freeze_request, CORE_COMMIT

GROUPS=tuple(f'sim_{i}' for i in range(51000,51008))
FAMILIES=('ar','hr','mixed','bandpass','dual_ar','mean_mix')


def source_records(group):
    if group not in GROUPS:raise ValueError('undeclared simulated material group')
    number=int(group.split('_')[1]);seed=20261101+137*number
    rng=np.random.default_rng(seed);wave=np.linspace(400.,800.,201)
    centers=[float(rng.uniform(1.35,1.6)),float(rng.uniform(1.9,2.7)),float(rng.uniform(1.45,2.5))]
    dispersions=[float(rng.uniform(.001,.025)),float(rng.uniform(.003,.05)),float(rng.uniform(.001,.012))]
    records=[];provenance=[]
    generator_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    for index,(alias,center,dispersion) in enumerate(zip(('low','high','glass'),centers,dispersions)):
        n=center+dispersion*((550./wave)**2-1.)
        missing=index==2 or (index==0 and number%5==0)
        base=float(np.exp(rng.uniform(np.log(1e-6),np.log(.015))))
        power=float(rng.uniform(-1.,1.))
        k=base*(wave/550.)**power
        zeroed=bool(rng.random()<.25)
        if zeroed:k=np.zeros(len(wave))
        peak=None
        if not missing and rng.random()<.3:
            peak=dict(center_nm=float(rng.uniform(450.,750.)),width_nm=float(rng.uniform(20.,120.)),
                amplitude=float(np.exp(rng.uniform(np.log(1e-5),np.log(.01)))))
            k+=peak['amplitude']*np.exp(-.5*((wave-peak['center_nm'])/peak['width_nm'])**2)
        optical=dict(id='nk',name='Explicit simulated optical curve',kind='tabulated',
            wavelength_unit='nm',wavelength_min=400.,wavelength_max=800.,wavelengths=wave.tolist(),
            n=n.tolist(),k=None if missing else k.tolist(),
            source='Project numerical material-transfer experiment 20261101; not a measured dataset',
            notes='Independent n/k parameterization over a finite visible interval; passive table values do not certify global causal dispersion or manufacturability. Missing k is explicit and used only under a zero-k assumption.')
        records.append(dict(id=alias,name=f'{group} simulated {alias}',design_ready=True,optical_sets=[optical]))
        provenance.append(dict(alias=alias,material_id=alias,optical_set_id='nk',core_commit=CORE_COMMIT,
            generator='tasks.py:source_records',generator_sha256=generator_hash,group_seed=seed,
            optical_group_sha256=hashlib.sha256(canonical_json(optical)).hexdigest(),unknown_k=missing,
            parameters=dict(n_at_550_nm=center,cauchy_like_dispersion=dispersion,
                extinction_base=base,extinction_power=power,base_curve_zeroed=zeroed,extinction_peak=peak,
                used_extinction='missing_assumed_zero' if missing else 'exact_stored_table'),
            limitation='Synthetic source, not measurement, process calibration or blind validation'))
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
    environment['name']='Synthetic material-transfer training expansion'
    environment['assume_lossless']=True  # Only missing k; never overwrites known extinction.
    substrate=records[2];environment['substrate'].update(material_id=substrate['id'],optical_set_id=substrate['optical_sets'][0]['id'])
    request=FilmSynthesisRequest(environment,objectives,
        tuple(Material(r['id'],r['optical_sets'][0]['id']) for r in records[:2]),
        validation_samples_multiplier=32,max_cycles=4,max_evaluations=300,search_strategy='legacy',
        cpu_workers=1,parallel_batch_size=1,max_working_set_bytes=256*1024*1024)
    frozen=freeze_request(memory_service(records),request)
    reference=float(np.exp(np.mean([np.log(np.sqrt(o.wavelength_min_nm*o.wavelength_max_nm)) for o in frozen.objectives])))
    task=dict(schema='synthetic-material-transfer-expansion-v1',case_id=f'material-{group}-{family}',
        group=group,family=family,split='posthoc_training_expansion_not_calibration_or_blind_test',synthetic=True,
        search_seed=20261101+FAMILIES.index(family),reference_wavelength_nm=reference,
        source_provenance=provenance,optical_domain_checks=optical_checks,request=asdict(frozen),
        source_note='All curves are simulated, not measured. Missing substrate and occasional low-film k explicitly assumed zero; known synthetic absorption retained. Same target geometry as prior material diagnostic; previously inspected published-model/table-source cases remain held out for subsequent transfer comparison.')
    if family=='bandpass':
        from native_seeds import build_native_seed_bundle
        task['native_seed_bundle']=build_native_seed_bundle(frozen,reference)
    return task
