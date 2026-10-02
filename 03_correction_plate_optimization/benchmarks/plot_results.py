#!/usr/bin/env python3
"""Optional static figures; numerical benchmark itself requires NumPy only."""
import json,csv
from pathlib import Path
import os,tempfile
os.environ.setdefault("MPLCONFIGDIR",str(Path(tempfile.gettempdir())/"coating_t03_mpl"))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent/'results'
s=json.loads((R/'benchmark_summary.json').read_text());d=json.loads((R/'designs.json').read_text());f=json.loads((R/'failure_case.json').read_text())
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':140})
fig,axs=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
labels=['No mask','Constant band','Rounded opacity','Pattern constant','Pattern opacity','Robust equal budget'];names=list(s['validation_metrics']);v=list(s['validation_metrics'].values())
ax=axs[0,0];x=np.arange(len(v));ax.barh(x-.16,[q['cv']*100 for q in v],height=.3,label='CV',color='#246a8b');ax.barh(x+.16,[q['pv_over_mean']*100 for q in v],height=.3,label='PV / mean',color='#a9c8d3');ax.set_yticks(x,labels);ax.invert_yaxis();ax.set_xlabel('Nonuniformity (%)');ax.set_title('Held-out solid-mask comparison');ax.legend()
ax=axs[0,1];poly=np.array(d['polygons_m'][s['selected']])*1000;ax.fill(poly[:,0],poly[:,1],color='#246a8b',alpha=.65);ax.plot(poly[:,0],poly[:,1],color='#246a8b');ax.set_aspect('equal',adjustable='datalim');ax.set_xlabel('Mask x (mm)');ax.set_ylabel('Mask y (mm)');ax.set_title('Synthetic selected polygon - not for fabrication');ax.grid(alpha=.2)
ax=axs[1,0];rows=list(csv.DictReader((R/'time_convergence.csv').open()));ax.plot([int(r['panels']) for r in rows],[float(r['max_abs_delta_over_mean'])*100 if r['max_abs_delta_over_mean'] else np.nan for r in rows],'o-',color='#246a8b');ax.set_xscale('log',base=2);ax.set_yscale('log');ax.set_xlabel('Midpoint time panels');ax.set_ylabel('Successive max thickness difference / mean (%)');ax.set_title('Time refinement - empirical difference, not a bound');ax.grid(alpha=.2)
ax=axs[1,1];a=f['unmasked'];b=f['binary_mask'];x=np.arange(3);ax.bar(x-.18,np.array([a['radial_cv'],a['angular_cv'],a['cv']])*100,.36,label='No mask',color='#a9c8d3');ax.bar(x+.18,np.array([b['radial_cv'],b['angular_cv'],b['cv']])*100,.36,label='Designed mask',color='#bb6b46');ax.set_xticks(x,['Radial CV','Angular CV','Full CV']);ax.set_ylabel('Nonuniformity (%)');ax.set_title('17.3 s counterexample: radial gain, full-field loss');ax.legend();ax.grid(axis='y',alpha=.2)
fig.suptitle('T03 synthetic mask-design evidence | ballistic model, no measured machine data',fontsize=14)
fig.savefig(R/'numerical_evidence.png');fig.savefig(R/'numerical_evidence.svg');print(R/'numerical_evidence.png')
