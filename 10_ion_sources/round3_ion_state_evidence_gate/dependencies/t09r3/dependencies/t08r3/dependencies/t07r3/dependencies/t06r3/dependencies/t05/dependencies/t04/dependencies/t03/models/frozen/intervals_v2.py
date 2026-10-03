"""Outward-rounded bounded arithmetic. Bounds are conditional, never confidence intervals."""
from dataclasses import dataclass
from fractions import Fraction
import math


def rounded(q, lower):
    f = float(q)
    if not math.isfinite(f):
        raise OverflowError('finite interval arithmetic overflow')
    if lower and Fraction(f) > q:
        f = math.nextafter(f, -math.inf)
    if not lower and Fraction(f) < q:
        f = math.nextafter(f, math.inf)
    return f


@dataclass(frozen=True)
class Interval:
    lo: float | None
    hi: float | None

    def __post_init__(self):
        if (self.lo is None) != (self.hi is None):
            raise ValueError('unknown interval requires two null endpoints')
        if self.lo is not None and (not math.isfinite(self.lo) or not math.isfinite(self.hi) or self.lo > self.hi):
            raise ValueError('ordered finite interval required')

    @classmethod
    def point(cls, v): return cls(float(v), float(v))
    @classmethod
    def unknown(cls): return cls(None, None)
    @property
    def known(self): return self.lo is not None
    @property
    def width(self): return self.hi-self.lo if self.known else None
    def to_dict(self): return {'lo': self.lo, 'hi': self.hi}
    @classmethod
    def from_dict(cls, d): return cls(d['lo'], d['hi'])

    def __add__(self, other):
        if not self.known or not other.known: return Interval.unknown()
        return Interval(rounded(Fraction(self.lo)+Fraction(other.lo), True), rounded(Fraction(self.hi)+Fraction(other.hi), False))

    def scale(self, s):
        if not math.isfinite(s): raise ValueError('finite scale required')
        if not self.known: return Interval.unknown()
        a, b = Fraction(self.lo)*Fraction(s), Fraction(self.hi)*Fraction(s)
        return Interval(rounded(min(a,b), True), rounded(max(a,b), False))

    def divide(self, other):
        if not self.known or not other.known or other.lo <= 0 <= other.hi: return Interval.unknown()
        v = [Fraction(x)/Fraction(y) for x in (self.lo,self.hi) for y in (other.lo,other.hi)]
        return Interval(rounded(min(v),True), rounded(max(v),False))

    def deviation(self, target):
        if not math.isfinite(target): raise ValueError('finite target required')
        if not self.known: return Interval.unknown()
        a,b=Fraction(self.lo)-Fraction(target),Fraction(self.hi)-Fraction(target)
        lo=Fraction(0) if a<=0<=b else min(abs(a),abs(b))
        return Interval(rounded(lo,True),rounded(max(abs(a),abs(b)),False))

    def widen(self, radius, nonnegative=False):
        if radius is None or not self.known: return Interval.unknown()
        if not math.isfinite(radius) or radius<0: raise ValueError('nonnegative finite radius required')
        lo=rounded(Fraction(self.lo)-Fraction(radius),True)
        hi=rounded(Fraction(self.hi)+Fraction(radius),False)
        return Interval(max(0.,lo) if nonnegative else lo,hi)


def sum_intervals(values):
    out=Interval.point(0)
    for v in values: out=out+v
    return out


def maximum(values):
    values=list(values)
    if not values or any(not v.known for v in values): return Interval.unknown()
    return Interval(max(v.lo for v in values),max(v.hi for v in values))
