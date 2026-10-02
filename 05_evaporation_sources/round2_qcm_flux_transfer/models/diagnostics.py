from pathlib import Path
import json
import numpy as np
from qcm_flux import *
from contract import convert
R=Path(__file__).resolve().parents[1]

def run():
 record=json.loads((R/'examples/synthetic_al.json').read_text());result=convert(record)
 unknown=convert(json.loads((R/'examples/actual_unknown.json').read_text()))
 f0=6045000.;fs=np.array([.999999,.999,.99,.95,.90])*f0
 finite_load=[{'f_over_f0':float(f/f0),'sauerbrey_kg_m2':float(mass_areal(f,f0,1.08,'sauerbrey')),'zmatch_kg_m2':float(mass_areal(f,f0,1.08))} for f in fs]
 x=np.array([[0,0,.5],[.1,0,.5],[0,.2,.5],[.3,0,.5],[0,.4,.5],[.2,.3,.5]]);ns=np.tile([0,0,-1],(6,1));Q=2e-6;n=2.4;a=.25;eta=.92
 y=eta*Q*point_kernel(x,ns,n,a)
 recovery=fit_source(x,ns,y,.01,capture=eta,loss='linear')
 fit_eta=fit_source(x,ns,y,.01,capture=.9,fit_capture=True,independent_source=(Q,.01),loss='linear')
 ranks={
 'single_qcm':rank_report(design_matrix(x[:1],ns[:1],n,a)),
 'diverse_monitors_known_capture':rank_report(design_matrix(x,ns,n,a)),
 'diverse_monitors_unknown_common_capture':rank_report(design_matrix(x,ns,n,a,fit_capture=True)),
 'diverse_monitors_plus_independent_source':rank_report(design_matrix(x,ns,n,a,fit_capture=True,independent_source_count=1))}
 # Exactly equal axial sensor observations under (Q,n) and (Q/2,2n+1).
 q0=2e-6;n0=1.;n1=3.;q1=q0/2;pos=np.array([[0,0,.5],[.5,0,.5]]);nor=np.tile([0,0,-1],(2,1))
 j0=q0*point_kernel(pos,nor,n0);j1=q1*point_kernel(pos,nor,n1)
 t=np.linspace(0,10,6);true_rate=1e-8;f=frequency_from_mass(1e-5+true_rate*t,f0,1.08);drift=2*t
 correct=rate_from_frequency(t,f+drift,f0,drift_hz=drift,z_ratio=1.08)
 uncorrected=rate_from_frequency(t,f+drift,f0,drift_hz=np.zeros(len(t)),z_ratio=1.08)
 yout=y.copy();yout[0]*=1.5
 robust=fit_source(x,ns,yout,.01,capture=eta,loss='soft_l1');linear=fit_source(x,ns,yout,.01,capture=eta,loss='linear')
 # Correlated uncertainty: log jQ, log etaQ, n, a. Sensor-workpiece ratio cancels Q.
 mean=np.array([np.log(y[1]),np.log(eta),n,a]);cov=np.diag([.02**2,.03**2,.12**2,.04**2]);cov[0,1]=cov[1,0]=.5*.02*.03
 def pred(v):
  k=point_kernel(x,ns,v[2],v[3]);return np.array([np.exp(v[0]-v[1])*k[4]/k[1]*N_A/MOLAR_MASS['Al']])
 uncertainty=propagate_covariance(pred,mean,cov)
 cluster=mixture_from_mass(2e-6,{'Al':.5,'Al2':.5},{'Al':{'Al':1},'Al2':{'Al':2}})
 gas=gas_impingement(1e-4,300,2*MOLAR_MASS['O'])
 reactive=retained_elements({'Al':2e19,'O2':1.5e19},{'Al':{'Al':1},'O2':{'O':2}},{'Al':1,'O2':1})
 return {'synthetic_contract':result,'actual_record':unknown,'finite_load_comparison':finite_load,
 'known_truth_recovery':recovery,'capture_with_independent_source':fit_eta,'identifiability':ranks,
 'blind_shape_change':{'sensor_equal_relative_difference':float(j1[0]/j0[0]-1),'off_axis_flux_ratio':float(j1[1]/j0[1]),'truth_A':[q0,n0],'truth_B':[q1,n1]},
 'drift_counterexample':{'true_rate_kg_m2_s':true_rate,'corrected_rate':correct['slope_kg_m2_s'],'uncorrected_rate':uncorrected['slope_kg_m2_s'],'unmodeled_drift_hz_s':2.,'consequence':'uncorrected negative net slope cannot be called source evaporation'},
 'occlusion_counterexample':{'known_visibility':.2,'inferred_source_ratio_if_ignored':.2,'fully_occluded':'division rejected; no source information'},
 'outlier_fit':{'truth':[Q,n,a],'robust':[robust['Q_kg_s'],robust['n'],robust['a']],'linear':[linear['Q_kg_s'],linear['n'],linear['a']],'not_guaranteed':'robust loss cannot fix coordinated drift, many occlusions or wrong model'},
 'uncertainty':uncertainty,'cluster_example':cluster,'gas_example_O2_particles_m2_s':gas,'reactive_atom_balance':reactive,
 'device_validation':'not_run','heavy_validation':'not_run','truth_origin':'declared synthetic inputs, no requested film thickness targets'}

if __name__=='__main__':
 result=run();(R/'verification/diagnostics.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(result,indent=2,allow_nan=False))
