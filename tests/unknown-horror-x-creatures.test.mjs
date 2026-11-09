import test from 'node:test';
import assert from 'node:assert/strict';
import {HORROR_CREATURES,HORROR_LAYERS,HORROR_SPAWN_PROFILES,
 chooseHorrorSpecies,generateHorrorSpawns,mayTameHorrorCreature} from '../src/unknown-horror-x-creatures.js';

test('five layers have zombies, wild animals and dinosaurs across the world',()=>{
 assert.equal(Object.keys(HORROR_LAYERS).length,5);
 const kinds=new Set(Object.values(HORROR_CREATURES).map(c=>c.kind));
 assert.deepEqual([...kinds].sort(),['animal','dinosaur','zombie']);
 for(const layer of Object.keys(HORROR_LAYERS)){
  assert.ok(Object.values(HORROR_CREATURES).some(c=>c.layers.includes(layer)&&c.kind==='zombie'));
  assert.ok(Object.values(HORROR_CREATURES).some(c=>c.layers.includes(layer)&&c.kind==='animal'));
  assert.ok(Object.values(HORROR_CREATURES).some(c=>c.layers.includes(layer)&&c.kind==='dinosaur'));
  assert.ok(Math.abs(Object.values(HORROR_SPAWN_PROFILES[layer]).reduce((a,b)=>a+b,0)-1)<1e-9);
 }
});
test('stable spawn generation and strict water filtering',()=>{
 const args={layer:'surface',cx:1,cz:2,limit:8};
 assert.deepEqual(generateHorrorSpawns(args),generateHorrorSpawns(args));
 assert.equal(generateHorrorSpawns({...args,land:false}).length,0);
 assert.equal(generateHorrorSpawns({...args,layer:'metro',isFlooded:true}).length,0);
 assert.equal(generateHorrorSpawns({...args,limit:999}).length,32);
 assert.equal(generateHorrorSpawns({...args,layer:'invalid'}).length,0);
});
test('low danger keeps dangerous creatures out',()=>{
 const low=generateHorrorSpawns({layer:'undergroundCity',cx:2,cz:2,limit:20,maxDanger:2});
 assert.ok(low.every(c=>c.danger<=2));
});
test('zombies never tame; wild animals and dinosaurs follow taming flag',()=>{
 assert.equal(mayTameHorrorCreature('zombie_colosse'),false);
 assert.equal(mayTameHorrorCreature('raptor'),true);
 assert.equal(mayTameHorrorCreature('wolf'),true);
 assert.equal(mayTameHorrorCreature('giant_rat'),false);
 assert.equal(mayTameHorrorCreature('unknown'),false);
});
test('selection only returns creatures of requested layer',()=>{
 for(const layer of Object.keys(HORROR_LAYERS)){
  for(let i=0;i<100;i++){
   const chosen=chooseHorrorSpecies(layer,i/100);
   assert.ok(chosen&&HORROR_CREATURES[chosen].layers.includes(layer));
  }
 }
});
