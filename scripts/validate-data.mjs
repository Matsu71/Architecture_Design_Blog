import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {hasCoordinates,duplicateCoordinates,safeUrl,localPhotoPath,VISITS,ERAS} from '../assets/core.mjs';
import {pointInRing} from '../assets/location.mjs';
export function validDate(value,today=new Date().toISOString().slice(0,10)) {
  if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(value)||value>today)return false;
  const d=new Date(`${value}T00:00:00Z`);
  return Number.isFinite(d.getTime())&&d.toISOString().slice(0,10)===value;
}
export function validate(data,{today=new Date().toISOString().slice(0,10)}={}) {
  const errors=[],warnings=[],ids=new Set(),slugs=new Set();
  if(!Array.isArray(data))return {errors:['データは配列である必要があります'],warnings};
  for(const b of data){
    if(!b||typeof b!=='object'||Array.isArray(b)){errors.push('建物レコードが不正');continue;}
    const label=b.id||'(idなし)',bad=message=>errors.push(`${label}: ${message}`);
    for(const field of ['id','slug','nameJa','prefecture','municipality','address','oneLiner','summary'])
      if(typeof b[field]!=='string'||!b[field].trim())bad(`${field}が未入力`);
    if(ids.has(b.id))bad('ID重複');ids.add(b.id);
    if(slugs.has(b.slug))bad('slug重複');slugs.add(b.slug);
    if(!/^[a-z0-9-]+$/.test(b.id||'')||!/^[a-z0-9-]+$/.test(b.slug||''))bad('IDまたはslugが不正');
    for(const field of ['completionYear',...(b.openingYear==null?[]:['openingYear'])])
      if(!Number.isInteger(b[field])||b[field]<1||b[field]>Number(today.slice(0,4)))bad(`${field}が不正`);
    if(!Object.hasOwn(ERAS,b.era))bad('年代区分が不正');
    for(const field of ['architects','buildingTypes'])if(!Array.isArray(b[field])||!b[field].length||b[field].some(v=>typeof v!=='string'||!v.trim()))bad(`${field}が不正`);
    const loc=b.location||{};
    if(!['address-matched','cross-checked','withheld'].includes(loc.status))bad('位置確認状態が不正');
    if(!hasCoordinates(b)&&loc.status!=='withheld')bad('位置不明はwithheldにし、仮座標を置かない');
    if(loc.status==='withheld'&&(b.lat!=null||b.lng!=null))bad('非表示の位置に仮座標を残さない');
    if(!['facility','building','entrance','unknown'].includes(loc.precision))bad('位置精度が未定義');
    if(!validDate(loc.checkedAt,today)||!validDate(b.verification?.lastVerified,today))bad('位置または基本情報の確認日が不正');
    const sources=new Set();
    if(!Array.isArray(b.sources)||!b.sources.length)bad('出典が未登録');
    for(const s of Array.isArray(b.sources)?b.sources:[]){
      if(!s||typeof s!=='object'){bad('出典形式が不正');continue;}
      if(!s.id||sources.has(s.id))bad('出典IDの欠落・重複');sources.add(s.id);
      if(!safeUrl(s.url))bad(`${s.id}: 出典URLが不正`);
      if(!s.title||!s.publisher||!s.scope||!validDate(s.checkedAt,today))bad(`${s.id}: 出典の確認情報が不足`);
    }
    const checkRefs=(refs,field)=>{
      if(!Array.isArray(refs)||!refs.length){bad(`${field}の出典なし`);return;}
      for(const id of refs)if(!sources.has(id))bad(`${field}の出典 ${id} が存在しない`);
    };
    for(const field of ['nameJa','completionYear','architects','address','buildingTypes',...(b.openingYear==null?[]:['openingYear'])]){
      const fact=b.verification?.fields?.[field];checkRefs(fact?.sourceIds,field);
      if(!validDate(fact?.checkedAt,today))bad(`${field}の確認日が不正`);
    }
    checkRefs(b.articleSourceIds,'本文');checkRefs(loc.sourceIds,'位置');
    for(const c of Array.isArray(b.components)?b.components:[])checkRefs(c.sourceIds,`構成要素 ${c.part}`);
    // A label alone is not enough evidence for a precise building or entrance pin.
    if(loc.precision==='building'){
      if(loc.status!=='cross-checked'||loc.evidence?.kind!=='building-outline'||!pointInRing(b.lat,b.lng,loc.evidence?.ring))bad('建物輪郭の証拠内にピンがありません');
      checkRefs(loc.evidence?.sourceIds,'建物輪郭');
      checkRefs(loc.evidence?.identitySourceIds,'棟の同定');
      if(!validDate(loc.evidence?.reviewedAt,today))bad('建物輪郭の確認日が不正');
      if(!(loc.evidence?.identitySourceIds||[]).some(id=>b.sources?.some(s=>s.id===id&&s.sourceType==='official')))bad('棟の同定に公式の根拠がありません');
      if(loc.evidence?.osmWayId&&(!loc.evidence.attribution||loc.evidence.license!=='ODbL 1.0'||!safeUrl(loc.evidence.licenseUrl)))bad('輪郭データのライセンス表示が不足');
    }
    if(loc.precision==='entrance'){
      if(loc.status!=='cross-checked'||loc.evidence?.kind!=='public-entrance'||loc.evidence?.lat!==b.lat||loc.evidence?.lng!==b.lng)bad('公開入口の照合証拠が不足');
      checkRefs(loc.evidence?.sourceIds,'公開入口');
    }
    if(loc.status==='cross-checked'&&loc.precision==='facility'&&(!loc.evidence?.method||!loc.evidence?.sourceIds?.length))bad('施設座標の照合方法と証拠が不足');
    if(!Object.hasOwn(VISITS,b.visit?.status))bad('見学状態が不正');
    if(!safeUrl(b.visit?.officialUrl)||!validDate(b.visit?.lastChecked,today))bad('見学案内または確認日が不正');
    if(b.visit?.status==='closed'||b.visit?.sourceIds?.length)checkRefs(b.visit.sourceIds,'見学');
    if(!b.verification?.pending?.length&&loc.precision==='facility')warnings.push(`${label}: 入口・棟の未照合状態を明示してください`);
    if(b.photo){
      const p=b.photo;
      if(!localPhotoPath(p.src)||!p.alt||!p.author||!p.caption||!p.modifications||!validDate(p.checkedAt,today))bad('写真の表示・確認情報が不足');
      if(!Number.isInteger(p.width)||!Number.isInteger(p.height)||p.width<1||p.height<1)bad('写真の寸法が不正');
      if(p.license!=='CC BY-SA 3.0'||p.licenseUrl!=='https://creativecommons.org/licenses/by-sa/3.0/'||!safeUrl(p.sourceUrl))bad('写真の許諾が未対応または不足');
      if(!/^[a-f0-9]{64}$/.test(p.sha256||''))bad('写真の照合ハッシュが不足');
    }
    if((b.oneLiner||'').length>60)warnings.push(`${label}: 一覧説明が60文字を超えています`);
  }
  for(const g of duplicateCoordinates(data.filter(b=>b&&typeof b==='object')))warnings.push(`座標重複 ${g.coordinate}: ${g.ids.join(', ')}（レコードを消さず棟を照合）`);
  return {errors,warnings};
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
  const data=JSON.parse(await readFile(new URL('../data/buildings.json',import.meta.url),'utf8'));
  const result=validate(data);
  console.log(JSON.stringify({buildings:data.length,prefectures:new Set(data.map(b=>b.prefecture)).size,...result},null,2));
  if(result.errors.length)process.exitCode=1;
}
