"""Guard the repository snapshot tool with full source fingerprints."""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from bson import json_util
from pymongo import MongoClient

OUT = Path('/evidence')
DATABASE = 'paysim_ui_evidence_20261028_194420'
URI = 'mongodb://mongodb:27017'
client = MongoClient(URI, tz_aware=True, serverSelectionTimeoutMS=10000)
source = client.paysim


def fingerprint():
    run = source.runs.find_one(sort=[('started_at', -1)])
    rid = run['run_id']
    result = {}
    for name in ['runs', 'evaluation_totals', 'pipeline_metrics', 'live_aggregates',
                 'fraud_alerts', 'recent_transactions', 'system_metrics']:
        query = {'_id': 'spark'} if name == 'system_metrics' else (
            {'_id': rid} if name == 'evaluation_totals' else {'run_id': rid})
        rows = list(source[name].find(query).sort('_id', 1))
        raw = json_util.dumps(rows, sort_keys=True).encode('utf-8')
        result[name] = {'count': len(rows), 'sha256': hashlib.sha256(raw).hexdigest()}
    return {'run_id': rid, 'collections': result}


before = fingerprint()
completed = subprocess.run([sys.executable, '/workspace/tests/snapshot_dashboard.py',
                           '--uri', URI, '--database', DATABASE,
                           '--output', str(OUT/'snapshot.json')], capture_output=True, text=True)
(OUT/'snapshot-tool.txt').write_text(completed.stdout + completed.stderr, encoding='utf-8')
after = fingerprint()
record = {'checked_at': datetime.now(timezone.utc).isoformat(), 'before': before, 'after': after,
          'source_unchanged_during_copy': before == after, 'snapshot_tool_exit_code': completed.returncode,
          'writers': 'Spark and replayer stopped before copy; no source writes by this script'}
(OUT/'snapshot-consistency.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(completed.stdout, completed.stderr)
assert completed.returncode == 0, 'Repository snapshot tool failed; see snapshot-tool.txt'
assert before == after, 'Source changed during snapshot; evidence cannot be accepted'
print('PASS: all seven source collection fingerprints unchanged during snapshot')
