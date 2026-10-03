"""Bounded independent review; imports production subject, never its tests as oracle.

By default results are printed, never written. An explicit --output path opts in
to saving a new result. Dataset edge cases use in-memory pathlib mocks, so no
author inputs or temporary datasets are changed.
"""
import argparse
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import time
from unittest.mock import patch
import warnings

import numpy as np

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'models'))
import reference as subject

INPUTS = [
    'reports/01_scope_and_error_taxonomy.md',
    'reports/02_pose_and_contact_model.md',
    'reports/03_observation_and_identifiability.md',
    'models/reference.py', 'models/offline_read.py',
    'verification/test_reference.py', 'verification/PRE_REGISTERED_PROTOCOL.md',
    'data/measurement_template.json', 'data/formal_calibration_plan.json',
    'data/synthetic_observations.json', 'data/synthetic_encoder.csv',
]


def digest_inputs():
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in INPUTS}


def quat_product(a, b):
    return np.r_[a[0]*b[0] - a[1:]@b[1:],
                 a[0]*b[1:] + b[0]*a[1:] + np.cross(a[1:], b[1:])]


def quat_rotate(rotation_vector, point):
    v = np.asarray(rotation_vector, dtype=float)
    t = np.linalg.norm(v)
    q = np.r_[math.cos(t/2), v*(math.sin(t/2)/t if t else .5)]
    return quat_product(quat_product(q, np.r_[0., point]), q*[1,-1,-1,-1])[1:]


def assert_close(a, b, atol=1e-11):
    np.testing.assert_allclose(a, b, rtol=0, atol=atol)


def pose_checks():
    ac = np.array([.14,-.08,0.]); ap = np.array([-.05,.12,0.])
    tc, phi, spin = .42, -.7, .025
    mount_vector = np.array([.12,.07,-.19])
    mount = np.column_stack([quat_rotate(mount_vector, e) for e in np.eye(3)])
    b = np.array([.32,-.04,.78]); dp = np.array([.002,-.001,.003])
    d = np.array([.004,.005,-.002])
    def carrier(v):
        return quat_rotate(ac, quat_rotate([0,0,tc], v))
    def orientation(v):
        return carrier(quat_rotate(ap, quat_rotate([0,0,phi+spin], quat_rotate(mount_vector,v))))
    c, Q = subject.pose(tc, phi, b, d, ac[:2], dp, ap[:2], spin, mount)
    assert_close(c, d+carrier(b+dp))
    assert_close(Q, np.column_stack([orientation(e) for e in np.eye(3)]))
    u = np.array([.11,-.09,.025]); eccentricity = np.array([.003,.002,-.001])
    x,n = subject.point_normal(c,Q,u,[0,0,-1],eccentricity)
    assert_close(x,c+orientation(u+eccentricity)); assert_close(n,orientation([0,0,-1]))
    Jx,Jn = subject.rigid_jacobians(c,x,n)
    h=2e-6; xp=[]; nparts=[]
    for k in range(6):
        dv=np.eye(6)[k]*h
        xp.append(((c+dv[:3]+quat_rotate(dv[3:],x-c))-(c-dv[:3]+quat_rotate(-dv[3:],x-c)))/(2*h))
        nparts.append((quat_rotate(dv[3:],n)-quat_rotate(-dv[3:],n))/(2*h))
    xerr=float(np.max(np.abs(np.array(xp).T-Jx)))
    nerr=float(np.max(np.abs(np.array(nparts).T-Jn)))
    assert xerr<8e-11 and nerr<8e-11
    assert_close(n@Jn,np.zeros(6))
    return {'status':'pass','max_position_jacobian_error':xerr,'max_normal_jacobian_error':nerr,
            'oracle':'Hamilton quaternion composition and central differences','perturbed_vector_evaluations':24}


def play_checks():
    x=[0,.2,.4,.3,.2,.1,0,-.1,0,.1]
    expected=[0,.1,.3,.3,.3,.2,.1,0,0,0]
    y=subject.play_backlash(x,.1,0)
    assert_close(y,expected)
    assert x[1]==x[4] and abs(y[1]-y[4])>.19
    assert_close(subject.play_backlash([0,.2,-.1],0,0),[0,.2,-.1])
    assert abs(y[2]-y[4])<1e-15 and abs(x[2]-x[4]-.2)<1e-15
    return {'status':'pass','half_width':.1,'reversal_dead_travel':.2,'same_input_history_outputs':[y[1],y[4]]}


def observability_checks():
    J=np.array([[1,.2],[0,1],[1,-1],[2,.4],[-1,.6],[.3,-.2]],float)
    B=np.array([[1,0],[1,1],[0,1],[.4,.2],[-.3,.7],[.8,-.5]],float)
    D=np.array([[1,.2,0,0,0,0],[.1,1.3,.1,0,0,0],[0,.1,.8,.2,0,0],
                [0,0,.2,1.2,.1,0],[0,0,0,.1,.9,.2],[0,0,0,0,.2,1.1]],float)
    C=D@D.T+.3*np.eye(6); scales=[.05,3.]
    r=subject.local_observability(J,B,C,scales)
    # Independent oracle: full physical-coordinate joint Fisher inverse block.
    K=np.column_stack((J,B)); joint=np.linalg.inv(K.T@np.linalg.solve(C,K))
    assert r['rank']==2 and r['nuisance_rank']==2
    err=float(np.max(np.abs(np.array(r['noise_conditional_covariance'])-joint[:2,:2])))
    assert err<2e-12
    r_units=subject.local_observability(J,B*[1e-12,1e12],C,[2.,.001])
    assert_close(r['noise_conditional_covariance'],r_units['noise_conditional_covariance'],2e-11)
    s=np.array([.1,2.,3.]); null_case=subject.local_observability([[1,2,3]],np.empty((1,0)),[[2.]],s)
    Ns=np.array(null_case['null_scaled']); Np=np.array(null_case['null_physical'])
    assert null_case['rank']==1 and Ns.shape==(2,3)
    assert_close(Ns@Ns.T,np.eye(2)); assert_close(np.array([[1,2,3]])@Np.T,np.zeros((1,2)))
    assert null_case['noise_conditional_covariance'] is None
    # Height/source global invariance, then correlated-noise projected rank zero.
    A,z,T,z2=2.3,1.7,4.,2.1
    assert_close(A*T/z**2,A*(z2/z)**2*T/z2**2)
    C4=np.eye(4)+.2*np.ones((4,4))
    h=subject.local_observability(np.full((4,1),-2/z),np.ones((4,1)),C4,[.02])
    assert h['rank']==0 and h['noise_conditional_covariance'] is None
    restored=subject.local_observability([[-2/z],[1]],[[1],[0]],[[1,.2],[.2,1]],[.02])
    assert restored['rank']==1
    clock=subject.local_observability(np.tile([1,2.7],(5,1)),np.empty((5,0)),np.eye(5),[.1,.02])
    assert clock['rank']==1
    varied=subject.local_observability(np.column_stack((np.ones(5),[1,1.3,2,2.4,3])),np.empty((5,0)),np.eye(5),[.1,.02])
    assert varied['rank']==2
    # Oblique collinear layout, not the author's y=0 special case.
    xx=np.array([-.1,0,.2]); xy=np.column_stack((xx,2*xx+.3))
    probe=subject.axial_probe_design(xy); assert_close(probe@[-.3,1,2],np.zeros(3))
    collinear=subject.local_observability(probe,np.empty((3,0)),np.eye(3),[.01,.02,.02])
    assert collinear['rank']==2
    triangle=subject.axial_probe_design([[.2,.1],[-.1,.1],[.05,-.2]])
    assert subject.local_observability(triangle,np.empty((3,0)),np.eye(3),[.01,.02,.02])['rank']==3
    assert subject.local_observability(triangle,np.eye(3),np.eye(3),[.01,.02,.02])['rank']==0
    return {'status':'pass','joint_inverse_covariance_max_error':err,'height_rank':h['rank'],
            'height_independent_probe_rank':restored['rank'],'clock_constant_rank':clock['rank'],
            'clock_varying_rank':varied['rank'],'oblique_collinear_rank':collinear['rank'],
            'max_matrix_shape':[6,6]}


def nuisance_cutoff_counterexample():
    # A has exactly the same column direction as a difference of represented B columns.
    eps=2.**-40; v=np.array([1.,-1.,1.,-1.])
    B=np.column_stack((np.ones(4),np.ones(4)+eps*v))
    coeff=np.array([-1/eps,1/eps])
    assert_close(B@coeff,v,0)
    r=subject.local_observability(v[:,None],B,np.eye(4),[1])
    tight=subject.local_observability(v[:,None],B,np.eye(4),[1],1e-14)
    if r['rank'] is None and r['noise_conditional_covariance'] is None:
        status='conservative_unresolved'
    elif r['rank']==0 and r['noise_conditional_covariance'] is None:
        status='strict_degeneracy_detected'
    else:
        status='limitation_reproduced'
    return {'status':status,'epsilon':eps,'exact_nuisance_compensation_residual':float(np.linalg.norm(B@coeff-v)),
            'default_result':r,'tighter_tolerance_result':tight,
            'meaning':'Numerical nuisance truncation can manufacture data information unless discarded directions are explicitly excluded or bounded.'}


def admission_checks():
    base=json.loads((ROOT/'data/synthetic_observations.json').read_text())
    def admit(csv_text,change=None):
        d=copy.deepcopy(base); raw=csv_text.encode()
        d['channels'][0]['raw_source']['sha256']=hashlib.sha256(raw).hexdigest()
        if change: change(d)
        with patch.object(Path,'read_text',return_value=json.dumps(d)), \
             patch.object(Path,'read_bytes',return_value=raw), \
             patch.object(Path,'open',return_value=io.StringIO(csv_text)), \
             warnings.catch_warnings():
            warnings.simplefilter('ignore',RuntimeWarning)
            return subject.load_observation_dataset(ROOT/'data/synthetic_observations.json',True)
    valid='time_device_s,value\n0,1\n1,2\n'
    negatives={
        'wrong_angle_unit':(valid,lambda d:d['channels'][0].update(unit='deg')),
        'missing_clock_evidence':(valid,lambda d:d['channels'][0]['time_map'].update(evidence='')),
        'zero_clock_scale':(valid,lambda d:d['channels'][0]['time_map'].update(scale=0)),
        'raw_hash_mismatch':(valid,lambda d:d['channels'][0]['raw_source'].update(sha256='0'*64)),
        'parent_path_escape':(valid,lambda d:d['channels'][0]['raw_source'].update(relative_path='../x.csv')),
        'nonfinite_raw_value':('time_device_s,value\n0,nan\n',None),
        'duplicate_device_time':('time_device_s,value\n0,1\n0,2\n',None),
    }
    results={}
    for name,(raw,change) in negatives.items():
        try: admit(raw,change)
        except (ValueError,OSError,TypeError,KeyError) as e: results[name]={'status':'pass_rejected','exception':type(e).__name__}
        else: results[name]={'status':'fail_accepted'}
    assert all(x['status']=='pass_rejected' for x in results.values())
    counterexamples={
        'extra_csv_fields':('time_device_s,value\n0,1,unmodelled\n1,2,unmodelled\n',None),
        'mapped_time_collapse':('time_device_s,value\n0,1\n1e-6,2\n',lambda d:d['channels'][0]['time_map'].update(offset_s=1e12)),
        'mapped_time_overflow':('time_device_s,value\n1e308,1\n1.1e308,2\n',lambda d:d['channels'][0]['time_map'].update(scale=10.)),
    }
    for name,(raw,change) in counterexamples.items():
        try: r=admit(raw,change)
        except (ValueError,OSError,TypeError,KeyError) as e: results[name]={'status':'rejected','exception':type(e).__name__}
        else:
            t=r['channels'][0]['time_reference_s']
            results[name]={'status':'defect_reproduced_accepted','mapped_time':[str(x) if not math.isfinite(x) else x for x in t]}
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,help='Explicit optional JSON destination; default prints only. Preserve the initial independent_results.json.')
    args=parser.parse_args()
    started=time.monotonic(); before=digest_inputs()
    result={'review_kind':'one bounded independent mathematical/interface check; not a specified-model review chain',
            'input_sha256':before,'pose':pose_checks(),'play':play_checks(),
            'observability':observability_checks(),'nuisance_cutoff':nuisance_cutoff_counterexample(),
            'admission':admission_checks()}
    result['inputs_unchanged_during_run']=before==digest_inputs()
    result['wall_seconds']=time.monotonic()-started
    assert result['inputs_unchanged_during_run'] and result['wall_seconds']<60
    result['summary']={'math':'pass',
                       'interface_counterexamples_accepted':sum(x['status']=='defect_reproduced_accepted' for x in result['admission'].values()),
                       'nuisance_false_information_reproduced':result['nuisance_cutoff']['status']=='limitation_reproduced'}
    encoded=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if args.output is not None:
        args.output.write_text(encoded,encoding='utf-8')
    print(encoded,end='')


if __name__=='__main__': main()
