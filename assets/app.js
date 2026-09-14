import {KANTO,ERAS,VISITS,escapeHtml as e,hasCoordinates,filterBuildings,directionsUrl} from './core.mjs';
import {nearbyScreenPoints} from './location.mjs';
const $=id=>document.getElementById(id);
let all=[],byId=new Map(),results=[],map=null,active=null,markers=new Map(),visibleLabels=false,pickerOrigin=null;
const controls={query:$('search-input'),region:$('region-filter'),architect:$('architect-filter'),type:$('type-filter'),era:$('era-filter'),visit:$('visit-filter'),sort:$('sort-filter')};
const reduceMotion=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
function filters(){return Object.fromEntries(Object.entries(controls).map(([k,v])=>[k,v.value]));}
function articleUrl(b){return `articles/${encodeURIComponent(b.slug)}.html`;}
function icon(selected=false){return L.divIcon({className:`arch-pin${selected?' active':''}`,html:'<span></span>',iconSize:[24,24],iconAnchor:[12,12]});}
function initMap(){
  if(!window.L){$('map').innerHTML='<p class="map-fallback">地図を読み込めませんでした。建物一覧と各記事の「行き方」は利用できます。</p>';$('map-note').textContent='地図ライブラリを読み込めませんでした。';$('map-note').classList.add('error');return;}
  map=L.map('map',{minZoom:3,maxZoom:19,scrollWheelZoom:true,zoomAnimation:!reduceMotion}).setView([35.78,139.52],10);
  const tiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'}).addTo(map);
  tiles.on('tileerror',()=>{$('map-note').textContent='背景地図を取得できません。位置情報と建物一覧は利用できます。';$('map-note').classList.add('error');});
  map.on('zoomend',updateLabels);
  map.on('click',()=>closePicker());
  new ResizeObserver(()=>map.invalidateSize()).observe($('map'));
}
function updateLabels(){
  if(!map)return;
  visibleLabels=map.getZoom()>=14;
  for(const [id,m]of markers){const b=byId.get(id);if(m.getTooltip())m.unbindTooltip();m.bindTooltip(e(b.nameJa),{permanent:visibleLabels,direction:'top',offset:[0,-9],className:'arch-label'});}
}
function select(id,{pan=false,scroll=false,commit=true}={}){
  if(commit)active=id;
  for(const [key,m]of markers){m.setIcon(icon(key===id));m.setZIndexOffset(key===id?1000:0);}
  for(const card of $('building-list').querySelectorAll('[data-id]')){const isActive=card.dataset.id===id;card.classList.toggle('is-active',isActive);if(isActive&&scroll)card.scrollIntoView({block:'nearest',behavior:reduceMotion?'instant':'smooth'});}
  const b=byId.get(id);
  if(pan&&map&&hasCoordinates(b))map.setView([b.lat,b.lng],Math.max(map.getZoom(),17),{animate:!reduceMotion});
}
function showOne(b){
  if(!b)return;closePicker();select(b.id,{pan:true,scroll:true});saveUrl();
  const marker=markers.get(b.id);if(marker)marker.bindPopup(`<div class="map-popup"><strong>${e(b.nameJa)}</strong><span>${e(b.address)}</span><a href="${e(articleUrl(b))}">建物を読む →</a><a href="${e(directionsUrl(b))}" target="_blank" rel="noopener noreferrer">行き方</a></div>`).openPopup();
}
function closePicker({restoreFocus=false}={}){
  $('overlap-picker').hidden=true;
  if(restoreFocus&&pickerOrigin?.isConnected)pickerOrigin.focus({preventScroll:true});
  pickerOrigin=null;
}
function markerClick(b){
  select(b.id,{scroll:true});
  const close=nearbyScreenPoints(results,b,x=>map.latLngToContainerPoint([x.lat,x.lng]));
  if(close.length<2){showOne(b);return;}
  closePicker();pickerOrigin=markers.get(b.id)?.getElement?.()||document.activeElement;
  const picker=$('overlap-picker');picker.hidden=false;
  picker.innerHTML=`<header><strong>この付近の建築 ${close.length}件</strong><button type="button" id="close-picker" aria-label="付近の建築を閉じる">閉じる</button></header>${close.map(x=>`<button type="button" class="candidate" data-pick="${e(x.id)}">${e(x.nameJa)}</button>`).join('')}<p class="muted">選ぶと、その建物の位置へ拡大します。</p>`;
  $('close-picker').onclick=()=>closePicker({restoreFocus:true});
  picker.querySelectorAll('[data-pick]').forEach(button=>button.onclick=()=>{const chosen=byId.get(button.dataset.pick);showOne(chosen);markers.get(chosen.id)?.getElement?.()?.focus({preventScroll:true});});
  picker.querySelector('[data-pick]')?.focus({preventScroll:true});
}
function renderMarkers(){
  if(!map)return;
  for(const m of markers.values())m.remove();markers.clear();
  for(const b of results.filter(hasCoordinates)){
    const marker=L.marker([b.lat,b.lng],{icon:icon(b.id===active),title:b.nameJa,alt:b.nameJa,keyboard:true}).addTo(map);
    marker.on('click',()=>markerClick(b));markers.set(b.id,marker);
  }
  updateLabels();
}
function renderList(){
  $('building-list').innerHTML=results.length?results.map(b=>`<article class="building-card${b.id===active?' is-active':''}" data-id="${e(b.id)}"><div class="card-meta"><span>${e(b.prefecture)} · ${e(b.municipality)}</span><time>${e(b.completionYear??'年代未確認')}</time></div><h2><a href="${e(articleUrl(b))}">${e(b.nameJa)}</a></h2><p class="card-architect">${e((b.architects||[]).join(' / '))}</p><p class="card-deck">${e(b.oneLiner)}</p><div class="card-actions"><span class="type-label">${e(b.buildingTypes?.[0]||'建築')}</span>${b.visit?.status==='closed'?'<span class="closed-badge">休館中</span>':''}${hasCoordinates(b)?`<button class="map-link" type="button" data-map="${e(b.id)}" aria-label="${e(b.nameJa)}を地図で見る">地図で見る ↗</button>`:'<span class="muted">位置を確認中</span>'}</div></article>`).join(''):'<div class="empty-state"><p>条件に合う建築がありません。</p><button id="empty-reset" class="secondary-button" type="button">条件をクリア</button></div>';
  $('empty-reset')?.addEventListener('click',reset);
  $('building-list').querySelectorAll('[data-map]').forEach(button=>button.onclick=()=>{setView(window.innerWidth<=700?'map':'split');showOne(byId.get(button.dataset.map));});
  $('building-list').querySelectorAll('[data-id]').forEach(card=>{card.onmouseenter=()=>select(card.dataset.id,{commit:false});card.onmouseleave=()=>select(active,{commit:false});card.onfocusin=()=>select(card.dataset.id,{commit:false});card.onfocusout=()=>select(active,{commit:false});});
}
function fitResults(){
  const points=results.filter(hasCoordinates).map(b=>[b.lat,b.lng]);if(!map||!points.length)return;
  if(points.length===1)map.setView(points[0],17,{animate:!reduceMotion});else map.fitBounds(points,{padding:[45,65],maxZoom:14,animate:!reduceMotion});
}
function saveUrl(){
  const u=new URL(location.href);u.search='';
  for(const[k,v]of Object.entries(filters()))if(v&&!(k==='region'&&v==='kanto')&&!(k==='sort'&&v==='name'))u.searchParams.set(k,v);
  if(active)u.searchParams.set('building',active);
  history.replaceState(null,'',u);
}
function apply({fit=true}={}){
  results=filterBuildings(all,filters());if(!results.some(b=>b.id===active))active=null;
  closePicker();renderList();renderMarkers();
  const mapped=results.filter(hasCoordinates).length;
  $('result-summary').textContent=`${results.length}件 / 全${all.length}件${mapped<results.length?` · 位置確認中 ${results.length-mapped}件`:''}`;
  const f=filters();$('active-filters').textContent=[f.region==='kanto'?'関東':f.region==='all'?'全国':f.region,f.query,f.architect,f.type,ERAS[f.era],VISITS[f.visit]].filter(Boolean).join(' / ');
  saveUrl();if(fit)fitResults();
}
function reset(){for(const[k,c]of Object.entries(controls))c.value=k==='region'?'all':k==='sort'?'name':'';active=null;apply();}
function setView(view){
  if(view==='split'&&window.innerWidth<=700)view='map';
  document.querySelector('.explore-layout').dataset.view=view;
  document.querySelectorAll('[data-view][type="button"]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.view===view)));
  if(map)requestAnimationFrame(()=>map.invalidateSize());
}
function fillOptions(control,values){for(const value of values){const option=document.createElement('option');option.value=value;option.textContent=value;control.append(option);}}
async function boot(){
  const initial=new URLSearchParams(location.search);
  try{
    const response=await fetch('data/map-index.json');if(!response.ok)throw Error(`HTTP ${response.status}`);all=await response.json();if(!Array.isArray(all))throw Error('建築データの形式が不正です');byId=new Map(all.map(b=>[b.id,b]));
    fillOptions(controls.region,[...new Set(all.map(b=>b.prefecture))].sort((a,b)=>(KANTO.indexOf(a)<0?99:KANTO.indexOf(a))-(KANTO.indexOf(b)<0?99:KANTO.indexOf(b))||a.localeCompare(b,'ja')));
    for(const[key,field]of [['architect','architects'],['type','buildingTypes']])fillOptions(controls[key],[...new Set(all.flatMap(b=>b[field]||[]))].sort((a,b)=>a.localeCompare(b,'ja')));
    for(const[k,c]of Object.entries(controls)){if(initial.has(k)){c.value=initial.get(k);if(k==='region'&&!c.value)c.value='kanto';}}
    if(['era','visit','sort'].some(k=>initial.has(k))){$('extra-filters').hidden=false;$('more-filters').setAttribute('aria-expanded','true');}
    $('overlap-picker').addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();event.stopPropagation();closePicker({restoreFocus:true});}});
    initMap();setView(!map?'list':window.innerWidth<=700?'map':'split');
    let timer;Object.entries(controls).forEach(([k,c])=>c.addEventListener(k==='query'?'input':'change',()=>{clearTimeout(timer);if(k==='query')timer=setTimeout(()=>apply(),180);else apply();}));
    $('filters').onsubmit=event=>{event.preventDefault();clearTimeout(timer);apply();};
    $('reset-filters').onclick=()=>{clearTimeout(timer);reset();};
    $('more-filters').onclick=()=>{const expanded=$('more-filters').getAttribute('aria-expanded')==='true';$('more-filters').setAttribute('aria-expanded',String(!expanded));$('extra-filters').hidden=expanded;};
    $('fit-results').onclick=fitResults;
    $('show-kanto').onclick=()=>{controls.region.value='kanto';apply();};
    $('show-japan').onclick=()=>{controls.region.value='all';apply({fit:false});if(map)map.fitBounds([[24,123],[46,146]],{padding:[20,40],animate:!reduceMotion});};
    document.querySelectorAll('[data-view][type="button"]').forEach(button=>button.onclick=()=>setView(button.dataset.view));
    window.matchMedia('(max-width:700px)').addEventListener('change',()=>setView(document.querySelector('.explore-layout').dataset.view));
    apply();
    const linked=byId.get(initial.get('building'));
    if(linked){if(!results.some(b=>b.id===linked.id)){for(const[k,c]of Object.entries(controls))c.value=k==='region'?linked.prefecture:k==='sort'?'name':'';apply();}showOne(linked);}
  }catch(error){console.error(error);$('result-summary').textContent='データを読み込めませんでした';$('building-list').innerHTML='<div class="empty-state"><p>通信状況をご確認のうえ、再読み込みしてください。</p><a href="catalogue.html">建築一覧を開く</a></div>';}
}
boot();
