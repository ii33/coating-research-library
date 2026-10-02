#!/usr/bin/env python3
"""Rebuild all derived T06 spectra, finite-band metrics and original SVG charts.
Offline: Python >=3.10, NumPy >=2.0. No third-party originals needed.
"""
from pathlib import Path
import csv,json,html
import numpy as np
from reference_tmm import evaluate_material,plate,band_metrics,coherent
ROOT=Path(__file__).resolve().parents[1]

def load():
 return json.loads((ROOT/'data/starter_stacks.json').read_text())['examples'],json.loads((ROOT/'data/material_proxies.json').read_text())['materials']

def compute(ex,materials,multiplier=1,rear=None,alpha=None,points=None):
 lo,hi,num=ex['wavelength_grid_um']; w=np.linspace(lo,hi,points or num)
 ns=evaluate_material(materials[ex['substrate']],w)
 nl=[evaluate_material(materials[d['material']],w) for d in ex['layers']]
 ds=[d['thickness_um']*multiplier for d in ex['layers']]
 spectra={}
 for angle in ex['angles_deg']:
  for pol in ex['polarizations']:
   r=plate(w,1,ns,nl,ds,ex['substrate_mm'],ex['bulk_alpha_cm_inv'] if alpha is None else alpha,angle,pol,ex['rear'] if rear is None else rear)
   spectra[f'{angle:g}_{pol}']=r
 return w,spectra

def svg_plot(path,panels,title):
 W,H=1180,180+280*((len(panels)+1)//2)
 s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">', '<rect width="100%" height="100%" fill="#f7f9fc"/>',f'<text x="36" y="38" font-family="sans-serif" font-size="24" fill="#17324b">{html.escape(title)}</text>','<text x="36" y="67" font-family="sans-serif" font-size="14" fill="#4b6074">Synthetic reference calculations. Not measured spectra or production qualifications. All values are fractions.</text>']
 for idx,(caption,w,curves) in enumerate(panels):
  x=70+(idx%2)*570;y=132+(idx//2)*280;pw=480;ph=170
  s.append(f'<text x="{x}" y="{y-25}" font-family="sans-serif" font-size="17">{html.escape(caption)}</text>')
  for tick in [0,.25,.5,.75,1]:
   yy=y+ph*(1-tick);s.append(f'<path d="M{x},{yy}h{pw}" stroke="#dbe3eb"/><text x="{x-34}" y="{yy+4}" font-family="sans-serif" font-size="11">{tick:g}</text>')
  for tick in np.linspace(w[0],w[-1],5):
   xx=x+pw*(tick-w[0])/(w[-1]-w[0]);s.append(f'<text x="{xx-16}" y="{y+ph+20}" font-family="sans-serif" font-size="11">{tick:.3g}</text>')
  s.append(f'<text x="{x+185}" y="{y+ph+39}" font-family="sans-serif" font-size="12">Wavelength (um)</text>')
  for k,(name,data,color) in enumerate(curves):
   ids=np.linspace(0,len(w)-1,min(600,len(w))).astype(int)
   if np.ptp(data)>1e-6:
    turns=np.where(np.diff(np.sign(np.diff(data)))!=0)[0]+1
    ids=np.r_[ids,turns]
   ids=np.unique(ids)
   pts=' '.join(f'{x+pw*(w[j]-w[0])/(w[-1]-w[0]):.2f},{y+ph*(1-data[j]):.2f}' for j in ids)
   s.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.6"/>')
   s.append(f'<text x="{x+k*155}" y="{y-7}" fill="{color}" font-family="sans-serif" font-size="11">{html.escape(name)}</text>')
 s.append('</svg>');path.write_text('\n'.join(s))

def main():
 examples,materials=load();summary=[];panels=[];anglepanels=[];sensitivity=[]
 for ex in examples:
  w,spectra=compute(ex,materials)
  columns=['wavelength_um']+[f'{a}_{k}' for a,r in spectra.items() for k in r]
  with (ROOT/'data/spectra'/f'{ex["id"]}_spectrum.csv').open('w') as f:
   writer=csv.writer(f);writer.writerow(columns)
   for j,wl in enumerate(w):writer.writerow([f'{wl:.10g}']+[f'{r[k][j]:.12g}' for r in spectra.values() for k in r])
  records=[]
  for key,sp in spectra.items():
   for name,band in ex['bands_um'].items():
    m=band_metrics(w,sp,band);m.update(angle_polarization=key,band_name=name)
    m['worst_case_OD_from_max_T']=-float(np.log10(max(m['T_max'],1e-300)))
    front={'R':sp['front_R'],'T':sp['front_T'],'A':sp['front_A']}
    m['front_surface_metrics']=band_metrics(w,front,band)
    records.append(m)
  zero=spectra['0_s'];summary.append(dict(id=ex['id'],layer_count=len(ex['layers']),physical_total_um=sum(d['thickness_um'] for d in ex['layers']),metrics=records,max_energy_residual=float(max(np.max(np.abs(r['R']+r['T']+r['A']-1)) for r in spectra.values()))))
  panels.append((ex['id']+' '+ex['title'],w,[('R total @0',zero['R'],'#bd4b3a'),('T total @0',zero['T'],'#167d9a'),('A total @0',zero['A'],'#8c5aad')]))
  key=max(ex['angles_deg']);s,p=spectra[f'{key:g}_s'],spectra[f'{key:g}_p']
  field='R' if ex['id'] in ('E04','E06') else 'T'
  anglepanels.append((f'{ex["id"]}: {field}, {key:g} deg s/p vs 0 deg',w,[(f'{field} 0deg',zero[field],'#6a7682'),(f'{field} {key:g}deg s',s[field],'#1967a0'),(f'{field} {key:g}deg p',p[field],'#cf5d27')]))
  band=next(iter(ex['bands_um'].values()))
  for factor in [.98,1,1.02]:
   w2,sp=compute(ex,materials,multiplier=factor)
   sensitivity.append(dict(id=ex['id'],perturbation='all layer physical thickness scaled, correlated deterministic scenario',factor=factor,metrics=band_metrics(w2,sp['0_s'],band)))
  # Show that a single front-surface AR cannot erase the untreated rear face.
  if ex['id'] in ('E01','E02','E03'):
   for rear in ['bare','same']:
    w2,sp=compute(ex,materials,rear=rear,alpha=.02)
    sensitivity.append(dict(id=ex['id'],perturbation='bulk alpha=0.02cm^-1 hypothetical; not measured',rear=rear,metrics=band_metrics(w2,sp['0_s'],band)))
 (ROOT/'data/finite_band_metrics.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
 (ROOT/'data/sensitivity_scenarios.json').write_text(json.dumps(sensitivity,ensure_ascii=False,indent=2)+'\n')
 svg_plot(ROOT/'figures/01_spectral_atlas.svg',panels,'T06: Six tunable starter stacks')
 svg_plot(ROOT/'figures/02_angle_polarization.svg',anglepanels,'T06: Incidence angle and polarization matter')
 lines=['# 自动复算结果表','', '全部为合成/条件化参考计算，不是实测。双面总外响应；均匀波长加权；极值是网格取样值。完整角度、偏振、单面和OD见JSON。','', '| 例 | 波段 µm | 总T均值 | 总T最小 | 总R最大 | 总A均值 |','|---|---|---:|---:|---:|---:|']
 for ex in summary:
  for m in ex['metrics']:
   if m['angle_polarization']=='0_s':lines.append(f'| {ex["id"]} {m["band_name"]} | {m["wavelength_band_um"]} | {m["T_mean"]:.6f} | {m["T_min"]:.6f} | {m["R_max"]:.6f} | {m["A_mean"]:.6f} |')
 (ROOT/'reports/06a_generated_metrics.md').write_text('\n'.join(lines)+'\n')
 print('\n'.join(lines))

if __name__=='__main__':main()
