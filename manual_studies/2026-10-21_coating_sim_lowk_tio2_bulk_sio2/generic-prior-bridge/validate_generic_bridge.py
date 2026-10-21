"""Supplemental no-answer-seed generator bridge; never reads retained candidates."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','BLIS_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
import sys,time,json,hashlib,signal,subprocess
from pathlib import Path
CORE=Path(__file__).resolve().parent.parent
OUT=Path(__file__).resolve().parent
root_env=os.environ.get('COATING_SIM_ROOT')
if not root_env: raise RuntimeError('Set COATING_SIM_ROOT to the clean coating-sim checkout at the recorded commit.')
os.environ['COATING_SIM_ROOT']=root_env
sys.path.insert(0,str(CORE/'scripts'));import tio2_research as r
import numpy as np
r.OUT=OUT
START=time.monotonic();DEADLINE=START+60.;CANCELLED=False
SOURCE_HASHES={'TiO2-Franta.yml':'2380783119baf079dfb5ed0eb846ef1f08dd17d719194d1e91610c34760ec174','MgF2-Franta.yml':'c51389d0430c21d8959388605266bc160abe14a04242cfa7ba8d1812bde2e58e','SiO2-Malitson.yml':'c587670f397241ecb93a1af3279d6fe7ed67888e587e399074b0eab729c92b52'}

def core_sources_unchanged():
 return all(hashlib.sha256((CORE/'sources'/name).read_bytes()).hexdigest()==digest for name,digest in SOURCE_HASHES.items())
def cancel(signum,frame):
 global CANCELLED
 CANCELLED=True;raise KeyboardInterrupt('Cancelled; completed candidates remain checkpointed')
signal.signal(signal.SIGINT,cancel);signal.signal(signal.SIGTERM,cancel)
# Generic inputs only, no per-target center/thickness answers.
band=(400.,700.);angles=(0.,30.);polarizations=('s','p');max_layers=32;target=.98
waves=np.array([band[0],np.sqrt(band[0]*band[1]),band[1]]);witness=[]
for a in angles:
 beta=np.sin(np.deg2rad(a))
 for p in polarizations:
  nh=r.nk('H',waves);nl=r.nk('L',waves);qh=np.sqrt(nh*nh-beta*beta+0j);ql=np.sqrt(nl*nl-beta*beta+0j)
  yh=qh if p=='s' else nh*nh/qh;yl=ql if p=='s' else nl*nl/ql
  for w,ratio in zip(waves,yh.real/yl.real):witness.append(dict(wavelength_nm=float(w),angle_deg=a,polarization=p,real_admittance_ratio=float(ratio)))
contrast=min(x['real_admittance_ratio'] for x in witness);assert contrast>1
width=float(4/np.pi*np.arcsin((contrast-1)/(contrast+1)))
fractions=[1/3,1/4,1/2];pairs=max_layers//2;allocation=(pairs//2,pairs-pairs//2)
protocol=dict(kind='no-answer-seed-generic-prior-bridge',band_nm=band,angles_deg=angles,polarizations=polarizations,target_min_R=target,max_layers=max_layers,pair_allocation=allocation,reference_phase_angle_deg=.5*(min(angles)+max(angles)),source_stopband_rule='Delta=4/pi*asin((C-1)/(C+1)); C=min Re(YH)/Re(YL) over band endpoints/geometric center and all requested conditions. Y_s=q,Y_p=n^2/q,q=sqrt(n^2-n0^2 sin^2theta). Lossless QW approximation for PRIOR SCHEDULING ONLY; all scores retain full sourced complex nk.',minimum_admittance_contrast=contrast,fractional_stopband_width=width,witness=witness,center_rule='c1=lo*(1+f*Delta), c2=hi/(1+f*Delta)',dimensionless_fraction_schedule=fractions,source_dependent_and_target_band_scaled=True,no_lookup_centers_or_answer_thicknesses=True,training_step_nm=1,total_wall_cap_s=60,per_candidate_optimizer_cap_s=15,max_iterations_each_stage=180,cancel_semantics='SIGINT/SIGTERM aborts, complete candidates atomically checkpointed. Optimizer checks deadline per evaluation. Pass only after completed independent audit.',source_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [CORE/'sources/TiO2-Franta.yml',CORE/'sources/MgF2-Franta.yml',CORE/'sources/SiO2-Malitson.yml']},prerequisite_engine_sha256=hashlib.sha256((CORE/'tio2_research.py').read_bytes()).hexdigest(),scope='Same32layercase only, no architecture/material expansion')
r.save('protocol.json',protocol);rows=[];passed=False;chosen=None
try:
 for index,f in enumerate(fractions):
  if time.monotonic()>DEADLINE-5:break
  padding=f*width;centers=[band[0]*(1+padding),band[1]/(1+padding)]
  if centers[0]>=centers[1]:continue
  c=r.prior([centers[0]]*allocation[0]+[centers[1]]*allocation[1],name=f'generic_source_stopband_f{index}')
  c['family']='generic_source_stopband_derived_two_substacks';c['generator_parameters']=dict(centers_nm=centers,fraction=f,padding=padding,normalized_centers_linear=[(x-band[0])/(band[1]-band[0]) for x in centers],normalized_centers_log=[float(np.log(x/band[0])/np.log(band[1]/band[0])) for x in centers],allocation=allocation)
  r.save(f'generated-prior-{index}.json',c);initial=r.Optics(c['labels'],np.arange(400,701)).worst(c['d']);t=time.monotonic()
  candidate=r.optimize(c,seconds=min(15,DEADLINE-time.monotonic()-5),maxiter=180);r.save(f'candidate-{index}.json',candidate)
  row=dict(index=index,generator_parameters=c['generator_parameters'],initial_worst=initial,training_worst=candidate['train_worst'],optimization_wall_s=time.monotonic()-t)
  if candidate['train_worst']['R']>=target:
   a=r.audit(candidate,f'generic-{index}');row['independent_audit']=dict(worst=a['worst'],passed=a['passed'],max_abs_RTA_crosscheck=a['max_abs_RTA_crosscheck'])
   if a['passed']:passed=True;chosen=index
  rows.append(row);r.save('search-summary.json',rows);print(json.dumps(r.plain(row)),flush=True)
  if passed:break
except KeyboardInterrupt:
 r.save('cancelled.json',dict(cancelled=True,elapsed_s=time.monotonic()-START,completed_candidates=len(rows)));raise
finally:
 unchanged=core_sources_unchanged()
 result=dict(passed=passed,chosen_index=chosen,completed_candidates=len(rows),elapsed_from_loaded_materials_s=time.monotonic()-START,cancelled=CANCELLED,generic_generator_validated_for_this_case_only=passed,no_answer_seed_used=True,search_summary=rows,core_source_tables_unchanged=unchanged,source_hashes=SOURCE_HASHES,software_git_clean=not subprocess.check_output(['git','-C',str(r.ROOT),'status','--porcelain'],text=True).strip(),scope='Not universal feasibility; bounded same32layercase bridge.')
 r.save('result.json',result);print('FINAL '+json.dumps(r.plain(result)),flush=True)
