"""Create clearly labeled synthetic records and an honestly unmeasured representative."""
from pathlib import Path
import copy,hashlib,json
from contract import AXES,calculate
ROOT=Path(__file__).resolve().parents[1]
def q(value,unit,rel=0.02,status='synthetic',sources=None,condition='SYNTH-LOCAL-001'):
    return {'value':value,'unit':unit,'status':status,'interval':None if value is None else [value-abs(value)*rel,value+abs(value)*rel],
            'interval_kind':'none' if value is None else 'synthetic_bound','standard_u':None,
            'uncertainty_note':'Unmeasured, not zero uncertainty' if value is None else 'Artificial deterministic ±relative bound; not a confidence interval',
            'source_ids':sources or (['SYNTHETIC-DEFINITION'] if value is not None else []),'condition_id':condition}
def unknown(unit):return q(None,unit,status='unknown',condition='UNMEASURED')
def identity(label,substrate=False):
    return {'material_id':'fused_silica_method_example' if substrate else 'SiO2_film','label':label,
     'manufacturer':None,'grade':None,'lot':None,'identity_status':'synthetic','physical_state':'bulk_substrate' if substrate else 'thin_film',
     'phase':'amorphous_assumed_for_synthetic_only','nominal_formula':'SiO2','composition_verified':True,'stoichiometry':{'Si':1.,'O':2.},
     'element_molar_mass_kg_mol':{'Si':q(.028085,'kg/mol',.00002),'O':q(.015999,'kg/mol',.00002)},
     'density':q(2150.,'kg/m3',.025),'density_basis':'bulk_substrate' if substrate else 'effective_film','density_composition_invariant':True}
def response(name):
    return {'property':name,'value':unknown({'n':'1','k':'1','biaxial_stress':'Pa','adhesion':'method_defined','rms_roughness':'m'}[name]),
      'sample_id':'SYNTH-FILM-001','sample_state':'thin_film','evidence':'unavailable','method':'unknown','wavelength':unknown('m'),
      'test_geometry':'unknown','failure_mode':'unknown','model_id':None,
      'domain':{'temperature_K':[],'incident_energy_eV':[],'fluence_m2':[],'flux_m2_s':[],'history_classes':[],'sample_ids':[],'validation_evidence':[]},'production_ready':False}
def base():
    film=identity('Synthetic stoichiometric amorphous silica film');sub=identity('Synthetic fused-silica witness substrate',True)
    bins=[]
    for i,(net,gamma,E,T) in enumerate([(1.2e18,2e17,100.,300.),(8e17,4e17,150.,310.)]):
        bins.append({'bin_id':f'b{i}','t_start_s':10.*i,'dt_s':10.,'surface_temperature':q(T,'K',.01),
         'net_element_flux':{'Si':q(net/3,'atoms/m2/s'),'O':q(net*2/3,'atoms/m2/s')},
         'net_flux_method':'synthetic_balance','net_flux_evidence':'Toy resolved elemental inventory balance, not QCM arrival flux',
         'beams':[{'species':'Ar+','charge_number':1,'nuclei_per_particle':1,'azimuth_policy':'axisymmetric_assumed_for_fixture','distribution_basis':'joint_energy_angle_bin_integrated_particle_flux','cells':[{'flux':q(gamma,'particles/m2/s'), 'energy':q(E,'eV/particle',.05),'theta':q(20.,'deg_from_normal',.025),'phi':unknown('deg_about_normal')}]}],
         'neutral_inventory':'measured_negligible','history_class':'codeposition','surface_potential':q(0.,'V',0),'reactive_gas_partial_pressure':q(.01,'Pa',.1)})
    return {'schema_version':'1.0','record_id':'SYNTH-POSITIVE-001','record_role':'synthetic_fixture','production_qualified':False,
     'film':film,'substrate':sub,
     'process_context':{'deposition_method':'synthetic net-inventory demonstration','source_type':None,'source_model':None,'chamber_id':None,'source_material_identity':{'label':'nominal SiO2, hypothetical source','manufacturer':None,'grade':None,'lot':None},'surface_preparation':'not specified; no actual sample','underlayers':[],'post_treatment_history':[],'environment_history':[],'gas_species':['Ar','O2'],'spectrum_resolution_note':'One bin per species per time interval is an artificial joint-spectrum fixture, not a measured narrow beam'},
     'spatial_support':{'point_id':'synthetic-local-point','area_m2':1.e-4,'coordinate_frame':'substrate_local_SI','normal_convention':'outward_surface_normal','scope':'local_point'},
     'flux_area_basis':'actual_substrate_surface_area','time_sampling':'piecewise_constant_bin_averages','history_resolution':'resolved_bins','atom_inventory_coverage':'all_retained_elements',
     'initial_inventory_atoms_m2':{'Si':q(1.e20,'atoms/m2',.0),'O':q(2.e20,'atoms/m2',.0)},'initial_thickness':unknown('m'),
     'bins':bins,'resputter_yield_records':[{'state':'unknown','target_composition_id':'SiO2_actual_film','target_state':'unknown','projectile':'Ar+',
      'evidence_source_ids':[],'energy_domain_eV':None,'angle_domain_deg':None,'temperature_domain_K':None,'fluence_domain_m2':None,
      'yield_basis':'atoms_per_incident_particle','values_by_element':{},'interpolation':'none','extrapolation':'forbidden','note':'No qualified Y(E,theta,state) transferred; measured net-element route does not require assigning a yield'}],
     'response_records':[response(x) for x in ('n','k','biaxial_stress','adhesion','rms_roughness')],
     'uncertainty_axes':{a:{'status':'bounded' if a=='input' else 'unknown','note':'Synthetic input intervals only' if a=='input' else 'No independent closure in this local fixture','bound_reference':'quantity intervals' if a=='input' else None} for a in AXES},
     'provenance':{'source_ids':['SYNTHETIC-DEFINITION'],'dependency_hashes':{},'ray_bundle_id':None,'measurement_ids':[],
      'notes':'Entire numerical record is synthetic. Does not assert user equipment, rates, actual material identity, film density, neutral fraction or production response.'},
     'requested_outputs':['N_net','h_increment','D','U','R','epsilon']}
def all_examples():
    a=base();ex={'positive':a}
    for name,value in [('zero',0.),('erosion',-1e18),('cross_zero',1e16)]:
        r=copy.deepcopy(a);r['record_id']='SYNTH-'+name.upper()
        for b in r['bins']:
            b['history_class']='erosion' if value<0 else 'ion_only' if value==0 else 'codeposition'
            for e,f in [('Si',1/3),('O',2/3)]:
                b['net_element_flux'][e]=q(value*f,'atoms/m2/s',0.)
                if name=='cross_zero':b['net_element_flux'][e]['interval']=[-1e16*f,3e16*f]
        ex[name]=r
    r=copy.deepcopy(a);r['record_id']='SYNTH-ILL-CONDITIONED'
    for b in r['bins']:
        for q_ in b['net_element_flux'].values():q_['interval']=[q_['value']*.1,q_['value']*1.9]
    ex['ill_conditioned']=r
    r=copy.deepcopy(a);r['record_id']='SYNTH-UNKNOWN-NEUTRALS';r['bins'][0]['neutral_inventory']='unknown';ex['unknown_neutrals']=r
    r=copy.deepcopy(a);r['record_id']='SYNTH-BULK-DENSITY-MISUSE';r['film']['density_basis']='bulk_substrate';ex['bulk_density_misuse']=r
    r=copy.deepcopy(a);r['record_id']='REF-SIO2-FUSED-SILICA-UNMEASURED';r['record_role']='reference_unmeasured'
    def erase(x):
        if isinstance(x,dict):
            if 'interval_kind' in x and 'unit' in x:
                u=x['unit'];x.clear();x.update(unknown(u))
            else:
                for v in x.values():erase(v)
        elif isinstance(x,list):
            for v in x:erase(v)
    erase(r)
    for m in (r['film'],r['substrate']):m['identity_status']='unresolved';m['phase']=None;m['composition_verified']=False;m['density_composition_invariant']=False
    for b in r['bins']:b['net_flux_method']='unknown';b['neutral_inventory']='unknown';b['history_class']='unknown';b['net_flux_evidence']='No user campaign data'
    r['process_context']['deposition_method']='unknown';r['process_context']['source_material_identity']['label']='unknown source material';r['process_context']['gas_species']=[];r['process_context']['spectrum_resolution_note']='No measured energy-angle spectrum';
    for b in r['bins']:
        for beam in b['beams']:beam['azimuth_policy']='unknown'
    r['history_resolution']='unresolved';r['atom_inventory_coverage']='unknown';r['provenance']['source_ids']=['MR-S01','MR-S02','MR-S03','MR-S04','MR-S05'];r['provenance']['notes']='Public-evidence selection only; time/position entries are template placeholders, not a campaign. No bulk reference value copied into actual film inputs.'
    for a_ in AXES:r['uncertainty_axes'][a_]={'status':'unknown','note':'No campaign measurement or numerical closure','bound_reference':None}
    ex['reference_unmeasured']=r
    return ex
if __name__=='__main__':
    outputs={}
    for name,r in all_examples().items():
        (ROOT/'examples'/f'{name}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
        outputs[name]=calculate(r)
    (ROOT/'verification/example_results.json').write_text(json.dumps(outputs,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print('wrote',len(outputs),'examples')
