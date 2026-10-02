#!/usr/bin/env python3
"""Deterministic synthetic checks. Fails with nonzero exit if any assertion fails."""
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'models'))
from deposition_reference import (VERSION, Source, point_source, disk_source, rotation_y,
    rotation_z, PlanetaryPose, RectangleMask, transfer_kernel, time_quadrature,
    deposit, disk_surface, ring_points)

results = []
def check(name, error, tolerance, evidence):
    error = float(error)
    results.append(dict(name=name, error=error, tolerance=tolerance,
                        passed=bool(error <= tolerance), evidence=evidence))

def relative(a,b):
    return np.max(np.abs(np.asarray(a)-np.asarray(b))) / max(float(np.max(np.abs(b))),1e-300)

# Analytic hemisphere angular normalization, including isotropic hemispheric p=0.
u,w=np.polynomial.legendre.leggauss(64); mu=(u+1)/2
for p in (0,1,4,20):
    val=(p+1)*np.sum(w/2*mu**p)
    check(f'angular_normalization_p{p}',abs(val-1),2e-13,'Integral f dOmega=(p+1) integral_0^1 mu^p dmu=1')

src=point_source(); points=np.array([[0,0,1.],[.2,0,1.],[.7,0,1.]])
normals=np.tile([0,0,-1.],(3,1))
k=transfer_kernel(points,normals,src)
exact=1/(np.pi*(1+points[:,0]**2)**2)
check('parallel_plane_analytic_profile',relative(k,exact),1e-14,'K=h^2/[pi(h^2+r^2)^2], h=1m')
check('inverse_square_scale',relative(transfer_kernel(points*3,normals,src), k/9),1e-14,'All source-target separations scaled by 3')
check('backside_target_zero',np.max(transfer_kernel(points,-normals,src)),0,'Receiver normal reversed')
check('backside_emission_p0_zero',np.max(transfer_kernel(-points,-normals,point_source(exponent=0))),0,'Isotropic hemisphere must not emit backward: avoid 0**0')

# A receiving disk captures R^2/(h^2+R^2) of a Lambert point-source mass rate.
R=2.; h=.8; u,w=np.polynomial.legendre.leggauss(128); r=R*np.sqrt((u+1)/2)
x=np.stack((r,r*0,r*0+h),axis=-1)
capture=np.pi*R*R*np.sum(w/2*transfer_kernel(x,np.tile([0,0,-1.],(len(r),1)),src))
check('capture_mass_conservation_disk',abs(capture-R*R/(h*h+R*R)),1e-12,'Integral K dA equals finite disk capture fraction <=1')

# Uniform Lambert emitting disk observed on axis: K=1/[pi(h^2+a^2)].
a=.12; h=.4
kd=transfer_kernel(np.array([[0,0,h]]),np.array([[0,0,-1.]]),disk_source(a,12,32))[0]
check('extended_disk_on_axis',relative(kd,1/(np.pi*(h*h+a*a))),1e-13,'Analytic area integral of a uniform disk, fixed total emitted mass rate')
small=disk_source(1e-6,4,12)
check('extended_source_point_limit',relative(transfer_kernel(points,normals,small),k),5e-12,'Uniform source radius ->0 at fixed total kg/s')

# Common rigid transform of source, target, normals and mask preserves transfer.
Q=rotation_z(.37)@rotation_y(.54); shift=np.array([.2,-.3,.7])
sr=Source(src.positions_m@Q.T+shift,src.normals@Q.T,src.fractions)
check('global_rigid_transform_invariance',relative(transfer_kernel(points@Q.T+shift,normals@Q.T,sr),k),2e-14,'Transforms positions and both source/receiver normals')

# Actual mask plane and finite thickness, not projected target-plane clipping.
mask=RectangleMask([.2,0,.5],np.eye(3),.01,.1)
moved=RectangleMask([.2,0,.25],np.eye(3),.01,.1)
target=np.array([[.4,0,1.]])
check('mask_at_actual_plane_blocked',transfer_kernel(target,[[0,0,-1]],src,[mask])[0],0,'Ray x=.2 at z=.5 intersects rectangle')
check('mask_height_changes_shadow',relative(transfer_kernel(target,[[0,0,-1]],src,[moved]),transfer_kernel(target,[[0,0,-1]],src)),1e-14,'Same xy silhouette at z=.25 no longer intersects')
front=RectangleMask([0,0,.5],np.eye(3),.05,.1,0)
solid=RectangleMask([0,0,.5],np.eye(3),.05,.1,.2)
sa=np.array([[-.4,0,0]]); xb=np.array([[.6,0,1]])
check('thick_mask_side_intersection',float(not(solid.blocked(sa,xb)[0] and not front.blocked(sa,xb)[0])),0,'Oblique segment hits finite box side but misses central thin plane')
behind=RectangleMask([0,0,2],np.eye(3),10,10)
check('mask_outside_segment_ignored',float(behind.blocked([[0,0,0]],[[0,0,1]])[0]),0,'Occluder behind target is not on source-target segment')
# Rotating the entire masked configuration too.
maskQ=RectangleMask(Q@mask.center_m+shift,Q,.01,.1)
check('masked_rigid_transform_invariance',relative(transfer_kernel(target@Q.T+shift,np.array([[0,0,-1]])@Q.T,sr,[maskQ]),[0.]),0,'Mask center and basis also transformed')

inactive=Source([[0,0,0],[0,0,1]],[[0,0,1],[0,0,1]],[1.,0.])
check('zero_weight_source_node_ignored',relative(transfer_kernel([[0,0,1]],[[0,0,-1]],inactive),[1/np.pi]),1e-14,'Inactive source node coincident with target must not create a singularity')

# Source penumbra: symmetric source gives exactly half on-axis visibility for half-plane.
wide=RectangleMask([5.,0,.5],np.eye(3),5.,5.)
kopen=transfer_kernel([[0,0,1]],[[0,0,-1]],disk_source(.1,8,40))[0]
khalf=transfer_kernel([[0,0,1]],[[0,0,-1]],disk_source(.1,8,40),[wide])[0]
check('extended_source_half_penumbra',abs(khalf/kopen-.5),2e-14,'Symmetry of disk and half-plane mask gives visibility-weighted half flux')

# Exact kinematics closure and tilted-frame normals.
local,nlocal=ring_points(.15,16)
for zp,period in ((36,12.),(37,148.)):
    pose=PlanetaryPose(.312,1.,15.,1+120/zp)
    xp,np_=pose.evaluate([0.,period],local,nlocal)
    check(f'pose_closure_{zp}',np.max(np.abs(xp[1]-xp[0])),1e-13,'Fixed 120 tooth external sun direct mesh, no slip; conditional ideal topology')
tiltpose=PlanetaryPose(.31,1,15,1+120/36,tilt_rad=.17)
x,n=tiltpose.evaluate([0,.13,.82],local,nlocal)
check('tilted_normals_unit',np.max(abs(np.linalg.norm(n,axis=-1)-1)),1e-14,'Both position and normal use common rotation chain')
check('rigid_distance_preservation',np.max(abs(np.linalg.norm(x[:,0]-x[:,5],axis=-1)-np.linalg.norm(local[0]-local[5]))),1e-14,'Local inter-point distances unchanged')

# Absolute seconds, rate kg/s, density kg/m3 and a known shutter event.
stationary=PlanetaryPose(0,1,0,1)
one=np.array([[0.,0,0]]); nn=np.array([[0.,0,-1]])
args=(stationary,one,nn,src)
a1=deposit(*args,lambda t:1e-6+0*t,3000,0,1,panels=1,order=1)
a60=deposit(*args,lambda t:1e-6+0*t,3000,0,60,panels=1,order=1)
check('duration_seconds_si',relative(a60['thickness_m'],60*a1['thickness_m']),1e-14,'60s at fixed kg/s yields 60x thickness, not normalized mean flux')
expected=1e-6/(3000*np.pi)
check('rate_density_units',relative(a1['thickness_m'],[expected]),1e-14,'kg/s * s * 1/m2 / (kg/m3) = m')
linear=deposit(*args,lambda t:1e-6*(1+.2*t),3000,0,3,panels=1,order=1)
check('linear_rate_exact',relative(linear['thickness_m'],[expected*(3+.1*9)]),1e-14,'Midpoint integrates affine temporal rate exactly at fixed geometry')
event=.37
shut=deposit(*args,lambda t:1e-6*(t>=event),3000,0,1,panels=1,order=1,breakpoints=[event])
check('shutter_event_split',relative(shut['thickness_m'],[expected*(1-event)]),1e-14,'Quadrature intervals explicitly split at known discontinuity')

# Area integration on curved surface and normal-vs-projected area distinction.
p,n,area=disk_surface(.15,12,48,curvature_radius_m=.5)
exact_area=2*np.pi*.5*(.5-np.sqrt(.5**2-.15**2))
check('spherical_cap_area',relative(area.sum(),exact_area),2e-13,'Weights include 1/|nz| Jacobian; analytic spherical cap area')
check('spherical_normals_unit',np.max(abs(np.linalg.norm(n,axis=-1)-1)),1e-14,'Normal (x/R,y/R,-sqrt(R2-r2)/R)')

# Input guards to prevent physically impossible parameters silently passing.
for name,func in [('negative_density',lambda:deposit(*args,lambda t:1e-6,0,0,1)),
                  ('negative_rate',lambda:deposit(*args,lambda t:-1e-6,3000,0,1)),
                  ('invalid_source_fraction',lambda:Source([[0,0,0]],[[0,0,1]],[2.])),
                  ('source_target_coincidence',lambda:transfer_kernel([[0,0,0]],[[0,0,-1]],src))]:
    caught=False
    try: func()
    except ValueError: caught=True
    check(name,float(not caught),0,'Invalid input must raise ValueError')

# Smooth exact reference independent of quadrature implementation: integral exp(t).
errors=[]
for panels in (8,16,32,64):
    t,w=time_quadrature(0,1,panels,1)
    errors.append(abs(w@np.exp(t)-(np.e-1)))
ratio=errors[-2]/errors[-1]
check('midpoint_order_two',abs(ratio-4),.002,'Refinement halves dt, smooth exp(t) integral error should drop by ~4')

report={'model_version':VERSION,'validation_scope':'synthetic analytical/code verification only; no physical-machine data',
        'python_version':platform.python_version(),'numpy_version':np.__version__,
        'checks':results,'passed':all(x['passed'] for x in results),
        'passed_count':sum(x['passed'] for x in results),'total_count':len(results),
        'midpoint_exp_errors':errors,
        'model_sha256':hashlib.sha256((ROOT/'models/deposition_reference.py').read_bytes()).hexdigest()}
out=ROOT/'verification/verification_results.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
if not report['passed']: sys.exit(1)
