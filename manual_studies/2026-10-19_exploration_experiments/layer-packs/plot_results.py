#!/usr/bin/env python3
"""Optional figures. Numerical experiment does not require matplotlib."""
from pathlib import Path
import json, os, tempfile
os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'coating-layer-packs-mpl'))
os.environ.setdefault('XDG_CACHE_HOME',str(Path(tempfile.gettempdir())/'coating-layer-packs-cache'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import run_layer_packs as e
ROOT=Path(__file__).resolve().parent

def main():
    e.load_kernel(ROOT/'verified_kernel');m=json.loads((ROOT/'mechanism_checks.json').read_text());r=json.loads((ROOT/'results/results.json').read_text());s=json.loads((ROOT/'results/summary.json').read_text());out=ROOT/'figures';out.mkdir(exist_ok=True)
    ds=np.array(m['base_thickness_um']);nn=np.array(m['base_indices']);worst=max(m['checks'],key=lambda x:x['window_max_R']);wl=np.linspace(3,5,4097);rb=e.KERNEL.tmm_normal(wl,ds,nn)[0];di=np.insert(ds,worst['position'],worst['d_um']);ni=np.insert(nn,worst['position'],worst['n']);ri=e.KERNEL.tmm_normal(wl,di,ni)[0]
    fig,ax=plt.subplots(figsize=(8,4.6));ax.plot(wl,rb*100,label='Original 6-layer design');ax.plot(wl,ri*100,label=f"Insert one half-wave layer: n={worst['n']}, position={worst['position']}");ax.axhline(1,color='gray',ls='--',label='Original R <= 1% target');ax.axvline(4,color='black',alpha=.3,ls=':');ax.scatter([4],[rb[2048]*100],color='black',zorder=5);ax.set(xlabel='Wavelength (um)',ylabel='Reflectance (%)',title='Exact neutrality at 4 um does not protect the 3-5 um window',xlim=(3,5));ax.legend(loc='upper center',fontsize=8);ax.grid(alpha=.2);fig.tight_layout();fig.savefig(out/'center_protection_failure.png',dpi=180);plt.close(fig)
    rows=[x for x in s if x['case']=='protected_short_window'];fig,ax=plt.subplots(figsize=(8.5,4.7));x=np.arange(len(rows));med=np.array([y['global_R_median']*100 for y in rows]);lo=med-np.array([y['global_R_min']*100 for y in rows]);hi=np.array([y['global_R_max']*100 for y in rows])-med;ax.bar(x-.18,med,.35,label='Global best: original short window damaged',color='#da8c61');ax.errorbar(x-.18,med,yerr=[lo,hi],fmt='none',ecolor='black',capsize=3);ax.bar(x+.18,[y['protected_R_median']*100 for y in rows],.35,label='Protected archive: original 6-layer stack retained',color='#56748b');ax.axhline(1,color='black',ls='--',label='Two-window target: 1%');ax.set_xticks(x,[y['method'].replace('_','\n') for y in rows],fontsize=8);ax.set(ylabel='Worst reflectance over both windows (%)',title='Four paired seeds; no successful protective insertion for any method',ylim=(0,65));ax.legend(fontsize=7.5,loc='upper center',ncol=1);ax.grid(axis='y',alpha=.2);fig.tight_layout();fig.savefig(out/'paired_seed_results.png',dpi=180);plt.close(fig)
if __name__=='__main__':main()
