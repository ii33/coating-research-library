"""Portable phase1 research optics: no product imports or local workstation paths."""
import json,math
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
BUNDLE=ROOT.parent/'normal_incidence'
MATERIALS={}
for row in json.loads((BUNDLE/'materials/sources.json').read_text(encoding='utf-8'))['materials']:
 data=np.genfromtxt(BUNDLE/row['data_file'],delimiter=',',names=True)
 MATERIALS[row['id']]={k:data[k] for k in ('wavelength_nm','n','k')}
PRES={r:json.loads((BUNDLE/'prescriptions'/f'{r}.json').read_text(encoding='utf-8'))['layers'] for r in ('A','B')}
def nk(material,w):
 data=MATERIALS[material];x=data['wavelength_nm'];w=np.asarray(w,float)
 if min(w)<x[0] or max(w)>x[-1]:raise ValueError('outside actual n/k domain: '+material)
 return np.interp(w,x,data['n'])+1j*np.interp(w,x,data['k'])

def qz(n,beta):
 q=np.sqrt(n*n-beta*beta+0j)
 return np.where((q.imag<0)|((q.imag==0)&(q.real<0)),-q,q)

def admittance(n,beta,pol):
 q=qz(n,beta);return q if pol=='s' else n*n/q

def characteristic(w,layers,beta,pol,substrate_override=None):
 w=np.asarray(w,float);a=np.ones(len(w),complex);b=np.zeros(len(w),complex);c=b.copy();d=a.copy()
 for j,layer in enumerate(layers):
  n=nk(layer['material'],w);q=qz(n,beta);y=q if pol=='s' else n*n/q
  delta=2*np.pi*q*layer['thickness_nm']/w
  if substrate_override is not None and layer.get('bulk'):
   delta=np.full(len(w),substrate_override,complex)+1j*delta.imag
  co=np.cos(delta);si=-1j*np.sin(delta)
  a,b,c,d=a*co+b*y*si,a*si/y+b*co,c*co+d*y*si,c*si/y+d*co
 return a,b,c,d

def block(w,layers,nin,nout,beta,pol):
 y0=admittance(nin,beta,pol);ys=admittance(nout,beta,pol)
 a,b,c,d=characteristic(w,layers,beta,pol);den=y0*(a+b*ys)+c+d*ys
 r=(y0*(a+b*ys)-c-d*ys)/den;t=2*y0/den
 return {'r':r,'t':t,'R':abs(r)**2,'T':ys.real/y0.real*abs(t)**2}

def spectrum(case,w):
 w=np.asarray(w,float);air=np.ones(len(w),complex);beta=math.sin(math.radians(case['angle_deg']));ns=nk('ZnS',w)
 if case['model']=='coating_on_ZnS_halfspace':
  out=block(w,PRES[case['route']][::-1],air,ns,beta,case['polarization']);r,t=out['R'],out['T']
 else:
  front=[] if case['front']=='bare' else PRES[case['front']][::-1]
  back=[] if case['back']=='bare' else PRES[case['back']]
  f=block(w,front,air,ns,beta,'s');rev=block(w,front[::-1],ns,air,beta,'s');b=block(w,back,ns,air,beta,'s')
  P=np.exp(-4*np.pi*qz(ns,beta).imag*case['thickness_mm']*1e6/w);den=1-rev['R']*b['R']*P*P
  r=f['R']+f['T']*rev['T']*b['R']*P*P/den;t=f['T']*b['T']*P/den
 return np.column_stack([r,t,1-r-t])
