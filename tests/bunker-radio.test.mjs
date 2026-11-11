import test from 'node:test';
import assert from 'node:assert/strict';
import {
 RADIO_BUNKERS,RADIO_ANTENNAS,ACCESS_SITES,ACCESS_ITEMS,
 radioTime,activeBunkers,unlockRadioBunker,radioDoorOpen,claimRadioBunkerLoot,
 broadcast,decodeBroadcast,decodeNumbers,encodeNumbers,canHearBroadcast
} from '../src/bunker-radio.js';
import {SITES,unlockSite,initialState} from '../src/mechanics.js';

test('23 original bunkers are split into mechanical keys, punch cards, and Morse',()=>{
 assert.equal(RADIO_BUNKERS.length,23);
 assert.deepEqual(
  [RADIO_BUNKERS.filter(b=>b.access==='key').length,
   RADIO_BUNKERS.filter(b=>b.access==='card').length,
   RADIO_BUNKERS.filter(b=>b.access==='morse').length],[8,8,7]);
 assert.equal(new Set(RADIO_BUNKERS.map(b=>b.grid)).size,23);
 assert.ok(RADIO_BUNKERS.filter(b=>b.building!=='military').length>=17);
 assert.ok(RADIO_ANTENNAS.length>=6);
 const access=new Set(ACCESS_SITES.map(s=>s.item));
 for(const bunker of RADIO_BUNKERS.filter(b=>b.required))assert.ok(access.has(bunker.required),bunker.required);
 assert.ok(SITES.some(s=>s.type==='radio-bunker'));
});

test('discovered keys/cards enter the inventory and unlock only their matching doors',()=>{
 const state=initialState();state.elapsed=940;
 for(const category of ['key','card']){
  const bunker=RADIO_BUNKERS.find(b=>b.access===category);
  state.position={x:bunker.x,z:bunker.z};
  assert.equal(unlockRadioBunker(state,bunker.id,'').ok,false);
  const cache=ACCESS_SITES.find(s=>s.item===bunker.required);
  const result=unlockSite(state,cache);
  assert.equal(result.ok,true);
  assert.equal(state.inventory[cache.item],1);
  assert.equal(unlockSite(state,cache).ok,false);
  const opened=unlockRadioBunker(state,bunker.id,'');
  assert.equal(opened.ok,true,opened.message);
  assert.equal(radioDoorOpen(state,bunker.id),true);
  state.elapsed+=200;
  assert.equal(radioDoorOpen(state,bunker.id),false);
 }
});

test('nightly Morse is audible only with radio and battery near relay, and code opens correct door',()=>{
 const state=initialState();state.elapsed=940;
 const a=RADIO_ANTENNAS[0];state.position={x:a.x,z:a.z};
 assert.equal(canHearBroadcast(state,state.position),false);
 state.inventory.radio_transceiver=1;
 state.inventory.radio_battery=1;
 state.radioFrequency=80;
 assert.equal(canHearBroadcast(state,state.position),true);
 const active=activeBunkers(state);
 assert.equal(active.length,3);
 assert.ok(active.every(b=>b.access==='morse'));
 const t=broadcast(state);
 assert.equal(t.digits,t.grid+t.digits.slice(6));
 assert.equal(decodeNumbers(t.morse),t.digits);
 assert.equal(encodeNumbers(t.digits),t.morse);
 const decoded=decodeBroadcast(t.morse);
 assert.equal(decoded.bunker.id,t.bunkerId);
 const bunker=RADIO_BUNKERS.find(b=>b.id===t.bunkerId);
 state.position={x:bunker.x,z:bunker.z};
 assert.equal(unlockRadioBunker(state,bunker.id,'00000').ok,false);
 assert.equal(unlockRadioBunker(state,bunker.id,t.digits.slice(6)).ok,true);
 const loot=claimRadioBunkerLoot(state,bunker.id);
 assert.equal(loot.ok,true);
 assert.equal(claimRadioBunkerLoot(state,bunker.id).ok,false);
});

test('no inactive Morse bunker is unlocked during daylight and position validation is enforced',()=>{
 const bunker=RADIO_BUNKERS.find(b=>b.access==='morse');
 const state=initialState();state.elapsed=600;state.position={x:bunker.x,z:bunker.z};
 assert.equal(radioTime(state.elapsed).onAir,false);
 assert.deepEqual(activeBunkers(state),[]);
 assert.equal(unlockRadioBunker(state,bunker.id,'0000').ok,false);
 state.elapsed=950;state.position={x:0,z:0};
 assert.equal(unlockRadioBunker(state,bunker.id,'0000').ok,false);
 assert.throws(()=>decodeBroadcast('...- ...'),/incomplète|invalide/);
});
