"""Final invariants, artifact hashes, and encoding normalization for evidence."""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from bson import json_util
from pymongo import MongoClient

OUT = Path('/evidence')
ROOT = Path('/workspace')
client = MongoClient(os.environ['MONGO_URI'], tz_aware=True)
snap = json_util.loads((OUT/'snapshot.json').read_text())
consistency = json.loads((OUT/'snapshot-consistency.json').read_text())
rid = snap['run_id']
source_checks = {}
evidence_checks = {}
for name, before in consistency['before']['collections'].items():
    query = {'_id': 'spark'} if name == 'system_metrics' else (
        {'_id': rid} if name == 'evaluation_totals' else {'run_id': rid})
    rows = list(client.paysim[name].find(query).sort('_id', 1))
    digest = hashlib.sha256(json_util.dumps(rows, sort_keys=True).encode('utf-8')).hexdigest()
    source_checks[name] = {'before': before, 'after': {'count': len(rows), 'sha256': digest},
                           'unchanged': before == {'count': len(rows), 'sha256': digest}}
    normalize = lambda docs: sorted(json_util.dumps(r, sort_keys=True) for r in docs)
    evidence_checks[name] = normalize(list(client[snap['database']][name].find())) == normalize(snap['collections'][name])
(OUT/'post-capture-database-checks.json').write_text(json.dumps({
    'source_checks': source_checks, 'evidence_checks': evidence_checks}, indent=2), encoding='utf-8')
# The live stack restarted after copy. Its source may advance; the isolated
# evidence database MUST still be identical to the accepted frozen snapshot.
assert all(evidence_checks.values())

initial = json.loads((OUT/'environment.json').read_text())['source_sha256']
hashes = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in initial}
assert all(hashes[name] == digest for name, digest in initial.items() if name != 'dashboard/app.py')

# PowerShell 5 redirects native output as UTF-16; make artifacts portable UTF-8.
for path in OUT.iterdir():
    if path.is_file() and path.suffix in ['.txt', '.json', '.diff']:
        raw = path.read_bytes()
        if raw.startswith(b'\xff\xfe'):
            suffix = b''
            # The first pytest command appended its exit code using UTF-8.
            marker = raw.rfind(b'\nEXIT_CODE=')
            if marker != -1:
                raw, suffix = raw[:marker], raw[marker:]
            text = raw.decode('utf-16') + suffix.decode('utf-8')
            path.write_text(text, encoding='utf-8')
        if path.name.startswith('services-') and path.suffix == '.json':
            text = path.read_text(encoding='utf-8')
            try:
                json.loads(text)
            except json.JSONDecodeError:
                path.write_text(json.dumps([json.loads(line) for line in text.splitlines() if line.strip()],
                                           ensure_ascii=False, indent=2), encoding='utf-8')

test_text = (OUT/'test-results.txt').read_text(encoding='utf-8')
assert '7 passed' in test_text and 'EXIT_CODE=0' in test_text
results = json.loads((OUT/'browser-results.json').read_text())
assert len(results) == 32 and all(r['six_kpis_equal_before'] for r in results)
pngs = list((OUT/'captures').glob('*.png'))
assert len(pngs) >= 36
required = ['snapshot.json', 'browser-results.json', 'test-results.txt',
            'dashboard-comparison.md', 'dashboard-analysis.md', 'execution-summary.md']
assert all((OUT/name).is_file() and (OUT/name).stat().st_size for name in required)
record = {'verified_at': datetime.now(timezone.utc).isoformat(), 'source_database_checks': source_checks,
          'evidence_database_unchanged': evidence_checks, 'source_sha256_final': hashes,
          'live_source_unchanged_since_copy': all(v['unchanged'] for v in source_checks.values()),
          'source_note': 'Live stack restarted after snapshot. Changes in paysim do not affect the isolated evidence database.',
          'business_logic_and_view_source_unchanged': True,
          'routing_changed_externally_and_preserved': hashes['dashboard/app.py'] != initial['dashboard/app.py'],
          'desktop_pages': 16, 'mobile_pages': 16, 'png_files': len(pngs), 'required_deliverables_present': True}
(OUT/'final-verification.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
manifest = {str(path.relative_to(OUT)): {'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for path in sorted(OUT.rglob('*'))
            if path.is_file() and path.name != 'artifact-manifest.json'}
(OUT/'artifact-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'PASS: {len(manifest)} artifacts; {len(pngs)} PNG; frozen evidence unchanged through capture; live source changes recorded separately')
