import test from 'node:test';
import assert from 'node:assert/strict';
import {createOfficialCharacterRegistry,sanitizePortableCharacter} from '../server/official-character-registry.mjs';
const survivor=()=>({
  schemaVersion:1,
  appearance:{head:'survivor-1',clothes:['jacket']},
  inventory:[{itemId:'rifle',count:1,container:'hands'},{itemId:'water',count:2,container:'backpack'}],
  hands:{itemId:'rifle'},worn:{vest:'plate'},
  survival:{health:79,hunger:42,thirst:66,fatigue:12,stamina:78,bodyTemperatureC:36.8}
});
const spawnPoints={
 '1PP':[{x:100,y:200,z:300},{x:500,y:700,z:800}],
 '3PP':[{x:1000,y:1200,z:1600},{x:1800,y:2000,z:2400}]
};
const servers={
 official1a:{category:'official',thirdPerson:false},
 official1b:{category:'official',thirdPerson:false},
 official3a:{category:'official',thirdPerson:true},
 official3b:{category:'official',thirdPerson:true}
};
const make=({now,pickIndex}={})=>createOfficialCharacterRegistry({servers,spawnPoints,cooldownMs:90000,now:now||(()=>100000),pickIndex:pickIndex||(()=>1)});
test('1PP official migration preserves hands, gear, appearance and vitals but forces a new spawn',()=>{
 let clock=100000;const r=make({now:()=>clock});
 const a=r.checkIn({playerId:'identity-123',serverId:'official1a'});
 assert.equal(a.switched,false);assert.equal(a.snapshot,null);
 assert.deepEqual(r.checkOut({playerId:'identity-123',serverId:'official1a',session:a.session,snapshot:survivor()}),{saved:true,revision:1,view:'1PP',characterSlot:1});
 assert.throws(()=>r.checkIn({playerId:'identity-123',serverId:'official1b'}),{code:'SERVER_HOP_COOLDOWN'});
 clock+=90000;
 const b=r.checkIn({playerId:'identity-123',serverId:'official1b'});
 assert.equal(b.switched,true);
 assert.deepEqual(b.spawn,spawnPoints['1PP'][1]);
 assert.deepEqual(b.snapshot,survivor());
 assert.deepEqual(b.snapshot.hands,{itemId:'rifle'});
 assert.equal(b.snapshot.survival.health,79);
 assert.equal(r.getStatus({playerId:'identity-123',serverId:'official1b'}).active,true);
});
test('1PP and 3PP never share a survivor, even for the same authenticated player',()=>{
 const r=make();
 const first=r.checkIn({playerId:'player1',serverId:'official1a'});
 r.checkOut({playerId:'player1',serverId:'official1a',session:first.session,snapshot:survivor()});
 const other=r.checkIn({playerId:'player1',serverId:'official3a'});
 assert.equal(other.snapshot,null);assert.equal(other.switched,false);assert.equal(other.view,'3PP');
 assert.equal(r._testingRecordCount(),2);
});
test('simultaneous server login and stale checkout are denied to prevent inventory duplication',()=>{
 const r=make();
 const a=r.checkIn({playerId:'player2',serverId:'official3a'});
 assert.throws(()=>r.checkIn({playerId:'player2',serverId:'official3b'}),{code:'CHARACTER_ALREADY_ONLINE'});
 assert.throws(()=>r.checkOut({playerId:'player2',serverId:'official3a',session:'stale-token',snapshot:survivor()}),{code:'STALE_SESSION'});
 r.checkOut({playerId:'player2',serverId:'official3a',session:a.session,snapshot:survivor()});
 assert.throws(()=>r.checkOut({playerId:'player2',serverId:'official3a',session:a.session,snapshot:survivor()}),{code:'STALE_SESSION'});
});
test('community is never accepted as official source or destination',()=>{
 const r=make();
 assert.throws(()=>r.checkIn({playerId:'player3',serverId:'community-test'}),{code:'NOT_OFFICIAL'});
 assert.throws(()=>r.checkOut({playerId:'player3',serverId:'community-test',session:'fake-token',snapshot:survivor()}),{code:'NOT_OFFICIAL'});
});
test('forbid vehicles, bases, caches, unknown world ownership and malformed inventory',()=>{
 for(const key of ['vehicles','bases','caches','tents','pose','world','serverId']){
  const item={...survivor(),[key]:[{id:'world-owned-object'}]};
  assert.throws(()=>sanitizePortableCharacter(item),{code:'WORLD_STATE_FORBIDDEN'});
 }
 assert.throws(()=>sanitizePortableCharacter({...survivor(),survival:{health:300,hunger:42,thirst:40}}),{code:'INVALID_SNAPSHOT'});
});
test('same official server restore has no forced spawn and switching again repeats cooldown',()=>{
 let t=200000;const r=make({now:()=>t});
 let a=r.checkIn({playerId:'player4',serverId:'official3a'});
 r.checkOut({playerId:'player4',serverId:'official3a',session:a.session,snapshot:survivor()});
 t+=1;
 a=r.checkIn({playerId:'player4',serverId:'official3a'});
 assert.equal(a.switched,false);assert.equal(a.spawn,null);
 r.checkOut({playerId:'player4',serverId:'official3a',session:a.session,snapshot:survivor()});
 t+=90000;
 a=r.checkIn({playerId:'player4',serverId:'official3b'});
 assert.equal(a.switched,true);assert.deepEqual(a.spawn,spawnPoints['3PP'][1]);
});

test('create additional official characters without overwriting the original, separated by 1PP and 3PP',()=>{
 const r=make();
 const original=r.checkIn({playerId:'one-person',serverId:'official1a'});
 r.checkOut({playerId:'one-person',serverId:'official1a',session:original.session,snapshot:survivor()});
 const second=r.createCharacter({playerId:'one-person',serverId:'official1a',characterSlot:2});
 assert.deepEqual(second,{created:true,characterSlot:2,view:'1PP'});
 assert.throws(()=>r.createCharacter({playerId:'one-person',serverId:'official1a',characterSlot:2}),{code:'CHARACTER_SLOT_EXISTS'});
 assert.throws(()=>r.createCharacter({playerId:'one-person',serverId:'official1a',characterSlot:1}),{code:'ORIGINAL_SLOT_PROTECTED'});
 const v=r.checkIn({playerId:'one-person',serverId:'official1a',characterSlot:2});
 assert.equal(v.snapshot,null);
 assert.equal(v.characterSlot,2);
 assert.throws(()=>r.checkIn({playerId:'one-person',serverId:'official1a',characterSlot:1}),{code:'CHARACTER_ALREADY_ONLINE'});
 r.checkOut({playerId:'one-person',serverId:'official1a',characterSlot:2,session:v.session,snapshot:{
   schemaVersion:1,inventory:[{itemId:'apple',count:3}],survival:{health:100,hunger:60,thirst:70}
 }});
 const first=r.checkIn({playerId:'one-person',serverId:'official1a'});
 assert.deepEqual(first.snapshot,survivor());
 r.checkOut({playerId:'one-person',serverId:'official1a',session:first.session,snapshot:survivor()});
 const otherView=r.checkIn({playerId:'one-person',serverId:'official3a',characterSlot:1});
 assert.equal(otherView.snapshot,null);
 assert.deepEqual(r.getStatus({playerId:'one-person',serverId:'official3a'}).availableSlots,[1]);
 assert.deepEqual(r.getStatus({playerId:'one-person',serverId:'official1a'}).availableSlots,[1,2]);
});
