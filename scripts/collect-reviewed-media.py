"""Fetch explicitly reviewed originals and temporary plan references, without publishing.
Photo licenses are checked on their file pages, not inferred from a category.
Plan references are for location review only, not website assets.
"""
import hashlib
import json
import urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'qa'/'media-review'; OUT.mkdir(parents=True,exist_ok=True)
FILES=[
    {'name':'iwasaki-original.jpg','url':'https://upload.wikimedia.org/wikipedia/commons/c/c2/Former_Iwasaki_Family_House_and_Garden_2009.jpg',
     'sha1':'96f1723a1e1922302e735a136a3c899c431a4576','sourcePage':'https://commons.wikimedia.org/wiki/File:Former_Iwasaki_Family_House_and_Garden_2009.jpg',
     'author':'Wiiii','license':'CC BY-SA 3.0','licenseUrl':'https://creativecommons.org/licenses/by-sa/3.0/','dateTaken':'2009'},
    {'name':'yoyogi-original.jpg','url':'https://upload.wikimedia.org/wikipedia/commons/1/1d/Yoyogi-National-Gymnasium-01.jpg',
     'sha1':'b95894579ff3fe94b177f5878de4f07dc0d81f50','sourcePage':'https://commons.wikimedia.org/wiki/File:Yoyogi-National-Gymnasium-01.jpg',
     'author':'Rs1421','license':'CC BY-SA 3.0','licenseUrl':'https://creativecommons.org/licenses/by-sa/3.0/','dateTaken':'2012-11'},
    {'name':'teien-reference.svg','url':'https://www.teien-art-museum.ne.jp/wp-content/themes/teien-art-museum/assets/images/floor-map/map_overall-view_modal.svg','referenceOnly':True},
    {'name':'nmwa-reference.gif','url':'https://www.nmwa.go.jp/jp/visit/img/img_map_all.gif','referenceOnly':True}
]
results=[]
for item in FILES:
    request=urllib.request.Request(item['url'],headers={'User-Agent':'ArchitectureJapanGuide/0.1 (https://github.com/Matsu71/Architecture_Design_Blog; reviewed-media)'} )
    try:
        with urllib.request.urlopen(request,timeout=40) as reply:raw=reply.read(8_000_001)
        if len(raw)>8_000_000:raise ValueError('File exceeds size limit')
        if item.get('sha1') and hashlib.sha1(raw).hexdigest()!=item['sha1']:raise ValueError('Original checksum differs from reviewed Commons version')
        (OUT/item['name']).write_bytes(raw)
        results.append(dict(item,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),status='downloaded'))
    except Exception as error:results.append(dict(item,status='failed',error=str(error)))
(OUT/'manifest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print('MEDIA_REVIEW '+json.dumps(results,ensure_ascii=False))
raise SystemExit(1 if any(x['status']=='failed' for x in results) else 0)
