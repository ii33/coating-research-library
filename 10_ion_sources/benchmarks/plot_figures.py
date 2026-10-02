from pathlib import Path
import json, numpy as np
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/t10_matplotlib')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/t10_cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
P=Path(__file__).resolve().parents[1]
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':150})
# Original conceptual diagram. No circuit, dimensions, or operational setpoints.
fig,ax=plt.subplots(figsize=(12,5));ax.set_xlim(0,12);ax.set_ylim(0,5);ax.axis('off')
ax.add_patch(Rectangle((.5,1),3.6,3,fc='#dcecf6',ec='#174c67',lw=2))
ax.text(2.2,3.5,'DC discharge chamber',ha='center',weight='bold');ax.text(2.2,2.8,'electron-emitting cathode\n+ gas + magnetic confinement',ha='center')
for x,label,col in [(4.2,'screen','#438aac'),(4.9,'accelerator','#d28b2b'),(5.6,'optional 3rd grid','#7f6bac')]:
 for y in [1,1.8,2.6,3.4]:ax.add_patch(Rectangle((x,y),.12,.42,color=col))
 ax.text(x,4.3,label,ha='center',rotation=25)
for y in [1.65,2.45,3.25]:ax.add_patch(FancyArrowPatch((3.3,y),(10.4,y),arrowstyle='->',mutation_scale=12,color='#dd7632'))
ax.add_patch(Rectangle((10.6,.9),.35,3.2,fc='#7e979a'));ax.text(11,4.3,'substrate\nactual V_s',ha='center')
ax.text(7.5,3.7,'ion beam + electrons\nquasi-neutral, not all neutral atoms',ha='center')
ax.add_patch(Rectangle((6.4,.3),1.8,.45,fc='#bed6b0'));ax.text(7.3,.53,'neutralizer',ha='center',va='center');ax.add_patch(FancyArrowPatch((7.2,.85),(7.7,1.45),arrowstyle='->',mutation_scale=12,color='#418037'))
ax.text(.5,.1,'Concept only: potentials, grids and cathodes are model-specific; no wiring or apparatus instructions',fontsize=9)
fig.suptitle('Kaufman-type source: distinct functional blocks (original schematic)',weight='bold');fig.tight_layout();fig.savefig(P/'figures/source_functional_blocks.svg');fig.savefig(P/'figures/source_functional_blocks.png');plt.close(fig)
# Maps
z=np.load(P/'data/synthetic_maps.npz');fig,axs=plt.subplots(2,2,figsize=(10,8))
for ax,key,title in zip(axs.flat,['j_A_m2','rate_nm_s','ratio','epsilon_eV'],['Positive-ion current on substrate [A/m2]','Net thickness rate [nm/s]','Charged ions / net deposited atom','Incident eV / net deposited atom']):
 a=np.ma.array(z[key],mask=~z['inside']);im=ax.pcolormesh(z['X']*100,z['Y']*100,a,shading='auto',cmap='viridis',rasterized=True);fig.colorbar(im,ax=ax);ax.set_aspect('equal');ax.set(xlabel='x [cm]',ylabel='y [cm]',title=title)
fig.suptitle('Synthetic fields: thickness uniformity does not imply assist uniformity',weight='bold');fig.tight_layout();fig.savefig(P/'figures/synthetic_spatial_fields.svg');fig.savefig(P/'figures/synthetic_spatial_fields.png');plt.close(fig)
# Diagnostic analytic trends
R=json.loads((P/'data/demo_results.json').read_text());fig,axs=plt.subplots(2,2,figsize=(10,7))
tau=np.linspace(0,2,101);axs[0,0].plot(tau,np.exp(-tau),label='energetic ions');axs[0,0].plot(tau,1-np.exp(-tau),label='fast neutrals');axs[0,0].plot(tau,np.ones_like(tau),'--',label='total energetic particles');axs[0,0].set(xlabel='Charge-exchange optical depth (synthetic)',ylabel='Fraction',title='Electric current can miss energetic neutrals');axs[0,0].legend(fontsize=8)
y=np.linspace(0,4.9,100);axs[0,1].plot(y,.2/(1-.2*y));axs[0,1].axhline(.2,color='gray',linestyle='--');axs[0,1].set(xlabel='Assumed constant sputter yield [atom/particle]',ylabel='Ion / net-atom ratio',ylim=(0,3),title='Net-growth denominator becomes unstable')
conv=R['motion_convergence'][:-1];axs[1,0].loglog([r['n'] for r in conv],[r['relative_error_to_12800'] for r in conv],'o-');axs[1,0].set(xlabel='Time bins',ylabel='Relative difference to 12800-bin reference',title='Finite-time motion quadrature convergence')
t=np.linspace(0,600,200);axs[1,1].plot(t,20*(1-np.exp(-.15*t/24)),label='G=0.15 W/K');axs[1,1].plot(t,3*t/24,'--',label='adiabatic');axs[1,1].set(xlabel='Time [s]',ylabel='Temperature rise [K]',title='Independent absorbed heat input: 3 W');axs[1,1].legend(fontsize=8)
fig.suptitle('Synthetic diagnostics only: no material fit or equipment qualification',weight='bold');fig.tight_layout();fig.savefig(P/'figures/synthetic_diagnostics.svg');fig.savefig(P/'figures/synthetic_diagnostics.png');plt.close(fig)
print('3 SVG and 3 PNG generated')
