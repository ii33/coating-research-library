"""Offline reader: exact manifest, safe ZIP, archived examples and regression checks."""
import argparse,hashlib,json,os,subprocess,sys,tempfile,zipfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE='T04_round2_material_response_contract_reader.zip'
EXCLUDED={'freeze_manifest.json',ARCHIVE,'verification/freeze_receipt.json','verification/unchanged_baseline.json'}
def included(path):return path not in EXCLUDED and '__pycache__' not in PurePosixPath(path).parts and not path.endswith('.pyc')
def digest(data):return hashlib.sha256(data).hexdigest()
def paths(root):return sorted(str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and included(str(p.relative_to(root))))
def verify_directory(root,run_tests=True):
    manifest=json.loads((root/'freeze_manifest.json').read_text());items=manifest['files'];names=[x['path'] for x in items]
    if len(names)!=len(set(names)):raise ValueError('duplicate manifest path')
    if paths(root)!=sorted(names):raise ValueError('manifest file set mismatch')
    for i in items:
        data=(root/i['path']).read_bytes()
        if len(data)!=i['bytes'] or digest(data)!=i['sha256']:raise ValueError('payload mismatch '+i['path'])
    # Core imported only from this reader tree; no upstream code/data is imported.
    sys.path.insert(0,str(root/'models'))
    from contract import calculate,validate
    expected=json.loads((root/'verification/example_results.json').read_text());n=0
    for p in sorted((root/'examples').glob('*.json')):
        r=json.loads(p.read_text());errs=validate(r)
        if errs:raise ValueError(str(errs))
        if calculate(r)!=expected[p.stem]:raise ValueError('archived calculation mismatch '+p.name)
        n+=1
    idx=json.loads((root/'data/inherited_evidence_index.json').read_text())
    source=json.loads((root/'sources/source_registry.json').read_text());idx['MR_SOURCE']={s['source_id']:s for s in source['sources']}
    mapped=json.loads((root/'data/priority_material_mapping.json').read_text());refs=0;ids=[]
    for m in mapped['materials']:
        ids+=m['T04_property_record_ids']
        for f in m['fields'].values():
            for ref in f['evidence_refs']:
                space,key=ref.split(':',1)
                if key not in idx[space]:raise ValueError('unresolved mapping evidence '+ref)
                refs+=1
    if len(ids)!=207 or len(set(ids))!=207 or len(mapped['materials'])!=16:raise ValueError('mapping completeness mismatch')
    if any(s.get('original_saved') for s in source['sources']):raise ValueError('originals unexpectedly saved')
    for s in source['sources']:
        if not (root/s['summary_path']).is_file():raise ValueError('missing source summary')
    result={'status':'pass','payload_files':len(items),'validated_examples':n,'mapped_parameters':len(ids),'resolved_field_references':refs,
      'source_cards':len(source['sources']),'original_documents_required':False,'network_required':False,
      'reader_dependencies':'Python standard library only','scope':'exact payload integrity and implementation checks; not experimental validity or source-original authentication'}
    if run_tests:
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
        p=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=root,env=env,capture_output=True,text=True,timeout=60)
        result['tests_returncode']=p.returncode;result['tests_tail']=p.stderr.strip().splitlines()[-4:]
        if p.returncode:raise ValueError('tests failed\n'+p.stdout+p.stderr)
    return result

def verify_zip(path):
    with zipfile.ZipFile(path) as z:
        infos=z.infolist();names=[i.filename for i in infos]
        if len(names)!=len(set(names)):raise ValueError('duplicate ZIP path')
        if any(PurePosixPath(n).is_absolute() or '..' in PurePosixPath(n).parts or '\\' in n for n in names):raise ValueError('unsafe ZIP path')
        if any((i.external_attr>>16)&0o170000==0o120000 for i in infos):raise ValueError('ZIP symlink forbidden')
        if sum(i.file_size for i in infos)>50_000_000:raise ValueError('unexpected ZIP expansion')
        if z.testzip():raise ValueError('ZIP CRC failed')
        manifest=json.loads(z.read('freeze_manifest.json'));expected={x['path'] for x in manifest['files']}|{'freeze_manifest.json'}
        if set(names)!=expected:raise ValueError('ZIP exact entries mismatch')
        for r in manifest['files']:
            b=z.read(r['path'])
            if len(b)!=r['bytes'] or digest(b)!=r['sha256']:raise ValueError('ZIP payload hash mismatch')
        with tempfile.TemporaryDirectory(prefix='t04r2_reader_') as tmp:
            z.extractall(tmp)
            p=subprocess.run([sys.executable,str(Path(tmp)/'models/reader.py'),'--directory',tmp],cwd=tmp,
              env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True,timeout=90)
            if p.returncode:raise ValueError('isolated reader failed: '+p.stdout+p.stderr)
            result=json.loads(p.stdout);result['isolated_zip_reader']=True;result['archive_sha256']=digest(path.read_bytes());return result
if __name__=='__main__':
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group(required=True);g.add_argument('--directory');g.add_argument('--zip');a=ap.parse_args()
    try:r=verify_zip(Path(a.zip).resolve()) if a.zip else verify_directory(Path(a.directory).resolve())
    except Exception as e:print(json.dumps({'status':'fail','error':str(e)},ensure_ascii=False,indent=2));raise SystemExit(1)
    print(json.dumps(r,ensure_ascii=False,indent=2))
