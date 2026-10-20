import test from 'node:test';
import assert from 'node:assert/strict';
import {restAtBed,collectFarmProduce,sleepTick} from '../src/homestead.js';

const survivor=()=>({position:{x:0,z:0},health:100,sleep:10,stamina:5,inventory:{}});
test('rest needs a nearby bed and live survivor, and cooldown survives save reload',()=>{
 const state=survivor(), bed=[{id:'bed-1',type:'bed',x:0,z:0}];
 assert.equal(restAtBed(state,[{...bed[0],x:10}],120000).ok,false);
 state.health=0;assert.equal(restAtBed(state,bed,120000).ok,false);state.health=100;
 assert.equal(restAtBed(state,bed,120000).ok,true);
 assert.equal(state.sleep,75);assert.equal(state.stamina,40);
 const reloaded=JSON.parse(JSON.stringify(state));
 assert.equal(restAtBed(reloaded,bed,120001).ok,false);
 assert.equal(restAtBed(reloaded,bed,180000).ok,true);
 assert.equal(reloaded.sleep,100);
});
test('farm produces legacy-compatible items and persists independent station cooldowns',()=>{
 const state=survivor();
 const cows=[{id:'cow-1',type:'cow_pen',x:0,z:0}];
 assert.equal(collectFarmProduce(state,cows,1000000).ok,true);
 assert.equal(state.inventory.milk,2);
 assert.equal(collectFarmProduce(state,cows,1000001).ok,false);
 const reloaded=JSON.parse(JSON.stringify(state));
 assert.equal(collectFarmProduce(reloaded,cows,1000002).ok,false);
 assert.equal(collectFarmProduce(reloaded,[{id:'coop-1',type:'chicken_coop',x:0,z:0}],1000002).ok,true);
 assert.equal(reloaded.inventory.eggs,3);
 assert.equal(collectFarmProduce(reloaded,[{id:'hive-1',type:'beehive',x:0,z:0}],1000002).ok,true);
 assert.equal(reloaded.inventory.honey,1);
});
test('remote farm and invalid clock leave inventory and cooldown unchanged',()=>{
 const state=survivor(), before=JSON.stringify(state);
 assert.equal(collectFarmProduce(state,[{id:'cow',type:'cow_pen',x:8,z:0}],1000000).ok,false);
 assert.equal(collectFarmProduce(state,[],NaN).ok,false);
 assert.equal(JSON.stringify(state),before);
});
test('fatigue updates remain bounded and ignore invalid elapsed time',()=>{
 const state=survivor();
 sleepTick(state,NaN);assert.equal(state.sleep,10);
 sleepTick(state,10000,{sprinting:true});
 assert.ok(state.sleep>=0&&state.sleep<=100);assert.ok(state.sleep>9);
});
