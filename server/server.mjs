import {WORLD_HALF} from "../src/mechanics.js";
import {validatePlacements} from "../src/building-rules.js";
import {GAME_MODES,validGameMode,canPlayerDamage} from "../src/server-modes.js";
import {normalizeServerId,readServerDocument,writeServerDocument} from "./server-storage.mjs";
import http from 'node:http';
import {WebSocketServer,WebSocket} from 'ws';
import {randomUUID,randomBytes,timingSafeEqual} from 'node:crypto';
import {pathToFileURL} from 'node:url';
const equal=(a,b)=>{const x=Buffer.from(String(a??'')),y=Buffer.from(String(b??''));return x.length===y.length&&timingSafeEqual(x,y)};
export function createMultiplayerServer({port=2303,host='0.0.0.0',password='',maxPlayers=16,mode,serverId='main',dataRoot='server-data',adminKey=randomBytes(32).toString('hex')}={}){
 serverId=normalizeServerId(serverId);
 const saved=readServerDocument(dataRoot,serverId,'world.json',{schemaVersion:1,objects:[],mode:'pve',revision:0});
 let objects=[],revision=0,activeMode=validGameMode(mode||saved.mode);
 try{objects=validatePlacements({schemaVersion:1,objects:saved.objects});revision=Math.max(0,Number(saved.revision)||0)}catch{}
 const persist=()=>writeServerDocument(dataRoot,serverId,'world.json',{schemaVersion:1,objects,mode:activeMode,revision});
 const players=new Map();
 const server=http.createServer((req,res)=>{res.writeHead(200,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify({game:'ANOMALIA PRIMEVAL OUTBOUNDUN',protocol:2,serverId,mode:activeMode,players:players.size,maxPlayers,revision}));});
 const wss=new WebSocketServer({server,maxPayload:256*1024,perMessageDeflate:false});
 const send=(ws,value)=>{if(ws.readyState===WebSocket.OPEN&&ws.bufferedAmount<512*1024)ws.send(JSON.stringify(value))};
 const broadcast=value=>{for(const ws of players.keys())send(ws,value)};
 wss.on('connection',ws=>{
  let player,last=0,lastEdit=0,lastShot=0,messages=0,windowAt=Date.now();
  const authTimeout=setTimeout(()=>ws.close(1008,'Join timeout'),10000);
  ws.on('message',raw=>{
   try{
    const now=Date.now();if(now-windowAt>1000){windowAt=now;messages=0}
    if(++messages>40)return ws.close(1008,'Rate limit');
    const m=JSON.parse(raw.toString());
    if(!player){
     if(m.type!=='join'||m.protocol!==2)return ws.close(1008,'Protocol');
     if(!equal(m.password,password))return ws.close(1008,'Password');
     if(players.size>=maxPlayers)return ws.close(1013,'Server full');
     clearTimeout(authTimeout);
     player={id:randomUUID(),name:String(m.name||'Survivor').replace(/[<>\x00-\x1f]/g,'').slice(0,24),x:0,z:180,yaw:0,hp:100,role:adminKey&&equal(m.adminKey,adminKey)?'owner':'player'};
     players.set(ws,player);last=now;
     send(ws,{type:'welcome',id:player.id,position:{x:player.x,z:player.z},mode:activeMode,serverId,role:player.role});
     send(ws,{type:'world-map',schemaVersion:1,objects,revision});
     return;
    }
    if(m.type==='move'&&[m.x,m.z,m.yaw].every(Number.isFinite)){
     const elapsed=Math.min(1,(now-last)/1000),distance=Math.hypot(m.x-player.x,m.z-player.z);
     if(Math.abs(m.x)>WORLD_HALF||Math.abs(m.z)>WORLD_HALF||distance>Math.max(2,elapsed*13)){send(ws,{type:'correction',x:player.x,z:player.z});return}
     Object.assign(player,{x:m.x,z:m.z,yaw:m.yaw});last=now;
    }
    if(m.type==='editor-update'){
     if(player.role!=='owner')return send(ws,{type:'operation-denied',action:'editor',reason:'Admin access required'});
     if(now-lastEdit<600)return;
     lastEdit=now;
     try{objects=validatePlacements({schemaVersion:1,objects:m.objects});revision++;persist();broadcast({type:'world-map',schemaVersion:1,objects,revision})}
     catch{send(ws,{type:'operation-denied',action:'editor',reason:'Carte invalide'})}
    }
    if(m.type==='shoot'){
     if(now-lastShot<330)return;
     lastShot=now;
     if(!GAME_MODES[activeMode].playerDamage)return;
     const dx=-Math.sin(player.yaw),dz=-Math.cos(player.yaw);
     let victim=null,best=120;
     for(const other of players.values()){
      if(!canPlayerDamage(activeMode,player,other)||other.hp<=0)continue;
      const vx=other.x-player.x,vz=other.z-player.z,dist=Math.hypot(vx,vz);
      if(dist>best||dist<.7||(vx*dx+vz*dz)/dist<.982)continue;
      victim=other;best=dist;
     }
     if(victim){
      victim.hp=Math.max(0,victim.hp-20);
      for(const [peer,member] of players)if(member.id===victim.id)send(peer,{type:'player-damage',hp:victim.hp,by:player.name});
      if(victim.hp===0){victim.hp=100;victim.x=0;victim.z=180;for(const [peer,member] of players)if(member.id===victim.id)send(peer,{type:'respawn',position:{x:0,z:180},hp:100});}
     }
    }
    if(m.type==='set-mode'){
     if(player.role!=='owner')return send(ws,{type:'operation-denied',action:'set-mode',reason:'Owner access required'});
     if(!Object.hasOwn(GAME_MODES,m.mode))return;
     activeMode=m.mode;persist();broadcast({type:'server-mode',mode:activeMode});broadcast({type:'server-status',mode:activeMode,players:players.size});
    }
   }catch{ws.close(1008,'Invalid message')}
  });
  ws.on('close',()=>{clearTimeout(authTimeout);players.delete(ws)});
 });
 const timer=setInterval(()=>{const data={type:'snapshot',players:[...players.values()].map(({id,name,x,z,yaw})=>({id,name,x,z,yaw}))};for(const ws of players.keys())send(ws,data)},100);
 server.listen(port,host);
 return {server,wss,players,serverId,get mode(){return activeMode},get worldMap(){return objects},adminKey,async close(){clearInterval(timer);for(const ws of wss.clients)ws.terminate();await new Promise(r=>wss.close(r));await new Promise(r=>server.close(r))}};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 const port=Number(process.env.PORT||2303);
 const instance=createMultiplayerServer({port,password:process.env.SERVER_PASSWORD||'',maxPlayers:Math.min(64,Math.max(2,Number(process.env.MAX_PLAYERS)||16)),serverId:process.env.SERVER_ID||'main',dataRoot:process.env.SERVER_DATA_ROOT||'server-data',mode:process.env.GAME_MODE||undefined,adminKey:process.env.SERVER_ADMIN_KEY||randomBytes(32).toString('hex')});
 console.log('ANOMALIA server :'+port+' · ID '+instance.serverId+' · '+instance.mode+' · data isolated');
}
