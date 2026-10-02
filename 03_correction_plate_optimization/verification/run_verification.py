#!/usr/bin/env python3
"""Hard assertions for the bounded T03 research reference, no real-machine data."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import sys,json
from pathlib import Path
from dataclasses import replace,asdict
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'models'))
from mask_design import *
checks=[]
def check(name,condition,detail=None):
    checks.append(dict(name=name,passed=bool(condition),detail=detail))
    assert condition,name
def raises(name,fn):
    try:fn()
    except ValueError:check(name,True);return
    check(name,False)

b=build_bundle(nr=3,na=8,panels=192)
p,n,a,pose,src,rate=case_parts(Config(),3,8,2,8)
ref=deposit(pose,p,n,src,rate,Config().density_kg_m3,0,Config().duration_s,panels=192,order=1)['thickness_m']*1e9
check('cached unmasked equals frozen T02',np.allclose(ref,b.base_nm,rtol=1e-13,atol=1e-13),float(np.max(abs(ref-b.base_nm))))
check('zero thickness config is supported',build_bundle(replace(Config(),mask_thickness_m=0),nr=1,na=4,panels=1).base_nm.min()>0)
check('source mass fractions normalized',np.isclose(src.fractions.sum(),1))
check('area weights normalized positive',np.all(b.area>0) and np.isclose(b.area.sum(),1))
check('normal thickness scales with source rate',np.allclose(build_bundle(replace(Config(),rate_kg_s=2e-6),nr=3,na=8,panels=192).base_nm,2*b.base_nm))
check('normal thickness scales inverse density',np.allclose(build_bundle(replace(Config(),density_kg_m3=6000),nr=3,na=8,panels=192).base_nm,.5*b.base_nm))
check('normal thickness scales with sticking',np.allclose(build_bundle(replace(Config(),sticking=.3),nr=3,na=8,panels=192).base_nm,.3*b.base_nm))
w=np.full(8,.04);h=b.masked(w)
check('passive mask cannot increase point thickness',np.all(h<=b.base_nm+1e-12))
check('passive mask nonnegative thickness',np.all(h>=-1e-12))
check('wider shape monotonic loss',np.all(b.masked(w*1.4)<=h+1e-12))
check('finite slab blocks superset of thin plane',np.all(h<=b.masked(w,0)+1e-12))
stream=evaluate_streaming(Config(),w,nr=3,na=8,panels=192,source_nr=2,source_na=8,azimuth_offset=0)
check('cached equals unpruned all-ray finite slab',np.allclose(stream['thickness_nm'],h,atol=1e-12))
# Random slab rays vs an independently parameterized frozen rectangular solid.
rng=np.random.default_rng(42);sx=rng.uniform(-.1,.4,2000);sy=rng.uniform(-.2,.2,2000);dx=rng.uniform(-2,2,2000);dy=rng.uniform(-2,2,2000)
a3=np.column_stack((sx-.5*dx,sy-.5*dy,np.zeros(2000)));b3=np.column_stack((sx+.5*dx,sy+.5*dy,np.ones(2000)))
rect=RectangleMask(np.array([(XKNOTS[0]+XKNOTS[-1])/2,0,.5]),np.eye(3),(XKNOTS[-1]-XKNOTS[0])/2,.04,.013)
check('trapezoid union slab equals T02 rectangle',np.array_equal(band_blocked(sx,sy,dx,dy,w,.013),rect.blocked(a3,b3)))
check('closed boundary counted opaque',bool(band_blocked(np.array([.1]),np.array([.04]),0,0,w,0)[0]))
check('outside lateral footprint transparent',not bool(band_blocked(np.array([.5]),np.array([0.]),0,0,w,0)[0]))
raises('negative thickness rejected',lambda:b.masked(w,-.001))
raises('larger cached slab override rejected',lambda:b.masked(w,.2))
# Concrete independent-review regression: cache empty for the thin slab.
cfg=replace(Config(),orbit_m=np.hypot(.1,.07),carrier_phase=np.arctan2(.07,.1),carrier_rpm=0,radius_m=.005,source_x_m=.1,source_y_m=.33,source_radius_m=0,rate_ripple=0)
bug=build_bundle(cfg,nr=1,na=4,panels=1,source_nr=1,source_na=1)
check('thicker-mask bug fixture has empty old cache',bug.numerics['cached_rays']==0)
raises('exact former silent wrong-answer repro now rejected',lambda:bug.masked(np.full(8,.1),.2))
check('rebuild thicker fixture produces all blocked',np.allclose(evaluate_streaming(replace(cfg,mask_thickness_m=.2),np.full(8,.1),nr=1,na=4,panels=1,source_nr=1,source_na=1,azimuth_offset=0)['thickness_nm'],0))
A,_,_=influence_matrix(b,6,4)
_,xe,ye=influence_matrix(b,6,4)
c0=np.linspace(0,1,24)
cv=evaluate_streaming(Config(),None,nr=3,na=8,panels=192,source_nr=2,source_na=8,azimuth_offset=0,thickness_m=0,opacity_grid=(xe,ye,c0))
check('streaming grayscale equals response matrix',np.allclose(cv['thickness_nm'],b.base_nm-A@c0,atol=1e-12))
check('influence nonnegative',np.all(A>=0))
check('cell losses sum no more than unmasked',np.all(A.sum(axis=1)<=b.base_nm+1e-12))
c=rng.uniform(0,1,A.shape[1]);check('opacity attenuation linear interpolation',np.allclose(b.base_nm-A@(.3*c),.7*b.base_nm+.3*(b.base_nm-A@c)))
P=radial_projection(b.rings,b.area);m=metric(h,b.base_nm,b.area,b.rings)
check('radial projection idempotent',np.allclose(P@P,P))
check('radial angular variance sum',abs(m['cv']**2-m['radial_cv']**2-m['angular_cv']**2)<1e-15)
check('uniform field metric zero',metric(np.ones(len(h)),np.ones(len(h)),b.area,b.rings)['cv']<1e-14)
raises('zero mean relative metrics rejected',lambda:metric(np.zeros(len(h)),b.base_nm,b.area,b.rings))
a=np.array([.2,.4,.8]);v=np.array([.6,.7,1.2]);cap=.15;x=project_box_throughput(v,a,cap)
check('throughput projection feasible',np.all((x>=0)&(x<=1)) and a@x<=cap+1e-12)
check('throughput projection idempotent',np.allclose(project_box_throughput(x,a,cap),x))
check('zero opacity allowed at zero loss budget',np.allclose(project_box_throughput(v,a,0),0,atol=1e-15))
free=(x>1e-9)&(x<1-1e-9);lam=(v[free]-x[free])/a[free]
check('projection KKT shared multiplier',np.ptp(lam)<1e-12)
raises('negative regularization rejected',lambda:optimize_relaxation(b,regularization=-1))
raises('invalid throughput ratio rejected',lambda:optimize_relaxation(b,min_throughput=1.01))
raises('nonfinite config rejected',lambda:build_bundle(replace(Config(),mask_z_m=float('nan'))))
r=optimize_relaxation(b,nx=6,ny=4,max_iterations=20000)
check('convex solver meets stated residual',r['converged'] and r['projected_gradient_inf']<=1e-8)
check('convex solver feasible',r['throughput_violation']<1e-12 and np.all((r['opacity']>=0)&(r['opacity']<=1)))
check('valid shape geometric screen',manufacturing(w)['passed'])
check('invalid shape screen',not manufacturing([1,2])['passed'])
check('too narrow shape rejected',not manufacturing(np.full(8,.001))['passed'])
check('slope curvature violation rejected',not manufacturing(np.array([.002,.1]*4))['passed'])
poly=export_polygon(w);check('polygon closed and finite',np.array_equal(poly[0],poly[-1]) and np.isfinite(poly).all())
check('infeasible requested throughput rejected by shape',not np.isfinite(shape_objective([b],w,min_throughput=1)[0]))
s=optimize_shape([b],np.full(8,.02),max_evaluations=65)
check('shape evaluation budget respected',s['evaluations']<=65)
check('pattern search score nonincreasing',np.all(np.diff([x['objective'] for x in s['trace']])<=1e-14))
# Correct generic two-material block solve, not an unverified paper inverse.
A1,B1,C1,D1=2.,3.,5.,7.;tH,tL=11.,13.
z=np.linalg.solve([[A1,B1],[C1,D1]],[tH,tL]);schur=(tH-B1/D1*tL)/(A1-B1/D1*C1)
check('two-material Schur solution agrees block solve',np.isclose(z[0],schur))
wrong1=(tH/B1-tL/D1)/(A1-C1);wrong2=(tH/A1-tL/C1)/(B1-D1)
check('published explicit Eq5 not generic block identity',not np.allclose(np.array([[A1,B1],[C1,D1]])@[wrong1,wrong2],[tH,tL]))
result={'version':'T03-mask-0.1','check_count':len(checks),'passed':all(x['passed'] for x in checks),'scope':'analytic and synthetic only','checks':checks}
(ROOT/'verification/verification_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':result['passed'],'check_count':len(checks)},ensure_ascii=False))
