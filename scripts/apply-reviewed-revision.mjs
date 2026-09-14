// One-time, hash-guarded data revision. Not run by the normal website build.
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const file=new URL('../data/buildings.json',import.meta.url);
const revision=JSON.parse(await readFile(new URL('../data/revisions/map-quality-20260914.json',import.meta.url),'utf8'));
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const bytes=await readFile(file);
if(hash(bytes)===revision.resultSha256){console.log('Reviewed data revision already applied');}
else{
  if(hash(bytes)!==revision.baseSha256)throw Error('Building data changed since review; reconcile rather than overwrite');
  const data=JSON.parse(bytes),seen=new Set();
  for(const patch of revision.updates){
    if(seen.has(patch.id)||Object.hasOwn(patch.set,'id')||Object.hasOwn(patch.set,'slug'))throw Error('Invalid stable-ID update');
    const b=data.find(x=>x.id===patch.id);if(!b)throw Error(`Missing building ${patch.id}`);
    Object.assign(b,patch.set);seen.add(patch.id);
  }
  const result=JSON.stringify(data,null,2)+'\n';
  if(hash(result)!==revision.resultSha256)throw Error('Reviewed output checksum mismatch');
  await writeFile(file,result);console.log(`Applied reviewed changes to ${seen.size} records`);
}
