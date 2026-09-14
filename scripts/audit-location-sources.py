"""Read-only building-footprint audit. Never changes production coordinates.
One small, bounded Overpass query; results require editorial/official-plan review.
OSM extracts and derived candidate points: ODbL 1.0, OpenStreetMap contributors.
"""
import datetime
import json
import math
import urllib.parse
import urllib.request
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'qa'/'location-audit'; OUT.mkdir(parents=True,exist_ok=True)
TARGETS={'kyu-iwasaki-tei','teien-art-museum-main','yoyogi-national-gymnasium','nmwa-main-building'}
buildings=[b for b in json.loads((ROOT/'data/buildings.json').read_text()) if b['id'] in TARGETS]
# Bounding boxes keep the spatial lookup small and predictable.
query='[out:json][timeout:25];('+''.join(
    f'way({b["lat"]-.002},{b["lng"]-.0025},{b["lat"]+.002},{b["lng"]+.0025})["building"];'
    for b in buildings)+');out geom;'
errors=[]
for endpoint in ('https://overpass-api.de/api/interpreter',
                 'https://overpass.private.coffee/api/interpreter'):
    try:
        request=urllib.request.Request(endpoint,data=urllib.parse.urlencode({'data':query}).encode(),headers={
            'User-Agent':'ArchitectureJapanGuide/0.1 (https://github.com/Matsu71/Architecture_Design_Blog; source-location-audit)',
            'Content-Type':'application/x-www-form-urlencoded'})
        with urllib.request.urlopen(request,timeout=45) as reply:
            raw=reply.read()
        response=json.loads(raw)
        if response.get('remark'):raise RuntimeError(response['remark'])
        if not isinstance(response.get('elements'),list):raise ValueError('Missing OSM elements')
        break
    except Exception as error:
        errors.append({'endpoint':endpoint,'error':str(error)})
        print('SOURCE_RETRY '+json.dumps(errors[-1]))
        time.sleep(3)
else:
    (OUT/'errors.json').write_text(json.dumps(errors,indent=2)+'\n')
    raise RuntimeError('Both bounded source requests failed; production locations remain unchanged')
(OUT/'overpass.json').write_bytes(raw)

def inside(x,y,ring):
    result=False
    for (a,b),(c,d) in zip(ring,ring[1:]):
        if (b>y)!=(d>y) and x<(c-a)*(y-b)/(d-b)+a: result=not result
    return result

def point(ring):
    # Scan across horizontal slices; pick the widest segment known to lie inside.
    ys=sorted(set(y for x,y in ring)); candidates=[]
    for lo,hi in zip(ys,ys[1:]):
        y=(lo+hi)/2; xs=sorted(a+(y-b)*(c-a)/(d-b) for (a,b),(c,d) in zip(ring,ring[1:]) if (b>y)!=(d>y))
        for left,right in zip(xs[::2],xs[1::2]): candidates.append((right-left,(left+right)/2,y))
    if not candidates:return None
    _,x,y=max(candidates);return [round(x,7),round(y,7)]

def meters(a,b):
    return math.hypot((a[0]-b[0])*111320*math.cos(math.radians(b[1])),(a[1]-b[1])*111320)

features=[]
for element in response['elements']:
    ring=[[p['lon'],p['lat']] for p in element.get('geometry',[])]
    if len(ring)<4 or ring[0]!=ring[-1]:continue
    candidate=point(ring)
    if not candidate:continue
    features.append({'osmId':element['id'],'sourceUrl':f'https://www.openstreetmap.org/way/{element["id"]}',
        'tags':element.get('tags',{}),'ring':ring,'candidate':candidate})
report={'checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':endpoint,
        'license':'https://opendatacommons.org/licenses/odbl/1-0/','attribution':'OpenStreetMap contributors',
        'sourceTimestamp':response.get('osm3s',{}).get('timestamp_osm_base'),'query':query,
        'productionChanged':False,'buildings':[]}
for b in buildings:
    old=[b['lng'],b['lat']]
    near=sorted(features,key=lambda f:meters(f['candidate'],old))
    named=[f for f in near if f['tags'].get('name') and meters(f['candidate'],old)<260]
    options=[]
    for f in [*named[:4],*near[:2]]:
        if f['osmId'] in [o['osmId'] for o in options]:continue
        options.append(dict(f,oldPointInside=inside(*old,f['ring']),distanceMeters=round(meters(f['candidate'],old),1)))
    item={'id':b['id'],'name':b['nameJa'],'storedPoint':old,'candidates':options}
    report['buildings'].append(item)
    print('LOCATION_REVIEW '+json.dumps(item,ensure_ascii=False))
(OUT/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('Location audit collected evidence only; no coordinate is automatically approved.')
