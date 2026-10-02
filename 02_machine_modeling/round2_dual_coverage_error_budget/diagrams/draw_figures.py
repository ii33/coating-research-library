from pathlib import Path
import json,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle,Ellipse
ROOT=Path(__file__).resolve().parents[1]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150})

def save(fig,name):
    fig.savefig(ROOT/'diagrams'/f'{name}.svg',bbox_inches='tight');fig.savefig(ROOT/'diagrams'/f'{name}.png',bbox_inches='tight');plt.close(fig)

def geometry():
    fig,ax=plt.subplots(1,2,figsize=(11.5,4.5),gridspec_kw={'width_ratios':[1.5,1]})
    a=ax[0]
    for x,col,label in [(.18,'#db8a29','Vapor disk / n = 1'),(-.62,'#247d9d','Ion aperture / n = 12')]:
        a.add_patch(Ellipse((x,0),.1,.018,color=col,alpha=.8));a.text(x-.08,-.065,label,color=col,fontsize=9)
    a.add_patch(Rectangle((.17,.19),.08,.025,color='#555555'));a.add_patch(Rectangle((-.49,.085),.12,.03,color='#555555'))
    a.plot([.17,.30],[.6,.6],lw=4,color='#333333');a.text(.13,.65,'Moving substrate W',fontsize=10)
    for s,col in [(.16,'#db8a29'),(.20,'#db8a29'),(-.64,'#247d9d'),(-.60,'#247d9d')]:
        a.annotate('',(.26,.6),(s,0),arrowprops={'arrowstyle':'->','color':col,'lw':1.3,'alpha':.65})
    a.annotate('receiver normal n',(.23,.48),(.31,.48),fontsize=9)
    a.annotate('',(.23,.48),(.23,.60),arrowprops={'arrowstyle':'->','color':'black'})
    a.text(-.64,.45,'Independent rays\nSame opaque solids\nOne common clock',fontsize=11)
    a.set(xlim=(-.8,.5),ylim=(-.11,.74),xlabel='x in chamber L (schematic)',ylabel='z');a.set_title('Unified ray and normal contract')
    b=ax[1];b.add_patch(Rectangle((-1,-.1),2,.2,color='#666666',alpha=.55));b.axhline(0,color='#666',ls='--',lw=.7)
    b.plot([-.9,3.1],[-.2,.2],color='#a44e3a',lw=2);b.scatter([1.1],[0],color='#a44e3a');b.scatter([.1],[-.1],color='#247d9d')
    b.annotate('Misses mid-plane rectangle',(1.1,0),(.25,.22),arrowprops={'arrowstyle':'->'},fontsize=9)
    b.annotate('Hits finite solid',(.1,-.1),(-1.1,-.30),arrowprops={'arrowstyle':'->'},fontsize=9)
    b.set(xlim=(-1.4,3.2),ylim=(-.37,.34),xlabel='plate-local u',ylabel='plate-local w');b.set_title('Finite thickness changes visibility')
    fig.suptitle('Original synthetic modeling diagram | no machine reconstruction',fontsize=12);fig.tight_layout();save(fig,'01_ray_normal_thick_plate')

def diagnostics():
    d=np.genfromtxt(ROOT/'data/B_penumbra.csv',delimiter=',',names=True);r=json.loads((ROOT/'data/results.json').read_text())
    fig,ax=plt.subplots(1,3,figsize=(13,4))
    ax[0].plot(d['x_m'],d['thin_transmission'],label='thin');ax[0].plot(d['x_m'],d['thick_transmission'],label='thick 0.06 m');ax[0].set(xlabel='receiver x (m)',ylabel='visible flux fraction',title='B | finite-source penumbra');ax[0].legend()
    vals=[q['max_relative_integral_difference'] for q in r['C']['diagnostic_axis']];labels=['S0-S1','S1-S2','T0-T1','T1-T2','cross','holdout']
    ax[1].bar(labels,100*np.array(vals),color=['#a44e3a' if v>.003 else '#247d9d' for v in vals]);ax[1].axhline(.3,color='k',ls='--',label='0.3% target');ax[1].set(ylabel='max integral difference / mean (%)',title='C | independent refinement axes');ax[1].tick_params(axis='x',rotation=45);ax[1].legend()
    vals=[q['ion_only_max_difference_s']*1000 for q in r['C']['diagnostic_axis']]
    ax[2].bar(labels,vals,color=['#a44e3a' if v>10 else '#247d9d' for v in vals]);ax[2].axhline(10,color='k',ls='--',label='10 ms target');ax[2].set(ylabel='ion-only time difference (ms)',title='C | unresolved indicator integral');ax[2].tick_params(axis='x',rotation=45);ax[2].legend()
    fig.suptitle('Differences are empirical evidence, not certified error bounds',fontsize=12);fig.tight_layout();save(fig,'02_penumbra_and_errors')

def maps():
    d=np.genfromtxt(ROOT/'data/C_main_map.csv',delimiter=',',names=True);fig,ax=plt.subplots(1,3,figsize=(12,4.1))
    for a,key,title in zip(ax,['h_nm','ion_fluence_m2','ion_to_net_atom_ratio'],['h (nm)','Ion fluence (1/m2)','Integrated ion / net atom']):
        z=d[key];sc=a.scatter(d['x_local_m']*1e3,d['y_local_m']*1e3,c=z,s=25,cmap='viridis');a.set(aspect='equal',xlabel='local x (mm)',ylabel='local y (mm)',title=title);fig.colorbar(sc,ax=a,fraction=.05,pad=.03)
    fig.suptitle('C | S1 / T1 / P2 sampled fields | source/time accuracy NOT fully accepted',fontsize=12);fig.tight_layout();save(fig,'03_dual_maps')
if __name__=='__main__':geometry();diagnostics();maps()
