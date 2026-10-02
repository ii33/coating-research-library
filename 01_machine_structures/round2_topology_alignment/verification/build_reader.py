"""Explicit-allowlist reader build/check. No third-party originals or caches."""
from pathlib import Path
import argparse,csv,hashlib,json,re,subprocess,sys,tempfile,zipfile
ROOT=Path(__file__).resolve().parents[1]
LIST=ROOT/'verification/public_allowlist.txt'
ARCHIVE=ROOT/'deliverables/T01_round2_topology_alignment_v0.1_reader.zip'


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def check(root, include_dependency_check=False):
    allowed=[x.strip() for x in (root/'verification/public_allowlist.txt').read_text().splitlines() if x.strip() and not x.startswith('#')]
    checks=[]
    assert len(allowed)==len(set(allowed)), 'duplicate allowlist entries'
    for f in allowed:
        p=Path(f)
        assert not p.is_absolute() and '..' not in p.parts, f
        assert p.suffix not in {'.pdf','.html','.pyc'} and '__pycache__' not in p.parts and 'originals' not in p.parts, f
        assert (root/p).is_file(), f'missing {f}'
    checks.append({'check':'explicit_allowlist_and_exclusions','pass':True,'files':len(allowed)})
    missing=[]
    for f in allowed:
        if f.endswith('.md'):
            text=(root/f).read_text()
            for link in re.findall(r'\]\(([^)]+)\)',text):
                link=link.split('#')[0]
                if not link or '://' in link: continue
                p=(root/f).parent/link
                if not p.exists(): missing.append({'document':f,'link':link})
    assert not missing,missing
    checks.append({'check':'local_markdown_links','pass':True})
    review=json.loads((root/'reviews/independent_math_check_results.json').read_text())
    hashes={p:sha(root/p)==h for p,h in review['input_sha256'].items()}
    assert all(hashes.values()),hashes
    checks.append({'check':'reviewed_input_hashes_unchanged','pass':True,'files':hashes})
    sys.path.insert(0,str(root/'models'))
    import numpy as np
    import dual_coverage as model
    summary=json.loads((root/'data/main_summary.json').read_text())
    for top,cases in summary.items():
        with (root/'data'/f'map_{top}.csv').open() as f: rows=list(csv.DictReader(f))
        assert len(rows)==1460*3, (top,len(rows))
        for case,expected in cases.items():
            rr=[r for r in rows if r['case']==case]
            weights=np.array([float(r['area_weight']) for r in rr])
            assert abs(weights.sum()-1)<1e-12
            for key,record in expected.items():
                values=np.array([float(r[key]) for r in rr]); got=model.statistics(values,weights)
                for statistic,value in record.items():
                    assert np.isclose(got[statistic],value,rtol=1e-12,atol=1e-12),(top,case,key,statistic)
            nn=np.array([float(r['net_atoms_m2']) for r in rr]);ii=np.array([float(r['ion_fluence_m2']) for r in rr])
            rat=np.array([float(r['ion_to_net_atom_ratio']) for r in rr]);energy=np.array([float(r['incident_energy_J_m2']) for r in rr])
            assert np.allclose(rat,ii/nn,rtol=1e-12)
            assert np.allclose(energy,ii*100*model.E_CHARGE,rtol=1e-12)
    checks.append({'check':'csv_summary_and_integral_units_reconciled','pass':True,'rows':13140})
    stage=json.loads((root/'round2_stage.json').read_text())
    access=json.loads((root/'sources/access_status.json').read_text())
    assert stage['all_structure_admission_gates_passed'] is False
    assert all(s['figure_pixels_read'] is False and s['structure_admission']=='unsupported_figure_gate' for s in access['sources'][1:])
    checks.append({'check':'source_gaps_remain_explicit','pass':True})
    num=json.loads((root/'verification/numerical_checks.json').read_text())
    assert num['run']['within_budget'] and num['run']['time_all_pass'] and num['run']['space_all_pass']
    checks.append({'check':'declared_sampled_numerics_record','pass':True,'scope':'record integrity, not reexecution of all numerical work'})
    r=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','verification','-v'],cwd=root,text=True,capture_output=True)
    assert r.returncode==0,r.stdout+r.stderr
    checks.append({'check':'unit_tests','pass':True,'output':r.stdout+r.stderr})
    if include_dependency_check:
        library=root.parents[1]
        deps=json.loads((root/'data/frozen_inputs.json').read_text())
        status={x['path']:sha(library/x['path'])==x['sha256'] for x in deps['files']}
        assert all(status.values()),status
        checks.append({'check':'frozen_inputs_unchanged','pass':True,'files':status})
    else:
        checks.append({'check':'frozen_inputs_unchanged','status':'not_checked','reason':'external read-only dependencies intentionally absent in standalone package'})
    return allowed,checks


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    is_library=(ROOT.parents[1]/'00_project/FIRST_SWEEP_REVIEW_DRAFT.md').exists()
    allowed,checks=check(ROOT,is_library)
    manifest={f:sha(ROOT/f) for f in allowed}
    if not args.check:
        ARCHIVE.parent.mkdir(exist_ok=True)
        with zipfile.ZipFile(ARCHIVE,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for f in allowed: z.write(ROOT/f,f)
            z.writestr('verification/reader_manifest.json',json.dumps(manifest,indent=2)+'\n')
        with zipfile.ZipFile(ARCHIVE) as z:
            assert set(z.namelist())==set(allowed)|{'verification/reader_manifest.json'}
            assert z.testzip() is None
            with tempfile.TemporaryDirectory(prefix='t01_r2_reader_') as tmp:
                z.extractall(tmp)
                for f,h in manifest.items(): assert sha(Path(tmp)/f)==h
                _,standalone_checks=check(Path(tmp),False)
        result={'pass':True,'archive':ARCHIVE.name,'sha256':sha(ARCHIVE),'size_bytes':ARCHIVE.stat().st_size,'files':len(allowed)+1,'checks':checks,'standalone_checks':standalone_checks,'scope':'packaging, declared-state integrity, link checks and 24 unit tests; not a full scientific/source audit'}
        (ROOT/'verification/release_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k not in ('checks','standalone_checks')},indent=2))
    else:
        man=ROOT/'verification/reader_manifest.json'
        if man.exists():
            expected=json.loads(man.read_text());assert all(sha(ROOT/f)==h for f,h in expected.items())
        print(json.dumps({'pass':True,'files':len(allowed),'checks':checks},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
