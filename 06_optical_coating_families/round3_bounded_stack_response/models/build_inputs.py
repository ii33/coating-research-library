"""Small bounded upstream bridge; one encoded trajectory, no heavy sweep."""
import json,sys,hashlib
from pathlib import Path
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'dependencies/t05/models'))
from source_retention import bridge_t04,t04

def build():
    r=t04.Response(source_scale_kg_s=None,angular_a=(.4,.4),density_kg_m3=(1998.,2002.))
    b=bridge_t04(t04.Scene(),r,(1.998e-6,2.002e-6),panels=16)
    h=b['t04_response']['signed_thickness_change_m'];href=(h[0]+h[1])/2
    material={'dataset_kind':'synthetic','nk_basis':'legacy_constant_seed_not_measured','density_basis':'synthetic_effective_film','composition_basis':'fixed_synthetic_identity','sample_state_id':'synthetic_shared_relative_density_v1','nk_sample_state_id':'synthetic_shared_relative_density_v1','density_sample_state_id':'synthetic_shared_relative_density_v1','normalization_h_ref_m':href,'expected_bridge_payload_sha256':hashlib.sha256(json.dumps(b,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest(),'mapping':'legacy thicknesses times one shared positive h/h_ref; layer-specific dose multipliers; NOT duration scaling','real_film_parameters':'unknown','density_correlation':'same relative density error across the surrogate layers by explicit synthetic assumption; not equal physical densities','fixed_identities':['ZnS surrogate','YF3 surrogate'],'fixed_substrate':'Ge surrogate n=4','temperature_state':'synthetic fixed 300 K optical state; no measured temperature dispersion'}
    op={'observable':'power_weighted_R','wavelength_um':['4.25','4.26','4.27'],'weights':['1/4','1/2','1/4'],'valid_band_um':['4.25','4.27'],'aoi_deg':0,'angular_distribution':'delta','polarization':'unpolarized','substrate_mode':'semi_infinite','transmission_meaning':'flux_entering_substrate','scatter':'synthetic_exact_zero','spectral_response':'declared_discrete_nodes','measurement_error_abs':'0.001','error_status':'synthetic bounded readout error, not measured uncertainty or 95 percent interval','instrument_id':'synthetic_3_node_operator','spot_contract':'spatially_uniform_planar_local_model_no_area_average'}
    case={'stage':'T06R3','bridge':b,'material':material,'measurement':op,'recipe_id':'S-AR-DUALIR6','variants':{'A':'1','B':'1.25','C':'1.002'},'point12':'partial_unchanged','point2':'conditional_non_strict_unchanged','formal_review_chain':'pending'}
    (ROOT/'data/case.json').write_text(json.dumps(case,ensure_ascii=False,indent=2)+'\n')
    return {'bridge_status':b['status'],'h_bounds_m':h,'response_contract_sha256':b['t04_response']['response_contract_sha256'],'bridge_contract_sha256':b['bridge_contract_sha256'],'panels':16,'one_trajectory_only':True}
if __name__=='__main__':print(json.dumps(build(),indent=2))
