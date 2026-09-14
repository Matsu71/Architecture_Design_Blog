"""Bounded, read-only source lookup for the next seven Kanto buildings.
This is candidate evidence, not an approval or an automatic coordinate update.
OSM coordinates/geometry remain subject to ODbL and editorial identity review.
"""
import datetime, json, urllib.parse, urllib.request, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'qa'/'kanto-sources';OUT.mkdir(parents=True,exist_ok=True)
pattern='東京駅丸の内|東京カテドラル|聖マリア大聖堂|自由学園明日館|神奈川県立音楽堂|浅草文化観光センター|国際子ども図書館|大さん橋国際客船'
query='[out:json][timeout:25];nwr["name"~"'+pattern+'"](35.3,139.5,35.9,140.0);out geom;'
errors=[]
for endpoint in ['https://overpass-api.de/api/interpreter','https://overpass.private.coffee/api/interpreter']:
    try:
        req=urllib.request.Request(endpoint,data=urllib.parse.urlencode({'data':query}).encode(),headers={'User-Agent':'ArchitectureJapanGuide/0.2 (https://github.com/Matsu71/Architecture_Design_Blog; bounded-source-review)'})
        with urllib.request.urlopen(req,timeout=45) as r: raw=r.read(3000000)
        data=json.loads(raw)
        if data.get('remark'):raise ValueError(data['remark'])
        (OUT/'osm-candidates.json').write_bytes(raw)
        break
    except Exception as exc:
        errors.append({'source':endpoint,'error':str(exc)});time.sleep(3)
else: raise RuntimeError(str(errors))
manifest={'collectedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':endpoint,'query':query,'sourceTimestamp':data.get('osm3s',{}).get('timestamp_osm_base'),'license':'ODbL 1.0','attribution':'OpenStreetMap contributors','productionChanged':False,'candidates':[]}
for e in data['elements']:
    item={'type':e['type'],'id':e['id'],'tags':e.get('tags',{}),'sourceUrl':f'https://www.openstreetmap.org/{e["type"]}/{e["id"]}'}
    if 'lat' in e:item.update(lat=e['lat'],lng=e['lon'])
    if 'geometry' in e:item['ring']=[[p['lon'],p['lat']] for p in e['geometry'] if 'lon' in p]
    if 'bounds' in e:item['bounds']=e['bounds']
    manifest['candidates'].append(item)
    print('CANDIDATE '+json.dumps(item,ensure_ascii=False))
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
