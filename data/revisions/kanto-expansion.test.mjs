import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {articleHtml,filterBuildings} from '../assets/core.mjs';
import {pointInRing} from '../assets/location.mjs';
import {validate} from '../scripts/validate-data.mjs';
const root=new URL('../',import.meta.url);
const data=JSON.parse(await readFile(new URL('data/buildings.json',root),'utf8'));
const additions=JSON.parse(await readFile(new URL('data/additions/kanto-20260914.json',root),'utf8'));
const get=id=>data.find(b=>b.id===id);
test('seven reviewed additions are present without replacing any of the original 13 IDs',()=>{
 assert.equal(additions.length,7);
 const baseline=['nmwa-main-building','kyu-iwasaki-tei','teien-art-museum-main','yoyogi-national-gymnasium','tokyo-international-forum','yokohama-kaiko-kinen-kaikan','momas','hoki-museum','art-tower-mito','bato-hiroshige','gunma-museum-modern-art','tokyo-bunka-kaikan','national-art-center-tokyo'];
 for(const id of baseline)assert(get(id),id);
 for(const b of additions)assert.deepEqual(get(b.id),b);
});
test('new types include station, church, school, library and terminal',()=>{
 for(const type of ['駅舎','教会','学校','図書館','客船ターミナル'])assert(additions.some(b=>b.buildingTypes.includes(type)));
});
test('new fundamental facts each refer to at least one official source',()=>{
 for(const b of additions){const sources=new Map(b.sources.map(s=>[s.id,s]));
  for(const [key,f] of Object.entries(b.verification.fields))assert(f.sourceIds.some(id=>sources.get(id)?.sourceType==='official'),`${b.id}/${key}`);
  assert(b.visit.sourceIds.length);assert(b.components.every(c=>c.sourceIds.length));
 }
});
test('facility points have explicit object provenance and remain inside reviewed source geometries',async()=>{
 const evidence=JSON.parse(await readFile(new URL('data/additions/kanto-osm-evidence.geojson',root),'utf8'));
 assert.equal(evidence.license,'ODbL 1.0');assert.equal(evidence.features.length,6);
 for(const f of evidence.features){const b=get(f.id),ev=b.location.evidence;
  assert.deepEqual([b.lng,b.lat],f.properties.point);assert.equal(ev.osmId,f.properties.osmId);
  assert.equal(b.location.precision,'facility');
  if(f.geometry.type==='Polygon')assert(pointInRing(b.lat,b.lng,f.geometry.coordinates[0]));
  else assert.deepEqual([b.lng,b.lat],f.geometry.coordinates);
 }
 assert.equal(get('tokyo-station-marunouchi').location.evidence.osmType,'relation');
 assert.equal(get('osanbashi-terminal').location.evidence.osmId,84830302);
});
test('no new facility point is silently called an entrance or a separately verified building',()=>{
 for(const b of additions){assert.equal(b.location.precision,'facility');assert.equal(b.location.status,'address-matched');assert.match(articleHtml(b,data),/施設座標（入口未照合）/);}
});
test('Myonichikan keeps the 1921/1922 source distinction and the school-opening label',()=>{
 const b=get('myonichikan-central'),html=articleHtml(b,data);
 assert.equal(b.completionYear,1922);assert.equal(b.openingYear,1921);
 assert.equal(b.verification.fields.completionYear.status,'qualified');
 assert.match(html,/<dt>開校<\/dt><dd>1921年/);assert.match(html,/文化庁の年代欄は1921年/);
 assert(html.indexOf('文化庁の年代欄')<html.indexOf('id="highlights"'));
});
test('Tokyo Station opening and gallery admission are not mislabeled as museum opening',()=>{
 const b=get('tokyo-station-marunouchi'),html=articleHtml(b,data);
 assert.match(html,/<dt>開業<\/dt><dd>1914年/);assert.match(html,/ギャラリーの入館条件は駅の通行とは別/);
});
test('library original designers and renovation designers remain distinct',()=>{
 const b=get('ilcl-brick-building'),html=articleHtml(b,data);
 assert.equal(b.completionYear,1906);assert.match(html,/安藤忠雄（改修）/);assert.match(html,/久留正道（創建）/);
 assert.match(html,/自由見学は予約不要/);assert.match(html,/団体見学は事前申込み/);
});
test('alias search is available in both canonical and lean map records',async()=>{
 const lean=JSON.parse(await readFile(new URL('data/map-index.json',root),'utf8'));
 for(const records of [data,lean]){
  assert.deepEqual(filterBuildings(records,{query:'旧帝国図書館'}).map(b=>b.id),['ilcl-brick-building']);
  assert(filterBuildings(records,{query:'くじらのせなか'}).some(b=>b.id==='osanbashi-terminal'));
 }
});
test('music-hall restriction appears before main text and has supporting references',()=>{
 const b=get('kanagawa-music-hall'),html=articleHtml(b,data);
 assert.equal(b.visit.status,'limited');assert(html.indexOf('見学は原則ツアーのみ')<html.indexOf('id="highlights"'));
 assert(b.visit.sourceIds.includes('visit'));assert.match(html,/建物全体が木造という意味ではありません/);
});
test('date notes, roles, labels and visit notices reject missing source metadata',()=>{
 let b=structuredClone(get('myonichikan-central'));b.factNotes[0].sourceIds=[];assert(validate([b]).errors.some(x=>x.includes('補足')));
 b=structuredClone(get('ilcl-brick-building'));b.designers[0].name='unmatched';assert(validate([b]).errors.some(x=>x.includes('一致')));
 b=structuredClone(get('kanagawa-music-hall'));b.visit.sourceIds=[];assert(validate([b]).errors.some(x=>x.includes('見学')));
 b=structuredClone(get('myonichikan-central'));b.openingLabel='<script>';assert(validate([b]).errors.some(x=>x.includes('ラベル')));
});
test('new explanatory fields are HTML-escaped, not inserted as markup',()=>{
 const b=structuredClone(get('ilcl-brick-building'));b.factNotes[0].text='<script>bad</script>';b.designers[0].role='<img onerror=bad>';
 b.visit.notice='<iframe>bad</iframe>';const html=articleHtml(b,data);
 assert(!html.includes('<script>'));assert(!html.includes('<img onerror'));assert(!html.includes('<iframe>'));
});
test('facility evidence cannot drift away from the displayed coordinate',()=>{
 const b=structuredClone(get('asakusa-culture-center'));b.lat+=0.01;
 assert(validate([b]).errors.some(x=>x.includes('施設位置の根拠')));
});
