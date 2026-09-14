from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
# Only apply to the reviewed implementation; never overwrite concurrent edits.
import sys
manifest=json.loads((R/'data/revisions/kanto-ui-hashes.json').read_text())
def digest(path):
 p=R/path
 return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
if all(digest(path)==item['after'] for path,item in manifest.items()):
 print('Kanto implementation already applied');sys.exit(0)
if any(digest(path)!=item['before'] for path,item in manifest.items()):
 raise RuntimeError('Implementation changed since review; reconcile before applying')
def replace(path,a,b):
 p=R/path;s=p.read_text();assert a in s,(path,a[:80]);p.write_text(s.replace(a,b))
# Supplement date labels and designer roles without injecting unchecked HTML.
replace('assets/core.mjs',"export const VISITS =", "export const OPENING_LABELS = ['開館','開校','開業','供用'];\nexport const VISITS =")
replace('assets/core.mjs',"b.nameJa,b.nameEn,b.prefecture", "b.nameJa,b.nameEn,...(b.aliases||[]),b.prefecture")
replace('assets/core.mjs',"  const coordinateStatus = locationLabel(b.location);", "  const coordinateStatus = locationLabel(b.location);\n  const designNames=Array.isArray(b.designers)&&b.designers.length?b.designers.map(d=>d.role?`${d.name}（${d.role}）`:d.name):(b.architects||[]);\n  const openingLabel=OPENING_LABELS.includes(b.openingLabel)?b.openingLabel:'開館';\n  const factNotes=(b.factNotes||[]).map(n=>`<p class=\"fact-note\">${e(n.text)}${refs(n.sourceIds)}</p>`).join('');")
replace('assets/core.mjs',"</p></aside>`:''}</header>", "</p></aside>`:b.visit?.notice?`<aside class=\"visit-alert visit-alert-compact\"><strong>${e(b.visit.notice)}</strong>${refs(b.visit.sourceIds)}</aside>`:''}</header>")
replace('assets/core.mjs',"${fact('設計',(b.architects||[]).join(' / '),'architects')}","${fact('設計',designNames.join(' / '),'architects')}")
replace('assets/core.mjs',"${b.openingYear?fact('開館',", "${b.openingYear?fact(openingLabel,")
replace('assets/core.mjs',"${fact('所在地',b.address,'address')}</dl>","${fact('所在地',b.address,'address')}</dl>${factNotes}")
replace('scripts/build-articles.mjs',"'id','slug','nameJa','nameEn','prefecture'", "'id','slug','nameJa','nameEn','aliases','prefecture'")
replace('about.html','輪郭と位置のデータ</a>には出典と取得時点を記録しています。','輪郭と位置のデータ</a>と、<a href="data/additions/kanto-osm-evidence.geojson">追加建築の施設位置の根拠</a>には出典と取得時点を記録しています。')
# Strong validation for new fields; existing records remain valid.
replace('scripts/validate-data.mjs','localPhotoPath,VISITS,ERAS','localPhotoPath,OPENING_LABELS,VISITS,ERAS')
replace('scripts/validate-data.mjs',"    if(!Object.hasOwn(ERAS,b.era))", "    if(b.openingLabel!=null&&(!OPENING_LABELS.includes(b.openingLabel)||b.openingYear==null))bad('開館・開校・開業等のラベルまたは年が不正');\n    if(b.aliases!=null&&(!Array.isArray(b.aliases)||b.aliases.some(v=>typeof v!=='string'||!v.trim())))bad('別名が不正');\n    if(!Object.hasOwn(ERAS,b.era))")
replace('scripts/validate-data.mjs',"    checkRefs(b.articleSourceIds,'本文');", "    if(b.factNotes!=null&&!Array.isArray(b.factNotes))bad('基本情報の補足は配列にしてください');\n    for(const n of Array.isArray(b.factNotes)?b.factNotes:[]){if(!n?.text||typeof n.text!=='string')bad('基本情報の補足文が不正');checkRefs(n?.sourceIds,'基本情報の補足');}\n    if(b.designers!=null){\n      if(!Array.isArray(b.designers)||!b.designers.length)bad('設計者の役割が不正');\n      else {\n        const names=b.designers.map(d=>d?.name);\n        if(names.length!==new Set(names).size||names.length!==(b.architects||[]).length||names.some(n=>!b.architects?.includes(n)))bad('設計者と役割の名前が一致しません');\n        for(const d of b.designers){if(typeof d?.role!=='string'||!d.role.trim())bad('設計者の役割が未入力');checkRefs(d?.sourceIds,'設計者の役割');}\n      }\n    }\n    if(loc.evidence?.kind==='facility-point'){\n      const ev=loc.evidence;\n      if(ev.lat!==b.lat||ev.lng!==b.lng||!['node','way','relation'].includes(ev.osmType)||!Number.isInteger(ev.osmId)||ev.osmId<=0)bad('施設位置の根拠が座標・地物と一致しません');\n      if(ev.license!=='ODbL 1.0'||ev.licenseUrl!=='https://opendatacommons.org/licenses/odbl/1-0/'||!ev.attribution)bad('施設位置の利用条件が不足');\n      checkRefs(ev.sourceIds,'施設位置の根拠');\n    }\n    checkRefs(b.articleSourceIds,'本文');")
replace('scripts/validate-data.mjs',"if(b.visit?.status==='closed'||b.visit?.sourceIds?.length)","if(b.visit?.status==='closed'||b.visit?.notice||b.visit?.sourceIds?.length)")
replace('scripts/validate-data.mjs',"    if(!Object.hasOwn(VISITS,b.visit?.status))", "    if(b.visit?.notice!=null&&(typeof b.visit.notice!=='string'||!b.visit.notice.trim()||b.visit.notice.length>40))bad('見学の注意見出しが不正');\n    if(!Object.hasOwn(VISITS,b.visit?.status))")
# Existing photo/geometry counts remain same; growing building count must not fail old tests.
replace('tests/core.test.mjs',"assert.equal(old[0].completionYear,1896);assert.equal(recent[0].completionYear,2010);", "assert.equal(old[0].completionYear,Math.min(...data.map(b=>b.completionYear)));assert.equal(recent[0].completionYear,Math.max(...data.map(b=>b.completionYear)));assert(old.every((b,i)=>i===0||b.completionYear>=old[i-1].completionYear));")
replace('tests/browser_integration.py',"page.locator('.building-card').count()==1)","page.locator('.building-card').count()==sum('隈研吾' in b['architects'] for b in DATA))")
replace('tests/public_smoke.py',"TARGETS=['assets/app.js','assets/core.mjs','data/map-index.json']", "TARGETS=['assets/app.js','assets/core.mjs','data/map-index.json']\nEXPECTED_BUILDINGS=len(json.loads((ROOT/'data/map-index.json').read_text()))")
replace('tests/public_smoke.py',"page.locator('.leaflet-marker-icon').count()==13", "page.locator('.leaflet-marker-icon').count()==EXPECTED_BUILDINGS")
replace('tests/public_smoke.py',"deployed Leaflet and 13 individual pins", "deployed Leaflet and {EXPECTED_BUILDINGS} individual pins")
# Add concise basic-info qualifications; no large new promotional sections.
p=R/'assets/refinements.css';p.write_text(p.read_text()+'''\n.fact-note{font-size:13px;line-height:1.8;color:var(--muted);margin:-8px 0 22px;padding-left:12px;border-left:2px solid var(--line)}\n.fact-note + .fact-note{margin-top:0}\n.visit-alert-compact{padding:.7rem 1rem;font-size:13px}\n''')

replace('tests/browser_integration.py','    # Thirty distinct records at a single location must remain individually selectable.','    context, page, errors = prepare(browser, 390)\n    try:\n        additions=json.loads((ROOT/\'data/additions/kanto-20260914.json\').read_text())\n        for b in additions:\n            page.goto(base+\'articles/\'+b[\'slug\']+\'.html\',wait_until=\'networkidle\')\n            verify(f"{engine}: new article {b[\'id\']}",page.locator(\'h1\').inner_text()==b[\'nameJa\'])\n            verify(f"{engine}: readable new article {b[\'id\']}",no_overflow(page) and page.locator(\'#sources\').is_visible())\n        page.goto(base+\'?query=\'+urllib.parse.quote(\'旧帝国図書館\'),wait_until=\'networkidle\')\n        verify(f\'{engine}: historical-name search\',page.locator(\'.building-card\').count()==1 and \'レンガ棟\' in page.locator(\'.building-card\').inner_text())\n        page.goto(base+\'articles/myonichikan-central.html\',wait_until=\'networkidle\')\n        verify(f\'{engine}: date qualification visible\',\'1921年\' in page.locator(\'.fact-note\').inner_text() and \'1922年\' in page.locator(\'.fact-note\').inner_text())\n        page.screenshot(path=str(OUT/f\'{engine}-myonichikan-390.png\'),full_page=True)\n        page.goto(base+\'articles/kanagawa-music-hall.html\',wait_until=\'networkidle\')\n        verify(f\'{engine}: tour-only notice visible\',page.locator(\'.visit-alert-compact\').is_visible())\n        page.screenshot(path=str(OUT/f\'{engine}-ongakudo-390.png\'),full_page=True)\n        verify(f\'{engine}: additions have no uncaught script errors\',not errors)\n    except Exception as error:\n        failures.append({\'case\':f\'{engine}/new-buildings\',\'error\':str(error),\'pageErrors\':errors})\n    finally:\n        context.close()\n    # Thirty distinct records at a single location must remain individually selectable.')

if any(digest(path)!=item['after'] for path,item in manifest.items()):raise RuntimeError('Implementation output does not match reviewed hashes')
print('Applied hash-verified Kanto UI and test changes')
