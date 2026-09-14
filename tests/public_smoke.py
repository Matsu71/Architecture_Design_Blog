"""Verify this revision is actually served before exercising the public Pages site.
No route interception, CDN replacement, or navigation fixtures are used here.
"""
import hashlib
import json
import os
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'qa'/'integration'; OUT.mkdir(parents=True,exist_ok=True)
BASE='https://matsu71.github.io/Architecture_Design_Blog/'
TARGETS=['assets/app.js','assets/core.mjs','data/map-index.json']
expected={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in TARGETS}
matched=False;attempts=[]
for n in range(12):
    try:
        hashes={}
        for path in TARGETS:
            req=urllib.request.Request(BASE+path+'?revision='+os.environ.get('GITHUB_SHA','local'),headers={'Cache-Control':'no-cache','User-Agent':'ArchitectureJapanGuide-PublicQA/1.0'})
            with urllib.request.urlopen(req,timeout=15) as response:raw=response.read()
            hashes[path]=hashlib.sha256(raw).hexdigest()
        if hashes==expected:matched=True;break
        attempts.append({'attempt':n+1,'result':'publication has not propagated'})
    except Exception as error:attempts.append({'attempt':n+1,'error':str(error)})
    time.sleep(10)
report={'commit':os.environ.get('GITHUB_SHA'),'publicUrl':BASE,'assetHashesMatched':matched,'attempts':attempts,'checks':[],'failures':[]}
try:
    if not matched:raise AssertionError('Public site did not serve the requested revision; no old-version test is accepted')
    with sync_playwright() as p:
        for engine,width in [('chromium',1440),('webkit',390)]:
            browser=getattr(p,engine).launch()
            try:
                page=browser.new_page(viewport={'width':width,'height':1000},reduced_motion='reduce')
                errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(BASE+'?building=kyu-iwasaki-tei',wait_until='networkidle')
                page.wait_for_selector('.leaflet-popup')
                assert page.evaluate('L.version')=='1.9.4'
                assert page.locator('.leaflet-marker-icon').count()==13
                report['checks'].append(f'{engine}: deployed Leaflet and 13 individual pins')
                assert '旧岩崎邸庭園 洋館' in page.locator('.leaflet-popup').inner_text()
                assert '建物位置を照合' in page.locator('.leaflet-popup').inner_text()
                report['checks'].append(f'{engine}: deployed corrected building link and precision')
                page.wait_for_function("Array.from(document.querySelectorAll('.leaflet-tile')).some(img=>img.complete&&img.naturalWidth>0)")
                report['checks'].append(f'{engine}: actual public background tiles decoded')
                page.screenshot(path=str(OUT/f'public-{engine}-map.png'),full_page=True)
                page.locator('.leaflet-popup a').first.click()
                page.wait_for_url('**/articles/kyu-iwasaki-tei-gardens.html')
                page.locator('.building-photo img').scroll_into_view_if_needed()
                page.wait_for_function("document.querySelector('.building-photo img').naturalWidth===800")
                assert 'Wiiii' in page.locator('.building-photo figcaption').inner_text()
                assert 'CC BY-SA 3.0' in page.locator('.building-photo figcaption').inner_text()
                report['checks'].append(f'{engine}: public article, photograph and attribution')
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                assert not errors,errors
                report['checks'].append(f'{engine}: no overflow or unhandled script errors')
                page.screenshot(path=str(OUT/f'public-{engine}-article.png'),full_page=True)
            finally:browser.close()
except Exception as error:
    report['failures'].append(str(error))
finally:
    report['passed']=len(report['checks'])
    (OUT/'public-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('PUBLIC_REPORT '+json.dumps(report,ensure_ascii=False))
raise SystemExit(1 if report['failures'] else 0)
