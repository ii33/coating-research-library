#!/usr/bin/env python3
"""Read-only checks of the topic registry, local links and ideal gear equations."""
from pathlib import Path
from fractions import Fraction as F
import hashlib,json,re,subprocess,sys,argparse
B=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--reader',action='store_true',help='Check authored reader package, explicitly skip excluded source originals')
args=parser.parse_args()
checks=[]
def check(name,condition,detail=''):
    checks.append({'name':name,'passed':bool(condition),'detail':detail})
reg=json.loads((B/'sources/source_registry.json').read_text())
ids={r['source_id'] for r in reg}
check('source_ids_unique',len(ids)==len(reg))
for r in reg:
    if r['original_path']:
        p=B/r['original_path']
        if args.reader and not p.exists():
            checks.append({'name':r['source_id']+'_original_archive','passed':None,'status':'skipped_original_excluded','detail':'Original PDF excluded from reader distribution; archived checksum retained, local bytes not verified.'})
            continue
        check(r['source_id']+'_archive_exists',p.is_file())
        check(r['source_id']+'_pdf_signature',p.read_bytes().startswith(b'%PDF'))
        check(r['source_id']+'_sha256',hashlib.sha256(p.read_bytes()).hexdigest()==r['original_sha256'])
        check(r['source_id']+'_archive_rights_recorded',r['rights']['archive_allowed'] is True and bool(r['rights']['basis']))
for p in B.rglob('*.json'):
    if p.name!='initial_release_checks.json':json.loads(p.read_text())
for p in B.rglob('*.md'):
    for dest in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if not re.match(r'^[a-z]+://',dest) and not dest.startswith('#'):
            check(str(p.relative_to(B))+' link '+dest,(p.parent/dest.split('#')[0]).exists())
for zp in [36,37]:
    zs=120;wc=F(15);ws=F(0);wp=wc+F(zs,zp)*(wc-ws)
    # Independently use pitch-circle contact velocity with module 1 length unit.
    rs=F(zs,2);rp=F(zp,2);R=rs+rp
    check(f'{zp}_contact_no_slip',R*wc-rp*wp-rs*ws==0)
    check(f'{zp}_relative_external_mesh',zs*(ws-wc)+zp*(wp-wc)==0)
    wrong=F(zs,zp)*wc
    check(f'{zp}_reject_missing_carrier_term',R*wc-rp*wrong!=0)
    ratio=wp/wc;N=ratio.denominator
    check(f'{zp}_pose_closes',(N*ratio).denominator==1)
    check(f'{zp}_no_smaller_integer_orbit_closure',all((n*ratio).denominator!=1 for n in range(1,N)))
    # General moving sun check, plus common rigid rotation limit.
    for ws_test in [F(-10),F(15),F(20)]:
        wp_test=wc+F(zs,zp)*(wc-ws_test)
        check(f'{zp}_moving_sun_{ws_test}',R*wc-rp*wp_test-rs*ws_test==0)
    check(f'{zp}_rigid_rotation_limit',wc+F(zs,zp)*(wc-wc)==wc)
output=subprocess.check_output([sys.executable,str(B/'reviews/planetary_kinematics_check.py')],text=True)
check('independent_script_reproduces_json',json.loads(output)==json.loads((B/'reviews/planetary_kinematics_results.json').read_text()))
try:
 import jsonschema
 schema=json.loads((B/'sources/source_record.schema.json').read_text())
 for r in reg:jsonschema.validate(r,schema)
 check('local_source_schema',True)
except Exception as e:check('local_source_schema',False,str(e))
result={'checked_at_utc':'2026-10-01','scope':'file integrity, source schema, local links, ideal kinematics only; no physical deposition validation','mode':'reader' if args.reader else 'full_archive','all_passed':all(c['passed'] is not False for c in checks),'passed_count':sum(c['passed'] is True for c in checks),'skipped_count':sum(c['passed'] is None for c in checks),'checks':checks}
print(json.dumps(result,ensure_ascii=False,indent=2))
sys.exit(0 if result['all_passed'] else 1)
