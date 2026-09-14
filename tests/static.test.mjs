import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,readdir} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {resolve,dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
const data=JSON.parse(await readFile(join(root,'data/buildings.json'),'utf8'));
const index=JSON.parse(await readFile(join(root,'data/map-index.json'),'utf8'));
test('lean map index preserves every coordinate and stable ID',()=>assert.deepEqual(index.map(b=>[b.id,b.lat,b.lng]),data.map(b=>[b.id,b.lat,b.lng])));
test('map payload excludes article prose and bibliography',()=>assert(index.every(b=>!('sources' in b)&&!('summary' in b)&&!('components' in b))));
test('all local HTML links and fragment targets resolve',async()=>{
 const files=['index.html','building.html','about.html','catalogue.html',...(await readdir(join(root,'articles'))).filter(f=>f.endsWith('.html')).map(f=>'articles/'+f)];
 for(const file of files){
  const html=await readFile(join(root,file),'utf8');
  for(const [,raw] of html.matchAll(/href="([^"]*)"/g)){
   const href=raw.replaceAll('&amp;','&');if(/^[a-z]+:/i.test(href)||href.startsWith('//'))continue;
   const [route,fragment]=href.split('#'),path=route.split('?')[0];
   let target=path?resolve(dirname(join(root,file)),decodeURIComponent(path)):join(root,file);
   if(path.endsWith('/')||path==='.'||path==='..')target=join(target,'index.html');
   assert(target.startsWith(root),`${file}: local link escaped root`);
   assert(existsSync(target),`${file}: missing ${raw}`);
   if(fragment){const targetHtml=await readFile(target,'utf8');assert(targetHtml.includes(`id="${decodeURIComponent(fragment)}"`),`${file}: missing fragment ${raw}`);}
  }
 }
});
