"""Strict JSON input gate. Unknown calibration remains blocked, never imputed."""
from pathlib import Path
import json
import sys
import numpy as np
from jsonschema import Draft202012Validator
from qcm_flux import rate_from_frequency, point_kernel, transfer_qcm_to_workpiece, mixture_from_mass
ROOT=Path(__file__).resolve().parents[1]

def validate(record):
    def check_finite(x):
        if isinstance(x, float) and not np.isfinite(x): raise ValueError('nonfinite JSON number')
        if isinstance(x, dict):
            for value in x.values(): check_finite(value)
        if isinstance(x, list):
            for value in x: check_finite(value)
    check_finite(record)
    schema=json.loads((ROOT/'data/qcm_flux.schema.json').read_text())
    Draft202012Validator(schema).validate(record)
    for name,p in record['parameters'].items():
        if p['status']=='unknown' and p['value'] is not None: raise ValueError(name+': unknown must be null')
        if p['status']!='unknown' and p['value'] is None: raise ValueError(name+': known must carry value')
        if p['status']=='assumed_synthetic' and record['record_kind']!='synthetic': raise ValueError('synthetic assumptions cannot calibrate an actual record')
    q=record['qcm']
    if q['times_s'] is not None:
        n=len(q['times_s'])
        if any(q[k] is None or len(q[k])!=n for k in ['frequency_hz','drift_hz']):raise ValueError('paired QCM vectors required')
        if n<3 or np.any(np.diff(q['times_s'])<=0):raise ValueError('3 increasing timestamps required')
    return True

def convert(record):
    validate(record)
    required=['f0_hz','z_ratio','capture_qcm','source_exponent_n','source_anisotropy_a']
    missing=[x for x in required if record['parameters'][x]['value'] is None]
    if record['qcm']['times_s'] is None:missing.append('raw_qcm_time_series')
    if any(record['geometry'][k] is None for k in record['geometry']):missing.append('geometry')
    if not record['qcm']['rigid_bonded_validated']:missing.append('rigid_bonded_model_validity')
    if record['species']['number_fractions'] is None:missing.append('vapor_species_fractions')
    if record['qcm']['side_terms_status']=='unknown':missing.append('reaction_outgoing_mass_balance')
    if missing:return {'status':'blocked_unmeasured','missing':missing,'production_qualified':False}
    p={k:v['value'] for k,v in record['parameters'].items()}; q=record['qcm']; g=record['geometry']
    if record['record_kind']=='actual_unmeasured':
        # Literature constants may support the quartz acoustic model, but geometry/capture
        # cannot become actual calibration merely by changing a label on synthetic data.
        gate=['capture_qcm','source_exponent_n','source_anisotropy_a']
        if any(record['parameters'][k]['status']!='measured' for k in gate):
            return {'status':'blocked_unmeasured','missing':['actual_capture_and_shape_calibration'],'production_qualified':False}
    rate=rate_from_frequency(q['times_s'],q['frequency_hz'],p['f0_hz'],drift_hz=q['drift_hz'],frequency_covariance_hz2=q['frequency_covariance_hz2'],z_ratio=p['z_ratio'],method=q['model'])
    sigma=rate['slope_std_kg_m2_s']
    if sigma is not None and rate['slope_kg_m2_s'] <= 5*sigma:
        return {'status':'blocked_low_signal','reason':'net positive source-arrival inversion needs an explicit low-signal model; analysis gate SNR>5','production_qualified':False,'rate':rate}
    pos=[g['qcm_position_m']]+g['workpiece_positions_m']; norm=[g['qcm_normal']]+g['workpiece_normals']
    k=point_kernel(pos,norm,p['source_exponent_n'],p['source_anisotropy_a'],g['visibility'],center_m=g['source_center_m'],source_normal=g['source_normal'],azimuth_axis=g['azimuth_axis'])
    transfer=transfer_qcm_to_workpiece(rate['slope_kg_m2_s'],p['capture_qcm'],k[0],k[1:],q['reactive_retained_kg_m2_s'],q['outgoing_kg_m2_s'])
    values=[]
    for mass in transfer['incident_workpiece_kg_m2_s']:
        values.append(mixture_from_mass(mass,record['species']['number_fractions'],record['species']['stoichiometries']))
    return {'status':'synthetic_computed' if record['record_kind']=='synthetic' else 'conditional_computed',
            'production_qualified':False,'rate':rate,'kernel_m_minus2':k.tolist(),
            'source_rate_kg_s':transfer['source_rate_kg_s'],'workpiece_arrival':values,
            'normalization':'per_actual_workpiece_area_per_second','T04_interface':'incident_element_flux_not_net_retained',
            'density_or_tooling_used':False,'film_thickness_or_n_k':'not_predicted'}

if __name__=='__main__':
    print(json.dumps(convert(json.loads(Path(sys.argv[1]).read_text())),indent=2,allow_nan=False))
