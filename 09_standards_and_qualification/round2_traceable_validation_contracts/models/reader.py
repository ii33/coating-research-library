"""Read-only reader payload verification, optionally copying to a disposable local folder.
No hardware, network, full inversion, or production qualification.
"""
import argparse,hashlib,json,shutil,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root,strict=False):
 m=json.loads((root/'reader_manifest.json').read_text());expected={r['path']:r for r in m['files']};missing=[];changed=[]
 for name,r in expected.items():
  p=root/name
  if not p.is_file():missing.append(name)
  elif p.stat().st_size!=r['bytes'] or digest(p)!=r['sha256']:changed.append(name)
 expected_paths=set(expected)|{'reader_manifest.json'}
 actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
 extra=sorted(actual-expected_paths) if strict else []
 allow=json.loads((root/'data/reader_allowlist.json').read_text())['paths']
 allow_matches=set(allow)==expected_paths
 return {'reader_payload_ok':not(missing or changed or extra) and allow_matches,'missing':missing,'changed':changed,'extra_in_strict_mode':extra,'allowlist_manifest_equal':allow_matches,'payload_files':len(expected_paths),'strict_isolated':strict,'visual_check':'not_run_blocked','normative_or_hardware_validation':False}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--directory',type=Path,default=ROOT);ap.add_argument('--isolated',action='store_true');a=ap.parse_args();root=a.directory.resolve()
 if a.isolated:
  allow=json.loads((root/'data/reader_allowlist.json').read_text())['paths']
  with tempfile.TemporaryDirectory(prefix='reader_check_',dir=ROOT/'reviews') as tmp:
   tmp=Path(tmp)
   for name in allow:
    src=root/name;dest=tmp/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
   result=verify(tmp,True)
 else:result=verify(root)
 print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(0 if result['reader_payload_ok'] else 1)
