import test from 'node:test';
import assert from 'node:assert/strict';
import {isCargoFloorHit} from './audit-bmw-e39-cargo.mjs';
const hit={part:'body',material:'frame',pointMetresYUp:[-2.1,.65,0],normalYUp:[0,1,0]};
test('horizontal fixed floor below clear cargo space is accepted',()=>assert(isCargoFloorHit(hit)));
test('a vertical lining at floor height is not a floor',()=>assert(!isCargoFloorHit({...hit,normalYUp:[1,0,0]})));
test('back-facing underside cannot masquerade as an upward floor',()=>assert(!isCargoFloorHit({...hit,normalYUp:[0,-1,0]})));
test('raised floor without twenty centimetres clearance is rejected',()=>assert(!isCargoFloorHit(hit,.80)));
test('moving lid cannot masquerade as a cargo floor',()=>assert(!isCargoFloorHit({...hit,part:'trunk'})));
test('unknown or non-finite floor evidence is rejected',()=>{
 for(const row of [null,{...hit,normalYUp:[0,0,0]},{...hit,normalYUp:[0,NaN,0]}, {...hit,pointMetresYUp:[0,NaN,0]}])
  assert(!isCargoFloorHit(row));
});
