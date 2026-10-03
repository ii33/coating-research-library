from pathlib import Path
import json,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/t03r3_matplotlib')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/t03r3_fontcache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
R=Path(__file__).resolve().parents[1];d=json.loads((R/'data/tiny_results.json').read_text())
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','axes.titleweight':'bold'})
fig,ax=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
b=np.linspace(0,.11,101);h=(.08-b)*(1/.4-1/.6)-1e-12
ax[0].plot(b,h,color='#225ea8',label='Fixed lower-face margin')
ax[0].axhline(0,color='#333333',lw=1);ax[0].axvline(.08,color='#b2182b',ls='--',label='Face tie (0.08 m)')
ax[0].axvline(d['clipped_plate_shift_m'],color='#238443',ls=':',lw=2,label='Clipped step (~0.064 m)')
ax[0].set(xlabel='Plate translation b (m)',ylabel='Projected face gap (m)',title='A. Affine branch guard');ax[0].legend(loc='upper right',fontsize=9)
a=np.linspace(0,1,101);ax[1].plot(a,1-a,label='First-order model',color='#225ea8');ax[1].plot(a,1-a-4*a*a,label='True nonlinear guard',color='#b2182b');ax[1].axhline(0,color='#333333',lw=1)
ax[1].axvline(.8,color='#666666',ls=':',label='Heuristic step 0.8');ax[1].scatter([.8],[-2.36],color='#b2182b',zorder=5)
ax[1].set(xlabel='Step alpha (unitless)',ylabel='Guard value (unitless)',title='B. Missing curvature breaks safety');ax[1].legend(fontsize=9)
fig.suptitle('Topology limits: exact affine evidence versus a first-order screen',fontsize=15)
fig.savefig(R/'figures/01_topology_step.png',dpi=180);fig.savefig(R/'figures/01_topology_step.svg');plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
e=d['event_aware_local_trial'];recs=[e['baseline'],e['trial'],e['baseline']];labels=['Baseline','Event-aware step','Omitted-event zero step'];colors=['#666666','#238443','#b2182b']
for i,(r,c) in enumerate(zip(recs,colors)):
 lo,hi=r['objective_interval'].values();mid=r['objective_estimate'];ax[0].errorbar(mid,i,xerr=[[mid-lo],[hi-mid]],fmt='o',color=c,capsize=5,elinewidth=3)
ax[0].set(yticks=range(3),yticklabels=labels,xlabel='J = 0.5 [(D - 1) / 1]^2 (unitless)',title='A. Qualified objective intervals');ax[0].invert_yaxis();ax[0].grid(axis='x',alpha=.2)
s=d['baseline_derivative_decomposition'];x=np.arange(2);width=.24
ax[1].bar(x-width,[s['target_shift_smooth_only'],s['half_width_smooth_only']],width,label='Smooth only',color='#9ecae1')
ax[1].bar(x,[s['target_shift_total']-s['target_shift_smooth_only'],s['half_width_total']],width,label='Event term',color='#238443')
ax[1].bar(x+width,[s['target_shift_total'],s['half_width_total']],width,label='Total',color='#225ea8')
ax[1].axhline(0,color='#333333',lw=1);ax[1].set(xticks=x,xticklabels=['Target shift u','Plate half-width a'],ylabel='dD / dp  ((s/m²) / m)',title='B. Retained derivative counterexamples');ax[1].legend(fontsize=9)
ax[1].annotate('Sign reversal at u',xy=(0,.69),xytext=(-.3,-4.),arrowprops={'arrowstyle':'->'},fontsize=10)
fig.suptitle('Same frozen finite-source objective; no physical or continuum certification',fontsize=14)
fig.savefig(R/'figures/02_objective_and_gradients.png',dpi=180);fig.savefig(R/'figures/02_objective_and_gradients.svg');plt.close(fig)
print('Rendered two PNG and two SVG figures from tiny_results')
