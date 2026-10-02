"""Original diagrams from T05 synthetic cases. Matplotlib is optional."""
import os,json
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/t05_matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch,Ellipse,Rectangle
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'figures';OUT.mkdir(exist_ok=True)
R=ROOT/'benchmarks/results'
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150})
fig,ax=plt.subplots(2,2,figsize=(11,8),layout='constrained')
a=np.genfromtxt(R/'misspecified_holdout.csv',delimiter=',',names=True)
ax[0,0].plot(a['angle_deg'],a['relative_error_percent'],'o',color='#c35034')
ax[0,0].set(xlabel='Held-out source angle (deg)',ylabel='Point-model error (%)',title='Near-axis fit hides finite-source error')
a=np.genfromtxt(R/'boat_azimuth_holdout.csv',delimiter=',',names=True)
for k,label,c in [('x_truth','Along long boat','#277c91'),('y_truth','Across boat','#8057a4'),('radial_fit_prediction','Point radial fit','#c35034')]:ax[0,1].plot(a['offset_m']*1000,a[k]*1e6,label=label,color=c)
ax[0,1].set(xlabel='Offset (mm)',ylabel='Mass flux (mg / m² / s)',title='An entire azimuth is held out');ax[0,1].legend(fontsize=8)
a=np.genfromtxt(R/'qcm_blind_shape_change.csv',delimiter=',',names=True)
ax[1,0].plot(a['angle_deg'],a['new_over_old'],'o-',color='#277c91');ax[1,0].axhline(1,color='gray',ls='--')
ax[1,0].set(xlabel='Source angle (deg)',ylabel='New / old flux',title='On-axis QCM is exactly unchanged',ylim=(0,1.1))
a=np.genfromtxt(R/'synthetic_thermal_history.csv',delimiter=',',names=True)
ax[1,1].plot(a['time_s'],a['temperature_K'],color='#c35034');ax[1,1].set(xlabel='Time (s)',ylabel='Effective temperature (K)',title='Fictional single-phase thermal response')
b=ax[1,1].twinx();b.plot(a['time_s'],a['power_W'],color='#277c91',alpha=.55);b.set_ylabel('Input power (W)',color='#277c91')
fig.suptitle('T05 synthetic diagnostics | No machine or production data',fontsize=14)
fig.savefig(OUT/'synthetic_diagnostics.png');fig.savefig(OUT/'synthetic_diagnostics.svg');plt.close(fig)

fig,ax=plt.subplots(figsize=(12,6.5),layout='constrained');ax.set(xlim=(0,12),ylim=(0,6.5));ax.axis('off')
def box(x,y,w,h,text,color='#e5f0f3'):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.10',fc=color,ec='#54737f',lw=1));ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=10)
def arrow(x1,y1,x2,y2,label=None):
 ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=13,color='#355460',lw=1.4))
 if label:ax.text((x1+x2)/2,(y1+y2)/2+.12,label,ha='center',va='bottom',fontsize=8)
box(.2,4.6,2.4,1.05,'Identity + source history\nlot, liner, fill, cycles')
box(3.25,4.6,2.35,1.05,'Heat / material state\nT, phase, composition')
box(6.25,4.6,2.35,1.05,'Emission\nQ(t) × q(s,t) × f(Ω)')
box(9.25,4.6,2.45,1.05,'Transport + geometry\nT02 kernel, T03 mask')
arrow(2.7,5.1,3.15,5.1);arrow(5.7,5.1,6.15,5.1);arrow(8.7,5.1,9.15,5.1)
box(.2,2.5,2.4,1.05,'Electrical inputs\nV I, beam path, logs');arrow(2.7,3,4.4,4.5,'absorbed power')
box(9.25,2.5,2.45,1.05,'Arrival mass flux j\nkg / m² / s');arrow(10.5,4.5,10.5,3.65)
box(6.25,.45,2.35,1.2,'QCM observation\nfrequency, Z, density\ntooling, drift','#f8eadf')
box(9.25,.45,2.45,1.2,'Film state\nd, density, n / k\ncomposition, defects','#f8eadf')
arrow(10.0,2.4,7.5,1.75,'sensor geometry');arrow(10.5,2.4,10.5,1.75,'retention / reaction')
box(.2,.45,5.4,1.2,'Independent calibration and held-out validation\nspatial coupons + source evidence + mass / optical metrology','#e9eadf')
arrow(6.15,1.05,5.7,1.05);arrow(2.9,1.75,2.9,4.2);ax.text(3.06,3.0,'Calibration',rotation=90,ha='left',va='center',fontsize=9)
ax.text(6,6.15,'T05 source model data flow',ha='center',fontsize=16,weight='bold')
ax.text(6,2.05,'A stable QCM signal alone cannot certify Q, shape, or film composition',ha='center',fontsize=11,color='#99442c')
fig.savefig(OUT/'source_model_dataflow.png');fig.savefig(OUT/'source_model_dataflow.svg');plt.close(fig)

fig,ax=plt.subplots(figsize=(11,4.6),layout='constrained');ax.set(xlim=(-1,10),ylim=(-1,4.2));ax.axis('off')
for off,title in [(0,'Resistive boat'),(5.5,'Electron-beam source')]:
 ax.plot([off,off+.4,off+2.3,off+2.7],[1.2,.7,.7,1.2],lw=5,color='#7e8c90')
 ax.plot([off+.7,off+1.9],[.9,.9],lw=7,color='#cf885e')
 ax.text(off+1.35,-.05,title,ha='center',fontsize=13)
 ax.text(off+1.35,3.6,'Receiver: separate cos(incidence)',ha='center',fontsize=10)
 ax.plot([off-.3,off+3],[3,3],color='#315f72',lw=6)
 for s,end in [(off+.8,off-.1),(off+1.4,off+1.5),(off+1.9,off+2.8)]:ax.add_patch(FancyArrowPatch((s,1.05),(end,2.9),arrowstyle='-|>',mutation_scale=10,color='#b65840',alpha=.7))
 ax.text(off+1.35,2.1,'Q × normalized angular law',ha='center',fontsize=9,color='#943d2e')
ax.text(1.35,-.6,'Finite hot region; contact + thermal lag',ha='center',fontsize=10)
ax.text(6.85,-.6,'Moving emission footprint; recess + cooling',ha='center',fontsize=10)
ax.annotate('Beam heating ≠ emitted-mass footprint',xy=(6.8,1),xytext=(8.4,1.7),ha='center',fontsize=9,arrowprops={'arrowstyle':'->','color':'#8057a4'},color='#8057a4')
fig.savefig(OUT/'source_geometry.png');fig.savefig(OUT/'source_geometry.svg');plt.close(fig)
print('Wrote 3 PNG + 3 SVG original figures')
