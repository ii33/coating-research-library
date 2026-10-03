from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def obj(props,required=None):
 return {'type':'object','properties':props,'required':list(props) if required is None else required,'additionalProperties':False}
def arr(items):return {'type':'array','items':items}
def enum(*values):return {'enum':list(values)}
text={'type':'string','minLength':1}; nullable={'type':['string','null']}; num={'type':'number'}; positive={'type':'number','exclusiveMinimum':0}; nonneg={'type':'integer','minimum':0}; boolean={'type':'boolean'}
schema={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:coating-research:T09R2:evidence-packet:1',
 'title':'Research-only evidence packet, not a release authorization',
 'description':'Strict shape only. Semantic gates are separately implemented. Real measurement and production qualification unsupported.'}
schema.update(obj({
 'packet_id':text,'evidence_mode':{'const':'synthetic_demo'},'requested_claim':{'const':'research_diagnostic'},
 'observations':arr(obj({'id':text,'value':num,'unit':enum('nm','nm/s','Hz','1','percent'),'quantity_kind':text,'coordinate':text,
 't_s':num,'run_id':text,'sample_id':text,'reading_origin':enum('measured','derived_from_measurement','substituted_setpoint','held','unknown'),
 'raw_ref':nullable,'requires_lock':boolean,'lock_state':enum('locked','unlocked','unknown','not_applicable'),'controller_mode':enum('measurement','qcm_control','time_power','manual','unknown'),
 'parameter_snapshot_id':text,'parameter_switched':boolean,'parameter_event_id':nullable,'negative_clip_mode':enum('none','project_max_zero_demo','device_specific_unknown'),
 'transformation_ref':nullable,'calibration_id':text})),
 'datasets':arr(obj({'id':text,'role':enum('fit','selection','heldout_final','calibration','process_estimate'),'observation_ids':arr(text),'used_to_update_model':boolean})),
 'parameter_snapshots':arr(obj({'id':text,'material_id':text,'density_kg_m3':positive,'z_factor':positive,'tooling_fraction':positive,'feedback_coordinate':text,'display_coordinate':text})),
 'events':arr(obj({'id':text,'kind':enum('parameter_change','reset','continue','restart','shutter_command','shutter_observation'),'t_s':num,'snapshot_id':nullable})),
 'calibrations':arr(obj({'id':text,'within_scope':{'type':['boolean','null']},'basis_ref':nullable})),
 'numerics':arr(obj({'id':text,'status':enum('not_run','running','converged_local','validated_analytic','budget_exhausted','solver_failure','invalid_model','interrupted','numerical_check_failed'),'required_for_claim':boolean,'calls':nonneg,'budget':nonneg,'stop_reason':text})),
 'cross_split_correlation':obj({'status':enum('known_synthetic','modelled_with_evidence','unknown'),'basis_ref':nullable}),
 'decision_rule':obj({'rule_id':enum('project_closed_interval_v1'),'preagreed':boolean,'approval_ref':nullable}),
 'source_visibility':arr(obj({'source_id':text,'workpiece_visibility':enum('unknown','open_verified','closed_verified'),'position_evidence_ref':nullable,'thermal_state':enum('unknown','hot','cooled_with_evidence'),'zero_flux_verified':boolean,'zero_flux_basis_ref':nullable}))}))
(ROOT/'contracts/evidence_packet.schema.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n')
