"""Independent node refinement of selected synthetic model-discrepancy cases."""
import json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'models'))
from source_reference import *
def grid(angles,H):
    a=np.array(angles);return np.column_stack((H*np.tan(np.deg2rad(a)),np.zeros(len(a)),np.full(len(a),H))),np.tile([0.,0.,-1.],(len(a),1))
def err(a,b):
    positive=b>1e-20
    return {'max_relative_percent_on_positive_nodes':float(np.max(abs(a[positive]/b[positive]-1))*100),'max_absolute_error_over_reference_peak_percent':float(np.max(abs(a-b))/b.max()*100)}
x,n=grid([-60,-50,-40,-12,0,12,40,50,60],.2)
ref=flux_kg_m2_s(disk_source(.1,nr=256,nphi=256,exponent=2.5),x,n,4e-6)
disk=[]
for nr,np_ in [(16,32),(32,64),(64,128),(128,256)]:
    j=flux_kg_m2_s(disk_source(.1,nr=nr,nphi=np_,exponent=2.5),x,n,4e-6)
    disk.append({'nr':nr,'nphi':np_,**err(j,ref)})
xb,nb=grid(np.linspace(-35,35,15),.2)
refb=flux_kg_m2_s(rectangle_source(.16,.025,nx=384,ny=64,exponent=1.5),xb,nb,4e-6)
boat=[]
for nx,ny in [(24,4),(48,8),(96,16),(192,32)]:
    j=flux_kg_m2_s(rectangle_source(.16,.025,nx=nx,ny=ny,exponent=1.5),xb,nb,4e-6)
    boat.append({'nx':nx,'ny':ny,**err(j,refb)})
xr,nr_=grid([0,20,35,45,55,65],.3)
def rim(a,b):
    s=disk_source(.02,nr=a,nphi=b,center=(0,0,-.04));v=circular_aperture(s,xr,0,.025)
    return flux_kg_m2_s(s,xr,nr_,4e-6,v)
refr=rim(320,640);aperture=[]
for a,b in [(20,80),(40,160),(80,320),(160,640)]:aperture.append({'nr':a,'nphi':b,**err(rim(a,b),refr)})
out={'kind':'synthetic discretization only','disk_reference':[256,256],'disk':disk,'boat_reference':[384,64],'boat':boat,'aperture_reference':[320,640],'aperture':aperture,'limitations':'Reference is finer numerical quadrature, not exact truth. Discontinuous aperture convergence need not be monotone; main counterexamples use no aperture.'}
assert disk[2]['max_relative_percent_on_positive_nodes']<.01
assert boat[2]['max_relative_percent_on_positive_nodes']<.01
(ROOT/'benchmarks/results/resolution_study.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
