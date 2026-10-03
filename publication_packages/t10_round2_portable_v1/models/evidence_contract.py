"""Traceable observation packet validation. Structure is not technical approval."""
from pathlib import Path
import hashlib
import json
import math
import jsonschema
from ion_observables import Cell, moments
ROOT=Path(__file__).resolve().parents[1]

def validate_packet(packet, raw_root=None):
    def nonfinite(value):
        if isinstance(value, float): return not math.isfinite(value)
        if isinstance(value, dict): return any(nonfinite(v) for v in value.values())
        if isinstance(value, list): return any(nonfinite(v) for v in value)
        return False
    if nonfinite(packet):
        return {'status':'blocked_structure','errors':[{'code':'NONFINITE','detail':'NaN and infinity are not permitted JSON measurements'}],'actual_validation':'not_run_awaiting_device'}
    schema=json.loads((ROOT/'contracts/observation_packet.schema.json').read_text())
    errors=[{'code':'SCHEMA','detail':e.message,'path':'/'.join(map(str,e.path))} for e in jsonschema.Draft202012Validator(schema).iter_errors(packet)]
    if errors: return {'status':'blocked_structure','errors':errors,'actual_validation':'not_run_awaiting_device'}
    def block(code,detail): errors.append({'code':code,'detail':detail})
    actual=packet['data_origin']=='actual'
    evid={r['id']:r for r in packet['evidence']}
    if len(evid)!=len(packet['evidence']): block('DUPLICATE_EVIDENCE','Evidence IDs must be unique')
    for requirement in ('instrument_identity','electrical_current_correction','area_normalization','energy_angle_response','species_charge_state','surface_representativeness','time_alignment','neutral_coverage','material_identity','film_state','optical_operator','traceability','raw_data'):
        ref=packet['requirements'][requirement]
        if ref is None: block('MISSING_'+requirement.upper(), 'Required evidence reference is missing')
        elif ref not in evid: block('BROKEN_REFERENCE',ref)
        elif actual and evid[ref]['status'] not in {'checked','approved'}: block('UNCHECKED_'+requirement.upper(),ref)
        elif actual and evid[ref]['basis']=='synthetic': block('SYNTHETIC_AS_ACTUAL',ref)
    if actual and packet['reading_origin'] not in {'measured','derived_from_measured'}:
        block('NOT_INDEPENDENT_OBSERVATION','Substituted, held, unknown or synthetic values cannot validate actual response')
    if not actual and packet['reading_origin']!='synthetic': block('ORIGIN_MISMATCH','Synthetic fixture must be labelled synthetic')
    if packet['observable_kind']!='local_joint_spectrum':
        block('WRONG_OBSERVABLE','Source setpoints or charge-only spectra cannot populate a species/angle-resolved flux packet')
    if packet['normalization']!='cell_integrated_per_actual_surface_area': block('AREA_OR_CELL_NORMALIZATION','No implicit cos or solid-angle correction allowed')
    if packet['neutral_coverage']=='unknown': block('NEUTRALS_UNKNOWN','Total kinetic energy and epsilon cannot be claimed; observed components remain reportable')
    if packet['source_identity']['family'] not in {'dc_kaufman_gridded','other_declared','unknown'}: block('SOURCE_FAMILY','Unknown source family')
    if actual and any(packet['source_identity'][x] is None for x in ['manufacturer','model','firmware','configuration_id']): block('SOURCE_IDENTITY_INCOMPLETE','Actual configuration identity missing')
    if actual and packet['source_identity']['family']=='unknown': block('SOURCE_FAMILY_UNKNOWN','No default Kaufman inference')
    if packet['film_state']['density_basis']=='bulk': block('BULK_IS_NOT_FILM','Bulk density cannot substitute measured effective film density')
    if packet['film_state']['net_inventory_basis']!='independent_element_inventory': block('NET_NOT_OBSERVED','QCM/source arrival alone is not local net film inventory')
    if packet['surface']['electrical_equivalence']=='unverified': block('SURFACE_CHARGING_UNVERIFIED','Conductive probe is not equivalent to actual floating dielectric')
    if not packet['history_complete']: block('HISTORY_INCOMPLETE','Missing time intervals or state events')
    for rec in packet['raw_records']:
        if raw_root is None:
            if actual: block('RAW_NOT_CHECKED',rec['relative_path'])
            continue
        rr=Path(raw_root).resolve(); p=(rr/rec['relative_path']).resolve()
        if not p.is_relative_to(rr) or not p.is_file(): block('RAW_PATH_INVALID',rec['relative_path']);continue
        if hashlib.sha256(p.read_bytes()).hexdigest()!=rec['sha256']: block('RAW_HASH_MISMATCH',rec['relative_path'])
    if actual and not packet['raw_records']: block('RAW_MISSING','Actual packet needs traceable raw records')
    groups={}; samples=set()
    for r in packet['response_split']:
        if r['sample_id'] in samples: block('DUPLICATE_SAMPLE',r['sample_id'])
        samples.add(r['sample_id'])
        if r['run_id'] in groups and groups[r['run_id']]!=r['split']: block('LEAKED_RUN',r['run_id'])
        groups[r['run_id']]=r['split']
    if packet['response_split'] and not {'fit','final'}<=set(groups.values()): block('SPLITS_INCOMPLETE','Fit and final independent run groups needed')
    if packet['numeric_stage']['status'] not in {'validated_analytic','converged_local','not_run'}:
        block('NUMERIC_INCOMPLETE','Unresolved numerical output cannot be an uncertainty endpoint')
    if packet['numeric_stage']['used_as_interval_endpoint'] and packet['numeric_stage']['status'] not in {'validated_analytic','converged_local'}:
        block('NUMERIC_ENDPOINT_UNRESOLVED','Not-run or failed profile endpoint withheld')
    if packet['claim_class'] not in {'measurement_result','conditional_prediction'}:
        block('CLAIM_OUT_OF_SCOPE','No production/environment/damage qualification in this package')
    w=packet['observation_window']
    if w['t0_s'] is None or w['t1_s'] is None or w['clock_id'] is None or not (w['t1_s']>w['t0_s']):
        block('TIME_WINDOW_UNKNOWN','Positive, clock-referenced observation window required')
    co=packet['coordinate']
    if co['frame_id'] is None or co['position_m'] is None or co['outward_normal'] is None:
        block('COORDINATE_UNKNOWN','Position and unit surface normal in declared frame required')
    elif not math.isclose(sum(x*x for x in co['outward_normal']),1,rel_tol=0,abs_tol=1e-8):
        block('NORMAL_NOT_UNIT','Surface normal must be normalized')
    if not packet['cells']:
        block('SPECTRUM_MISSING','This joint-spectrum packet requires nonempty measured or synthetic cells')
    components=None
    if packet['cells']:
        try:
            cells=[Cell(**r) for r in packet['cells']]
            components=moments(cells, 'complete_conditional' if packet['neutral_coverage']=='complete_conditional' else 'unknown')
        except (ValueError,TypeError) as e: block('CELL_SEMANTICS',str(e))
    if errors and components is not None:
        components['usage']='unapproved_input_diagnostic_only'
    return {'status':'blocked_evidence' if errors else 'conditional_research_structure_valid',
            'errors':errors,'component_calculation':components,
            'actual_validation':'not_run_awaiting_device','production_release':False,
            'note':'Schema/evidence checks do not authenticate evidence or approve device/model validity'}
