"""Restricted conditional synthetic optical interval algorithm.
Normal incidence, real positive constant n, k=0, semi-infinite substrate,
no scattering. Unknown or unsupported contracts fail closed. No optimizer.
"""
from pathlib import Path
import hashlib,json,math
from exact_intervals import I,C,F,PI,phase,iv,hull,f
ROOT=Path(__file__).resolve().parents[1]
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def verify_dependencies():
    rows=json.loads((ROOT/'data/frozen_dependencies.json').read_text())
    for row in rows:
        p=ROOT/row['copy']
        if p.is_symlink() or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('copied_dependency_mismatch:'+row['copy'])
    return len(rows)
def validate_operator(op):
    if op['aoi_deg']!=0 or op['angular_distribution']!='delta' or op['polarization']!='unpolarized':raise ValueError('unsupported_AOI_polarization')
    if op['substrate_mode']!='semi_infinite' or op['transmission_meaning']!='flux_entering_substrate' or op['scatter']!='synthetic_exact_zero':raise ValueError('unsupported_backside_or_scatter')
    if op['observable']!='power_weighted_R' or op['spectral_response']!='declared_discrete_nodes':raise ValueError('operator_not_supported')
    w=op['wavelength_um'];a=op['weights']
    if len(w)!=len(a) or not w or any(f(v)<=0 for v in w) or any(f(v)<0 for v in a) or sum(map(f,a))!=1:raise ValueError('invalid_spectral_nodes_weights')
    if any(not f(op['valid_band_um'][0])<=f(v)<=f(op['valid_band_um'][1]) for v in w):raise ValueError('bandwidth_node_out_of_domain')
    if f(op['measurement_error_abs'])<0:raise ValueError('negative_measurement_error')
    return op

def source_gate(bridge,material):
    verify_dependencies()
    if material['dataset_kind']!='synthetic' or material['nk_basis']!='legacy_constant_seed_not_measured' or material['density_basis']!='synthetic_effective_film' or material['composition_basis']!='fixed_synthetic_identity':return {'status':'unknown_material_state','bounds':None}
    if material['sample_state_id']!=material['nk_sample_state_id'] or material['sample_state_id']!=material['density_sample_state_id']:return {'status':'unknown_state_mismatch','bounds':None}
    if bridge.get('status')!='bounded_synthetic_response':return {'status':bridge.get('status','unknown'),'bounds':None}
    if digest(bridge)!=material.get('expected_bridge_payload_sha256'):return {'status':'unbound_or_modified_full_forward_payload','bounds':None}
    src=bridge['source_contract'];out=bridge.get('t04_response')
    if src.get('n')!=1 or src.get('c')!=0 or not out:return {'status':'unsupported_or_unknown_source','bounds':None}
    if out.get('status')!='bounded_synthetic_response' or out.get('physical_certification') is not False:return {'status':'upstream_unqualified','bounds':None}
    for key in ['response_contract_sha256','upstream_full_forward','response_definition','net_mass_kg_m2','signed_thickness_change_m','retained_transfer_s_m2']:
        if out.get(key) is None:return {'status':'missing_'+key,'bounds':None}
    resp=out['response_definition']
    if resp['density_basis']!='synthetic_constant_effective_film' or resp['density_kg_m3'] is None:return {'status':'unknown_density','bounds':None}
    if min(resp['initial_inventory_kg_m2'])<max(resp['erosion_mass_kg_m2']):return {'status':'inventory_unresolved','bounds':None}
    mass=I(*out['net_mass_kg_m2']);h=I(*out['signed_thickness_change_m'])
    if mass.hi<0 or h.hi<0:return {'status':'negative_net','bounds':None}
    if mass.lo<=0 or h.lo<=0:return {'status':'zero_or_crossing_net','bounds':None}
    if h.lo<=f('1e-15') or h.hi-h.lo>=h.lo:return {'status':'ill_conditioned_net','bounds':None}
    if not out['upstream_full_forward'].get('input_uncertainty_qualified'):return {'status':'upstream_unqualified','bounds':None}
    return {'status':'conditional_synthetic_only','bounds':h,'response_contract_sha256':out['response_contract_sha256'],'bridge_contract_sha256':bridge['bridge_contract_sha256'],'point12':'partial_unchanged','point2':'conditional_non_strict_unchanged'}

def load_case():return json.loads((ROOT/'data/case.json').read_text())
def incident_stack(recipe):
    if recipe['order']!='substrate_to_incident_medium':raise ValueError('unrecognized_layer_order')
    layers=list(reversed(recipe['layers']))
    n=[f(recipe['incident_n_for_seed_only'])]+[f(v['n_for_seed_only']) for v in layers]+[f(recipe['substrate_n_for_seed_only'])]
    d=[f(v['thickness_nm'])/1000 for v in layers]
    if any(v<=0 for v in n+d):raise ValueError('nonpositive_seed')
    return n,d,[v['layer'] for v in layers]

def reflectance(n,d,w):
    """Bottom-up Airy recursion, rectangular complex interval enclosure."""
    if len(n)!=len(d)+2 or any(iv(x).lo<=0 for x in n) or f(w)<=0 or any(iv(x).lo<=0 for x in d):raise ValueError('strict_positive_normal_lossless_contract')
    rr=[(iv(n[j])-iv(n[j+1]))/(iv(n[j])+iv(n[j+1])) for j in range(len(n)-1)]
    r=C(rr[-1])
    for j in reversed(range(len(d))):
        z=r*phase(4*PI*iv(n[j+1])*iv(d[j])/f(w))
        r=(C(rr[j])+z)/(1+C(rr[j])*z)
    return r.abs2().intersect(0,1)

def measured_R(recipe,scale,op):
    validate_operator(op);n,d,_=incident_stack(recipe)
    return sum((f(a)*reflectance(n,[iv(v)*scale for v in d],w) for w,a in zip(op['wavelength_um'],op['weights'])),I(0))

def split_interval(x,count):
    if type(count)is not int or count<1:raise ValueError('positive_integer_cells')
    dx=(x.hi-x.lo)/count
    return [I(x.lo+j*dx,x.lo+(j+1)*dx) for j in range(count)]
def propagate(recipe,bridge,material,op,variant_scale='1',cells=8):
    gate=source_gate(bridge,material);validate_operator(op)
    if gate['bounds'] is None:return {'status':gate['status'],'R_bounds':None}
    # Positive deterministic scale is a synthetic dose multiplier, NOT time dilation.
    # All layers use the SAME latent h/h_ref. h_ref normalizes a scenario, not data.
    href=f(material['normalization_h_ref_m']);v=f(variant_scale)
    if href<=0 or v<=0:raise ValueError('positive_synthetic_scale_required')
    z=gate['bounds']/href
    values=[];unresolved=0
    for cell in split_interval(z,cells):
        try:values.append(measured_R(recipe,cell*v,op))
        except ZeroDivisionError:values.append(I(0,1));unresolved+=1
    out=values[0]
    for x in values[1:]:out=hull(out,x)
    contract={'recipe':recipe,'material':material,'measurement':op,'response':gate['response_contract_sha256'],'bridge':gate['bridge_contract_sha256'],'mapping':'all_d_i=d_legacy_i*variant_scale*h/h_ref','variant_scale':str(v),'arithmetic':'dyadic80_Machin_Taylor20_rectangular_Airy'}
    return {'status':'conditional_synthetic_enclosure' if not unresolved else 'unresolved_optical_denominator','R_bounds':out.floats(),'R_bounds_exact':out.exact(),'T_into_substrate_bounds':(1-out).floats(),'scale_bounds':z.floats(),'cells':cells,'unresolved_cells':unresolved,'optical_contract_sha256':digest(contract),'response_contract_sha256':gate['response_contract_sha256'],'bridge_contract_sha256':gate['bridge_contract_sha256'],'measurement_contract_sha256':digest(op),'material_contract_sha256':digest(material),'physical_certification':False,'scope':'finite_discrete_normal_lossless_synthetic_model_only'}

def distinguish(a,b,error_abs):
    for k in ('response_contract_sha256','measurement_contract_sha256','material_contract_sha256'):
        if a.get(k)!=b.get(k):return {'status':'incomparable_contracts'}
    if a.get('status')!='conditional_synthetic_enclosure' or b.get('status')!='conditional_synthetic_enclosure':return {'status':'unresolved'}
    e=f(error_abs)
    if e<0:raise ValueError('negative_measurement_error')
    A=I(*a['R_bounds_exact'])+I(-e,e);B=I(*b['R_bounds_exact'])+I(-e,e)
    if A.hi<B.lo or B.hi<A.lo:return {'status':'distinguishable_under_declared_error','A_observed_bounds':A.floats(),'B_observed_bounds':B.floats(),'minimum_gap':float(max(B.lo-A.hi,A.lo-B.hi))}
    return {'status':'unresolved_overlap_not_proof_of_equivalence','A_observed_bounds':A.floats(),'B_observed_bounds':B.floats()}

def paired_difference(recipe,bridge,material,op,scale_a,scale_b,cells=8):
    """Same-run shared latent errors, hence A/B evaluated on SAME subcells.
    Interval arithmetic loses within-cell dependency, but subdivision recovers it.
    Independent sample/run comparison must instead use independent latent sets.
    """
    gate=source_gate(bridge,material)
    if gate['bounds'] is None:return {'status':gate['status'],'bounds':None}
    z=gate['bounds']/f(material['normalization_h_ref_m']);out=None
    for cell in split_interval(z,cells):
        try:d=measured_R(recipe,cell*f(scale_b),op)-measured_R(recipe,cell*f(scale_a),op)
        except ZeroDivisionError:return {'status':'unresolved_optical_denominator','bounds':None}
        out=d if out is None else hull(out,d)
    return {'status':'conditional_paired_difference','B_minus_A_R_bounds':out.floats(),'cells':cells,'requires_same_latent_realization':True}
