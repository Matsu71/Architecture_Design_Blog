"""Read-only extraction of explicitly linked official map evidence.
Viewport centers must not be substituted for facility coordinates.
"""
import hashlib,html,json,re,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'qa/official-maps';OUT.mkdir(parents=True,exist_ok=True)
URLS={
'ashino-stone-museum':'https://stonemuseum.jp/museum/',
'kadokawa-culture-museum':'https://kadcul.com/guide/access',
'tochigi-prefectural-art':'https://www.art.pref.tochigi.lg.jp/visit/access.html',
'hitachi-station':'https://www.city.hitachi.lg.jp/citypromotion/hitachi_donnamachi/1007477/1011149/1010610/1004743/1004744.html',
'chiba-prefectural-art':'https://www.chiba-muse.or.jp/ART/visit/',
'ota-art-museum-library':'https://www.artmuseumlibraryota.jp/facilities/'
}
results=[]
for id,url in URLS.items():
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'ArchitectureJapanGuide/0.3 (https://github.com/Matsu71/Architecture_Design_Blog; map-source-review)'})
  with urllib.request.urlopen(req,timeout=40) as r:raw=r.read(2500000)
  text=raw.decode('utf-8',errors='replace');(OUT/(id+'.html')).write_bytes(raw)
  maps=[html.unescape(m) for m in re.findall(r'(?:src|href)=[\"\']([^\"\']+)[\"\']',text) if any(s in m.lower() for s in ['maps.google','google.com/maps','goo.gl/maps','maps.app','map.js'])]
  coordinates=re.findall(r'.{0,80}(?:\d{2}\.\d{4,}|latitude|longitude|latlng|map_lat|map_lng).{0,100}',text,flags=re.I)
  results.append({'id':id,'url':url,'sha256':hashlib.sha256(raw).hexdigest(),'mapLinks':maps,'coordinateContexts':coordinates[:60]})
 except Exception as e:results.append({'id':id,'url':url,'error':str(e)})
(OUT/'review.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(results,ensure_ascii=False))
