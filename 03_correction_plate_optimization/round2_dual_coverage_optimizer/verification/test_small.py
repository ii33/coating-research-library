"""Small analytical/contract regressions, not a performance evaluation."""
from pathlib import Path
import sys,unittest,tempfile,json,subprocess,copy
from dataclasses import replace,asdict
from fractions import Fraction
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'models'))
from intervals import Interval
from geometry import Design,Plate,Manufacturing
from contracts import ErrorSource,validate_evaluation
from oracle import SyntheticOracle,RayOracle,RayBundle,Ray,VisibilityCache,static_point_fixture
from optimizer import Search,Limits,compare,feasibility
from chunked_oracle import ChunkedRayOracle
from device_runner import bundle_from_dict,import_t02_evidence,execute
ROOT=Path(__file__).resolve().parents[1]


def candidates():
    p=Plate('a',(1,0),1,2,.02,(-.04,0,.3),.002)
    q=Plate('b',(1,0),1,2,.02,(.04,0,.7),.002)
    return [Design((replace(p,center_m=(p.center_m[0]+i*.001,0,.3)),q)) for i in range(3)]


class Intervals(unittest.TestCase):
    def test_outward(self):
        x=Interval.point(.1)+Interval.point(.2);true=Fraction(.1)+Fraction(.2)
        self.assertLessEqual(Fraction(x.lo),true);self.assertGreaterEqual(Fraction(x.hi),true)
        q=Interval(.1,.2).divide(Interval(.3,.4))
        self.assertLessEqual(Fraction(q.lo),Fraction(.1)/Fraction(.4));self.assertGreaterEqual(Fraction(q.hi),Fraction(.2)/Fraction(.3))
    def test_zero_denominator(self): self.assertFalse(Interval(1,2).divide(Interval(0,1)).known)
    def test_unknown(self): self.assertFalse((Interval.unknown()+Interval.point(1)).known)
    def test_invalid(self):
        for v in [(2,1),(0,float('nan')),(None,1)]:
            with self.assertRaises(ValueError): Interval(*v)


class Geometry(unittest.TestCase):
    def test_binary_only(self):
        with self.assertRaises(ValueError): Plate('a',(.5,),1,1,.02,(0,0,.3),.001)
    def test_two_plate_conflict(self):
        d=candidates()[0];self.assertEqual(Manufacturing().check(d),[])
        collision=Design((d.plates[0],replace(d.plates[1],center_m=d.plates[0].center_m)))
        self.assertIn('two_plate_envelope_conflict',Manufacturing().check(collision))
    def test_feature_and_mount(self):
        d=candidates()[0];p=replace(d.plates[0],nx=2,ny=2,bits=(0,0,0,1))
        self.assertTrue(any('unsupported' in x for x in Manufacturing().check(Design((p,d.plates[1])))))
        self.assertTrue(any('minimum_feature' in x for x in Manufacturing(min_feature_m=.03).check(d)))
    def test_thickness_workspace_boundary(self):
        d=candidates()[0];p=replace(d.plates[0],thickness_m=.02,center_m=(2,0,.3))
        errors=Manufacturing(max_boundary_m=.001).check(Design((p,d.plates[1])));self.assertTrue(any('thickness' in e for e in errors));self.assertTrue(any('workspace' in e for e in errors));self.assertTrue(any('boundary' in e for e in errors))


class Decisions(unittest.TestCase):
    def setUp(self):
        self.ds=candidates();self.values={d.id:v for d,v in zip(self.ds,[(.1,.1,-1),(.4,.4,-1),(.1,.1,.1)])}
    def test_dominance_and_infeasible(self):
        o=SyntheticOracle(self.values);a,b,c=[o.evaluate(d) for d in self.ds]
        self.assertEqual(compare(a,b)['relation'],'a_dominates');self.assertEqual(feasibility(c),'infeasible')
    def test_noise_overlap_not_ranked(self):
        o=SyntheticOracle(self.values,radius=.3);a,b=[o.evaluate(d) for d in self.ds[:2]]
        r=compare(a,b);self.assertEqual(r['relation'],'inconclusive');self.assertTrue(r['refinements'])
    def test_equal_no_false_rank(self):
        self.values[self.ds[1].id]=self.values[self.ds[0].id]
        o=SyntheticOracle(self.values);self.assertEqual(compare(o.evaluate(self.ds[0]),o.evaluate(self.ds[1]))['relation'],'inconclusive')
    def test_unknown_and_estimated(self):
        for kw in [dict(unknown_ids=[self.ds[0].id]),dict(estimated=True)]:
            o=SyntheticOracle(self.values,**kw);a,b=[o.evaluate(d) for d in self.ds[:2]]
            self.assertEqual(feasibility(a),'unknown');self.assertEqual(compare(a,b)['relation'],'inconclusive')
    def test_wrong_surrogate(self):
        o=SyntheticOracle(self.values)
        r=Search(self.ds,o,Manufacturing(),surrogate=lambda d:-self.values[d.id][0]).run()
        self.assertEqual(r['certified_feasible_nondominated_ids'],[self.ds[0].id])
    def test_empty_objectives_rejected(self):
        a=SyntheticOracle(self.values).evaluate(self.ds[0]);a['objectives']={}
        with self.assertRaises(ValueError): validate_evaluation(a)
    def test_single_uncertain_objective_is_inconclusive(self):
        base=SyntheticOracle(self.values)
        class OneUncertain:
            signature=base.signature
            estimate=base.estimate
            def evaluate(inner,d,fidelity=0,cancel=lambda:False):
                r=base.evaluate(d,fidelity,cancel);r['objectives']['h_target_max_deviation']['status']='estimated';r['status']='estimated';return r
        r=Search([self.ds[0]],OneUncertain(),Manufacturing()).run()
        self.assertEqual(r['decision_status'],'inconclusive');self.assertEqual(r['certified_feasible_nondominated_ids'],[])
    def test_units_checked_before_feasibility_dominance(self):
        o=SyntheticOracle(self.values);a=o.evaluate(self.ds[0]);b=o.evaluate(self.ds[2]);b['constraints']['throughput']['unit']='m'
        with self.assertRaises(ValueError): compare(a,b)
    def test_bad_error_status(self):
        a=SyntheticOracle(self.values).evaluate(self.ds[0]);a['objectives']['h_target_max_deviation']['errors'][0]['status']='estimated'
        with self.assertRaises(ValueError): validate_evaluation(a)
    def test_tradeoff(self):
        self.values[self.ds[1].id]=(.05,.4,-1);o=SyntheticOracle(self.values)
        self.assertEqual(compare(o.evaluate(self.ds[0]),o.evaluate(self.ds[1]))['relation'],'tradeoff')


class Control(unittest.TestCase):
    def setUp(self):
        self.ds=candidates();self.o=SyntheticOracle({d.id:(i/10,i/10,-1) for i,d in enumerate(self.ds)})
    def test_zero_budget(self):
        r=Search(self.ds,self.o,Manufacturing(),Limits(evaluations=0)).run()
        self.assertEqual(r['evaluated_candidate_count'],0);self.assertEqual(r['execution_status'],'budget_exhausted:evaluations')
    def test_ray_budget_before_call(self):
        r=Search(self.ds,self.o,Manufacturing(),Limits(rays=3)).run()
        self.assertEqual(r['evaluated_candidate_count'],0);self.assertEqual(r['budget']['reserved']['rays'],0)
    def test_cancel_restore_consistency(self):
        with tempfile.TemporaryDirectory() as tmp:
            flag={'cancel':False};progress=lambda _:flag.update(cancel=True)
            s=Search(self.ds,self.o,Manufacturing(),checkpoint=Path(tmp)/'cp.json',progress=progress,cancel=lambda:flag['cancel'])
            part=s.run();self.assertEqual(part['execution_status'],'cancelled');self.assertEqual(part['evaluated_candidate_count'],1)
            full=Search(self.ds,self.o,Manufacturing(),checkpoint=Path(tmp)/'cp.json').restore().run()
            direct=Search(self.ds,self.o,Manufacturing()).run()
            self.assertEqual(full['evaluations'],direct['evaluations']);self.assertEqual(full['budget']['reserved'],direct['budget']['reserved'])
    def test_changed_data_refuses_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            cp=Path(tmp)/'cp.json';Search(self.ds,self.o,Manufacturing(),checkpoint=cp).run()
            changed=SyntheticOracle({d.id:(1,1,-1) for d in self.ds})
            with self.assertRaises(ValueError): Search(self.ds,changed,Manufacturing(),checkpoint=cp).restore()
    def test_parallel_explicit_only(self):
        with self.assertRaises(ValueError): Search(self.ds,self.o,Manufacturing(),workers=2)
    def test_default_plan_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'result';s=subprocess.check_output([sys.executable,'-B',str(ROOT/'models/run_optimizer.py'),'--output',str(out)],text=True)
            self.assertEqual(json.loads(s)['status'],'plan_only');self.assertFalse(out.exists())
    def test_device_plan_only(self):
        s=subprocess.check_output([sys.executable,'-B',str(ROOT/'models/device_runner.py')],text=True)
        self.assertEqual(json.loads(s)['status'],'plan_only')
    def test_device_placeholder_execute_refuses(self):
        cfg=json.loads((ROOT/'verification/device_validation_plan.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError): execute(cfg,tmp,tmp)


class RayChecks(unittest.TestCase):
    def setUp(self):
        self.b=static_point_fixture();self.empty=Design((Plate('a',(0,),1,1,.02,(0,0,.3),.002),Plate('b',(0,),1,1,.02,(0,0,.7),.002)))
    def oracle(self,b=None,**kw): return RayOracle(b or self.b,self.b.baseline_mean_h_m,target_D_m2=1e16,**kw)
    def test_smoke_eight_rays(self):
        r=self.oracle().evaluate(self.empty)
        self.assertEqual(r['work']['rays'],8);self.assertEqual(r['status'],'bounded_conditional');self.assertEqual(r['area_statistics']['ratio_valid_area_fraction'],1)
    def test_dual_channel_not_shared_and_double_ion(self):
        r1=self.oracle().evaluate(self.empty)
        b2=replace(self.b,rays=tuple(replace(r,contribution=r.contribution*2) if r.channel=='ion' else r for r in self.b.rays))
        r2=self.oracle(b2).evaluate(self.empty)
        for a,b in zip(r1['point_fields'],r2['point_fields']):
            self.assertEqual(a['h'],b['h']);self.assertAlmostEqual(b['D']['lo'],2*a['D']['lo'])
        self.assertNotEqual(r1['objectives']['ion_target_max_deviation'],r2['objectives']['ion_target_max_deviation'])
    def test_cache_rate_separation(self):
        cache=VisibilityCache();o1=self.oracle(cache=cache);r1=o1.evaluate(self.empty)
        b=replace(self.b,rays=tuple(replace(r,contribution=r.contribution*2) for r in self.b.rays));r2=self.oracle(b,cache=cache).evaluate(self.empty)
        self.assertTrue(r2['work']['geometry_cache_hit']);self.assertEqual(r1['provenance']['geometry_cache_key'],r2['provenance']['geometry_cache_key']);self.assertNotEqual(r1['provenance']['weighted_data_key'],r2['provenance']['weighted_data_key'])
        moved=replace(self.empty,plates=(replace(self.empty.plates[0],center_m=(.001,0,.3)),self.empty.plates[1]));r3=o1.evaluate(moved);self.assertFalse(r3['work']['geometry_cache_hit'])
    def test_margin_unknown_ratio(self):
        # Target ray exactly on a plate edge; measurement margin makes visibility unknown.
        rays=(Ray('vapor',0,0,(.01,0,0),(.01,0,1),1.),Ray('ion',0,0,(.02,0,0),(.02,0,1),1.))
        b=RayBundle(rays,(1.,),(1.,),1.,100.,1.,{'fixture':'edge'},(),True,.001)
        d=Design((Plate('a',(1,),1,1,.02,(0,0,.3),.002),self.empty.plates[1]))
        r=RayOracle(b,1,target_epsilon_eV=100).evaluate(d)
        self.assertEqual(r['point_fields'][0]['N_net']['lo'],0);self.assertEqual(r['point_fields'][0]['N_net']['hi'],1)
        self.assertTrue(any(e['axis']=='geometry' and e['points']==[0] for e in r['error_sources']));self.assertEqual(r['point_fields'][0]['epsilon']['status'],'unknown');self.assertEqual(r['point_fields'][0]['tau']['lo'],0);self.assertEqual(r['point_fields'][0]['tau']['hi'],1)
    def test_ion_interval_constraint(self):
        r=RayOracle(self.b,self.b.baseline_mean_h_m,target_D_m2=1e16,ion_allowed_interval=(0,1),max_h_relative_deviation=.2).evaluate(self.empty)
        self.assertEqual(feasibility(r),'infeasible');self.assertIn('h_target_deviation',r['constraints'])
    def test_ill_conditioned_ratio_and_event_error(self):
        rays=(Ray('vapor',0,0,(0,0,0),(0,0,1),1.),Ray('ion',0,0,(0,0,0),(0,0,1),1.))
        b=RayBundle(rays,(1.,),(1.,),1.,1.,1.,{'fixture':'denominator'},(ErrorSource('input','bounded_conditional',.6,'N',(0,)),),True)
        r=RayOracle(b,1,target_epsilon_eV=1).evaluate(self.empty)
        self.assertEqual(r['point_fields'][0]['ratio_conditioning'],'ill_conditioned');self.assertEqual(r['objectives']['ion_target_max_deviation']['status'],'unknown');self.assertEqual(r['point_fields'][0]['tau']['status'],'unknown')
    def test_error_point_outside_domain_rejected(self):
        with self.assertRaises(ValueError): replace(self.b,errors=(ErrorSource('model','unknown',None,'N',(2,)),))
    def test_physical_error_coverage_per_point(self):
        errors=tuple(ErrorSource(a,'unknown',None,f,(0,)) for f in ('N','D') for a in ('source','time','space','geometry','kernel','input','model'))
        with self.assertRaises(ValueError): replace(self.b,finite_fixture=False,errors=errors)
    def test_missing_physical_error_axes_refused(self):
        with self.assertRaises(ValueError): replace(self.b,finite_fixture=False)
    def test_physical_unknowns_propagate(self):
        errors=tuple(ErrorSource(a,'unknown',None,f,evidence='unclosed T02 reference') for f in ('N','D') for a in ('source','time','space','geometry','kernel','input','model'))
        b=replace(self.b,finite_fixture=False,errors=errors);r=self.oracle(b).evaluate(self.empty)
        self.assertEqual(r['status'],'partial');self.assertEqual(feasibility(r),'unknown')
    def test_bundle_roundtrip(self): self.assertEqual(bundle_from_dict(asdict(self.b)),self.b)
    def test_chunked_matches_full_point_partition(self):
        chunks=[]
        for pt in range(2):
            chunks.append(replace(self.b,rays=tuple(replace(r,point=0) for r in self.b.rays if r.point==pt),area_weights=(self.b.area_weights[pt],)))
        specs=[{'sha256':str(i),'point_count':1,'time_panels':2,'ray_count':4} for i in range(2)]
        co=ChunkedRayOracle(specs,lambda i:chunks[i],{'target_h_m':self.b.baseline_mean_h_m,'target_D_m2':1e16})
        a=self.oracle().evaluate(self.empty);b=co.evaluate(self.empty)
        self.assertEqual(a['point_fields'],b['point_fields']);self.assertEqual(a['objectives']['h_target_max_deviation']['lo'],b['objectives']['h_target_max_deviation']['lo'])
        self.assertAlmostEqual(a['constraints']['throughput']['lo'],b['constraints']['throughput']['lo'],places=14)
        self.assertEqual(b['work']['rays'],8);self.assertEqual(b['work']['point_chunks'],2)
    def test_error_alias_copy(self):
        indices=[0];e=ErrorSource('model','unknown',None,'N',indices);indices[0]=99
        self.assertEqual(e.points,(0,))
        errors=[e];b=replace(self.b,errors=errors);errors.clear();self.assertEqual(len(b.errors),1)
    def test_t02_estimate_no_upgrade(self):
        x=import_t02_evidence({'point_id':12,'status':'completed_estimates_only','assessment':{'reference_checks':{'ion':{'agreement':True}}}})
        self.assertFalse(x['usable_as_certified_optimizer_oracle']);self.assertFalse(x['strict_certificate'])

if __name__=='__main__': unittest.main()
