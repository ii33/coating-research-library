"""Dyadic outward intervals, exact rational arithmetic, no libm certificate.
All input floats mean their exact binary encoding. 80-bit absolute dyadic mesh.
Pi: Machin identity with alternating arctan remainder. Trig: Taylor + Lagrange
remainder at a rational center, enlarged by radius using |sin'|,|cos'| <= 1.
"""
from fractions import Fraction as F
from dataclasses import dataclass
import math
BITS=80
GRID=1<<BITS

def f(x):
    if isinstance(x,bool):raise ValueError('boolean is not numeric')
    if isinstance(x,F):return x
    if isinstance(x,float) and not math.isfinite(x):raise ValueError('finite required')
    return F(x)
def down(x):return F((x*GRID).__floor__(),GRID)
def up(x):return F((x*GRID).__ceil__(),GRID)
@dataclass(frozen=True)
class I:
    lo:F
    hi:F
    def __init__(self,a,b=None):
        a=f(a);b=a if b is None else f(b)
        if a>b:raise ValueError('reversed interval')
        object.__setattr__(self,'lo',down(a));object.__setattr__(self,'hi',up(b))
    def __add__(self,b):
        b=iv(b);return I(self.lo+b.lo,self.hi+b.hi)
    __radd__=__add__
    def __neg__(self):return I(-self.hi,-self.lo)
    def __sub__(self,b):return self+-iv(b)
    def __rsub__(self,b):return iv(b)+-self
    def __mul__(self,b):
        b=iv(b);v=[a*c for a in (self.lo,self.hi) for c in (b.lo,b.hi)];return I(min(v),max(v))
    __rmul__=__mul__
    def __truediv__(self,b):
        b=iv(b)
        if b.lo<=0<=b.hi:raise ZeroDivisionError('interval_denominator_contains_zero')
        return self*I(1/b.hi,1/b.lo)
    def __rtruediv__(self,b):return iv(b)/self
    def sq(self):return I(0 if self.lo<=0<=self.hi else min(self.lo**2,self.hi**2),max(self.lo**2,self.hi**2))
    def intersect(self,a,b):
        lo=max(self.lo,f(a));hi=min(self.hi,f(b))
        if lo>hi:raise ArithmeticError('inconsistent_physical_intersection')
        return I(lo,hi)
    def floats(self):
        a=float(self.lo);b=float(self.hi)
        if F(a)>self.lo:a=math.nextafter(a,-math.inf)
        if F(b)<self.hi:b=math.nextafter(b,math.inf)
        return [a,b]
    def exact(self):return [str(self.lo),str(self.hi)]
def iv(x):return x if isinstance(x,I) else I(x)
def hull(a,b):return I(min(a.lo,b.lo),max(a.hi,b.hi))
def atan_inv(q,n=28):
    s=sum((F((-1)**k,(2*k+1)*q**(2*k+1)) for k in range(n)),F(0))
    nxt=F((-1)**n,(2*n+1)*q**(2*n+1));return I(min(s,s+nxt),max(s,s+nxt))
PI=16*atan_inv(5)-4*atan_inv(239)
def trig(a,cosine=False):
    a=iv(a)
    if a.hi-a.lo>=2*PI.lo:return I(-1,1)
    k=round(((a.lo+a.hi)/2)/((PI.lo+PI.hi)))
    a=a-2*k*PI;c=(a.lo+a.hi)/2;r=(a.hi-a.lo)/2
    if abs(c)>4:raise ArithmeticError('range_reduction_failed')
    n=20
    if cosine:
        s=sum(((-1)**j*c**(2*j)/math.factorial(2*j) for j in range(n)),F(0))
        rem=abs(c)**(2*n)/math.factorial(2*n)
    else:
        s=sum(((-1)**j*c**(2*j+1)/math.factorial(2*j+1) for j in range(n)),F(0))
        rem=abs(c)**(2*n+1)/math.factorial(2*n+1)
    return I(s-rem-r,s+rem+r).intersect(-1,1)
@dataclass(frozen=True)
class C:
    re:I
    im:I
    def __init__(self,re=0,im=0):object.__setattr__(self,'re',iv(re));object.__setattr__(self,'im',iv(im))
    def __add__(self,b):
        b=cv(b);return C(self.re+b.re,self.im+b.im)
    __radd__=__add__
    def __mul__(self,b):
        b=cv(b);return C(self.re*b.re-self.im*b.im,self.re*b.im+self.im*b.re)
    __rmul__=__mul__
    def __truediv__(self,b):
        b=cv(b);den=b.re.sq()+b.im.sq()
        return C((self.re*b.re+self.im*b.im)/den,(self.im*b.re-self.re*b.im)/den)
    def abs2(self):return self.re.sq()+self.im.sq()
def cv(x):return x if isinstance(x,C) else C(x)
def phase(a):return C(trig(a,True),trig(a))
