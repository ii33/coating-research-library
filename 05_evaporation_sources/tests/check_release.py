"""T05 structural/physics/provenance checks, core dependencies: NumPy+stdlib.
Not a general JSON-Schema engine; Source.validate enforces extra physical invariants.
"""
import argparse,hashlib,json,re,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'models'))
from source_reference import Source
parser=argparse.ArgumentParser();parser.add_argument('--reader',action='store_true');args=parser.parse_args()
checks=[]
def ck(value,what):
    if not value:raise AssertionError(what)
    checks.append(what)
load=lambda p:json.loads((ROOT/p).read_text())
reg=load('sources/source_registry.json');ids={x['source_id'] for x in reg}
ck(len(reg)==len(ids)==27,'27 unique source records')
for x in reg:
    ck((ROOT/x['summary_path']).is_file(),'source summary exists: '+x['source_id'])
    ck(x['url'].startswith('https://') and bool(x['read_scope']) and bool(x['limitations']),'source boundary recorded: '+x['source_id'])
    if x['original_path'] and not args.reader:
        p=ROOT/x['original_path'];ck(p.is_file(),'local original exists')
        ck(hashlib.sha256(p.read_bytes()).hexdigest()==x['original_sha256'],'local original hash matches')
        ck(x['rights']['archive_allowed'],'local original archival right documented')
mat=load('data/material_source_matrix.json')
ck(len(mat)==12 and len({x['material'] for x in mat})==12,'12 unique material/source records')
for x in mat:
    ck(set(x['source_ids'])<=ids,'material source references resolve: '+x['material'])
    ck((ROOT/x['t04_card']).is_file(),'T04 card exists: '+x['material'])
    ck(x['calibrated_exponent'] is None and x['production_settings'] is None,'unknown calibration not invented: '+x['material'])
snap=load('data/synthetic_source_snapshot.json');s=snap['source'];Source(np.array(s['nodes_m']),np.array(s['normals']),np.array(s['fractions']),s['exponent']).validate()
ck(snap['mass_rate_definition']=='intrinsic_hemispherical_pre_aperture','Q convention explicit')
ck(snap['mass_rate_kg_s']>=0 and snap['evidence_type']=='synthetic' and snap['validity']['machine_validated'] is False,'synthetic snapshot safely labelled')
report=list((ROOT/'reports').glob('*.md'));ck(len(report)==7,'seven report chapters')
for p in ROOT.rglob('*.md'):
    if '/originals/' in str(p):continue
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if target.startswith(('http:','https:','#')):continue
        target=target.split('#')[0]
        if target:ck((p.parent/target).exists(),'local link resolves: '+str(p.relative_to(ROOT))+' -> '+target)
for name in ['source_geometry','source_model_dataflow','synthetic_diagnostics']:
    for ext in ['png','svg']:ck((ROOT/'figures'/f'{name}.{ext}').is_file(),'figure exists: '+name+'.'+ext)
summary=load('benchmarks/results/benchmark_summary.json');ck(summary['point_fit']['heldout']['max_absolute_relative_percent']<5,'point heldout benchmark')
ck(summary['misspecified_point_for_disk']['heldout']['max_absolute_relative_percent']>100,'model discrepancy counterexample retained')
resolution=load('benchmarks/results/resolution_study.json');ck(resolution['disk'][2]['max_relative_percent_on_positive_nodes']<.01,'disk resolution evidence retained')
stage=load('stage_status.json');ck(stage['machine_validation']=='not_run' and stage['formal_status']=='awaiting_seed','verification claims bounded')
manifest=ROOT/'release_manifest.json'
if manifest.exists():
    for x in load('release_manifest.json')['files']:
        p=ROOT/x['path'];ck(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'],'release hash: '+x['path'])
print(json.dumps({'result':'PASS','checks':len(checks),'reader_mode':args.reader,'sources':len(reg),'materials':len(mat),'originals_checked':0 if args.reader else sum(bool(x['original_path']) for x in reg)},ensure_ascii=False,indent=2))
