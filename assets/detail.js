import {articleHtml} from './core.mjs';
const article=document.getElementById('article');
try{
  const response=await fetch('data/buildings.json');if(!response.ok)throw Error(`HTTP ${response.status}`);
  const data=await response.json(),id=new URLSearchParams(location.search).get('id'),b=data.find(x=>x.id===id||x.slug===id);
  if(!b){document.title='建築が見つかりません｜建築巡り JAPAN';article.innerHTML='<h1>建築が見つかりません</h1><p><a href="./">建築マップへ戻る</a></p>';}
  else{document.title=`${b.nameJa}｜建築巡り JAPAN`;document.querySelector('meta[name="description"]').content=b.oneLiner;article.innerHTML=articleHtml(b,data);if(location.hash)document.getElementById(decodeURIComponent(location.hash.slice(1)))?.scrollIntoView();}
}catch(error){console.error(error);article.innerHTML='<h1>記事を読み込めませんでした</h1><p><a href="catalogue.html">建築一覧</a>から記事をご確認ください。</p>';}
finally{article.setAttribute('aria-busy','false');}
