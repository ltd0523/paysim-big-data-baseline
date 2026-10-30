import os
import subprocess
import sys
import time
from playwright.sync_api import sync_playwright

p = subprocess.Popen([sys.executable,'-m','streamlit','run','/tmp/paysim9a/after/entry.py',
    '--server.port=8512','--server.headless=true','--browser.gatherUsageStats=false','--theme.base=light'],
    env={**os.environ,'MONGO_URI':'mongodb://mongodb:27017','MONGO_DATABASE':'paysim_ui_evidence_20261028_194420'},
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    time.sleep(2)
    with sync_playwright() as pw:
        browser=pw.chromium.launch()
        page=browser.new_page(viewport={'width':1366,'height':768})
        page.goto('http://localhost:8512')
        page.get_by_text('Nguồn đã phát',exact=True).wait_for()
        print(page.evaluate('''() => {
          const selectors=['[data-testid="stSidebar"]','[data-testid="stSidebarContent"]',
          '[data-testid="stSidebarUserContent"]','[data-testid="stCaptionContainer"] p',
          '[data-testid="stExpander"] summary','[data-testid="stSidebarCollapsedControl"]',
          '[data-testid="stTooltipIcon"] svg','[data-testid="stCaptionContainer"]'];
          return selectors.map(s => ({selector:s, elements:[...document.querySelectorAll(s)].slice(0,3).map(e => ({
           html:e.outerHTML.slice(0,1300),color:getComputedStyle(e).color,background:getComputedStyle(e).backgroundColor,
           opacity:getComputedStyle(e).opacity,padding:getComputedStyle(e).padding,rect:e.getBoundingClientRect().toJSON(),
           ancestors:[e.parentElement,e.parentElement.parentElement].map(p=>({html:p.outerHTML.slice(0,100),opacity:getComputedStyle(p).opacity,padding:getComputedStyle(p).padding}))
          }))}));
        }'''))
        browser.close()
finally:
    p.terminate();p.wait()
