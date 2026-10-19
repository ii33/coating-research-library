"""Independent half-wave mechanism checks; does not modify the verified kernel."""
from pathlib import Path
import sys, json, hashlib
import numpy as np
KERNEL=Path(__file__).resolve().parent/'verified_kernel'/'run_experiment.py'
sys.path.insert(0,str(KERNEL.parent))
from run_experiment import tmm_normal, reflection_recursion
OUT=Path(__file__).resolve().parent

def check():
    ds=np.array([.6718207875641499,.9596658089704853,.2686941745557452,.16440325380469994,1.5589439301147199,.41467230316209586])
    nn=np.array([1.45,2.35]*3)
    wl=np.linspace(3,5,4097)
    rb,tb=tmm_normal(wl,ds,nn)
    rows=[]
    for n in (1.45,2.35):
        d=4/(2*n)
        for pos in range(7):
            di=np.insert(ds,pos,d);ni=np.insert(nn,pos,n)
            r,t=tmm_normal(wl,di,ni)
            ri=reflection_recursion(wl,di,ni)
            ra,ta=tmm_normal(wl,di,np.insert(nn.astype(complex),pos,n+.005j))
            rows.append(dict(n=n,d_um=d,position=pos,center_abs_R_change=float(abs(r[2048]-rb[2048])),center_abs_T_change=float(abs(t[2048]-tb[2048])),window_max_abs_R_change=float(np.max(abs(r-rb))),window_max_R=float(r.max()),independent_recursion_max_error=float(np.max(abs(ri-r))),absorption_center_abs_R_change=float(abs(ra[2048]-rb[2048])),absorption_center_T_loss=float(tb[2048]-ta[2048])))
    out=dict(kernel_sha256=hashlib.sha256(KERNEL.read_bytes()).hexdigest(),anchor_um=4,base_thickness_um=ds.tolist(),base_indices=nn.tolist(),base_window_max_R=float(rb.max()),base_center_R=float(rb[2048]),checks=rows,scope='Normal incidence, two synthetic constant-index lossless materials; complex-index perturbation is a deliberate counterexample, not a measured material.')
    assert max(x['center_abs_R_change'] for x in rows)<1e-12
    assert max(x['center_abs_T_change'] for x in rows)<1e-12
    assert max(x['independent_recursion_max_error'] for x in rows)<1e-12
    assert max(x['window_max_abs_R_change'] for x in rows)>.01
    assert max(x['absorption_center_abs_R_change'] for x in rows)>1e-7
    (OUT/'mechanism_checks.json').write_text(json.dumps(out,indent=2))
    return out
if __name__=='__main__':
    a=check(); print(json.dumps({'center_max_abs_R_change':max(x['center_abs_R_change'] for x in a['checks']),'off_center_max_abs_R_change':max(x['window_max_abs_R_change'] for x in a['checks']),'worst_inserted_window_R':max(x['window_max_R'] for x in a['checks']),'all_checks_passed':True},indent=2))
