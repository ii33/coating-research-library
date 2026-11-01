"""Bounded feature extraction only: no stack simulation, optimization or audit."""
from copy import deepcopy
import json,math
import numpy as np
from coat_sim.core.optical_constants import prepare_optical_set
from coat_sim.core.film_synthesis_absorption import sample_synthesis_optical

SCHEMA='resource-features-v1'
MAX_OBJECTIVES=3
MAX_MATERIALS=3
MAX_ANGLES=9
SAMPLES=9


def extract_features(request):
    r=deepcopy(request);env=r['environment'];objectives=r['objectives'];refs=r['candidate_materials']
    if r.get('selected_surfaces') not in (['front'],('front',)) or env.get('back_layers') or env.get('front_layers'):
        raise ValueError('only empty single-front design resource requests supported')
    if env.get('incident_medium')!={'kind':'constant','n':1.0} or env['substrate'].get('sides')!='single':
        raise ValueError('only air and single-sided substrate reference supported')
    if env.get('use_k',True) is not True:raise ValueError('known absorption cannot be disabled')
    if (env.get('layer_order')!='substrate_outward' or env.get('first_surface')!='front' or env.get('exit_medium')!={'kind':'constant','n':1.0}
            or env['substrate'].get('mode')!='auto'
            or env['substrate'].get('thickness')!={'unit':'mm','value':1.0}):
        raise ValueError('substrate/exit geometry outside the frozen reference domain')
    fixed_reference=dict(max_cycles=4,max_evaluations=300,max_seconds=None,
        validation_samples_multiplier=32,search_strategy='legacy',
        seed_designs=[],search_checkpoint=None,warm_start_seed_index=None)
    for key,expected in fixed_reference.items():
        if r.get(key)!=expected:raise ValueError('reference-flow field outside frozen domain: '+key)
    if any(r.get(k) is not None for k in ('max_layers','max_layer_thickness_nm','max_total_thickness_nm')) or r.get('minimum_nonzero_thickness_nm') not in (None,0):
        raise ValueError('manufacturing/resource-constrained references not calibrated')
    acceptance=r.get('acceptable_normalized_error',0)
    if type(acceptance) not in (int,float) or not math.isfinite(acceptance) or not 0<=acceptance<=1:raise ValueError('invalid normalized acceptance tolerance')
    if not 1<=len(objectives)<=MAX_OBJECTIVES or not 2<=len(refs)<=MAX_MATERIALS:raise ValueError('unsupported objective/material count')
    assume=env.get('assume_lossless',False)
    if type(assume) is not bool:raise ValueError('explicit boolean missing-k policy required')
    def semantic_key(o):
        value={key:o[key] for key in ('wavelength_min_nm','wavelength_max_nm','metric',
            'polarization','normalization_scale','weight','wavelength_samples')}
        value['angles_deg']=sorted(o['angles_deg'])
        for kind in ('pointwise','mean'):
            c=o[kind]
            value[kind]=({key:c[key] for key in ('enabled','mode','lower_bound','upper_bound',
                'strict_lower','strict_upper')} if c['enabled'] else {'enabled':False})
        return (o['wavelength_min_nm'],o['wavelength_max_nm'],o['metric'],json.dumps(value,sort_keys=True))
    objectives=sorted(objectives,key=semantic_key)
    for o in objectives:
        if o['wavelength_samples']!=17:raise ValueError('reference objective sample count must be17')
        lo,hi=o['wavelength_min_nm'],o['wavelength_max_nm']
        if not 0<lo<hi or o['metric'] not in ('R','T') or o['polarization'] not in ('s','p','unpolarized'):raise ValueError('unsupported objective')
        aa=o['angles_deg']
        if not 1<=len(aa)<=MAX_ANGLES or len(set(aa))!=len(aa) or any(not 0<=a<90 for a in aa):raise ValueError('unsupported angle grid')
        if o['normalization_scale']<=0 or o['weight']<=0:raise ValueError('positive objective scale/weight required')
        for c in (o['pointwise'],o['mean']):
            if type(c['enabled']) is not bool or c['mode']!='range':raise ValueError('only explicit range criterion supported')
            for b in ('lower_bound','upper_bound'):
                if c[b] is not None and not 0<=c[b]<=1:raise ValueError('invalid optical bound')
            if c['lower_bound'] is not None and c['upper_bound'] is not None and c['lower_bound']>c['upper_bound']:raise ValueError('inverted bound')
        if not any(c['enabled'] for c in (o['pointwise'],o['mean'])):raise ValueError('inactive objective')
    reference=math.exp(np.mean([math.log(math.sqrt(o['wavelength_min_nm']*o['wavelength_max_nm'])) for o in objectives]))
    optics={(m['id'],s['id']):s for m in r['frozen_material_snapshot']['materials'] for s in m['optical_sets']}
    def optical_features(ref):
        optical=optics[ref['material_id'],ref['optical_set_id']]
        sampler=prepare_optical_set(optical,k_sampling_policy='source');rows=[];sort_values=[];unknown=False
        for o in objectives:
            ns=[];ks=[];missing=[]
            for wave in np.linspace(o['wavelength_min_nm'],o['wavelength_max_nm'],SAMPLES):
                n,k,d=sample_synthesis_optical(sampler,float(wave),assume_unknown_k_zero=assume)
                ns.append(n);ks.append(k);missing.append(not bool(d.get('k_known')))
            unknown|=any(missing);sort_values.extend(ns+ks)
            rows.append([float(np.mean(ns)),min(ns),max(ns),ns[-1]-ns[0],float(np.std(ns)),
                math.log1p(1000*float(np.mean(ks))),math.log1p(1000*max(ks)),float(any(missing))])
        return rows,tuple(sort_values),unknown
    films=sorted([optical_features(ref) for ref in refs],key=lambda x:x[1])
    substrate=optical_features(env['substrate'])
    conditional=substrate[2] or any(f[2] for f in films)
    values=[];names=[]
    def put(name,value):
        value=float(value)
        if not math.isfinite(value):raise ValueError('nonfinite feature')
        names.append(name);values.append(value)
    put('log_reference_nm_over_550',math.log(reference/550));put('objective_count',len(objectives));put('film_count',len(films))
    put('acceptable_normalized_error',acceptance);put('missing_k_policy',assume);put('conditional_missing_k',conditional)
    for j in range(MAX_OBJECTIVES):
        o=objectives[j] if j<len(objectives) else None;prefix=f'objective_{j}_'
        put(prefix+'present',o is not None)
        for key in ('lo','hi'):
            put(prefix+key+'_log_relative',math.log(o['wavelength_min_nm' if key=='lo' else 'wavelength_max_nm']/reference) if o else 0)
        for metric in ('R','T'):put(prefix+metric,bool(o and o['metric']==metric))
        for pol in ('s','p','unpolarized'):put(prefix+pol,bool(o and o['polarization']==pol))
        put(prefix+'log_normalization',math.log(o['normalization_scale']) if o else 0)
        put(prefix+'log_weight',math.log(o['weight']) if o else 0)
        angles=sorted(o['angles_deg']) if o else []
        put(prefix+'angle_count',len(angles))
        for i in range(MAX_ANGLES):put(prefix+f'angle_{i}_sin',math.sin(math.radians(angles[i])) if i<len(angles) else 0)
        for kind in ('pointwise','mean'):
            c=o[kind] if o else None;enabled=bool(c and c['enabled']);put(prefix+kind+'_enabled',enabled)
            for direction in ('lower','upper'):
                bound=c[direction+'_bound'] if enabled else None
                put(prefix+kind+'_'+direction+'_present',bound is not None)
                put(prefix+kind+'_'+direction+'_value',bound if bound is not None else 0)
                put(prefix+kind+'_'+direction+'_strict',bool(enabled and c['strict_'+direction]))
    for i in range(MAX_MATERIALS+1):
        role='substrate' if i==MAX_MATERIALS else f'film_{i}'
        f=substrate if i==MAX_MATERIALS else (films[i] if i<len(films) else None)
        put(role+'_present',f is not None)
        for j in range(MAX_OBJECTIVES):
            row=f[0][j] if f and j<len(objectives) else [0]*8
            for key,value in zip(('n_mean','n_min','n_max','n_delta','n_std','log_k_mean','log_k_max','missing_k'),row):put(f'{role}_objective_{j}_{key}',value)
    return dict(schema=SCHEMA,names=names,values=values,reference_wavelength_nm=reference,conditional_on_unknown_k=bool(conditional),
        caveat='Nine fixed source samples per window; narrow spectral behavior may be missed. No optical design generated.')
