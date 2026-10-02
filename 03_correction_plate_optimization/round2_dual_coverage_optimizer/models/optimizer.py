"""Deterministic finite candidate search with certified interval comparisons.

No global optimum claim. Surrogates order proposals; only qualified oracle bounds
may reject/accept scientific comparisons. Unknown candidates remain unresolved.
"""
from dataclasses import dataclass, asdict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json, os, math, time
from geometry import digest, canonical
from contracts import value, validate_evaluation, refinement_requests

WORK_KEYS=('evaluations','rays','source_samples','point_time_samples','time_panels','plate_tests')


def feasibility(result):
    states=[]
    for m in result['constraints'].values():
        v=value(m)
        if m['status']!='bounded_conditional' or not v.known: states.append('unknown')
        elif v.lo>0: return 'infeasible'
        elif v.hi<=0: states.append('feasible')
        else: states.append('unknown')
    return 'unknown' if 'unknown' in states else 'feasible'


def compare(a,b):
    if a['provenance'].get('oracle_signature')!=b['provenance'].get('oracle_signature'): raise ValueError('incompatible oracle/data versions')
    if set(a['objectives'])!=set(b['objectives']) or set(a['constraints'])!=set(b['constraints']): raise ValueError('incompatible metric schemas')
    for group in ('objectives','constraints'):
        for key in a[group]:
            if a[group][key]['unit']!=b[group][key]['unit']: raise ValueError('incompatible '+group+' units')
            if a[group][key].get('definition','')!=b[group][key].get('definition',''): raise ValueError('incompatible metric definitions')
    fa,fb=feasibility(a),feasibility(b)
    if fa=='feasible' and fb=='infeasible': return {'relation':'a_dominates','basis':'certified_feasibility','refinements':[]}
    if fb=='feasible' and fa=='infeasible': return {'relation':'b_dominates','basis':'certified_feasibility','refinements':[]}
    if fa=='infeasible' and fb=='infeasible': return {'relation':'both_infeasible','basis':'constraint_bounds','refinements':[]}
    if fa!='feasible' or fb!='feasible': return {'relation':'inconclusive','basis':'unknown_feasibility','refinements':refinement_requests(a,b)}
    pairs=[]
    for key in a['objectives']:
        am,bm=a['objectives'][key],b['objectives'][key]
        if am['unit']!=bm['unit']: raise ValueError('incompatible objective units')
        if any(m['status']!='bounded_conditional' or not value(m).known for m in (am,bm)):
            return {'relation':'inconclusive','basis':'uncertified_objective_error','refinements':refinement_requests(a,b)}
        pairs.append((value(am),value(bm)))
    ad=all(x.hi<=y.lo for x,y in pairs) and any(x.hi<y.lo for x,y in pairs)
    bd=all(y.hi<=x.lo for x,y in pairs) and any(y.hi<x.lo for x,y in pairs)
    if ad or bd: return {'relation':'a_dominates' if ad else 'b_dominates','basis':'outward_interval_pareto','refinements':[]}
    if any(x.hi<y.lo for x,y in pairs) and any(y.hi<x.lo for x,y in pairs): return {'relation':'tradeoff','basis':'opposing_resolved_objectives','refinements':[]}
    return {'relation':'inconclusive','basis':'overlapping_uncertainty_or_equal_objectives','refinements':refinement_requests(a,b)}


@dataclass(frozen=True)
class Limits:
    evaluations: int=100
    rays: int=100_000
    source_samples: int=100_000
    point_time_samples: int=100_000
    time_panels: int=100_000
    plate_tests: int=1_000_000
    wall_seconds: float=60.
    def __post_init__(self):
        if any(type(getattr(self,k)) is not int or getattr(self,k)<0 for k in WORK_KEYS) or not math.isfinite(self.wall_seconds) or self.wall_seconds<=0: raise ValueError('invalid limits')


class Budget:
    def __init__(self,limits,used=None,elapsed=0.):
        self.limits=limits;self.used=dict(used) if used is not None else dict.fromkeys(WORK_KEYS,0);self.elapsed_prior=elapsed;self.start=time.monotonic()
        if set(self.used)!=set(WORK_KEYS) or any(type(v) is not int or v<0 for v in self.used.values()) or elapsed<0 or not math.isfinite(elapsed): raise ValueError('invalid checkpoint budget')
        if any(self.used[k]>getattr(limits,k) for k in WORK_KEYS): raise ValueError('resume budget below already reserved work')
    @property
    def elapsed(self): return self.elapsed_prior+time.monotonic()-self.start
    def reserve(self,work):
        if set(work)!=set(WORK_KEYS) or any(type(v) is not int or v<0 for v in work.values()): raise ValueError('bad cost estimate')
        if self.elapsed>=self.limits.wall_seconds: return 'wall_seconds'
        for k in WORK_KEYS:
            if self.used[k]+work[k]>getattr(self.limits,k): return k
        for k in WORK_KEYS: self.used[k]+=work[k]
        return None
    def report(self): return {'reserved':self.used.copy(),'limits':asdict(self.limits),'elapsed_seconds':self.elapsed,'reservation_is_upper_budget_not_measured_device_work':True}


def atomic_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp')
    with tmp.open('w') as f:
        f.write(json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)


class Search:
    def __init__(self,candidates,oracle,manufacturing,limits=Limits(),checkpoint=None,progress=None,cancel=None,workers=1,allow_parallel=False,surrogate=None):
        if type(workers) is not int or not 1<=workers<=4 or (workers>1 and not allow_parallel): raise ValueError('local parallelism requires explicit allow_parallel, 1..4 workers')
        if not candidates or len({d.id for d in candidates})!=len(candidates): raise ValueError('nonempty unique candidate list required')
        self.candidates=list(candidates);self.oracle=oracle;self.manufacturing=manufacturing;self.checkpoint=Path(checkpoint) if checkpoint else None;self.progress=progress or (lambda x:None);self.cancel=cancel or (lambda:False);self.workers=workers;self.budget=Budget(limits)
        # The predictor is not an oracle. Its finite output influences order only.
        if surrogate:
            predicted={d.id:surrogate(d) for d in candidates}
            if any(not math.isfinite(v) for v in predicted.values()): raise ValueError('finite surrogate ordering scores required')
            self.candidates.sort(key=lambda d:(predicted[d.id],d.id))
        self.signature=digest({'candidates':[d.to_dict() for d in self.candidates],'oracle':oracle.signature,'manufacturing':asdict(manufacturing),'schema':'T03-R2-checkpoint-v1'})
        self.records=[];self.rejected={};self.next_index=0;self.state='ready';self.failures=[]

    def save(self):
        if self.checkpoint:
            payload={'schema':'T03-R2-checkpoint-v1','signature':self.signature,'records':self.records,'rejected':self.rejected,'next_index':self.next_index,'state':self.state,'failures':self.failures,'budget':self.budget.report()}
            atomic_json(self.checkpoint,{'payload':payload,'payload_sha256':digest(payload)})

    def restore(self):
        if not self.checkpoint or not self.checkpoint.exists(): raise ValueError('checkpoint missing')
        d=json.loads(self.checkpoint.read_text());p=d['payload']
        if digest(p)!=d['payload_sha256'] or p['signature']!=self.signature or p['schema']!='T03-R2-checkpoint-v1': raise ValueError('checkpoint integrity/provenance mismatch')
        if type(p['next_index']) is not int or not 0<=p['next_index']<=len(self.candidates): raise ValueError('checkpoint cursor')
        self.records=[validate_evaluation(r) for r in p['records']];self.rejected=p['rejected'];self.next_index=p['next_index'];self.state='ready';self.failures=p['failures']
        ids={d.id for d in self.candidates[:self.next_index]}
        if any(r['candidate_id'] not in ids or r['provenance'].get('oracle_signature')!=self.oracle.signature for r in self.records) or len({r['candidate_id'] for r in self.records})!=len(self.records): raise ValueError('invalid checkpoint records')
        self.budget=Budget(self.budget.limits,p['budget']['reserved'],p['budget']['elapsed_seconds'])
        return self

    def run(self):
        self.state='running';self.save()
        while self.next_index<len(self.candidates):
            if self.cancel(): self.state='cancelled';break
            jobs=[];cursor=self.next_index;stop_reason=None
            while cursor<len(self.candidates) and len(jobs)<self.workers:
                d=self.candidates[cursor];violations=self.manufacturing.check(d)
                if violations:
                    self.rejected[d.id]=violations;cursor+=1
                    if not jobs: self.next_index=cursor;self.save()
                    continue
                estimate=self.oracle.estimate(d,0);stop_reason=self.budget.reserve(estimate)
                if stop_reason: break
                jobs.append((cursor,d));cursor+=1
            if not jobs:
                self.next_index=cursor
                if stop_reason: self.state='budget_exhausted:'+stop_reason
                break
            def evaluate(job):
                i,d=job
                try:
                    r=validate_evaluation(self.oracle.evaluate(d,0,lambda:self.cancel() or self.budget.elapsed>=self.budget.limits.wall_seconds))
                    if r['candidate_id']!=d.id or r['provenance'].get('oracle_signature')!=self.oracle.signature: raise ValueError('oracle result identity/version mismatch')
                    return i,r,None
                except Exception as e: return i,None,{'type':type(e).__name__,'message':str(e),'candidate_id':d.id}
            if self.workers==1: results=[evaluate(jobs[0])]
            else:
                with ThreadPoolExecutor(max_workers=self.workers) as pool: results=list(pool.map(evaluate,jobs))
            # Merge in planned order, independent of completion timing. Interrupted jobs
            # remain pending; reservations are retained across retries/crashes.
            interrupted=False
            for i,r,error in sorted(results):
                if interrupted: continue
                if error:
                    self.failures.append(error);self.next_index=i
                    self.state='cancelled' if error['type']=='InterruptedError' and self.cancel() else 'budget_exhausted:wall_seconds' if error['type']=='InterruptedError' else 'oracle_failed'
                    interrupted=True;break
                self.records.append(r);self.next_index=i+1
                self.progress({'event':'evaluation_completed','candidate_id':r['candidate_id'],'completed':len(self.records),'total':len(self.candidates),'feasibility':feasibility(r),'reserved':self.budget.used.copy()});self.save()
            if interrupted: break
            self.next_index=cursor;self.save()
            if stop_reason: self.state='budget_exhausted:'+stop_reason;break
        if self.next_index==len(self.candidates) and not self.state.startswith(('cancelled','oracle_failed','budget_exhausted')): self.state='completed_finite_candidate_set'
        self.save();return self.summary()

    def summary(self):
        dominated=set();comparisons=[];requests=[]
        for i,a in enumerate(self.records):
            for b in self.records[i+1:]:
                c=compare(a,b);comparisons.append({'a':a['candidate_id'],'b':b['candidate_id'],**c})
                if c['relation']=='a_dominates': dominated.add(b['candidate_id'])
                if c['relation']=='b_dominates': dominated.add(a['candidate_id'])
                requests.extend(c['refinements'])
        def qualified(r): return all(m['status']=='bounded_conditional' and value(m).known for m in r['objectives'].values())
        unknown=[r['candidate_id'] for r in self.records if feasibility(r)=='unknown' or (feasibility(r)=='feasible' and not qualified(r))]
        pair_unresolved={cid for c in comparisons if c['relation']=='inconclusive' for cid in (c['a'],c['b'])}
        for r in self.records:
            if r['candidate_id'] in unknown: requests.extend(refinement_requests(r))
        archive=[r['candidate_id'] for r in self.records if feasibility(r)=='feasible' and qualified(r) and r['candidate_id'] not in dominated]
        inconclusive=bool(unknown) or any(c['relation']=='inconclusive' for c in comparisons)
        return {'schema_version':'T03-R2-search-v1','execution_status':self.state,'decision_status':'inconclusive' if inconclusive else 'resolved_on_evaluated_candidates','certified_feasible_nondominated_ids':archive,'unresolved_ids':sorted(set(unknown)|pair_unresolved),'archive_semantics':'qualified feasible candidates not eliminated by certified dominance; overlapping interval survivors are not proven true Pareto members','manufacturing_rejections':self.rejected,'comparisons':comparisons,'refinement_requests':list({digest(r):r for r in requests}.values()),'evaluations':self.records,'budget':self.budget.report(),'failures':self.failures,'evaluated_candidate_count':len(self.records),'planned_candidate_count':len(self.candidates),'global_optimality_claim':False,'physical_certification':False,'stage_status':'implementation_ready_validation_pending'}
