"""Browser smoke test against the actual rebuilt Streamlit service (live data)."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path('/tmp/paysim-charts/docker')
OUT.mkdir(parents=True, exist_ok=True)
report = []
with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={'width':1440,'height':900})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    page.goto('http://streamlit:8501')
    page.get_by_text('Nguồn đã phát', exact=True).wait_for(timeout=30000)
    for i, expected in enumerate(['Ingest Latency p95', '01. Ingestion',
                                 'Rule baseline vs Spark MLlib', 'Giao dịch vừa đi qua Spark']):
        page.locator('.st-key-dashboard_page button').nth(i).click()
        page.get_by_text(expected, exact=True).first.wait_for(timeout=30000)
        page.wait_for_timeout(600)
        assert not page.locator('[data-testid="stException"]').count()
        assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
        if i == 0:
            assert page.locator('[data-testid="stVegaLiteChart"]').count() == 5
        if i == 3:
            assert page.locator('[data-testid="stVegaLiteChart"]').count() == 1
        page.screenshot(path=str(OUT / f'live-page-{i+1}.png'))
        report.append(dict(page=i+1, exceptions=[], errors=list(errors), passed=True))
    assert not errors, errors
    browser.close()
(OUT / 'results.json').write_text(json.dumps(report, indent=2))
print('PASS: rebuilt Docker service, all four Operations pages, 5 live charts and 1 distribution chart')
