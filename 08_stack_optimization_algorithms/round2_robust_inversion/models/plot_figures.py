"""Original plots from saved tiny diagnostics only; no additional optimizer run."""
from pathlib import Path
import json
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/t08-mpl-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
x=json.loads((ROOT/'verification/diagnostics.json').read_text())
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#f6f8fa','axes.facecolor':'white'})
fig,ax=plt.subplots(1,2,figsize=(12,4.4),layout='constrained')
r=x['correlated_repeat_information_increment'];v=list(r.values())
ax[0].bar(list(r),v,color=['#197c83','#4da6a8','#91c7c6']);ax[0].set(xlabel='Correlation with existing observation',ylabel='Conditional information increment',title='A repeated datum is not always new information',ylim=(0,1.18))
for i,a in enumerate(v):ax[0].text(i,a+.035,f'{a:.6g}',ha='center')
b=x['precise_biased_candidate'];vv=[1,b['reported_variance'],b['actual_mse']]
ax[1].bar(['Baseline MSE','Reported variance\nwith new datum','Actual MSE\nwith bias'],vv,color=['#197c83','#91c7c6','#cf673d']);ax[1].set(ylabel='Squared parameter units',title='Misspecification can reverse the apparent benefit',ylim=(0,4.6))
for i,a in enumerate(vv):ax[1].text(i,a+.10,f'{a:.5g}',ha='center')
fig.suptitle('T08 · Conditional synthetic counterexamples',fontweight='bold')
for ext in ['png','svg']:fig.savefig(ROOT/f'figures/01_information_and_bias.{ext}',dpi=160)
plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(12,4.4),layout='constrained')
a=x['local_rank2_global_alias'];cc=a['discovery']['clusters'];d=[c['representative']['x'][1] for c in cc];n=[c['representative']['x'][0] for c in cc]
ax[0].scatter(d,n,s=120,color='#197c83');ax[0].set(xlabel='Geometric thickness d (µm)',ylabel='Refractive index n',title='Two exact aliases; local rank = 2',ylim=(1.74,1.86),xlim=(.06,.32))
for xx,yy in zip(d,n):ax[0].annotate(f'd = {xx:.6f} µm',(xx,yy),xytext=(0,16),textcoords='offset points',ha='center')
ax[0].text(.19,1.757,'Same wavelength / angle / phase convention\nTwo analytic-informed starts, not search coverage',ha='center',fontsize=10)
b=x['optical_model_mismatch']['heldout_residual_noise_units'];ax[1].bar(['R at 0.9 µm','T at 0.9 µm'],b,color=['#cf673d','#197c83']);ax[1].axhline(0,color='#34495e',lw=.8);ax[1].set(ylabel='Difference / assumed σ = 0.002',title='Perfect training match, large holdout error',ylim=(-37,37))
for i,a in enumerate(b):ax[1].text(i,a+(2 if a>0 else -4),f'{a:.2f} σ',ha='center')
fig.suptitle('T08 · Local identifiability is conditional',fontweight='bold')
for ext in ['png','svg']:fig.savefig(ROOT/f'figures/02_alias_and_mismatch.{ext}',dpi=160)
