"""Bounded, read-only footprint lookup. Results need official identity review.
No production coordinates are changed; OSM geometry is ODbL 1.0.
"""
import datetime, json, urllib.parse, urllib.request, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'qa'/'kanto-sources';OUT.mkdir(parents=True,exist_ok=True)
# Search extents only, never fallback coordinates for publication.
query='[out:json][timeout:25];(way["building"](35.7257,139.7062,35.7276,139.7087);way["building"](35.7178,139.7738,35.7203,139.7771);way["building"](35.4495,139.6455,35.454,139.650););out geom;'
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
    if 'geometry' in e:item['ring']=[[p['lon'],p['lat']] for p in e['geometry'] if 'lon' in p]
    if 'bounds' in e:item['bounds']=e['bounds']
    manifest['candidates'].append(item)
    if e.get('tags',{}).get('name'):print('CANDIDATE '+json.dumps(item,ensure_ascii=False))
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
