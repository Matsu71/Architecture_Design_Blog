import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {pointInRing} from '../assets/location.mjs';
import {validate} from '../scripts/validate-data.mjs';
import {photoHtml,articleHtml} from '../assets/core.mjs';
const data=JSON.parse(await readFile(new URL('../data/buildings.json',import.meta.url),'utf8'));
const building=id=>data.find(b=>b.id===id);
test('Iwasaki pin corrects an exterior point, not to the nearer billiard building',()=>{
  const b=building('kyu-iwasaki-tei'),e=b.location.evidence;
  assert.equal(e.osmWayId,502703799);
  assert.deepEqual([b.lng,b.lat],[139.7671857,35.7097579]);
  assert.equal(pointInRing(e.previousPoint[1],e.previousPoint[0],e.ring),false);
  assert.equal(pointInRing(b.lat,b.lng,e.ring),true);
});
test('already-contained museum and first-gym points are preserved',()=>{
  for(const id of ['nmwa-main-building','yoyogi-national-gymnasium']){
    const b=building(id);assert.deepEqual([b.lng,b.lat],b.location.evidence.previousPoint);
    assert(pointInRing(b.lat,b.lng,b.location.evidence.ring));
  }
});
test('combined Teien outline is not promoted to main-building precision',()=>{
  const b=building('teien-art-museum-main');assert.equal(b.location.precision,'facility');
  assert.equal(b.location.review.candidateOsmWayId,161011785);
  assert.match(articleHtml(b,data),/本館単独の輪郭照合は保留/);
});
test('degenerate closed polygon is not valid building evidence',()=>{
  assert.equal(pointInRing(35,139.1,[[139,35],[139.1,35],[139.2,35],[139,35]]),false);
  assert.equal(pointInRing(35,139,[[139,35],[139,35],[139,35],[139,35]]),false);
});
test('building precision needs official identity evidence and reviewed status',()=>{
  let b=structuredClone(building('kyu-iwasaki-tei'));b.location.status='address-matched';
  assert(validate([b]).errors.some(x=>x.includes('輪郭')));
  b=structuredClone(building('kyu-iwasaki-tei'));b.location.evidence.identitySourceIds=['osm-footprint'];
  assert(validate([b]).errors.some(x=>x.includes('公式')));
});
test('derived geography export matches canonical rings and carries attribution',async()=>{
  const g=JSON.parse(await readFile(new URL('../data/building-footprints.geojson',import.meta.url),'utf8'));
  assert.equal(g.features.length,3);assert.equal(g.license,'ODbL 1.0');assert(g.attribution);
  for(const f of g.features)assert.deepEqual(f.geometry.coordinates[0],building(f.id).location.evidence.ring);
});
test('all published photos match the reviewed derivative hash and WebP header',async()=>{
  const withPhotos=data.filter(b=>b.photo);assert.equal(withPhotos.length,2);
  for(const b of withPhotos){const p=b.photo,bytes=await readFile(new URL('../'+p.src,import.meta.url));
    assert.equal(createHash('sha256').update(bytes).digest('hex'),p.sha256);
    assert.equal(bytes.subarray(0,4).toString(),'RIFF');assert.equal(bytes.subarray(8,12).toString(),'WEBP');
    assert(bytes.length<150000);
  }
});
test('photo credits, modifications, dimensions and lazy loading travel with rendering',()=>{
  for(const b of data.filter(b=>b.photo))for(const compact of [true,false]){
    const html=photoHtml(b.photo,'../',compact);
    assert(html.includes(b.photo.author));assert(html.includes(b.photo.license));
    assert(html.includes(b.photo.modifications));assert(html.includes('loading="lazy"'));
    assert(html.includes(`width="${b.photo.width}"`));assert(html.includes(`src="../${b.photo.src}"`));
    assert(html.includes(b.photo.sourceUrl));assert(html.includes(b.photo.licenseUrl));
  }
});
test('unreviewed path or javascript credit URL cannot render a photo',()=>{
  const p=building('kyu-iwasaki-tei').photo;
  assert.equal(photoHtml({...p,src:'../../evil.webp'}),'');
  assert.equal(photoHtml({...p,src:'https://tracking.invalid/pixel.webp'}),'');
  assert.equal(photoHtml({...p,sourceUrl:'javascript:alert(1)'}),'');
});
test('no unsupported site-wide photo license or plan reproduction',async()=>{
  const credits=await readFile(new URL('../assets/photos/CREDITS.md',import.meta.url),'utf8');
  assert.match(credits,/not automatically to all site code/);
  for(const b of data)assert(!b.photo||b.photo.src.endsWith('-exterior.webp'));
});
