import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,existsSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {once} from 'node:events';
import {WebSocket} from 'ws';
import {createMultiplayerServer} from '../server/server.mjs';
import {normalizeServerId,serverDirectory,readServerDocument,writeServerDocument,serverIdFromAddress} from '../server/server-storage.mjs';

test('server paths never escape own namespace',()=>{
 assert.equal(normalizeServerId('Survie_RP-1'),'survie_rp-1');
 for(const id of ['../admin','../../','a/b','a\\b','', '.hidden','x'.repeat(80)])assert.throws(()=>normalizeServerId(id));
 assert.notEqual(serverIdFromAddress('ws://127.0.0.1:2303'),serverIdFromAddress('ws://127.0.0.1:2304'));
 assert.notEqual(serverDirectory('/tmp/anomalia','rp'),serverDirectory('/tmp/anomalia','pvp'));
});
test('RP/PVP servers persist editor maps independently; guests cannot edit other worlds',async()=>{
 const root=mkdtempSync(join(tmpdir(),'anomalia-isolation-'));
 const a=createMultiplayerServer({port:0,host:'127.0.0.1',dataRoot:root,serverId:'rp',mode:'rp',adminKey:'private-a'});
 const b=createMultiplayerServer({port:0,host:'127.0.0.1',dataRoot:root,serverId:'pvp',mode:'pvp',adminKey:'private-b'});
 const clients=[];
 try{
  await Promise.all([once(a.server,'listening'),once(b.server,'listening')]);
  const open=async(port,adminKey)=>{
   const ws=new WebSocket('ws://127.0.0.1:'+port);clients.push(ws);await once(ws,'open');
   const welcome=new Promise(resolve=>ws.on('message',raw=>{const m=JSON.parse(raw.toString());if(m.type==='welcome')resolve(m)}));
   ws.send(JSON.stringify({type:'join',protocol:2,name:'Test',password:'',adminKey}));return {ws,welcome:await welcome};
  };
  const owner=await open(a.server.address().port,'private-a');
  const guest=await open(b.server.address().port,'private-a');
  assert.equal(owner.welcome.role,'owner');
  assert.equal(guest.welcome.role,'player');
  owner.ws.send(JSON.stringify({type:'editor-update',objects:[{id:'house-one',type:'house',x:500,z:500,yaw:0}]}));
  await new Promise(resolve=>setTimeout(resolve,120));
  assert.equal(a.worldMap.length,1);
  assert.equal(b.worldMap.length,0);
  guest.ws.send(JSON.stringify({type:'editor-update',objects:[{id:'bad-house',type:'house',x:100,z:100,yaw:0}]}));
  await new Promise(resolve=>setTimeout(resolve,120));
  assert.equal(b.worldMap.length,0);
  assert.equal(readServerDocument(root,'rp','world.json',{}).objects[0].id,'house-one');
  assert.equal(existsSync(serverDirectory(root,'pvp')+'/world.json'),false);
  assert.equal(a.mode,'rp');assert.equal(b.mode,'pvp');
 }finally{for(const ws of clients)ws.terminate();await Promise.all([a.close(),b.close()]);rmSync(root,{recursive:true,force:true})}
});
test('configuration documents cannot be overwritten via traversal',()=>{
 const root=mkdtempSync(join(tmpdir(),'anomalia-config-'));
 try{writeServerDocument(root,'server-a','settings.json',{difficulty:2});writeServerDocument(root,'server-b','settings.json',{difficulty:5});assert.equal(readServerDocument(root,'server-a','settings.json',{}).difficulty,2);assert.equal(readServerDocument(root,'server-b','settings.json',{}).difficulty,5);assert.throws(()=>writeServerDocument(root,'server-a','../settings.json',{}))}
 finally{rmSync(root,{recursive:true,force:true})}
});
