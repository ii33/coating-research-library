"""Portable independent fixed-11-layer audit. No production code imports.
Scientific functions retain the independently accepted implementation unchanged.
Use --check-inputs-only for identity checks, or --output NEW_DIRECTORY for a full audit.
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,platform,tempfile,time
import numpy as np
import scipy
import mpmath as mp
from scipy.optimize import minimize,minimize_scalar
SOURCE=Path(__file__).resolve().parents[1]
FINAL=SOURCE/'recommended'
PKG=SOURCE.parent/'normal_incidence'
P=None
TABLES={};STATS={'calls':0,'condition_points':0,'min_q_real':1.,'min_q_imag':0.,'max_q_imag':0.,'min_cascade_denominator':1.}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,obj):(P/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def tree(root):return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()}
def baseline():return dict(angular_package=tree(SOURCE),materials=tree(PKG/'materials'))
def load_materials():
 out=[];recorded={m['id']:m for m in read(SOURCE/'independent_review/summary.json')['materials']}
 for source in read(PKG/'materials/sources.json')['materials']:
  path=PKG/source['data_file'];assert sha(path)==source['packaged_data_sha256']
  t=np.genfromtxt(path,delimiter=',',names=True);table=np.column_stack([t[k] for k in ('wavelength_nm','n','k')]);assert np.all(np.isfinite(table)) and np.all(np.diff(table[:,0])>0) and np.all(table[:,1:]>=[0,0])
  TABLES[source['id']]=table
  item=dict(recorded[source['id']]);item.pop('raw_yaml_csv_exact',None);item['raw_yaml_csv_identity_previously_independently_verified']=True;item['csv_sha256_verified_this_run']=sha(path);out.append(item)
 return out
def package_checks():
 manifest=read(SOURCE/'publication_manifest.json')['files']
 checks={name:sha(SOURCE/name)==digest for name,digest in manifest.items()}
 assert all(checks.values())
 pres=read(FINAL/'final-prescription.json');summary=read(SOURCE/'independent_review/summary.json')
 assert sha(FINAL/'final-prescription.json')==summary['prescription_sha256']
 assert pres['layers']==summary['layers_substrate_outward'] and len(pres['layers'])==11
 assert pres['targets']==summary['targets'] and pres['targets']['windows_nm']==[[3000,5000],[8000,12000]]
 assert pres['targets']['angle_range_deg']==[0,15] and pres['targets']['polarizations']==['s','p']
 assert pres['targets']['R_upper']==.0099 and pres['targets']['T_lower']==.9001 and pres['targets']['tolerance']==1e-6
 return checks

def nk(name,w):
 t=TABLES[name];w=np.asarray(w,float)
 if np.any(w<t[0,0]) or np.any(w>t[-1,0]):raise ValueError('outside explicit n/k source domain')
 return np.interp(w,t[:,0],t[:,1])+1j*np.interp(w,t[:,0],t[:,2])

def optics(w,angle,seq):
 w,angle=np.broadcast_arrays(np.atleast_1d(w).astype(float),np.asarray(angle,float));w=w.ravel();angle=angle.ravel()
 n=np.column_stack([np.ones(len(w)),*[nk(m,w) for m in seq],nk('ZnS',w)])
 beta=np.sin(np.deg2rad(angle));q=np.sqrt(n*n-beta[:,None]**2+0j)
 q=np.where((q.imag<0)|((q.imag==0)&(q.real<0)),-q,q)
 STATS['min_q_real']=min(STATS['min_q_real'],float(q.real.min()));STATS['min_q_imag']=min(STATS['min_q_imag'],float(q.imag.min()));STATS['max_q_imag']=max(STATS['max_q_imag'],float(q.imag.max()))
 return w,angle,n,q

def scatter(w,angle,pol,seq,th):
 STATS['calls']+=1
 w,angle,n,q=optics(w,angle,seq);STATS['condition_points']+=len(w)
 # Main p variable is magnetic Hy; its flux admittance is q/N^2, not N^2/q.
 flux=q if pol=='s' else q/(n*n)
 z=np.zeros(len(w),complex);a,b,c,d=z.copy(),np.ones(len(w),complex),np.ones(len(w),complex),z.copy()
 def cascade(e,f,g,h):
  nonlocal a,b,c,d
  den=1-d*e;STATS['min_cascade_denominator']=min(STATS['min_cascade_denominator'],float(abs(den).min()))
  a,b,c,d=a+b*e*c/den,b*f/den,g*c/den,h+g*d*f/den
 for j in range(len(th)+1):
  left,right=flux[:,j],flux[:,j+1];r=(left-right)/(left+right)
  cascade(r,2*right/(left+right),2*left/(left+right),-r)
  if j<len(th):
   phase=np.exp(2j*np.pi*q[:,j+1]*th[j]/w);cascade(z,phase,phase,z)
 R=abs(a)**2;T=flux[:,-1].real/flux[:,0].real*abs(c)**2
 return np.column_stack([R,T,1-R-T])

def boundary(w,angle,pol,seq,th):
 # Independent full Maxwell tangential-E unknowns; no scattering interface calls.
 waves,angles,n,q=optics([w],angle,seq);n=n[0];q=q[0];Y=q if pol=='s' else n*n/q
 count=len(th);M=np.zeros((2*count+2,2*count+2),complex);rhs=np.zeros(2*count+2,complex)
 def add(row,j,factor,forward):
  if j==0:
   if forward:rhs[row]-=factor
   else:M[row,0]+=factor
  elif j==count+1:
   if forward:M[row,-1]+=factor
  else:M[row,2*j-1+(0 if forward else 1)]+=factor
 for j in range(count+1):
  phase=1 if j==0 else np.exp(2j*np.pi*q[j]*th[j-1]/w)
  for magnetic in (False,True):
   row=2*j+int(magnetic)
   add(row,j,phase*(Y[j] if magnetic else 1),True);add(row,j,(1/phase)*(-Y[j] if magnetic else 1),False)
   add(row,j+1,-(Y[j+1] if magnetic else 1),True);add(row,j+1,(Y[j+1] if magnetic else -1),False)
 x=np.linalg.solve(M,rhs);R=abs(x[0])**2;T=Y[-1].real/Y[0].real*abs(x[-1])**2
 def F(f,b,admittance):return float(np.real((f+b)*np.conj(admittance*(f-b)))/Y[0].real)
 losses=[]
 for j in range(1,count+1):
  f,b=x[2*j-1:2*j+1];phase=np.exp(2j*np.pi*q[j]*th[j-1]/w);losses.append(F(f,b,Y[j])-F(f*phase,b/phase,Y[j]))
 result=dict(R=float(R),T=float(T),A=float(1-R-T),equation_residual=float(abs(M@x-rhs).max()),condition=float(np.linalg.cond(M)),
             film_absorption=losses,film_absorption_sum=float(sum(losses)),absorption_flux_residual=float(sum(losses)-(1-R-T)))
 if pol=='p':
  q0=q[0].real;t_total_E=x[-1]*q0*n[-1]/q[-1]
  physical_T=(q[-1]*n[-1].conjugate()/n[-1]).real/q0*abs(t_total_E)**2
  naive_T=q[-1].real/q0*abs(x[-1])**2
  result.update(full_E_p_T=float(physical_T),full_E_p_difference=float(physical_T-T),wrong_tangential_E_s_flux_T=float(naive_T))
 return result

def mp_boundary(w,angle,pol,seq,th):
 mp.mp.dps=60;wave=mp.mpf(str(w));beta=mp.sin(mp.mpf(str(angle))*mp.pi/180)
 def index(name):
  t=TABLES[name];j=max(0,min(int(np.searchsorted(t[:,0],w,side='right'))-1,len(t)-2));f=(wave-mp.mpf(str(t[j,0])))/(mp.mpf(str(t[j+1,0]))-mp.mpf(str(t[j,0])))
  return mp.mpc(*[mp.mpf(str(t[j,c]))+f*(mp.mpf(str(t[j+1,c]))-mp.mpf(str(t[j,c]))) for c in (1,2)])
 n=[mp.mpc(1),*[index(m) for m in seq],index('ZnS')];q=[mp.sqrt(x*x-beta*beta) for x in n];q=[-v if mp.im(v)<0 or mp.im(v)==0 and mp.re(v)<0 else v for v in q]
 y=q if pol=='s' else [a*a/b for a,b in zip(n,q)];N=len(th);M=mp.matrix(2*N+2);rhs=mp.matrix(2*N+2,1)
 def add(row,j,factor,forward):
  if j==0:
   if forward:rhs[row]-=factor
   else:M[row,0]+=factor
  elif j==N+1:
   if forward:M[row,2*N+1]+=factor
  else:M[row,2*j-1+(0 if forward else 1)]+=factor
 for j in range(N+1):
  phase=mp.mpc(1) if j==0 else mp.exp(2j*mp.pi*q[j]*mp.mpf(str(th[j-1]))/wave)
  add(2*j,j,phase,True);add(2*j,j,1/phase,False);add(2*j,j+1,-1,True);add(2*j,j+1,-1,False)
  add(2*j+1,j,y[j]*phase,True);add(2*j+1,j,-y[j]/phase,False);add(2*j+1,j+1,-y[j+1],True);add(2*j+1,j+1,y[j+1],False)
 x=mp.lu_solve(M,rhs);R=abs(x[0])**2;T=mp.re(y[-1])/mp.re(y[0])*abs(x[2*N+1])**2
 return [str(R),str(T),str(1-R-T)]

def grids(lo,hi,wdiv,adiv):
 w=np.linspace(lo,hi,wdiv+1);wshift=lo+(hi-lo)*(np.arange(wdiv)+(np.sqrt(5)-1)/2)/wdiv
 knots=np.concatenate([t[(t[:,0]>=lo)&(t[:,0]<=hi),0] for t in TABLES.values()])
 a=np.linspace(0,15,adiv+1);ashift=15*(np.arange(adiv)+(np.sqrt(2)-1))/adiv
 return np.unique(np.r_[w,wshift,knots]),np.unique(np.r_[a,ashift])

def sweep(w,a,pol,seq,th):return np.array([scatter(w,t,pol,seq,th) for t in a])

def extrema(w,a,data,pol,seq,th):
 rows={};details=[]
 for col,label,sign in ((0,'Rmax',-1),(1,'Tmin',1),(2,'Amax',-1),(2,'Amin',1)):
  obj=sign*data[:,:,col];ia,iw=np.unravel_index(np.argmin(obj),obj.shape);best=[float(data[ia,iw,col]),float(w[iw]),float(a[ia])]
  padded=np.pad(obj,1,constant_values=np.inf);mask=np.ones(obj.shape,bool)
  for da,dw in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)):mask&=obj<=padded[1+da:1+da+len(a),1+dw:1+dw+len(w)]
  picks=np.argwhere(mask);count2d=count1d=0
  for i,j in picks:
   wl,wh=float(w[max(0,j-1)]),float(w[min(len(w)-1,j+1)]);al,ah=float(a[max(0,i-1)]),float(a[min(len(a)-1,i+1)])
   fun=lambda u:sign*scatter([wl+(wh-wl)*u[0]],al+(ah-al)*u[1],pol,seq,th)[0,col]
   if i in (0,len(a)-1):
    edge=float(i==len(a)-1);res=minimize_scalar(lambda x:fun([x,edge]),bounds=(0,1),method='bounded',options={'xatol':3e-13,'maxiter':400});point=[wl+(wh-wl)*res.x,a[i]];count1d+=1
   elif j in (0,len(w)-1):
    edge=float(j==len(w)-1);res=minimize_scalar(lambda x:fun([edge,x]),bounds=(0,1),method='bounded',options={'xatol':3e-13,'maxiter':400});point=[w[j],al+(ah-al)*res.x];count1d+=1
   else:
    initial=[(w[j]-wl)/(wh-wl),(a[i]-al)/(ah-al)];res=minimize(fun,initial,method='Nelder-Mead',bounds=[(0,1),(0,1)],options={'xatol':3e-11,'fatol':2e-15,'maxiter':600});point=[wl+(wh-wl)*res.x[0],al+(ah-al)*res.x[1]];count2d+=1
   value=float(sign*res.fun);details.append(dict(metric=label,wavelength_bracket_nm=[wl,wh],angle_bracket_deg=[al,ah],value=value,wavelength_nm=float(point[0]),angle_deg=float(point[1]),success=bool(res.success),nfev=int(res.nfev)))
   if sign*value<sign*best[0]:best=[value,float(point[0]),float(point[1])]
  rows[label]=best[0];rows[label+'_nm']=best[1];rows[label+'_angle_deg']=best[2];rows[label+'_brackets_1d']=count1d;rows[label+'_brackets_2d']=count2d
 return rows,details

def main():
 global P
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--check-inputs-only',action='store_true')
 parser.add_argument('--output',type=Path,help='New or empty directory outside the entire research package')
 args=parser.parse_args()
 checks=package_checks();load_materials()
 if args.check_inputs_only:
  print(json.dumps({'input_identity_passed':all(checks.values()),'scientific_evaluations':STATS['calls'],'prescription_layers':11,'production_imports':False}));return
 if args.output is None:parser.error('--output is required for numerical evaluation')
 P=args.output.resolve()
 if P.is_relative_to(SOURCE.parent):parser.error('output must be outside the research package')
 if P.exists() and any(P.iterdir()):parser.error('output directory must be empty')
 P.mkdir(parents=True,exist_ok=True)
 started=time.monotonic();before=baseline();save('inputs-before.json',before)
 checks=package_checks()
 materials=load_materials();pres=read(FINAL/'final-prescription.json');old=read(SOURCE/'history/archived12-prescription.json');layers=pres['layers'];seq=[x['material'] for x in layers][::-1];th=np.array([x['thickness_nm'] for x in layers][::-1])
 assert len(layers)==11 and len(old['layers'])==12 and np.all(th>0) and np.all(th<=10000) and sum(th)<20000 and abs(sum(th)-3871.098426)<1e-9
 assert pres['layer_order']=='substrate_outward' and pres['targets']['T_definition']=='flux entering semi-infinite ZnS'
 assert pres['targets']['angle_range_deg']==[0,15] and pres['targets']['R_upper']==.0099 and pres['targets']['T_lower']==.9001 and pres['targets']['polarizations']==['s','p']
 filtered=[dict(x) for x in old['layers'] if not (x['material']=='NaCl' and x['thickness_nm']==.1)]
 assert [(x['material'],x['thickness_nm']) for x in filtered]==[(x['material'],x['thickness_nm']) for x in layers]
 result=dict(checked_utc=datetime.now(timezone.utc).isoformat(),python_version=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
             input_prescription='recommended/final-prescription.json',prescription_sha256=sha(FINAL/'final-prescription.json'),layer_count=len(layers),total_nm=float(sum(th)),minimum_layer_nm=float(min(th)),maximum_layer_nm=float(max(th)),
             layers_substrate_outward=layers,targets=pres['targets'],handoff_hash_checks=checks,materials=materials,windows=[],global_boundary_checks=[],high_precision_checks=[],
             cleanup='One 0.1 nm NaCl layer removed from archived12; a physical change, not identity. This audit evaluates cleaned11.',continuous_certificate=False,production_materials_calibrated=False,
             transmission='Flux entering semi-infinite source-specific ZnS; no finite substrate/back face',imports_author_or_product_code=False,synthesis_search_restarted=False)
 author=read(FINAL/'final-audit.json')['windows'];all_extrema=[]
 for pol in ('s','p'):
  for wi,(lo,hi) in enumerate(((3000.,5000.),(8000.,12000.))):
   print(f'BEGIN {pol} {lo:g}-{hi:g}: independent coarse/refined 2D sweeps',flush=True)
   levels=[]
   for wdiv,adiv in ((3001,103),(6007,181)):
    w,a=grids(lo,hi,wdiv,adiv);data=sweep(w,a,pol,seq,th);ext,details=extrema(w,a,data,pol,seq,th);all_extrema.extend([dict(pol=pol,window_nm=[lo,hi],wavelength_divisions=wdiv,angle_divisions=adiv,**x) for x in details])
    levels.append(dict(wavelength_points=len(w),angle_points=len(a),condition_points=len(w)*len(a),wavelength_divisions=wdiv,angle_divisions=adiv,
                       max_wavelength_gap_nm=float(np.diff(w).max()),max_angle_gap_deg=float(np.diff(a).max()),extrema=ext,
                       grid_sha256=hashlib.sha256(w.tobytes()+a.tobytes()+data.tobytes()).hexdigest(),strict_grid_R_violation_count=int(np.count_nonzero(data[:,:,0]>.0099)),strict_grid_T_violation_count=int(np.count_nonzero(data[:,:,1]<.9001))))
    if wdiv==6007:
     base=f'{pol}-{int(lo)}';np.savetxt(P/f'{base}-angle-envelope.csv',np.column_stack([a,data[:,:,0].max(axis=1),data[:,:,1].min(axis=1),data[:,:,2].max(axis=1),data[:,:,2].min(axis=1)]),delimiter=',',header='angle_deg,Rmax,Tmin,Amax,Amin',comments='')
     np.savetxt(P/f'{base}-wavelength-envelope.csv',np.column_stack([w,data[:,:,0].max(axis=0),data[:,:,1].min(axis=0),data[:,:,2].max(axis=0),data[:,:,2].min(axis=0)]),delimiter=',',header='wavelength_nm,Rmax,Tmin,Amax,Amin',comments='')
     iw=np.unique(np.r_[np.arange(0,len(w),10),len(w)-1]);ia=np.unique(np.r_[np.arange(0,len(a),3),len(a)-1]);display=data[ia[:,None],iw[None,:],:]
     np.savez_compressed(P/f'{base}-display-grid.npz',wavelength_nm=w[iw],angle_deg=a[ia],R=display[:,:,0],T=display[:,:,1],A=display[:,:,2])
   retained=dict(levels[-1]['extrema'])
   for label,sign in (('Rmax',-1),('Tmin',1),('Amax',-1),('Amin',1)):
    for level in levels:
     ext=level['extrema']
     if sign*ext[label]<sign*retained[label]:
      for suffix in ('','_nm','_angle_deg'):retained[label+suffix]=ext[label+suffix]
   original=next(x for x in author if x['polarization']==pol and x['window_nm']==[lo,hi]);row=dict(polarization=pol,window_nm=[lo,hi],levels=levels,**retained,
          strict_pass=retained['Rmax']<=.0099 and retained['Tmin']>=.9001,R_margin=.0099-retained['Rmax'],T_margin=retained['Tmin']-.9001,
          author_extrema_differences={k:retained[k]-original[k] for k in ('Rmax','Tmin','Amax')},refinement_differences={k:levels[1]['extrema'][k]-levels[0]['extrema'][k] for k in ('Rmax','Tmin','Amax','Amin')})
   selected=[(retained[k+'_nm'],retained[k+'_angle_deg']) for k in ('Rmax','Tmin','Amax','Amin')]
   for wave,angle in selected:
    b=boundary(wave,angle,pol,seq,th);v=scatter([wave],angle,pol,seq,th)[0];difference=float(max(abs(np.array([b[k] for k in ('R','T','A')])-v)))
    result['global_boundary_checks'].append(dict(pol=pol,wavelength_nm=wave,angle_deg=angle,max_abs_RTA_difference=difference,**b))
    high=mp_boundary(wave,angle,pol,seq,th);result['high_precision_checks'].append(dict(pol=pol,wavelength_nm=wave,angle_deg=angle,rta_60_digits=high,max_abs_double_difference=max(abs(float(x)-y) for x,y in zip(high,v))))
   result['windows'].append(row);save('checkpoint.json',result);print(json.dumps({k:row[k] for k in ('polarization','window_nm','Rmax','Rmax_nm','Rmax_angle_deg','Tmin','Tmin_nm','Tmin_angle_deg','strict_pass')}),flush=True)
 # Global boundary crosscheck throughout the domain, including corners and off-grid interiors.
 for pol in ('s','p'):
  for angle in (0.,.193,1.717,4.139,7.113,10.367,13.619,14.863,15.):
   for wave in (3000.,3067.5,3422.94,3719.263,4132.2,4789.131,5000.,8000.,8437.219,9361.373,10573.511,11353.6,12000.):
    b=boundary(wave,angle,pol,seq,th);v=scatter([wave],angle,pol,seq,th)[0]
    result['global_boundary_checks'].append(dict(pol=pol,wavelength_nm=wave,angle_deg=angle,max_abs_RTA_difference=float(max(abs(np.array([b[k] for k in ('R','T','A')])-v))),**b))
 # Self-consistency at normal incidence without averaging polarization powers.
 testw=np.array([3000.,3422.94,4132.2,5000.,8000.,10000.,12000.]);result['normal_s_p_max_abs_RTA_difference']=float(abs(scatter(testw,0,'s',seq,th)-scatter(testw,0,'p',seq,th)).max())
 result['max_boundary_difference']=max(x['max_abs_RTA_difference'] for x in result['global_boundary_checks']);result['max_high_precision_difference']=max(x['max_abs_double_difference'] for x in result['high_precision_checks']);result['max_p_full_E_normalization_difference']=max(abs(x.get('full_E_p_difference',0)) for x in result['global_boundary_checks']);result['max_wrong_p_flux_difference']=max(abs(x.get('wrong_tangential_E_s_flux_T',x['T'])-x['T']) for x in result['global_boundary_checks'])
 after=baseline();changes={key:[n for n in set(before[key])|set(after[key]) if before[key].get(n)!=after[key].get(n)] for key in before};result['stability']=dict(changes=changes,counts={key:len(v) for key,v in before.items()},package_inputs_unchanged=not any(changes.values()))
 result['strict_pass']=all(w['strict_pass'] for w in result['windows']);result['sampling_stats']=STATS;result['elapsed_seconds']=time.monotonic()-started;result['extrema_failures']=[x for x in all_extrema if not x['success']]
 assert not any(changes.values());assert result['max_boundary_difference']<1e-11 and result['max_high_precision_difference']<1e-11 and result['max_p_full_E_normalization_difference']<1e-12
 save('extrema.json',all_extrema);save('summary.json',result)
 print(json.dumps({'strict_pass':result['strict_pass'],'max_boundary_difference':result['max_boundary_difference'],'max_p_full_E_normalization_difference':result['max_p_full_E_normalization_difference'],'max_wrong_p_flux_difference':result['max_wrong_p_flux_difference'],'stats':STATS,'elapsed_seconds':result['elapsed_seconds'],'failed_extrema':len(result['extrema_failures']),'stability':result['stability']},indent=2),flush=True)
if __name__=='__main__':main()
