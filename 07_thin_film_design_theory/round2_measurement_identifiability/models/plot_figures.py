"""Plot saved tiny results only. No new optical scans, fitting, or network."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/t07-r2-mpl')
from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
x=json.loads((ROOT/'verification/diagnostics.json').read_text())
keys=['single_R','single_RT','RT_plus_independent_d','angle_resolved_RT','single_ellipsometric_ratio','ellipsometry_plus_independent_d','RT_plus_ellipsometry','three_wavelength_R']
labels=['R','R + T','R/T + geometric d','3 angles, s/p R/T','single complex rho','rho + geometric d','R/T + rho','3 wavelengths R']
fig,ax=plt.subplots(figsize=(10,6),layout='constrained');colors=['#0b7285','#2f9e44','#f08c00']
for j in range(3):
    vals=[x['cases'][k]['singular_values'][j] for k in keys]
    ax.scatter([v if v>0 else .08 for v in vals],np.arange(len(keys))+.15*(j-1),color=colors[j],label=f's{j+1}',s=60)
ax.set_xscale('log');ax.set_yticks(range(len(keys)),labels);ax.invert_yaxis();ax.set_xlabel('Whitened scaled singular value (zero placed at 0.08)')
ax.axvline(1,color='gray',ls='--',lw=1);ax.grid(axis='x',alpha=.25);ax.legend(loc="center left",bbox_to_anchor=(1,.5));ax.set_title('Conditional synthetic information directions\nDifferent rows/noise/costs: not a hardware ranking')
fig.savefig(ROOT/'figures/01_conditional_singular_values.png',dpi=160);fig.savefig(ROOT/'figures/01_conditional_singular_values.svg');plt.close(fig)
a=x['global_alias'];fig,axs=plt.subplots(1,2,figsize=(10,4),layout='constrained')
axs[0].scatter([100,1000*a['other_theta_n_d_um'][1]],[1.8,1.8],s=110,color=['#0b7285','#e8590c']);axs[0].set_ylim(1.75,1.85);axs[0].set_xlabel('Geometric thickness (nm)');axs[0].set_ylabel('Synthetic refractive index');axs[0].set_title('Different parameters, same observations\n550 nm / 50 deg, transparent layer')
axs[1].bar(['same-condition\nmax abs difference','held-out 65 deg\nRs difference'],[a['same_condition_max_abs_difference'],a['heldout_65deg_Rs_difference']],color=['#0b7285','#e8590c']);axs[1].set_yscale('log');axs[1].set_ylabel('Absolute observation difference');axs[1].set_title('Local full rank does not remove aliases');axs[1].grid(axis='y',alpha=.25)
fig.savefig(ROOT/'figures/02_local_rank_global_alias.png',dpi=160);fig.savefig(ROOT/'figures/02_local_rank_global_alias.svg');plt.close(fig)
