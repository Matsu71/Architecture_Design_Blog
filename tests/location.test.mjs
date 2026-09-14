import test from 'node:test';
import assert from 'node:assert/strict';
import {isJapanCoordinate, locationLabel, nearbyScreenPoints, pointInRing} from '../assets/location.mjs';

test('coordinate validation rejects coerced, missing and nonfinite values',()=>{
  for (const value of [null,undefined,'35',NaN,Infinity]) assert.equal(isJapanCoordinate(value,139),false);
  assert.equal(isJapanCoordinate(35,139),true);
});
test('location labels never promote a facility point to an entrance',()=>{
  assert.equal(locationLabel({status:'cross-checked',precision:'building'}),'建物位置を照合（入口未照合）');
  assert.equal(locationLabel({status:'cross-checked',precision:'facility'}),'施設位置を照合（入口未照合）');
  assert.equal(locationLabel({status:'cross-checked',precision:'entrance'}),'公開入口の位置を照合');
});
test('all thirty coincident records remain selectable without coordinate mutation',()=>{
  const data=Array.from({length:30},(_,i)=>({id:String(i),lat:35,lng:139}));
  const before=JSON.stringify(data);
  assert.equal(nearbyScreenPoints(data,data[0],p=>({x:p.lng,y:p.lat})).length,30);
  assert.equal(JSON.stringify(data),before);
});
test('withheld and nonfinite points never enter picker',()=>{
  const anchor={lat:35,lng:139};
  assert.deepEqual(nearbyScreenPoints([anchor,{lat:35,lng:139,location:{status:'withheld'}},{lat:NaN,lng:139}],anchor,p=>({x:p.lng,y:p.lat})),[anchor]);
});
test('point-in-ring distinguishes inside, outside, boundary and invalid ring',()=>{
  const ring=[[139,35],[139.1,35],[139.1,35.1],[139,35.1],[139,35]];
  assert.equal(pointInRing(35.05,139.05,ring),true);
  assert.equal(pointInRing(35.2,139.05,ring),false);
  assert.equal(pointInRing(35,139.05,ring),true);
  assert.equal(pointInRing(35.05,139.05,ring.slice(0,-1)),false);
});
