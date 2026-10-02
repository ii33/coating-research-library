"""Build the frozen strict interchange schema; no network or device access."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def obj(props, required=None):
    return {'type':'object','properties':props,'required':list(props) if required is None else required,'additionalProperties':False}
def arr(x, n=0):return {'type':'array','items':x,'minItems':n}
def en(*x):return {'enum':list(x)}
S={'type':'string','minLength':1}; N={'type':'number'}; Z={'type':['number','null']}; SS={'type':['string','null']}
Q=obj({'value':Z,'unit':S,'status':en('measured','derived','synthetic','literature_reference','unknown','calibration_required'),
 'interval':{'anyOf':[{'type':'null'},{'type':'array','items':N,'minItems':2,'maxItems':2}]},
 'interval_kind':en('hard_bound','expanded_uncertainty','synthetic_bound','none'), 'standard_u':Z,'uncertainty_note':S,
 'source_ids':arr(S),'condition_id':S})
QR={'$ref':'#/$defs/quantity'}
identity=obj({'material_id':S,'label':S,'manufacturer':SS,'grade':SS,'lot':SS,'identity_status':en('verified','synthetic','unresolved'),
 'physical_state':en('thin_film','bulk_substrate'),'phase':SS,'nominal_formula':SS,'composition_verified':{'type':'boolean'},
 'stoichiometry':{'type':['object','null'],'additionalProperties':{'type':'number','exclusiveMinimum':0}},
 'element_molar_mass_kg_mol':{'type':'object','additionalProperties':QR},'density':QR,
 'density_basis':en('effective_film','bulk_substrate','unknown'),'density_composition_invariant':{'type':'boolean'}})
cell=obj({'flux':QR,'energy':QR,'theta':QR,'phi':QR})
beam=obj({'species':S,'charge_number':{'type':'integer','minimum':0},'nuclei_per_particle':{'type':'integer','minimum':1},
 'azimuth_policy':en('axisymmetric_assumed_for_fixture','resolved','unknown'),'distribution_basis':en('joint_energy_angle_bin_integrated_particle_flux'),'cells':arr(cell,1)})
Y=obj({'state':en('unknown','calibrated','literature_reference','synthetic'),'target_composition_id':S,'target_state':S,
 'projectile':S,'evidence_source_ids':arr(S),'energy_domain_eV':{'anyOf':[{'type':'null'},{'type':'array','items':N,'minItems':2,'maxItems':2}]},
 'angle_domain_deg':{'anyOf':[{'type':'null'},{'type':'array','items':N,'minItems':2,'maxItems':2}]},'temperature_domain_K':{'anyOf':[{'type':'null'},{'type':'array','items':N,'minItems':2,'maxItems':2}]},
 'fluence_domain_m2':{'anyOf':[{'type':'null'},{'type':'array','items':N,'minItems':2,'maxItems':2}]},'yield_basis':en('atoms_per_incident_particle'),
 'values_by_element':{'type':'object','additionalProperties':QR},'interpolation':en('none','piecewise_linear_in_domain'),
 'extrapolation':{'const':'forbidden'},'note':S})
bin_=obj({'bin_id':S,'t_start_s':N,'dt_s':{'type':'number','exclusiveMinimum':0},'surface_temperature':QR,
 'net_element_flux':{'type':'object','additionalProperties':QR},'net_flux_method':en('measured_inventory_change','synthetic_balance','unknown'),
 'net_flux_evidence':S,'beams':arr(beam),'neutral_inventory':en('included','measured_negligible','unknown'),
 'history_class':en('codeposition','ion_only','deposition_only','erosion','mixed','unknown'),
 'surface_potential':QR,'reactive_gas_partial_pressure':QR})
response=obj({'property':en('n','k','biaxial_stress','adhesion','rms_roughness'),'value':QR,'sample_id':S,
 'sample_state':en('thin_film','bulk_substrate'),'evidence':en('measurement','validated_model','unavailable'),
 'method':S,'wavelength':QR,'test_geometry':S,'failure_mode':S,'model_id':SS,
 'domain':obj({'temperature_K':arr(N),'incident_energy_eV':arr(N),'fluence_m2':arr(N),'flux_m2_s':arr(N),'history_classes':arr(S),'sample_ids':arr(S),'validation_evidence':arr(S)}),
 'production_ready':{'const':False}})
axis=obj({'status':en('bounded','unknown','not_applicable'),'note':S,'bound_reference':SS})
schema={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:coating-research:T04R2:material-response:1.0',
 'title':'Conditioned material response input contract',**obj({
 'schema_version':{'const':'1.0'},'record_id':S,'record_role':en('reference_unmeasured','synthetic_fixture','measured_campaign'),
 'production_qualified':{'const':False},'film':identity,'substrate':identity,
 'process_context':obj({'deposition_method':S,'source_type':SS,'source_model':SS,'chamber_id':SS,
 'source_material_identity':obj({'label':S,'manufacturer':SS,'grade':SS,'lot':SS}),
 'surface_preparation':S,'underlayers':arr(S),'post_treatment_history':arr(S),'environment_history':arr(S),'gas_species':arr(S),'spectrum_resolution_note':S}),
 'spatial_support':obj({'point_id':S,'area_m2':{'type':'number','exclusiveMinimum':0},'coordinate_frame':S,'normal_convention':{'const':'outward_surface_normal'},'scope':en('local_point','finite_cell_average')}),
 'flux_area_basis':{'const':'actual_substrate_surface_area'},'time_sampling':{'const':'piecewise_constant_bin_averages'},
 'history_resolution':en('resolved_bins','unresolved'),'atom_inventory_coverage':en('all_retained_elements','partial','unknown'),
 'initial_inventory_atoms_m2':{'type':'object','additionalProperties':QR},'initial_thickness':QR,
 'bins':arr(bin_,1),'resputter_yield_records':arr(Y),'response_records':arr(response),
 'uncertainty_axes':obj({a:axis for a in ('source','time','space','geometry','kernel','input','model')}),
 'provenance':obj({'source_ids':arr(S),'dependency_hashes':{'type':'object','additionalProperties':S},'ray_bundle_id':SS,'measurement_ids':arr(S),'notes':S}),
 'requested_outputs':arr(en('N_net','h_increment','D','U','R','epsilon'),1)
 }), '$defs':{'quantity':Q}}
(ROOT/'data/material_response.schema.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':print('schema written')
