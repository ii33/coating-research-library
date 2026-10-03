"""Read-only portable integrity/navigation check; standard library only.

No source tree, original archive, network, subprocess, device or browser access.
Hashes establish internal integrity, not cryptographic authenticity.
"""
from pathlib import Path, PurePosixPath
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote
import argparse
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {'derived_manifest.json', 'derived_receipt.json'}
TEXT_SUFFIXES = {'.py', '.txt', '.json', '.md', '.html', '.svg', '.csv'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_path(value):
    if not isinstance(value, str) or not value or '\\' in value:
        raise ValueError('Invalid package-relative path')
    p = PurePosixPath(value)
    if p.is_absolute() or any(x in ('', '.', '..') for x in value.split('/')):
        raise ValueError('Unsafe package-relative path: ' + value)
    return value


class HTMLScan(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs, self.ids = [], []
        self.scripts, self.images = 0, 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.append(a['id'])
        if tag == 'script':
            self.scripts += 1
        if tag == 'img':
            self.images += 1
        for k in ('href', 'src'):
            if k in a:
                self.refs.append((tag, a[k]))
        if 'style' in a and re.search(r'url\s*\(', a['style'], re.I):
            self.refs.append(('runtime_style', a['style']))


def markdown_links(text):
    """Balanced parentheses, as used by bundled reports; no raw HTML renderer."""
    pattern = r'(!?)\[([^\]]+)\]\('
    end_at = 0
    for match in re.finditer(pattern, text):
        if match.start() < end_at:
            continue
        depth, end = 1, match.end()
        while end < len(text) and depth:
            if text[end] == '(':
                depth += 1
            elif text[end] == ')':
                depth -= 1
            end += 1
        if depth:
            raise ValueError('Unbalanced Markdown link')
        yield ('img' if match[1] else 'a'), text[match.end():end-1]
        end_at = end


def content_checks():
    issues, external = [], set()
    checked, refs_count, images, anchors = 0, 0, 0, 0
    local_refs, external_refs = 0, 0
    scans = {}
    for p in sorted(ROOT.rglob('*.html')):
        if p.is_symlink():
            issues.append('HTML symlink: ' + p.relative_to(ROOT).as_posix())
            continue
        scan = HTMLScan()
        text = p.read_text(encoding='utf-8')
        scan.feed(text)
        scans[p.resolve()] = scan
        if scan.scripts or len(scan.ids) != len(set(scan.ids)):
            issues.append('Script or duplicate HTML IDs: ' + p.name)
        if re.search(r'@import|url\s*\(', text, re.I):
            issues.append('Uninspected CSS runtime resource: ' + p.name)
        images += scan.images
        anchors += len(scan.ids)
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file() or p.is_symlink():
            continue
        rel = p.relative_to(ROOT).as_posix()
        if p.suffix in TEXT_SUFFIXES:
            text = p.read_text(encoding='utf-8')
            private_patterns = [r'libfile_[A-Za-z0-9]+', 'sedi' + 'ment://', r'https?://[^\s"<>]*(?:oaiusercontent\.com|blob\.core\.windows\.net|[?&](?:sig|X-Amz-Signature|access_token)=)', r'/(?:workspace|tmp|home|root)/[A-Za-z0-9_./-]+', r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']
            if any(re.search(pat, text, re.I) for pat in private_patterns):
                issues.append('Private identifier, private download link, machine path or key: ' + rel)
        if p.suffix not in {'.md', '.html'}:
            continue
        checked += 1
        refs = scans[p.resolve()].refs if p.suffix == '.html' else list(markdown_links(text))
        for tag, url in refs:
            refs_count += 1
            u = urlparse(url)
            if u.scheme or u.netloc:
                if u.scheme not in {'http', 'https', 'mailto'} or tag != 'a':
                    issues.append('Nonlocal runtime or unsafe URL: ' + rel + ': ' + url)
                else:
                    external.add(url)
                    external_refs += 1
                continue
            local_refs += 1
            target = (p.parent / unquote(u.path)).resolve() if u.path else p.resolve()
            if not target.is_relative_to(ROOT) or not target.is_file():
                issues.append('Missing/escaping local link: ' + rel + ': ' + url)
            elif u.fragment:
                scan = scans.get(target)
                if scan is None or unquote(u.fragment) not in scan.ids:
                    issues.append('Unchecked/missing local anchor: ' + rel + ': ' + url)
    return {'status': 'passed' if not issues else 'failed', 'issues': issues,
            'html_and_markdown_files': checked, 'link_references_checked': refs_count,
            'local_link_references_checked': local_refs,
            'external_bibliographic_link_occurrences': external_refs,
            'main_reader_images': images, 'html_anchors': anchors,
            'external_bibliographic_urls_not_fetched': len(external),
            'browser_layout': 'unverified; previously denied route not retried'}


def verify():
    issues = []
    manifest = json.loads((ROOT / 'derived_manifest.json').read_text())
    receipt = json.loads((ROOT / 'derived_receipt.json').read_text())
    if manifest['schema'] != 't10-portable-derived-manifest-v1':
        issues.append('Unknown manifest schema')
    if set(manifest['excluded']) != EXCLUDED:
        issues.append('Unexpected circular-hash exclusions')
    files = manifest['files']
    paths = [relative_path(e['path']) for e in files]
    if len(paths) != len(set(paths)):
        issues.append('Duplicate payload paths')
    actual = set()
    for p in ROOT.rglob('*'):
        rel = p.relative_to(ROOT).as_posix()
        if p.is_symlink():
            issues.append('Symlink forbidden: ' + rel)
        elif p.is_file():
            actual.add(rel)
            if p.suffix in {'.zip', '.pdf', '.pyc'} or '__pycache__' in p.parts or '.git' in p.parts:
                issues.append('Excluded archive/original/cache present: ' + rel)
    expected = set(paths) | EXCLUDED
    if actual != expected:
        issues.append('Exact package path mismatch: ' + json.dumps({'missing': sorted(expected-actual), 'extra': sorted(actual-expected)}))
    for entry in files:
        p = ROOT / entry['path']
        if p.is_symlink() or not p.is_file() or p.stat().st_size != entry['bytes'] or sha(p) != entry['sha256']:
            issues.append('Payload mismatch: ' + entry['path'])
    allowed = (ROOT / 'PUBLICATION_ALLOWLIST.txt').read_text().splitlines()
    if len(allowed) != len(set(allowed)) or set(allowed) != expected or allowed != sorted(allowed):
        issues.append('Publication allowlist mismatch')
    if sha(ROOT / 'derived_manifest.json') != receipt['derived_manifest_sha256']:
        issues.append('Derived receipt/manifest mismatch')
    if receipt['package_id'] != manifest['package_id'] or receipt['payload_files'] != len(files):
        issues.append('Derived receipt identity/count mismatch')
    source_map = json.loads((ROOT / 'DERIVATION_MAP.json').read_text())
    src_paths = [r['source_path'] for r in source_map['source_files']]
    if len(src_paths) != len(set(src_paths)):
        issues.append('Duplicate source mapping')
    mapped = set()
    for row in source_map['source_files']:
        dp = row['derived_path']
        if dp is None:
            if row['derived_sha256'] is not None:
                issues.append('Excluded source has derived hash')
            continue
        dp = relative_path(dp)
        if dp in mapped:
            issues.append('Duplicate derived mapping: ' + dp)
        mapped.add(dp)
        p = ROOT / dp
        if not p.is_file() or p.is_symlink() or sha(p) != row['derived_sha256']:
            issues.append('Derived provenance mismatch: ' + dp)
        if row['transformation'] in {'byte_identical', 'historical_relocation', 'byte_identical_supplement'} and row['source_sha256'] != row['derived_sha256']:
            issues.append('Invalid byte-identical claim: ' + dp)
    generated = {relative_path(r['derived_path']) for r in source_map['generated_files']}
    if mapped & generated or mapped | generated != expected:
        issues.append('Full derivation/generated provenance coverage mismatch')
    for row in json.loads((ROOT / 'dependencies/provenance.json').read_text())['dependencies']:
        if row['derived_path']:
            p = ROOT / relative_path(row['derived_path'])
            if not p.is_file() or p.is_symlink() or sha(p) != row['derived_sha256']:
                issues.append('Local dependency provenance mismatch: ' + row['derived_path'])
    content = content_checks()
    issues += content['issues']
    return {'status': 'passed' if not issues else 'failed', 'package_id': manifest['package_id'],
            'derived_manifest_sha256': sha(ROOT / 'derived_manifest.json'),
            'payload_files': len(files), 'allowlisted_files': len(expected),
            'historical_source_manifest_sha256': source_map['source_manifest_sha256'],
            'issues': issues, 'content': content,
            'scope': 'Current package only. No original archive, receipt, sibling, snapshot, network or browser required.',
            'authenticity': 'Unsigned integrity ledger; not proof of origin or scientific correctness.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true', required=True)
    parser.parse_args()
    try:
        result = verify()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result = {'status': 'failed', 'issues': [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
