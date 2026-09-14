"""Read-only checks of newly published articles. No request interception."""
import hashlib,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'qa'/'integration';OUT.mkdir(parents=True,exist_ok=True)
BASE='https://matsu71.github.io/Architecture_Design_Blog/'
data=json.loads((ROOT/'data/additions/kanto-20260914.json').read_text())
report={'commit':os.environ.get('GITHUB_SHA'),'checks':[],'failures':[]}
with sync_playwright() as p:
 for engine in ['chromium','webkit']:
  browser=getattr(p,engine).launch()
  try:
   page=browser.new_page(viewport={'width':390,'height':900},reduced_motion='reduce')
   for b in data:
    url=BASE+'articles/'+b['slug']+'.html'
    response=page.goto(url,wait_until='networkidle');assert response.ok
    assert hashlib.sha256(response.body()).hexdigest()==hashlib.sha256((ROOT/'articles'/(b['slug']+'.html')).read_bytes()).hexdigest(),f'Stale article: {b["id"]}'
    assert page.locator('h1').inner_text()==b['nameJa']
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    if b.get('factNotes'):assert page.locator('.fact-note').count()==len(b['factNotes'])
    if b.get('visit',{}).get('notice'):assert page.locator('.visit-alert-compact').is_visible()
    report['checks'].append(f'{engine}: published and hash-matched {b["id"]}')
    if b['id'] in ['myonichikan-central','kanagawa-music-hall','ilcl-brick-building']:
     page.screenshot(path=str(OUT/f'public-{engine}-{b["id"]}.png'),full_page=True)
  except Exception as error:report['failures'].append({'engine':engine,'error':str(error)})
  finally:browser.close()
report['passed']=len(report['checks'])
(OUT/'public-content-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('PUBLIC_CONTENT_REPORT '+json.dumps(report,ensure_ascii=False))
raise SystemExit(1 if report['failures'] else 0)
