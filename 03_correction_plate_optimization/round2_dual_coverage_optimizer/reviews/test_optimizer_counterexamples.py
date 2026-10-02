"""Independent tiny stdlib counterexample suite for T03 optimizer review.
Run from this directory with: python -m unittest -v test_optimizer_counterexamples.py
No external data, network, T02 evaluation, or production claim.
"""
import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "models"))

from intervals import Interval
from geometry import Design, Plate, Manufacturing
from oracle import Ray, RayBundle, RayOracle, SyntheticOracle, VisibilityCache
from optimizer import Search, Limits, compare, feasibility, WORK_KEYS
from contracts import validate_evaluation, measure, ErrorSource
from contracts import ERROR_AXES


def plate(name, center, bits=(1, 0), nx=2, ny=1):
    return Plate(name, bits, nx, ny, .02, center, .002)


def eval_record(cid, sig, obj, con, top='bounded_conditional'):
    return {'candidate_id': cid, 'fidelity': 0, 'provenance': {'oracle_signature': sig},
            'objectives': {'loss': obj}, 'constraints': {'g': con}, 'point_fields': [],
            'error_sources': [], 'work': {}, 'status': top, 'physical_certification': False}


class Counterexamples(unittest.TestCase):
    def test_unknown_and_estimated_measures_never_certify_feasibility(self):
        u=measure(Interval.unknown(),'1','unknown')
        e=measure(Interval(0,0),'1','estimated')
        self.assertEqual(feasibility(eval_record('u','s',u,u,'partial')), 'unknown')
        self.assertEqual(feasibility(eval_record('e','s',e,e,'estimated')), 'unknown')
        self.assertEqual(compare(eval_record('u','s',u,u,'partial'),
                                 eval_record('e','s',e,e,'estimated'))['relation'], 'inconclusive')

    def test_incompatible_units_cannot_take_feasibility_shortcut(self):
        a=eval_record('a','same',measure(Interval(0,1),'kg'),measure(Interval(-1,-1),'dimensionless'))
        b=eval_record('b','same',measure(Interval(0,1),'s'),measure(Interval(1,2),'meter'))
        with self.assertRaises(ValueError): compare(a,b)

    def test_noise_overlap_is_not_dominance(self):
        sig='same'; a=eval_record('a',sig,measure(Interval(.19,.31),'1'),measure(Interval(-.2,-.1),'1'))
        b=eval_record('b',sig,measure(Interval(.24,.36),'1'),measure(Interval(-.2,-.1),'1'))
        c=compare(a,b)
        self.assertEqual(c['relation'],'inconclusive')
        self.assertEqual(c['basis'],'overlapping_uncertainty_or_equal_objectives')

    def test_single_candidate_estimated_objective_is_unresolved_not_archived(self):
        design=Design((plate('vapor',(-.03,0,.3),(0,0)),plate('ion',(.03,0,.7),(0,0))))
        base=SyntheticOracle({design.id:(.1,.2,-1.)})
        class EstimatedObjectiveOracle:
            signature=base.signature
            def estimate(self,d,fidelity=0): return base.estimate(d,fidelity)
            def evaluate(self,d,fidelity=0,cancel=lambda:False):
                r=base.evaluate(d,fidelity,cancel)
                for m in r['objectives'].values():
                    m['status']='estimated'
                    for e in m['errors']: e['status']='estimated'
                r['status']='estimated'
                return validate_evaluation(r)
        limits=Limits(evaluations=2,rays=100,source_samples=100,point_time_samples=100,time_panels=100,plate_tests=100,wall_seconds=5)
        result=Search([design],EstimatedObjectiveOracle(),Manufacturing(),limits).run()
        self.assertEqual(result['decision_status'],'inconclusive')
        self.assertEqual(result['certified_feasible_nondominated_ids'],[])
        self.assertEqual(result['unresolved_ids'],[design.id])

    def test_denominator_spanning_zero_fails_closed(self):
        self.assertFalse(Interval(2,3).divide(Interval(-.01,.02)).known)
        self.assertFalse(Interval(2,3).divide(Interval(0,2)).known)
        self.assertTrue(Interval(2,3).divide(Interval(.5,2)).known)

    def test_two_plate_envelope_conflict_and_connected_mount(self):
        same_z=Design((plate('vapor',(0.,0,.4)),plate('ion',(0.,0,.4))))
        self.assertIn('two_plate_envelope_conflict', Manufacturing().check(same_z))
        apart=Design((plate('vapor',(-.03,0,.3)),plate('ion',(.03,0,.7))))
        self.assertNotIn('two_plate_envelope_conflict', Manufacturing().check(apart))
        disconnected=Design((plate('vapor',(-.03,0,.3),(1,0,1),3,1),
                             plate('ion',(.03,0,.7),(0,0),2,1)))
        self.assertIn('vapor:unsupported_or_disconnected_material',Manufacturing().check(disconnected))

    def test_out_of_range_error_point_is_rejected(self):
        rays=(Ray('vapor',0,0,(-.06,0,0),(0,0,1),1e17),
              Ray('ion',0,0,(.06,0,0),(0,0,1),1e16))
        # The unknown N error point is outside the only valid point ID (0).
        # RayBundle must reject it before RayOracle can filter the uncertainty out.
        with self.assertRaises(ValueError):
            bad=RayBundle(rays,(1.,),(1.,),1e28,100.,1e-10,
                  {'fixture':'point-index-check'},
                  (ErrorSource('model','unknown',None,'N',(1,),evidence='outside valid point set'),),True)

    def test_error_source_points_input_cannot_mutate_after_validation(self):
        pts=[0]
        try:
            error=ErrorSource('model','unknown',None,'N',pts,evidence='mutable alias regression')
        except (TypeError,ValueError):
            return  # Strict tuple-only constructors are safe.
        pts[0]=1
        self.assertEqual(tuple(error.points),(0,), 'ErrorSource retained caller-owned mutable point list')

    def test_ray_bundle_error_list_cannot_be_cleared_after_validation(self):
        rays=(Ray('vapor',0,0,(-.06,0,0),(0,0,1),1e17),
              Ray('ion',0,0,(.06,0,0),(0,0,1),1e16))
        errors=[ErrorSource('model','unknown',None,'N',(0,),evidence='mutable errors-list regression')]
        try:
            bundle=RayBundle(rays,(1.,),(1.,),1e28,100.,1e-10,{'fixture':'mutable-errors'},errors,True)
        except (TypeError,ValueError):
            return  # Strict tuple-only constructors are safe.
        errors.clear()
        design=Design((plate('vapor',(-.03,0,.3),(0,0)),plate('ion',(.03,0,.7),(0,0))))
        result=RayOracle(bundle,1e-9,target_D_m2=1e16).evaluate(design)
        self.assertNotEqual(result['objectives']['h_target_max_deviation']['status'],'bounded_conditional',
                            'RayBundle retained caller-owned mutable error list and certified after it was cleared')

    def test_physical_error_axes_must_cover_each_field_point(self):
        rays=tuple(Ray(ch,p,0,(-.06 if ch=='vapor' else .06,0,0),(-.02 if p==0 else .02,0,1),1.)
                   for ch in ('vapor','ion') for p in (0,1))
        errors=tuple(ErrorSource(axis,'bounded_conditional',0.,field,(p,),evidence='tiny complete coverage fixture')
                     for field in ('N','D') for p in (0,1) for axis in ERROR_AXES)
        args=(rays,(.5,.5),(1.,),1e28,100.,1.,{'fixture':'axis-point-coverage'},errors)
        self.assertIsInstance(RayBundle(*args),RayBundle)
        missing=tuple(e for e in errors if not (e.field=='D' and e.points==(1,) and e.axis=='model'))
        with self.assertRaises(ValueError): RayBundle(*args[:-1],missing)

    def test_geometry_unknown_retains_point_time_and_is_not_widened_twice(self):
        rays=(Ray('vapor',0,0,(0,0,0),(0,0,1),10.),Ray('ion',0,0,(0,0,0),(0,0,1),5.))
        bundle=RayBundle(rays,(1.,),(1.,),1.,100.,1.,{'fixture':'local-geometry'},(),True,.02)
        design=Design((Plate('vapor',(1,),1,1,.02,(0,0,.5),.002),
                       Plate('ion',(0,),1,1,.02,(.1,0,.8),.002)))
        result=RayOracle(bundle,.1,target_D_m2=1.).evaluate(design)
        geometry_errors=[e for e in result['error_sources'] if e['axis']=='geometry']
        self.assertEqual({(e['field'],tuple(e['points'])) for e in geometry_errors},{('N',(0,)),('D',(0,))})
        self.assertTrue(all('time_index=0' in e['evidence'] for e in geometry_errors))
        # The transmitted interval already contains the tri-state ambiguity.
        self.assertAlmostEqual(result['point_fields'][0]['N_net']['hi']-result['point_fields'][0]['N_net']['lo'],10.)
        self.assertAlmostEqual(result['point_fields'][0]['D']['hi']-result['point_fields'][0]['D']['lo'],5.)

    def test_cache_reuses_geometry_but_not_weighted_rates(self):
        design=Design((plate('vapor',(-.03,0,.3),(0,0)),plate('ion',(.03,0,.7),(0,0))))
        def bundle(rate):
            rays=(Ray('vapor',0,0,(-.06,0,0),(0,0,1),rate),
                  Ray('ion',0,0,(.06,0,0),(0,0,1),rate/2))
            return RayBundle(rays,(1.,),(1.,),1e28,100.,1e-10,
              {'source':'tiny review fixture'},(),True)
        cache=VisibilityCache()
        a=RayOracle(bundle(1e17),1e-9,target_D_m2=1e16,cache=cache).evaluate(design)
        b=RayOracle(bundle(2e17),1e-9,target_D_m2=1e16,cache=cache).evaluate(design)
        self.assertEqual(a['provenance']['geometry_cache_key'],b['provenance']['geometry_cache_key'])
        self.assertNotEqual(a['provenance']['weighted_data_key'],b['provenance']['weighted_data_key'])
        self.assertFalse(a['work']['geometry_cache_hit'])
        self.assertTrue(b['work']['geometry_cache_hit'])
        self.assertEqual(b['work']['actual_predicate_rays'],0)
        changed=Design((Plate('vapor',(1,),1,1,.02,(0,0,.5),.002),design.plates[1]))
        c=RayOracle(bundle(2e17),1e-9,target_D_m2=1e16,cache=cache).evaluate(changed)
        self.assertNotEqual(a['provenance']['geometry_cache_key'],c['provenance']['geometry_cache_key'])
        self.assertFalse(c['work']['geometry_cache_hit'])
        self.assertEqual(c['work']['actual_predicate_rays'],2)

    def test_cancel_checkpoint_resume_retains_reservations_and_progress(self):
        cands=[Design((plate('vapor',(-.03,0,.3),(0,0)),plate('ion',(.03,0,.7),(0,0))))]
        # Need distinct candidate identities without changing manufacturability.
        cands.append(Design((plate('vapor',(-.04,0,.3),(0,0)),plate('ion',(.03,0,.7),(0,0)))) )
        cands.append(Design((plate('vapor',(-.05,0,.3),(0,0)),plate('ion',(.03,0,.7),(0,0)))) )
        oracle=SyntheticOracle({d.id:(.1,.1,-1.) for d in cands})
        limits=Limits(evaluations=5,rays=100,source_samples=100,point_time_samples=100,time_panels=100,plate_tests=100,wall_seconds=30)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'ck.json'; calls={'n':0}
            def cancel_after_one():
                calls['n']+=1
                return calls['n']>=3  # run pre-check, oracle pre-check, then next loop
            first=Search(cands,oracle,Manufacturing(),limits,path,cancel=cancel_after_one)
            partial=first.run()
            self.assertEqual(partial['execution_status'],'cancelled')
            self.assertEqual(partial['evaluated_candidate_count'],1)
            self.assertEqual(partial['budget']['reserved']['evaluations'],1)
            second=Search(cands,oracle,Manufacturing(),limits,path)
            second.restore()
            result=second.run()
            self.assertEqual(result['execution_status'],'completed_finite_candidate_set')
            self.assertEqual(result['evaluated_candidate_count'],3)
            self.assertEqual(result['budget']['reserved']['evaluations'],3)

    def test_measure_error_qualification_cannot_be_hidden(self):
        """Estimated/unknown error provenance must not be hidden by a bounded measure."""
        estimated_error={'axis':'source','status':'estimated','absolute_radius':.1,'field':'g','points':[],'time_window_s':None,'evidence':'fixture'}
        bad=measure(Interval(-1,-.9),'1','bounded_conditional',[estimated_error])
        record=eval_record('forged','sig',measure(Interval(0,0),'1'),bad,'bounded_conditional')
        with self.assertRaises(ValueError): validate_evaluation(record)

    def test_empty_decision_schema_is_rejected(self):
        """An evaluation with no objectives must not appear decision-resolved."""
        record={'candidate_id':'empty','fidelity':0,'provenance':{'oracle_signature':'sig'},'objectives':{},'constraints':{},'point_fields':[],'error_sources':[],'work':{},'status':'bounded_conditional','physical_certification':False}
        with self.assertRaises(ValueError): validate_evaluation(record)


if __name__=='__main__': unittest.main(verbosity=2)
