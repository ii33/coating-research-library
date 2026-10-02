#!/usr/bin/env python3
"""Load the deliberately limited T02-case-0.1 SI protocol and export CSV/JSON.
Example: python models/run_case.py data/synthetic_case.json --output benchmarks/results/example
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform
import numpy as np
from deposition_reference import (VERSION, PlanetaryPose, point_source, disk_source,
    disk_surface, ring_points, RectangleMask, deposit, thickness_metrics)


def run(path, output):
    path=Path(path); cfg=json.loads(path.read_text())
    if cfg['schema_version'] != 'T02-case-0.1': raise ValueError('Unsupported schema')
    expected={'length':'m','time':'s','angle':'rad','mass_rate':'kg/s','density':'kg/m3'}
    if cfg['units'] != expected: raise ValueError('Convert to exact SI unit contract first')
    p=cfg['pose']
    if p['kind'] != 'carrier_tilt_relative_spin': raise ValueError('Unsupported pose')
    pose=PlanetaryPose(p['orbit_radius_m'],p['height_m'],p['carrier_rpm'],p['spin_ratio_absolute_planar'],
                       p['phase_carrier_rad'],p['phase_relative_rad'],p['tilt_rad'])
    s=cfg['surface']
    if s['kind']=='ring':
        pts,normals=ring_points(s['radius_m'],s['point_count']); areas=None; sampling='ring_line_samples'
    elif s['kind']=='disk':
        pts,normals,areas=disk_surface(s['radius_m'],s['radial_order'],s['azimuth_nodes'],s.get('curvature_radius_m'))
        sampling='actual_surface_area_quadrature'
    else: raise ValueError('Unsupported surface')
    s=cfg['source']
    if s['kind']=='point': source=point_source(s['position_m'],s['normal'],s['emission_exponent'])
    elif s['kind']=='disk': source=disk_source(s['radius_m'],s['radial_order'],s['azimuth_nodes'],s['position_m'],np.asarray(s['orientation']),s['emission_exponent'])
    else: raise ValueError('Unsupported source')
    masks=[]
    for m in cfg['masks']:
        if m['kind']!='rectangle': raise ValueError('Only rectangular masks supported')
        masks.append(RectangleMask(m['center_m'],m['orientation'],m['half_width_m'],m['half_height_m'],m['thickness_m']))
    r=cfg['rate']
    if r['kind']!='harmonic_total_mass_rate': raise ValueError('Unsupported rate type')
    if r['mean_kg_s']<0 or sum(abs(c['amplitude_fraction']) for c in r['components'])>1:
        raise ValueError('Input rate must be nonnegative over entire continuous time interval')
    def rate(t):
        a=np.ones_like(t)
        for c in r['components']: a+=c['amplitude_fraction']*np.sin(2*np.pi*c['frequency_hz']*t+c['phase_rad'])
        return r['mean_kg_s']*a
    mat,t,nu=cfg['material'],cfg['time'],cfg['numerics']
    out=deposit(pose,pts,normals,source,rate,mat['effective_film_density_kg_m3'],t['start_s'],t['end_s'],
                panels=nu['panels'],order=nu['gauss_order'],sticking=mat['constant_sticking'],masks=masks,
                breakpoints=t['event_times_s'],time_chunk=nu['time_chunk'])
    prefix=Path(output); prefix.parent.mkdir(parents=True,exist_ok=True)
    with prefix.with_suffix('.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['point_id','local_x_m','local_y_m','local_z_m','normal_thickness_m','retained_areal_mass_kg_m2','area_weight_m2'])
        for i,p in enumerate(pts): w.writerow([i,*p,out['thickness_m'][i],out['retained_areal_mass_kg_m2'][i],'' if areas is None else areas[i]])
    report={'model_version':VERSION,'case_id':cfg['case_id'],'value_status':cfg['value_status'],
            'validation_status':'synthetic_example_only' if cfg['value_status']=='synthetic_assumption' else 'unvalidated_input',
            'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'model_sha256':hashlib.sha256(Path(__file__).with_name('deposition_reference.py').read_bytes()).hexdigest(),
            'python':platform.python_version(),'numpy':np.__version__,'sampling':sampling,
            'time_nodes':out['time_nodes'],'source_nodes':out['source_nodes'],
            'emitted_mass_kg':out['emitted_mass_kg'],'metrics':thickness_metrics(out['thickness_m'],areas),
            'actual_surface_integrated_mass_kg': None if areas is None else float(areas@out['retained_areal_mass_kg_m2'])}
    prefix.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('--output',required=True)
    a=ap.parse_args();print(json.dumps(run(a.input,a.output),ensure_ascii=False,indent=2))
