"""One bounded, independent audit of the declared synthetic D/C/I contract.
Does not alter production/model code. Run from the round2 directory.
"""
from pathlib import Path
import sys, json, math, hashlib
from fractions import Fraction as F
from copy import deepcopy
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'models'))
import dual_coverage as m
c=m.load_config()
results={'input_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'models/dual_coverage.py',ROOT/'data/synthetic_contract.json',ROOT/'verification/test_reference.py',ROOT/'verification/PRE_REGISTERED_PROTOCOL.md']},'checks':{},'findings':{}}
# Derive independently with exact rational scalar arithmetic.
wH=F(1,4); wB=wH*(1-F(160,32)); wA=wB
rates={'D':{'carrier':wH,'sun':F(0),'output':wH*(1+F(120,36))},
       'C':{'carrier':wH,'ring':F(0),'compound':wB,'input':wH-F(40,88)*(wA-wH),'output':wH-F(32,64)*(wB-wH)},
       'I':{'carrier':wH,'output':F(-7,20)}}
for k,r in rates.items(): assert m.rates(c,k)==r
assert 120*(0-wH)+36*(rates['D']['output']-wH)==0
assert 160*(0-wH)-32*(wB-wH)==0
assert 88*(rates['C']['input']-wH)+40*(wB-wH)==0
assert 32*(wB-wH)+64*(rates['C']['output']-wH)==0
periods={'D':12,'C':8,'I':20}
for k,T in periods.items():
    for member in ['carrier','output']: assert (rates[k][member]*T).denominator==1
    # Fixed carrier period=4 means the minimum position return lies in this list.
    assert all((rates[k]['output']*t).denominator!=1 for t in range(4,T,4))
assert all((v*88).denominator==1 for v in rates['C'].values())
assert (rates['C']['input']*8).denominator!=1
assert all(any((v*t).denominator!=1 for v in rates['C'].values()) for t in range(8,88,8))
results['checks']['rates_rps']={k:{n:str(v) for n,v in r.items()} for k,r in rates.items()}
results['checks']['periods_s']={'workpiece':periods,'marked_full_C':88,'C_input_turns_at_8s':str(rates['C']['input']*8)}
R=.312; rb=.008*(160-32)/2; db=.008*(32+64)/2
xb=(R*R+rb*rb-db*db)/(2*R);yb=math.sqrt(rb*rb-xb*xb)
assert abs(math.hypot(xb,yb)-rb)<1e-14
assert abs(math.hypot(xb-R,yb)-db)<1e-14
assert .008*(88+40)/2==rb
assert abs(rb-db)<R<rb+db
assert R+.008*64/2<.008*160/2
results['checks']['C_pitch_geometry']={'compound_center_m':[xb,yb],'central_to_compound_m':rb,'compound_to_output_m':db,'output_outer_pitch_radius_m':R+.008*64/2,'ring_pitch_radius_m':.008*160/2,'upper_and_lower_axial_planes_required':True}
zero=deepcopy(c);zero['geometry']['carrier_rps']='0'
for k in ['D','C']: assert all(v==0 for v in m.rates(zero,k).values())
assert m.rates(zero,'I')['output']==F(-7,20)
x,n=m.pose(zero,'I',[0,1],[[.04,0,0]])
expected=np.array([[R+.04,0,.6],[R+.04*math.cos(-.7*math.pi),.04*math.sin(-.7*math.pi),.6]])
np.testing.assert_allclose(x[:,0],expected,atol=1e-15)
results['checks']['independent_absolute_output_zero_orbit']='pass'
# Analytic center-point roots; no model pose or model root finder used for oracle.
solver=m.EventIntegrator(c,'C'); p=np.array([0.,0.,0.]); t0,t1=0.,7.3; wc=math.pi/2
root_checks=[]
for axis,level in solver.thresholds:
    z=level/R
    if abs(z)>1: continue
    base=[math.acos(z),-math.acos(z)] if axis==0 else [math.asin(z),math.pi-math.asin(z)]
    exact=sorted(set(round((a+2*math.pi*k)/wc,14) for a in base for k in range(-3,5) if t0<=(a+2*math.pi*k)/wc<=t1))
    grid=R*(np.cos(wc*solver.ts) if axis==0 else np.sin(wc*solver.ts))
    found,width,amb=solver.roots(p,axis,level,grid)
    assert len(found)==len(exact),(axis,level,found,exact)
    err=max([min(abs(a-b) for b in found) for a in exact] or [0.])
    assert err<=solver.root_tol
    root_checks.append({'axis':axis,'level':level,'count':len(exact),'max_error_s':err,'ambiguous':amb})
results['checks']['analytic_center_roots']=root_checks
# Independent midpoint kernel: closed-form horizontal intersections with separate rays.
def independent_midpoint(top,points,N=32771):
    h=7.3/N; t=(np.arange(N)+.5)*h
    pc=2*np.pi*.25*t; pw=2*np.pi*float(rates[top]['output'])*t
    X=np.empty((N,len(points),3))
    X[:,:,0]=R*np.cos(pc)[:,None]+np.cos(pw)[:,None]*points[:,0]-np.sin(pw)[:,None]*points[:,1]
    X[:,:,1]=R*np.sin(pc)[:,None]+np.sin(pw)[:,None]*points[:,0]+np.cos(pw)[:,None]*points[:,1]
    X[:,:,2]=.6
    S=np.array(c['vapor']['position_L_m']); rv=X-S; dist2=np.sum(rv*rv,axis=-1)
    vap=2e19*.6**2*.6**2/(dist2**2)
    D=np.array([.8,0,.6]); B=np.array([-.62,.04,0]); ri=X-B
    along=ri@D; a=ri@np.array([.6,0,-.8]); b=ri[:,:,1]
    ions=2e18*.6*np.exp(-(a*a+b*b)/(2*.13**2))*(along>0)
    vap*=((t>=.55)&(t<6.55))[:,None]
    out={}
    for case,names in c['cases'].items():
        v=vap.copy(); i=ions.copy()
        for name in names:
            plate=c['plates'][name]; O=np.array(plate['origin_L_m']); hx,hy=plate['half_width_m']
            lam=(O[2]-S[2])/(.6-S[2]); hv=S+lam*(X-S)
            v*=~((0<lam)&(lam<1)&(np.abs(hv[:,:,0]-O[0])<=hx)&(np.abs(hv[:,:,1]-O[1])<=hy))
            distance=(.6-O[2])/.6; hi=X-distance*D
            i*=~((distance>0)&(distance<along)&(np.abs(hi[:,:,0]-O[0])<=hx)&(np.abs(hi[:,:,1]-O[1])<=hy))
        out[case]=np.stack([v.sum(axis=0)*h,i.sum(axis=0)*h,(i.sum(axis=0)*h)*100*1.602176634e-19,((i>0)&(v==0)).sum(axis=0)*h],axis=-1)
    return out
pts=np.array([[0,0,0],[.03,.02,0],[-.04,.04,0]])
comparisons=[]
for top in 'DCI':
    reference=m.EventIntegrator(c,top).integrate(pts)
    independent=independent_midpoint(top,pts)
    for case in reference:
        rel=np.abs(independent[case][:,:3]-reference[case][:,:3])/reference[case][:,:3]
        abst=np.abs(independent[case][:,3]-reference[case][:,3])
        assert rel.max()<.003 and abst.max()<.003
        comparisons.append({'topology':top,'case':case,'max_relative_flux_integral_difference':float(rel.max()),'max_ion_only_difference_s':float(abst.max())})
results['checks']['independent_midpoint_32771_comparisons']=comparisons
# Single incidence projection and energy accounting.
d=np.array([.8,0,.6]); x=np.array([[np.array(c['ion']['origin_L_m'])+d]])
g_beam=m.flux_at(c,[1.],x,np.array([[-d]]),'none')[1].item()
g_down=m.flux_at(c,[1.],x,np.array([[[0,0,-1]]]),'none')[1].item()
assert abs(g_down/g_beam-.6)<1e-15
out=m.output_values(c,np.array([[0.,1.,100*m.E_CHARGE,1.],[4.,2.,200*m.E_CHARGE,0.]]))
assert np.isnan(out['ion_to_net_atom_ratio'][0]) and out['ion_to_net_atom_ratio'][1]==.5
assert out['eV_per_net_atom'][1]==50
results['checks']['projection_energy_zero_denominator']='pass; one cosine factor, fixed 100 eV, exact zero/negative denominator guarded'
# Counterexamples to two limiting interfaces; intentionally not asserted as core failures.
psi=2*np.pi*float(rates['D']['output'])*2
p=np.array([[-.059*np.cos(psi),.059*np.sin(psi),0.]])
x,n=m.pose(c,'D',[2.],p);gv=m.flux_at(c,[2.],x,n,'ion_only',uniform_vapor=True)[0].item()
plate=c['plates']['ion_plate']; O=np.array(plate['origin_L_m']); hx,hy=plate['half_width_m']
vertical_hit=x[0,0].copy();vertical_hit[2]=O[2]
physical_blocked=(abs(vertical_hit[0]-O[0])<=hx and abs(vertical_hit[1]-O[1])<=hy)
results['findings']['uniform_parallel_vapor_visibility']={'local_point':p[0].tolist(),'time_s':2.,'world_point':x[0,0].tolist(),'model_flux':gv,'vertical_ray_hit':vertical_hit.tolist(),'physical_vertical_ray_blocked':bool(physical_blocked),'status':'counterexample' if gv>0 and physical_blocked else 'not_reproduced'}
try:
    zsolver=m.EventIntegrator(zero,'D'); ze=zsolver.point_events(np.array([.023,0,0]))
    results['findings']['stationary_boundary']={'status':'completed','events':len(ze)}
except RuntimeError as e:
    results['findings']['stationary_boundary']={'status':'counterexample','carrier_rps':0,'point':[.023,0,0],'message':str(e),'subdivisions':zsolver.subdivision_count}
# Confirm the constrained repair rather than implying unsupported masked uniform integration.
assert gv == 0. and physical_blocked
try:
    m.EventIntegrator(c,'D').integrate(p,cases=['ion_only'],uniform_vapor=True)
except NotImplementedError:
    results['checks']['uniform_masked_event_integration']='explicitly unsupported, as required by current interface'
else:
    raise AssertionError('Masked uniform-vapor event solver must not silently reuse point-source events')
for top in 'DC':
    zint=m.EventIntegrator(zero,top).integrate(np.array([[.023,0,0]]),cases=['vapor_only'])['vapor_only'][0]
    assert np.isfinite(zint).all()
    instantaneous=m.fields(zero,top,[1.],np.array([[.023,0,0]]),'vapor_only')[0,0]
    np.testing.assert_allclose(zint[:3],instantaneous[:3]*np.array([6.,7.3,7.3]),rtol=1e-14)
results['checks']['stationary_D_C_integrals']='finite and consistent with constant flux times exact open-gate duration'
# A tangent stresses floating-point arithmetic rather than just crossing roots.
ts=m.EventIntegrator(c,'D');cand,width,amb=ts.roots(np.zeros(3),0,R,R*ts.cs)
assert min(abs(v) for v in cand)<1e-10 and min(abs(v-4) for v in cand)<1e-10
results['checks']['tangent_root_limit']={'exact_roots_s':[0.,4.], 'candidate_count':len(cand),'ambiguous_tiny_brackets':amb,'sum_candidate_width_s':float(width),'max_candidate_distance_from_exact_root_s':float(max(min(abs(v),abs(v-4)) for v in cand)),'conclusion':'No missed tangent in this example; candidate width is not a floating-point root-error certificate.'}
results['findings']['resolution']='Both original defects were corrected by the owner during this same narrow review and locally rechecked. No core files edited by reviewer.'
results['scope']='Synthetic fixed geometry only. C/I conditional_text_grounded; source-figure gate unsupported. No source browsing, full-library review, dense spatial convergence rerun, real-machine or manufacturing qualification.'
path=ROOT/'reviews/independent_math_check_results.json';path.write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(results,indent=2,ensure_ascii=False))
