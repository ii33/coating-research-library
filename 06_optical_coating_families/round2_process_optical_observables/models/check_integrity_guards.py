"""Tiny tamper/path negative checks in temporary copies, no code execution."""
import copy,json,shutil,tempfile
from pathlib import Path
from process_optics import ROOT
from reader import verify

def run():
 results={}
 for mode in ['modified_payload','extra_file','missing_file','duplicate_manifest_path','unsafe_manifest_path','symlink']:
  with tempfile.TemporaryDirectory(prefix='t06-tamper-') as td:
   r=Path(td)/'copy';shutil.copytree(ROOT,r,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
   if mode=='modified_payload':(r/'README.md').write_text('tamper')
   if mode=='extra_file':(r/'unexpected.txt').write_text('extra')
   if mode=='missing_file':(r/'README.md').unlink()
   if mode in ['duplicate_manifest_path','unsafe_manifest_path']:
    p=r/'freeze_manifest.json';m=json.loads(p.read_text())
    if mode=='duplicate_manifest_path':m['files'].append(copy.deepcopy(m['files'][0]))
    else:m['files'][0]['path']='../escape'
    p.write_text(json.dumps(m))
   if mode=='symlink':(r/'unexpected_link').symlink_to(r/'README.md')
   try:verify(r,recompute=False)
   except ValueError as e:results[mode]={'status':'rejected_as_expected','reason':str(e).replace(str(r),'<copy>')}
   else:raise AssertionError('integrity guard missed '+mode)
 return {'status':'passed','checks':results,'scope':'accidental corruption/path defense; attacker able to rewrite all payload+manifest is not authenticated'}
if __name__=='__main__':print(json.dumps(run(),indent=2))
