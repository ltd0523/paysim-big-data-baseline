"""Final syntax, regression and unchanged-data verification; no source writes."""
from pathlib import Path
import subprocess
import sys

ROOT = Path('/workspace')
OUT = Path('/tmp/paysim-charts')
for path in [*ROOT.joinpath('dashboard').glob('*.py'), ROOT / 'tests/test_dashboard.py']:
    compile(path.read_text(), str(path), 'exec')
(OUT / 'syntax-results.txt').write_text('PASS: all dashboard Python modules and tests/test_dashboard.py compile\n')
for name, cmd in [
    ('test-results.txt', [sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', str(ROOT/'tests/test_dashboard.py')]),
    ('audit-after-results.txt', [sys.executable, str(Path(__file__).with_name('audit.py')), 'after']),
    ('comparison-results.txt', [sys.executable, str(Path(__file__).with_name('audit.py')), 'compare']),
]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    (OUT / name).write_text(result.stdout + result.stderr)
    print(name, result.returncode, flush=True)
    if result.returncode:
        print(result.stdout, result.stderr)
        sys.exit(result.returncode)
