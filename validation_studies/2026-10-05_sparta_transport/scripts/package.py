#!/usr/bin/env python3
"""Produce a bounded reproducibility bundle without redistributing solver binaries."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib,json,zipfile
import study

R=study.ROOT
class Audit(HTMLParser):
    def __init__(self):super().__init__();self.h1=0;self.external_assets=[];self.tables=0;self.links=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='h1':self.h1+=1
        if tag=='table':self.tables+=1
        if tag in ['script','img','link'] and ('src' in a or 'href' in a):self.external_assets.append(a)
        if tag=='a':self.links.append(a.get('href',''))

audit=Audit();audit.feed((R/'docs/transport_validation.html').read_text());assert audit.h1==1 and audit.tables==2 and not audit.external_assets
study.save(R/'provenance/report_quality.json',{'offline_html_structure_pass':True,'headline_count':audit.h1,'table_count':audit.tables,'external_assets':audit.external_assets,'scientific_plot_pixels_inspected':True,'full_browser_render':'BLOCKED: runtime socket Operation not permitted; logs/report_render.log retained','no_browser_visual_acceptance_claim':True})
summary=json.loads((R/'results/validation_summary.json').read_text())
study.save(R/'RUN_STATUS.json',{'status':'bounded_synthetic_method_validation_completed','checks_passed':summary['all_checks_passed'],'case_groups':{'thermal_surface_injection':1,'collisionnone_finite_source_geometry':12,'periodic_bath_and_two_refinement_levels':17,'additional_independent_seed_bath_replicates':8},'total_real_SPARTA_cases':38,'upstream_source_unmodified':True,'physical_equipment_prediction':False,'zero_collision_fraction':'measured from complete every-step collision histories','finite_receiver_scattered_flux':'NEVER RUN','double_masks_and_planetary_motion':'NEVER RUN','real_material_background_cross_sections':'UNAVAILABLE','browser_preview':'BLOCKED; offline structure and chart pixels checked','report':'docs/transport_validation.html','checker':'scripts/check_results.py','summary':'results/validation_summary.json'})
(R/'results/failed_attempts/README.md').write_text('''# Retained failed or superseded attempts

These files are evidence, not validation passes.

- geometry_vanish_incomplete_tally: real collisionnone run used vanish and surf/collision/tally. Surface tallies did not match nscoll; full conservation audit rejected it. The pinned upstream vanish implementation does not set the reaction output flag; collision tally also has null-pointer hazards. Final geometry uses specular + surf_react global 1 0 and reaction tally.
- static_mesh40_insufficient_initial_majorant.json: the first low-initial-majorant fine-grid result P0=0.9236 versus 0.904837 failed the 4-sigma threshold. All final bath decks initialize the collision majorant using a 4800K collision mixture while actual created distributions remain separately specified.
- thermal_equal_mass_feedback: initial equal-mass thermal bath heated and acquired drift from the tracer pulse. It was not a maintained thermal reference. Final thermal tests use a deliberately synthetic heavy/hot bath that preserves the velocity scale and makes feedback negligible.
- First emit/surf + collision tally run on the emitting surface terminated with signal 11. The parent tool return recorded it; the echo/debug log is preserved as emitter_tally_null_debug.log when available. Input was adjusted without editing upstream solver source.

No failed attempt is included in results/validation_summary.json.
''')
debug=R/'results/injection/debug.log'
if debug.exists():(R/'results/failed_attempts/emitter_tally_null_debug.log').write_bytes(debug.read_bytes())

manifest=[]
for group in ['inputs','scripts','provenance','results','logs']:
    for path in sorted((R/group).rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts and path.name!='file_manifest.json':
            manifest.append({'path':str(path.relative_to(R)),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
for path in [R/'README.md',R/'RUN_STATUS.json',R/'docs/transport_validation.html']:
    manifest.append({'path':str(path.relative_to(R)),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
study.save(R/'provenance/file_manifest.json',{'hash_algorithm':'sha256','scope':'all study input/scripts/logs/results and deliverable report, including full raw event traces; excludes official vendor tree and report cache','files':manifest})

archive=R/'SPARTA_transport_validation_2026-10-05.zip'
paths=[R/'README.md',R/'RUN_STATUS.json',R/'docs/transport_validation.html']
for group in ['inputs','scripts','provenance','logs']:
    paths.extend(p for p in (R/group).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
paths.extend(p for p in (R/'results').rglob('*') if p.is_file() and p.suffix in ['.json','.csv','.md'] or p.is_file() and p.name in ['in.sparta','log.sparta','console.log','emitter_tally_null_debug.log'])
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for path in sorted(set(paths)):z.write(path,str(path.relative_to(R)))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
study.save(R/'provenance/package_readback.json',{'archive':archive.name,'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'zip_integrity_pass':True,'raw_event_traces':'full study folder only; re-create by running study.py','SPARTA_binary_included':False,'SPARTA_official_source_included':False,'pinned_upstream_commit':json.loads((R/'provenance/source_build.json').read_text())['pinned_commit']})
print(archive,archive.stat().st_size)
