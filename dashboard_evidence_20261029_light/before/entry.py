import sys
sys.path.insert(0, '/workspace/dashboard')
from dashboard_core import render
import importlib.util
spec = importlib.util.spec_from_file_location('operations_before', '/workspace/dashboard_evidence_20261029_light/view_operations.before.py')
view = importlib.util.module_from_spec(spec)
spec.loader.exec_module(view)
render(view)
