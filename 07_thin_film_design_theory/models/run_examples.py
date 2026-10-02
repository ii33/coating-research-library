#!/usr/bin/env python3
"""Regenerate all original T07 examples, CSVs and plots. No network calls."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/t07-mpl-cache')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/t07-cache')
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from optics_kernel import scattering, characteristic_matrix, recursive, local_profile, phase_derivatives, intensity_combine
ROOT=Path(__file__).resolve().parents[1]
plt.rcParams.update({'font.size':10,'axes.grid':True,'grid.alpha':.25,'svg.fonttype':'none','figure.dpi':130})


def clean(x):
    if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple,np.ndarray)):return [clean(v) for v in x]
    if isinstance(x,(bool,np.bool_)):return bool(x)
    if isinstance(x,(np.integer,int)):return int(x)
    if isinstance(x,(np.floating,float)):return float(x) if np.isfinite(x) else str(x)
    if isinstance(x,(complex,np.complexfloating)):return {'real':clean(x.real),'imag':clean(x.imag)}
    return x


def csvwrite(name,headers,cols):
    with (ROOT/'data/spectra'/name).open('w',newline='') as f:
        w=csv.writer(f);w.writerow(headers);w.writerows(zip(*cols))


def save(fig,name):
    fig.tight_layout();fig.savefig(ROOT/'figures'/f'{name}.svg')
    fig.savefig(ROOT/'reviews'/f'{name}_preview.png');plt.close(fig)


def main():
    out={'schema_version':'1.0','status':'synthetic_theory_examples_not_measured','length_unit':'um',
         'phase_convention':'exp(-i omega t); N=n+ik; tangential E amplitudes',
         'limits':'No production qualification; sampled extrema; statistical scenarios not measured distributions.'}
    # W01
    wl=np.linspace(1,2,1001); ns=1.52; ideal=np.sqrt(ns); lam0=1.5
    ideal_o=scattering(wl,[1,ideal,ns],[lam0/4/ideal]); practical=scattering(wl,[1,1.375,ns],[lam0/4/1.375])
    out['W01_AR']={'n_substrate':ns,'n_ideal':ideal,'d_ideal_um':lam0/4/ideal,
      'assumed_MgF2_n':1.375,'R_at_center_ideal':scattering(lam0,[1,ideal,ns],[lam0/4/ideal])['R'][0],
      'R_at_center_available_index':scattering(lam0,[1,1.375,ns],[lam0/4/1.375])['R'][0],
      'note':'Independent synthetic substrate=1.52. T06 E01 actual proxy is 1.50106, not silently replaced.'}
    csvwrite('W01_ar.csv',['wavelength_um','R_ideal','R_available_index'],[wl,ideal_o['R'],practical['R']])
    # W02 quarter wave mirror and angle
    h,l,m=2.1,1.45,8; inds=[1]+[h,l]*m+[1.52]; ds=[1/4/h,1/4/l]*m
    w=np.linspace(.65,1.5,1701); s0=scattering(w,inds,ds); s45=scattering(w,inds,ds,45,'s');p45=scattering(w,inds,ds,45,'p')
    frac=4/np.pi*np.arcsin((h-l)/(h+l)); edges=[1/(1+frac/2),1/(1-frac/2)]
    ys=1.52*(h/l)**(2*m)
    out['W02_Bragg']={'nH':h,'nL':l,'pairs':m,'center_um':1.,'center_R':((1-ys)/(1+ys))**2,
     'infinite_period_relative_frequency_gap':frac,'infinite_period_wavelength_edges_um':edges,
     'finite_8pair_R_at_gap_edges':[scattering(x,inds,ds)['R'][0] for x in edges]}
    csvwrite('W02_bragg.csv',['wavelength_um','R_normal','R_s45','R_p45'],[w,s0['R'],s45['R'],p45['R']])
    fig,axs=plt.subplots(1,2,figsize=(11,4))
    axs[0].plot(wl,ideal_o['R']*100,label='ideal matching index');axs[0].plot(wl,practical['R']*100,label='available index 1.375')
    axs[0].set(xlabel='Vacuum wavelength (um)',ylabel='Front reflectance (%)',title='W01: matching is material-limited');axs[0].legend()
    for arr,label in [(s0,'normal'),(s45,'s, 45 deg'),(p45,'p, 45 deg')]:axs[1].plot(w,arr['R'],label=label)
    for edge in edges:axs[1].axvline(edge,color='gray',linestyle='--')
    axs[1].set(xlabel='Vacuum wavelength (um)',ylabel='Reflectance',title='W02: 8 HL pairs; dashed = infinite gap');axs[1].legend();save(fig,'01_matching_and_bandgap')
    # W03 stability, no fabricated clipping
    thick=np.array([0,.01,.03,.1,.3,.5,1,3,10,20,100]); table=[]
    for d in thick:
        a=scattering(1,[1,.2+6j,1.5],[d]);b=characteristic_matrix(1,[1,.2+6j,1.5],[d])
        M=b['M'][0]
        with np.errstate(over='ignore',invalid='ignore'):
            det=np.linalg.det(M) if np.all(np.isfinite(M)) else complex(np.nan,np.nan)
            try:cond=np.linalg.cond(M) if np.all(np.isfinite(M)) else np.inf
            except np.linalg.LinAlgError:cond=np.inf
        table.append(dict(thickness_um=d,Im_delta=12*np.pi*d,R_s=a['R'][0],T_s=a['T'][0],A_s=a['A'][0],
                          R_naive=b['R'][0],T_naive=b['T'][0],matrix_cond=cond,det_error=float(np.hypot(np.real(det)-1,np.imag(det))),
                          naive_finite=bool(np.all(np.isfinite(M)) and np.all(np.isfinite(b['r'])))))
    out['W03_stability']={'index':'.2+6i','wavelength_um':1,'rows':table,'semi_infinite_R':abs((1-(.2+6j))/(1+(.2+6j)))**2,
                          'underflow_note':'Floating zero T cannot be converted into a verified infinite OD.'}
    csvwrite('W03_stability.csv',list(table[0]),[[row[k] for row in table] for k in table[0]])
    fig,axs=plt.subplots(1,2,figsize=(11,4))
    xs=np.array([r['Im_delta'] for r in table[1:]]);err=np.array([r['det_error'] for r in table[1:]])
    axs[0].loglog(xs,np.maximum(err,1e-17),'o-',label='abs(det M - 1), naive')
    axs[0].axhline(1,color='red',ls='--',label='order-one determinant error')
    axs[0].set(xlabel='Im phase thickness',ylabel='Determinant error',title='W03: conditioning fails before overflow');axs[0].legend()
    axs[1].semilogx(thick[1:],[r['R_s'] for r in table[1:]],'o-',label='stable S: R')
    axs[1].semilogx(thick[1:],[r['A_s'] for r in table[1:]],'s-',label='stable S: A')
    axs[1].axvline(20,color='red',ls='--',label='naive overflow at sampled 20 um')
    axs[1].set(xlabel='Film physical thickness (um)',ylabel='Power fraction',title='Passive opaque limit remains finite');axs[1].legend();save(fig,'02_numerical_stability')
    # W04 phase ensemble and incoherence
    phi=np.arange(4096)*2*np.pi/4096;r=.04
    # t = t01*t10 exp(i phi)/(1-r exp(2i phi)), n=1.5 plate in air.
    amp=.96*np.exp(1j*phi)/(1-r*np.exp(2j*phi));cohT=np.abs(amp)**2
    out['W04_incoherence']={'interface_R':r,'analytic_incoherent_T':(1-r)/(1+r),
        'phase_ensemble_T':np.mean(cohT),'incorrect_average_amplitude_power':abs(amp.mean())**2,
        'coherent_T_min':cohT.min(),'coherent_T_max':cohT.max(),'phase_samples':len(phi),
        'assumptions':'uniform one-way phase ensemble, no bulk loss, all reflected orders collected'}
    csvwrite('W04_phase_average.csv',['phase_rad','T_coherent'],[phi,cohT])
    # W05 cavity GD and loss density
    c=299792458.;n=1.5;d=5.;omega0=2*np.pi*c/(1.5e-6)
    omega=np.linspace(.995*omega0,1.005*omega0,2001);w=2*np.pi*c/omega*1e6
    cavity=scattering(w,[1,n,1],[d]);phase=phase_derivatives(omega,cavity['t']);ic=len(w)//2
    analytic_tau=n*d*1e-6/c*(1+r)/(1-r)
    out['W05_cavity']={'n':n,'d_um':d,'resonance_wavelength_um':1.5,'interface_R':r,
      'center_T':cavity['T'][ic],'center_GD_fs':phase['GD_s'][ic]*1e15,'analytic_center_GD_fs':analytic_tau*1e15,
      'FSR_frequency_Hz':c/(2*n*d*1e-6),'reference_planes':'two physical slab faces; no added external propagation'}
    z=np.linspace(0,.5,2001);prof=local_profile(1,[1,2+.15j,1.5],[.5],0,z,35,'p')
    absorption=scattering(1,[1,2+.15j,1.5],[.5],35,'p',fields=True)
    out['W05_layer_absorption']={'finite_layer_A':absorption['A'][0],
      'density_integral':np.trapezoid(prof['normalized_absorption_density'],z),'parameters':{'lambda_um':1,'N':'2+.15i','d_um':.5,'AOI_deg':35,'pol':'p'}}
    csvwrite('W05_phase.csv',['omega_rad_s','wavelength_um','T','phase_rad','GD_fs','GDD_fs2'],[omega,w,cavity['T'],phase['phase'],phase['GD_s']*1e15,phase['GDD_s2']*1e30])
    csvwrite('W05_absorption.csv',['depth_um','full_E2','net_flux','absorption_density_per_um'],[z,prof['E2'],prof['flux'],prof['normalized_absorption_density']])
    fig,axs=plt.subplots(1,3,figsize=(14,3.8))
    axs[0].plot(phi,cohT);axs[0].axhline(np.mean(cohT),color='red',ls='--',label='intensity average')
    axs[0].set(xlabel='One-way phase (rad)',ylabel='Transmittance',title='W04: averaging intensity');axs[0].legend()
    axs[1].plot(w,phase['GD_s']*1e15);axs[1].set(xlabel='Vacuum wavelength (um)',ylabel='Transmission GD (fs)',title='W05: reference-plane delay')
    axs[2].plot(z,prof['E2'],label='full electric field squared');axs[2].plot(z,prof['normalized_absorption_density'],label='absorption / um')
    axs[2].set(xlabel='Depth (um)',title='W05: standing-wave absorption');axs[2].legend(fontsize=8);save(fig,'03_coherence_phase_and_absorption')
    # W06 symmetric equivalent layer pointwise reconstruction
    eq=[]
    for wv in [.7,.9,1.,1.4,2.]:
        M=characteristic_matrix(wv,[1,h,l,h,1],[1/(8*h),1/(4*l),1/(8*h)])['M'][0]
        de=np.arccos(complex(M[0,0]));qe=-1j*np.sin(de)/M[0,1]
        Me=np.array([[np.cos(de),-1j*np.sin(de)/qe],[-1j*qe*np.sin(de),np.cos(de)]])
        eq.append(dict(wavelength_um=wv,A=M[0,0],D=M[1,1],delta_equiv=de,q_equiv=qe,reconstruction_error=np.max(abs(M-Me))))
    out['W06_equivalent_layer']={'triplet':'H/2 L H/2: quarter-wave symbols at 1 um','rows':eq}
    # W07 graded index slicing convergence
    w=np.linspace(.7,2.,651);length=2.;grad=[];grins={}
    for count in [20,40,80,160,320,640]:
        u=(np.arange(count)+.5)/count;profile=1+.52*(3*u*u-2*u**3)
        grins[count]=scattering(w,[1,*profile,1.52],[length/count]*count)['R']
    for count in [20,40,80,160,320]:
        grad.append({'slices':count,'max_absolute_R_error_vs_640':np.max(abs(grins[count]-grins[640]))})
    out['W07_gradient']={'profile':'n(z)=1+0.52(3u^2-2u^3); u=z/(2 um)','rows':grad,
      'max_R_640_on_0p7_to_2um':grins[640].max(),'not_manufacturing_recipe':True}
    csvwrite('W07_gradient.csv',['wavelength_um']+[f'R_{k}_slices' for k in grins],[w,*grins.values()])
    # W08 sensitivity and common mode covariance, no optimization
    inds=[1]+[h,l]*4+[h]+[l,h]*4+[1];ds=np.array([1/4/h,1/4/l]*4+[1/2/h]+[1/4/l,1/4/h]*4)
    wv=1.01;eps=1e-5
    def metric(dd):return scattering(wv,inds,dd)['T'][0]
    J=np.array([(metric(ds+np.eye(len(ds))[j]*eps)-metric(ds-np.eye(len(ds))[j]*eps))/(2*eps) for j in range(len(ds))])
    J2=np.array([(metric(ds+np.eye(len(ds))[j]*eps/2)-metric(ds-np.eye(len(ds))[j]*eps/2))/eps for j in range(len(ds))])
    sigma=.001*ds;independent=np.diag(sigma**2);common=np.outer(sigma,sigma)
    rng=np.random.default_rng(708);samples=3000
    independent_y=np.array([metric(ds+sigma*v) for v in rng.normal(size=(samples,len(ds)))])
    common_y=np.array([metric(ds+sigma*v) for v in rng.normal(size=samples)])
    out['W08_sensitivity']={'wavelength_um':wv,'center_design_um':1,'nominal_T':metric(ds),'sigma_fractional_thickness':.001,
      'J_per_um':J,'d_um':ds,'J_step_halving_max_abs_change':np.max(abs(J-J2)),
      'linear_sigma_T_independent':np.sqrt(J@independent@J),'linear_sigma_T_common':np.sqrt(J@common@J),
      'MC_std_T_independent':independent_y.std(ddof=1),'MC_std_T_common':common_y.std(ddof=1),
      'MC_samples':samples,'seed':708,'distribution':'illustrative Gaussian scenarios, no estimated production yield'}
    # Quadratic failure of first order at perfect matching
    nf=np.sqrt(1.52);da=1/(4*nf);jj=(scattering(1,[1,nf,1.52],[da+eps])['R'][0]-scattering(1,[1,nf,1.52],[da-eps])['R'][0])/(2*eps)
    out['W08_stationary_counterexample']={'dR_dd_center':jj,'R_at_1percent_thicker':scattering(1,[1,nf,1.52],[da*1.01])['R'][0],
      'message':'Vanishing first derivative at nominal perfect AR does not mean zero tolerance loss.'}
    csvwrite('W08_sensitivity.csv',['layer_1_based','thickness_um','dT_dd_per_um'],[np.arange(1,len(ds)+1),ds,J])
    fig,axs=plt.subplots(1,3,figsize=(14,3.8))
    uu=np.linspace(0,1,300);axs[0].plot(uu*length,1+.52*(3*uu**2-2*uu**3));axs[0].set(xlabel='Depth (um)',ylabel='Refractive index',title='W07: smoothstep profile')
    axs[1].loglog([a['slices'] for a in grad],[a['max_absolute_R_error_vs_640'] for a in grad],'o-');axs[1].set(xlabel='Number of slices',ylabel='max absolute R difference',title='Convergence to 640-slice reference')
    axs[2].hist(independent_y,bins=45,alpha=.65,density=True,label='independent thickness errors');axs[2].hist(common_y,bins=45,alpha=.55,density=True,label='shared fractional thickness error')
    axs[2].set(xlabel='T at 1.01 um',ylabel='Scenario density',title='W08: same per-layer sigma, different covariance');axs[2].legend(fontsize=8);save(fig,'04_gradient_and_tolerance')
    # T06 frozen cross comparison + hash dependencies
    prev=ROOT.parent/'06_optical_coating_families';spec=importlib.util.spec_from_file_location('t06_reference',prev/'models/reference_tmm.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    mats=json.loads((prev/'data/material_proxies.json').read_text())['materials'];cases=json.loads((prev/'data/starter_stacks.json').read_text())['examples'];comparison=[]
    for ex in cases:
        w=np.linspace(*ex['wavelength_grid_um'][:2],151)
        n=[np.ones_like(w),*[mod.evaluate_material(mats[x['material']],w) for x in ex['layers']],mod.evaluate_material(mats[ex['substrate']],w)]
        d=[x['thickness_um'] for x in ex['layers']]
        for angle in ex['angles_deg']:
            for pol in ('s','p'):
                a=scattering(w,n,d,angle,pol);b=mod.coherent(w,n,d,angle,pol)
                comparison.append(dict(case=ex['id'],AOI_deg=angle,pol=pol,max_abs_r_difference=np.max(abs(a['r']-b['r'])),max_abs_T_difference=np.max(abs(a['T']-b['T']))))
    out['T06_crosscheck']={'scope':'front coating only; 151 wavelengths per case and declared angles/polarizations; no material changes','rows':comparison}
    dependencies=['models/reference_tmm.py','data/material_proxies.json','data/starter_stacks.json']
    (ROOT/'data/t06_dependency_manifest.json').write_text(json.dumps({p:hashlib.sha256((prev/p).read_bytes()).hexdigest() for p in dependencies},indent=2)+'\n')
    (ROOT/'data/example_results.json').write_text(json.dumps(clean(out),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    # Short generated evidence, explanatory chapter is authored separately.
    text=['# 自动生成算例指标\n','全部为理论合成场景，不是实测。完整条件见 example_results.json。\n']
    for name in ['W01_AR','W02_Bragg','W04_incoherence','W05_cavity','W05_layer_absorption','W07_gradient','W08_sensitivity','W08_stationary_counterexample']:
        text+=['\n## '+name+'\n','```json\n'+json.dumps(clean(out[name]),ensure_ascii=False,indent=2)+'\n```\n']
    text+=['\n## W03 稳定性\n','| d / µm | Imδ | R(S) | T(S) | |det M−1| | naive finite |\n','|---:|---:|---:|---:|---:|---|\n']
    for v in table:text.append(f"| {v['thickness_um']:g} | {v['Im_delta']:.4g} | {v['R_s']:.9g} | {v['T_s']:.3g} | {v['det_error']:.3g} | {v['naive_finite']} |\n")
    text+=['\n## T06 数值对照\n',f"{len(comparison)}组条件，最大复反射振幅绝对差 {max(v['max_abs_r_difference'] for v in comparison):.4g}；最大透过功率绝对差 {max(v['max_abs_T_difference'] for v in comparison):.4g}。\n"]
    (ROOT/'reports/09a_generated_results.md').write_text(''.join(text))
    print(json.dumps({'status':'completed','examples':8,'original_figures':4,'T06_cases':len(comparison),'worst_T06_r_error':max(v['max_abs_r_difference'] for v in comparison)},indent=2))

if __name__=='__main__': main()
