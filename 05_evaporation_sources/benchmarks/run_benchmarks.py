"""Deterministic synthetic counterexamples, not data from a coating machine."""
import csv,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'models'));sys.path.insert(0,str(ROOT/'tests'))
from source_reference import *
from test_source_reference import thermal_parameters
OUT=ROOT/'benchmarks/results';OUT.mkdir(parents=True,exist_ok=True)

def grid(angles,H=.5):
    angles=np.asarray(angles);x=np.column_stack((H*np.tan(np.deg2rad(angles)),np.zeros(len(angles)),np.full(len(angles),H)))
    return x,np.tile([0.,0.,-1.],(len(x),1))
def predict(f,x,n):return flux_kg_m2_s(disk_source(0,exponent=f['exponent']),x,n,f['mass_rate_kg_s'])
def relative(pred,true):return {'rms_relative_percent':float(100*np.sqrt(np.mean((pred/true-1)**2))),'max_absolute_relative_percent':float(100*np.max(abs(pred/true-1)))}
def dumpcsv(name,headers,rows):
    with (OUT/name).open('w',newline='') as h:
        w=csv.writer(h);w.writerow(headers);w.writerows(rows)

rng=np.random.default_rng(20261002)
# Known-model fit with angular holdout and calibrated independent multiplicative noise.
train_angles=np.array([-35,-25,-15,-5,5,15,25,35.]);test_angles=np.array([-60,-50,-40,40,50,60.])
x,n=grid(train_angles);xt,nt=grid(test_angles)
truth=flux_kg_m2_s(disk_source(0,exponent=2.5),x,n,4e-6)
yt=flux_kg_m2_s(disk_source(0,exponent=2.5),xt,nt,4e-6)
y=truth*np.exp(rng.normal(0,.01,len(x)))
f=fit_point_logflux(x,n,y,.01);pred=predict(f,xt,nt)
res={'kind':'synthetic only','seed':20261002,'point_fit':{'truth_Q_kg_s':4e-6,'truth_n':2.5,'fit':f,'heldout':relative(pred,yt),'training_angles_deg':train_angles.tolist(),'heldout_angles_deg':test_angles.tolist()}}
dumpcsv('angular_holdout.csv',['angle_deg','true_kg_m2_s','predicted_kg_m2_s','relative_error_percent'],zip(test_angles,yt,pred,100*(pred/yt-1)))
# Parametric repeated-noise coverage conditional on exact point model. Not bootstrap of production data.
est=[];covered=[]
for k in range(400):
    ff=fit_point_logflux(x,n,truth*np.exp(rng.normal(0,.01,len(x))),.01)
    v=np.array([np.log(ff['mass_rate_kg_s']),ff['exponent']]);se=np.sqrt(np.diag(ff['covariance_logQ_n']))
    est.append(v);covered.append(abs(v-[np.log(4e-6),2.5])<=1.96*se)
res['conditional_noise_ensemble']={'replicates':400,'std_logQ_n':np.std(est,axis=0,ddof=1).tolist(),'marginal_95pct_coverage_logQ_n':np.mean(covered,axis=0).tolist(),'excludes':['geometry error','model discrepancy','density','sticking','correlated sensor drift']}
# Narrow-angle source data can hide a wrong extended-source geometry.
train2=np.linspace(-12,12,9);test2=np.array([-60,-50,-40,40,50,60.]);xa,na=grid(train2,H=.2);xb,nb=grid(test2,H=.2)
extended=disk_source(.10,nr=64,nphi=128,exponent=2.5)
ya=flux_kg_m2_s(extended,xa,na,4e-6);yb=flux_kg_m2_s(extended,xb,nb,4e-6)
wrong=fit_point_logflux(xa,na,ya,.01);train_pred=predict(wrong,xa,na);badpred=predict(wrong,xb,nb)
res['misspecified_point_for_disk']={'disk_radius_m':.1,'height_m':.2,'true_n':2.5,'fit':wrong,'training':relative(train_pred,ya),'heldout':relative(badpred,yb),'training_angles_deg':train2.tolist(),'heldout_angles_deg':test2.tolist()}
dumpcsv('misspecified_holdout.csv',['angle_deg','extended_truth_kg_m2_s','point_prediction_kg_m2_s','relative_error_percent'],zip(test2,yb,badpred,100*(badpred/yb-1)))
# Non-axisymmetric boat: withholding an entire azimuth diagnoses a false radial fit.
boat=rectangle_source(.16,.025,nx=96,ny=16,exponent=1.5)
xx,nn=grid(np.linspace(-35,35,15),H=.2);yy=xx.copy();yy[:,1]=xx[:,0];yy[:,0]=0
boatx=flux_kg_m2_s(boat,xx,nn,4e-6);boaty=flux_kg_m2_s(boat,yy,nn,4e-6)
boatfit=fit_point_logflux(xx,nn,boatx,.01)
res['withheld_azimuth_boat']={'dimensions_m':[.16,.025],'height_m':.2,'fit':boatfit,'training_x_plane':relative(predict(boatfit,xx,nn),boatx),'heldout_y_plane':relative(predict(boatfit,yy,nn),boaty)}
dumpcsv('boat_azimuth_holdout.csv',['offset_m','x_truth','y_truth','radial_fit_prediction'],zip(xx[:,0],boatx,boaty,predict(boatfit,yy,nn)))
# Deterministic source-height offsets are model/input uncertainty, not sensor noise.
height_cases=[]
for dz in [-.002,0,.002]:
    jg=flux_kg_m2_s(disk_source(0,exponent=2.5,center=(0,0,dz)),x,n,4e-6)
    fg=fit_point_logflux(x,n,jg,.01)
    height_cases.append({'source_height_offset_m':dz,'fit_Q_relative_bias_percent':100*(fg['mass_rate_kg_s']/4e-6-1),'fit_n_bias':fg['exponent']-2.5})
res['geometry_sensitivity']=height_cases
# Identifiability layout conditioning and uncertainty.
layouts={}
for name,angles in [('wide',train_angles),('narrow',np.linspace(-3,3,8))]:
    gx,gn=grid(angles);gj=flux_kg_m2_s(disk_source(0,exponent=2.5),gx,gn,4e-6)
    ff=fit_point_logflux(gx,gn,gj,.01)
    layouts[name]={'angles_deg':angles.tolist(),'condition':ff['scaled_design_condition'],'standard_errors_logQ_n':np.sqrt(np.diag(ff['covariance_logQ_n'])).tolist()}
try:fit_point_logflux([[0,0,1],[0,0,2]],[[0,0,-1],[0,0,-1]],[1,1])
except ValueError as e:layouts['axis_only']={'rejected':True,'reason':str(e)}
res['identifiability']=layouts
# Perfect on-axis QCM feedback cannot keep off-axis shape fixed when n changes.
angles=np.array([0,15,30,45,60.]);xc,nc=grid(angles)
old=flux_kg_m2_s(disk_source(0,exponent=1),xc,nc,4e-6)
new=flux_kg_m2_s(disk_source(0,exponent=3),xc,nc,2e-6) # axial Q*(n+1) identical
res['constant_qcm_shape_drift']={'angles_deg':angles.tolist(),'new_over_old':(new/old).tolist(),'Q_old_kg_s':4e-6,'Q_new_kg_s':2e-6,'n_old':1,'n_new':3}
dumpcsv('qcm_blind_shape_change.csv',['angle_deg','old_flux_kg_m2_s','new_flux_kg_m2_s','new_over_old'],zip(angles,old,new,new/old))
# Correlated source rate and footprint: averaging them independently is wrong.
base=disk_source(.06,nr=10,nphi=48,exponent=1)
xm,nm=grid(np.linspace(-35,35,21),H=.2)
N=120;ts=(np.arange(N)+.5)/N
Qs=4e-6*(1+.6*np.sin(2*np.pi*ts));allw=[];exact=np.zeros(len(xm));maskexact=np.zeros(len(xm))
for t,Q in zip(ts,Qs):
    src=gaussian_footprint(base,(.035*np.sin(2*np.pi*t),0),.012,.1);allw.append(src.fractions)
    exact+=flux_kg_m2_s(src,xm,nm,Q)/N
    # Static half-plane opening at z=.1, transmitting x>0. Exactly sourced geometry.
    s=src.nodes_m;u=(.1-s[None,:,2])/(xm[:,None,2]-s[None,:,2])
    hit=s[None,:,0]+u*(xm[:,None,0]-s[None,:,0]);v=(hit>0).astype(float)
    maskexact+=flux_kg_m2_s(src,xm,nm,Q,v)/N
meanw=np.mean(allw,axis=0);mean=Source(base.nodes_m,base.normals,meanw,1)
wrongmean=flux_kg_m2_s(mean,xm,nm,Qs.mean())
weightedw=np.sum(np.array(allw)*Qs[:,None],axis=0)/Qs.sum();weighted=Source(base.nodes_m,base.normals,weightedw,1)
correctmean=flux_kg_m2_s(weighted,xm,nm,Qs.mean())
wrongmask=flux_kg_m2_s(mean,xm,nm,Qs.mean(),v)
res['correlated_sweep_and_rate']={'independent_average':relative(wrongmean,exact),'mass_weighted_average':relative(correctmean,exact),'mask_absolute_error_over_peak_percent':float(np.max(abs(wrongmask-maskexact))/maskexact.max()*100),'note':'Static receiver and mask only; mass-weighted footprint identity need not hold with moving geometry.'}
dumpcsv('sweep_footprint.csv',['x_m','exact_flux','independent_average','mass_weighted_average','masked_exact','masked_independent_average'],zip(xm[:,0],exact,wrongmean,correctmean,maskexact,wrongmask))
# Recession at same intrinsic Q: aperture clips off-axis rays, cannot renormalize lost mass away.
angr=np.array([0,20,35,45,55,65.]);xr,nr=grid(angr,H=.3);rows=[]
for depth in [.005,.020,.040]:
    s=disk_source(.02,nr=20,nphi=80,center=(0,0,-depth));v=circular_aperture(s,xr,0,.025)
    jj=flux_kg_m2_s(s,xr,nr,4e-6,v)
    rows.extend(zip(np.full(len(xr),depth),angr,jj))
dumpcsv('recession_aperture.csv',['depth_m','receiver_angle_deg_from_initial_origin','flux_kg_m2_s'],rows)
res['recession']={'aperture_radius_m':.025,'emitting_disk_radius_m':.02,'model':'absorbing zero-thickness rim; same intrinsic Q; real hot walls may re-emit'}
# Synthetic, thermodynamically consistent single-phase material: deltaH/M == latent heat.
p=thermal_parameters();dt=.1;t=(np.arange(3000)+.5)*dt;P=np.where(t<120,100.,np.where(t<220,150.,0.))
h=lumped_history(p,P,dt);half=lumped_history(p,np.repeat(P,2),dt/2)
res['thermal_history']={'parameters':p,'dt_s':dt,'max_temperature_K':float(h['temperature_K'].max()),'evaporated_mass_kg':float(h['mass_kg'][0]-h['mass_kg'][-1]),'mass_balance_absolute_error_kg':float(abs(h['mass_kg'][0]-h['mass_kg'][-1]-np.sum(h['mass_rate_kg_s'])*dt)),'max_discrete_energy_residual_J':float(np.max(abs(h['energy_residual_J']))),'coarse_fine_max_temperature_difference_K':float(np.max(abs(h['temperature_K']-half['temperature_K'][::2]))),'coarse_fine_evaporated_mass_relative_difference':float(abs(np.sum(h['mass_rate_kg_s'])*dt/(np.sum(half['mass_rate_kg_s'])*dt/2)-1))}
dumpcsv('synthetic_thermal_history.csv',['time_s','power_W','temperature_K','remaining_mass_kg','evaporation_kg_s'],zip(t,P,h['temperature_K'][:-1],h['mass_kg'][:-1],h['mass_rate_kg_s']))
# Controlled repeatability checks, never interpreted as physical validation.
assert res['point_fit']['heldout']['max_absolute_relative_percent']<5
assert res['misspecified_point_for_disk']['training']['max_absolute_relative_percent']<1
assert res['misspecified_point_for_disk']['heldout']['max_absolute_relative_percent']>5
assert res['correlated_sweep_and_rate']['mass_weighted_average']['max_absolute_relative_percent']<1e-10
assert res['constant_qcm_shape_drift']['new_over_old'][0]==1
assert all(.90<c<.99 for c in res['conditional_noise_ensemble']['marginal_95pct_coverage_logQ_n'])
(OUT/'benchmark_summary.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(res,ensure_ascii=False,indent=2))
