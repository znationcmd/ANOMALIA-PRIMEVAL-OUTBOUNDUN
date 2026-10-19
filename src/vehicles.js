import {WORLD_HALF} from "./mechanics.js";
import {moveWithCollisions,groundHeight} from './movement.js';
export const VEHICLES={
 car:{name:'Berline',mode:'land',speed:30,accel:7,turn:1.4,length:4.4,width:2,eye:1.5},
 truck:{name:'Camion',mode:'land',speed:23,accel:4,turn:.8,length:7.5,width:2.7,eye:2.4},
 motorcycle:{name:'Moto',mode:'land',speed:42,accel:10,turn:1.7,length:2.3,width:.8,eye:1.5},
 tank:{name:'Char',mode:'land',speed:17,accel:4,turn:.8,length:6.5,width:3.6,eye:2.4},
 boat:{name:'Bateau',mode:'water',speed:24,accel:5,turn:.75,length:6,width:2.4,eye:2},
 carrier:{name:'Porte-avions',mode:'water',speed:15,accel:1.2,turn:.18,length:85,width:20,eye:12},
 warship:{name:'Navire de guerre',mode:'water',speed:22,accel:2.2,turn:.32,length:42,width:10,eye:8},
 submarine:{name:'Sous-marin',mode:'submarine',speed:18,accel:2,turn:.4,length:32,width:6,eye:4},
 helicopter:{name:'Hélicoptère',mode:'helicopter',speed:38,accel:5,turn:1,length:9,width:2.5,eye:1.8},
 airplane:{name:'Avion',mode:'airplane',speed:65,accel:5,turn:.65,length:9,width:10,eye:1.6}
};
export function spawnVehicle(s,type,x,z,heightAt){const def=VEHICLES[type];if(!def)return {ok:false,message:'Véhicule inconnu.'};s.vehicles??=[];if(s.vehicles.length>=60)return {ok:false,message:'60 véhicules maximum.'};
 const ground=groundHeight(x,z,heightAt);if((def.mode==='water'||def.mode==='submarine')&&heightAt(x,z)>2)return {ok:false,message:'Place le bateau sur l’eau : téléporte-toi près d’une rive.'};
 if(def.mode==='land'&&ground< -1)return {ok:false,message:'Ce véhicule doit être placé sur terre.'};
 s.vehicleSequence=(Number(s.vehicleSequence)||0)+1;const vehicle={id:'vehicle-'+s.vehicleSequence,type,x,z,y:def.mode==='submarine'?-2:def.mode==='water'?.4:Math.max(ground,0),yaw:0,speed:0,fuel:100,verticalSpeed:0,hp:100};s.vehicles.push(vehicle);return {ok:true,vehicle,message:def.name+' créé.'};
}
export function enterVehicle(s,id){const v=(s.vehicles||[]).find(v=>v.id===id);if(!v||Math.hypot(v.x-s.position.x,v.z-s.position.z)>12)return {ok:false,message:'Approche du véhicule.'};s.activeVehicle=id;s.boat=false;s.mounted=null;s.position={x:v.x,z:v.z};s.vehicleView=s.vehicleView||'outside';return {ok:true,message:'Pilotage : ZQSD/WASD · E sortir · F5 vue · Espace monter / Ctrl descendre.'}}
export function exitVehicle(s,heightAt,solids=[]){const v=(s.vehicles||[]).find(v=>v.id===s.activeVehicle);if(!v)return {ok:false,message:'Aucun véhicule.'};const ground=groundHeight(v.x,v.z,heightAt);if(v.y>Math.max(0,ground)+4)return {ok:false,message:'Pose le véhicule avant de sortir.'};
 const positions=[1,-1,2,-2].map(n=>({x:v.x+Math.cos(v.yaw)*n*(VEHICLES[v.type].width+1),z:v.z-Math.sin(v.yaw)*n*(VEHICLES[v.type].width+1)}));
 const p=positions.find(p=>!solids.some(b=>Math.abs(p.x-b.x)<b.width/2+.7&&Math.abs(p.z-b.z)<b.depth/2+.7));if(!p)return {ok:false,message:'La sortie est bloquée.'};s.position=p;s.activeVehicle=null;v.speed=0;return {ok:true,message:'Véhicule quitté.'}}
export function tickVehicle(v,input,dt,{heightAt,solids=[],fuelRate=.03,bounds=WORLD_HALF}){
 const d=VEHICLES[v.type];if(!d)return;dt=Math.min(.1,Math.max(0,dt));const throttle=v.fuel>0?Math.max(-1,Math.min(1,input.forward||0)):0;
 v.speed=Math.max(-d.speed*.25,Math.min(d.speed,v.speed+throttle*d.accel*dt));
 if(!throttle)v.speed*=Math.max(0,1-dt*.7);if(input.brake)v.speed*=Math.max(0,1-dt*4);
 v.yaw+=(input.turn||0)*d.turn*dt*(d.mode==='helicopter'||v.type==='tank'?1:Math.max(.15,Math.min(1,Math.abs(v.speed)/8)));
 v.fuel=Math.max(0,v.fuel-Math.abs(throttle)*fuelRate*dt);
 let dx=-Math.sin(v.yaw)*v.speed*dt,dz=-Math.cos(v.yaw)*v.speed*dt;
 const ground=groundHeight(v.x,v.z,heightAt);
 if(d.mode==='airplane'){
  const lift=Math.abs(v.speed)>18?(input.up?6:Math.abs(v.speed)>30?1.1:0): -6;
  v.verticalSpeed+=(lift-v.verticalSpeed)*dt*2;v.y=Math.max(Math.max(0,ground),v.y+v.verticalSpeed*dt-(input.down?5*dt:0));
 }else if(d.mode==='helicopter')v.y=Math.max(Math.max(0,ground),v.y+((input.up?8:0)-(input.down?6:0))*dt);
 const airborne=(d.mode==='helicopter'||d.mode==='airplane')&&v.y>Math.max(0,ground)+4;
 if(airborne){v.x+=dx;v.z+=dz}else if(d.mode==='submarine'){
  if(heightAt(v.x+dx,v.z+dz)<-3){v.x+=dx;v.z+=dz}else v.speed=0;const seabed=heightAt(v.x,v.z)+2;v.y=Math.max(seabed,Math.min(.2,v.y+((input.up?3:0)-(input.down?3:0))*dt));
 }else if(d.mode==='water'){
  if(heightAt(v.x+dx,v.z+dz)<2){v.x+=dx;v.z+=dz}else v.speed=0;v.y=.4;
 }else{
  const prev={x:v.x,z:v.z};const next=moveWithCollisions(prev,dx,dz,solids,(x,z,nx,nz)=>groundHeight(nx,nz,heightAt)>-1&&Math.abs(groundHeight(nx,nz,heightAt)-groundHeight(x,z,heightAt))<1.3,d.width/2);
  if(Math.hypot(next.x-v.x,next.z-v.z)<Math.hypot(dx,dz)*.25&&Math.abs(v.speed)>1)v.speed*=.1;
  v.x=next.x;v.z=next.z;if(d.mode==='land')v.y=Math.max(0,groundHeight(v.x,v.z,heightAt));
 }
 v.x=Math.max(-bounds,Math.min(bounds,v.x));v.z=Math.max(-bounds,Math.min(bounds,v.z));v.y=Math.min(1500,v.y);
}
export function togglePerspective(s){if(!s.activeVehicle&&s.thirdPersonAllowed===false)return {ok:false,message:'Troisième personne désactivée dans la configuration.'};if(s.activeVehicle)s.vehicleView=s.vehicleView==='inside'?'outside':'inside';else s.thirdPerson=!s.thirdPerson;return {ok:true,message:s.activeVehicle?(s.vehicleView==='inside'?'Vue intérieure':'Vue extérieure'):(s.thirdPerson?'Troisième personne':'Première personne')}}
