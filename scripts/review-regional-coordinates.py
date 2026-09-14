"""Alternative read-only, named-entity location evidence. Never geocode to a region center."""
import json,time,urllib.request,urllib.parse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'qa/regional-coordinates';OUT.mkdir(parents=True,exist_ok=True)
UA='ArchitectureJapanGuide/0.3 (https://github.com/Matsu71/Architecture_Design_Blog; editorial-coordinate-review)'
titles=['埼玉会館','角川武蔵野ミュージアム','千葉県立美術館','千葉市美術館','つくばセンタービル','日立駅','栃木県立美術館','石の美術館','富岡製糸場','太田市美術館・図書館']
def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':UA})
 with urllib.request.urlopen(req,timeout=40) as r:raw=r.read(8000001)
 if len(raw)>8000000:raise ValueError('Response exceeds bounded review size')
 return json.loads(raw)
params={'action':'query','format':'json','redirects':1,'prop':'pageprops|coordinates','coprimary':'primary','titles':'|'.join(titles)}
result=get('https://ja.wikipedia.org/w/api.php?'+urllib.parse.urlencode(params));(OUT/'wiki-title-resolution.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
records=[]
for p in result.get('query',{}).get('pages',{}).values():
 q=p.get('pageprops',{}).get('wikibase_item');item={'title':p['title'],'wikidataId':q,'wikipediaCoordinate':p.get('coordinates')}
 if q:
  try:
   data=get('https://www.wikidata.org/wiki/Special:EntityData/'+q+'.json');entity=data['entities'][q]
   item['labels']={lang:value['value'] for lang,value in entity.get('labels',{}).items() if lang in ['ja','en']}
   item['claimsP625']=entity.get('claims',{}).get('P625',[])
   item['lastrevid']=entity.get('lastrevid');item['modified']=entity.get('modified')
  except Exception as e:item['error']=str(e)
 records.append(item);time.sleep(.4)
(OUT/'locations.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
# Discover canonical primary reference URLs, not facts to import from Wikipedia.
for title in ['角川武蔵野ミュージアム','栃木県立美術館']:
 try:
  p={'action':'parse','format':'json','page':title,'prop':'externallinks'}
  data=get('https://ja.wikipedia.org/w/api.php?'+urllib.parse.urlencode(p))
  (OUT/(title+'-source-links.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 except Exception as e:print(str(e))
print(json.dumps(records,ensure_ascii=False))
