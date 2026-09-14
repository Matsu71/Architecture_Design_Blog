"""Read-only source collection for a manually reviewed regional batch.
No coordinates or photographs are automatically added to the published dataset.
One bounded OSM query and three Commons file candidates per named building.
"""
import datetime, hashlib, json, time, urllib.parse, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'qa'/'regional-sources';OUT.mkdir(parents=True,exist_ok=True)
UA='ArchitectureJapanGuide/0.3 (https://github.com/Matsu71/Architecture_Design_Blog; editorial-source-review)'
TARGETS={
 'saitama-kaikan':'"Saitama Kaikan"',
 'kadokawa-culture-museum':'"Kadokawa Culture Museum"',
 'chiba-prefectural-art':'"Chiba Prefectural Museum of Art"',
 'chiba-sayado':'"Chiba City Museum of Art"',
 'tsukuba-center':'"Tsukuba Center"',
 'hitachi-station':'"Hitachi Station"',
 'tochigi-prefectural-art':'"Tochigi Prefectural Museum of Fine Arts"',
 'ashino-stone-museum':'"Stone Museum" "Kuma"',
 'tomioka-silk-mill':'"Tomioka Silk Mill"',
 'ota-art-museum-library':'"Ota Art Museum"'
}
def get(url,data=None,limit=5000000):
 req=urllib.request.Request(url,data=data,headers={'User-Agent':UA})
 with urllib.request.urlopen(req,timeout=45) as response:
  raw=response.read(limit+1)
 if len(raw)>limit:raise ValueError('Response exceeds review size limit')
 return raw
errors=[]
pattern='埼玉会館|角川武蔵野|千葉県立美術館|千葉市美術館|川崎銀行|つくばセンター|日立駅|栃木県立美術館|石の美術館|富岡製糸場|太田市美術館'
query='[out:json][timeout:25];nwr["name"~"'+pattern+'"](35.1,138.5,37.1,141.1);out geom;'
for endpoint in ['https://overpass-api.de/api/interpreter','https://overpass.private.coffee/api/interpreter']:
 try:
  raw=get(endpoint,urllib.parse.urlencode({'data':query}).encode());response=json.loads(raw)
  if response.get('remark'):raise ValueError(response['remark'])
  (OUT/'osm.json').write_bytes(raw)
  (OUT/'osm-provenance.json').write_text(json.dumps({'endpoint':endpoint,'query':query,'timestamp':response.get('osm3s',{}).get('timestamp_osm_base'),'license':'ODbL 1.0','attribution':'OpenStreetMap contributors','productionChanged':False},ensure_ascii=False,indent=2)+'\n')
  break
 except Exception as e:errors.append({'source':endpoint,'error':str(e)});time.sleep(2)
media=[]
for target,term in TARGETS.items():
 try:
  params={'action':'query','format':'json','generator':'search','gsrsearch':term+' filetype:bitmap','gsrnamespace':6,'gsrlimit':3,'prop':'imageinfo','iiprop':'url|size|sha1|extmetadata','iiurlwidth':320}
  response=json.loads(get('https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(params)))
  for page in response.get('query',{}).get('pages',{}).values():
   info=page.get('imageinfo',[{}])[0]
   if not info.get('url'):continue
   item={'target':target,'title':page['title'],'pageId':page['pageid'],'info':info}
   thumb=info.get('thumburl')
   if thumb:
    try:
     thumb_bytes=get(thumb,limit=1000000)
     name=f'{target}-{page["pageid"]}.jpg';(OUT/name).write_bytes(thumb_bytes);item['preview']=name
    except Exception as e:item['previewError']=str(e)
   media.append(item)
  time.sleep(.5)
 except Exception as e:errors.append({'target':target,'error':str(e)})
(OUT/'commons-candidates.json').write_text(json.dumps(media,ensure_ascii=False,indent=2)+'\n')
(OUT/'errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'collectedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'commonsFiles':len(media),'osmCollected':(OUT/'osm.json').exists(),'errors':errors},ensure_ascii=False))
if not (OUT/'osm.json').exists():raise SystemExit(1)
