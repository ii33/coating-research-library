#!/usr/bin/env python3
"""Readback/hash verification; optional bounded deterministic full rerun."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
sys.dont_write_bytecode = True
from calibration import STUDY, PROJECTS


def verify(rerun=False):
    manifest_path = STUDY / 'freeze_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    bad = [name for name, row in manifest['files'].items()
           if not (STUDY / name).is_file() or
           hashlib.sha256((STUDY / name).read_bytes()).hexdigest() != row['sha256']]
    if bad:
        raise RuntimeError('Study payload hash mismatch: ' + ', '.join(bad))
    baseline = json.loads((STUDY / 'results/runtime_sources_before.json').read_text())
    runtime_bad = [name for name, digest in baseline.items()
                   if not (PROJECTS.parent / name).is_file() or
                   hashlib.sha256((PROJECTS.parent / name).read_bytes()).hexdigest() != digest]
    if runtime_bad:
        raise RuntimeError('External runtime source changed: ' + ', '.join(runtime_bad))
    print(f'Payload {len(manifest["files"])} files verified; {len(baseline)} runtime/reference hashes unchanged')
    if rerun:
        import os
        env = {**os.environ, 'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1',
               'MKL_NUM_THREADS': '1', 'PYTHONDONTWRITEBYTECODE': '1'}
        subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', str(STUDY / 'tests'), '-v'],
                       cwd=STUDY, env=env, check=True)
        repetitions = json.loads((STUDY / 'results/study_results.json').read_text())['study_configuration']['repetitions_per_cell']
        with tempfile.TemporaryDirectory(prefix='bounded_readback_', dir=STUDY) as temporary:
            target = Path(temporary)
            subprocess.run([sys.executable, str(STUDY / 'run_study.py'), '--repetitions', str(repetitions),
                            '--output-dir', str(target)], cwd=STUDY, env=env, check=True)
            for name in ['representative_profiles.json', 'recovery_trials.csv', 'synthetic_input_contract.json', 'runtime_source_check.json']:
                if (target / name).read_bytes() != (STUDY / 'results' / name).read_bytes():
                    raise RuntimeError('Deterministic rerun mismatch: ' + name)
            old = json.loads((STUDY / 'results/study_results.json').read_text())
            new = json.loads((target / 'study_results.json').read_text())
            old['environment'].pop('elapsed_seconds'); new['environment'].pop('elapsed_seconds')
            if old != new:
                raise RuntimeError('Study semantic rerun mismatch')
            print('20 tests passed; full deterministic study rerun/readback matched except elapsed time')
    return {'payload_file_count': len(manifest['files']), 'runtime_file_count': len(baseline),
            'payload_hashes_match': True, 'runtime_sources_unchanged': True,
            'deterministic_rerun': bool(rerun)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--rerun', action='store_true')
    args = parser.parse_args()
    verify(args.rerun)
