"""Recheck reported explicit bulk-k sensitivity points; no product imports."""
import sys,json,math
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'scripts'))
import optics as p
def response(w,route,scale):
 w=np.asarray(w,float);air=np.ones(len(w),complex);source=p.nk('ZnS',w);ns=source.real+1j*scale*source.imag;f=p.block(w,p.PRES[route][::-1],air,ns,0,'s');rev=p.block(w,p.PRES[route],ns,air,0,'s');back=p.block(w,p.PRES[route],ns,air,0,'s');P=np.exp(-4*np.pi*ns.imag*1e6/w);den=1-rev['R']*back['R']*P*P;r=f['R']+f['T']*rev['T']*back['R']*P*P/den;t=f['T']*back['T']*P/den;return np.column_stack([r,t,1-r-t])
maximum=0.
for row in json.loads((ROOT/'sensitivity.json').read_text(encoding='utf-8'))['scenarios']:
 for w in row['windows']:
  for key,col in [('Rmax',0),('Tmin',1),('Amax',2)]:
   value=float(response(np.array([w[key+'_nm']]),row['route_both_sides'],row['bulk_k_scale'])[0,col]);maximum=max(maximum,abs(value-w[key]))
assert maximum<2e-10
print(json.dumps({'all_sensitivity_points_reproduced':True,'max_RTA_difference':maximum,'measurement_claimed':False}))
