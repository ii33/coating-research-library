"""Original explanatory diagrams; synthetic numbers are labelled as such."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,Rectangle
ROOT=Path(__file__).resolve().parents[1]
fig,ax=plt.subplots(figsize=(12,5.7));ax.set_xlim(0,12);ax.set_ylim(0,5.7);ax.axis('off')
ax.text(.2,5.35,'T03: uncertainty-aware dual-channel plate search',fontsize=17,weight='bold')
labels=[(.3,3.55,2.5,1.05,'Binary two-plate design\nfeature / support / collision'),(3.2,3.55,2.6,1.05,'Separate vapor + ion rays\nclear / blocked / unknown'),(6.2,3.55,2.4,1.05,'Intervals + error sources\nN, h, D, U, R, epsilon, tau'),(9.0,3.55,2.5,1.05,'Qualified constraints\ninterval Pareto comparison')]
for x,y,w,h,text in labels:
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.06',facecolor='#e4f0f5',edgecolor='#315469'));ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=10)
for x in (2.85,5.86,8.66): ax.annotate('',xy=(x+.3,4.07),xytext=(x,4.07),arrowprops={'arrowstyle':'->','lw':2})
ax.text(.3,2.83,'Both plates are binary and opaque to BOTH channels',fontsize=11,weight='bold')
for offset in (0,1.8):
 for i in range(3):
  for j in range(3):
   solid=(i==0 or i==1 and j==1)
   ax.add_patch(Rectangle((.45+offset+.38*i,1.18+.38*j),.35,.35,facecolor='#274b60' if solid else 'white',edgecolor='#89a0ae'))
ax.text(.45,.83,'Two supported cell grids; no gray fabricated cells',fontsize=9)
ax.text(4.4,2.55,'If intervals overlap:',fontsize=12,weight='bold',color='#9a5d0b')
ax.text(4.4,2.04,'inconclusive, keep both candidates',fontsize=12,color='#9a5d0b')
ax.text(4.4,1.55,'Request named local source / time / space refinement',fontsize=10)
ax.text(4.4,1.18,'Geometry / calibration / model gaps need evidence',fontsize=10)
ax.text(4.4,.7,'Reserve budget -> evaluate -> atomic checkpoint',fontsize=10)
ax.text(.3,.2,'Finite fixture and conditional bounds only. Full T02 oracle remains partial; device validation pending.',fontsize=10,color='#7c2530')
fig.tight_layout();fig.savefig(ROOT/'diagrams/01_method.png',dpi=160);fig.savefig(ROOT/'diagrams/01_method.svg');plt.close(fig)
r=json.loads((ROOT/'data/fixture_results.json').read_text());fig,ax=plt.subplots(figsize=(7.8,5.2))
for row in r['evaluations']:
 x=row['objectives']['h_target_max_deviation'];y=row['objectives']['ion_target_max_deviation']
 xm=(x['lo']+x['hi'])/2;ym=(y['lo']+y['hi'])/2
 ax.errorbar(xm,ym,xerr=(x['hi']-x['lo'])/2,yerr=(y['hi']-y['lo'])/2,fmt='o',alpha=.55,capsize=3,color='#246587')
ax.set_xlabel('Synthetic thickness target deviation [1]');ax.set_ylabel('Synthetic ion target deviation [1]');ax.set_title('13 finite-fixture evaluations: overlap remains inconclusive')
ax.text(.02,.02,'Not coating optimization performance evidence\nIntervals are invented analytic fixtures, not experimental noise',transform=ax.transAxes,fontsize=9,bbox={'facecolor':'white','alpha':.8,'edgecolor':'#bbb'})
ax.grid(alpha=.2);fig.tight_layout();fig.savefig(ROOT/'diagrams/02_fixture_intervals.png',dpi=160);fig.savefig(ROOT/'diagrams/02_fixture_intervals.svg')
