#!/usr/bin/env python3
"""Optional scientific figures from saved benchmark CSVs; matplotlib only."""
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parent; DATA=ROOT/'results'
def read(name): return list(csv.DictReader((DATA/name).open()))
summary=json.loads((DATA/'benchmark_summary.json').read_text())
fig,axes=plt.subplots(2,2,figsize=(11,7.5),layout='constrained')
for ax,name,title in ((axes[0,0],'time_accuracy.csv','Smooth time integral'),(axes[0,1],'mask_time_accuracy.csv','Moving shadow without event splitting')):
    rows=read(name)
    for order,label in ((1,'Midpoint'),(4,'4-point Gauss')):
        r=[a for a in rows if int(a['order'])==order]
        ax.loglog([float(a['median_seconds']) for a in r],[float(a['max_abs_error_over_reference_mean']) for a in r],'o-',label=label)
    ax.set(xlabel='Median elapsed time (s)',ylabel='Max abs. error / reference mean',title=title)
    ax.grid(True,alpha=.2);ax.legend()
axes[0,1].axhline(summary['mask_reference_refinement_error'],color='gray',ls='--',lw=1,label='Reference refinement difference')
axes[0,1].legend(fontsize=8)
r=read('extended_source_shadow_accuracy.csv');ax=axes[1,0]
ax.loglog([int(a['total_source_nodes']) for a in r],[float(a['max_abs_error_over_reference_mean']) for a in r],'o-',color='#236b51')
ax.axhline(summary['extended_source_reference_refinement_error'],color='gray',ls='--',label='Reference refinement difference')
ax.set(xlabel='Extended-source quadrature nodes',ylabel='Max abs. error / reference mean',title='Finite source cut by a mask edge');ax.grid(True,alpha=.2);ax.legend()
r=read('quadrature_aliasing.csv');ax=axes[1,1]
x=np.arange(len(r)); vals=[float(a['estimated_integral']) for a in r]
ax.bar(x,vals,color=['#af532b' if abs(v-1)>.01 else '#416b94' for v in vals]);ax.axhline(1,color='black',ls='--',label='Exact integral = 1')
ax.set(xticks=x,xticklabels=[a['panels'] for a in r],xlabel='Midpoint panels',ylabel='Estimated integral',ylim=(0,1.45),title='16 and 32 panels agree but are both wrong');ax.legend(loc='lower right')
fig.suptitle('T02 synthetic numerical evidence | no machine calibration',fontsize=14)
for ext in ('png','svg'):fig.savefig(DATA/f'numerical_evidence.{ext}',dpi=160)
