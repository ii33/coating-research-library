"""New explicit synthetic tasks. This does not reconstruct missing old inputs."""
from copy import deepcopy
from dataclasses import asdict
import numpy as np
from core_bridge import memory_service, freeze_request

FAMILIES=('ar','hr','mixed','bandpass','dual_ar','mean_mix')


def make_task(group, family):
    from coat_sim.core.film_design import new_design
    from coat_sim.core.film_auto_synthesis import FilmSynthesisRequest
    from coat_sim.core.film_optimization import FilmOptimizationObjective as Objective
    from coat_sim.core.film_objective_criteria import FilmObjectiveConstraint as Constraint
    from coat_sim.core.film_optimization_needle import FilmNeedleMaterialReference as Material
    if family not in FAMILIES:
        raise ValueError('unknown task family')
    seed=20261101+13*group
    rng=np.random.default_rng(seed)
    wave=np.geomspace(200.,30000.,161)
    records=[]
    for name,center in zip(('low','high','glass'),(rng.uniform(1.35,1.55),rng.uniform(2.,2.6),rng.uniform(1.45,2.1))):
        dispersion=rng.uniform(.001,.02) if name!='glass' else rng.uniform(.001,.008)
        k=np.zeros(len(wave)) if name=='glass' else np.full(len(wave),np.exp(rng.uniform(np.log(1e-6),np.log(1e-4))))
        if name!='glass' and rng.random()<.25:
            peak=np.exp(rng.uniform(np.log(350.),np.log(12000.)))
            width=rng.uniform(.04,.25)
            amplitude=np.exp(rng.uniform(np.log(1e-5),np.log(1e-3)))
            k+=amplitude*np.exp(-.5*(np.log(wave/peak)/width)**2)
        optical=dict(id='nk',name=name,kind='tabulated',notes='synthetic numerical source, not measured',
            source='replayable resource study 20261101',wavelength_unit='nm',wavelength_min=200.,wavelength_max=30000.,
            wavelengths=wave.tolist(),n=(center+dispersion*((550./wave)**2-1)).tolist(),k=k.tolist())
        records.append(dict(id=name,name=name,design_ready=True,optical_sets=[optical]))
    film_ids=['low','high']
    if rng.integers(2):
        mix=rng.uniform(.3,.7);middle=deepcopy(records[0]);middle['id']='middle';middle['name']='middle'
        middle['optical_sets'][0]['n']=(mix*np.array(records[0]['optical_sets'][0]['n'])+(1-mix)*np.array(records[1]['optical_sets'][0]['n'])).tolist()
        records.append(middle);film_ids.append('middle')
    task_rng=np.random.default_rng(seed*11+FAMILIES.index(family)*131)
    angle=0. if task_rng.random()<.3 else float(task_rng.uniform(10.,50.))
    angles=(angle,) if angle==0. or task_rng.random()<.4 else (angle-5.,angle,angle+5.)
    polarization=str(task_rng.choice(['s','unpolarized','p'],p=[.2,.6,.2]))
    scale=float(task_rng.uniform(.8,1.5));warp=float(task_rng.uniform(.7,1.8))
    def wavelength(value):return 400.*scale*(value/400.)**warp
    def objective(lo,hi,metric,lower=None,upper=None,mean=False):
        factor=float(np.exp(task_rng.uniform(np.log(.4),np.log(2.))))
        lower=None if lower is None else 1-(1-lower)*factor
        upper=None if upper is None else upper*factor
        criterion=Constraint(lower_bound=lower,upper_bound=upper,strict_lower=lower is not None and group%2==0,
            strict_upper=upper is not None and group%2==0)
        return Objective(wavelength(lo),wavelength(hi),17,angles_deg=angles,polarization=polarization,metric=metric,
            pointwise=Constraint(enabled=False) if mean else criterion,mean=criterion if mean else Constraint(enabled=False),
            normalization_scale=max(.001,upper if upper is not None else 1-lower))
    cases={
        'ar':lambda:(objective(450,700,'R',upper=.015),),
        'hr':lambda:(objective(600,800,'R',lower=.95),),
        'mixed':lambda:(objective(500,650,'R',lower=.9),objective(1000,1400,'T',lower=.9)),
        'bandpass':lambda:(objective(420,500,'R',lower=.85),objective(650,750,'T',lower=.85),objective(1000,1200,'R',lower=.85)),
        'dual_ar':lambda:(objective(420,550,'R',upper=.02),objective(1000,1400,'R',upper=.02)),
        'mean_mix':lambda:(objective(450,600,'R',lower=.9,mean=True),objective(1000,1500,'T',lower=.92,mean=True)),
    }
    environment=new_design(design_id=f'synthetic-{group}-{family}')
    environment['name']='Synthetic research task'
    environment['substrate'].update(material_id='glass',optical_set_id='nk')
    service=memory_service(records)
    request=FilmSynthesisRequest(environment,tuple(cases[family]()),tuple(Material(m,'nk') for m in film_ids),
        validation_samples_multiplier=32,max_cycles=4,max_evaluations=300,search_strategy='legacy',
        cpu_workers=1,parallel_batch_size=1,max_working_set_bytes=256*1024*1024)
    frozen=freeze_request(service,request)
    reference=float(np.exp(np.mean([np.log(np.sqrt(o.wavelength_min_nm*o.wavelength_max_nm)) for o in frozen.objectives])))
    return dict(schema='replayable-synthetic-task-v1',case_id=f'train-{group}-{family}',group=group,family=family,
        split='new_training_pilot_not_calibration_or_test',seed=seed,synthetic=True,reference_wavelength_nm=reference,
        request=asdict(frozen),source_note='Numeric synthetic curves; not measured materials or a process qualification')
