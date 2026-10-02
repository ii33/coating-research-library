"""Bounded reference predicate for encoded geometry, standard library only.

Not a physical-geometry certificate or production vectorized kernel. See the
numerical contract and uncertainty semantics in reports/01_predicate_and_api.md.
All rational operations use the exact values of admitted Python int/float inputs.
"""
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction as F
import math

MIN_INPUT = F(1, 2**200)
MAX_INPUT = F(2**80)
MIN_SIZE = F(1, 2**80)
FRAME_RESIDUAL = F.from_float(1e-12)
MAX_BATCH = 4096


class Verdict(str, Enum):
    BLOCKED = 'blocked'
    CLEAR = 'clear'
    UNKNOWN = 'unknown'


@dataclass(frozen=True)
class HitResult:
    verdict: Verdict
    reason: str

    def __post_init__(self):
        if not isinstance(self.verdict, Verdict):
            raise TypeError('verdict must be a Verdict member, not a string or arbitrary value')

    def __bool__(self):
        raise TypeError('A tri-state hit result has no Boolean value; inspect verdict or transmission_interval')

    @property
    def transmission_interval(self):
        return {Verdict.BLOCKED: (0, 0), Verdict.CLEAR: (1, 1),
                Verdict.UNKNOWN: (0, 1)}[self.verdict]

    def blocks_conservatively(self):
        """True for unknown: lower transmitted nonnegative flux, NOT every metric."""
        return self.verdict is not Verdict.CLEAR


def _q(value, name, max_abs=MAX_INPUT):
    if type(value) not in (int, float):
        raise TypeError(f'{name}: Python int or binary64 float required')
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f'{name}: finite value required')
    q = F(value)
    if abs(q) > max_abs or (q and abs(q) < MIN_INPUT):
        raise ValueError(f'{name}: outside admitted numeric domain')
    return q


def _v3(values, name):
    if len(values) != 3:
        raise ValueError(f'{name}: length 3 required')
    return tuple(_q(x, name) for x in values)


def _solid_hit(a, b, bounds):
    """Slab intersection in rational arithmetic, open segment / closed box.

    Parallel means d == 0 exactly in the encoded model. No epsilon cutoff.
    Bounds may be zero for eroded uncertainty-set witnesses.
    """
    enter, leave = F(0), F(1)
    for aa, bb, h in zip(a, b, bounds):
        d = bb - aa
        if d == 0:
            if abs(aa) > h:
                return False
            continue
        t0, t1 = (-h - aa) / d, (h - aa) / d
        enter = max(enter, min(t0, t1))
        leave = min(leave, max(t0, t1))
        if enter > leave:
            return False
    return enter <= leave and leave > 0 and enter < 1


def _thin_hit(a, b, bounds):
    d = tuple(bb - aa for aa, bb in zip(a, b))
    if d[2] == 0:  # includes exactly coplanar: explicit ideal-plane convention
        return False
    t = -a[2] / d[2]
    return (0 < t < 1 and abs(a[0] + t*d[0]) <= bounds[0]
            and abs(a[1] + t*d[1]) <= bounds[1])


class RectangleMask:
    """Nominal half-spaces |(x-center) dot Q[:,j]| <= half_extent[j].

    orientation rows are laboratory coordinates, columns are local frame axes.
    Near-orthogonality is validated, not repaired. The represented coefficients
    define this reference model; an ideal unrounded frame can differ.
    local_margin_m encloses all local endpoint + boundary uncertainty. It is
    an external assumption, not an automatically estimated calibration bound.
    """
    def __init__(self, center_m, orientation, half_width_m,
                 half_height_m, thickness_m=0.0):
        self.center = _v3(center_m, 'center')
        if len(orientation) != 3 or any(len(row) != 3 for row in orientation):
            raise ValueError('orientation: shape (3,3) required')
        self.Q = tuple(tuple(_q(x, 'orientation', F(2)) for x in row)
                       for row in orientation)
        for j in range(3):
            for k in range(3):
                gram = sum(self.Q[i][j]*self.Q[i][k] for i in range(3))
                if abs(gram - int(j == k)) > FRAME_RESIDUAL:
                    raise ValueError('orientation: encoded Gram residual exceeds 1e-12')
        q = self.Q
        det = (q[0][0]*(q[1][1]*q[2][2]-q[1][2]*q[2][1])
               - q[0][1]*(q[1][0]*q[2][2]-q[1][2]*q[2][0])
               + q[0][2]*(q[1][0]*q[2][1]-q[1][1]*q[2][0]))
        if det <= 0:
            raise ValueError('orientation: proper frame required')
        w, h, t = (_q(v, 'size') for v in
                   (half_width_m, half_height_m, thickness_m))
        if w < MIN_SIZE or h < MIN_SIZE or t < 0 or (t and t < MIN_SIZE):
            raise ValueError('sizes outside admitted positive domain')
        self.bounds = w, h, t/F(2)
        self.thin = t == 0

    def _local(self, point):
        p = _v3(point, 'point')
        return tuple(sum((p[i]-self.center[i])*self.Q[i][j]
                         for i in range(3)) for j in range(3))

    def classify(self, source_xyz, target_xyz, *, local_margin_m=0.0):
        a, b = self._local(source_xyz), self._local(target_xyz)
        margin = _q(local_margin_m, 'local_margin_m')
        if margin < 0:
            raise ValueError('local_margin_m must be nonnegative')
        if margin == 0:
            hit = (_thin_hit if self.thin else _solid_hit)(a, b, self.bounds)
            return HitResult(Verdict.BLOCKED if hit else Verdict.CLEAR,
                             'nominal_encoded_geometry')
        expanded = tuple(x + margin for x in self.bounds)
        if not _solid_hit(a, b, expanded):
            return HitResult(Verdict.CLEAR, 'separated_from_expanded_geometry')
        if not self.thin:
            eroded = tuple(x - margin for x in self.bounds)
            if all(x >= 0 for x in eroded) and _solid_hit(a, b, eroded):
                return HitResult(Verdict.BLOCKED, 'eroded_geometry_witness')
        # A thin plate has no nonempty 3-D eroded volume. This conservative
        # reference does not attempt a stronger uncertain-plane crossing test.
        return HitResult(Verdict.UNKNOWN, 'uncertainty_tube_may_change_contact')

    def classify_many(self, pairs, *, local_margin_m=0.0):
        """Explicit bounded sequence, no broadcasting or lazy unbounded stream."""
        margin = _q(local_margin_m, 'local_margin_m')
        if margin < 0:
            raise ValueError('local_margin_m must be nonnegative even for an empty batch')
        if len(pairs) > MAX_BATCH:
            raise ValueError(f'batch limit is {MAX_BATCH}')
        return tuple(self.classify(a, b, local_margin_m=local_margin_m)
                     for a, b in pairs)


def combine_masks(results):
    """Opaque-union tri-state: one certain blocker dominates unknown masks."""
    values = tuple(results)
    if any(not isinstance(x, HitResult) for x in values):
        raise TypeError('HitResult values required')
    if any(x.verdict is Verdict.BLOCKED for x in values):
        return HitResult(Verdict.BLOCKED, 'opaque_union_has_certain_blocker')
    if any(x.verdict is Verdict.UNKNOWN for x in values):
        return HitResult(Verdict.UNKNOWN, 'opaque_union_has_unknown')
    return HitResult(Verdict.CLEAR, 'opaque_union_all_clear')


def _outward_float(q, lower):
    f = float(q)
    if not math.isfinite(f):
        raise OverflowError('aggregate outside finite binary64 output range')
    if lower and F(f) > q:
        f = math.nextafter(f, -math.inf)
    if not lower and F(f) < q:
        f = math.nextafter(f, math.inf)
    return f


def transmitted_sum_interval(nonnegative_contributions, results):
    """Enclosure of a finite discrete sum, with all weights already included.

    This bounds visibility ambiguity only. Kernel, source/time quadrature,
    calibration, and model-form error must be separately propagated.
    """
    if len(results) != len(nonnegative_contributions) or len(results) > MAX_BATCH:
        raise ValueError('matching bounded sequences required')
    lo = hi = F(0)
    for value, result in zip(nonnegative_contributions, results):
        q = _q(value, 'contribution')
        if q < 0 or not isinstance(result, HitResult):
            raise ValueError('nonnegative contributions and HitResult required')
        lower, upper = result.transmission_interval
        lo += q*lower
        hi += q*upper
    return _outward_float(lo, True), _outward_float(hi, False)
