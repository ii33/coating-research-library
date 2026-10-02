"""Serializable scientific contracts. Unknowns carry axes and locations."""
from dataclasses import dataclass, asdict
import math,json
from intervals import Interval
from geometry import digest

ERROR_AXES=('source','time','space','geometry','kernel','input','model')

@dataclass(frozen=True)
class ErrorSource:
    axis: str
    status: str                  # bounded_conditional / estimated / unknown
    absolute_radius: float | None
    field: str
    points: tuple[int,...]=()
    time_window_s: tuple[float,float] | None=None
    evidence: str=''
    def __post_init__(self):
        object.__setattr__(self,'points',tuple(self.points))
        if self.time_window_s is not None: object.__setattr__(self,'time_window_s',tuple(self.time_window_s))
        if self.axis not in ERROR_AXES or self.status not in ('bounded_conditional','estimated','unknown'): raise ValueError('invalid error state')
        if any(type(p) is not int or p<0 for p in self.points): raise ValueError('nonnegative integer point IDs required')
        if self.time_window_s is not None and (len(self.time_window_s)!=2 or not all(math.isfinite(t) for t in self.time_window_s) or self.time_window_s[0]>=self.time_window_s[1]): raise ValueError('valid local time window required')
        if self.status=='unknown' and self.absolute_radius is not None: raise ValueError('unknown cannot assert radius')
        if self.status!='unknown' and (self.absolute_radius is None or not math.isfinite(self.absolute_radius) or self.absolute_radius<0): raise ValueError('invalid error radius')


def measure(interval, unit, status='bounded_conditional', errors=(), definition=''):
    if status not in ('bounded_conditional','estimated','unknown'): raise ValueError('bad measure status')
    if not interval.known: status='unknown'
    return {**interval.to_dict(),'unit':unit,'status':status,'errors':[asdict(x) if isinstance(x,ErrorSource) else x for x in errors],'definition':definition}


def field_status(errors):
    if any(e.status=='unknown' for e in errors): return 'unknown'
    return 'estimated' if any(e.status=='estimated' for e in errors) else 'bounded_conditional'


def apply_errors(interval, errors):
    out=interval
    for e in errors: out=out.widen(e.absolute_radius,nonnegative=True)
    return out


def value(d): return Interval.from_dict(d)


def validate_evaluation(result):
    required={'candidate_id','fidelity','provenance','objectives','constraints','point_fields','error_sources','work','status','physical_certification'}
    if not required.issubset(result): raise ValueError('incomplete evaluation contract')
    if not isinstance(result['objectives'],dict) or not result['objectives']: raise ValueError('at least one decision objective required')
    if not isinstance(result['constraints'],dict): raise ValueError('constraints must be a dictionary; empty means explicitly unconstrained')
    if result['physical_certification'] is not False: raise ValueError('research contract cannot certify physical performance')
    if result['status'] not in ('bounded_conditional','estimated','partial'): raise ValueError('invalid evaluation status')
    related=[]
    for group in ('objectives','constraints'):
        for name,m in result[group].items():
            value(m);related.append(m['status'])
            statuses=[e['status'] for e in m.get('errors',[])]
            if m['status']=='bounded_conditional' and any(v!='bounded_conditional' for v in statuses): raise ValueError('measure contradicts its error qualification')
            if m['status'] not in ('bounded_conditional','estimated','unknown'): raise ValueError('invalid status')
            if m['status']=='bounded_conditional' and not value(m).known: raise ValueError('unknown endpoints cannot certify')
    if result['status']=='bounded_conditional' and any(v!='bounded_conditional' for v in related): raise ValueError('aggregate status contradicts decision metrics')
    # A partial aggregate can describe an optional unknown tau. Comparisons
    # qualify exactly the selected decision fields, not unrelated observables.
    return json.loads(json.dumps(result,allow_nan=False))


def refinement_requests(a,b=None):
    """Scientific diagnostic requests only; never silently increase workload."""
    out=[];seen=set()
    for r in (a,b):
        if r is None: continue
        for e in r['error_sources']:
            if e['status']=='bounded_conditional' and e['absolute_radius']==0: continue
            req={'candidate_id':r['candidate_id'],'from_fidelity':r['fidelity'],'axis':e['axis'],'field':e['field'],'point_ids':e['points'],'time_window_s':e['time_window_s'],
                 'action':{'source':'change_source_family_and_increase_local_source_order','time':'split_event_or_rate_panels_and_change_phase','space':'add_area_and_separate_edge_witnesses','geometry':'tighten_input_margin_or_exact_predicate','kernel':'validate_kernel_rounding_enclosure','input':'obtain_calibrated_input_bounds','model':'obtain_missing_physics_or_restrict_claim'}[e['axis']],
                 'automatic_refinement_allowed':e['axis'] in ('source','time','space'), 'reason':e['evidence']}
            key=digest(req)
            if key not in seen: seen.add(key);out.append(req)
    if not out:
        out=[{'candidate_id':a['candidate_id'],'axis':'objective_overlap','action':'supply_tighter_validated_bounds_or_report_equivalence','automatic_refinement_allowed':False,'point_ids':[],'time_window_s':None}]
    return out
