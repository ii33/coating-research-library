"""Original explanatory figure; author-only matplotlib dependency."""
from pathlib import Path
import csv,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((root/'electro_optics/results/synthetic_spectra.csv').open()))
cases=json.loads((root/'electro_optics/results/synthetic_summary.json').read_text())['cases']
colors=['#286a8b','#cc713a','#5a8b58']
fig,ax=plt.subplots(1,2,figsize=(12,4.9),sharex=True,layout='constrained')
for c,col in zip(cases,colors):
 r=[a for a in rows if a['case']==c['name']]
 label=c['name'].replace('synthetic_','').replace('_',' ')+' | Rs = %.1f ohm/sq'%c['R_sheet_ohm_square']
 for a,metric in zip(ax,['T','A']):
  a.plot([float(x['wavelength_nm']) for x in r],[100*float(x[metric]) for x in r],lw=2.2,color=col,label=label)
for a,title in zip(ax,['Transmittance (%)','Absorptance (%)']):
 a.set(xlabel='Vacuum wavelength (nm)',ylabel=title,xlim=(400,2500),ylim=(0,100))
 a.grid(alpha=.2);a.axvspan(400,700,color='#e6ecdc',alpha=.5)
 a.spines[['top','right']].set_visible(False)
ax[0].legend(loc='lower left',fontsize=8,frameon=False)
fig.suptitle('Synthetic ITO examples: visible transparency does not determine infrared loss',fontsize=14)
fig.supxlabel('ASSUMED PARAMETERS ONLY | Not measured, not calibrated to an evaporation process',fontsize=10,color='#8a3e21')
fig.savefig(root/'integration/synthetic_tradeoff.png',dpi=160)
