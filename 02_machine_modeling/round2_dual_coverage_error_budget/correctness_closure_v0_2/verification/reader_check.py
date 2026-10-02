#!/usr/bin/env python3
"""Exact-list reader integrity check. Standard library, no ZIP/ancestor inputs.

--build writes only the self-excluding manifest. --check --reader is read-only.
Hashes establish integrity relative to this manifest, not publisher authenticity.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST = 'verification/public_allowlist.txt'
MANIFEST = 'verification/reader_manifest.json'
FORBIDDEN = {'__pycache__','cache','caches','archive','archives','originals',
             'credentials','secrets','deliverables'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def names_from_list():
    names = [x.strip() for x in (ROOT/ALLOWLIST).read_text().splitlines()
             if x.strip() and not x.lstrip().startswith('#')]
    if len(names)!=len(set(names)) or ALLOWLIST not in names or MANIFEST not in names:
        raise ValueError('list must be unique and include itself and manifest')
    for name in names:
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or str(path)!=name or '\\' in name:
            raise ValueError(f'unsafe public path: {name}')
        if any(part.lower() in FORBIDDEN for part in path.parts) or path.suffix.lower() in {'.zip','.pyc','.pyo'}:
            raise ValueError(f'excluded file category: {name}')
        current = ROOT
        for part in path.parts:
            current = current/part
            if current.is_symlink():
                raise ValueError(f'symlink is not a public reader file: {name}')
    return names


def main():
    parser=argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--build',action='store_true')
    group.add_argument('--check',action='store_true')
    parser.add_argument('--reader',action='store_true')
    args=parser.parse_args()
    if args.reader and not args.check:
        parser.error('--reader requires --check')
    names=names_from_list()
    if args.build:
        manifest={'schema':'T02R2-correctness-closure-reader-0.2',
          'allowlist_file_count':len(names),'manifest_self_exclusion':MANIFEST,
          'self_exclusion_reason':'No ordinary SHA-256 self-reference. Integrity hashes are not an authenticity signature.',
          'file_sha256':{name:digest(ROOT/name) for name in names if name!=MANIFEST}}
        (ROOT/MANIFEST).write_text(json.dumps(manifest,indent=2)+'\n')
    manifest=json.loads((ROOT/MANIFEST).read_text())
    if manifest['allowlist_file_count']!=len(names) or manifest['manifest_self_exclusion']!=MANIFEST:
        raise ValueError('manifest/list mismatch')
    if set(manifest['file_sha256'])!=set(names)-{MANIFEST}:
        raise ValueError('manifest file set mismatch')
    for name,expected in manifest['file_sha256'].items():
        if digest(ROOT/name)!=expected:
            raise ValueError(f'SHA-256 mismatch: {name}')
    print(json.dumps({'status':'pass','mode':'reader_files_only',
                      'explicit_file_count':len(names),'hashed_file_count':len(names)-1,
                      'zip_required':False,'parent_files_required':False,
                      'third_party_originals_required':False},indent=2))


if __name__=='__main__':
    main()
