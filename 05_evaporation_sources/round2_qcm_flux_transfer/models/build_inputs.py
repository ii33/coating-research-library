from pathlib import Path
import json,copy
import numpy as np
from qcm_flux import point_kernel,frequency_from_mass
R=Path(__file__).resolve().parents[1]
def obj(props):return {'type':'object','properties':props,'required':list(props),'additionalProperties':False}
def arr(item,n=None):
 d={'type':'array','items':item}
 if n is not None:d.update(minItems=n,maxItems=n)
 return d
num={'type':'number'}; nullable={'type':['number','null']}; vec=arr(num,3)
def nullor(s):return {'anyOf':[s,{'type':'null'}]}
def qty(unit,minimum=None,maximum=None):
 value=dict(nullable)
 if minimum is not None:value['minimum']=minimum
 if maximum is not None:value['maximum']=maximum
 return obj({'value':value,'unit':{'const':unit},'status':{'enum':['unknown','assumed_synthetic','measured','literature_reference']},'source':{'type':'string','minLength':1}})
params=obj({'f0_hz':qty('Hz',1),'z_ratio':qty('1',1e-12),'capture_qcm':qty('1',1e-12,1),'source_exponent_n':qty('1',0),'source_anisotropy_a':qty('1',-.95,.95),'display_density_setting':qty('kg/m3',1e-12),'actual_qcm_film_density':qty('kg/m3',1e-12),'actual_workpiece_film_density':qty('kg/m3',1e-12),'tooling_percent':qty('%',1e-12)})
schema=obj({'schema_version':{'const':'T05-QCM-2.0'},'record_id':{'type':'string'},'record_kind':{'enum':['synthetic','actual_unmeasured']},'source_material':{'const':'Al'},'substrate':{'type':'string'},'parameters':params,
'qcm':obj({'controller_model':{'type':['string','null']},'model':{'enum':['sauerbrey','zmatch']},'fundamental_mode':{'const':True},'rigid_bonded_validated':{'type':'boolean'},'times_s':nullor(arr(num)),'frequency_hz':nullor(arr(num)),'drift_hz':nullor(arr(num)),'frequency_covariance_hz2':nullor(arr(arr(num))),'drift_evidence':{'type':'string'},'side_terms_status':{'enum':['unknown','assumed_synthetic','measured']},'reactive_retained_kg_m2_s':{'type':'number','minimum':0},'outgoing_kg_m2_s':{'type':'number','minimum':0},'sensor_temperature_K':nullor(arr(num)),'quality_notes':{'type':'string'}}),
'geometry':obj({'source_center_m':nullor(vec),'source_normal':nullor(vec),'azimuth_axis':nullor(vec),'qcm_position_m':nullor(vec),'qcm_normal':nullor(vec),'workpiece_positions_m':nullor(arr(vec)),'workpiece_normals':nullor(arr(vec)),'visibility':nullor(arr({'type':'number','minimum':0,'maximum':1}))}),
'species':obj({'number_fractions':nullor({'type':'object','additionalProperties':{'type':'number','minimum':0,'maximum':1}}),'stoichiometries':{'type':'object','additionalProperties':{'type':'object','minProperties':1,'additionalProperties':{'type':'integer','minimum':1}}},'evidence':{'type':'string'}}),
'error_budget':obj({k:{'type':'string','minLength':1} for k in ['source','time','space','geometry','kernel','input','model']}),'qualification':{'const':'research_only_not_production'}})
schema.update({'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'https://example.invalid/research/T05-QCM-2.0'})
(R/'data/qcm_flux.schema.json').write_text(json.dumps(schema,indent=2)+'\n')
def p(x,u='1',src='synthetic known truth'):return {'value':x,'unit':u,'status':'assumed_synthetic','source':src}
t=np.linspace(0,20,11);f0=6045000.;z=1.08; Q=2e-6;n=2.4;a=.25; eta=.92
pos=[[.12,.03,.5],[0,0,.6],[.30,.1,.6]];norm=[[0,0,-1]]*3;k=point_kernel(pos,norm,n,a); mass=1e-5+eta*Q*k[0]*t; drift=.15*t
base={'schema_version':'T05-QCM-2.0','record_id':'Al_synthetic_known_truth','record_kind':'synthetic','source_material':'Al','substrate':'synthetic inert flat coupon; actual user substrate unknown',
'parameters':{'f0_hz':p(f0,'Hz'),'z_ratio':p(z,src='T05-R2-S01 manual table value used as synthetic truth only'),'capture_qcm':p(eta),'source_exponent_n':p(n),'source_anisotropy_a':p(a),'display_density_setting':p(2700.,'kg/m3'),'actual_qcm_film_density':p(2600.,'kg/m3'),'actual_workpiece_film_density':p(2500.,'kg/m3'),'tooling_percent':{'value':None,'unit':'%','status':'unknown','source':'not calibrated; not needed for raw-frequency transfer'}},
'qcm':{'controller_model':'INFICON SQM-160 equations used as literature example, no connected instrument','model':'zmatch','fundamental_mode':True,'rigid_bonded_validated':True,'times_s':t.tolist(),'frequency_hz':(frequency_from_mass(mass,f0,z)+drift).tolist(),'drift_hz':drift.tolist(),'frequency_covariance_hz2':(np.eye(len(t))*.05**2).tolist(),'drift_evidence':'synthetic independent blank truth; covariance conditional on drift truth','side_terms_status':'assumed_synthetic','reactive_retained_kg_m2_s':0.,'outgoing_kg_m2_s':0.,'sensor_temperature_K':None,'quality_notes':'All values synthetic. No actual mass sensitivity profile or bond validation.'},
'geometry':{'source_center_m':[0,0,0],'source_normal':[0,0,1],'azimuth_axis':[1,0,0],'qcm_position_m':pos[0],'qcm_normal':norm[0],'workpiece_positions_m':pos[1:],'workpiece_normals':norm[1:],'visibility':[1.,1.,1.]},
'species':{'number_fractions':{'Al':1.},'stoichiometries':{'Al':{'Al':1}},'evidence':'T05-R2-S07 NIST confirms Al(g) species existence, not actual plume purity; pure atomic vapor is synthetic assumption'},
'error_budget':{k:'synthetic input exact for this case; actual machine '+k+' uncertainty unknown' for k in ['source','time','space','geometry','kernel','input','model']},'qualification':'research_only_not_production'}
(R/'examples/synthetic_al.json').write_text(json.dumps(base,indent=2)+'\n')
actual=copy.deepcopy(base);actual.update(record_id='actual_machine_unknown',record_kind='actual_unmeasured',substrate='unknown')
for key,v in actual['parameters'].items():v.update(value=None,status='unknown',source='actual measurement/calibration absent')
for key in actual['geometry']:actual['geometry'][key]=None
actual['species']['number_fractions']=None;actual['species']['evidence']='actual vapor composition unknown'
for key in ['times_s','frequency_hz','drift_hz','frequency_covariance_hz2']:actual['qcm'][key]=None
actual['qcm'].update(controller_model=None,rigid_bonded_validated=False,side_terms_status='unknown',drift_evidence='unknown',quality_notes='no actual data supplied')
(R/'examples/actual_unknown.json').write_text(json.dumps(actual,indent=2)+'\n')
(R/'data/synthetic_truth.json').write_text(json.dumps({'Q_kg_s':Q,'n':n,'a':a,'capture_qcm':eta,'net_qcm_mass_rate_kg_m2_s':eta*Q*k[0],'workpiece_incident_kg_m2_s':(Q*k[1:]).tolist(),'initial_load_kg_m2':1e-5,'drift_hz_s':.15},indent=2)+'\n')
