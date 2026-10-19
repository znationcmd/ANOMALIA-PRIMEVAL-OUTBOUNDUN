import test from 'node:test';
import assert from 'node:assert/strict';
import {once} from 'node:events';
import {mkdtempSync,rmSync,existsSync,readFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {WebSocket} from 'ws';
import {createMultiplayerServer} from '../server/server.mjs';
import {GAME_MODES,SAFE_ZONES,protectedZone,canPlayerDamage,permissionsFor} from '../src/server-modes.js';

const waitMessage=(ws,match)=>new Promise((resolve,reject)=>{
 const timer=setTimeout(()=>{ws.off('message',read);reject(Error('Timed out waiting for '+match))},4000);
 function read(raw){let m;try{m=JSON.parse(raw.toString())}catch{return}if(match(m)){clearTimeout(timer);ws.off('message',read);resolve(m)}}
 ws.on('message',read);
});
const joinClient=async(url,opts)=>{
 const client=new WebSocket(url);await once(client,'open');
 const welcome=waitMessage(client,m=>m.type==='welcome');
 client.send(JSON.stringify({type:'join',protocol:2,name:opts.name||'Survivant',password:opts.password||'',adminKey:opts.adminKey||''}));
 return {ws:client,welcome:await welcome};
};

test('menu and editor expose an authenticated ANOMALIA Editor and host mode presets',async()=>{
 const {readFileSync}=await import('node:fs');
 const menu=readFileSync(new URL('../src/start-menu.js',import.meta.url),'utf8');
 const editor=readFileSync(new URL('../src/map-editor.js',import.meta.url),'utf8');
 const desktop=readFileSync(new URL('../desktop/main.cjs',import.meta.url),'utf8');
 for(const item of ['id="serverMode"','value="rp"','value="pvp"','value="pve"','value="mixed"','id="serverAdminKey"','hostedAdminKey'])
  assert.ok(menu.includes(item),'Missing game mode or private admin key UI: '+item);
 for(const item of ['ANOMALIA EDITOR','network.canEdit','network.publishEditor(copy())'])
  assert.ok(editor.includes(item),'Editor missing secure synchronization: '+item);
 assert.ok(desktop.includes('dataRoot:app.getPath(\'userData\')'));
});
test('RP, PVE and mixed protect players; PVP accepts damage; safe zones do not overlap whole world',()=>{
 assert.deepEqual(Object.keys(GAME_MODES).sort(),['mixed','pve','pvp','rp']);
 assert.equal(canPlayerDamage('rp',{id:1,x:500,z:500},{id:2,x:501,z:500}),false);
 assert.equal(canPlayerDamage('pve',{id:1,x:500,z:500},{id:2,x:501,z:500}),false);
 assert.equal(canPlayerDamage('pvp',{id:1,x:0,z:180},{id:2,x:0,z:179}),true);
 assert.equal(canPlayerDamage('mixed',{id:1,x:0,z:180},{id:2,x:0,z:179}),false);
 assert.equal(canPlayerDamage('mixed',{id:1,x:2100,z:180},{id:2,x:2101,z:180}),true);
 assert.ok(protectedZone(0,180));
 assert.ok(SAFE_ZONES.length>=3);
 assert.equal(permissionsFor('player','pvp').canEditWorld,false);
 assert.equal(permissionsFor('owner','rp').canEditWorld,true);
 assert.equal(permissionsFor('player','pve').canBuild,true);
});

test('ANOMALIA Editor changes require a private owner credential, sync to guests and persist on restart',async()=>{
 const folder=mkdtempSync(join(tmpdir(),'anomalia-server-test-')),file=join(folder,'servers','main','world.json');
 const secret='an-independent-owner-secret';
 const app=createMultiplayerServer({port:0,host:'127.0.0.1',mode:'pve',adminKey:secret,dataRoot:folder,serverId:'main'});
 await once(app.server,'listening');
 const url='ws://127.0.0.1:'+app.server.address().port;
 const clients=[];
 try{
  const owner=await joinClient(url,{name:'Alice',adminKey:secret});clients.push(owner.ws);
  const guest=await joinClient(url,{name:'Bob',adminKey:'bad-key'});clients.push(guest.ws);
  assert.equal(owner.welcome.role,'owner');
  assert.equal(guest.welcome.role,'player');
  assert.equal(owner.welcome.mode,'pve');
  // map + mode information is a separate server-controlled payload.
  const denied=waitMessage(guest.ws,m=>m.type==='operation-denied'&&m.action==='editor');
  guest.ws.send(JSON.stringify({type:'editor-update',objects:[{id:'guest-map',type:'house',x:500,z:500,yaw:0}]}));
  assert.match((await denied).reason,/Admin/);
  assert.equal(app.worldMap.length,0);
  const shared=waitMessage(guest.ws,m=>m.type==='world-map'&&m.objects.some(o=>o.id==='new-hospital'));
  owner.ws.send(JSON.stringify({type:'editor-update',objects:[{id:'new-hospital',type:'hospital',x:510,z:510,yaw:0}]}));
  const map=await shared;assert.equal(map.objects[0].id,'new-hospital');
  assert.equal(app.worldMap.length,1);
  assert.equal(existsSync(file),true);
  const saved=JSON.parse(readFileSync(file,'utf8'));assert.equal(saved.objects[0].id,'new-hospital');
  const rejected=waitMessage(guest.ws,m=>m.type==='operation-denied'&&m.action==='set-mode');
  guest.ws.send(JSON.stringify({type:'set-mode',mode:'pvp'}));await rejected;
  assert.equal(app.mode,'pve');
  const modeChanged=waitMessage(guest.ws,m=>m.type==='server-status'&&m.mode==='pvp');
  owner.ws.send(JSON.stringify({type:'set-mode',mode:'pvp'}));
  await modeChanged;
  assert.equal(app.mode,'pvp');
  const moved=waitMessage(owner.ws,m=>m.type==='snapshot'&&m.players.some(p=>p.name==='Bob'&&p.z===179));
  guest.ws.send(JSON.stringify({type:'move',x:0,z:179,yaw:0}));
  await moved;
  const hit=waitMessage(guest.ws,m=>m.type==='player-damage');
  owner.ws.send(JSON.stringify({type:'shoot'}));
  assert.equal((await hit).hp,80);
  const mixed=waitMessage(guest.ws,m=>m.type==='server-status'&&m.mode==='mixed');
  owner.ws.send(JSON.stringify({type:'set-mode',mode:'mixed'}));await mixed;
  await new Promise(r=>setTimeout(r,360));
  owner.ws.send(JSON.stringify({type:'shoot'}));
  await new Promise(r=>setTimeout(r,180));
  const bob=[...app.players.values()].find(p=>p.name==='Bob');
  assert.equal(bob.hp,80,'Mixed RP safe zone must protect Bob');
 }finally{
  for(const ws of clients)ws.terminate();
  await app.close();
 }
 const reloaded=createMultiplayerServer({port:0,host:'127.0.0.1',dataFile:file});
 try{await once(reloaded.server,'listening');assert.equal(reloaded.mode,'mixed');assert.equal(reloaded.worldMap[0].id,'new-hospital')}
 finally{await reloaded.close();rmSync(folder,{recursive:true,force:true})}
});
