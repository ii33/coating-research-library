#!/usr/bin/env python3
"""Copy final experiment artifacts away, then run each suite from an unrelated cwd."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
PACKAGES = ['batched-audit', 'lookahead', 'phase-guide']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', default=sys.executable,
                        help='Python with NumPy, SciPy and pytest installed')
    args = parser.parse_args()
    probe = subprocess.run([args.python, '-c',
                            'import json,platform,numpy,scipy,pytest; '
                            'print(json.dumps(dict(python=platform.python_version(), '
                            'numpy=numpy.__version__,scipy=scipy.__version__,pytest=pytest.__version__)))'],
                           text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if probe.returncode:
        raise SystemExit('Choose --python with NumPy, SciPy and pytest installed:\n'+probe.stdout)
    environment = json.loads(probe.stdout)
    started = time.perf_counter()
    rows = []
    logs = []
    with tempfile.TemporaryDirectory(prefix='coating-round2-portability-') as tmp:
        base = Path(tmp)
        unrelated = base/'unrelated-cwd'
        unrelated.mkdir()
        for name in PACKAGES:
            source = ROOT/name
            destination = base/'relocated'/name
            shutil.copytree(source, destination,
                            ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
            hashes = {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in sorted(source.rglob('*.py')) if '__pycache__' not in str(p)}
            equal = all(hashlib.sha256((destination/p).read_bytes()).hexdigest() == digest
                        for p, digest in hashes.items())
            tests = sorted(destination.glob('test_*.py'))
            command = [args.python, '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider']
            command += [str(p) for p in tests]
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
            start = time.perf_counter()
            run = subprocess.run(command, cwd=unrelated, env=env, text=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
            logs.append('\n### '+name+'\n'+run.stdout)
            generator = None
            if (destination/'write_report.py').exists():
                generated = subprocess.run([args.python, '-B', str(destination/'write_report.py')],
                                           cwd=unrelated, env=env, text=True,
                                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
                report_equal = hashlib.sha256((destination/'研究报告.md').read_bytes()).hexdigest() == hashlib.sha256((source/'研究报告.md').read_bytes()).hexdigest()
                generator = dict(returncode=generated.returncode, output=generated.stdout,
                                 generated_report_matches_frozen=report_equal,
                                 cwd='unrelated sibling directory')
                logs.append('\n### '+name+' relocated report generator\n'+generated.stdout)
            rows.append(dict(package=name, source_equal_after_copy=equal, source_sha256=hashes,
                             command=[str(Path(args.python).name), '-B', '-m', 'pytest', '-q',
                                      '-p', 'no:cacheprovider']+[p.name for p in tests],
                             cwd='unrelated sibling directory', returncode=run.returncode,
                             elapsed_seconds=time.perf_counter()-start, output=run.stdout,
                             relocated_report_generator=generator))
            print(name, run.returncode, run.stdout.strip().splitlines()[-1] if run.stdout.strip() else '', flush=True)
    out = dict(audit_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
               environment=environment,
               all_passed=all(x['returncode'] == 0 and x['source_equal_after_copy'] and
                              (x['relocated_report_generator'] is None or
                               (x['relocated_report_generator']['returncode'] == 0 and
                                x['relocated_report_generator']['generated_report_matches_frozen']))
                              for x in rows),
               suites=rows, wall_seconds=time.perf_counter()-started,
               scope='Relocated copies of experiment tests; no main-software certification.')
    (ROOT/'independent-tests.json').write_text(json.dumps(out, indent=2, ensure_ascii=False))
    (ROOT/'independent-tests.log').write_text(''.join(logs))
    if not out['all_passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
