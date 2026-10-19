import http from 'node:http';
import {WebSocketServer,WebSocket} from 'ws';
import {randomUUID,randomBytes,timingSafeEqual} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {readFileSync,writeFileSync,existsSync,mkdirSync} from 'node:fs';
import {dirname} from 'node:path';
import {validatePlacements} from '../src/building-rules.js';
import {GAME_MODES,SAFE_ZONES,permissionsFor,canPlayerDamage,validGameMode} from '../src/server-modes.js';
const sameSecret=(a,b)=>{const one=Buffer.from(String(a||'')),two=Buffer.from(String(b||''));return one.length===two.length&&timingSafeEqual(one,two)};
export function createMultiplayerServer({port=2303,host='0.0.0.0',password='',maxPlayers=16,mode='pve',adminKey=randomBytes(32).toString('hex'),dataFile=null}={}){
 const players=new Map();
 const selected=validGameMode(mode);
 let activeMode=selected,objects=[],mapRevision=0;
 if(dataFile&&existsSync(dataFile)){
  try{const data=JSON.parse(readFileSync(dataFile,'utf8'));objects=validatePlacements({schemaVersion:1,objects:data.objects||[]});mapRevision=Number.isSafeInteger(data.revision)?Math.max(0,data.revision):0;activeMode=validGameMode(data.mode||mode)}
  catch(e){console.warn('[ANOMALIA] Saved map invalid; starting with current map:',String(e.message).slice(0,120))}
 }
 const persist=()=>{
  if(!dataFile)return;
  try{mkdirSync(dirname(dataFile),{recursive:true});writeFileSync(dataFile,JSON.stringify({schemaVersion:1,objects,mode:activeMode,revision:mapRevision}),'utf8')}
  catch(e){console.warn('[ANOMALIA] Could not save server map:',String(e.message).slice(0,120))}
 };
 const server=http.createServer((req,res)=>{res.writeHead(200,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify({game:'ANOMALIA PRIMEVAL OUTBOUNDUN',protocol:1,players:players.size,maxPlayers,mode:activeMode,editor:'owner-only',mapRevision}))});
 const wss=new WebSocketServer({server,maxPayload:256*1024,perMessageDeflate:false});
 const send=(ws,value)=>{if(ws.readyState===WebSocket.OPEN&&ws.bufferedAmount<512*1024)ws.send(JSON.stringify(value));};
 const broadcast=(value)=>{for(const ws of players.keys())send(ws,value)};
 const mapMessage=()=>({type:'world-map',schemaVersion:1,revision:mapRevision,objects});
 wss.on('connection',ws=>{
  let player;let last=0,lastShot=0,lastEditor=0,messages=0,windowAt=Date.now();
  const authTimeout=setTimeout(()=>ws.close(1008,'Join timeout'),10000);
  ws.on('message',raw=>{
   try{
    const now=Date.now();if(now-windowAt>1000){windowAt=now;messages=0}
    if(++messages>40)return ws.close(1008,'Rate limit');
    const m=JSON.parse(raw.toString());
    if(!player){
     if(m.type!=='join'||m.protocol!==1)return ws.close(1008,'Protocol');
     if(!sameSecret(m.password,password))return ws.close(1008,'Password');
     if(players.size>=maxPlayers)return ws.close(1013,'Server full');
     clearTimeout(authTimeout);
     const role=adminKey&&sameSecret(m.adminKey,adminKey)?'owner':'player';
     player={id:randomUUID(),name:String(m.name||'Survivor').replace(/[<>\x00-\x1f]/g,'').slice(0,24),x:0,z:180,yaw:0,hp:100,role};
     players.set(ws,player);last=now;
     send(ws,{type:'welcome',id:player.id,position:{x:player.x,z:player.z},mode:activeMode,role:player.role,permissions:permissionsFor(role,activeMode),safeZones:SAFE_ZONES});
     send(ws,mapMessage());
     broadcast({type:'server-status',mode:activeMode,players:players.size});
     return;
    }
    if(m.type==='move'&&[m.x,m.z,m.yaw].every(Number.isFinite)){
     const elapsed=Math.min(1,(now-last)/1000),distance=Math.hypot(m.x-player.x,m.z-player.z);
     if(Math.abs(m.x)>10240||Math.abs(m.z)>10240||distance>Math.max(2,elapsed*13)){send(ws,{type:'correction',x:player.x,z:player.z});return;}
     Object.assign(player,{x:m.x,z:m.z,yaw:m.yaw});last=now;
    }
    if(m.type==='editor-update'){
     if(!permissionsFor(player.role,activeMode).canEditWorld)return send(ws,{type:'operation-denied',action:'editor',reason:'Admin access required'});
     if(now-lastEditor<750)return send(ws,{type:'operation-denied',action:'editor',reason:'Editor cooldown'});
     lastEditor=now;
     try{
      const proposed=validatePlacements({schemaVersion:1,objects:m.objects});
      objects=proposed;mapRevision++;persist();broadcast(mapMessage());
     }catch{return send(ws,{type:'operation-denied',action:'editor',reason:'Invalid map objects'})}
    }
    if(m.type==='set-mode'){
     if(player.role!=='owner')return send(ws,{type:'operation-denied',action:'set-mode',reason:'Owner access required'});
     if(!Object.hasOwn(GAME_MODES,m.mode))return;
     activeMode=m.mode;persist();
     broadcast({type:'server-status',mode:activeMode,players:players.size,description:GAME_MODES[activeMode].description});
     for(const [client,member] of players)send(client,{type:'permissions',permissions:permissionsFor(member.role,activeMode)});
    }
    if(m.type==='kick'){
     if(!permissionsFor(player.role,activeMode).canKickPlayers)return send(ws,{type:'operation-denied',action:'kick',reason:'Admin access required'});
     const found=[...players].find(([,member])=>member.id===m.targetId&&member.id!==player.id);
     if(found)found[0].close(1008,'Kicked by admin');
    }
    if(m.type==='shoot'){
     if(now-lastShot<330)return;
     lastShot=now;
     // Prototype server-controlled hits: server determines target from saved position/yaw;
     // no target ID, client damage value or fabricated location is accepted.
     if(!GAME_MODES[activeMode].playerDamage)return send(ws,{type:'combat',status:'disabled',mode:activeMode});
     const dx=-Math.sin(player.yaw),dz=-Math.cos(player.yaw);
     let victim=null,best=120;
     for(const other of players.values()){
      if(!canPlayerDamage(activeMode,player,other)||other.hp<=0)continue;
      const vx=other.x-player.x,vz=other.z-player.z,dist=Math.hypot(vx,vz);
      if(dist>best||dist<.7||((vx*dx+vz*dz)/dist)<.982)continue;
      victim=other;best=dist;
     }
     if(!victim)return;
     victim.hp=Math.max(0,victim.hp-20);
     for(const [peer,p] of players)if(p.id===victim.id)send(peer,{type:'player-damage',hp:victim.hp,by:player.name});
     send(ws,{type:'combat',status:'hit',target:victim.name});
     if(victim.hp===0){
      // Short, server-owned respawn keeps the presence prototype playable.
      victim.hp=100;victim.x=0;victim.z=180;
      for(const [peer,p] of players)if(p.id===victim.id)send(peer,{type:'respawn',position:{x:0,z:180},hp:100});
     }
    }
   }catch{ws.close(1008,'Invalid message')}
  });
  ws.on('close',()=>{clearTimeout(authTimeout);players.delete(ws)});
 });
 const timer=setInterval(()=>{
  const data={type:'snapshot',players:[...players.values()].map(({id,name,x,z,yaw,role,hp})=>({id,name,x,z,yaw,role,hp}))};
  for(const ws of players.keys())send(ws,data);
 },100);
 server.listen(port,host);
 return {server,wss,players,get mode(){return activeMode},get worldMap(){return objects},get adminKey(){return adminKey},async close(){clearInterval(timer);for(const ws of wss.clients)ws.terminate();await new Promise(r=>wss.close(r));await new Promise(r=>server.close(r));}};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 const port=Number(process.env.PORT||2303);
 const server=createMultiplayerServer({port,password:process.env.SERVER_PASSWORD||'',maxPlayers:Math.min(64,Math.max(2,Number(process.env.MAX_PLAYERS)||16)),mode:process.env.GAME_MODE||'pve',adminKey:process.env.SERVER_ADMIN_KEY||randomBytes(32).toString('hex'),dataFile:process.env.SERVER_DATA_FILE||'server-data/world.json'});
 console.log('[ANOMALIA] Server on port '+port+'; mode='+server.mode+'; map persisted');
}
