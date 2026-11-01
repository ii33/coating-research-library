"""Offline deterministic local search with immediate durable audited witnesses.

A finite reference procedure, NOT a minimum-resource oracle or online predictor.
Only the declared single-front/air/synthetic-table task family is supported here.
"""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import re
from pathlib import Path
import time
import numpy as np
from scipy.optimize import least_squares
from artifact_store import canonical_json,write_immutable_json,_target
from core_bridge import memory_service,request_from_dict,audit_candidate

PROFILE=dict(schema='local-reference-profile-v2',layer_counts=[0,2,4,8,12,16,24,32],starts=3,
    fit_samples=41,max_nfev=60,case_seconds=45.,reduction_rounds=2,reduction_proposals=2,
    normalized_thickness_bounds=[1e-7,2.],criterion_margin_fraction=.03,
    selection='log1p(N)+log1p(D/lambda_ref); ties N,D,physical hash',
    search_seed_policy='integer from first16hex SHA256(case_id)',
    initialization='frozen native R/T/R seeds when supplied; otherwise unchanged baseline recipe',
    native_seed_limit=8,
    numerical_limits='Search counts, thickness box and time are effort limits, not physical impossibility bounds')


class BudgetStop(RuntimeError):
    pass


class Control:
    def __init__(self,seconds):self.started=time.monotonic();self.seconds=seconds
    def is_set(self):return time.monotonic()-self.started>=self.seconds
    def check(self):
        if self.is_set():raise BudgetStop('declared offline case budget exhausted')


def select_witness(witnesses,reference):
    if not np.isfinite(reference) or reference<=0:raise ValueError('invalid reference wavelength')
    def score(w):
        n=w['layer_count'];d=w['total_thickness_nm']
        if not np.isfinite(n) or not np.isfinite(d) or isinstance(n,bool) or int(n)!=n or n<0 or d<0 or ((n==0)!=(d==0)):raise ValueError('inconsistent paired resources')
        return np.log1p(n)+np.log1p(d/reference),n,d,w['physical_design_hash']
    return min(witnesses,key=score) if witnesses else None


def design_from_thickness(base,names,x,reference):
    if len(names)!=len(x) or np.ndim(x)!=1 or not np.all(np.isfinite(x)) or np.any(np.asarray(x)<0):
        raise ValueError('invalid thickness vector')
    design=deepcopy(base.environment)
    design['front_layers']=[dict(id=f'L{j}',material_id=key[0],optical_set_id=key[1],
        thickness=dict(value=float(value*reference),unit='nm'),note='offline reference candidate')
        for j,(key,value) in enumerate(reversed(list(zip(names,x))))]
    return design


def delete_and_merge(design,index):
    design=deepcopy(design);design['front_layers'].pop(index);merged=[]
    for layer in design['front_layers']:
        if layer['thickness']['unit']!='nm':raise ValueError('requires physical nm thickness')
        if merged and (merged[-1]['material_id'],merged[-1]['optical_set_id'])==(layer['material_id'],layer['optical_set_id']):
            merged[-1]['thickness']['value']+=layer['thickness']['value']
        else:merged.append(layer)
    for j,layer in enumerate(merged):layer['id']=f'L{j}';layer['note']='offline reference candidate'
    design['front_layers']=merged
    return design


def solve(task,root):
    from coat_sim.core.optical_constants import prepare_optical_set
    from coat_sim.core.film_synthesis_absorption import sample_synthesis_optical
    from coat_sim.core.film_optics import coherent_rta
    from coat_sim.core.film_optimization_derivatives import _analytic_one_polarization
    from coat_sim.core.film_objective_criteria import reduce_objective_responses
    from coat_sim.core.film_synthesis_archive import physical_design_hash
    root=Path(root);case_id=task['case_id']
    if not isinstance(case_id,str) or not re.fullmatch(r'[A-Za-z0-9_-]+',case_id):raise ValueError('invalid case identity')
    case_root=_target(root,f'cases/{case_id}')
    result_path=_target(root,f'cases/{case_id}/result.json')
    task_hash=hashlib.sha256(canonical_json(task)).hexdigest()
    def check_witness(w, identity):
        if not isinstance(identity,str) or not re.fullmatch('[0-9a-f]{64}',identity):raise ValueError('invalid witness identity')
        if w.get('physical_design_hash')!=identity:raise ValueError('witness filename and physical hash differ')
        if w['request_sha256']!=task_hash:raise ValueError('resumed witness belongs to different input')
        if physical_design_hash(w['design'])!=w['physical_design_hash']:raise ValueError('resumed design hash mismatch')
        audit=w.get('audit',{});reports=audit.get('candidate_reports',[])
        if len(reports)!=1 or reports[0].get('state')!='audited' or not all(reports[0].get(key) is True for key in ('targets_met','solver_acceptable','within_constraints','within_material_pool')):
            raise ValueError('resumed witness lacks successful original audit')
        row=reports[0]
        if audit.get('pareto_witnesses')!=reports or not isinstance(row.get('audit'),dict) or not row['audit']:
            raise ValueError('resumed witness lacks full audit evidence')
        if physical_design_hash(row.get('candidate_design'))!=identity:
            raise ValueError('audited candidate differs from witness design')
        if type(row.get('layer_count')) is not int or isinstance(row.get('total_thickness_nm'),bool) or not isinstance(row.get('total_thickness_nm'),(int,float)):
            raise ValueError('invalid audited resource types')
        if row['physical_hash']!=w['physical_design_hash'] or row['layer_count']!=w['layer_count'] or row['total_thickness_nm']!=w['total_thickness_nm']:
            raise ValueError('resumed witness resource pair differs from its audit')
        if len(w['design']['front_layers'])!=w['layer_count'] or not np.isclose(sum(l['thickness']['value'] for l in w['design']['front_layers']),w['total_thickness_nm'],rtol=0,atol=1e-8):
            raise ValueError('resumed witness resources differ from its design')
        select_witness([w],task['reference_wavelength_nm'])
    def witness_inventory():
        directory=_target(root,f'cases/{case_id}/witnesses')
        if not directory.exists():return {}
        if not directory.is_dir():raise ValueError('witness directory is not a directory')
        found={}
        for path in sorted(directory.iterdir()):
            if not path.is_file() or path.is_symlink() or not re.fullmatch(r'[0-9a-f]{64}\.json',path.name):
                raise ValueError('invalid witness filename')
            identity=path.stem
            w=json.loads(_target(root,f'cases/{case_id}/witnesses/{identity}.json').read_text())
            check_witness(w,identity);found[identity]=w
        return found
    if result_path.exists():
        previous=json.loads(result_path.read_text())
        if previous.get('case_id')!=case_id or previous.get('request_sha256')!=task_hash:
            raise ValueError('completed result belongs to different input')
        required={'schema','case_id','request_sha256','state','estimate_state','profile','selected_hash','layer_count','total_thickness_nm','retained_witness_hashes'}
        if not required<=set(previous):raise ValueError('completed result is missing required fields')
        if previous.get('schema')!='offline-reference-result-v1' or previous.get('profile')!=PROFILE or previous.get('state') not in ('completed','declared_budget_stopped'):
            raise ValueError('invalid completed result metadata')
        retained=previous.get('retained_witness_hashes')
        if not isinstance(retained,list) or any(not isinstance(h,str) or not re.fullmatch('[0-9a-f]{64}',h) for h in retained) or retained!=sorted(set(retained)):
            raise ValueError('invalid retained witness identities')
        found=witness_inventory()
        if set(retained)!=set(found):raise ValueError('retained witness inventory mismatch')
        selected=select_witness(list(found.values()),task['reference_wavelength_nm'])
        expected_hash=None if selected is None else selected['physical_design_hash']
        expected_state='unknown_not_infeasible' if selected is None else 'audited_reference'
        expected_n=None if selected is None else selected['layer_count']
        expected_d=None if selected is None else selected['total_thickness_nm']
        if selected is not None and (type(previous.get('layer_count')) is not int or isinstance(previous.get('total_thickness_nm'),bool) or not isinstance(previous.get('total_thickness_nm'),(int,float))):
            raise ValueError('invalid completed resource types')
        if (previous.get('selected_hash')!=expected_hash or previous.get('estimate_state')!=expected_state or
                previous.get('layer_count')!=expected_n or previous.get('total_thickness_nm')!=expected_d):
            raise ValueError('completed result selection or label differs from retained witnesses')
        return previous
    write_immutable_json(root,f'cases/{case_id}/input.json',task)
    base=request_from_dict(task['request']);reference=task['reference_wavelength_nm']
    if (base.selected_surfaces!=('front',) or base.environment['back_layers'] or
        base.minimum_nonzero_thickness_nm not in (None,0) or base.max_layer_thickness_nm is not None or
        base.environment['incident_medium']!={'kind':'constant','n':1.0}):
        raise ValueError('outside this declared offline reference profile')
    service=memory_service(base.frozen_material_snapshot['materials'])
    samplers={(m['id'],o['id']):prepare_optical_set(o,k_sampling_policy='source')
        for m in base.frozen_material_snapshot['materials'] for o in m['optical_sets']}
    def sample(key,wavelength):return complex(*sample_synthesis_optical(samplers[key],float(wavelength),assume_unknown_k_zero=False)[:2])
    sub=base.environment['substrate'];substrate=(sub['material_id'],sub['optical_set_id'])
    pool=[(r.material_id,r.optical_set_id) for r in base.candidate_materials]
    witnesses=list(witness_inventory().values())
    seen={w['physical_design_hash'] for w in witnesses};trials=[];control=Control(PROFILE['case_seconds'])
    def retain(design):
        identity=physical_design_hash(design)
        if identity in seen:return True
        control.check()
        audit=audit_candidate(service,base,design,cancel_event=control)
        if not audit['pareto_witnesses']:return False
        row=audit['candidate_reports'][0]
        if not all(row[key] for key in ('targets_met','solver_acceptable','within_constraints','within_material_pool')):
            raise ValueError('audited candidate has inconsistent pass flags')
        if row['physical_hash']!=identity:raise ValueError('audit identity mismatch')
        w=dict(schema='full-audited-witness-v1',request_sha256=task_hash,physical_design_hash=identity,
            layer_count=row['layer_count'],total_thickness_nm=row['total_thickness_nm'],design=design,audit=audit)
        # Commit immediately, before another solver/audit call or budget check.
        write_immutable_json(root,f'cases/{case_id}/witnesses/{identity}.json',w)
        witnesses.append(w);seen.add(identity)
        return True
    originals=tuple(replace(o,wavelength_samples=PROFILE['fit_samples']) for o in base.objectives)
    def margin(c):
        if not c.enabled:return c
        f=PROFILE['criterion_margin_fraction']
        return replace(c,lower_bound=None if c.lower_bound is None else c.lower_bound+f*(1-c.lower_bound),
            upper_bound=None if c.upper_bound is None else c.upper_bound*(1-f))
    margins=tuple(replace(o,pointwise=margin(o.pointwise),mean=margin(o.mean)) for o in originals)
    waves=[np.linspace(o.wavelength_min_nm,o.wavelength_max_nm,PROFILE['fit_samples']) for o in originals]
    spectra=[{key:np.array([sample(key,w) for w in grid]) for key in pool+[substrate]} for grid in waves]
    def repair(seed,label):
        control.check();layers=list(reversed(seed['front_layers']));names=[(l['material_id'],l['optical_set_id']) for l in layers]
        x=np.array([l['thickness']['value']/reference for l in layers]);n=len(names);ids=[str(i) for i in range(n)];columns={s:i for i,s in enumerate(ids)}
        optics=[np.column_stack([np.ones(len(w)),*[row[key] for key in names],row[substrate]]) for w,row in zip(waves,spectra)]
        def calculate(z,targets):
            control.check();frames=[]
            for oi,o in enumerate(targets):
                for angle in o.angles_deg:
                    values=[];jacobians=[]
                    for pol in (('s','p') if o.polarization=='unpolarized' else (o.polarization,)):
                        response=coherent_rta(waves[oi]/reference,optics[oi],z,angle_deg=angle,polarization=pol)
                        values.append(np.array(response[o.metric]))
                        if n:
                            jr,jt=_analytic_one_polarization(waves[oi]/reference,optics[oi],z,ids,columns,angle,pol)
                            jacobians.append(jr if o.metric=='R' else jt)
                    v=np.mean(values,axis=0);jac=np.mean(jacobians,axis=0) if n else np.zeros((len(waves[oi]),0))
                    frames.append(dict(objective_index=oi,angle_deg=angle,wavelength_nm=waves[oi],actual_values=v,
                        jacobian_values_by_layer_id={s:jac[:,i] for i,s in enumerate(ids)}))
            return reduce_objective_responses(targets,frames,layer_ids=ids)
        initial=calculate(x,originals)
        if initial.nominal_pass:retain(seed)
        if n:
            lower,upper=PROFILE['normalized_thickness_bounds'];x=np.clip(x,lower,upper);cache=[None,None]
            def cached(z):
                if cache[0] is None or not np.array_equal(z,cache[0]):cache[:]=[z.copy(),calculate(z,margins)]
                return cache[1]
            fit=least_squares(lambda z:cached(z).residual_vector,x,jac=lambda z:cached(z).jacobian_matrix,
                bounds=(lower,upper),max_nfev=PROFILE['max_nfev'],ftol=1e-9,xtol=1e-9,gtol=1e-9)
            x=fit.x
        nominal=calculate(x,originals);design=design_from_thickness(base,names,x,reference)
        passed=retain(design) if nominal.nominal_pass else False
        trials.append(dict(label=label,layer_count=n,local_nominal_pass=bool(nominal.nominal_pass),
            local_max_error=float(nominal.max_error),audited_witness_available=passed,candidate_design=design))
        return passed
    reflect=[o for o in base.objectives if o.metric=='R' and any(c.enabled and c.lower_bound is not None and c.lower_bound>.5 for c in (o.pointwise,o.mean))]
    passing=[o for o in base.objectives if o.metric=='T' and any(c.enabled and c.lower_bound is not None and c.lower_bound>.5 for c in (o.pointwise,o.mean))]
    reflect_center=float(np.exp(np.mean([np.log(np.sqrt(o.wavelength_min_nm*o.wavelength_max_nm)) for o in reflect]))) if reflect else reference
    pass_center=float(np.exp(np.mean([np.log(np.sqrt(o.wavelength_min_nm*o.wavelength_max_nm)) for o in passing]))) if passing else reference
    lo=min(pool,key=lambda key:sample(key,reflect_center).real);hi=max(pool,key=lambda key:sample(key,reflect_center).real)
    angle=float(np.mean([a for o in base.objectives for a in o.angles_deg]));beta=np.sin(np.deg2rad(angle))
    search_rng=np.random.default_rng(int(hashlib.sha256(case_id.encode()).hexdigest()[:16],16))
    def seeds(n):
        if n==0:return [design_from_thickness(base,[],np.array([]),reference)]
        output=[]
        for start in range(PROFILE['starts']):
            names=([hi,lo]*n)[:n] if start==0 else ([lo]+([hi,lo]*n)[:n-1])
            if start==2:
                names=[]
                for _ in range(n):
                    choices=[key for key in pool if not names or key!=names[-1]]
                    names.append(choices[int(search_rng.integers(len(choices)))])
            centers=np.full(n,reflect_center if reflect else reference)
            if start==1 and reflect and passing:centers[0]=pass_center
            if start==1 and reflect and not passing:
                centers=np.geomspace(min(o.wavelength_min_nm for o in reflect),max(o.wavelength_max_nm for o in reflect),n)
            fraction=.25 if reflect else (.12 if start==0 else .06)
            x=np.array([fraction*w/max(1e-6,np.sqrt(max(sample(key,w).real**2-beta**2,1e-12)))/reference for key,w in zip(names,centers)])
            if start==2:x*=search_rng.uniform(.6,1.4,size=n)
            output.append(design_from_thickness(base,names,x,reference))
        return output
    state='completed';passed_counts=0
    try:
        bundle=task.get('native_seed_bundle')
        if bundle is not None:
            if bundle.get('audited') is not False or bundle.get('original_request_sha256')!=hashlib.sha256(canonical_json(task['request'])).hexdigest():
                raise ValueError('native seeds are not bound to the original unmodified request')
            rows=bundle['seeds']
            if len(rows)>PROFILE['native_seed_limit']:raise ValueError('native seed quota exceeded')
            bycount={0:[design_from_thickness(base,[],np.array([]),reference)]}
            for row in rows:
                seed=row['design'];n=len(seed['front_layers'])
                if n>32 or n!=row['layer_count'] or physical_design_hash(seed)!=row['physical_design_hash']:
                    raise ValueError('native seed identity or effort cap mismatch')
                if any(l['thickness']['unit']!='nm' or not np.isfinite(l['thickness']['value']) or not 0<l['thickness']['value']<=2*reference for l in seed['front_layers']):
                    raise ValueError('native seed outside normalized thickness effort box')
                bycount.setdefault(n,[]).append(seed)
        else:
            bycount={n:None for n in PROFILE['layer_counts']}
        for n,provided in sorted(bycount.items()):
            passed=False
            starts=seeds(n) if provided is None else provided
            for i,seed in enumerate(starts):passed=repair(seed,f'count-{n}-start-{i}') or passed
            if passed:
                passed_counts+=1
                if n==0 or passed_counts>=2:break
        for turn in range(PROFILE['reduction_rounds']):
            best=select_witness(witnesses,reference)
            if best is None or best['layer_count']<=1:break
            design=best['design']
            order=sorted(range(len(design['front_layers'])),key=lambda i:sample((design['front_layers'][i]['material_id'],design['front_layers'][i]['optical_set_id']),reference).real*design['front_layers'][i]['thickness']['value'])
            proposals=[];identities=set()
            for i in order:
                candidate=delete_and_merge(design,i);identity=physical_design_hash(candidate)
                if identity not in identities:proposals.append(candidate);identities.add(identity)
                if len(proposals)>=PROFILE['reduction_proposals']:break
            before=best['physical_design_hash']
            for i,seed in enumerate(proposals):repair(seed,f'reduction-{turn}-proposal-{i}')
            if select_witness(witnesses,reference)['physical_design_hash']==before:break
    except BudgetStop:
        state='declared_budget_stopped'
    if control.is_set():state='declared_budget_stopped'
    selected=select_witness(witnesses,reference)
    result=dict(schema='offline-reference-result-v1',case_id=case_id,request_sha256=task_hash,
        state=state,estimate_state='audited_reference' if selected else 'unknown_not_infeasible',
        profile=PROFILE,selected_hash=None if selected is None else selected['physical_design_hash'],
        layer_count=None if selected is None else selected['layer_count'],
        total_thickness_nm=None if selected is None else selected['total_thickness_nm'],
        retained_witness_hashes=sorted(seen),trials=trials,elapsed_seconds=time.monotonic()-control.started,
        limits='Finite-budget audited design resources, not physical minimum or a continuous certificate')
    write_immutable_json(root,f'cases/{case_id}/result.json',result)
    return result
