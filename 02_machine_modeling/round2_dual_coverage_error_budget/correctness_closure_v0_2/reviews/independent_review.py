"""One bounded independent audit; no implementation changes or external inputs.

Independent oracle enumerates world-halfspace boundary parameters and an interior
parameter, without slab clipping or calling private implementation helpers.
"""
import sys
sys.dont_write_bytecode = True
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import random
import time
from fractions import Fraction as F

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('audited_robust_mask', ROOT/'models/robust_mask.py')
M = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = M
spec.loader.exec_module(M)
START = time.monotonic()
COUNTS = {'predicate_evaluations': 0, 'oracle_evaluations': 0,
          'aggregate_checks': 0, 'assertions': 0, 'invalid_checks': 0}
FAILURES = []
GROUPS = {}
I = ((1.,0.,0.),(0.,1.,0.),(0.,0.,1.))
SEED = 2718281828
rng = random.Random(SEED)


def tick(kind):
    COUNTS[kind] += 1
    if COUNTS['predicate_evaluations'] + COUNTS['oracle_evaluations'] > 20000:
        raise RuntimeError('Independent predicate/oracle budget exceeded')
    if time.monotonic() - START > 180:
        raise RuntimeError('Independent run exceeded 180 seconds')


def check(condition, label, data=None):
    COUNTS['assertions'] += 1
    if not condition:
        item = {'label': label, 'data': data}
        FAILURES.append(item)
        print('FAIL ' + json.dumps(item, default=str), flush=True)


def oracle(center, Q, sizes, a, b):
    """Exact encoded geometry in world coordinates, candidate enumeration."""
    tick('oracle_evaluations')
    c, p, r = map(lambda xs: tuple(F(x) for x in xs), (center,a,b))
    q = tuple(tuple(F(x) for x in row) for row in Q)
    h = (F(sizes[0]), F(sizes[1]), F(sizes[2])/2)
    # The line coefficients are formed directly from world halfspaces.
    alpha = tuple(sum(q[i][j]*p[i] for i in range(3)) -
                  sum(q[i][j]*c[i] for i in range(3)) for j in range(3))
    beta = tuple(sum(q[i][j]*(r[i]-p[i]) for i in range(3)) for j in range(3))
    if h[2] == 0:
        if beta[2] == 0:
            return False
        t = -alpha[2]/beta[2]
        return 0 < t < 1 and all(abs(alpha[j]+t*beta[j]) <= h[j] for j in (0,1))
    ts = [F(1,2)]
    for j in range(3):
        if beta[j]:
            ts += [(sgn*h[j]-alpha[j])/beta[j] for sgn in (-1,1)]
    return any(0 < t < 1 and all(abs(alpha[j]+t*beta[j]) <= h[j]
                                for j in range(3)) for t in ts)


def pred(mask, a, b, margin=0.):
    tick('predicate_evaluations')
    return mask.classify(a,b,local_margin_m=margin).verdict


def case(label, c, Q, dims, a, b, expected=None):
    mask = M.RectangleMask(c,Q,*dims)
    actual = pred(mask,a,b)
    ref = oracle(c,Q,dims,a,b)
    check(actual is (M.Verdict.BLOCKED if ref else M.Verdict.CLEAR), label+'_oracle',
          {'center':c,'frame':Q,'sizes':dims,'source':a,'target':b,'actual':actual,'reference':ref})
    if expected is not None:
        check(ref == expected, label+'_explicit_convention')
    return actual


def raises(fn, label):
    COUNTS['invalid_checks'] += 1
    try:
        fn()
    except (TypeError, ValueError, OverflowError):
        check(True,label)
    else:
        check(False,label)


# Explicit convention and contact cases, including constant parametrizations.
fixed = [
 ('old_sidewall_miss',(.1+4e-15,0,-.1),(.1-4e-15,0,.1),True),
 ('axial_through',(0,0,-.1),(0,0,.1),True),
 ('axial_outside',(.2,0,-.1),(.2,0,.1),False),
 ('parallel_outside',(.2,0,0),(.2,.1,0),False),
 ('parallel_face',(.1,0,0),(.1,.1,0),True),
 ('interior',(0,0,0),(.01,.01,.01),True),
 ('same_inside',(0,0,0),(0,0,0),True),
 ('same_surface',(.1,.2,.02),(.1,.2,.02),True),
 ('same_outside',(.2,.2,.02),(.2,.2,.02),False),
 ('start_face_out',(.1,0,0),(.2,0,0),False),
 ('end_face_out',(.2,0,0),(.1,0,0),False),
 ('start_face_in',(.1,0,0),(0,0,0),True),
 ('end_face_in',(0,0,0),(.1,0,0),True),
 ('front_endpoint',(0,0,-.1),(0,0,-.02),False),
 ('back_endpoint',(0,0,.02),(0,0,.1),False),
 ('edge_tangent',(0,.3,0),(.2,.1,0),None),
 ('edge_exact',(-.25,.75,0),(.75,-.25,0),None),
 ('near_parallel_inside',(.1-4e-15,0,-.1),(.1-8e-15,0,.1),True),
 ('near_parallel_outside',(.1+4e-15,0,-.1),(.1+8e-15,0,.1),False),
 ('front_parallel',(0,0,-.03),(.01,.01,-.03),False),
]
for name,a,b,expected in fixed:
    case(name,(0,0,0),I,(.1,.2,.04),a,b,expected)
    case(name+'_reverse',(0,0,0),I,(.1,.2,.04),b,a,expected)
# Exactly representable corner/edge tangencies.
case('one_point_corner',(0,0,0),I,(.25,.25,.5),(-.5,0,0),(0,.5,0),True)
case('corner_endpoint',(0,0,0),I,(.25,.25,.5),(-.5,0,0),(-.25,.25,0),False)
for name,a,b,expect in [
 ('cross',(0,0,-1),(0,0,1),True), ('coplanar',(0,0,0),(.05,0,0),False),
 ('constant',(0,0,0),(0,0,0),False), ('start',(0,0,0),(0,0,1),False),
 ('end',(0,0,1),(0,0,0),False), ('edge',(.1,0,-1),(.1,0,1),True),
 ('corner',(.1,.2,-1),(.1,.2,1),True), ('tiny_cross',(0,0,-2.**-199),(0,0,2.**-199),True),
 ('parallel',(0,0,2.**-199),(.05,0,2.**-199),False)]:
    case('thin_'+name,(0,0,0),I,(.1,.2,0),a,b,expect)
GROUPS['deterministic_cases'] = len(fixed)*2 + 2 + 9

# All 24 proper signed-permutation frames and five fixed power-of-two scales.
def determinant(a):
    return (a[0][0]*(a[1][1]*a[2][2]-a[1][2]*a[2][1])-
            a[0][1]*(a[1][0]*a[2][2]-a[1][2]*a[2][0])+
            a[0][2]*(a[1][0]*a[2][1]-a[1][1]*a[2][0]))
frames=[]
for p in itertools.permutations(range(3)):
    for signs in itertools.product((-1,1),repeat=3):
        q=tuple(tuple(signs[j] if i==p[j] else 0 for j in range(3)) for i in range(3))
        if determinant(q)==1: frames.append(q)
def world(q,p): return tuple(sum(q[i][j]*p[j] for j in range(3)) for i in range(3))
for k in (-40,-20,0,20,40):
    s=2.**k
    aa=tuple(x*s for x in fixed[0][1]); bb=tuple(x*s for x in fixed[0][2])
    for j,q in enumerate(frames):
        case(f'scale_{k}_frame_{j}',(0,0,0),q,(.1*s,.2*s,.04*s),world(q,aa),world(q,bb),True)
        case(f'scale_{k}_frame_{j}_reverse',(0,0,0),q,(.1*s,.2*s,.04*s),world(q,bb),world(q,aa),True)
# Translation uses separately encoded center and endpoints and does not assume
# that rounding a world-coordinate translation preserves the original ray.
for shift in (2.**-20, 1., 8., 2.**20):
    c=(shift,-shift,shift)
    a=tuple(x+y for x,y in zip(fixed[0][1],c)); b=tuple(x+y for x,y in zip(fixed[0][2],c))
    case('translation_'+str(shift),c,I,(.1,.2,.04),a,b)
GROUPS['scale_sign_translation_cases']=244

# Independent fixed-seed ordinary cases, including rounded proper rotations.
for j in range(1800):
    angle=rng.uniform(-math.pi,math.pi); cs=math.cos(angle); sn=math.sin(angle)
    q=((cs,-sn,0),(sn,cs,0),(0,0,1)) if j%2 else I
    c=tuple(rng.uniform(-4,4) for _ in range(3))
    s=2.**rng.randrange(-40,41)
    dims=(s*rng.uniform(.05,.5),s*rng.uniform(.05,.5),s*rng.uniform(.01,.4) if j<1300 else 0.)
    a=tuple(c[i]+s*rng.uniform(-1,1) for i in range(3))
    b=tuple(c[i]+s*rng.uniform(-1,1) for i in range(3))
    case('random_'+str(j),c,q,dims,a,b)
GROUPS['seeded_ordinary_cases']=1800

# Adjacent-representable and dyadic sidewall/plane cases, no seed search.
for j in range(800):
    s=2.**rng.randrange(-60,61)
    side=s*.125
    ulp=math.ulp(side)
    x1=side+rng.randrange(-8,9)*ulp; x2=side+rng.randrange(-8,9)*ulp
    a=(x1,0.,-.5*s); b=(x2,0.,.5*s)
    t=(0 if j%4==0 else .0625*s)
    case('adversarial_'+str(j),(0,0,0),I,(side,.25*s,t),a,b)
GROUPS['seeded_adversarial_cases']=800

# Extremal valid magnitudes and a slightly nonorthonormal admitted frame.
for s in (2.**-80,2.**80):
    case('extreme_cross_'+str(s),(0,0,0),I,(s,s,s),(0,0,-s),(0,0,s),True)
case('min_point',(0,0,0),I,(2.**-80,2.**-80,0.),(0,0,-2.**-200),(0,0,2.**-200),True)
near=((1.+2.**-44,0.,0.),(0.,1.,0.),(0.,0.,1.))
case('unrepaired_frame',(0,0,0),near,(.25,.25,.125),(.25,0,-1),(.25,0,1),False)
GROUPS['extreme_numeric_cases']=4

# Margin certification under independently varied dyadic endpoint and boundary
# perturbations. The point error and half-boundary error are each <= margin/2.
# Exact dyadic arithmetic avoids accidentally exceeding the assumed budget.
margin_counts={'blocked':0,'clear':0,'unknown':0}
for j in range(400):
    h=(.25,.5,.125 if j<300 else 0.)
    a=tuple(rng.randrange(-20,21)/32 for _ in range(3))
    b=tuple(rng.randrange(-20,21)/32 for _ in range(3))
    m=1/32
    mask=M.RectangleMask((0,0,0),I,h[0],h[1],2*h[2])
    v=pred(mask,a,b,m); margin_counts[v.value]+=1
    baseline=oracle((0,0,0),I,(h[0],h[1],2*h[2]),a,b)
    check(v is M.Verdict.UNKNOWN or (v is M.Verdict.BLOCKED)==baseline,'margin_nominal_'+str(j))
    for n in range(12):
        da=tuple(rng.choice((-1,0,1))/64 for _ in range(3))
        db=tuple(rng.choice((-1,0,1))/64 for _ in range(3))
        dh=tuple(rng.choice((-1,0,1))/64 for _ in range(3))
        hp=tuple(h[i]+dh[i] for i in range(3))
        if h[2]==0:
            # The thin geometric convention is preserved; plane offset is a
            # center-z perturbation sharing the endpoint/boundary budget.
            hp=(hp[0],hp[1],0.)
            cp=(0.,0.,dh[2])
        else: cp=(0.,0.,0.)
        ap=tuple(a[i]+da[i] for i in range(3)); bp=tuple(b[i]+db[i] for i in range(3))
        actual=oracle(cp,I,(hp[0],hp[1],2*hp[2]),ap,bp)
        check(v is M.Verdict.UNKNOWN or (v is M.Verdict.BLOCKED)==actual,
              'margin_witness_'+str(j)+'_'+str(n))
GROUPS['margin_cases']=400; GROUPS['perturbed_margin_witnesses']=4800

# Tri-state truth table and exact outward-rounded sum enclosure.
R={v:M.HitResult(v,'review') for v in M.Verdict}
for n in range(5):
    for states in itertools.product(tuple(M.Verdict),repeat=n):
        expected=(M.Verdict.BLOCKED if M.Verdict.BLOCKED in states else
                  M.Verdict.UNKNOWN if M.Verdict.UNKNOWN in states else M.Verdict.CLEAR)
        check(M.combine_masks([R[x] for x in states]).verdict is expected,'union_truth_table')
for j in range(800):
    n=rng.randrange(0,20)
    weights=[math.ldexp(rng.uniform(.5,1.),rng.randrange(-190,81)) for _ in range(n)]
    states=[rng.choice(tuple(M.Verdict)) for _ in range(n)]
    lo,hi=M.transmitted_sum_interval(weights,[R[x] for x in states])
    elo=sum((F(w) for w,v in zip(weights,states) if v is M.Verdict.CLEAR),F(0))
    ehi=sum((F(w) for w,v in zip(weights,states) if v is not M.Verdict.BLOCKED),F(0))
    COUNTS['aggregate_checks']+=1
    check(F(lo)<=elo<=ehi<=F(hi),'outward_enclosure_'+str(j))
    check((F(lo)==elo or F(math.nextafter(lo,math.inf))>elo) and
          (F(hi)==ehi or F(math.nextafter(hi,-math.inf))<ehi),'tight_directed_rounding_'+str(j))
weights=[2.**80]*4096; states=[R[M.Verdict.CLEAR]]*4096
check(M.transmitted_sum_interval(weights,states)==(2.**92,2.**92),'maximum_sum_domain')
COUNTS['aggregate_checks']+=1

# Domain rejection and no implicit unknown Boolean coercion.
mask=M.RectangleMask((0,0,0),I,.25,.5,.125)
for value in (math.nan,math.inf,-math.inf,True,'0.0',2.**-201,2.**81):
    raises(lambda v=value: mask.classify((v,0,0),(0,0,1)),'invalid_point_'+repr(value))
for value in (-1,2.**-201,2.**81,math.nan,True):
    raises(lambda v=value: mask.classify((0,0,-1),(0,0,1),local_margin_m=v),'invalid_margin_'+repr(value))
for value in (0.,-1.,2.**-81,2.**81):
    raises(lambda v=value: M.RectangleMask((0,0,0),I,v,.5,.125),'invalid_size_'+repr(value))
raises(lambda: M.RectangleMask((0,0,0),((-1,0,0),(0,1,0),(0,0,1)),1,1,1),'reflection_rejected')
raises(lambda: M.RectangleMask((0,0,0),((1.001,0,0),(0,1,0),(0,0,1)),1,1,1),'bad_gram_rejected')
raises(lambda: bool(R[M.Verdict.UNKNOWN]),'unknown_boolean_rejected')
raises(lambda: mask.classify_many([((0,0,0),(0,0,1))]*4097),'oversized_batch_rejected')
raises(lambda: M.transmitted_sum_interval([-1],[R[M.Verdict.UNKNOWN]]),'negative_contribution_rejected')

# Public API contract robustness probes. These are separate from geometric
# correctness: a malformed tri-state must never silently become CLEAR.
for value in ('blocked','unknown','nonsense',None):
    try:
        malformed=M.HitResult(value,'public_constructor')
        combined=M.combine_masks([malformed])
    except (TypeError,ValueError,KeyError):
        check(True,'malformed_verdict_rejected_'+str(value))
    else:
        check(False,'malformed_verdict_accepted_'+str(value),
              {'input_verdict':value,'union_verdict':combined.verdict.value})
raises(lambda: mask.classify_many([],local_margin_m=-1),'empty_batch_negative_margin_rejected')

RESULT={
 'review_status':'FAIL' if FAILURES else 'PASS',
 'seed':SEED,'counts':COUNTS,'groups':GROUPS,'margin_verdict_distribution':margin_counts,
 'failures':FAILURES,'elapsed_seconds':time.monotonic()-START,
 'limits':{'predicate_plus_oracle':20000,'run_seconds':180},
 'hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in
           ('models/robust_mask.py','verification/PRE_REGISTERED_PROTOCOL.md','reviews/independent_review.py')},
 'scope':'One bounded independent review; world-halfspace rational candidate enumeration; no source/time integration or physical exactness claim.'}
(ROOT/'reviews/independent_results.json').write_text(json.dumps(RESULT,indent=2)+'\n')
print(json.dumps(RESULT,indent=2),flush=True)
