"""Original illustrative plots from packaged synthetic data only."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/t04r2_matplotlib')
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
ROOT=Path(__file__).resolve().parents[1]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':160})
def save(fig,name):
    for ext in ('png','svg'):fig.savefig(ROOT/'figures'/f'{name}.{ext}',bbox_inches='tight',facecolor=fig.get_facecolor())
    plt.close(fig)
fig,ax=plt.subplots(figsize=(12,6));fig.patch.set_facecolor('#f6f8fa');ax.axis('off');ax.set_xlim(0,12);ax.set_ylim(0,6)
boxes=[(.2,3.6,3.3,1.5,'Conditioned observations\nFilm + substrate identity\nElement inventories, density\nJoint spectra + time history','#e3eef7'),
 (4.2,3.6,3.3,1.5,'Contract gates\nUnits + complete atom basis\nBounds + evidence + state\nNo guessed material constants','#ddeee5'),
 (8.2,3.6,3.5,1.5,'Conditional integrals\nN_net, D, U\nh only for invariant film state\nR, epsilon: stable positive N','#e3eef7'),
 (4.2,.6,3.3,1.55,'Keep blocked outcomes\nUnknown / partial inputs\nErosion / exhausted film\nNear-zero denominator','#fbe6df'),
 (8.2,.6,3.5,1.55,'Material response evidence\nn/k, stress, adhesion\nMeasurement or validated model\nNo dose-only prediction','#efe7f7')]
for x,y,w,h,t,c in boxes:
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.12',linewidth=0,facecolor=c));ax.text(x+w/2,y+h/2,t,ha='center',va='center',linespacing=1.5)
for a,b in [((3.6,4.35),(4.05,4.35)),((7.6,4.35),(8.05,4.35)),((5.85,3.4),(5.85,2.35)),((9.95,3.4),(9.95,2.35))]:ax.annotate('',b,a,arrowprops={'arrowstyle':'->','lw':1.8,'color':'#415a6b'})
ax.text(.1,5.8,'Material response input contract',fontsize=19,fontweight='bold');ax.text(.1,.05,'Original interface diagram | no process qualification | all seven uncertainty axes retained',fontsize=10,color='#536471')
save(fig,'01_contract_flow')
c=json.loads((ROOT/'verification/synthetic_calibration.json').read_text());fig,axs=plt.subplots(1,2,figsize=(11,4.7),constrained_layout=True)
for ax,key,title in zip(axs,['rows','unidentifiable_rows'],['Independent input variation','Fixed ion-to-arrival ratio']):
    rows=c[key];sc=ax.scatter([r['arrival'] for r in rows],[r['energetic'] for r in rows],c='#267c81',s=90,edgecolor='white')
    ax.set_ylim(0.12,0.82) if key=='rows' else ax.set_ylim(0.3,3.5)
    ax.set(xlabel='Arrival F  [10$^{18}$ atoms m$^{-2}$ s$^{-1}$]',ylabel='Energetic flux  [10$^{18}$ particles m$^{-2}$ s$^{-1}$]',title=title);ax.grid(alpha=.15)
    if key=='unidentifiable_rows':ax.plot([1,6],[.5,3],color='#9c3442',alpha=.7);ax.text(.04,.93,'Only eta - 0.5 Y is identifiable',transform=ax.transAxes,color='#9c3442')
    else:ax.text(.04,.93,'eta = 0.8424, Y = 0.3275 (toy fit)',transform=ax.transAxes)
fig.suptitle('Synthetic identification: more points do not repair a rank-deficient design',fontsize=14)
save(fig,'02_identifiability')
x=json.loads((ROOT/'verification/example_results.json').read_text());fig,ax=plt.subplots(figsize=(10,4.6),constrained_layout=True)
for i,name in enumerate(['positive','ill_conditioned','cross_zero','zero','erosion']):
    o=x[name];lo,hi=[v/1e19 for v in o['N_net']['interval']];mid=o['N_net']['value']/1e19;color='#2b7a62' if name=='positive' else '#ad4747'
    ax.plot([lo,hi],[i,i],lw=7,color=color,solid_capstyle='round');ax.scatter([mid],[i],color='black',s=24,zorder=4)
    ax.text(4.0,i,o['ratio_conditioning'],va='center',fontsize=10)
ax.axvline(0,color='#333',lw=1,ls='--');ax.set_yticks(range(5),['Positive','Ill-conditioned','Crossing zero','Zero','Erosion']);ax.set_xlim(-2.5,7);ax.invert_yaxis();ax.set_xlabel('Signed net atom fluence [10$^{19}$ atoms m$^{-2}$]');ax.set_title('Only a well-conditioned strictly positive denominator supports R and epsilon');ax.grid(axis='x',alpha=.15)
save(fig,'03_denominator_states')
print('six original figure files written')
