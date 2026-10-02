#!/usr/bin/env python3
"""Reproduce synthetic timing/error, aliasing, gear and identifiability examples.
All numbers are made-up demonstration inputs, never device calibration data.
"""
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'models'))
from deposition_reference import *
OUT=ROOT/'benchmarks/results'; OUT.mkdir(parents=True,exist_ok=True)

def dump_csv(name, rows):
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader();w.writerows(rows)

def err(a,b): return float(np.max(abs(a-b))/np.mean(b))

def timed(fun,repeats=3):
    fun()  # warm-up; do not report as a timing sample
    times=[]
    for _ in range(repeats):
        t=time.perf_counter(); out=fun();times.append(time.perf_counter()-t)
    return out,float(np.median(times)),float(np.min(times)),float(np.max(times))

pose=PlanetaryPose(.312,1.,15.,1+120/36,phase_carrier_rad=.23,phase_relative_rad=.71)
p,n=ring_points(.15,72); src=point_source((.1,0,0),exponent=2.)
rate=lambda t:1e-6*(1+.2*np.sin(2*np.pi*.25*t+.4)+.05*np.cos(2*np.pi*1.7*t))
base=dict(pose=pose,local_points_m=p,local_normals=n,source=src,total_rate_kg_s=rate,
          density_kg_m3=3000.,t0_s=0.,t1_s=7.3)
ref=deposit(**base,panels=8192,order=4)['thickness_m']
ref2=deposit(**base,panels=16384,order=4)['thickness_m']
rows=[]
for order in (1,4):
    for panels in (16,32,64,128,256,512):
        result,sec,lo,hi=timed(lambda:deposit(**base,panels=panels,order=order))
        rows.append(dict(case='smooth_dynamic_point',order=order,panels=panels,time_nodes=result['time_nodes'],
                         max_abs_error_over_reference_mean=err(result['thickness_m'],ref2),
                         median_seconds=sec,min_seconds=lo,max_seconds=hi))
dump_csv('time_accuracy.csv',rows)

# Discontinuous mask: numerical agreement is empirical, not a rigorous error bound.
mask=RectangleMask([.08,0,.5],np.eye(3),.012,1.)
maskbase={**base,'masks':[mask],'total_rate_kg_s':lambda t:1e-6+0*t}
mr=deposit(**maskbase,panels=32768,order=4)['thickness_m']
mr2=deposit(**maskbase,panels=65536,order=4)['thickness_m']
mrows=[]
for order in (1,4):
    for panels in (64,256,1024,4096):
        r,sec,lo,hi=timed(lambda:deposit(**maskbase,panels=panels,order=order))
        mrows.append(dict(case='unsplit_moving_shadow',order=order,panels=panels,time_nodes=r['time_nodes'],
                          max_abs_error_over_reference_mean=err(r['thickness_m'],mr2),median_seconds=sec,min_seconds=lo,max_seconds=hi))
dump_csv('mask_time_accuracy.csv',mrows)

# Extended-source quadrature across an off-center opaque edge.
xx=np.linspace(-.1,.1,11); targets=np.stack((xx,xx*0,xx*0+.4),axis=-1)
ns=np.tile([0.,0.,-1.],(len(xx),1)); sm=RectangleMask([5.015,0,.2],np.eye(3),5.,5.)
source_ref=transfer_kernel(targets,ns,disk_source(.08,128,512),[sm])
source_ref2=transfer_kernel(targets,ns,disk_source(.08,192,768),[sm])
srows=[]
for nr,na in ((2,8),(4,16),(8,32),(16,64),(32,128),(64,256)):
    ss=disk_source(.08,nr,na)
    r,sec,lo,hi=timed(lambda:transfer_kernel(targets,ns,ss,[sm]))
    srows.append(dict(radial_order=nr,azimuth_nodes=na,total_source_nodes=nr*na,
                      max_abs_error_over_reference_mean=err(r,source_ref2),median_seconds=sec))
dump_csv('extended_source_shadow_accuracy.csv',srows)

# Workpiece spatial quadrature: compare true area-weighted average, not just a ring.
sprows=[]
def spatial(nr,na):
    sp,sn,area=disk_surface(.15,nr,na,curvature_radius_m=.8)
    d=deposit(**{**base,'local_points_m':sp,'local_normals':sn,'t1_s':1.3},panels=128,order=4)['thickness_m']
    return np.sum(area*d)/np.sum(area),len(sp),thickness_metrics(d,area)
sref,_,_=spatial(24,96)
for nr,na in ((2,8),(4,16),(8,32),(12,48)):
    (v,c,metrics),sec,lo,hi=timed(lambda:spatial(nr,na))
    sprows.append(dict(radial_order=nr,azimuth_nodes=na,points=c,mean_thickness_m=v,
                       relative_area_mean_error=abs(v-sref)/sref,median_seconds=sec,
                       sampled_peak_to_valley=metrics['peak_to_valley_over_mean']))
dump_csv('surface_area_accuracy.csv',sprows)

# Adversarial same-error nested quadrature: both N=16 and N=32 miss 64 cycles.
alias=[]
for panels in (16,32,64,65,128,257):
    t,w=time_quadrature(0,1,panels,1)
    estimate=w@(1+.3*np.cos(2*np.pi*64*t))
    alias.append(dict(panels=panels,estimated_integral=float(estimate),analytic_integral=1.,relative_error=float(abs(estimate-1))))
dump_csv('quadrature_aliasing.csv',alias)

# 36/37 controlled and mechanically coupled cases. Constant total kg/s and same T.
# Standard external spur module .004m implies a36=.312m and a37=.314m.
gear=[]
for duration in (.75,7.3,12.,60.,148.):
    for dynamic in (False,True):
        for zp,geometry in ((36,'standard_center_distance'),(37,'fixed_center_counterfactual'),(37,'standard_center_distance')):
            orbit=.004*(120+zp)/2 if geometry=='standard_center_distance' else .312
            gp=PlanetaryPose(orbit,1.,15.,1+120/zp,phase_carrier_rad=.23,phase_relative_rad=.71)
            gr=(lambda t:1e-6*(1+.2*np.sin(2*np.pi*.25*t+.4))) if dynamic else (lambda t:1e-6+0*t)
            g=deposit(gp,p,n,src,gr,3000,0,duration,panels=max(128,int(duration*64)),order=4)
            metrics=thickness_metrics(g['thickness_m'])
            gear.append(dict(duration_s=duration,dynamic_rate=dynamic,planet_teeth=zp,geometry=geometry,orbit_radius_m=orbit,
                             mean_nm=metrics['mean_m']*1e9,ring_pv_over_mean=metrics['peak_to_valley_over_mean'],
                             ring_cv=metrics['coefficient_of_variation'],emitted_mass_kg=g['emitted_mass_kg']))
dump_csv('gear_center_distance_confound.csv',gear)

# Static axisymmetric plane: joint emission and empirical incidence exponents degenerate.
# h(r) = A * mu^(p+1+q)/r^2, with A absorbing normalization and instrument scale.
r=np.linspace(0,.4,41); h=1.; mu=h/np.sqrt(h*h+r*r)
J=np.column_stack((np.ones_like(mu),np.log(mu),np.log(mu)))
sv=np.linalg.svd(J,compute_uv=False)
# Calibration magnitude: log h = log(rate)+log(sticking)-log(density)+log(K)+log(time).
Jscale=np.column_stack((np.ones_like(mu),np.ones_like(mu),-np.ones_like(mu)))
svscale=np.linalg.svd(Jscale,compute_uv=False)
ident=dict(exponent_log_jacobian_columns=['log_amplitude','emission_exponent','extra_incidence_exponent'],
           singular_values=sv.tolist(),rank=int(np.linalg.matrix_rank(J)),
           sample_count=len(r),scale_columns=['log_rate','log_sticking','log_density'],
           scale_singular_values=svscale.tolist(),scale_rank=int(np.linalg.matrix_rank(Jscale)),
           interpretation='Synthetic structural degeneracy; fitting more points in the same geometry cannot remove equal Jacobian columns.')
(OUT/'identifiability.json').write_text(json.dumps(ident,indent=2)+'\n')

summary=dict(model_version=VERSION,case_status='synthetic_assumptions_only',python=platform.python_version(),numpy=np.__version__,
             platform=platform.platform(),cpu_count=os.cpu_count(),timing_method='perf_counter; warm-up once; median/min/max of 3 sequential trials; no claimed cross-machine speedup',
             smooth_reference_refinement_error=err(ref,ref2),mask_reference_refinement_error=err(mr,mr2),
             extended_source_reference_refinement_error=err(source_ref,source_ref2),
             smooth_reference_panels=16384,smooth_reference_order=4,mask_reference_panels=65536,mask_reference_order=4,
             extended_source_reference_nodes=192*768,point_count=72,
             model_sha256=hashlib.sha256((ROOT/'models/deposition_reference.py').read_bytes()).hexdigest())
(OUT/'benchmark_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
print('Saved CSVs and identifiability.json to',OUT)
