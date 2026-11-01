"""Headless research adapter to an immutable, published coating-sim revision.

This module does not optimize a design or predict resources. It reconstructs
public request semantics and performs explicitly requested candidate audits.
"""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import subprocess
import sys

CORE_COMMIT = '131d3fc989c3dc9ac8d94fee3c39541a61b851df'


def configure_core(repository):
    repository = Path(repository).resolve()
    actual = subprocess.check_output(['git', '-C', str(repository), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != CORE_COMMIT:
        raise ValueError('research core commit differs from the declared revision')
    if subprocess.check_output(['git', '-C', str(repository), 'status', '--porcelain', '--untracked-files=no'], text=True).strip():
        raise ValueError('research core tracked files must match the declared revision')
    sys.path.insert(0, str(repository))
    return repository


class MaterialRecords:
    def __init__(self, records):
        self.records = {record['id']: deepcopy(record) for record in records}

    def get(self, identifier):
        return deepcopy(self.records[identifier])

    def _records(self):
        return deepcopy(list(self.records.values()))


def memory_service(records):
    from coat_sim.core.film_design import validate_design
    from coat_sim.core.film_design_service import FilmDesignService

    class Service:
        validate = staticmethod(validate_design)
        freeze_design = FilmDesignService.freeze_design

        def __init__(self):
            self.materials = MaterialRecords(records)

    return Service()


def request_from_dict(value, *, validation_samples_multiplier=None):
    from coat_sim.core.film_auto_synthesis import FilmSynthesisRequest
    from coat_sim.core.film_optimization import FilmOptimizationObjective
    from coat_sim.core.film_objective_criteria import FilmObjectiveConstraint
    from coat_sim.core.film_optimization_needle import FilmNeedleMaterialReference
    value = deepcopy(value)
    objectives = []
    for row in value.pop('objectives'):
        for key in ('pointwise', 'mean'):
            if key in row:
                row[key] = FilmObjectiveConstraint(**row[key])
        if 'angles_deg' in row:
            row['angles_deg'] = tuple(row['angles_deg'])
        objectives.append(FilmOptimizationObjective(**row))
    materials = tuple(FilmNeedleMaterialReference(**row) for row in value.pop('candidate_materials'))
    for key in ('selected_surfaces', 'seed_designs', 'growth_quarter_wave_fractions'):
        if key in value:
            value[key] = tuple(value[key])
    if validation_samples_multiplier is not None:
        value['validation_samples_multiplier'] = validation_samples_multiplier
    return FilmSynthesisRequest(objectives=tuple(objectives), candidate_materials=materials, **value)


def freeze_request(service, request):
    from coat_sim.core.film_resource_estimation import FilmResourceEstimateRequest
    from coat_sim.core.film_resource_prediction import freeze_film_prediction_request
    return freeze_film_prediction_request(service, FilmResourceEstimateRequest(request)).synthesis_request


def audit_candidate(service, request, design, *, cancel_event=None):
    from coat_sim.core.film_resource_estimation import FilmResourceEstimateRequest, estimate_film_resources
    result = estimate_film_resources(service, FilmResourceEstimateRequest(
        request, (deepcopy(design),), audit_candidates=True,
        probe_max_evaluations=0, layer_search_limit=0), cancel_event=cancel_event)
    return asdict(result)
