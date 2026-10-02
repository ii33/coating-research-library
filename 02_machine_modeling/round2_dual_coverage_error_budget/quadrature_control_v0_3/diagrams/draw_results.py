from pathlib import Path
import json,sys
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]
s=json.loads((R/'data/small_checks.json').read_text());l=json.loads((R/'data/localization.json').read_text())
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(1,3,figsize=(15,4.9),layout='constrained')
d=s['A_support']['2']['duration'];v=[l['s2t2'][2][3],l['holdout'][2][3],d['midpoint_s']]
ax[0].bar(['S2 grid','Holdout grid','Continuous\nsupport'],np.array(v)*1000,color=['#4169a1','#dc9140','#228372'])
ax[0].set_ylim(1300,1420);ax[0].set_ylabel('Ion-only duration (ms)');ax[0].set_title('A. Point 2: grid agreement is not a bound')
for i,x in enumerate(v):ax[0].text(i,x*1000+2,f'{x*1000:.3f}',ha='center')
ax[0].text(.02,.04,'Support interval width: 0.02146 ms\nConditional float guard; not certified',transform=ax[0].transAxes,fontsize=9)
bs=s['B']['rows'];labels=['127 mid','254 mid','509 mid','127 shifted','254 shifted','Adaptive']
ax[1].bar(labels,[r['absolute_error'] for r in bs],color=['#a64440','#a64440','#228372','#dc9140','#dc9140','#228372'])
ax[1].tick_params(axis='x',rotation=35);ax[1].set_ylim(0,.92);ax[1].set_title('B. Known analytic rate alias');ax[1].set_ylabel('Absolute integral error (truth = 1)')
ax[1].text(.03,.91,'127 and 254 give the same wrong 1.8',transform=ax[1].transAxes,fontsize=9)
ax[2].axis('off');ax[2].set_title('C. Sidewall propagation / device boundary')
ax[2].text(.02,.85,'One incorrectly visible weight = 1e-12\nFlux integral leak = 1.59155e-12 atoms/m²\nIon-only duration error = 200 ms',va='top',linespacing=1.7)
ax[2].text(.02,.49,'High-cost validation: NOT RUN\n2-point planned fixed-grid work: 2.451e9 rays\n13 / 236 point sets are device options\nOriginal global status: PARTIAL',va='top',linespacing=1.7,color='#8b403c')
fig.suptitle('T02 v0.3 | Shadow-aware quadrature evidence and explicit limits',fontsize=15)
for ext in ['png','svg']:fig.savefig(R/'diagrams'/('01_error_and_work.'+ext),dpi=170)
plt.close(fig)
