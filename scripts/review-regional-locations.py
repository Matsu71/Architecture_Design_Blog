"""Read-only bounded source retrieval; geographic candidates are not publication approval."""
import datetime,hashlib,json,time,urllib.parse,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'qa/regional-detail';OUT.mkdir(parents=True,exist_ok=True)
UA='ArchitectureJapanGuide/0.3 (https://github.com/Matsu71/Architecture_Design_Blog; editorial-review)'
# Bounds restrict searches only. Their centers are never used as building coordinates.
AREAS=[('埼玉会館',(35.85,139.64,35.86,139.66)),('角川武蔵野',(35.78,139.49,35.81,139.53)),('千葉県立美術館',(35.59,140.09,35.61,140.11)),('千葉市美術館|川崎銀行',(35.60,140.11,35.62,140.14)),('つくばセンター',(36.07,140.11,36.10,140.14)),('日立駅',(36.58,140.64,36.60,140.68)),('栃木県立美術館',(36.55,139.85,36.58,139.89)),('石の美術館',(36.91,140.10,37.04,140.20)),('富岡製糸場|東置繭',(36.25,138.88,36.26,138.90)),('太田市美術館',(36.29,139.37,36.31,139.40))]
query='[out:json][timeout:35];('+''.join('nwr["name"~"'+name+'"]('+','.join(map(str,box))+');' for name,box in AREAS)+');out geom;'
def request(url,data=None):
 req=urllib.request.Request(url,data=data,headers={'User-Agent':UA})
 with urllib.request.urlopen(req,timeout=50) as r:raw=r.read(9000001)
 if len(raw)>9000000:raise ValueError('Review response too large')
 return raw
errors=[]
for endpoint in ['https://overpass-api.de/api/interpreter','https://overpass.private.coffee/api/interpreter']:
 try:
  raw=request(endpoint,urllib.parse.urlencode({'data':query}).encode());data=json.loads(raw)
  if data.get('remark'):raise RuntimeError(data['remark'])
  (OUT/'osm.json').write_bytes(raw)
  (OUT/'provenance.json').write_text(json.dumps({'source':endpoint,'query':query,'timestamp':data.get('osm3s',{}).get('timestamp_osm_base'),'license':'ODbL 1.0','attribution':'OpenStreetMap contributors','productionChanged':False},ensure_ascii=False,indent=2)+'\n')
  break
 except Exception as e:errors.append({'endpoint':endpoint,'error':str(e)});time.sleep(2)
ORIGINALS=[('saitama-kaikan','https://upload.wikimedia.org/wikipedia/commons/1/1b/2018_Saitama_Hall_1.jpg','3a72d438859e553ffe9487dbaa9895cfb39d915d'),('hitachi-station','https://upload.wikimedia.org/wikipedia/commons/b/bd/Hitachi_station_21-11-14-1.jpg','28d4a77d82412217a4d071ed052ce749f4b2c4aa'),('tochigi-prefectural-art','https://upload.wikimedia.org/wikipedia/commons/7/73/Tochigi_Prefectural_Museum_of_Fine_Arts_2020_2.jpg','c80474619533406335835bcb5bceaf32b505acd1'),('ashino-stone-museum','https://upload.wikimedia.org/wikipedia/commons/c/ce/Stone_Plaza.jpg','3c5a0d2d295fbffa936570ce056c0c6bcd4aa3be')]
for id,url,expected in ORIGINALS:
 try:
  raw=request(url)
  if hashlib.sha1(raw).hexdigest()!=expected:raise ValueError('Original changed since file-page review')
  (OUT/(id+'.jpg')).write_bytes(raw)
 except Exception as e:errors.append({'photo':id,'error':str(e)})
(OUT/'errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'osm':(OUT/'osm.json').exists(),'photos':len(list(OUT.glob('*.jpg'))),'errors':errors},ensure_ascii=False))
raise SystemExit(0 if (OUT/'osm.json').exists() else 1)
