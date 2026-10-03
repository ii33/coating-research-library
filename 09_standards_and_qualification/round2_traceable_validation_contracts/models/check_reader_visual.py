"""Render only this generated local HTML artifact with the installed renderer.
No user browser, third-party website, network request, or deployment.
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
records=[]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-crash-reporter','--disable-breakpad'])
 for name,width,height in [('desktop',1440,1050),('mobile',390,844)]:
  page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
  # Block all network; file:// is the only artifact source.
  page.route('http://**',lambda r:r.abort());page.route('https://**',lambda r:r.abort())
  page.goto((ROOT/'index.html').as_uri())
  page.screenshot(path=str(ROOT/'reviews'/f'reader_{name}.png'),full_page=False)
  result=page.evaluate('''() => ({title:document.title,chapters:document.querySelectorAll('.chapter').length,
  horizontalOverflow:document.documentElement.scrollWidth>innerWidth,
  scripts:[...document.scripts].filter(s=>s.src).length,
  images:[...document.images].filter(i=>!i.complete||i.naturalWidth===0).length})''')
  page.locator('#q').fill('失锁')
  result['search_matching_chapters']=page.locator('.chapter:not(.hidden)').count()
  page.locator('#q').fill('___NO_MATCH_EXPECTED___')
  result['no_match_message_visible']=page.locator('#empty').is_visible()
  page.locator('#q').fill('')
  result['reset_chapters']=page.locator('.chapter:not(.hidden)').count()
  result['viewport']=[width,height];result['render_mode']='local file, network blocked; not dot cloud browser'
  records.append(result);page.close()
 browser.close()
(ROOT/'reviews/reader_qa.json').write_text(json.dumps({'views':records,'visually_inspected':False,'note':'Screenshots require human/model pixel inspection after this script. Browser tool could not open localhost; local generated-artifact renderer used.'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps(records,ensure_ascii=False,indent=2))
