"""Verify delivered payload by exact path set and SHA-256; no network required."""
from pathlib import Path
import hashlib,json,sys
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text())
expected={x['path']:x for x in manifest['files']}
errors=[]
for rel,item in expected.items():
    path=root/rel
    if not path.is_file(): errors.append('missing: '+rel);continue
    data=path.read_bytes()
    if len(data)!=item['bytes'] or hashlib.sha256(data).hexdigest()!=item['sha256']:
        errors.append('mismatch: '+rel)
# Local archives may contain originals and receipts not distributed in the reader.
def excluded(p):
    r=p.relative_to(root)
    return ('originals' in r.parts or '__pycache__' in r.parts or p.suffix in ('.pyc','.zip') or str(r) in
            ('manifest.json','verification/frozen_topics_before.json','verification/library_upload_receipt.json','verification/freeze_receipt.json'))
actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and not excluded(p)}
for rel in sorted(actual-set(expected)): errors.append('unexpected: '+rel)
print(json.dumps({'passed':not errors,'payload_files':len(expected),'errors':errors},ensure_ascii=False,indent=2))
sys.exit(bool(errors))
