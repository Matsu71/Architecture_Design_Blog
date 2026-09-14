import {isJapanCoordinate, locationLabel} from './location.mjs';
export const KANTO = ['東京都','神奈川県','埼玉県','千葉県','茨城県','栃木県','群馬県'];
export const ERAS = {traditional:'江戸以前','early-modern':'明治',modern:'大正・昭和前期',postwar:'戦後',contemporary:'現代'};
export const OPENING_LABELS = ['開館','開校','開業','供用'];
export const VISITS = {public:'公開施設',limited:'公開条件あり',reservation:'予約制','exterior-only':'外観のみ',private:'非公開',closed:'休館・閉館',demolished:'現存せず',unknown:'見学要確認'};
export function escapeHtml(value = '') { return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
export function safeUrl(value) { try { const u = new URL(value); return ['https:','http:'].includes(u.protocol) ? u.href : ''; } catch { return ''; } }
export function normalize(value) { return String(value ?? '').normalize('NFKC').toLocaleLowerCase('ja').replace(/[\u30a1-\u30f6]/g, c => String.fromCharCode(c.charCodeAt(0)-0x60)); }
export function hasCoordinates(b) { return !!b && isJapanCoordinate(b.lat,b.lng) && b.location?.status !== 'withheld'; }
export function searchText(b) { return normalize([b.nameJa,b.nameEn,...(b.aliases||[]),b.prefecture,b.municipality,b.area,b.address,...(b.architects||[]),...(b.buildingTypes||[]),...(b.styles||[]),...(b.materials||[]),b.oneLiner].join(' ')); }
export function filterBuildings(data, filters = {}) {
  const terms = normalize(filters.query).trim().split(/\s+/).filter(Boolean);
  return data.filter(b => (!filters.region || filters.region === 'all' || (filters.region === 'kanto' ? KANTO.includes(b.prefecture) : b.prefecture === filters.region))
    && (!filters.era || b.era === filters.era) && (!filters.type || (b.buildingTypes||[]).includes(filters.type))
    && (!filters.architect || (b.architects||[]).includes(filters.architect))
    && (!filters.visit || b.visit?.status === filters.visit)
    && terms.every(term => searchText(b).includes(term)))
    .sort((a,b) => filters.sort === 'oldest' ? (a.completionYear ?? Infinity)-(b.completionYear ?? Infinity) || a.nameJa.localeCompare(b.nameJa,'ja')
      : filters.sort === 'newest' ? (b.completionYear ?? -Infinity)-(a.completionYear ?? -Infinity) || a.nameJa.localeCompare(b.nameJa,'ja')
      : a.nameJa.localeCompare(b.nameJa,'ja'));
}
export function distanceMeters(a, b) {
  const rad = Math.PI / 180, dLat = (b.lat-a.lat)*rad, dLng=(b.lng-a.lng)*rad;
  const h = Math.sin(dLat/2)**2+Math.cos(a.lat*rad)*Math.cos(b.lat*rad)*Math.sin(dLng/2)**2;
  return 6371008.8*2*Math.asin(Math.sqrt(Math.min(1,h)));
}
export function duplicateCoordinates(data) {
  const groups = new Map();
  for (const b of data.filter(hasCoordinates)) { const key = `${b.lat.toFixed(6)},${b.lng.toFixed(6)}`; groups.set(key,[...(groups.get(key)||[]),b.id]); }
  return [...groups.entries()].filter(([,ids]) => ids.length>1).map(([coordinate,ids])=>({coordinate,ids}));
}
export function directionsUrl(b) { return 'https://www.google.com/maps/search/?api=1&query='+encodeURIComponent(`${b.nameJa} ${b.address||''}`); }
export function sourceLink(s) { const url=safeUrl(s.url); return url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(s.title||s.publisher||'出典')}</a>` : escapeHtml(s.title||'出典'); }
export function localPhotoPath(value) { return typeof value === 'string' && /^assets\/photos\/[a-z0-9-]+\.webp$/.test(value) ? value : ''; }
export function photoHtml(photo, root = './', compact = false) {
  if (!photo || !localPhotoPath(photo.src) || !safeUrl(photo.sourceUrl) || !safeUrl(photo.licenseUrl)) return '';
  const e = escapeHtml;
  return `<figure class="${compact?'card-photo':'building-photo'}"><img src="${e(root + photo.src)}" width="${Number(photo.width)}" height="${Number(photo.height)}" alt="${e(photo.alt)}" loading="lazy" decoding="async"><figcaption>${compact?'':`${e(photo.caption)}<br>`}写真：<a href="${e(safeUrl(photo.sourceUrl))}" target="_blank" rel="noopener noreferrer">${e(photo.author)}</a> · <a href="${e(safeUrl(photo.licenseUrl))}" target="_blank" rel="noopener noreferrer">${e(photo.license)}</a> · ${e(photo.modifications)}</figcaption></figure>`;
}
export function articleHtml(b, data = [], root = './') {
  const e=escapeHtml, sources=b.sources||[];
  const refs = ids => (ids||[]).map(id=> {const i=sources.findIndex(s=>s.id===id); return i<0?'':`<a class="citation" href="#source-${i+1}" aria-label="出典${i+1}">[${i+1}]</a>`;}).join('');
  const fact = (label,value,field) => `<div><dt>${label}</dt><dd>${e(value||'未確認')}${refs(b.verification?.fields?.[field]?.sourceIds)}</dd></div>`;
  const nearby=hasCoordinates(b)?data.filter(x=>x.id!==b.id&&hasCoordinates(x)).map(x=>({b:x,d:distanceMeters(b,x)})).filter(x=>x.d<20000).sort((a,c)=>a.d-c.d).slice(0,3):[];
  const coordinateStatus = locationLabel(b.location);
  const designNames=Array.isArray(b.designers)&&b.designers.length?b.designers.map(d=>d.role?`${d.name}（${d.role}）`:d.name):(b.architects||[]);
  const openingLabel=OPENING_LABELS.includes(b.openingLabel)?b.openingLabel:'開館';
  const factNotes=(b.factNotes||[]).map(n=>`<p class="fact-note">${e(n.text)}${refs(n.sourceIds)}</p>`).join('');
  return `<header class="article-heading"><p class="eyebrow">${e(b.prefecture)} / ${e(b.municipality)}</p><h1>${e(b.nameJa)}</h1><p class="article-deck">${e(b.oneLiner)}</p>${b.visit?.status==='closed'?`<aside class="visit-alert"><strong>休館・閉館</strong><p>${e(b.visit.note)}${refs(b.visit.sourceIds)}</p></aside>`:b.visit?.notice?`<aside class="visit-alert visit-alert-compact"><strong>${e(b.visit.notice)}</strong>${refs(b.visit.sourceIds)}</aside>`:''}</header>
  ${photoHtml(b.photo,root)}
  <dl class="facts">${fact('竣工',b.completionYear?`${b.completionYear}年`:'未確認','completionYear')}${fact('設計',designNames.join(' / '),'architects')}${b.openingYear?fact(openingLabel,`${b.openingYear}年`,'openingYear'):''}${fact('用途',(b.buildingTypes||[]).join(' / '),'buildingTypes')}${fact('所在地',b.address,'address')}</dl>${factNotes}
  <nav class="article-toc" aria-label="記事の目次"><a href="#highlights">見どころ</a><a href="#materials">構造・素材</a><a href="#visit">見学</a><a href="#sources">出典</a></nav>
  <section id="highlights"><h2>見どころ</h2><p>${e(b.summary)}${refs(b.articleSourceIds)}</p><ul class="highlights">${(b.highlights||[]).map(x=>`<li>${e(x)}</li>`).join('')}</ul></section>
  <section id="materials"><h2>構造・素材</h2>${(b.components||[]).length?(b.components||[]).map(c=>`<details class="component"><summary>${e(c.part)}<span>${e(c.material)}</span></summary><p>${e(c.description)}${refs(c.sourceIds)}</p>${c.origin?`<p>原材料：${e(c.origin)}${refs(c.sourceIds)}</p>`:''}</details>`).join(''):'<p class="muted">部位ごとの材料を資料で確認しています。外観だけでは判定しません。</p>'}</section>
  <section id="visit"><h2>見学</h2><p class="visit-status">${e(VISITS[b.visit?.status]||VISITS.unknown)} · 確認 ${e(b.visit?.lastChecked||'未確認')}</p><p>${e(b.visit?.note||'公開日・料金・予約条件は、訪問前に公式サイトでご確認ください。')}${refs(b.visit?.sourceIds)}</p><div class="article-actions"><a class="primary-button" href="${e(directionsUrl(b))}" target="_blank" rel="noopener noreferrer">行き方</a>${safeUrl(b.visit?.officialUrl)?`<a class="secondary-button" href="${e(safeUrl(b.visit.officialUrl))}" target="_blank" rel="noopener noreferrer">公式案内</a>`:''}<a class="secondary-button" href="${e(root)}?building=${e(encodeURIComponent(b.id))}#explore">地図で見る</a></div><p class="muted">${coordinateStatus}。地図のピンは入口を保証するものではありません。${b.location?.note?` ${e(b.location.note)}`:''}</p></section>
  ${nearby.length?`<section><h2>近くの建築</h2><div class="nearby">${nearby.map(({b:x,d})=>`<a href="${e(root)}building.html?id=${e(encodeURIComponent(x.id))}"><strong>${e(x.nameJa)}</strong><span>直線 ${(d/1000).toFixed(1)} km</span></a>`).join('')}</div></section>`:''}
  <section id="sources"><h2>出典・確認状況</h2><p class="muted">基本情報と位置を別々に確認しています。全項目の検証完了を意味しません。</p><dl class="verification"><div><dt>基本情報</dt><dd>${e(b.verification?.status === 'basic-checked'?'一次資料と照合':'確認中')}</dd></div><div><dt>位置</dt><dd>${coordinateStatus}${refs(b.location?.sourceIds)}</dd></div><div><dt>資料確認日</dt><dd>${e(b.verification?.lastVerified||'未確認')}</dd></div></dl><ol class="sources">${sources.map((s,i)=>`<li id="source-${i+1}">${sourceLink(s)}<small>${e(s.publisher||'')} · ${e(s.checkedAt||'確認日未登録')}${s.scope?` · ${e(s.scope)}`:''}</small></li>`).join('')}</ol>${(b.verification?.pending||[]).length?`<details><summary>未確認の項目</summary><ul>${b.verification.pending.map(x=>`<li>${e(x)}</li>`).join('')}</ul></details>`:''}</section>`;
}
