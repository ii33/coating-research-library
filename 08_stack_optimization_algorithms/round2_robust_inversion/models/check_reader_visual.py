"""Optional local artifact layout check; no web navigation or external resources."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-crash-reporter','--disable-breakpad'])
 context=browser.new_context(viewport={'width':1360,'height':1050},device_scale_factor=1,offline=True)
 page=context.new_page();page.goto((ROOT/'index.html').as_uri(),wait_until='load')
 page.screenshot(path=str(ROOT/'reviews/reader_desktop.png'))
 desktop=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(ROOT/'reviews/reader_mobile.png'))
 mobile=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
 browser.close()
result={'browser':'headless Chromium on dot cloud filesystem, offline mode','url':'local index.html','desktop':desktop,'mobile':mobile,'no_horizontal_page_overflow':desktop['scroll']<=desktop['width'] and mobile['scroll']<=mobile['width'],'screenshots':['reviews/reader_desktop.png','reviews/reader_mobile.png'],'initial_sandbox_attempt':'failed: process socket denied; authorized artifact-render retry used sandbox escalation'}
(ROOT/'verification/reader_visual_check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
