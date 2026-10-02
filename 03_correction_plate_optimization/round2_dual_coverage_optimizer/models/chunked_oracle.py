"""Point-partition streaming adapter. Each point retains all its time/source nodes.

Only one point block is loaded at a time; no whole-grid bundle or cross-block
visibility cache is needed. Metadata costs are verified against loaded bundles.
Correlation is not assumed away: all aggregation is interval arithmetic.
"""
from geometry import digest
from oracle import RayOracle,VisibilityCache,code_hash
from contracts import measure,value,validate_evaluation
from intervals import Interval,maximum,sum_intervals


def qualification(statuses):
    return 'unknown' if 'unknown' in statuses else 'estimated' if 'estimated' in statuses else 'bounded_conditional'


class ChunkedRayOracle:
    def __init__(self,chunk_specs,load_bundle,objectives):
        self.specs=tuple(dict(s) for s in chunk_specs);self.load_bundle=load_bundle;self.objectives=dict(objectives)
        if not self.specs: raise ValueError('nonempty point chunk list required')
        for s in self.specs:
            if any(type(s[k]) is not int or s[k]<1 for k in ('point_count','time_panels','ray_count')) or not s.get('sha256'): raise ValueError('complete positive chunk metadata required')
        self.signature=digest({'chunks':self.specs,'objectives':self.objectives,'code':code_hash()});self._metadata_digest=digest([self.specs,self.objectives])
    def estimate(self,design,fidelity=0):
        if fidelity!=0: raise ValueError('refinement needs separate supplied chunk set')
        rays=sum(s['ray_count'] for s in self.specs)
        return {'evaluations':1,'rays':rays,'source_samples':rays,'point_time_samples':sum(s['point_count']*s['time_panels'] for s in self.specs),'time_panels':sum(s['time_panels'] for s in self.specs),'plate_tests':rays*sum(sum(p.bits) for p in design.plates)}
    def evaluate(self,design,fidelity=0,cancel=lambda:False):
        if digest([self.specs,self.objectives])!=self._metadata_digest: raise ValueError('chunk metadata mutated')
        work=self.estimate(design,fidelity);points=[];errors=[];parts=[];offset=0;actual=0
        # Each lightweight part retains scalar aggregate intervals, not rays.
        reference_constants=None
        for index,spec in enumerate(self.specs):
            if cancel(): raise InterruptedError('cancelled between point chunks')
            b=self.load_bundle(index)
            if (len(b.rays),len(b.area_weights),len(b.time_weights_s))!=(spec['ray_count'],spec['point_count'],spec['time_panels']): raise ValueError('loaded chunk shape differs from reserved work')
            constants=(b.atomic_density_m3,b.energy_per_ion_eV,b.baseline_mean_h_m)
            if reference_constants is not None and constants!=reference_constants: raise ValueError('incompatible constants across point chunks')
            reference_constants=constants
            o=RayOracle(b,**self.objectives,cache=VisibilityCache(max_entries=1));r=o.evaluate(design,cancel=cancel)
            for p in r['point_fields']:
                p['point_id']+=offset
                for k in ('N_net','h','D','U','R','epsilon','tau'):
                    for e in p[k]['errors']:
                        e['points']=[v+offset for v in e['points']] if e['points'] else list(range(offset,offset+len(b.area_weights)))
                points.append(p)
            for e in r['error_sources']:
                e['points']=[v+offset for v in e['points']] if e['points'] else list(range(offset,offset+len(b.area_weights)))
                errors.append(e)
            w=sum_intervals(Interval.point(v) for v in b.area_weights)
            parts.append({'weight':w,'objectives':r['objectives'],'constraints':r['constraints'],'mean_h':r['area_statistics']['mean_h_m'],'status':r['status'],'fixture':b.finite_fixture})
            actual+=r['work']['actual_predicate_rays'];offset+=len(b.area_weights)
            del o,b,r
        objectives={k:measure(maximum(value(part['objectives'][k]) for part in parts),parts[0]['objectives'][k]['unit'],qualification([part['objectives'][k]['status'] for part in parts]),definition='maximum across disjoint point blocks') for k in parts[0]['objectives']}
        total_weight=sum_intervals(p['weight'] for p in parts)
        # Multiplication of nonnegative area-weight intervals by signed g values.
        def product(a,b):
            if not a.known or not b.known:return Interval.unknown()
            from fractions import Fraction
            from intervals import rounded
            vals=[Fraction(x)*Fraction(y) for x in (a.lo,a.hi) for y in (b.lo,b.hi)]
            return Interval(rounded(min(vals),True),rounded(max(vals),False))
        constraints={}
        for k in parts[0]['constraints']:
            iv=(sum_intervals(product(value(p['constraints'][k]),p['weight']) for p in parts).divide(total_weight) if k=='throughput' else maximum(value(p['constraints'][k]) for p in parts))
            constraints[k]=measure(iv,parts[0]['constraints'][k]['unit'],qualification([p['constraints'][k]['status'] for p in parts]))
        mean=sum_intervals(product(value(p['mean_h']),p['weight']) for p in parts).divide(total_weight)
        status='partial' if any(p['status']=='partial' for p in parts) else 'estimated' if any(p['status']=='estimated' for p in parts) else 'bounded_conditional'
        result={'candidate_id':design.id,'fidelity':fidelity,'provenance':{'oracle_signature':self.signature,'chunk_sha256':[s['sha256'] for s in self.specs],'code_sha256':code_hash(),'finite_discrete_fixture':all(p['fixture'] for p in parts),'point_partition_only':True},'objectives':objectives,'constraints':constraints,'point_fields':points,'error_sources':errors,'work':{**work,'actual_predicate_rays':actual,'point_chunks':len(parts)},'status':status,'physical_certification':False,'area_statistics':{'mean_h_m':measure(mean,'m',qualification([p['mean_h']['status'] for p in parts]))}}
        return validate_evaluation(result)
