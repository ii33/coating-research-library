"""Two independent channel visibility sums and explicit synthetic test oracles.

The ray oracle encloses the supplied finite nonnegative quadrature contributions.
Its kernel/quadrature/model qualifications are caller supplied and fail closed.
It is not the unfinished T02 continuous oracle or an automatic production adapter.
"""
from dataclasses import dataclass, asdict
from pathlib import Path
from hashlib import sha256
import math, json, threading
from copy import deepcopy
from collections import OrderedDict
from intervals import Interval, sum_intervals, maximum
from geometry import digest, canonical
from contracts import ErrorSource, measure, apply_errors, field_status, validate_evaluation
from frozen.robust_mask_v02 import combine_masks, Verdict, transmitted_sum_interval


def code_hash():
    root=Path(__file__).resolve().parent
    return digest({str(p.relative_to(root)):sha256(p.read_bytes()).hexdigest() for p in sorted(list(root.glob('*.py'))+list((root/'frozen').glob('*.py')))})


@dataclass(frozen=True)
class Ray:
    channel: str
    point: int
    time: int
    source: tuple[float,float,float]
    target: tuple[float,float,float]
    contribution: float            # atom/m2 or ion/m2, including time/source weights
    def __post_init__(self):
        object.__setattr__(self,'source',tuple(self.source));object.__setattr__(self,'target',tuple(self.target))
        if self.channel not in ('vapor','ion') or type(self.point) is not int or type(self.time) is not int or min(self.point,self.time)<0: raise ValueError('invalid ray index')
        if len(self.source)!=3 or len(self.target)!=3 or not all(math.isfinite(x) for x in (*self.source,*self.target,self.contribution)) or self.contribution<0: raise ValueError('finite nonnegative ray required')


@dataclass(frozen=True)
class RayBundle:
    rays: tuple[Ray,...]
    area_weights: tuple[float,...]  # zero weights are diagnostic witnesses only
    time_weights_s: tuple[float,...]
    atomic_density_m3: float
    energy_per_ion_eV: float
    baseline_mean_h_m: float
    provenance: dict
    errors: tuple[ErrorSource,...]
    finite_fixture: bool=False
    margin_m: float=0.
    def __post_init__(self):
        for name in ('rays','area_weights','time_weights_s','errors'): object.__setattr__(self,name,tuple(getattr(self,name)))
        object.__setattr__(self,'provenance',deepcopy(self.provenance))
        if not self.area_weights or not self.time_weights_s or not self.rays: raise ValueError('nonempty bundle required')
        if not all(math.isfinite(x) and x>=0 for x in self.area_weights) or sum(self.area_weights)<=0: raise ValueError('valid positive area required')
        if not all(math.isfinite(x) and x>0 for x in self.time_weights_s): raise ValueError('positive time weights required')
        if not all(math.isfinite(x) and x>0 for x in (self.atomic_density_m3,self.baseline_mean_h_m)) or not math.isfinite(self.energy_per_ion_eV) or self.energy_per_ion_eV<0 or not math.isfinite(self.margin_m) or self.margin_m<0: raise ValueError('invalid physical constants')
        if any(r.point>=len(self.area_weights) or r.time>=len(self.time_weights_s) for r in self.rays): raise ValueError('ray index out of bounds')
        # Each channel/point/time group must be represented, even if gated off.
        required={(ch,p,t) for ch in ('vapor','ion') for p in range(len(self.area_weights)) for t in range(len(self.time_weights_s))}
        if {(r.channel,r.point,r.time) for r in self.rays}!=required: raise ValueError('missing channel/point/time group')
        if any(any(p>=len(self.area_weights) for p in e.points) for e in self.errors): raise ValueError('error source point index out of bounds')
        if not self.finite_fixture:
            for f in ('N','D'):
                for p in range(len(self.area_weights)):
                    axes={e.axis for e in self.errors if e.field==f and (not e.points or p in e.points)}
                    if axes!=set(('source','time','space','geometry','kernel','input','model')): raise ValueError('physical bundle requires all seven error axes per N/D point')
        if any(e.field not in ('N','D','tau') for e in self.errors): raise ValueError('errors must address N, D, or tau')
        if not self.provenance: raise ValueError('provenance required')


class VisibilityCache:
    """Pure geometric outcomes only; rates, species and weights never enter this key.
    In-memory locking permits the bounded local thread backend. No global disk cache.
    """
    def __init__(self,max_entries=16):
        if type(max_entries) is not int or max_entries<1: raise ValueError('positive cache capacity')
        self.items=OrderedDict();self.lock=threading.RLock();self.hits=0;self.max_entries=max_entries
    def get(self,key):
        with self.lock:
            v=self.items.get(key)
            if v is not None: self.hits+=1;self.items.move_to_end(key)
            return v
    def put(self,key,value):
        with self.lock:
            self.items[key]=value;self.items.move_to_end(key)
            while len(self.items)>self.max_entries: self.items.popitem(last=False)


class RayOracle:
    def __init__(self,bundle,target_h_m,target_D_m2=None,target_epsilon_eV=None,min_throughput=.5,max_ion_only_s=None,cache=None,ion_allowed_interval=None,max_h_relative_deviation=None):
        if target_h_m<=0 or not math.isfinite(target_h_m) or (target_D_m2 is None)==(target_epsilon_eV is None): raise ValueError('positive h and exactly one ion target required')
        target=target_D_m2 if target_D_m2 is not None else target_epsilon_eV
        if not math.isfinite(target) or target<=0 or not 0<=min_throughput<=1: raise ValueError('invalid targets')
        if max_ion_only_s is not None and (not math.isfinite(max_ion_only_s) or max_ion_only_s<0): raise ValueError('invalid duration constraint')
        if ion_allowed_interval is not None:
            ion_allowed_interval=tuple(ion_allowed_interval)
            if len(ion_allowed_interval)!=2 or not all(math.isfinite(v) for v in ion_allowed_interval) or not 0<=ion_allowed_interval[0]<ion_allowed_interval[1]: raise ValueError('ordered nonnegative ion interval required')
        if max_h_relative_deviation is not None and (not math.isfinite(max_h_relative_deviation) or max_h_relative_deviation<0): raise ValueError('nonnegative h deviation limit required')
        self.ion_allowed_interval=ion_allowed_interval;self.max_h_relative_deviation=max_h_relative_deviation
        self.bundle=deepcopy(bundle);self.bundle_digest=digest(asdict(self.bundle));self.target_h=target_h_m;self.target_D=target_D_m2;self.target_eps=target_epsilon_eV;self.min_throughput=min_throughput;self.max_tau=max_ion_only_s
        self.cache=cache or VisibilityCache();self.version=code_hash()
        self.signature=digest({'bundle':asdict(bundle),'targets':[target_h_m,target_D_m2,target_epsilon_eV,min_throughput,max_ion_only_s,ion_allowed_interval,max_h_relative_deviation],'code':self.version})
    def estimate(self,design,fidelity=0):
        if fidelity!=0: raise ValueError('ray refinements require a new validated bundle/job; not generated silently')
        b=self.bundle;n=len(b.rays)
        return {'evaluations':1,'rays':n,'source_samples':n,'point_time_samples':len(b.area_weights)*len(b.time_weights_s),'time_panels':len(b.time_weights_s),'plate_tests':n*sum(sum(p.bits) for p in design.plates)}
    def evaluate(self,design,fidelity=0,cancel=lambda:False):
        if digest(asdict(self.bundle))!=self.bundle_digest: raise ValueError('oracle bundle mutated after signature freeze')
        estimate=self.estimate(design,fidelity);b=self.bundle
        geometry_key=digest({'plates':design.to_dict(),'rays':[(r.source,r.target) for r in b.rays],'margin_m':b.margin_m,'predicate_code':sha256((Path(__file__).parent/'frozen/robust_mask_v02.py').read_bytes()).hexdigest()})
        weighted_key=digest({'geometry_key':geometry_key,'bundle':asdict(b),'oracle_signature':self.signature,'fidelity':fidelity})
        visibility=self.cache.get(geometry_key);hit=visibility is not None
        if visibility is None:
            boxes=[box for p in design.plates for box in p.boxes()];visibility=[]
            for r in b.rays:
                if cancel(): raise InterruptedError('cancelled between bounded rays')
                visibility.append(combine_masks(box.classify(r.source,r.target,local_margin_m=b.margin_m) for box in boxes))
            visibility=tuple(visibility);self.cache.put(geometry_key,visibility)
        groups={}
        for index,(r,v) in enumerate(zip(b.rays,visibility)):
            if index%1024==0 and cancel(): raise InterruptedError('cancelled between aggregation chunks')
            groups.setdefault((r.channel,r.point,r.time),[]).append((r.contribution,v))
        per_time={}
        for key,values in groups.items():
            if cancel(): raise InterruptedError('cancelled between source sums')
            per_time[key]=Interval(*transmitted_sum_interval([x for x,v in values],[v for x,v in values]))
        points=[];flat_errors=[asdict(e) for e in b.errors]
        # Visibility ambiguity is already in the interval sum, not added twice.
        # Keep its location as a refinement source even for finite fixtures.
        for (ch,pt,ti),ivalue in per_time.items():
            if ivalue.width and any(v.verdict is Verdict.UNKNOWN and w>0 for w,v in groups[ch,pt,ti]):
                flat_errors.append(asdict(ErrorSource('geometry','bounded_conditional',ivalue.width,'N' if ch=='vapor' else 'D',(pt,),evidence=f'tri-state visibility at time_index={ti}; interval already propagated; tighten local_margin_m with evidence')))
        for p in range(len(b.area_weights)):
            raw={f:sum_intervals(per_time[ch,p,t] for t in range(len(b.time_weights_s))) for ch,f in [('vapor','N'),('ion','D')]}
            errors={f:[e for e in b.errors if e.field==f and (not e.points or p in e.points)] for f in ('N','D','tau')}
            N,D=(apply_errors(raw[f],errors[f]) for f in ('N','D'));h=N.divide(Interval.point(b.atomic_density_m3));U=D.scale(b.energy_per_ion_eV).scale(1.602176634e-19)
            ratio=D.divide(N) if N.known and N.lo>0 else Interval.unknown();eps=ratio.scale(b.energy_per_ion_eV)
            tau=Interval.point(0)
            for t,dt in enumerate(b.time_weights_s):
                n,i=per_time['vapor',p,t],per_time['ion',p,t]
                # Indicator 1 iff I>0 and N=0; no arbitrary small-flux threshold.
                lo=1. if i.lo>0 and n.hi==0 else 0.
                hi=0. if i.hi==0 or n.lo>0 else 1.
                tau=tau+Interval(lo,hi).scale(dt)
            unresolved_event_effect=any(e.status!='bounded_conditional' or e.absolute_radius!=0 for e in errors['N']+errors['D'])
            if (not b.finite_fixture or unresolved_event_effect) and not errors['tau']:
                tau=Interval.unknown()
                terr=[ErrorSource('time','unknown',None,'tau',(p,),evidence='continuous support/rate or integrated-error event effects not certified by sampled rays')]
            else: terr=errors['tau'];tau=apply_errors(tau,terr)
            def m(v,unit,ee): return measure(v,unit,field_status(ee),ee)
            point={'point_id':p,'area_weight':b.area_weights[p], 'N_net':m(N,'atom/m2',errors['N']),'h':m(h,'m',errors['N']),'D':m(D,'ion/m2',errors['D']),'U':m(U,'J/m2',errors['D']), 'R':m(ratio,'ion/atom',errors['N']+errors['D']),'epsilon':m(eps,'eV/atom',errors['N']+errors['D']),'tau':m(tau,'s',terr)}
            poor_denominator=N.known and N.lo>0 and N.width>=N.lo
            point['ratio_conditioning']='ill_conditioned' if poor_denominator else 'bounded_positive' if N.known and N.lo>0 else 'undefined_or_unbounded_denominator'
            if poor_denominator:
                # Keep mathematical bounds for diagnosis but deny an optimization
                # reward from a denominator uncertain on its own positive scale.
                point['R']['status']=point['epsilon']['status']='unknown'
            points.append(point)
            flat_errors.extend(asdict(e) for e in terr if e not in b.errors)
        def iv(p,k): return Interval.from_dict(p[k])
        def stat(keys):
            statuses=[p[k]['status'] for p in points for k in keys]
            return 'unknown' if 'unknown' in statuses else 'estimated' if 'estimated' in statuses else 'bounded_conditional'
        mean_h=sum_intervals(iv(p,'h').scale(p['area_weight']) for p in points if p['area_weight']>0).divide(sum_intervals(Interval.point(w) for w in b.area_weights))
        throughput=mean_h.divide(Interval.point(b.baseline_mean_h_m))
        hdev=maximum(iv(p,'h').deviation(self.target_h).divide(Interval.point(self.target_h)) for p in points)
        key,target=('D',self.target_D) if self.target_D is not None else ('epsilon',self.target_eps)
        idev=maximum(iv(p,key).deviation(target).divide(Interval.point(target)) for p in points)
        objectives={'h_target_max_deviation':measure(hdev,'1',stat(['h']),definition='sample/witness max |h-target|/target; not continuous extreme'), 'ion_target_max_deviation':measure(idev,'1',stat([key]),definition=f'sample/witness max |{key}-target|/target')}
        # All constraints use g<=0. Area witnesses do not change the mean.
        constraints={'throughput':measure(throughput.scale(-1)+Interval.point(self.min_throughput),'1',stat(['h']))}
        if self.ion_allowed_interval is not None:
            low,high=self.ion_allowed_interval
            constraints['ion_lower']=measure(maximum(iv(p,key).scale(-1)+Interval.point(low) for p in points),points[0][key]['unit'],stat([key]))
            constraints['ion_upper']=measure(maximum(iv(p,key)+Interval.point(-high) for p in points),points[0][key]['unit'],stat([key]))
        if self.max_h_relative_deviation is not None:
            constraints['h_target_deviation']=measure(hdev+Interval.point(-self.max_h_relative_deviation),'1',stat(['h']))
        if self.max_tau is not None: constraints['ion_only_duration']=measure(maximum(iv(p,'tau') for p in points)+Interval.point(-self.max_tau),'s',stat(['tau']))
        allmeasures=list(objectives.values())+list(constraints.values())
        status='partial' if any(m['status']=='unknown' for m in allmeasures) or any(p['tau']['status']=='unknown' for p in points) else 'estimated' if any(m['status']=='estimated' for m in allmeasures) else 'bounded_conditional'
        result={'candidate_id':design.id,'fidelity':fidelity,'provenance':{**b.provenance,'oracle_signature':self.signature,'code_sha256':self.version,'geometry_cache_key':geometry_key,'weighted_data_key':weighted_key,'finite_discrete_fixture':b.finite_fixture,'continuous_or_physical_certificate':False},'objectives':objectives,'constraints':constraints,'point_fields':points,'error_sources':flat_errors,'work':{**estimate,'geometry_cache_hit':hit,'actual_predicate_rays':0 if hit else len(b.rays)},'status':status,'physical_certification':False,
                'area_statistics':{'mean_h_m':measure(mean_h,'m',stat(['h'])),'throughput_ratio':measure(throughput,'1',stat(['h'])),'ratio_valid_area_fraction':sum(p['area_weight'] for p in points if iv(p,'R').known)/sum(b.area_weights),'undefined_ratio_point_ids':[p['point_id'] for p in points if not iv(p,'R').known]}}
        return validate_evaluation(result)


class SyntheticOracle:
    """Reviewable deterministic fixtures; never evidence of coating optimization quality."""
    def __init__(self,values,radius=.0,unknown_ids=(),estimated=False):
        self.values=deepcopy(values);self.values_digest=digest(self.values);self.radius=radius;self.unknown=set(unknown_ids);self.estimated=estimated
        if not math.isfinite(radius) or radius<0: raise ValueError('invalid fixture radius')
        self.signature=digest({'kind':'synthetic_fixture_v1','code_sha256':code_hash(),'values':values,'radius':radius,'unknown':sorted(unknown_ids),'estimated':estimated})
    def estimate(self,design,fidelity=0): return {'evaluations':1,'rays':4*(2**fidelity),'source_samples':2*(2**fidelity),'point_time_samples':2,'time_panels':1,'plate_tests':0}
    def evaluate(self,design,fidelity=0,cancel=lambda:False):
        if cancel(): raise InterruptedError('fixture cancelled')
        if digest(self.values)!=self.values_digest: raise ValueError('fixture data mutated after signature freeze')
        h,i,g=self.values[design.id];status='unknown' if design.id in self.unknown else 'estimated' if self.estimated else 'bounded_conditional'
        radius=self.radius/(2**fidelity)
        err=ErrorSource('source',status,None if status=='unknown' else radius,'N',(0,),evidence='analytic fixture interval, not measured process noise')
        def m(v): return measure(Interval.unknown() if status=='unknown' else Interval.point(v).widen(radius),'1',status,[err])
        return validate_evaluation({'candidate_id':design.id,'fidelity':fidelity,'provenance':{'oracle_signature':self.signature,'fixture_only':True},'objectives':{'h_target_max_deviation':m(h),'ion_target_max_deviation':m(i)},'constraints':{'throughput':m(g)},'point_fields':[],'error_sources':[asdict(err)],'work':self.estimate(design,fidelity),'status':'partial' if status=='unknown' else status,'physical_certification':False})


def static_point_fixture():
    """Small genuine ray/visibility calculation, 2 channels x 2 points x 2 times.
    Analytic point emitters, stationary receivers, constant rates. No T02 reference claim.
    """
    rays=[];points=[(-.02,0,1.),(.02,0,1.)]
    for ch,source,total in [('vapor',(-.06,0,0),1e17),('ion',(.06,0,0),2e16)]:
        for p,target in enumerate(points):
            d=tuple(b-a for a,b in zip(source,target));r2=sum(v*v for v in d);cos=d[2]/math.sqrt(r2)
            for t in range(2): rays.append(Ray(ch,p,t,source,target,total*cos*cos/(math.pi*r2)*.5))
    baseline=sum(r.contribution for r in rays if r.channel=='vapor')/2/1e28
    return RayBundle(tuple(rays),(.5,.5),(.5,.5),1e28,100.,baseline,{'origin':'original analytic static fixture','units':'SI','clock':'two exact constant half-second panels'},(),True)
