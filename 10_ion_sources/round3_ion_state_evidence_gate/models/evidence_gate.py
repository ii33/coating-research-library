"""Output-specific evidence gate; file hashes never authenticate physical facts."""
from pathlib import Path
import json,hashlib,math
ROOT=Path(__file__).resolve().parents[1]
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def legacy():return json.loads((ROOT/'data/legacy_binding.json').read_text())

def verify_dependencies():
    rows=json.loads((ROOT/'data/frozen_dependencies.json').read_text())
    for r in rows:
        p=ROOT/r['copy']
        if p.is_symlink() or ROOT not in p.resolve().parents or not p.is_file() or p.stat().st_size!=r['bytes'] or sha(p)!=r['sha256']:
            raise ValueError('copied_dependency_mismatch:'+r['copy'])
    # Reconstruct the original parent contracts rather than trusting duplicated labels.
    c=json.loads((ROOT/'dependencies/t09r3/dependencies/t08r3/dependencies/t07r3/data/case.json').read_text());base=c['inherited_case'];b=c['inherited_binding'];L=legacy()
    fields={'sample_state_id':base['material']['sample_state_id'],'source_contract_sha256':digest(base['bridge']['source_contract']),
            'full_forward_contract_sha256':base['bridge']['t04_response']['upstream_full_forward']['contract_signature'],
            'response_contract_sha256':b['response_contract_sha256'],'bridge_contract_sha256':b['bridge_contract_sha256'],
            'material_contract_sha256':b['material_contract_sha256'],'parent_measurement_contract_sha256':b['measurement_contract_sha256'],
            'optical_operator_sha256':c['derived_observation_contract_sha256'],'recipe_payload_sha256':b['recipe_payload_sha256']}
    if any(L[k]!=v for k,v in fields.items()):raise ValueError('legacy_binding_mismatch')
    return len(rows)

REQUIRED={
 'charged_energy_flow':['corrected_charge_spectrum','surface_equivalence','time_area_support'],
 'history_state':['species_charge','joint_energy_angle','neutral_bound','temperature_history','surface_potential','time_area_support','initial_state','response_coefficients','net_inventory'],
 'process_response':['source_identity','species_charge','joint_energy_angle','neutral_bound','temperature_history','surface_potential','time_area_support','initial_state','net_inventory','film_composition','film_density','film_nk','response_domain','independent_validation','correlation','optical_operator'],
 'new_optical_state':['sample_identity','film_composition','film_density','film_nk','geometric_thickness','correlation','optical_operator','optical_domain','independent_validation'],
 'sample_optical_observation':['sample_identity','optical_operator','raw_observation','measurement_uncertainty']}

def inventory_guard(p):
    """No normalization for net<=0/cross-zero/wide-positive; no silent clipping.
    trajectory_min is a certified bin-envelope LOWER bound, not a sparse sample.
    """
    n=p.get('net_atoms_m2');tr=p.get('inventory_min_atoms_m2')
    if n is None:return 'net_unknown'
    if len(n)!=2 or any(type(x)not in(int,float)or not math.isfinite(x)for x in n)or n[0]>n[1]:raise ValueError('net_interval_invalid')
    lo,hi=n
    if hi<0:return 'net_erosion'
    if lo<=0:return 'zero_or_crossing'
    if hi-lo>=lo:return 'near_zero_or_wide_positive'
    if tr is None:return 'inventory_unknown'
    if not tr or any(type(x)not in(int,float)or not math.isfinite(x)for x in tr.values()):raise ValueError('inventory_lower_invalid')
    if min(tr.values())<=0:return 'inventory_depletion_possible'
    if p.get('inventory_support')!='all_time_bin_envelope':return 'inventory_support_unverified'
    return 'positive_non_depleted_conditional'

def derive_state(p):
    """Fresh contract is a candidate identity, never a measured material database."""
    L=legacy();body={'parent_binding_sha256':digest(L),'parent_state':L['sample_state_id'],
          'data_origin':p['data_origin'],'material_identity':p.get('material_identity','unknown'),
          'exposure_record_sha256':digest(p.get('exposure',{})),
          'evidence_sha256':digest(p.get('evidence',{})),
          'net_inventory_record_sha256':digest({k:p.get(k) for k in ('net_atoms_m2','inventory_min_atoms_m2','inventory_support')}),
          'lineage':'candidate_derived_state_no_physical_identity_certification',
          'nk':None,'film_density_kg_m3':None,'response_model':None,
          'optical_operator':None,'old_nk_reuse':False,'old_density_reuse':False,
          'source_realization':'not_established','formal_review_chain':'pending'}
    return {'state_contract_sha256':digest(body),'state_id':'derived_'+digest(body)[:20],**body}

def decision(status,reason,**kw):
    return {'status':status,'reason':reason,'physical_certification':False,'production_release':False,
            'formal_stage_acceptance':'pending','point12':'partial_unchanged','point2':'conditional_non_strict_unchanged',**kw}

def evaluate(p):
    # Reject nonfinite payloads (JSON encoders otherwise allow NaN by default).
    digest(p)
    if p.get('data_origin')not in ('synthetic','actual'):raise ValueError('origin_required')
    target=p.get('claim');L=legacy()
    if target=='legacy_reuse':
        if p.get('binding')!=L:return decision('blocked_evidence','source_forward_response_operator_binding_changed')
        if p['data_origin']!='synthetic':return decision('blocked_evidence','legacy_constants_are_synthetic_not_actual')
        if p.get('exposure_changed')is not False:return decision('blocked_evidence','changed_or_unknown_ion_state_requires_new_contract',derived_state=derive_state(p))
        if p.get('sample_state_id')!=L['sample_state_id']:return decision('blocked_evidence','state_identity_mismatch')
        return decision('conditional_accept','unchanged_legacy_synthetic_replay_eligible_only',optical_evaluation_performed=False,source_realization='not_established')
    if target not in REQUIRED:return decision('blocked_evidence','unsupported_claim')
    ev=p.get('evidence',{});missing=[];bad=[]
    for k in REQUIRED[target]:
        r=ev.get(k)
        if r is None or r.get('status')=='unknown':missing.append(k);continue
        if r.get('status')not in ('bounded','measured','synthetic_declared')or not r.get('reference') or not r.get('scope'):bad.append(k)
        if p['data_origin']=='actual' and r.get('origin')!='actual':bad.append(k+':synthetic_or_unspecified_as_actual')
        if p['data_origin']=='synthetic' and r.get('origin')!='synthetic':bad.append(k+':origin_mismatch')
    d=derive_state(p) if p.get('exposure_changed')is not False else None
    if bad:return decision('blocked_evidence','invalid_or_mixed_evidence_origin',invalid_evidence=bad,derived_state=d)
    if target in ('history_state','process_response'):
        guard=inventory_guard(p)
        if guard!='positive_non_depleted_conditional':return decision('blocked_evidence',guard,missing_evidence=missing,derived_state=d)
    if missing:return decision('retain_unknown','output_specific_evidence_incomplete',missing_evidence=missing,derived_state=d)
    if target=='charged_energy_flow':
        return decision('conditional_accept','only_corrected_surface_charge_energy_integral',particle_dose=None,total_energy=None,material_state=None)
    if target=='sample_optical_observation':
        return decision('conditional_accept','descriptive_sample_observation_only',process_causality='unknown',process_transfer=False,derived_state=d)
    return decision('conditional_accept','conditional_dossier_ready_for_new_model_review_not_old_operator_reuse',
                    derived_state=d,old_operator_callable=False,actual_model_evaluation=False,
                    required_next_step='build_and_independently_validate_new_state_response_optical_operator',
                    basis='advisory_on_declared_evidence_truth_not_authentication')

def equivalence(bounds,margins):
    """Predeclared hard joint outer bounds on response differences, not p-values.
    Acceptance means those response differences are bounded; not identical latent state.
    """
    if not bounds or set(bounds)!=set(margins):raise ValueError('equivalence_endpoints_required')
    cross=[]
    for k,(lo,hi)in bounds.items():
        m=margins[k]
        if any(type(x)not in(int,float)or not math.isfinite(x) for x in (lo,hi,m))or lo>hi or m<0:raise ValueError('invalid_equivalence_bound')
        if hi < -m or lo>m:return decision('reject_claim','specified_response_not_equivalent',quantity=k)
        if lo < -m or hi>m:cross.append(k)
    return decision('retain_unknown' if cross else 'conditional_accept','equivalence_crossing' if cross else 'specified_response_subspace_only',crossing=cross,latent_state_identity=False,old_nk_reuse=False)
