"""Finite, binary, two-plate design space; no relaxed gray cell is fabricated."""
from dataclasses import dataclass, asdict, replace
from hashlib import sha256
import json, math
from frozen.robust_mask_v02 import RectangleMask


def canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(value): return sha256(canonical(value).encode()).hexdigest()


@dataclass(frozen=True)
class Plate:
    name: str
    bits: tuple[int, ...]
    nx: int
    ny: int
    pitch_m: float
    center_m: tuple[float,float,float]
    thickness_m: float
    # This version admits horizontal, laboratory-fixed frames only.
    def __post_init__(self):
        object.__setattr__(self,'bits',tuple(self.bits));object.__setattr__(self,'center_m',tuple(self.center_m))
        if type(self.nx) is not int or type(self.ny) is not int or min(self.nx,self.ny)<1: raise ValueError('positive integer grid dimensions required')
        if len(self.bits)!=self.nx*self.ny or any(type(b) is not int or b not in (0,1) for b in self.bits): raise ValueError('binary cells required')
        if len(self.center_m)!=3 or not all(math.isfinite(v) for v in (*self.center_m,self.pitch_m,self.thickness_m)) or min(self.pitch_m,self.thickness_m)<=0: raise ValueError('finite positive dimensions required')
    def boxes(self):
        for i,b in enumerate(self.bits):
            if b:
                x,y=divmod(i,self.ny)
                c=(self.center_m[0]+(x-(self.nx-1)/2)*self.pitch_m,self.center_m[1]+(y-(self.ny-1)/2)*self.pitch_m,self.center_m[2])
                yield RectangleMask(c,((1,0,0),(0,1,0),(0,0,1)),self.pitch_m/2,self.pitch_m/2,self.thickness_m)
    def envelope(self):
        half=(self.nx*self.pitch_m/2,self.ny*self.pitch_m/2,self.thickness_m/2)
        return tuple((c-h,c+h) for c,h in zip(self.center_m,half))


@dataclass(frozen=True)
class Design:
    plates: tuple[Plate,...]
    def __post_init__(self): object.__setattr__(self,'plates',tuple(self.plates))
    @property
    def id(self): return digest(self.to_dict())[:20]
    def to_dict(self): return {'plates':[asdict(p) for p in self.plates]}
    @classmethod
    def from_dict(cls,d):
        return cls(tuple(Plate(**{**p,'bits':tuple(p['bits']),'center_m':tuple(p['center_m'])}) for p in d['plates']))


@dataclass(frozen=True)
class Manufacturing:
    min_feature_m: float=.01
    min_thickness_m: float=.001
    max_thickness_m: float=.01
    workspace_m: tuple=((-1.,1.),(-1.,1.),(.01,.99))
    clearance_m: float=.005
    max_boundary_m: float=10.
    max_material_fraction: float=1.
    mount_edge: str='xmin'
    allow_absent_plate: bool=True

    def __post_init__(self):
        object.__setattr__(self,'workspace_m',tuple(tuple(b) for b in self.workspace_m))
        vals=(self.min_feature_m,self.min_thickness_m,self.max_thickness_m,self.clearance_m,self.max_boundary_m,self.max_material_fraction)
        if not all(math.isfinite(x) for x in vals) or self.min_feature_m<=0 or not 0<self.min_thickness_m<=self.max_thickness_m or self.clearance_m<0 or self.max_boundary_m<=0 or not 0<self.max_material_fraction<=1: raise ValueError('invalid fabrication contract')
        if self.mount_edge!='xmin': raise ValueError('only xmin support edge implemented')
        if len(self.workspace_m)!=3 or any(len(b)!=2 or not all(math.isfinite(v) for v in b) or b[0]>=b[1] for b in self.workspace_m): raise ValueError('invalid workspace')

    def check(self, design):
        errors=[]
        if len(design.plates)!=2 or len(set(p.name for p in design.plates))!=2: errors.append('exactly_two_named_plate_slots_required')
        active=[]
        for p in design.plates:
            tag=p.name+':'
            if p.pitch_m<self.min_feature_m: errors.append(tag+'minimum_feature')
            if not self.min_thickness_m<=p.thickness_m<=self.max_thickness_m: errors.append(tag+'thickness')
            if any(a<wa or b>wb for (a,b),(wa,wb) in zip(p.envelope(),self.workspace_m)): errors.append(tag+'workspace')
            solid={i for i,b in enumerate(p.bits) if b}
            if not solid:
                if not self.allow_absent_plate: errors.append(tag+'absent_plate')
                continue
            active.append(p)
            if len(solid)/len(p.bits)>self.max_material_fraction: errors.append(tag+'material_fraction')
            roots={i for i in solid if i//p.ny==0}
            visited=set(roots); frontier=list(roots)
            perimeter=0
            for i in solid:
                x,y=divmod(i,p.ny)
                perimeter+=sum(not (0<=a<p.nx and 0<=b<p.ny and a*p.ny+b in solid) for a,b in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)])
            while frontier:
                i=frontier.pop();x,y=divmod(i,p.ny)
                for a,b in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                    k=a*p.ny+b
                    if 0<=a<p.nx and 0<=b<p.ny and k in solid and k not in visited: visited.add(k);frontier.append(k)
            if visited!=solid: errors.append(tag+'unsupported_or_disconnected_material')
            if perimeter*p.pitch_m>self.max_boundary_m: errors.append(tag+'boundary_length')
        # Sufficient separation of full plate envelopes is deliberately conservative.
        for i,p in enumerate(active):
            for q in active[i+1:]:
                sep=any(b+self.clearance_m<=c or d+self.clearance_m<=a for (a,b),(c,d) in zip(p.envelope(),q.envelope()))
                if not sep: errors.append('two_plate_envelope_conflict')
        return errors


def neighborhood(design, thickness_levels, translation_steps, max_candidates=1000):
    """Deterministic finite binary/position/thickness proposals, bounded before evaluation."""
    if type(max_candidates) is not int or max_candidates<1: raise ValueError('positive proposal cap')
    seen={design.id}; yield design;count=1
    for index,p in enumerate(design.plates):
        variants=[]
        for k in range(len(p.bits)):
            bits=list(p.bits);bits[k]=1-bits[k];variants.append(replace(p,bits=tuple(bits)))
        variants.extend(replace(p,thickness_m=t) for t in thickness_levels)
        for axis,delta in translation_steps:
            if axis not in (0,1,2) or not math.isfinite(delta): raise ValueError('invalid translation step')
            c=list(p.center_m);c[axis]+=delta;variants.append(replace(p,center_m=tuple(c)))
        for variant in variants:
            plates=list(design.plates);plates[index]=variant;v=Design(tuple(plates))
            if v.id in seen: continue
            if count>=max_candidates: return
            seen.add(v.id);count+=1;yield v


def discrete_space(seed, position_catalogs, thickness_catalogs, max_candidates=1000):
    """Lazy full binary/catalog parameter enumeration, stopped at a caller cap.

    The cap is a search budget, not a completeness certificate. Catalogs bound
    the admitted placements/thicknesses; manufacturing is checked by Search.
    With an uncropped catalog product, exhaustive interval filtering is possible.
    """
    from itertools import product
    if len(seed.plates)!=2 or len(position_catalogs)!=2 or len(thickness_catalogs)!=2 or type(max_candidates) is not int or max_candidates<1: raise ValueError('two plate catalogs and a positive cap required')
    if any(not x for x in position_catalogs+thickness_catalogs): raise ValueError('nonempty catalogs required')
    # Build only individual plate alternatives. Avoid allocating the full pair
    # product; candidates are yielded lazily until the explicit finite cap.
    def variants(p,positions,thicknesses):
        for bits in product((0,1),repeat=len(p.bits)):
            for center in positions:
                for thick in thicknesses: yield replace(p,bits=tuple(bits),center_m=tuple(center),thickness_m=thick)
    count=0
    for a in variants(seed.plates[0],position_catalogs[0],thickness_catalogs[0]):
        for b in variants(seed.plates[1],position_catalogs[1],thickness_catalogs[1]):
            if count>=max_candidates: return
            count+=1;yield Design((a,b))
