"""Render only saved tiny diagnostic results. No new optical sweep."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from process_optics import ROOT
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
def save(fig,name):
 fig.savefig(ROOT/'figures'/f'{name}.png',dpi=150,bbox_inches='tight');fig.savefig(ROOT/'figures'/f'{name}.svg',bbox_inches='tight');plt.close(fig)
def main():
 x=json.loads((ROOT/'verification/diagnostics.json').read_text())
 fig,ax=plt.subplots(figsize=(12,5));ax.axis('off')
 boxes=[(.10,.65,'T05 arrival\natoms / m2 / s\nNOT net retained'),(.36,.65,'Explicit net balance\ncomposition + film density\nunknown => BLOCK'),(.66,.65,'Conditional film state\nsource + sample + temperature\nbind n,k explicitly'),(.91,.65,'Stable S-matrix\nR / T / film A')]
 for a,b,t in boxes:ax.text(a,b,t,transform=ax.transAxes,va='center',ha='center',fontsize=10,bbox=dict(boxstyle='round,pad=.6',fc='#e9f1f5',ec='#37718b'))
 for a,b in [(.20,.245),(.49,.535),(.785,.835)]:ax.annotate('',xy=(b,.65),xytext=(a,.65),xycoords='axes fraction',arrowprops=dict(arrowstyle='->',lw=1.5))
 ax.text(.5,.12,'Keep separate: design d | geometry d = mass / film density\nQCM d = sensor mass / display density | optical thickness n(lambda) d',ha='center',transform=ax.transAxes,bbox=dict(fc='#fff2d7',ec='#c99730',pad=8))
 ax.text(.5,.35,'Backside + bulk alpha + bandpass + angle/polarization\n+ explicit scatter / detector collection -> observed R,T',transform=ax.transAxes,ha='center',bbox=dict(fc='#e4f2df',ec='#6d905b',pad=6))
 ax.set_title('T06 Round 2 | conditional calculation is not process calibration',loc='left',fontsize=15,pad=15);save(fig,'01_process_observable_contract')
 fig,axes=plt.subplots(1,2,figsize=(10,4));c=x['n_d_nonuniqueness'];pos=np.arange(2)
 axes[0].bar(pos-.17,c['R_normal'],.34,label='normal incidence');axes[0].bar(pos+.17,c['R_45_s'],.34,label='45 deg, s');axes[0].set_xticks(pos,['n=1.200\nd=114.58 nm','n=1.267\nd=108.55 nm']);axes[0].set_ylabel('Reflectance at 550 nm');axes[0].legend();axes[0].set_title('Equal n d and normal R; angle separates')
 c=x['absorption_omitted_R_only'];axes[1].bar(['true absorbing film','wrong lossless R fit'],[c['true_T'],c['predicted_T_wrong']],color=['#37718b','#c27436']);axes[1].set_ylim(.8,.92);axes[1].set_ylabel('Transmission at 550 nm');axes[1].set_title('R-only residual ~4e-17 hides 3.89 pp T error')
 fig.suptitle('Synthetic counterexamples | not measured material data',fontsize=14);fig.tight_layout();save(fig,'02_nonuniqueness_and_false_fit')
 fig,axes=plt.subplots(1,2,figsize=(10,4));a=x['representative'];w=np.array(a['wavelength_um'])*1000
 for k,lab in [('R_total','R total'),('A_absorption','A absorption'),('T_total','T external')]:axes[0].plot(w,a['observables'][k],'o-',label=lab)
 axes[0].set_xlabel('Wavelength (nm)');axes[0].set_ylabel('Fraction');axes[0].set_ylim(-.03,1.03);axes[0].legend();axes[0].set_title('Public-film Al n,k\nsynthetic 300 nm geometry')
 s=x['scatter_misread_as_absorption'];axes[1].bar(['true A','out-of-specular S','false fitted A'],[s['truth_A'],s['truth_S_out'],s['fitted_A_wrong']],color=['#37718b','#71a088','#c27436']);axes[1].set_ylabel('Fraction at 550 nm');axes[1].set_title('Specular R/T mistakes scatter\nfor absorption, k=0.0400')
 fig.suptitle('All results conditional; no production calibration',fontsize=14);fig.tight_layout();save(fig,'03_energy_and_observability')
if __name__=='__main__':main()
