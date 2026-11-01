"""Bounded, unscored native structural priors for R/T/R training diagnostics."""
from copy import deepcopy
from dataclasses import asdict,replace
from itertools import islice
import hashlib
import numpy as np
from artifact_store import canonical_json

PREFIX=256
COUNTS_PER_FAMILY=4


def build_native_seed_bundle(base,reference):
    from coat_sim.core.film_synthesis_global import iter_bandpass_proposals
    from coat_sim.core.film_synthesis_multispectral_priors import iter_multispectral_hr_proposals
    from coat_sim.core.film_synthesis_archive import physical_design_hash
    before=hashlib.sha256(canonical_json(asdict(base))).hexdigest()
    cap=min(32,base.max_layers) if base.max_layers is not None else 32
    thickness_cap=min(2*reference,base.max_layer_thickness_nm) if base.max_layer_thickness_nm is not None else 2*reference
    # Effort limits for construction only. Never replace original audit request.
    generation=replace(base,max_layers=cap,max_layer_thickness_nm=thickness_cap)
    selected=[];details={}
    for family,generator in [('multispectral_hr',iter_multispectral_hr_proposals),('coupled_cavity',iter_bandpass_proposals)]:
        seen=set();counts={}
        for index,proposal in enumerate(islice(generator(generation),PREFIX)):
            design=deepcopy(proposal.design)
            # Layer identifiers and notes do not define the optics, but making
            # these deterministic keeps stored unscored inputs easy to compare.
            for i,layer in enumerate(design['front_layers']):layer['id']=f'native-L{i}'
            identity=physical_design_hash(design)
            if identity in seen:continue
            seen.add(identity);n=len(design['front_layers'])
            counts.setdefault(n,dict(family=family,design=design,physical_design_hash=identity,
                layer_count=n,total_thickness_nm=sum(l['thickness']['value'] for l in design['front_layers']),
                provenance=deepcopy(proposal.provenance),iterator_index=index))
        ordered=sorted(counts)
        indices=sorted(set(int(i) for i in np.linspace(0,len(ordered)-1,min(COUNTS_PER_FAMILY,len(ordered))))) if ordered else []
        chosen=[counts[ordered[i]] for i in indices];selected.extend(chosen)
        details[family]=dict(unique_prefix_candidates=len(seen),distinct_layer_counts=ordered,
            selected_layer_counts=[r['layer_count'] for r in chosen])
    unique={}
    for row in selected:unique.setdefault(row['physical_design_hash'],row)
    selected=sorted(unique.values(),key=lambda r:(r['layer_count'],r['family']!='multispectral_hr',r['physical_design_hash']))
    if not selected:raise ValueError('no native priors within this declared seed effort domain')
    if hashlib.sha256(canonical_json(asdict(base))).hexdigest()!=before:raise ValueError('native constructor changed original request')
    return dict(schema='frozen-native-seed-bundle-v1',original_request_sha256=before,
        prefix_limit_per_family=PREFIX,distinct_counts_per_family=COUNTS_PER_FAMILY,
        selection='first per layer count, up to4 evenly spaced count indices per family; deduplicate and sort by N/family/hash',
        seed_layer_cap=cap,seed_single_layer_cap_nm=thickness_cap,selection_details=details,
        seeds=selected,audited=False,physical_evaluations=0,
        note='Unscored constructions; not feasible witnesses. Preparation cost is separate from the45s repair budget.')
