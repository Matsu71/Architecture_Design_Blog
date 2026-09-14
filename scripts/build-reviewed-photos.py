"""Rebuild only the two explicitly reviewed Commons photographs.
Downloads must match the reviewed original SHA-256. No official plan is published.
Already-correct derivatives are left untouched; other sources need editorial review.
"""
import hashlib
import io
import json
import re
import urllib.request
from pathlib import Path
from PIL import Image, ImageOps
ROOT=Path(__file__).resolve().parents[1]
REVIEWED={
 'kyu-iwasaki-tei':('https://upload.wikimedia.org/wikipedia/commons/c/c2/Former_Iwasaki_Family_House_and_Garden_2009.jpg','938d522e714fda0c6e49a60bb39091c9a29a1899809135df45b225a6286f307c'),
 'yoyogi-national-gymnasium':('https://upload.wikimedia.org/wikipedia/commons/1/1d/Yoyogi-National-Gymnasium-01.jpg','ae013d55c52e06aed672b3df7e12198883ee48b48c30a537efe007bcf385ee01')
}
data=json.loads((ROOT/'data/buildings.json').read_text())
for b in data:
    p=b.get('photo')
    if not p:continue
    if b['id'] not in REVIEWED:raise ValueError('Photo has not been added to the reviewed-source manifest')
    url,expected=REVIEWED[b['id']]
    if p['originalUrl']!=url or p['license']!='CC BY-SA 3.0':raise ValueError('Source or license differs from editorial review')
    if not re.fullmatch(r'assets/photos/[a-z0-9-]+\.webp',p['src']):raise ValueError('Unsafe destination')
    dest=ROOT/p['src']
    if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest()==p['sha256']:continue
    req=urllib.request.Request(url,headers={'User-Agent':'ArchitectureJapanGuide/0.1 (https://github.com/Matsu71/Architecture_Design_Blog; reviewed-photo-build)'})
    with urllib.request.urlopen(req,timeout=40) as response:raw=response.read(8_000_001)
    if len(raw)>8_000_000 or hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Original photograph checksum mismatch')
    image=ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert('RGB')
    image.thumbnail((800,800),Image.Resampling.LANCZOS)
    output=io.BytesIO();image.save(output,'WEBP',quality=76,method=6)
    result=output.getvalue()
    if hashlib.sha256(result).hexdigest()!=p['sha256'] or image.size!=(p['width'],p['height']):
        raise ValueError('Derivative differs from reviewed output; use Pillow 12.3.0 and review before changing hashes')
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(result)
    print(f'{p["src"]}: {len(result)} bytes, original and derivative hashes matched')
