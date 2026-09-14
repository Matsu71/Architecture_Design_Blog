// Optional static output. Commit generated articles alongside the app for no-build hosting.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {articleHtml,escapeHtml as e} from '../assets/core.mjs';
import {validate} from './validate-data.mjs';
const root=new URL('../',import.meta.url);
const data=JSON.parse(await readFile(new URL('data/buildings.json',root),'utf8'));
const {errors}=validate(data); if(errors.length)throw Error(errors.join('\n'));
const checking=process.argv.includes('--check');
if(!checking)await mkdir(new URL('articles/',root),{recursive:true});
async function output(path,content){
 const url=new URL(path,root);
 if(checking){const current=await readFile(url,'utf8').catch(()=>null);if(current!==content)throw Error(`${path} is stale; run npm run build:articles`);}
 else await writeFile(url,content);
}
function frame(title,description,body,prefix='./'){
return `<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${e(title)}｜建築巡り JAPAN</title><meta name="description" content="${e(description)}"><link rel="stylesheet" href="${prefix}assets/styles.css"></head><body><a class="skip-link" href="#content">本文へ</a><header class="site-header"><a class="brand" href="${prefix}"><span class="brand-mark" aria-hidden="true">建</span><span>建築巡り <b>JAPAN</b><small>Architecture Japan Guide</small></span></a><nav aria-label="主要ナビゲーション"><a href="${prefix}">建築を探す</a><a href="${prefix}about.html">掲載方針</a></nav></header><main id="content" class="article-page">${body}</main><footer><span>建築巡り JAPAN</span><a href="${prefix}catalogue.html">建築一覧</a><a href="${prefix}about.html">出典と掲載方針</a></footer></body></html>\n`;
}
const staticLinks=html=>html.replace(/href="\.\.\/building\.html\?id=([^"&]+)"/g,(match,id)=>{const b=data.find(x=>x.id===decodeURIComponent(id));return b?`href="${e(b.slug)}.html"`:match;});
for(const b of data){
 const html=frame(b.nameJa,b.oneLiner,`<a class="back-link" href="../catalogue.html">← 建築一覧</a><article>${staticLinks(articleHtml(b,data,'../'))}</article>`,'../');
 await output(`articles/${b.slug}.html`,html);
}
const areas=[...new Set(data.map(b=>b.prefecture))];
const catalogue=`<header class="article-heading"><p class="eyebrow">BUILDINGS</p><h1>建築一覧</h1><p class="article-deck">${data.length}件 · ${areas.length}都県</p></header><nav class="article-toc" aria-label="地域">${areas.map((p,i)=>`<a href="#area-${i}">${e(p)}</a>`).join('')}</nav>${areas.map((pref,i)=>`<section id="area-${i}"><h2>${e(pref)}</h2><div class="nearby">${data.filter(b=>b.prefecture===pref).map(b=>`<a href="articles/${e(b.slug)}.html"><strong>${e(b.nameJa)}</strong><span>${b.completionYear}年 · ${e(b.architects.join(' / '))}</span></a>`).join('')}</div></section>`).join('')}`;
await output('catalogue.html',frame('建築一覧','地域別の建物一覧。各建物の見どころ、設計、構造・素材、見学情報を読めます。',catalogue));
const fields=['id','slug','nameJa','nameEn','prefecture','municipality','area','address','lat','lng','completionYear','era','architects','buildingTypes','styles','materials','oneLiner'];
const index=data.map(b=>({...Object.fromEntries(fields.map(k=>[k,b[k]])),location:{status:b.location.status,precision:b.location.precision},visit:{status:b.visit.status}}));
await output('data/map-index.json',JSON.stringify(index,null,2)+'\n');
console.log(`${checking?'Checked':'Generated'} ${data.length} articles, catalogue.html and map-index.json`);
