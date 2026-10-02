#!/usr/bin/env python3
"""T04 bounded optical calculations. Not a production coating solver.
Only standard-library; wavelength is um, k>=0 convention N=n+ik.
Full originals stay local. Published derived point records suffice for examples.
"""
from pathlib import Path
import bisect, csv, json, math, re
ROOT=Path(__file__).resolve().parents[1]

def read_nk(path):
    rows=[]
    for line in Path(path).read_text().splitlines():
        parts=line.split()
        if len(parts)!=3: continue
        try: row=tuple(map(float,parts))
        except ValueError: continue
        rows.append(row)
    validate_nk(rows)
    return rows

def validate_nk(rows):
    if len(rows)<2: raise ValueError('At least two wavelength rows required')
    if any(not all(math.isfinite(x) for x in r) for r in rows): raise ValueError('Nonfinite data')
    if any(w<=0 or n<=0 or k<0 for w,n,k in rows): raise ValueError('Positive wavelength/n and passive k required')
    if any(a[0]>=b[0] for a,b in zip(rows,rows[1:])): raise ValueError('Wavelengths must strictly increase')

def interp_nk(rows,w):
    validate_nk(rows)
    if not math.isfinite(w) or not rows[0][0]<=w<=rows[-1][0]: raise ValueError('Extrapolation forbidden')
    j=bisect.bisect_left([r[0] for r in rows],w)
    if rows[j][0]==w: return rows[j][1:]
    a,b=rows[j-1],rows[j]; t=(w-a[0])/(b[0]-a[0])
    return tuple(a[i]+t*(b[i]-a[i]) for i in (1,2))

def surface_R(n,k=0.,n0=1.):
    if n<=0 or k<0 or n0<=0: raise ValueError('Invalid optical input')
    return ((n-n0)**2+k*k)/((n+n0)**2+k*k)

def intensity_depth_nm(w_um,k):
    if w_um<=0 or k<0: raise ValueError('Invalid optical input')
    return math.inf if k==0 else 1000*w_um/(4*math.pi*k)

def incoherent_slab(n,alpha_cm_inv,thickness_mm):
    """Air / homogeneous slab / air, normal incidence, small interface k ignored."""
    if n<=0 or alpha_cm_inv<0 or thickness_mm<0: raise ValueError('Invalid slab')
    r=surface_R(n); a=math.exp(-alpha_cm_inv*thickness_mm/10)
    den=1-r*r*a*a
    t=(1-r)**2*a/den
    rt=r+(1-r)**2*r*a*a/den
    return dict(single_surface_R=r,internal_T=a,total_T=t,total_R=rt,total_A=1-t-rt)

def lorentz_lorenz_void(n_dense,void_fraction):
    """Illustrative isotropic nonabsorbing polarizability mixture, not measurement."""
    if n_dense<1 or not 0<=void_fraction<1: raise ValueError('Invalid mixture')
    f=(1-void_fraction)*(n_dense*n_dense-1)/(n_dense*n_dense+2)
    return math.sqrt((1+2*f)/(1-f))

def examples():
    records=json.loads((ROOT/'data/metal_nk_derived_points.json').read_text())
    result=[]
    for r in records:
        q=dict(r)
        q.update(R_semi_infinite_air=surface_R(r['n'],r['k']),intensity_1e_depth_nm=intensity_depth_nm(r['wavelength_um'],r['k']))
        result.append(q)
    examples=dict(metal_point_calculations=result,
      ge_slab_11um_zero_absorption=incoherent_slab(4.0026,0,5),
      ge_slab_10p6um_illustrative_alpha_limit=incoherent_slab(4.0026,.027,5),
      ge_quarterwave_10um_bulk_n4_um=10/(4*4),
      ge_quarterwave_10um_historical_film_n4p3_um=10/(4*4.3),
      hypothetical_dielectric_dense_n2p1_void_10pct=lorentz_lorenz_void(2.1,.10),
      hypothetical_density_10pct_low_thickness_error=1/.9-1,
      notes=['Slab alpha=.027 uses a typical upper-bound at10.6um and n at11um: illustrative mixed-nearby-wavelength sensitivity, not measured spectrum.','Metal R is homogeneous semi-infinite flat surface, not ultrathin film, protected mirror, or damage threshold.','Dataset spread is model/sample sensitivity, not statistical confidence interval.'])
    return examples

if __name__=='__main__':
    out=examples(); (ROOT/'data/worked_examples.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    for r in out['metal_point_calculations']:
        print(f"{r['dataset_id']:12} {r['wavelength_um']:.4f} n={r['n']:.6g} k={r['k']:.6g} R={100*r['R_semi_infinite_air']:.4f}% deltaI={r['intensity_1e_depth_nm']:.4f}nm")
    print(json.dumps({k:v for k,v in out.items() if k!='metal_point_calculations'},ensure_ascii=False,indent=2))
