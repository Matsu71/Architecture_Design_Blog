import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {validate,validDate} from '../scripts/validate-data.mjs';
import {articleHtml,filterBuildings} from '../assets/core.mjs';
const data=JSON.parse(await readFile(new URL('../data/buildings.json',import.meta.url),'utf8'));
const edit=fn=>{const b=structuredClone(data[0]);fn(b);return validate([b],{today:'2026-09-14'}).errors;};
test('impossible and future verification dates are rejected',()=>{
 for(const value of ['2026-02-30','2025-02-29','2026-13-01','2026-09-15','abc',null])assert.equal(validDate(value,'2026-09-14'),false);
 assert.equal(validDate('2024-02-29','2026-09-14'),true);
});
test('null records fail validation without throwing',()=>assert(validate([null,[],false]).errors.length===3));
test('a precise building label requires polygon evidence',()=>assert(edit(b=>{b.location.precision='building';delete b.location.evidence;}).some(x=>x.includes('輪郭'))));
test('an entrance label requires a matching public entrance point and sources',()=>assert(edit(b=>{b.location.status='cross-checked';b.location.precision='entrance';}).some(x=>x.includes('入口'))));
test('withheld locations cannot keep invented coordinates',()=>assert(edit(b=>b.location.status='withheld').some(x=>x.includes('仮座標'))));
test('closed status requires visit evidence',()=>assert(edit(b=>{b.visit.status='closed';b.visit.sourceIds=[];}).some(x=>x.includes('見学'))));
test('completion and opening years render separately',()=>{
 const b=data.find(x=>x.id==='national-art-center-tokyo'),html=articleHtml(b,data);
 assert.equal(b.completionYear,2006);assert.equal(b.openingYear,2007);
 assert.match(html,/<dt>竣工<\/dt><dd>2006年/);assert.match(html,/<dt>開館<\/dt><dd>2007年/);
});
test('Tokyo Bunka closure is visible before main article content',()=>{
 const b=data.find(x=>x.id==='tokyo-bunka-kaikan'),html=articleHtml(b,data);
 assert.equal(b.address,'東京都台東区上野公園5-45');assert.equal(b.visit.status,'closed');
 assert(html.indexOf('visit-alert')<html.indexOf('id="highlights"'));
 assert(filterBuildings(data,{visit:'closed'}).some(x=>x.id===b.id));
 assert(!filterBuildings(data,{visit:'public'}).some(x=>x.id===b.id));
});
test('material additions retain room-specific source references',()=>{
 const b=data.find(x=>x.id==='teien-art-museum-main');
 assert(b.components.some(c=>c.material.includes('蛇紋岩')||c.origin?.includes('蛇紋岩')));
 assert(b.components.filter(c=>c.sourceIds.includes('rooms')).length===3);
});
