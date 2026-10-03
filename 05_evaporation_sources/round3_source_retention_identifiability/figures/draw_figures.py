from pathlib import Path
import sys,json,math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
R=Path(__file__).resolve().parents[1];d=json.loads((R/'data/tiny_results.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#f6f8fb','axes.facecolor':'white','savefig.facecolor':'#f6f8fb'})
C=['#136b9d','#d46535','#5c548e','#33836c']
def save(fig,name):
 for ext in ['png','svg']:fig.savefig(R/f'figures/{name}.{ext}',dpi=170,bbox_inches='tight')
 plt.close(fig)
fig,ax=plt.subplots(figsize=(12,5.8));ax.set_axis_off();ax.set_xlim(0,12);ax.set_ylim(0,6)
boxes=[(.2,3.25,2.35,1.25,'SOURCE\nQ total [kg/s]\nf [1/sr], sum(w)=1'),(3.05,3.25,2.4,1.25,'GEOMETRY\nvisibility x cos(incidence)\n/ distance squared'),(6,3.25,2.5,1.25,'WORKPIECE MASS\ns0 [1-a sin^2(theta)]\nretention separate'),(9.05,3.25,2.7,1.25,'PHYSICAL THICKNESS\nmass / film density\nQCM density is not rho'),(3.05,1.05,2.4,1.1,'QCM BRANCH\neta_Q x incident flux\nnot workpiece retention')]
for i,(x,y,w,h,t) in enumerate(boxes):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.07',fc='white',ec=C[i%4],lw=1.7));ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=10)
for x1,y1,x2,y2 in [(2.62,3.88,2.97,3.88),(5.53,3.88,5.9,3.88),(8.58,3.88,8.96,3.88),(4.25,3.17,4.25,2.25)]:ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=15,color='#405266'))
ax.text(.15,5.35,'Keep source shape, capture, retention and density separate',fontsize=17,fontweight='bold')
ax.text(6.15,1.55,'Frozen T04 bridge: Lambert only\nQ intensity = Q total / pi, exactly once\nFull forward + hashes + unknown guards retained',fontsize=11,va='center')
ax.text(.2,.25,'Source clock controls Q and sweep; pose clock controls workpiece motion. Synthetic diagnostic contract.',color='#4b6070')
save(fig,'01_contract')
fig,axes=plt.subplots(1,2,figsize=(11.8,4.8),gridspec_kw={'width_ratios':[1.2,1]});g=d['exact_global_ambiguity'];a=axes[0]
a.plot(g['angles_deg'],np.array(g['parallel_A'])*1e9,color=C[0],label='A: n=3, a=0',lw=2.5);a.scatter(g['angles_deg'],np.array(g['parallel_B'])*1e9,facecolors='none',edgecolors=C[1],s=70,label='B: n=1, a=1; Q doubled',zorder=3)
a.set(xlabel='Source angle = incidence angle [deg]',ylabel='Thickness rate [nm/s]',title='All parallel witnesses coincide');a.legend(fontsize=9);a.grid(alpha=.2)
a=axes[1];rat=[g['axis_QCM_B']/g['axis_QCM_A'],g['off_axis_QCM_B']/g['off_axis_QCM_A'],g['tilted_witness_B']/g['tilted_witness_A']];a.bar(['On-axis\nQCM','Off-axis\nQCM 45 deg','Tilted\nwitness'],rat,color=[C[2],C[0],C[1]],width=.55);a.axhline(1,color='#555',ls='--',lw=1);a.set(ylabel='Prediction B / prediction A',ylim=(0,2.4),title='New directions break this ambiguity')
for i,x in enumerate(rat):a.text(i,x+.05,f'{x:.0f}x',ha='center',fontweight='bold')
fig.suptitle('A global counterexample, not just an optimizer failure',fontsize=17,fontweight='bold');fig.text(.05,.005,'SYNTHETIC: same QCM capture and film density. These are not machine observations.',color='#4b6070');fig.tight_layout(rect=[0,.045,1,.91]);save(fig,'02_exact_ambiguity')
fig,axes=plt.subplots(1,2,figsize=(11.8,4.9));a=axes[0]
for key,label,col in [('unanchored_multidirection','8 observations, no scale anchors',C[1]),('anchored_multidirection','10 observations, Q and rho anchors',C[0])]:
 s=d[key]['singular_values'];a.semilogy(range(1,len(s)+1),np.maximum(s,1e-14),'-o',label=label,color=col)
a.set(xlabel='Singular value index',ylabel='Singular value (display floor 1e-14)',title='Declared parameter scales = 1');a.legend(fontsize=8,loc='lower left');a.grid(alpha=.2)
a=axes[1];labels=['Single\nQCM','Multiple\ndirections','Plus Q, rho\nanchors','Separate eta\nper QCM'];ranks=[1,5,7,9];cols=[7,7,7,10];a.bar(range(4),cols,color='#dce4eb',label='unknown count');a.bar(range(4),ranks,color=[C[2],C[1],C[0],C[3]],label='local rank');a.set_xticks(range(4),labels);a.set(ylim=(0,11.3),ylabel='Rank / parameter count',title='More sensors still need assumptions')
for i,(r,c) in enumerate(zip(ranks,cols)):a.text(i,c+.25,f'{r}/{c}',ha='center',fontweight='bold')
a.legend(fontsize=8);fig.suptitle('Conditional identifiability in the seven-parameter family',fontsize=17,fontweight='bold');fig.text(.05,.005,'SYNTHETIC nominal point. Full column rank is necessary locally, not a global or physical certificate.',color='#4b6070');fig.tight_layout(rect=[0,.055,1,.91]);save(fig,'03_identifiability')
print('3 PNG and 3 SVG rendered')
