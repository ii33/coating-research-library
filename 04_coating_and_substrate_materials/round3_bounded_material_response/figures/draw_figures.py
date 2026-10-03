from pathlib import Path
import sys,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'models'))
from bounded_response import *
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white','axes.titlesize':13})
colors={'A':'#2166ac','B':'#c46018'}
def save(fig,name):
 fig.savefig(R/f'figures/{name}.png',dpi=180,bbox_inches='tight');fig.savefig(R/f'figures/{name}.svg',bbox_inches='tight');plt.close(fig)
fig,ax=plt.subplots(figsize=(12,4.5));ax.set_axis_off()
blocks=[(.02,.4,.26,.42,'Frozen T03 forward','poses + clock + finite source\nvisibility events + D interval\nfull event / smooth gradients'),(.36,.4,.28,.42,'Material response layer','Q, retention, film density\nangle / energy / temperature\nnet mass + inventory guard'),(.73,.4,.25,.42,'Qualified output','signed thickness interval\nrelative objective interval\ndisjoint: rank\noverlap: unresolved')]
for x,y,w,h,title,body in blocks:
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.01',facecolor='#eef3f7',edgecolor='#9baebe'));ax.text(x+w/2,y+h-.08,title,ha='center',fontweight='bold');ax.text(x+w/2,y+.19,body,ha='center',va='center',linespacing=1.6)
for a,b in [(.285,.35),(.65,.72)]:ax.annotate('',xy=(b,.6),xytext=(a,.6),arrowprops={'arrowstyle':'->','lw':2})
ax.text(.5,.21,'Literature evidence defines missing measurements; it does not fill unknown coefficients',ha='center',fontsize=12)
ax.text(.5,.08,'Synthetic bounded law only  |  Real material calibration: unknown  |  No physical certification',ha='center',color='#833b2a')
ax.set_title('T04 bounded material response contract',pad=18);save(fig,'01_response_contract')
d=json.loads((R/'data/tiny_results.json').read_text())['cases']
fig,axes=plt.subplots(1,3,figsize=(13.5,4.5),sharey=True)
for ax,name,title in zip(axes,['unit_response','angular_response','angular_uncertain'],['Unit response: B better','Angle response: A better','Angle uncertainty: unresolved']):
 for i,k in enumerate(['A','B']):
  lo,hi=d[name][k]['objective_interval'];ax.plot([lo,hi],[1-i,1-i],lw=7,color=colors[k],solid_capstyle='butt');ax.scatter([(lo+hi)/2],[1-i],s=38,color=colors[k]);ax.text(lo,.15+1-i,f'{lo:.2g} to {hi:.2g}',fontsize=9)
 ax.set_yticks([0,1],['B','A']);ax.set_ylim(-.5,1.5);ax.set_xlim(-.0004,.0105);ax.grid(axis='x',alpha=.2);ax.set_xlabel('Relative thickness objective J');ax.set_title(title)
fig.suptitle('Same frozen candidates and 1 nm target; synthetic material scenarios',y=1.03,fontsize=15);fig.tight_layout();save(fig,'02_ranking_intervals')
fig,axes=plt.subplots(1,2,figsize=(12,4.5));theta=np.linspace(0,85,300)
axes[0].plot(theta,np.ones_like(theta),label='unit retention',color='#555');axes[0].plot(theta,np.cos(np.deg2rad(theta))**2,label='synthetic angle law',color='#2166ac');axes[0].fill_between(theta,np.cos(np.deg2rad(theta))**2,1,color='#2166ac',alpha=.16,label='a in [0, 1]');axes[0].set_xlabel('Arrival angle to surface normal (deg)');axes[0].set_ylabel('Retention factor (dimensionless)');axes[0].set_title('A response factor changes kernel shape');axes[0].legend(loc='lower left',fontsize=10);axes[0].grid(alpha=.2)
x=np.array([0,1]);axes[1].bar(x-.17,[1,1],.32,label='geometric D',color='#a5b7c5');axes[1].bar(x+.17,[1,.25],.32,label='retained transfer',color='#2166ac');axes[1].set_xticks(x,['all flux at 0 deg','all flux at 60 deg']);axes[1].set_ylim(0,1.3);axes[1].set_ylabel('Transfer (s/m2)');axes[1].set_title('Equal integrated D loses angle information');axes[1].legend(loc='upper right',fontsize=10)
fig.suptitle('Synthetic counterexample only; no measured material coefficients',y=1.03,fontsize=15);fig.tight_layout();save(fig,'03_kernel_shape')
