"""T01-r3-v0.1.0: small conditional reference, not a production calibration engine.
SI units; active rotations; column vectors; angles unwrapped in radians.
No sensor data are generated, inferred or silently calibrated by this module.
"""
from fractions import Fraction
import hashlib
import csv
import io
import json
import math
from pathlib import Path
import numpy as np


def finite(value, shape=None, name='value'):
    a = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(a)) or (shape is not None and a.shape != shape):
        raise ValueError(f'{name}: finite shape {shape} required')
    return a


def skew(v):
    x, y, z = finite(v, (3,), 'rotation vector')
    return np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])


def exp_so3(v):
    """Rodrigues with stable series at zero; vector norm is angle in radians."""
    v = finite(v, (3,)); theta = float(np.linalg.norm(v)); K = skew(v)
    if theta < 1e-5:
        a = 1 - theta**2/6 + theta**4/120
        b = .5 - theta**2/24 + theta**4/720
    else:
        a, b = math.sin(theta)/theta, (1-math.cos(theta))/theta**2
    return np.eye(3) + a*K + b*(K@K)


def rz(angle):
    a = float(finite(angle, ())); c, s = math.cos(a), math.sin(a)
    return np.array([[c,-s,0.],[s,c,0.],[0.,0.,1.]])


def rotation(Q):
    Q = finite(Q, (3,3), 'rotation')
    if not np.allclose(Q.T@Q, np.eye(3), atol=1e-11, rtol=0) or not math.isclose(np.linalg.det(Q), 1, abs_tol=1e-11):
        raise ValueError('proper orthogonal rotation required')
    return Q


def direct_external_ratio(sun=120, planet=36, topology_confirmed=False):
    """The fact of two tooth counts alone never confirms a transmission topology."""
    if not topology_confirmed:
        raise ValueError('direct external mesh with fixed sun and rigid output must be confirmed')
    if any(type(x) is not int or x <= 0 for x in (sun, planet)):
        raise ValueError('positive integer tooth counts required')
    return Fraction(sun+planet, planet)


def nominal_center_distance(module_m, sun=120, planet=36):
    if module_m is None:
        raise ValueError('module/real center distance is unknown; do not replace by zero')
    m = float(finite(module_m, ()))
    direct_external_ratio(sun, planet, True)
    if m <= 0:
        raise ValueError('module must be positive in m')
    return m*(sun+planet)/2


def pose(theta_c, phi, b_C, carrier_translation_L=(0,0,0),
         carrier_tilt_L=(0,0), planet_translation_C=(0,0,0),
         planet_tilt_C=(0,0), spin_error=0., mount_rotation=None):
    """c=t+Rc(b+dp), Q=Rc Exp(ap) Rz(phi+spin_error) Qmount.
    Both tilts have x,y components only, eliminating duplicate yaw parameters.
    b_C includes nominal height; translations are m, tilts/spin error rad.
    Values are evaluated at one instant; their time/harmonic histories are external.
    """
    ac = finite(carrier_tilt_L, (2,)); ap = finite(planet_tilt_C, (2,))
    Rc = exp_so3([*ac,0.]) @ rz(theta_c)
    c = finite(carrier_translation_L,(3,)) + Rc @ (finite(b_C,(3,)) + finite(planet_translation_C,(3,)))
    Qm = np.eye(3) if mount_rotation is None else rotation(mount_rotation)
    Q = Rc @ exp_so3([*ap,0.]) @ rz(float(finite(phi,())) + float(finite(spin_error,()))) @ Qm
    return c, Q


def point_normal(c, Q, u, n_local=(0,0,-1), eccentricity_W=(0,0,0)):
    Q = rotation(Q); n = finite(n_local,(3,))
    if not math.isclose(float(n@n),1.,abs_tol=1e-12,rel_tol=0):
        raise ValueError('unit local normal required')
    return finite(c,(3,)) + Q@(finite(u,(3,))+finite(eccentricity_W,(3,))), Q@n


def rigid_jacobians(c, x, n):
    """Lab-frame left infinitesimal pose about c: [dc(m), dalpha(rad)]."""
    r = finite(x,(3,))-finite(c,(3,)); n = finite(n,(3,))
    return np.hstack((np.eye(3),-skew(r))), np.hstack((np.zeros((3,3)),-skew(n)))


def play_backlash(input_angle, half_width_rad, initial_output):
    """Rate-independent scalar play, NOT a loaded tooth contact/dynamics model.
    Output y_i=clip(y_{i-1}, x_i-b, x_i+b); initial contact state is required.
    Half width b; total reversal travel 2b. No interpolation across missing data.
    """
    x = finite(input_angle)
    b = float(finite(half_width_rad,())); y = float(finite(initial_output,()))
    if x.ndim != 1 or len(x)==0 or b<0:
        raise ValueError('nonempty 1D angles and nonnegative half-width required')
    if abs(y-x[0]) > b+1e-14:
        raise ValueError('initial output violates contact interval')
    out = [y]
    for xi in x[1:]:
        y = float(np.clip(y,xi-b,xi+b)); out.append(y)
    return np.array(out)


def local_observability(J_mechanical, J_nuisance, covariance, parameter_scales,
                        relative_rank_tolerance=1e-10):
    """Whiten full SPD covariance, project fitted nuisance, SVD scaled mechanics.
    This is a local linear diagnostic, not a global identifiability certificate.
    Covariance is in observation units squared; scales are physical parameter units.
    Returns noise-conditional covariance only when full column rank is present.
    """
    J = finite(J_mechanical); B = finite(J_nuisance); C = finite(covariance)
    s = finite(parameter_scales)
    if J.ndim!=2 or J.shape[0]<1 or J.shape[1]<1:
        raise ValueError('nonempty mechanical Jacobian required')
    n,p = J.shape
    if B.ndim!=2 or B.shape[0]!=n or C.shape!=(n,n) or s.shape!=(p,) or np.any(s<=0):
        raise ValueError('Jacobian/covariance/scales dimensions or signs invalid')
    tol = float(finite(relative_rank_tolerance,()))
    if not 0<tol<1 or not np.allclose(C,C.T,rtol=0,atol=1e-14*np.max(np.abs(C))):
        raise ValueError('rank tolerance invalid or covariance not symmetric')
    try: L=np.linalg.cholesky(C)
    except np.linalg.LinAlgError as exc: raise ValueError('SPD covariance required; handle deterministic constraints separately') from exc
    A=np.linalg.solve(L,J)*s[None,:]; Bw=np.linalg.solve(L,B)
    nuisance_sv=[]; nuisance_unresolved=False
    nuisance_stability_floor=max(tol, float(np.sqrt(np.finfo(float).eps)))
    if B.shape[1]:
        # Normalize nuisance columns to avoid a mere change of parameter units changing rank.
        bn=np.linalg.norm(Bw,axis=0); keep=bn>0
        Bs=Bw[:,keep]/bn[keep] if np.any(keep) else np.empty((n,0))
        U,sv,_=np.linalg.svd(Bs,full_matrices=False)
        rb=int(np.sum(sv>tol*sv[0])) if len(sv) and sv[0]>0 else 0
        nuisance_sv=list(map(float,sv))
        # A tiny nonzero singular direction is still a free nuisance direction.
        # Dropping it can fabricate mechanical information; report unresolved.
        nuisance_unresolved=bool(len(sv)>0 and sv[0]>0 and sv[-1]<=nuisance_stability_floor*sv[0])
        Ar=A-U[:,:rb]@(U[:,:rb].T@A)
    else: rb=0; Ar=A
    U,sv,Vt=np.linalg.svd(Ar,full_matrices=True)
    # Compare to unprojected sensitivity, not tiny cancellation residue after projection.
    reference=float(np.linalg.norm(A,2)); threshold=tol*reference
    rank=int(np.sum(sv>threshold)) if reference>0 else 0
    singular=list(map(float,sv))+[0.]*(p-len(sv))
    result={'rank':None if nuisance_unresolved else rank,
            'rank_under_truncated_nuisance':rank,
            'rank_status':'unresolved_nuisance_subspace' if nuisance_unresolved else 'conditional_local_numerical',
            'nuisance_singular_values':nuisance_sv,
            'nuisance_relative_stability_floor':nuisance_stability_floor,
            'parameters':p,'observations':n,'nuisance_rank':rb,
            'singular_values':singular,'rank_absolute_threshold':threshold,
            'rank_reference':'spectral_norm_of_whitened_scaled_unprojected_J',
            'relative_rank_tolerance':tol,'condition_number':float(sv[0]/sv[-1]) if rank==p and not nuisance_unresolved else None,
            'null_vectors_status':'conditional_on_numerical_nuisance_subspace_not_certified' if nuisance_unresolved else 'conditional_local',
            'null_scaled':Vt[rank:].tolist(),'null_physical':(Vt[rank:]*s).tolist(),
            'noise_conditional_covariance':None,'interpretation':'conditional local linear diagnostic only'}
    if rank==p and not nuisance_unresolved:
        cov_scaled=(Vt[:p].T*(1/sv[:p]**2))@Vt[:p]
        result['noise_conditional_covariance']=(s[:,None]*cov_scaled*s[None,:]).tolist()
    return result


def axial_probe_design(xy_m):
    xy=finite(xy_m)
    if xy.ndim!=2 or xy.shape[1]!=2:
        raise ValueError('probe coordinates must be N by 2 in m')
    return np.column_stack((np.ones(len(xy)),xy[:,1],-xy[:,0]))


def load_observation_dataset(path, allow_synthetic=False):
    """Offline strict admission for the documented CSV observation contract.
    SHA refers to the raw local input file, not this derived JSON. No parent needed.
    Does not authenticate raw data or check calibration validity independently.
    """
    path=Path(path).resolve(); d=json.loads(path.read_text(encoding='utf-8'))
    if d.get('schema_version')!='t01-r3-observations-1': raise ValueError('unknown schema')
    kind=d.get('dataset_kind')
    if kind not in ('measured','synthetic') or (kind=='synthetic' and not allow_synthetic):
        raise ValueError('template/incomplete or synthetic data not admitted')
    if d.get('frame_convention')!='L_right_handed_CCW_view_from_plus_z': raise ValueError('frame convention missing')
    if not d.get('reference_clock_id'): raise ValueError('reference clock required')
    channels=d.get('channels')
    if not isinstance(channels,list) or not channels: raise ValueError('channels required')
    ids=set(); rows=[]
    allowed_units={'carrier_angle':'rad','output_angle':'rad','axial_displacement':'m',
                   'radial_displacement':'m','thickness':'m','source_monitor':'1'}
    for ch in channels:
        sid=ch.get('sensor_id')
        if not isinstance(sid,str) or not sid or sid in ids: raise ValueError('unique sensor_id required')
        ids.add(sid); q=ch.get('quantity')
        if q not in allowed_units or ch.get('unit')!=allowed_units[q]: raise ValueError('quantity/unit mismatch')
        if ch.get('time_unit')!='s' or ch.get('angle_wrap') not in ('unwrapped','not_applicable'):
            raise ValueError('time unit and wrap convention required')
        if q.endswith('angle') and ch['angle_wrap']!='unwrapped': raise ValueError('angles must be unwrapped')
        mp=ch.get('time_map',{}); offset=mp.get('offset_s'); scale=mp.get('scale')
        if offset is None or scale is None or not isinstance(mp.get('evidence'),str) or not mp['evidence']:
            raise ValueError('unresolved clock mapping')
        scale=float(finite(scale,())); offset=float(finite(offset,()))
        if scale<=0: raise ValueError('clock scale must be positive')
        raw=ch.get('raw_source',{}); rel=Path(raw.get('relative_path',''))
        if not str(raw.get('relative_path','')) or rel.is_absolute() or '..' in rel.parts:
            raise ValueError('local confined raw source required')
        target=(path.parent/rel).resolve()
        if not target.is_relative_to(path.parent): raise ValueError('symlink escape forbidden')
        raw_bytes=target.read_bytes()
        digest=raw.get('sha256')
        if not isinstance(digest,str) or len(digest)!=64 or hashlib.sha256(raw_bytes).hexdigest()!=digest:
            raise ValueError('raw source hash mismatch')
        if not ch.get('calibration_status') or not ch.get('sensor_mount_description'):
            raise ValueError('calibration status and mount description required')
        if kind=='measured' and ch['calibration_status']!='traceable_calibrated':
            raise ValueError('measured fit admission requires traceable calibration evidence')
        if kind=='measured' and not ch.get('calibration_evidence'):
            raise ValueError('calibration evidence required')
        with io.StringIO(raw_bytes.decode('utf-8'), newline='') as f:
            reader=csv.DictReader(f)
            if reader.fieldnames!=['time_device_s','value']:
                raise ValueError('CSV header must be time_device_s,value')
            records=list(reader)
            if any(set(r)!= {'time_device_s','value'} or any(v is None for v in r.values()) for r in records):
                raise ValueError('CSV row must contain exactly two fields')
            a=finite([[float(r['time_device_s']),float(r['value'])] for r in records],name='samples')
        if a.ndim!=2 or a.shape[1]!=2 or len(a)<1 or np.any(np.diff(a[:,0])<=0):
            raise ValueError('strictly increasing [device_time,value] samples required')
        with np.errstate(over='ignore',invalid='ignore'):
            mapped=scale*a[:,0]+offset
        if not np.all(np.isfinite(mapped)) or np.any(np.diff(mapped)<=0):
            raise ValueError('clock map produced nonfinite or nonincreasing reference time; use relative time origin')
        rows.append({'sensor_id':sid,'quantity':q,'time_reference_s':mapped.tolist(),
                     'value':a[:,1].tolist(),'unit':ch['unit']})
    return {'dataset_kind':kind,'channels':rows,'status':'admitted_for_interface_only',
            'limitations':'No file authenticity, actual calibration or model validity certification'}
