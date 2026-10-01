#!/usr/bin/env python3
"""Read-only verification of the published research snapshot."""
from pathlib import Path
import hashlib
import json
import sys

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / '00_project/github_snapshot_manifest.json').read_text())
checks = []
for record in manifest['files']:
    path = root / record['path']
    ok = path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256']
    checks.append({'path': record['path'], 'passed': ok})
for path in root.rglob('*.json'):
    if '.git' not in path.parts:
        json.loads(path.read_text())
original = json.loads((root / '00_project/original_manifest.json').read_text())
checks.append({'path': original['archived_path'], 'passed': hashlib.sha256((root / original['archived_path']).read_bytes()).hexdigest() == original['sha256']})
excluded = [str(path.relative_to(root)) for path in root.rglob('*') if path.is_file() and 'sources' in path.parts and 'originals' in path.parts]
checks.append({'check': 'third_party_originals_excluded', 'passed': not excluded, 'unexpected_files': excluded})
result = {'all_passed': all(check['passed'] for check in checks), 'checked_files': len(manifest['files']), 'checks': checks}
print(json.dumps(result, ensure_ascii=False, indent=2))
sys.exit(0 if result['all_passed'] else 1)
