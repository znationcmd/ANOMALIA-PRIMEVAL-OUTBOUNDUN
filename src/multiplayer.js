import {gameSocket} from "./native-socket.js";
import {validatePlacements} from "./building-rules.js";
import * as THREE from 'three';
import {buildSurvivor} from './survivor-preview.js';
export function createMultiplayer({scene,state,heightAt,notice,onDisconnect,onMapChanged,onModeChanged}){
 let socket,id,clock=0,joined=false,soloPosition=null,soloMap=null,role='player',mode='pve',permissions={};
 const actors=new Map();
 const clear=()=>{
  for(const a of actors.values()){scene.remove(a.avatar.root);a.avatar.dispose();a.nameTexture?.dispose()}
  actors.clear();joined=false;role='player';mode='pve';permissions={};
  if(soloPosition){state.position=soloPosition;soloPosition=null}
  if(soloMap){state.editorObjects=soloMap;soloMap=null;onMapChanged?.()}
 };
 const send=value=>{if(joined&&socket?.readyState===1)socket.send(JSON.stringify(value))};
 return {
  get connected(){return joined},get count(){return actors.size+1},
  get role(){return role},get mode(){return mode},
  get canEdit(){return joined&&permissions.canEditWorld===true},
  get canPvP(){return joined&&permissions.canDamagePlayers===true},
  connect(url,name,password,adminKey=''){return new Promise((resolve,reject)=>{
   if(socket)socket.close();clear();
   soloPosition={...state.position};soloMap=JSON.parse(JSON.stringify(state.editorObjects||[]));
   let settled=false;
   const parsed=new URL(url);
   if(!['ws:','wss:'].includes(parsed.protocol))throw Error('WebSocket URL required');
   socket=gameSocket(parsed.href);const active=socket;
   const timer=setTimeout(()=>{active.close();if(!settled){settled=true;reject(Error('Connection timeout'))}},10000);
   active.onopen=()=>active.send(JSON.stringify({type:'join',protocol:1,name,password,adminKey}));
   active.onmessage=e=>{
    if(socket!==active)return;
    try{
     const m=JSON.parse(e.data);
     if(m.type==='welcome'){
      id=m.id;state.position={...m.position};joined=true;role=m.role||'player';mode=m.mode||'pve';permissions=m.permissions||{};
      onModeChanged?.({mode,role,permissions});
      clearTimeout(timer);settled=true;resolve();
     }
     if(m.type==='permissions'){permissions=m.permissions||{};onModeChanged?.({mode,role,permissions})}
     if(m.type==='server-status'){
      const previous=mode;mode=m.mode||mode;if(previous!==mode){notice('Mode du serveur : '+mode.toUpperCase());onModeChanged?.({mode,role,permissions})}
     }
     if(m.type==='world-map'&&joined){
      try{const objects=validatePlacements({schemaVersion:1,objects:m.objects});state.editorObjects=objects;onMapChanged?.(objects,m.revision)}catch{notice('Plan du serveur rejeté : format de carte invalide')}
     }
     if(m.type==='correction')state.position={x:m.x,z:m.z};
     if(m.type==='operation-denied')notice('Accès refusé : '+String(m.reason||'non autorisé'));
     if(m.type==='combat'&&m.status==='disabled')notice('Combat entre joueurs désactivé sur ce serveur');
     if(m.type==='combat'&&m.status==='hit')notice('Joueur touché : '+String(m.target||''));
     if(m.type==='player-damage'){state.health=Math.max(0,Math.min(100,Number(m.hp)||0));notice('Touché par '+String(m.by||'un joueur'))}
     if(m.type==='respawn'){state.position={...m.position};state.health=m.hp||100;notice('Réapparition au point de départ')}
     if(m.type==='snapshot'&&joined){
      const seen=new Set();
      for(const p of m.players){
       if(p.id===id)continue;
       seen.add(p.id);let a=actors.get(p.id);
       if(!a){
        a={avatar:buildSurvivor({equipment:{torso:'shirt',legs:'jeans'}})};
        actors.set(p.id,a);
        const canvas=document.createElement('canvas');canvas.width=512;canvas.height=64;
        const ctx=canvas.getContext('2d');ctx.fillStyle='#12201edb';ctx.fillRect(0,0,512,64);ctx.fillStyle='#d6ebd8';ctx.font='30px system-ui';ctx.textAlign='center';ctx.fillText(String(p.name).slice(0,24),256,43);
        a.nameTexture=new THREE.CanvasTexture(canvas);
        const label=new THREE.Sprite(new THREE.SpriteMaterial({map:a.nameTexture,depthTest:true}));
        label.position.y=2.2;label.scale.set(2.8,.35,1);a.avatar.root.add(label);scene.add(a.avatar.root);
       }
       a.target=p;
      }
      for(const [key,a]of actors)if(!seen.has(key)){scene.remove(a.avatar.root);a.avatar.dispose();a.nameTexture?.dispose();actors.delete(key)}
     }
    }catch{}
   };
   active.onerror=()=>{if(!settled){settled=true;clearTimeout(timer);reject(Error('Connection failed'))}};
   active.onclose=()=>{if(socket!==active)return;clearTimeout(timer);const was=joined;clear();if(!settled){settled=true;reject(Error('Connection refused'))}if(was){notice('Connexion au serveur interrompue');onDisconnect?.()}};
  })},
  disconnect(){const old=socket;socket=null;old?.close();clear()},
  publishEditor(objects){
   if(!this.canEdit){notice('ANOMALIA Editor réservé au propriétaire sur ce serveur.');return false}
   send({type:'editor-update',objects});return true
  },
  setMode(next){if(role==='owner')send({type:'set-mode',mode:next})},
  kick(targetId){if(permissions.canKickPlayers)send({type:'kick',targetId})},
  shoot(){send({type:'shoot'})},
  update(dt,yaw,playing){
   if(!joined)return;
   clock+=dt;if(clock>=.1&&playing){clock=0;send({type:'move',x:state.position.x,z:state.position.z,yaw})}
   for(const a of actors.values()){
    const p=a.target;if(!p)continue;
    const root=a.avatar.root;
    root.position.lerp({x:p.x,y:heightAt(p.x,p.z),z:p.z},Math.min(1,dt*12));
    root.rotation.y=p.yaw+Math.PI;
   }
  }
 };
}
