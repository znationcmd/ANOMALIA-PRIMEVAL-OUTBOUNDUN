import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState,equip,unequip,consume,weight} from '../src/systems.js';
import {syncInventory,moveStack,takeInHands,splitStack,mergeStacks,dropStack,nearbyDrops,pickupDrop,sortInventory,fits} from '../src/inventory.js';
const state=()=>({...initialState(),position:{x:0,z:0},underground:null});
const totals=s=>Object.fromEntries([...new Set(s.inventoryStacks.map(t=>t.id))].map(id=>[id,s.inventoryStacks.filter(t=>t.id===id).reduce((n,t)=>n+t.count,0)]));
test('inventory migration preserves quantities; splitting and sorting never duplicate items',()=>{
 const s=state();s.inventory={ammo:48,water:2,pistol:1,wood:5};syncInventory(s);const before=totals(s);
 const ammo=s.inventoryStacks.find(t=>t.id==='ammo');assert.ok(splitStack(s,ammo.uid,13).ok);assert.equal(s.inventoryStacks.filter(t=>t.id==='ammo').length,2);
 assert.deepEqual(totals(s),before);mergeStacks(s);sortInventory(s,'weight');assert.deepEqual(totals(s),before);
 for(const t of s.inventoryStacks)if(t.container!=='overflow')assert.ok(fits(s,t,t.container,t.x,t.y,t.uid));
});
test('grid rejects overlapping items and invalid rotation without changing positions',()=>{
 const s=state();s.inventory={wood:5,water:2};syncInventory(s);const [a,b]=s.inventoryStacks;
 const before=structuredClone(b);assert.equal(moveStack(s,b.uid,a.container,a.x,a.y).ok,false);assert.deepEqual(b,before);
 assert.equal(moveStack(s,b.uid,'missing',0,0).ok,false);assert.deepEqual(b,before);
});
test('hands and quickbar state survive serialization; consuming a held item updates the hands',()=>{
 const s=state();syncInventory(s);const water=s.inventoryStacks.find(t=>t.id==='water');assert.ok(takeInHands(s,water.uid).ok);assert.equal(s.hands,'water');
 while(s.inventory.water>0)consume(s,'water');syncInventory(s);assert.equal(s.hands,null);
 const pistol=s.inventoryStacks.find(t=>t.id==='pistol');takeInHands(s,pistol.uid);s.quickbar[3]='pistol';const restored=JSON.parse(JSON.stringify(s));syncInventory(restored);assert.equal(restored.hands,'pistol');assert.equal(restored.quickbar[3],'pistol');
});
test('dropping and picking up obey distance and weight and conserve quantities',()=>{
 const s=state();s.inventory={water:2};syncInventory(s);const id=s.inventoryStacks[0].uid;
 dropStack(s,id,1);assert.equal(s.inventory.water,1);assert.equal(nearbyDrops(s).length,1);
 const uid=s.groundDrops[0].uid;s.position.x=20;assert.equal(pickupDrop(s,uid).ok,false);assert.equal(s.inventory.water,1);
 s.position.x=0;assert.equal(pickupDrop(s,uid).ok,true);assert.equal(s.inventory.water,2);assert.equal(s.groundDrops.length,0);
 dropStack(s,s.inventoryStacks[0].uid,1);s.inventory.stone=100;syncInventory(s);assert.equal(pickupDrop(s,s.groundDrops[0].uid).ok,false);assert.equal(s.inventory.water,1);
});
test('removing a loaded backpack retains overflow items instead of deleting them',()=>{
 const s=state();s.inventory={backpack:1,rifle:5,water:12};equip(s,'backpack');syncInventory(s);const before=totals(s);unequip(s,'back');syncInventory(s);
 for(const [id,n]of Object.entries(before))assert.equal(totals(s)[id],n);
 assert.ok(s.inventoryStacks.some(t=>t.container==='overflow'));assert.ok(weight(s)>0);
});
