#!/usr/bin/env python3
"""Validate T07 local structure, numerical evidence, dependencies and publication exclusions."""
from pathlib import Path
import argparse,csv,hashlib,json,re,xml.etree.ElementTree as ET
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--reader',action='store_true',help='Validate published reader package without checking private local original files or their hashes')
args=parser.parse_args()
checks=[]
def ck(name,ok,detail=''):checks.append(dict(check=name,passed=bool(ok),detail=detail))
src=json.loads((ROOT/'data/source_registry.json').read_text())['sources'];ids={s['id'] for s in src}
ck('18 distinct primary or official sources',len(src)==18 and len(ids)==18)
ck('every source has card, scope, locator, limit',all((ROOT/s['summary_path']).is_file() and all(s.get(k) for k in ['read_extent','locator','limitations','original_archival_status','url']) for s in src))
originals=[s for s in src if s['local_original']]
if args.reader:
 ck('4 archival originals registered; raw-file checks skipped in reader mode',len(originals)==4,'Reader publication excludes all originals; presence and file hashes were not checked.')
else:
 ck('4 local originals exist with matching hashes',len(originals)==4 and all((ROOT/'sources/originals'/s['local_original']).is_file() and hashlib.sha256((ROOT/'sources/originals'/s['local_original']).read_bytes()).hexdigest()==s['sha256'] for s in originals),'Full local archival check; use --reader for published packages.')
ck('9 narrative chapters',len([p for p in (ROOT/'reports').glob('*.md') if re.match(r'0[1-9]_',p.name)])==9)
with (ROOT/'data/formula_index.csv').open() as f:forms=list(csv.DictReader(f))
ck('32 formula entries with units assumptions evidence',len(forms)==32 and all(x['units'] and x['assumptions'] and x['evidence'] for x in forms))
bad=[];cites=set()
for p in ROOT.rglob('*.md'):
 if 'originals' in p.parts and p.name!='README.md':continue
 t=p.read_text();cites.update(re.findall(r'\[(S\d{2})(?:\s|\])',t))
 for u in re.findall(r'\]\(([^)]+)\)',t):
  if '://' in u or u.startswith(('#','mailto:')):continue
  u=u.split('#')[0]
  if u and not (p.parent/u).exists():bad.append((str(p.relative_to(ROOT)),u))
ck('all local Markdown links resolve',not bad,str(bad));ck('all source IDs registered',cites<=ids,str(sorted(cites-ids)))
r=json.loads((ROOT/'data/example_results.json').read_text())
ck('synthetic not measured status explicit',r['status']=='synthetic_theory_examples_not_measured')
ck('W01 ideal AR and material-limited residual',r['W01_AR']['R_at_center_ideal']<1e-25 and .01<r['W01_AR']['R_at_center_available_index']<.02)
ck('W03 stable finite opaque limit and naive failure',all(np.isfinite(v['R_s']+v['T_s']+v['A_s']) for v in r['W03_stability']['rows']) and r['W03_stability']['rows'][-1]['naive_finite'] is False)
ck('W04 phase mean matches intensity sum',abs(r['W04_incoherence']['phase_ensemble_T']-12/13)<1e-12 and r['W04_incoherence']['incorrect_average_amplitude_power']<1e-25)
ck('W05 GD analytic agreement',abs(r['W05_cavity']['center_GD_fs']-r['W05_cavity']['analytic_center_GD_fs'])<1e-5)
ck('W05 absorbed density vs flux',abs(r['W05_layer_absorption']['finite_layer_A']-r['W05_layer_absorption']['density_integral'])<5e-8)
ck('W06 equivalent matrix reconstruction',max(x['reconstruction_error'] for x in r['W06_equivalent_layer']['rows'])<2e-13)
errs=[x['max_absolute_R_error_vs_640'] for x in r['W07_gradient']['rows']]
ck('W07 slicing converges over reported sequence',all(b<a for a,b in zip(errs,errs[1:])) and errs[-1]<2e-8)
v=r['W08_sensitivity']
ck('W08 illustrative Monte Carlo agrees with local covariance to 5 percent',all(abs(v['MC_std_T_'+k]/v['linear_sigma_T_'+k]-1)<.05 for k in ['independent','common']))
comp=r['T06_crosscheck']['rows']
ck('28 T06 crosschecks within 5e-11',len(comp)==28 and max(x['max_abs_r_difference'] for x in comp)<5e-11 and max(x['max_abs_T_difference'] for x in comp)<5e-11)
deps=json.loads((ROOT/'data/t06_dependency_manifest.json').read_text());prev=ROOT.parent/'06_optical_coating_families'
ck('T06 frozen dependencies unchanged',all(hashlib.sha256((prev/p).read_bytes()).hexdigest()==h for p,h in deps.items()))
svgs=list((ROOT/'figures').glob('*.svg'))
for f in svgs:ET.parse(f)
ck('4 SVG figures with PNG previews',len(svgs)==4 and all((ROOT/'reviews'/(f.stem+'_preview.png')).is_file() for f in svgs))
log=(ROOT/'reviews/test_output.txt').read_text();ck('28 unit tests passed',re.search(r'Ran 28 tests',log) is not None and log.rstrip().endswith('OK'))
ck('T08 handoff and contract present',(ROOT/'T08_HANDOFF.md').is_file() and (ROOT/'data/design_theory_contract.json').is_file())
ck('originals exclusion rule explicit','sources/originals/*' in (ROOT/'.gitignore').read_text())
result=dict(passed=all(x['passed'] for x in checks),mode='reader' if args.reader else 'full_local_archive',scope='local package and frozen numerical evidence; no HTTP, production or external review certification',checks=checks)
(ROOT/'reviews/package_check_output.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(0 if result['passed'] else 1)
