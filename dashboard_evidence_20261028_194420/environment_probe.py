"""Read-only environment/source probe for this Track 9 evidence session."""
import hashlib
import importlib.metadata
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

from bson import json_util
from pymongo import MongoClient

OUT = Path('/evidence')
ROOT = Path('/workspace')
client = MongoClient('mongodb://mongodb:27017', tz_aware=True, serverSelectionTimeoutMS=10000)
source = client.paysim
run = source.runs.find_one(sort=[('started_at', -1)])
if run is None:
    raise RuntimeError('No real pipeline run in source database')
run_id = run['run_id']
evaluation = source.evaluation_totals.find_one({'_id': run_id})
latest = source.pipeline_metrics.find_one({'run_id': run_id}, sort=[('batch_id', -1)])
files = ['dashboard/app.py', 'dashboard/dashboard_core.py', 'dashboard/view_operations.py',
         'dashboard/view_report.py', 'dashboard/view_studio.py', 'tests/test_dashboard.py',
         'tests/snapshot_dashboard.py', 'tests/capture_dashboard.py', 'spark/pipeline.py',
         'docker-compose.yml', 'docs/05_Huong_Dan_Cai_Tien_Dashboard.md',
         'docs/06_Kiem_Thu_Dashboard_Va_Khoi_Dong.md']
data = dict(observed_at=datetime.now(timezone.utc), python=platform.python_version(),
            platform=platform.platform(), mongo_ping=client.admin.command('ping'),
            mongo_version=client.server_info()['version'], run=run, evaluation=evaluation,
            latest_metric=latest,
            source_counts={name: source[name].count_documents({'run_id': run_id}) for name in
                           ['pipeline_metrics', 'live_aggregates', 'fraud_alerts', 'recent_transactions']},
            versions={name: importlib.metadata.version(name) for name in
                      ['streamlit', 'pymongo', 'pandas', 'altair']},
            source_sha256={name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files})
(OUT/'environment.json').write_text(json_util.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print(json_util.dumps({k: v for k, v in data.items() if k not in ['source_sha256', 'latest_metric']}, ensure_ascii=False, indent=2))
