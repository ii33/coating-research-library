#!/usr/bin/env python3
"""Finite independent face-oracle checks. --record saves author-run evidence.
Default execution is read-only, including in a copied reader directory.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import permutations, product
from collections import Counter
import hashlib
import json
import math
import random
import sys
import time
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'models'))
from robust_mask import RectangleMask, Verdict, HitResult, combine_masks, transmitted_sum_interval
I = ((1.,0.,0.), (0.,1.,0.), (0.,0.,1.))
SEED = 202610020506


class Budget:
    def __init__(self):
        self.start = time.monotonic()
        self.count = Counter()
    def add(self, kind):
        self.count[kind] += 1
        if sum(self.count.values()) > 40000 or time.monotonic()-self.start > 180:
            raise RuntimeError('pre-registered per-run budget exceeded')
    def stats(self):
        return {'counts':dict(self.count), 'total_evaluations':sum(self.count.values()),
                'limit_evaluations':40000, 'wall_seconds':time.monotonic()-self.start,
                'wall_limit_seconds':180}


def face_oracle(g, a, b):
    """Independent six-face enumeration, not slab enter/leave intersection.

    Dot products are recomputed directly from public geometry input, without
    calling production transforms or reading its preprocessed bounds.
    """
    c, q, w, h, thick = g
    q = tuple(tuple(F(x) for x in row) for row in q)
    aa = tuple(sum((F(a[i])-F(c[i]))*q[i][j] for i in range(3)) for j in range(3))
    bb = tuple(sum((F(b[i])-F(c[i]))*q[i][j] for i in range(3)) for j in range(3))
    direction = tuple(y-x for x,y in zip(aa,bb))
    bounds = (F(w), F(h), F(thick)/2)
    inside = lambda point: all(abs(point[j]) <= bounds[j] for j in range(3))
    if thick == 0:
        if aa[2] == bb[2] or not (min(aa[2],bb[2]) < 0 < max(aa[2],bb[2])):
            return False
        # Homogeneous face test avoids using the production hit-point formula.
        d = bb[2]-aa[2]
        return all(abs(aa[j]*bb[2]-bb[j]*aa[2]) <= bounds[j]*abs(d) for j in (0,1))
    # Fully contained/coplanar segments have an interior parameter witness.
    if inside(tuple((x+y)/2 for x,y in zip(aa,bb))):
        return True
    for j in range(3):
        if direction[j] == 0:
            continue
        for wall in (-bounds[j], bounds[j]):
            t = (wall-aa[j])/direction[j]
            if 0 < t < 1 and inside(tuple(aa[k]+t*direction[k] for k in range(3))):
                return True
    return False


def legacy_identity_solid(g, a, b):
    """Attributable small transcription of v0.1 RectangleMask.blocked slab branch.
    Identity frame only. Reproduces the fixed SI epsilon mechanism, not a full API.
    """
    c, _, w, h, thick = g
    aa = [x-y for x,y in zip(a,c)]; bb = [x-y for x,y in zip(b,c)]
    enter, leave = -math.inf, math.inf
    for x,y,bound in zip(aa,bb,(w,h,thick/2)):
        d=y-x
        if abs(d) <= 1e-14:
            if abs(x)>bound: return False
        else:
            lo,hi=(-bound-x)/d,(bound-x)/d
            enter=max(enter,min(lo,hi)); leave=min(leave,max(lo,hi))
    return max(enter,0)<=min(leave,1) and leave>0 and enter<1


def run():
    budget=Budget(); groups=Counter(); verdicts=Counter(); failures=[]
    def check(name,g,a,b,expected=None):
        mask=RectangleMask(*g)
        budget.add('predicate'); r=mask.classify(a,b)
        budget.add('oracle'); truth=face_oracle(g,a,b)
        assert (r.verdict is Verdict.BLOCKED)==truth, (name,r,truth,g,a,b)
        assert r.verdict is not Verdict.UNKNOWN
        if expected is not None: assert truth==expected, (name,truth,expected)
        groups[name.split('/')[0]]+=1; verdicts[r.verdict.value]+=1
        return r
    def classified(mask,a,b,margin=0.):
        budget.add('predicate'); return mask.classify(a,b,local_margin_m=margin)
    solid=((0.,0.,0.),I,.1,.2,.04)
    thin=((0.,0.,0.),I,.1,.2,0.)
    base_a=(.1+4e-15,0.,-.1); base_b=(.1-4e-15,0.,.1)
    deterministic=[
      ('known_sidewall',solid,base_a,base_b,True),
      ('parallel_outside',solid,(.1+4e-15,0.,-.1),(.1+4e-15,0.,.1),False),
      ('parallel_inside',solid,(.1-4e-15,0.,-.1),(.1-4e-15,0.,.1),True),
      ('parallel_on_face',solid,(.1,0.,-.1),(.1,0.,.1),True),
      ('axial_front_back',solid,(0.,0.,-.1),(0.,0.,.1),True),
      ('contained',solid,(0.,0.,0.),(.01,.01,.01),True),
      ('outside',solid,(1.,0.,0.),(2.,0.,0.),False),
      ('start_only',solid,(.1,0.,0.),(.2,0.,0.),False),
      ('end_only',solid,(.2,0.,0.),(.1,0.,0.),False),
      ('start_then_inside',solid,(.1,0.,0.),(0.,0.,0.),True),
      ('face_coplanar',solid,(.1,-.3,0.),(.1,.3,0.),True),
      ('edge_coplanar',solid,(.1,.2,-.1),(.1,.2,.1),True),
      ('corner_tangent',solid,(0.,.3,.02),(.2,.1,.02),True),
      ('zero_segment_inside',solid,(0.,0.,0.),(0.,0.,0.),True),
      ('zero_segment_outside',solid,(.3,0.,0.),(.3,0.,0.),False),
      ('thin_cross',thin,(0.,0.,-.1),(0.,0.,.1),True),
      ('thin_small_cross',thin,(0.,0.,-4e-16),(0.,0.,4e-16),True),
      ('thin_coplanar',thin,(0.,0.,0.),(.05,0.,0.),False),
      ('thin_start_only',thin,(0.,0.,0.),(0.,0.,.1),False),
      ('thin_end_only',thin,(0.,0.,-.1),(0.,0.,0.),False),
      ('thin_edge',thin,(.1,0.,-.1),(.1,0.,.1),True),
      ('thin_outside',thin,(math.nextafter(.1,math.inf),0.,-.1),(math.nextafter(.1,math.inf),0.,.1),False),
      ('thin_zero_segment',thin,(0.,0.,0.),(0.,0.,0.),False),
    ]
    for label,g,a,b,truth in deterministic:
        check('deterministic/'+label,g,a,b,truth)
    budget.add('legacy'); old=legacy_identity_solid(solid,base_a,base_b)
    assert old is False
    reproduced={'source_m':base_a,'target_m':base_b,'encoded_x_displacement_m':base_b[0]-base_a[0],
                'legacy_blocked':old,'replacement':'blocked','independent_face_oracle':'blocked',
                'source_x_hex':base_a[0].hex(),'target_x_hex':base_b[0].hex()}
    # Proper signed permutations, power-of-two scales, and segment reversal.
    for perm in permutations(range(3)):
        parity=(-1)**sum(perm[i]>perm[j] for i in range(3) for j in range(i+1,3))
        for signs in product((-1,1),repeat=3):
            if parity*math.prod(signs)!=1: continue
            P=tuple(tuple(float(signs[i]) if j==perm[i] else 0. for j in range(3)) for i in range(3))
            transform=lambda p:tuple(sum(P[i][j]*p[j] for j in range(3)) for i in range(3))
            for exponent in (-40,-20,0,20,40):
                s=2.**exponent
                g=((0.,0.,0.),P,.1*s,.2*s,.04*s)
                a=transform(tuple(x*s for x in base_a)); b=transform(tuple(x*s for x in base_b))
                check('scale_symmetry/forward',g,a,b,True)
                check('scale_symmetry/reverse',g,b,a,True)
    for c in ((.5,-.25,.125),(-.5,.25,-.125)):
        g=(c,I,.1,.2,.04)
        check('translation/preserved',g,tuple(x+y for x,y in zip(base_a,c)),tuple(x+y for x,y in zip(base_b,c)),True)
    rng=random.Random(SEED)
    for group in range(6):
        angle=rng.uniform(-math.pi,math.pi); ca,sa=math.cos(angle),math.sin(angle)
        Q=((ca,-sa,0.),(sa,ca,0.),(0.,0.,1.))
        c=tuple(rng.uniform(-.2,.2) for _ in range(3))
        g=(c,Q,.1,.2,0. if group%3==0 else .04)
        for j in range(1000):
            a=tuple(rng.uniform(-.7,.7) for _ in range(3))
            b=tuple(rng.uniform(-.7,.7) for _ in range(3))
            check('ordinary/%d/%d'%(group,j),g,a,b)
    for j in range(2000):
        exponent=rng.randrange(44,61); delta=2.**(-exponent)
        y=rng.uniform(-.3,.3)
        sign=rng.choice((-1.,1.)); shift=rng.choice((-2.,-1.,0.,1.,2.))*delta
        if j%4==0:
            a=(rng.uniform(-.15,.15),y,-delta); b=(a[0],y,delta)
            g=thin
        else:
            a=(sign*.1+delta+shift,y,-.1)
            b=(sign*.1-delta+shift,y,.1)
            g=solid
        check('adversarial/%d'%j,g,a,b)
    # Input uncertainty: margin encloses endpoint L-infinity errors; test all
    # endpoint perturbation signs on x,y,z for each of the selected ray families.
    mask=RectangleMask(*solid); margin=2.**-20
    margin_cases=[((0.,0.,-.1),(0.,0.,.1),Verdict.BLOCKED),
                  ((.3,0.,-.1),(.3,0.,.1),Verdict.CLEAR),
                  ((.1,0.,-.1),(.1,0.,.1),Verdict.UNKNOWN),
                  ((.1,0.,0.),(.2,0.,0.),Verdict.UNKNOWN)]
    margin_counts=Counter()
    for a,b,expected in margin_cases:
        result=classified(mask,a,b,margin); assert result.verdict is expected
        margin_counts[result.verdict.value]+=1
        for signs in product((-1.,1.),repeat=6):
            # perturb in exact binary64 at a dyadic radius; Fraction measures
            # the actual perturbation to ensure it lies within the assumed bound.
            delta=margin/4
            ap=tuple(a[k]+signs[k]*delta for k in range(3))
            bp=tuple(b[k]+signs[k+3]*delta for k in range(3))
            assert all(abs(F(x)-F(y))<=F(margin) for x,y in zip(ap+bp,a+b))
            budget.add('oracle'); hit=face_oracle(solid,ap,bp)
            low,high=result.transmission_interval
            assert low<=int(not hit)<=high
            groups['margin_perturbation_witness']+=1
    thinmask=RectangleMask(*thin)
    assert classified(thinmask,(0.,0.,-.1),(0.,0.,.1),margin).verdict is Verdict.UNKNOWN
    assert classified(thinmask,(.3,0.,-.1),(.3,0.,.1),margin).verdict is Verdict.CLEAR
    # Explicit no-Boolean API and union/weighted visibility interval behavior.
    rclear=HitResult(Verdict.CLEAR,'test'); rblock=HitResult(Verdict.BLOCKED,'test'); runknown=HitResult(Verdict.UNKNOWN,'test')
    try: bool(runknown)
    except TypeError: pass
    else: raise AssertionError('unknown converted to Boolean')
    assert runknown.blocks_conservatively()
    assert combine_masks([rclear,runknown]).verdict is Verdict.UNKNOWN
    assert combine_masks([rblock,runknown]).verdict is Verdict.BLOCKED
    assert combine_masks([]).verdict is Verdict.CLEAR
    interval=transmitted_sum_interval([.1,.2,.3],[rclear,runknown,rblock])
    assert F(interval[0])<=F(.1) and F(interval[1])>=F(.1)+F(.2)
    assert interval[0]>=0
    invalid_tests=[lambda:RectangleMask((0.,0.,0.),I,0.,.2,.04),
      lambda:RectangleMask((0.,0.,0.),I,2.**-81,.2,.04),
      lambda:RectangleMask((0.,0.,0.),I,.1,.2,-1.),
      lambda:RectangleMask((0.,0.,0.),((-1.,0.,0.),(0.,1.,0.),(0.,0.,1.)),.1,.2,.04),
      lambda:RectangleMask((0.,0.,0.),((2.,0.,0.),(0.,1.,0.),(0.,0.,1.)),.1,.2,.04),
      lambda:classified(mask,(math.inf,0.,0.),(0.,0.,0.)),
      lambda:classified(mask,(math.nan,0.,0.),(0.,0.,0.)),
      lambda:classified(mask,(2.**81,0.,0.),(0.,0.,0.)),
      lambda:classified(mask,(2.**-201,0.,0.),(0.,0.,0.)),
      lambda:classified(mask,(0.,0.,0.),(0.,0.,0.),-1.),
      lambda:mask.classify_many([((0.,0.,0.),(0.,0.,0.))]*4097),
      lambda:transmitted_sum_interval([-1.],[rclear]),
      lambda:transmitted_sum_interval([1.],[]),
      lambda:HitResult('unknown','invalid'),
      lambda:HitResult('blocked','invalid'),
      lambda:HitResult('nonsense','invalid'),
      lambda:HitResult(None,'invalid'),
      lambda:mask.classify_many([],local_margin_m=-1.)]
    for call in invalid_tests:
        try: call()
        except (ValueError,TypeError): pass
        else: raise AssertionError('invalid input accepted')
    return {'status':'pass','seed':SEED,'groups':dict(groups),'nominal_verdicts':dict(verdicts),
            'known_counterexample':reproduced,'margin_case_verdicts':dict(margin_counts),
            'thin_positive_margin':'unknown_by_design','invalid_cases_rejected':len(invalid_tests),
            'visibility_sum_example':interval,'budget':budget.stats(),
            'source_time_grid_runs':0,'scope':'encoded_geometry_only; input uncertainty conditional on supplied margin',
            'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (ROOT/'models/robust_mask.py',Path(__file__).resolve(),ROOT/'verification/PRE_REGISTERED_PROTOCOL.md')}}


if __name__=='__main__':
    out=run()
    if '--record' in sys.argv:
        ledger_path=ROOT/'verification/execution_ledger.json'
        ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else {'main_cumulative_limit':160000,'runs':[]}
        used=sum(x['total_evaluations'] for x in ledger['runs'])+out['budget']['total_evaluations']
        if used>ledger['main_cumulative_limit']: raise RuntimeError('cumulative budget exceeded')
        ledger['runs'].append(out['budget']); ledger['main_cumulative_evaluations']=used
        ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
        (ROOT/'data/check_results.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
