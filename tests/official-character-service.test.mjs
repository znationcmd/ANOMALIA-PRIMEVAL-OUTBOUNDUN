import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,rmSync,existsSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createOfficialCharacterService} from '../server/official-character-service.mjs';
const operators={
 firstA:{category:'official',thirdPerson:false,secret:'server_A_secret_123456789_1234567890'},
 firstB:{category:'official',thirdPerson:false,secret:'server_B_secret_123456789_1234567890'},
 thirdA:{category:'official',thirdPerson:true,secret:'server_C_secret_123456789_1234567890'},
};
const spawnPoints={'1PP':[{x:100,y:500,z:100},{x:200,y:500,z:200}],
'3PP':[{x:300,y:500,z:300},{x:400,y:500,z:400}]};
const snapshot={schemaVersion:1,survival:{health:95,hunger:60,thirst:40},
 hands:{itemId:'rifle'},inventory:[{itemId:'water',count:2,container:'backpack'}]};
const request=async(server,serverId,action,body,secret=operators[serverId]?.secret)=>{
 const base='http://127.0.0.1:'+server.address().port;
 const r=await fetch(base+'/v1/official/'+action,{method:'POST',
   headers:{'content-type':'application/json','x-anomalia-server-id':serverId,
     Authorization:'Bearer '+(secret||'not-authorized')},
   body:JSON.stringify(body)});
 return {status:r.status,body:await r.json()};
};
test('official service rejects outsiders, persists snapshots, and blocks parallel active sessions after restart',async()=>{
 const dir=mkdtempSync(join(tmpdir(),'anomalia-official-test-'));
 const path=join(dir,'central.json');
 let time=100000;
 const make=()=>createOfficialCharacterService({operators,spawnPoints,storagePath:path,now:()=>time,pickIndex:()=>1});
 let service=make();
 try{
  await new Promise(resolve=>service.server.once('listening',resolve));
  const outsider=await request(service.server,'firstA','check-in',{playerId:'test-person'},'invalid-secret');
  assert.equal(outsider.status,403);
  const first=await request(service.server,'firstA','check-in',{playerId:'test-person'});
  assert.equal(first.status,200);assert.equal(first.body.switched,false);
  const dup=await request(service.server,'firstB','check-in',{playerId:'test-person'});
  assert.equal(dup.status,409);assert.equal(dup.body.error,'CHARACTER_ALREADY_ONLINE');
  const out=await request(service.server,'firstA','check-out',{playerId:'test-person',session:first.body.session,snapshot});
  assert.equal(out.status,200);assert.equal(out.body.revision,1);
  assert.equal(existsSync(path),true);
  await service.close();
  service=make();await new Promise(resolve=>service.server.once('listening',resolve));
  const early=await request(service.server,'firstB','check-in',{playerId:'test-person'});
  assert.equal(early.status,409);assert.equal(early.body.error,'SERVER_HOP_COOLDOWN');
  time+=90000;
  const second=await request(service.server,'firstB','check-in',{playerId:'test-person'});
  assert.equal(second.status,200);assert.equal(second.body.switched,true);
  assert.deepEqual(second.body.spawn,spawnPoints['1PP'][1]);
  assert.deepEqual(second.body.snapshot,snapshot);
  // Once admitted, a restart must not allow a second session to duplicate.
  await service.close();
  service=make();await new Promise(resolve=>service.server.once('listening',resolve));
  const blocked=await request(service.server,'firstB','check-in',{playerId:'test-person'});
  assert.equal(blocked.status,409);assert.equal(blocked.body.error,'CHARACTER_ALREADY_ONLINE');
 }finally{
  await service.close().catch(()=>{});rmSync(dir,{recursive:true,force:true});
 }
});
test('official service will not admit a community server pretending to be official',async()=>{
 const dir=mkdtempSync(join(tmpdir(),'anomalia-official-protocol-'));
 const service=createOfficialCharacterService({operators,spawnPoints,storagePath:join(dir,'fleet.json')});
 try{
  await new Promise(resolve=>service.server.once('listening',resolve));
  const r=await request(service.server,'community1','check-in',{playerId:'test-person'});
  assert.equal(r.status,403);
  const forged=await request(service.server,'firstA','check-in',{playerId:'test-person',serverId:'thirdA'},operators.firstA.secret);
  assert.equal(forged.status,200);assert.equal(forged.body.view,'1PP');
 }finally{
  await service.close();rmSync(dir,{recursive:true,force:true});
 }
});

test('authenticated server can create extra character slots; same view retains separate inventories across central restart',async()=>{
 const dir=mkdtempSync(join(tmpdir(),'anomalia-official-extra-slot-'));
 const path=join(dir,'official.json');
 let svc=createOfficialCharacterService({operators,spawnPoints,storagePath:path});
 try{
  await new Promise(resolve=>svc.server.once('listening',resolve));
  const c=await request(svc.server,'firstA','create-character',{playerId:'second-survivor',characterSlot:2});
  assert.equal(c.status,200);assert.equal(c.body.characterSlot,2);
  const repeat=await request(svc.server,'firstA','create-character',{playerId:'second-survivor',characterSlot:2});
  assert.equal(repeat.status,409);assert.equal(repeat.body.error,'CHARACTER_SLOT_EXISTS');
  const invalid=await request(svc.server,'firstA','create-character',{playerId:'second-survivor',characterSlot:1});
  assert.equal(invalid.status,409);assert.equal(invalid.body.error,'ORIGINAL_SLOT_PROTECTED');
  await svc.close();
  svc=createOfficialCharacterService({operators,spawnPoints,storagePath:path});
  await new Promise(resolve=>svc.server.once('listening',resolve));
  const status=await request(svc.server,'firstA','status',{playerId:'second-survivor'});
  assert.deepEqual(status.body.availableSlots,[1,2]);
  const selected=await request(svc.server,'firstA','check-in',{playerId:'second-survivor',characterSlot:2});
  assert.equal(selected.status,200);assert.equal(selected.body.characterSlot,2);
 }finally{
  await svc.close().catch(()=>{});
  rmSync(dir,{recursive:true,force:true});
 }
});
