"""Bounded algebraic examples; not measured data. Default stdout only."""
import argparse,json,time
from pathlib import Path
import numpy as np
from reference import local_observability,axial_probe_design,play_backlash
ROOT=Path(__file__).resolve().parents[1]

def examples():
    start=time.monotonic(); out={}
    def ob(A,B=None,scales=None,C=None):
        A=np.asarray(A,float);n,p=A.shape
        assert n<=128 and p<=16
        B=np.empty((n,0)) if B is None else np.asarray(B,float)
        C=np.eye(n) if C is None else np.asarray(C,float)
        scales=np.ones(p) if scales is None else scales
        return local_observability(A,B,C,scales)
    out['height_source_only']=ob([[-2.]]*4,[[1.]]*4)
    out['height_plus_probe']=ob([[-2.],[1.]],[[1.],[0.]])
    out['clock_constant']=ob(np.column_stack((np.ones(8),np.full(8,2.))))
    out['clock_varying']=ob(np.column_stack((np.ones(8),np.linspace(1,2,8))))
    out['axial_noncollinear']=ob(axial_probe_design([[0,0],[1,0],[0,1]]))
    out['axial_collinear']=ob(axial_probe_design([[-1,0],[0,0],[1,0]]))
    phase=np.arange(8)*2*np.pi/8
    out['harmonic_motion_source']=ob(np.sin(phase)[:,None],np.sin(phase)[:,None])
    out['common_noise_mean']=ob(np.ones((4,1)),C=.2*np.eye(4)+.8*np.ones((4,4)))
    out['independent_noise_mean']=ob(np.ones((4,1)))
    out['backlash']={'input_rad':[0,.2,.4,.3,.2,.1],'half_width_rad':.1,'initial_output_rad':0.,'output_rad':play_backlash([0,.2,.4,.3,.2,.1],.1,0).tolist()}
    expected={'height_source_only':0,'height_plus_probe':1,'clock_constant':1,'clock_varying':2,'axial_noncollinear':3,'axial_collinear':2,'harmonic_motion_source':0,'common_noise_mean':1,'independent_noise_mean':1}
    for k,v in expected.items(): assert out[k]['rank']==v,(k,out[k])
    assert abs(out['common_noise_mean']['noise_conditional_covariance'][0][0]-.85)<1e-12
    assert abs(out['independent_noise_mean']['noise_conditional_covariance'][0][0]-.25)<1e-12
    elapsed=time.monotonic()-start
    if elapsed>60: raise RuntimeError('light-check time budget exceeded')
    return {'kind':'synthetic_algebra_only','interpretation':'proof/interface examples, no device measurements or fitted physical error amplitudes','example_units':{'height_source':'z=1m illustrative nominal; J height per m, normalized log-thickness variance=1','axial_layout':'coordinates 1m deliberately simple algebraic basis, not a sensor layout recommendation','clock':'omega 1..2rad/s or 2rad/s illustrative','covariance':'unit normalized observations, synthetic rho=.8, not calibrated noise'},'results':out,'all_expected_assertions_pass':True}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();s=json.dumps(examples(),ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if a.write:(ROOT/'data/algebraic_results.json').write_text(s)
    print(s)
