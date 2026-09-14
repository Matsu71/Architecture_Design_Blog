// Offline contract fixture, not Leaflet and never loaded by the production app.
// It verifies our marker creation/selection logic, not OSM tiles or Leaflet rendering.
(()=>{
class MapFixture{
 constructor(id){this.el=document.getElementById(id);this.el.style.position='relative';this.events={};this.markers=[];this.zoom=8;this.center=[36,139];window.__mapFixture=this;}
 on(n,f){(this.events[n]??=[]).push(f);return this;}
 emit(n){for(const f of this.events[n]||[])f();}
 setView(p,z){this.center=p;this.zoom=z;this.invalidateSize();this.emit('zoomend');return this;}
 getZoom(){return this.zoom;}
 fitBounds(ps,o={}){this.center=[ps.reduce((s,p)=>s+p[0],0)/ps.length,ps.reduce((s,p)=>s+p[1],0)/ps.length];this.zoom=Math.min(8,o.maxZoom||8);this.invalidateSize();this.emit('zoomend');return this;}
 latLngToContainerPoint(p){const scale=256*Math.pow(2,this.zoom),w=this.el.clientWidth,h=this.el.clientHeight,x=w/2+(p[1]-this.center[1])/360*scale,y=h/2-(p[0]-this.center[0])/360*scale;return {x,y,distanceTo:q=>Math.hypot(x-q.x,y-q.y)};}
 invalidateSize(){for(const m of this.markers){const p=this.latLngToContainerPoint(m.coords);m.el.style.left=(p.x-12)+'px';m.el.style.top=(p.y-12)+'px';}return this;}
}
class MarkerFixture{
 constructor(coords,opts){this.coords=[...coords];this.opts=opts;this.el=document.createElement('div');this.el.style.position='absolute';this.el.setAttribute('role','button');this.el.tabIndex=0;this.el.title=opts.title;this.el.setAttribute('aria-label',opts.alt);this.setIcon(opts.icon);}
 addTo(map){this.map=map;map.markers.push(this);map.el.append(this.el);map.invalidateSize();return this;}
 on(n,f){this.el.addEventListener(n,e=>{e.stopPropagation();f(e);});return this;}
 remove(){this.el.remove();this.map.markers=this.map.markers.filter(m=>m!==this);}
 setIcon(i){this.el.className='leaflet-marker-icon '+i.className;this.el.innerHTML=i.html;return this;}
 setZIndexOffset(z){this.el.style.zIndex=z+1;return this;}
 getElement(){return this.el;}
 getTooltip(){return this.tooltip;}
 bindTooltip(t,opts){this.tooltip={text:t,opts};return this;}
 unbindTooltip(){this.tooltip=null;return this;}
 bindPopup(t){this.popup=t;return this;}
 openPopup(){let p=this.map.el.querySelector('.leaflet-popup');if(!p){p=document.createElement('div');p.className='leaflet-popup';this.map.el.append(p);}p.innerHTML=this.popup;return this;}
}
window.L={map:id=>new MapFixture(id),divIcon:x=>x,marker:(p,o)=>new MarkerFixture(p,o),tileLayer:()=>({addTo(){return this;},on(n,f){window.__tileError=f;return this;}})};
})();
