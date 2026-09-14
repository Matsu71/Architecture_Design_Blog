"""HTTP/browser integration using genuine, hash-verified Leaflet 1.9.4.

No map, DOM, projection, navigation or application-fetch substitutes. Tile requests
are intentionally aborted in deterministic tests; an independent live-tile smoke
check reports background availability without conflating it with application QA.
Run after `python -m playwright install --with-deps chromium webkit`.
"""
import base64
import functools
import hashlib
import http.server
import json
import os
import tempfile
import threading
import urllib.request
import urllib.parse
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'qa' / 'integration'
OUT.mkdir(parents=True, exist_ok=True)
DATA = json.loads((ROOT / 'data' / 'map-index.json').read_text())
LIBRARIES = {
    'leaflet.js': '20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=',
    'leaflet.css': 'p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=',
}
checks, failures, observations = [], [], []


def distribution(name):
    """Accept only the exact official distribution hash, including fallback CDN."""
    cache = OUT / name
    urls = [f'https://unpkg.com/leaflet@1.9.4/dist/{name}',
            f'https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/{name}']
    errors = []
    for url in urls:
        try:
            payload = urllib.request.urlopen(url, timeout=30).read()
            digest = base64.b64encode(hashlib.sha256(payload).digest()).decode()
            if digest != LIBRARIES[name]:
                raise ValueError(f'SHA-256 mismatch: {name}')
            cache.write_bytes(payload)
            return payload
        except Exception as error:
            errors.append(str(error))
    raise RuntimeError(f'Unable to verify {name}: {errors}')


JS, CSS = distribution('leaflet.js'), distribution('leaflet.css')


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def probe(page):
    # Read-only observation hook; original Leaflet/app code is not replaced.
    page.add_init_script("""document.addEventListener('load', event => {
      if (event.target.tagName === 'SCRIPT' && /leaflet/.test(event.target.src) && window.L) {
        L.Map.addInitHook(function () { window.__qualityMap = this; });
      }
    }, true);""")


def prepare(browser, width=1440, library=True, data=None, live_tiles=False):
    context = browser.new_context(viewport={'width': width, 'height': 1000},
                                  reduced_motion='reduce')
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    probe(page)
    def resource(route):
        url = route.request.url
        if url.endswith('leaflet.js'):
            if library:
                route.fulfill(body=JS, content_type='text/javascript')
            else:
                route.abort()
        elif url.endswith('leaflet.css'):
            route.fulfill(body=CSS, content_type='text/css')
        else:
            route.continue_()
    page.route('https://unpkg.com/**', resource)
    if not live_tiles:
        page.route('https://tile.openstreetmap.org/**', lambda route: route.abort())
    if data is not None:
        page.route('**/data/map-index.json', lambda route: route.fulfill(
            body=json.dumps(data, ensure_ascii=False), content_type='application/json'))
    return context, page, errors


def verify(name, condition):
    if not condition:
        raise AssertionError(name)
    checks.append(name)


def no_overflow(page):
    return page.evaluate('document.documentElement.scrollWidth <= innerWidth')


def run_browser(engine, browser, base):
    for width in (1440, 768, 390, 320):
        context, page, errors = prepare(browser, width)
        try:
            page.goto(base, wait_until='networkidle')
            page.wait_for_function("document.querySelectorAll('.building-card').length > 0")
            verify(f'{engine}/{width}: genuine Leaflet', page.evaluate('L.version') == '1.9.4')
            verify(f'{engine}/{width}: one marker per building',
                   page.locator('.leaflet-marker-icon').count() == len(DATA))
            coords = page.evaluate("""() => {
                const points=[]; __qualityMap.eachLayer(layer => {
                  if (layer instanceof L.Marker) { const p=layer.getLatLng(); points.push([p.lat,p.lng]); }
                }); return points;
            }""")
            verify(f'{engine}/{width}: no coordinate mutation',
                   sorted(coords) == sorted([[b['lat'], b['lng']] for b in DATA]))
            verify(f'{engine}/{width}: no horizontal overflow', no_overflow(page))
            verify(f'{engine}/{width}: advanced filters initially collapsed', page.locator('#extra-filters').is_hidden())
            if width <= 390:
                verify(f'{engine}/{width}: compact primary controls', page.locator('#filters').bounding_box()['height'] < 160)
            page.locator('#search-input').evaluate("""element=>{
                element.dispatchEvent(new CompositionEvent('compositionstart',{bubbles:true}));
                element.value='磯崎新';
                element.dispatchEvent(new InputEvent('input',{bubbles:true,isComposing:true}));
            }""")
            page.wait_for_timeout(250)
            verify(f'{engine}/{width}: IME intermediate text does not refilter', page.locator('.building-card').count()==len(DATA))
            page.locator('#search-input').evaluate("element=>element.dispatchEvent(new CompositionEvent('compositionend',{bubbles:true}))")

            page.wait_for_function("document.querySelectorAll('.building-card').length===2")
            verify(f'{engine}/{width}: map/list search sync',
                   page.locator('.leaflet-marker-icon').count() == 2)
            page.locator('#reset-filters').click()
            page.locator('[data-view="list"][type="button"]').click()
            page.evaluate("""() => {window.__iconMutations=0;const original=L.Marker.prototype.setIcon;L.Marker.prototype.setIcon=function(...args){window.__iconMutations++;return original.apply(this,args)};}""")
            page.locator('.building-card').first.hover()
            page.locator('.building-card').nth(1).hover()
            verify(f'{engine}/{width}: hover preserves marker DOM', page.evaluate('window.__iconMutations')==0)
            page.locator('[data-map="nmwa-main-building"]').click()
            page.wait_for_selector('.leaflet-popup')
            verify(f'{engine}/{width}: selected zoom', page.evaluate('__qualityMap.getZoom()') >= 17)
            verify(f'{engine}/{width}: URL selection', 'building=nmwa-main-building' in page.url)
            page.locator('.leaflet-popup a').first.click()
            page.wait_for_url('**/articles/national-museum-western-art.html')
            verify(f'{engine}/{width}: HTTP article navigation',
                   page.locator('h1').inner_text() == '国立西洋美術館 本館')
            verify(f'{engine}/{width}: article no overflow', no_overflow(page))
            page.locator('a.secondary-button', has_text='地図で見る').click()
            page.wait_for_selector('.leaflet-popup')
            verify(f'{engine}/{width}: article-to-map deep link',
                   page.locator('.leaflet-popup').inner_text().startswith('国立西洋美術館'))
            verify(f'{engine}/{width}: no uncaught error', not errors)
            if width in (1440, 390):
                page.screenshot(path=str(OUT / f'{engine}-map-{width}.png'), full_page=True)
        except Exception as error:
            failures.append({'case': f'{engine}/{width}', 'error': str(error), 'pageErrors': errors})
            page.screenshot(path=str(OUT / f'{engine}-failure-{width}.png'), full_page=True)
        finally:
            context.close()
    context, page, errors = prepare(browser, 390)
    try:
        page.goto(base+'?architect='+urllib.parse.quote('隈研吾'),wait_until='networkidle')
        verify(f'{engine}: advanced query reveals its control', page.locator('#architect-filter').is_visible())
        verify(f'{engine}: advanced filter query result',page.locator('.building-card').count()==sum('隈研吾' in b['architects'] for b in DATA))
        page.goto(base+'articles/kyu-iwasaki-tei-gardens.html',wait_until='networkidle')
        page.locator('.building-photo img').scroll_into_view_if_needed()
        page.wait_for_function("document.querySelector('.building-photo img').naturalWidth===800")
        verify(f'{engine}: licensed photograph is decoded over HTTP',page.locator('.building-photo img').evaluate('(img)=>img.complete'))
        verify(f'{engine}: visible author and license credit', 'Wiiii' in page.locator('.building-photo figcaption').inner_text() and 'CC BY-SA 3.0' in page.locator('.building-photo figcaption').inner_text())
        verify(f'{engine}: photographed article has no overflow',no_overflow(page))
        page.screenshot(path=str(OUT/f'{engine}-iwasaki-390.png'),full_page=True)
        page.locator('a.secondary-button',has_text='地図で見る').click()
        page.wait_for_selector('.leaflet-popup')
        verify(f'{engine}: corrected building coordinate drives navigation',page.evaluate('Math.abs(__qualityMap.getCenter().lat-35.7097579)<0.003'))
        verify(f'{engine}: building precision visible in popup','建物位置を照合' in page.locator('.leaflet-popup').inner_text())
    except Exception as error:
        failures.append({'case':f'{engine}/photos-and-filters','error':str(error),'pageErrors':errors})
    finally:
        context.close()
    context, page, errors = prepare(browser, 390)
    try:
        additions=json.loads((ROOT/'data/additions/kanto-20260914.json').read_text())
        for b in additions:
            page.goto(base+'articles/'+b['slug']+'.html',wait_until='networkidle')
            verify(f"{engine}: new article {b['id']}",page.locator('h1').inner_text()==b['nameJa'])
            verify(f"{engine}: readable new article {b['id']}",no_overflow(page) and page.locator('#sources').is_visible())
        page.goto(base+'?query='+urllib.parse.quote('旧帝国図書館'),wait_until='networkidle')
        verify(f'{engine}: historical-name search',page.locator('.building-card').count()==1 and 'レンガ棟' in page.locator('.building-card').inner_text())
        page.goto(base+'articles/myonichikan-central.html',wait_until='networkidle')
        verify(f'{engine}: date qualification visible','1921年' in page.locator('.fact-note').inner_text() and '1922年' in page.locator('.fact-note').inner_text())
        page.screenshot(path=str(OUT/f'{engine}-myonichikan-390.png'),full_page=True)
        page.goto(base+'articles/kanagawa-music-hall.html',wait_until='networkidle')
        verify(f'{engine}: tour-only notice visible',page.locator('.visit-alert-compact').is_visible())
        page.screenshot(path=str(OUT/f'{engine}-ongakudo-390.png'),full_page=True)
        verify(f'{engine}: additions have no uncaught script errors',not errors)
    except Exception as error:
        failures.append({'case':f'{engine}/new-buildings','error':str(error),'pageErrors':errors})
    finally:
        context.close()
    # Thirty distinct records at a single location must remain individually selectable.
    many = [dict(DATA[0], id=f'test-{i}', nameJa=f'テスト建築 {i}') for i in range(30)]
    context, page, errors = prepare(browser, data=many)
    try:
        page.goto(base, wait_until='networkidle')
        page.locator('.leaflet-marker-icon').last.click()
        page.wait_for_selector('[data-pick]')
        verify(f'{engine}: all 30 overlap candidates', page.locator('[data-pick]').count() == 30)
        page.keyboard.press('Escape')
        verify(f'{engine}: Escape dismisses picker', page.locator('#overlap-picker').is_hidden())
        verify(f'{engine}: focus returns to marker',
               page.locator('.leaflet-marker-icon').last.evaluate('(e)=>e===document.activeElement'))
        page.locator('.leaflet-marker-icon').last.click()
        page.locator('[data-pick="test-29"]').click()
        verify(f'{engine}: exact overlap selection',
               'テスト建築 29' in page.locator('.leaflet-popup').inner_text())
    except Exception as error:
        failures.append({'case': f'{engine}/overlap', 'error': str(error), 'pageErrors': errors})
    finally:
        context.close()
    context, page, errors = prepare(browser, 390, library=False)
    try:
        page.goto(base, wait_until='networkidle')
        page.wait_for_function("document.querySelectorAll('.building-card').length>0")
        verify(f'{engine}: CDN failure preserves list', page.locator('.results-panel').is_visible())
        page.locator('.building-card h2 a').first.click()
        page.wait_for_selector('#sources')
        verify(f'{engine}: CDN failure preserves real article links', page.locator('h1').count() == 1)
    except Exception as error:
        failures.append({'case': f'{engine}/fallback', 'error': str(error), 'pageErrors': errors})
    finally:
        context.close()
    context, page, _ = prepare(browser, 1440, live_tiles=True)
    try:
        page.goto(base + '?building=nmwa-main-building', wait_until='networkidle')
        page.wait_for_function("Array.from(document.querySelectorAll('.leaflet-tile')).some(i=>i.complete&&i.naturalWidth>0)", timeout=20000)
        decoded = page.locator('.leaflet-tile').evaluate_all('(tiles)=>tiles.filter(i=>i.complete&&i.naturalWidth>0).length')
        observations.append({'browser': engine, 'liveTiles': 'loaded', 'decodedTiles': decoded})
        page.screenshot(path=str(OUT / f'{engine}-live-map.png'), full_page=True)
    except Exception as error:
        observations.append({'browser': engine, 'liveTiles': 'unavailable', 'error': str(error)})
    finally:
        context.close()


with tempfile.TemporaryDirectory() as serving:
    (Path(serving) / 'Architecture_Design_Blog').symlink_to(ROOT, target_is_directory=True)
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0),
        functools.partial(QuietHandler, directory=serving))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}/Architecture_Design_Blog/'
    try:
        with sync_playwright() as playwright:
            for engine in ('chromium', 'webkit'):
                browser = getattr(playwright, engine).launch()
                try:
                    run_browser(engine, browser, base)
                finally:
                    browser.close()
    finally:
        server.shutdown()
report = {'commit': os.environ.get('GITHUB_SHA'), 'passed': len(checks),
          'checks': checks, 'failures': failures, 'observations': observations,
          'scope': 'Genuine SHA-256 verified Leaflet; real local HTTP; Chromium and WebKit.',
          'limitations': ['WebKit is not a physical iPhone/Safari device.',
                         'Geometry checks do not establish geographical truth.',
                         'Tile availability is reported separately from deterministic application checks.']}
(OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print('E2E_REPORT ' + json.dumps(report, ensure_ascii=False))
raise SystemExit(1 if failures else 0)
