// Append a reviewed batch once; refuse changes to the reviewed baseline.
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const root=new URL('../',import.meta.url),file=new URL('data/buildings.json',root);
const current=await readFile(file),data=JSON.parse(current);
const additions=JSON.parse(await readFile(new URL('data/additions/kanto-20260914.json',root),'utf8'));
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const existing=additions.filter(b=>data.some(x=>x.id===b.id));
if(existing.length){
 if(existing.length!==additions.length||additions.some(b=>JSON.stringify(data.find(x=>x.id===b.id))!==JSON.stringify(b)))throw Error('Partial or changed batch; reconcile rather than overwrite');
 console.log('Kanto additions already present');
}else{
 if(hash(current)!=='cd9ffcd17b079de0d674eccb0afc6b5d2b6a830ee6d2e435db06cdf642e0e2a8')throw Error('Baseline changed; reconcile before appending');
 if(additions.length!==7)throw Error('Unexpected reviewed batch size');
 for(const key of ['id','slug'])if(new Set([...data,...additions].map(b=>b[key])).size!==data.length+additions.length)throw Error('Duplicate stable ID or slug');
 await writeFile(file,JSON.stringify([...data,...additions],null,2)+'\n');
 console.log(`Appended ${additions.length} buildings without changing ${data.length} existing records`);
}
