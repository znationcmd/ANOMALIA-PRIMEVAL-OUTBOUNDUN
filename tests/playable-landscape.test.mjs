import test from 'node:test';
import assert from 'node:assert/strict';
import {playableHeight,playableNormal} from '../scripts/vehicle-assets/playable-landscape.mjs';
test('existing house parcels and complete driving corridor remain exactly flat',()=>{
 for(let x=-68;x<=68;x++)for(let z=-57;z<=57;z++)assert.equal(playableHeight(x,z),0);
 for(let z=9;z<=21;z++)for(let x=-100;x<=100;x++)assert.equal(playableHeight(x,z),0);
});
test('forest perimeter has bounded relief and finite normalized surface normals',()=>{
 let relief=0;
 for(let x=-100;x<=100;x+=2)for(let z=-100;z<=100;z+=2){
  const h=playableHeight(x,z);assert.ok(h>=0&&h<=3.2);if(h>.5)relief++;
  const normal=playableNormal(x,z);assert.ok(normal.every(Number.isFinite));assert.ok(Math.abs(Math.hypot(...normal)-1)<1e-10);
  assert.ok(normal[1]>.9,'slope must remain walkable');
 }
 assert.ok(relief>1000);
});
