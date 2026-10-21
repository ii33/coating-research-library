"""Isolated reproducible low-loss reflector research. No production source mutation.
All layer arrays are incident-to-substrate, nm; optical convention n+ik.
"""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','BLIS_NUM_THREADS','NUMEXPR_NUM_THREADS'): os.environ[k]='1'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
import sys,json,hashlib,time,subprocess,csv,copy
from pathlib import Path
import numpy as np
from scipy.optimize import minimize,minimize_scalar
from scipy.special import logsumexp
root_env=os.environ.get('COATING_SIM_ROOT')
if not root_env: raise RuntimeError('Set COATING_SIM_ROOT to a clean coating-sim checkout at the recorded commit.')
ROOT=Path(root_env).expanduser().resolve()
OUT=Path(os.environ.get('COATING_RESEARCH_OUT',Path(__file__).resolve().parent.parent/'runs'/'default')).expanduser().resolve()
OUT.mkdir(parents=True,exist_ok=True)
SOURCE_DIR=Path(__file__).resolve().parent.parent/'sources'
sys.path.insert(0,str(ROOT))
from coat_sim.core.optical_constants import prepare_optical_set
from coat_sim.core.film_optics import coherent_rta,_longitudinal_many,_interface_many
COMMIT='0a631b7428486ab08fe0f27aa8938c50783f5280'

def plain(x):
 if isinstance(x,dict):return {str(k):plain(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [plain(v) for v in x]
 if isinstance(x,np.ndarray):return x.tolist()
 if isinstance(x,np.generic):return x.item()
 return x

def save(name,x):
 p=OUT/name;t=p.with_suffix(p.suffix+'.partial');t.write_text(json.dumps(plain(x),ensure_ascii=False,indent=2,allow_nan=False)+'\n');t.replace(p)

catalog=json.load(open(ROOT/'data/optical_catalog.json'))
sets={o['id']:o for m in catalog['materials'] for o in m['optical_constants']}
old_samplers={l:prepare_optical_set(sets[i],k_sampling_policy='source') for l,i in {'Lold':'ri_mgf2_rodriguez_de_marcos','S':'ri_sio2_malitson'}.items()}
raw=(SOURCE_DIR/'MgF2-Franta.yml').read_text()
rows=[];in_data=False
for line in raw.splitlines():
 s=line.strip()
 if s=='data: |':in_data=True;continue
 if in_data:
  try:
   a=list(map(float,s.split()))
   if len(a)==3:rows.append(a)
  except ValueError:pass
franta=np.array(rows);assert len(franta)>100 and franta[0,0]<=.4 and franta[-1,0]>=.7

rawH=(SOURCE_DIR/'TiO2-Franta.yml').read_text()
Hrows=[];in_data=False
for line in rawH.splitlines():
 s=line.strip()
 if s=='data: |':in_data=True;continue
 if in_data:
  try:
   a=list(map(float,s.split()))
   if len(a)==3:Hrows.append(a)
  except ValueError:pass
tio2=np.array(Hrows);assert len(tio2)>100 and tio2[0,0]<=.4 and tio2[-1,0]>=.7

# Existing sampler values are retained. Malitson provides n only: k=0 is an explicit
# semi-infinite-exit-medium assumption, not a measured-k replacement.
def nk(label,waves,model='selected'):
 w=np.asarray(waves,float)
 if label=='H':
  val=np.interp(w/1000,tio2[:,0],tio2[:,1])+1j*np.interp(w/1000,tio2[:,0],tio2[:,2])
  return val.real.astype(complex) if model=='Hk0_diagnostic' else val
 if label=='L' and model!='legacy':
  return np.interp(w/1000,franta[:,0],franta[:,1])+1j*np.interp(w/1000,franta[:,0],franta[:,2])
 key='Lold' if label=='L' else label
 vals=[old_samplers[key](float(x),'nm') for x in w]
 if label=='S':
  assert all(v[1] is None and not v[2]['k_known'] for v in vals)
  return np.array([complex(v[0],0.) for v in vals])
 assert all(v[1] is not None and v[2]['k_known'] for v in vals)
 ans=np.array([complex(v[0],v[1]) for v in vals])
 if model=='Hk0_diagnostic' and label=='H':ans=ans.real.astype(complex)
 return ans

class Optics:
 def __init__(self,labels,waves,model='selected'):
  self.labels=list(labels);self.waves=np.asarray(waves);self.model=model
  values={l:nk(l,self.waves,model) for l in ['H','L','S']}
  self.n=np.column_stack([np.ones(len(waves)),*[values[l] for l in labels],values['S']])
  ars=[];qs=[];self.conditions=[]
  for a in [0.,30.]:
   q=_longitudinal_many(self.n,np.full(len(waves),np.sin(np.deg2rad(a))))
   for p in ['s','p']:
    ars.append(np.column_stack([_interface_many(self.n[:,i],self.n[:,i+1],q[:,i],q[:,i+1],p)[0] for i in range(len(labels)+1)]));qs.append(q[:,1:-1]);self.conditions.extend([(a,p,float(w)) for w in waves])
  self.a=np.concatenate(ars);self.q=np.concatenate(qs);self.w=np.tile(self.waves,4);self.k=4j*np.pi*self.q/self.w[:,None];self.nfev=0
 def eval(self,d,grad=False):
  self.nfev+=1;d=np.asarray(d);z=np.exp(self.k*d[None,:]);r=self.a[:,-1].copy()
  if grad:own=np.empty_like(z);trans=np.empty_like(z)
  for i in range(len(d)-1,-1,-1):
   ri=self.a[:,i];den=1+ri*r*z[:,i]
   if grad:
    transfer=(1-ri*ri)/den**2;own[:,i]=transfer*r*z[:,i]*self.k[:,i];trans[:,i]=transfer*z[:,i]
   r=(ri+r*z[:,i])/den
  R=abs(r)**2
  if not grad:return R
  alpha=np.ones_like(r);jac=np.empty((len(r),len(d)))
  for i in range(len(d)):
   jac[:,i]=2*np.real(np.conj(r)*alpha*own[:,i]);alpha*=trans[:,i]
  return R,jac
 def worst(self,d):
  rv=self.eval(d);j=int(np.argmin(rv));a,p,w=self.conditions[j];return dict(R=float(rv[j]),wavelength_nm=w,angle_deg=a,polarization=p)

# Fully independent characteristic-admittance matrix implementation, no production
# Fresnel, longitudinal-wave-vector, recursion or R/T helpers.
def matrix_rta(labels,d,waves,angle,pol,model='selected'):
 w=np.asarray(waves,float);n=np.column_stack([np.ones(len(w)),*[nk(l,w,model) for l in labels],nk('S',w,model)])
 beta=np.sin(np.deg2rad(angle));q=np.sqrt(n*n-beta*beta+0j);q=np.where((q.imag<0)|((q.imag==0)&(q.real<0)),-q,q);Y=q if pol=='s' else n*n/q
 A=np.ones(len(w),complex);B=np.zeros(len(w),complex);C=B.copy();D=A.copy()
 for j,t in enumerate(d,1):
  delta=2*np.pi*q[:,j]*t/w;c=np.cos(delta);s=np.sin(delta);b=-1j*s/Y[:,j];cc=-1j*Y[:,j]*s
  A,B,C,D=A*c+B*cc,A*b+B*c,C*c+D*cc,C*b+D*c
 den=Y[:,0]*A+Y[:,0]*Y[:,-1]*B+C+Y[:,-1]*D
 r=(Y[:,0]*A+Y[:,0]*Y[:,-1]*B-C-Y[:,-1]*D)/den
 R=abs(r)**2;T=4*Y[:,0].real*Y[:,-1].real/abs(den)**2;return np.column_stack([R,T,1-R-T])


def audit(c,name,model='selected'):
 labels=c['labels'];d=np.array(c['d']);w=np.arange(8000,14001)/20 # .05 nm, independent of train
 # all original material interpolation knots, so derivative discontinuities are tested
 knots=np.unique(np.r_[franta[:,0]*1000,tio2[:,0]*1000]);knots=knots[(knots>=400)&(knots<=700)];w=np.unique(np.r_[w,knots])
 results=[];full=[];cross=[]
 for angle in [0.,30.]:
  for pol in ['s','p']:
   v=matrix_rta(labels,d,w,angle,pol,model);j=int(np.argmin(v[:,0]));ext=[]
   points=[(400.,v[0]),(700.,v[-1]),(float(w[j]),v[j])]
   jj=np.flatnonzero((v[1:-1,0]<v[:-2,0])&(v[1:-1,0]<v[2:,0]))+1
   for z in jj:
    rr=minimize_scalar(lambda x:float(matrix_rta(labels,d,[x],angle,pol,model)[0,0]),bounds=(w[z-1],w[z+1]),method='bounded',options={'xatol':1e-9,'maxiter':80})
    val=matrix_rta(labels,d,[rr.x],angle,pol,model)[0];points.append((float(rr.x),val));ext.append(dict(wavelength_nm=float(rr.x),R=float(val[0]),bracket_nm=[float(w[z-1]),float(w[z+1])],success=bool(rr.success)))
   ww,vv=min(points,key=lambda p:p[1][0]);record=dict(angle_deg=angle,polarization=pol,worst=dict(wavelength_nm=ww,R=float(vv[0]),T=float(vv[1]),A=float(vv[2])),extrema=ext,max_A=float(v[:,2].max()),minimum_A=float(v[:,2].min()),mean_R=float(np.trapezoid(v[:,0],w)/300),mean_T=float(np.trapezoid(v[:,1],w)/300),mean_A=float(np.trapezoid(v[:,2],w)/300));results.append(record)
   checks=np.unique(np.r_[np.arange(400,701,10),ww]);n=np.column_stack([np.ones(len(checks)),*[nk(l,checks,model) for l in labels],nk('S',checks,model)]);ref=coherent_rta(checks,n,d,angle,pol);ind=matrix_rta(labels,d,checks,angle,pol,model);err=max(float(np.max(abs(ind[:,i]-ref[k]))) for i,k in enumerate(['R','T','A']));cross.append(dict(angle_deg=angle,polarization=pol,points=len(checks),max_abs_RTA_difference=err))
   full.extend([dict(wavelength_nm=float(ww),angle_deg=angle,polarization=pol,R=float(x[0]),T=float(x[1]),A=float(x[2])) for ww,x in zip(w,v)])
 worst=min(results,key=lambda x:x['worst']['R']);out=dict(name=name,model=model,layer_count=len(d),total_thickness_nm=float(sum(d)),min_layer_nm=float(min(d)),max_layer_nm=float(max(d)),independent_audit=dict(base_step_nm=.1,offset_nm=.05,mesh_union_step_nm=.05,source_knots_included=True,samples_per_condition=len(w),all_bracketed_minima_refined=True,not_interval_proof=True),worst=dict(**worst['worst'],angle_deg=worst['angle_deg'],polarization=worst['polarization']),conditions=results,production_crosschecks=cross,max_abs_RTA_crosscheck=max(x['max_abs_RTA_difference'] for x in cross),passed=min(x['worst']['R'] for x in results)>=.98)
 save('audit-'+name+'.json',out)
 with (OUT/('spectra-'+name+'.csv')).open('w') as f:
  wr=csv.DictWriter(f,fieldnames=['wavelength_nm','angle_deg','polarization','R','T','A']);wr.writeheader();wr.writerows(full)
 return out

def qwave(label,centers,angle=15.):
 ns=nk(label,centers);return np.array(centers)/(4*np.sqrt(ns*ns-np.sin(np.deg2rad(angle))**2).real)

def prior(centers,orientation='HL',name=''):
 labels=list(orientation)*len(centers);d=np.array([qwave(l,[c])[0] for c in centers for l in orientation]);return dict(name=name,labels=labels,d=d,centers_nm=np.array(centers),family='chirped_QW' if len(np.unique(centers))>3 else 'overlapped_HR_substacks')

class BudgetStop(Exception):pass

def optimize(c,seconds=40.,maxiter=160,waves=None):
 st=time.monotonic();deadline=st+seconds;o=Optics(c['labels'],np.arange(400,701) if waves is None else waves);x=np.array(c['d'])/100;best=[float(min(o.eval(c['d']))),x.copy()];stages=[];cache={}
 def pair(xx):
  if time.monotonic()>deadline:raise BudgetStop()
  if not np.array_equal(cache.get('x'),xx):
   rv,j=o.eval(xx*100,True);cache.update(x=xx.copy(),value=(rv,j*100));v=float(min(rv))
   if v>best[0] and sum(xx)*100<=5000.00001:best[:]=[v,xx.copy()]
  return cache['value']
 for beta in [100.,400.,1500.]:
  try:
   def fun(xx):
    rv,j=pair(xx);weights=np.exp(-beta*rv-logsumexp(-beta*rv));return logsumexp(-beta*rv)/beta,-weights@j
   rr=minimize(fun,x,jac=True,method='L-BFGS-B',bounds=[(.1,5.)]*len(x),options={'maxiter':maxiter,'ftol':2e-13,'gtol':1e-9,'maxls':25});x=rr.x;stages.append(dict(method='L-BFGS-B',beta=beta,success=bool(rr.success),iterations=rr.nit,train_R=best[0],message=str(rr.message)))
  except BudgetStop:break
 try:
  x=best[1];rv,j=pair(x)
  def eq(v):return pair(v[:-1])[0]-v[-1]
  def ej(v):return np.column_stack([pair(v[:-1])[1],-np.ones(len(o.w))])
  rr=minimize(lambda v:-v[-1],np.r_[x,min(rv)],jac=lambda v:np.r_[np.zeros(len(x)),-1.],method='SLSQP',bounds=[(.1,5.)]*len(x)+[(0,1)],constraints=[dict(type='ineq',fun=eq,jac=ej),dict(type='ineq',fun=lambda v:50-sum(v[:-1]),jac=lambda v:np.r_[-np.ones(len(x)),0.])],options={'maxiter':maxiter,'ftol':1e-11});stages.append(dict(method='SLSQP_epigraph',success=bool(rr.success),iterations=rr.nit,train_R=best[0],message=str(rr.message)))
 except BudgetStop:stages.append(dict(method='deadline',seconds=seconds))
 ans=copy.deepcopy(c);ans.update(d=best[1]*100,initial_worst=o.worst(c['d']),train_worst=o.worst(best[1]*100),stages=stages,elapsed_s=time.monotonic()-st,evaluations=o.nfev);return ans

if __name__=='__main__':
 start=time.monotonic();assert subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()==COMMIT;assert not subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain'],text=True).strip()
 protocol=dict(protocol='lowk-MgF2-TiO2-film-bulk-SiO2-v1',software_commit=COMMIT,separate_from_frozen_original_benchmark=True,target=dict(wavelength_nm=[400,700],training_step_nm=1,angles_deg=[0,30],polarizations=['s','p'],minimum_R=.98),constraints=dict(max_layers=32,min_layer_nm=10,max_layer_nm=500,max_total_nm=5000),materials=dict(H='TiO2 Franta2015 99.6nm e-beam amorphous/fine-polycrystalline film author fitted n,k retained, not bulk rutile',L='MgF2 Franta2017 author fitted n,k retained exactly, not direct ultralow-k measurement',substrate='Bulk fused SiO2 Malitson n-only; explicit k=0 semi-infinite exit medium assumption'),priors=['two_stacks_440_625','two_stacks_460_630','three_stacks_425_540_675','linear_chirp_415_700','exp_chirp_425_700','reverse_linear_chirp'],per_candidate_search_cap_s=45,total_search_cap_s=360,max_full_refinement_iterations=180,independent_audit='characteristic matrix, .1nm and .05nm shifted union, material knots, all bracketed extrema refined',no_software_publication=True,new_user_material_direction='Switch high index from ZnS to TiO2; reoptimize all thicknesses, preserve old evidence')
 save('protocol.json',protocol);save('sampled-nk.json',{l:[dict(wavelength_nm=w,n=float(z.real),k=float(z.imag)) for w,z in zip([400,450,550,650,700],nk(l,[400,450,550,650,700]))] for l in ['H','L','S']})
 priors=[prior([440]*8+[625]*8,name='two_stacks_440_625'),prior([460]*8+[630]*8,name='two_stacks_460_630'),prior([425]*5+[540]*6+[675]*5,name='three_stacks_425_540_675'),prior(np.linspace(415,700,16),name='linear_chirp_415_700'),prior(np.geomspace(425,700,16),name='exp_chirp_425_700'),prior(np.linspace(700,415,16),name='reverse_linear_chirp')]
 # Gradient self-check on one deterministic prior, central finite differences.
 test=Optics(priors[0]['labels'],[400,431,550,700]);d=priors[0]['d'];rv,j=test.eval(d,True);errs=[]
 for i in [0,1,14,31]:
  dd=np.zeros(len(d));dd[i]=1e-4;fd=(test.eval(d+dd)-test.eval(d-dd))/(2e-4);errs.append(float(np.max(abs(fd-j[:,i]))))
 save('analytic-gradient-check.json',dict(max_abs_error=max(errs),step_nm=.0001,columns=[0,1,14,31]));assert max(errs)<1e-7
 summaries=[];best=None;best_audit=None
 for c in priors:
  if time.monotonic()-start>360:break
  candidate=optimize(c,45,180);save('candidate-'+c['name']+'.json',candidate)
  summary={k:candidate[k] for k in ['name','family','initial_worst','train_worst','elapsed_s','evaluations','stages']};summary.update(layer_count=len(candidate['d']),total_thickness_nm=float(sum(candidate['d'])));summaries.append(summary);save('search-summary.json',summaries);print('CANDIDATE '+json.dumps(plain(summary)),flush=True)
  if best is None or candidate['train_worst']['R']>best['train_worst']['R']:best=candidate;save('retained-best.json',best)
  if candidate['train_worst']['R']>=.98005:
   a=audit(candidate,candidate['name']);print('AUDIT '+json.dumps({k:a[k] for k in ['name','worst','passed','max_abs_RTA_crosscheck']}),flush=True)
   if a['passed']:best=candidate;best_audit=a;break
 if best_audit is None:best_audit=audit(best,'terminal-best')
 save('retained-best.json',best);save('result.json',dict(passed=best_audit['passed'],audit=best_audit,search_comparisons=len(summaries),elapsed_s=time.monotonic()-start,git_clean_after=not subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain'],text=True).strip()))
 print('FINAL '+json.dumps(dict(passed=best_audit['passed'],worst=best_audit['worst'],elapsed_s=time.monotonic()-start)),flush=True)
