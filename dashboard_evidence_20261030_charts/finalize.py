"""Verify evidence completeness and write an artifact manifest on the host."""
import hashlib
import json
from pathlib import Path
import re

EVIDENCE = Path(__file__).resolve().parent
ROOT = EVIDENCE.parent
read = lambda path: json.loads(path.read_text(encoding='utf-8-sig'))
verification = read(EVIDENCE / 'verification.json')
assert verification['business_logic_ast_unchanged']
assert verification['frozen_database_unchanged']
assert len(verification['pages']) == 16
assert len(read(EVIDENCE / 'before/browser-results.json')) == 12
assert len(read(EVIDENCE / 'after/browser-results.json')) == 48
assert all(r['passed'] for r in read(EVIDENCE / 'edges/results.json'))
assert all(r['passed'] for r in read(EVIDENCE / 'docker/results.json'))
assert '14 passed' in (EVIDENCE / 'test-results.txt').read_text()
assert (EVIDENCE / 'comparison-results.txt').read_text().startswith('PASS:')
for row in read(EVIDENCE / 'deployment-verification.json'):
    if 'streamlit' not in row['Name']:
        assert row['ContainerIdUnchanged'] and row['StartedAtUnchanged']
for row in read(EVIDENCE / 'runtime-source-verification.json'):
    assert hashlib.sha256((ROOT / 'dashboard' / row['File']).read_bytes()).hexdigest() == row['Sha256']
for doc in [ROOT / 'dashboard-chart-improvements.md', EVIDENCE / 'README.md']:
    for target in re.findall(r'\]\(([^)]+)\)', doc.read_text(encoding='utf-8')):
        if not target.startswith(('http:', 'https:', '#')):
            assert (doc.parent / target).exists(), target
files = [p for p in EVIDENCE.rglob('*') if p.is_file() and p.name != 'artifact-manifest.json']
files.append(ROOT / 'dashboard-chart-improvements.md')
manifest = {str(p.relative_to(ROOT)).replace('\\', '/'): dict(
    bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(files)}
(EVIDENCE / 'artifact-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(f'PASS: final evidence complete, {len(manifest)} artifacts, all report links resolve, deployed source matches')
