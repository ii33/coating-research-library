from pathlib import Path
import json,os
os.environ.setdefault("MPLCONFIGDIR","/tmp/t05-matplotlib")
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from qcm_flux import mass_areal,point_kernel
R=Path(__file__).resolve().parents[1]
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#fafafa','axes.facecolor':'#fafafa','svg.hashsalt':'T05-QCM-R2'})
def save(fig,name):
 fig.savefig(R/'figures'/f'{name}.svg',bbox_inches='tight',metadata={'Date':None});fig.savefig(R/'figures'/f'{name}.png',dpi=160,bbox_inches='tight');plt.close(fig)
fig,ax=plt.subplots(figsize=(11,3.8));ax.axis('off')
boxes=[('Raw f(t), f0, mode\nindependent drift model',(0.02,.56)),('Areal mass mQ(t)\nrigid acoustic model',(.28,.56)),('Net mass rate\nGLS / side-term balance',(.55,.56)),('Incident source mass\ncapture etaQ required',(.79,.56)),('Known source geometry\nKQ, KW, n, anisotropy',(.28,.1)),('Workpiece incident flux\nper ACTUAL area',(.55,.1)),('Species -> element nuclei\nnot net film thickness',(.79,.1))]
for text,(xx,yy) in boxes:ax.text(xx,yy,text,transform=ax.transAxes,va='center',bbox=dict(boxstyle='round,pad=.6',fc='#e6eff3',ec='#547886'))
for start,end in [((.23,.56),(.28,.56)),((.51,.56),(.55,.56)),((.75,.56),(.79,.56)),((.9,.42),(.68,.23)),((.51,.1),(.55,.1)),((.76,.1),(.79,.1))]:ax.annotate('',xy=end,xytext=start,xycoords='axes fraction',arrowprops={'arrowstyle':'->','color':'#547886'})
fig.suptitle('QCM to arrival-flux contract | unknown calibration blocks inversion',weight='bold');save(fig,'01_transfer_contract')
loss=np.linspace(1e-6,.1,250);f0=6045000.;fig,ax=plt.subplots(figsize=(7,4));
for z in [.5,1,1.08,2]:
 zmatch=mass_areal(f0*(1-loss),f0,z);small=mass_areal(f0*(1-loss),f0,z,'sauerbrey');ax.plot(loss*100,(zmatch/small-1)*100,label=f'Z ratio = {z}')
ax.set(xlabel='Fundamental fractional frequency loss (%)',ylabel='Z-match / Sauerbrey - 1 (%)',title='Finite-load model difference (no validity guarantee)');ax.legend();ax.grid(alpha=.2);save(fig,'02_finite_load')
angles=np.linspace(0,65,151)*np.pi/180;x=np.c_[.5*np.tan(angles),np.zeros_like(angles),np.full_like(angles,.5)];norm=np.tile([0,0,-1],(len(x),1));j0=2e-6*point_kernel(x,norm,1);j1=1e-6*point_kernel(x,norm,3)
fig,ax=plt.subplots(figsize=(7,4));ax.plot(angles*180/np.pi,j0/j0[0],label='Q=2e-6 kg/s, n=1');ax.plot(angles*180/np.pi,j1/j0[0],label='Q=1e-6 kg/s, n=3');ax.scatter([0],[1],color='#b64b43',zorder=4,label='Identical single axial QCM');ax.set(xlabel='Source angle (degrees)',ylabel='Flux / common axial QCM flux',title='Equal QCM signal does not establish spatial shape');ax.legend();ax.grid(alpha=.2);save(fig,'03_blind_shape_change')
d=json.loads((R/'verification/diagnostics.json').read_text());labels=['1 QCM','6 QCM\nknown capture','6 QCM\nunknown capture','6 QCM +\nindependent Q'];vals=list(d['identifiability'].values());fig,ax=plt.subplots(figsize=(7,4));ii=np.arange(4);ax.bar(ii-.16,[v['rank'] for v in vals],.32,label='Matrix rank');ax.bar(ii+.16,[v['columns'] for v in vals],.32,label='Unknown count');ax.set(xticks=ii,xticklabels=labels,ylabel='Count',title='Extra data must add an independent parameter direction');ax.set_ylim(0,5);ax.legend();save(fig,'04_identifiability')
