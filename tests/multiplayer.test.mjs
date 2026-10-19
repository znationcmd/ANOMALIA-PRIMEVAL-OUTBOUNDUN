import test from 'node:test';
import assert from 'node:assert/strict';
import {once} from 'node:events';
import {WebSocket} from 'ws';
import {createMultiplayerServer} from '../server/server.mjs';
const receive=(ws,match)=>new Promise((resolve,reject)=>{const timer=setTimeout(()=>{ws.off('message',read);reject(Error('Message timeout'));},3000);function read(raw){const m=JSON.parse(raw);if(match(m)){clearTimeout(timer);ws.off('message',read);resolve(m);}}ws.on('message',read);});
test('two real clients join, see movement, reject teleports and remove disconnected survivors',async()=>{
 const app=createMultiplayerServer({port:0,host:'127.0.0.1',password:'test'});await once(app.server,'listening');const url=`ws://127.0.0.1:${app.server.address().port}`;const clients=[];
 try{for(const name of ['Alice','Bob']){const ws=new WebSocket(url);clients.push(ws);await once(ws,'open');const welcome=receive(ws,m=>m.type==='welcome');ws.send(JSON.stringify({type:'join',protocol:2,name,password:'test'}));assert.ok((await welcome).id);}
 let snapshot=await receive(clients[0],m=>m.type==='snapshot'&&m.players.length===2);assert.deepEqual(snapshot.players.map(p=>p.name),['Alice','Bob']);
 const moved=receive(clients[1],m=>m.type==='snapshot'&&m.players.find(p=>p.name==='Alice')?.x===1);clients[0].send(JSON.stringify({type:'move',x:1,z:180,yaw:.5}));await moved;
 const correction=receive(clients[0],m=>m.type==='correction');clients[0].send(JSON.stringify({type:'move',x:9000,z:9000,yaw:0}));assert.equal((await correction).x,1);
 clients[1].close();snapshot=await receive(clients[0],m=>m.type==='snapshot'&&m.players.length===1);assert.equal(snapshot.players[0].name,'Alice');
 const refused=new WebSocket(url);clients.push(refused);await once(refused,'open');const closed=once(refused,'close');refused.send(JSON.stringify({type:'join',protocol:2,password:'wrong'}));assert.equal((await closed)[0],1008);
 }finally{for(const ws of clients)ws.terminate();await app.close();}
});
