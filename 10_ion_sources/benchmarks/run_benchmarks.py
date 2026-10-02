"""Synthetic T10 examples. Not apparatus settings and not fitted material data."""
from pathlib import Path
import json,sys,math,csv
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'models'))
from ion_assist_reference import *
P=Path(__file__).resolve().parents[1]
SPECIES=[Species('synthetic Ar+',.85,1,90),Species('synthetic Ar2+',.15,2,180)]
base=beam_moments(.48,SPECIES)
growth=atom_flux_from_net_growth(.35,2.1,60.0843,3)
norm=normalize_assist(base,growth['net_atom_flux_m2_s'])
R={'disclaimer':'SYNTHETIC ONLY; not a production recipe, empirical fit or equipment qualification',
 'baseline':{'inputs':{'current_density_A_m2':.48,'species_particle_fractions':[.85,.15],'charge_numbers':[1,2],'energies_eV':[90,180],'rate_nm_s':.35,'assumed_film_density_g_cm3':2.1,'stoichiometric_formula_mass_g_mol':60.0843,'atoms_per_formula':3,'exposure_s':600},'beam':base,'growth':growth,'normalized':norm,'ion_fluence_m2':600*base['charged_particle_flux_m2_s'],'kinetic_energy_J_m2':600*base['incident_kinetic_power_W_m2'],'net_thickness_nm':210}}
# Neutralization is not modeled as recombination. This separate demo is charge exchange.
cx=charge_exchange_split(1e19,.01,300,.5,1e-19)
R['charge_exchange']={**cx,'inputs':{'incident_flux_m2_s':1e19,'pressure_Pa':.01,'gas_temperature_K':300,'path_m':.5,'SYNTHETIC_cross_section_m2':1e-19},'ion_plus_neutral_flux_ratio':(cx['energetic_ion_flux_m2_s']+cx['fast_neutral_flux_m2_s'])/1e19,'scope':'one pass forward energy retained; slow ions excluded; no real cross section claimed'}
# Independent mixture-count identity and formula normalization checks.
R['single_charge_assumption_error']={'assumed_over_true_particle_flux':base['mean_charge_number'],'percent_overestimate':100*(base['mean_charge_number']-1)}
R['formula_vs_atom']={'eV_per_formula':norm['incident_eV_per_net_atom']*3,'eV_per_total_atom':norm['incident_eV_per_net_atom']}
# Simple resputtering, incident and net denominators differ.
arrival=1e19;ions=2e18;Y=.7;net=simple_resputter_net_flux(arrival,ions,Y)
R['resputter']={'assumed_arrival_m2_s':arrival,'assumed_ion_m2_s':ions,'assumed_constant_yield':Y,'net_m2_s':net,'ion_to_arrival_ratio':ions/arrival,'ion_to_net_ratio':ions/net,'erosion_at_yield_6_m2_s':simple_resputter_net_flux(arrival,ions,6)}
R['time_weighting_counterexample']={'ion_flux_arbitrary':[1,1],'net_atom_flux_arbitrary':[1,9],'equal_bins':True,'ratio_of_integrals':ratio_of_integrals([1,1],[1,9],[1,1]),'mean_of_ratios':(1+1/9)/2}
# lognormal input model avoids negative densities/rates; rho-rate correlation is deliberate.
rng=np.random.default_rng(1042);n=60000
sig=np.array([.06,.04,.03,.02]) # log standard deviations j,rate,rho,z
cov=np.diag(sig**2);cov[1,2]=cov[2,1]=-.5*sig[1]*sig[2]
noise=rng.multivariate_normal(np.zeros(4),cov,n)
rr=np.exp(noise[:,0]-noise[:,1]-noise[:,2]-noise[:,3])
analytic=relative_ratio_uncertainty(*[.06,.04,.03,.02],corr_rate_rho=-.5)
R['uncertainty']={'distribution':'correlated lognormal, medians at inputs; zbar uncertainty treated continuous approximation','samples':n,'seed':1042,'log_input_standard_deviations':sig.tolist(),'rate_density_correlation':-.5,'linearized_relative_standard_uncertainty':analytic,'exact_lognormal_cv':math.sqrt(math.expm1(analytic**2)),'monte_carlo_cv':float(rr.std(ddof=1)/rr.mean()),'relative_ratio_quantiles':np.quantile(rr,[.025,.5,.975]).tolist(),'excluded_uncertainties':['fast neutrals','probe bias','geometry','model discrepancy','species systematics']}
R['thermal']={'absorbed_power_W_assumed':3,'capacity_J_K_assumed':24,'conductance_W_K_assumed':.15,'duration_s':180,'lumped_rise_K':lumped_temperature_rise(3,24,.15,180),'adiabatic_rise_K':lumped_temperature_rise(3,24,0,180),'scope':'absorbed heat is independent input, not inferred from ion current'}
# Spatial map on actual substrate plane; do not project a second time.
coords=np.linspace(-.12,.12,301);X,Ygrid=np.meshgrid(coords,coords);inside=X*X+Ygrid*Ygrid<=.12**2
J=.72*np.exp(-((X-.03)**2+(Ygrid+.01)**2)/(2*.09**2))
rate=.35*(1-.15*(X*X+Ygrid*Ygrid)/.12**2)*(1+.08*X/.12)
atom_factor=atom_flux_from_net_growth(1,2.1,60.0843,3)['net_atom_flux_m2_s']
Gamma=J/(E_CHARGE*1.15);ratio=Gamma/(rate*atom_factor);eps=ratio*103.5

def stat(a):
 v=a[inside];return {'mean':float(v.mean()),'min':float(v.min()),'max':float(v.max()),'rms_relative':float(v.std()/v.mean()),'peak_to_valley_over_mean':float((v.max()-v.min())/v.mean())}
R['spatial']={'grid_points_per_side':301,'accepted_points':int(inside.sum()),'radius_m':.12,'current_density_A_m2':stat(J),'rate_nm_s':stat(rate),'ion_to_net_atom_ratio':stat(ratio),'eV_per_net_atom':stat(eps),'ratio_of_area_means':float(Gamma[inside].mean()/(rate[inside].mean()*atom_factor)),'mean_local_ratio':float(ratio[inside].mean()),'scope':'uniform Cartesian area quadrature; no real source map'}
np.savez_compressed(P/'data/synthetic_maps.npz',X=X,Y=Ygrid,inside=inside,j_A_m2=J,rate_nm_s=rate,ratio=ratio,epsilon_eV=eps)
# Periodic motion, finite duration and shutter-only deposition occlusion.
def path_result(n):
 t=(np.arange(n)+.5)*(180/n)
 x=.07*np.cos(2*np.pi*.027*t)+.025*np.cos(2*np.pi*.071*t)
 y=.07*np.sin(2*np.pi*.027*t)+.025*np.sin(2*np.pi*.071*t)
 j=.72*np.exp(-((x-.03)**2+(y+.01)**2)/(2*.09**2))
 rate=.35*(1-.15*(x*x+y*y)/.12**2)*(1+.08*x/.12)
 # Fixed smooth attenuation used for convergence; no discontinuity-alignment luck.
 attenuation=.15+.85*(.5+.5*np.cos(2*np.pi*.041*t))**2
 rate*=attenuation
 gam=j/(E_CHARGE*1.15);atoms=rate*atom_factor;dt=180/n
 return {'n':n,'ion_to_net_atom_ratio':float(gam.sum()/atoms.sum()),'ion_fluence_m2':float(gam.sum()*dt),'net_thickness_nm':float(rate.sum()*dt),'energy_J_m2':float((gam*103.5*E_CHARGE).sum()*dt)},t,j,rate
conv=[]
for nn in [100,200,400,800,1600,3200,12800]:conv.append(path_result(nn)[0])
ref=conv[-1]['ion_to_net_atom_ratio']
for rr0 in conv:rr0['relative_error_to_12800']=abs(rr0['ion_to_net_atom_ratio']/ref-1)
R['motion_convergence']=conv
r0,t,j,r=path_result(1600)
with (P/'data/synthetic_time_history.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['time_s','j_on_substrate_A_m2','net_rate_nm_s']);w.writerows(zip(t,j,r))
(P/'data/demo_results.json').write_text(json.dumps(R,ensure_ascii=False,indent=2))
print(json.dumps(R,ensure_ascii=False,indent=2))
