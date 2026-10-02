import hashlib,json,math,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'models'))
from optical_examples import interp_nk,validate_nk,surface_R,intensity_depth_nm,incoherent_slab,lorentz_lorenz_void,examples
from build_nk_points import build
from build_material_package import CATALOG

def read(name):return json.loads((ROOT/'data'/name).read_text())
class MaterialRegistryTests(unittest.TestCase):
    def test_original_priority_order(self):
        manifest=read('materials_manifest.json')
        self.assertEqual([x['material_id'] for x in manifest],[x[0] for x in CATALOG])
        self.assertEqual([x['order'] for x in manifest],list(range(1,17)))
        self.assertEqual(sum(x['role']=='coating' for x in manifest),12)
        self.assertEqual(sum(x['role']=='substrate' for x in manifest),4)
    def test_cards_and_source_summaries(self):
        sources=read('source_registry.json')['sources'];ids=[x['id'] for x in sources]
        self.assertEqual(len(ids),len(set(ids)));self.assertEqual(len(ids),76)
        for s in sources:
            self.assertTrue(s['url'].startswith('https://'));self.assertTrue((ROOT/s['summary_path']).is_file(),s['id'])
        for card in read('materials_manifest.json'):
            self.assertGreater(len((ROOT/card['card_file']).read_text()),1000)
            self.assertTrue(card['source_ids']);self.assertTrue(set(card['source_ids'])<=set(ids));self.assertFalse(card['design_ready'])
    def test_parameter_integrity(self):
        rows=read('property_records.json')['records'];src={x['id'] for x in read('source_registry.json')['sources']};mids={x[0] for x in CATALOG}
        ids=[r['record_id'] for r in rows];self.assertEqual(len(ids),len(set(ids)))
        self.assertEqual({r['material_id'] for r in rows},mids)
        for r in rows:
            for field in ['property','unit','state','conditions','uncertainty','status']:self.assertTrue(r[field],(r['record_id'],field))
            self.assertFalse(r['design_ready'])
            if r['value'] is None:
                self.assertEqual(r['status'],'unknown');self.assertTrue(r['unknown_reason'])
            else:
                self.assertIn(r['source_id'],src)
                vals=r['value'] if isinstance(r['value'],list) else [r['value']]
                for v in vals:
                    if isinstance(v,(float,int)):self.assertTrue(math.isfinite(v))
    def test_quarantine_and_strict_bounds(self):
        rows=read('property_records.json')['records']
        bad=[r for r in rows if r['material_id']=='ZnS_film' and r['property']=='extinction_coefficient_k' and r['value']==3.85]
        self.assertEqual(len(bad),1);self.assertEqual(bad[0]['status'],'quarantined')
        ta=[r for r in rows if r.get('eligible_for_pure_material_default') is False]
        self.assertEqual(len(ta),2);self.assertTrue(all(r['status']=='quarantined' for r in ta))
        for r in rows:
            if r.get('bound_type')=='strict_upper_bound' or r['conditions'].get('comparison')=='<':self.assertEqual(r['qualifier'],'<')
    def test_schema_when_validator_available(self):
        try:import jsonschema
        except ImportError:self.skipTest('Optional jsonschema absent; structural tests still run')
        schema=read('property_record.schema.json')
        for r in read('property_records.json')['records']:jsonschema.validate(r,schema)
class OpticalExampleTests(unittest.TestCase):
    def test_interpolation_exact_linear_and_domain(self):
        rows=[(1.,2.,.1),(2.,4.,.3)]
        self.assertEqual(interp_nk(rows,1),(2.,.1));self.assertEqual(interp_nk(rows,2),(4.,.3))
        n,k=interp_nk(rows,1.5);self.assertEqual(n,3.);self.assertAlmostEqual(k,.2)
        for x in [.99,2.01,math.nan]:
            with self.assertRaises(ValueError):interp_nk(rows,x)
    def test_invalid_spectra_rejected(self):
        for rows in [[(1,1,-1),(2,1,0)],[(1,1,0),(1,2,0)],[(2,1,0),(1,1,0)],[(1,1,0),(2,math.inf,0)]]:
            with self.assertRaises(ValueError):validate_nk(rows)
    def test_fresnel_and_absorption(self):
        self.assertEqual(surface_R(1,0),0);self.assertAlmostEqual(surface_R(1.5,0),.04)
        self.assertAlmostEqual(intensity_depth_nm(1,1),1000/(4*math.pi));self.assertTrue(math.isinf(intensity_depth_nm(1,0)))
    def test_slab_limits_and_energy(self):
        for n in [1.,1.5,2.2,4.0026]:
            for alpha in [0.,.01,1.,100.]:
                d=incoherent_slab(n,alpha,5)
                self.assertAlmostEqual(d['total_R']+d['total_T']+d['total_A'],1)
                self.assertTrue(all(-1e-14<=d[x]<=1+1e-14 for x in ['total_R','total_T','total_A']))
                if alpha==0:self.assertAlmostEqual(d['total_T'],(1-surface_R(n))/(1+surface_R(n)))
        self.assertAlmostEqual(incoherent_slab(1,1,10)['total_T'],math.exp(-1))
    def test_void_model_limits(self):
        self.assertAlmostEqual(lorentz_lorenz_void(2.1,0),2.1)
        self.assertAlmostEqual(lorentz_lorenz_void(2.1,.1),1.9379787790323317)
        with self.assertRaises(ValueError):lorentz_lorenz_void(2.1,1)
    def test_frozen_examples_regression(self):
        self.assertEqual(examples(),read('worked_examples.json'))
        pts=examples()['metal_point_calculations']
        cu={r['dataset_id']:r for r in pts if r['material']=='Cu' and r['wavelength_um']==.6328}
        self.assertAlmostEqual(cu['Cu_Johnson']['R_semi_infinite_air'],.9183482069704898,places=8)
        self.assertAlmostEqual(cu['Cu_McPeak']['R_semi_infinite_air'],.9688893750464314,places=8)
    def test_original_hash_and_rebuild_if_local(self):
        files=[ROOT/r['local_original'] for r in read('local_originals_manifest.json')]
        if not all(x.exists() for x in files):self.skipTest('Originals intentionally local-only')
        self.assertEqual(build(),read('metal_nk_derived_points.json'))
if __name__=='__main__':unittest.main()
