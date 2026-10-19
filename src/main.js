import worldMetrics from "./world-metrics.json";
import {createConstructionUI} from "./construction-ui.js";
import {createConstructionWorld} from "./construction-world.js";
import {validateConstruction} from "./construction.js";
import {spawnVehicle} from "./vehicles.js";
import {startBeachJourney,beachObjective,reserveBeach} from "./beach-journey.js";
import {createMapEditor} from "./map-editor.js";
import {createBuildings} from "./rp-buildings.js";
import {reserveBuilding,RP_SITES} from "./building-rules.js";
import {createStartMenu} from "./start-menu.js";
import {createMultiplayer} from "./multiplayer.js";
import {createWorldRuntime} from "./world-runtime.js";
import {inventoryInterface} from "./inventory-ui.js";
import {syncInventory,takeInHands,nearbyDrops} from "./inventory.js";
import {createGraphics} from "./graphics.js";
import {BRIDGES,movementVector,bridgeSurface,groundHeight,moveWithCollisions} from "./movement.js";

import * as THREE from "three";
import {JUNGLE_ZONES,WILDLIFE,KIBBLE_TIERS,KIBBLE_RECIPES,wildlifeSpawn,huntAnimal,forageSupplies,fishAt,cookFood,craftSurvival,tranquilize,tickTorpor,tameWithKibble} from "./ecology.js";
import {readGamepad,selectGamepad,controllerFamily,GAMEPAD_LABELS} from "./gamepad.js";
import {WORLD_HALF,CHUNK_SIZE,SEA_LEVEL,CITIES,CONTINENTS,PEAKS,SITES,ITEM_NAMES,hash2,heightAt,biomeAt,nearestCity,nearestSite,initialState,normalizeState,unlockSite,buildStructure,tickSurvival,clamp} from "./mechanics.js";
import {ITEM_DEFS,EQUIPMENT_SLOTS,capacity,weight,protection,warmth,equip,consume,rewardLoot,tame,saddleMount,breed,survivalTick,DINO_TYPES,hasItem} from "./systems.js";

const $=id=>document.getElementById(id);
const STORAGE="anomalia-primeval-outboundun-save-v1",scene=new THREE.Scene();
scene.background=new THREE.Color(0x9aafbd);
scene.fog=new THREE.FogExp2(0x829bb0,.00055);
const camera=new THREE.PerspectiveCamera(74,innerWidth/innerHeight,.08,2500);
const renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:"high-performance"});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setSize(innerWidth,innerHeight);
renderer.shadowMap.enabled=false;
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;
document.getElementById("app").prepend(renderer.domElement);
renderer.domElement.id="gameCanvas";
const hemi=new THREE.HemisphereLight(0xd6ecff,0x344f38,2.3);scene.add(hemi);
const sun=new THREE.DirectionalLight(0xffe4ac,2.1);sun.position.set(300,600,-250);scene.add(sun);
const outside=new THREE.Group(),underground=new THREE.Group();
scene.add(outside,underground);underground.visible=false;
const mat=(color,metalness=0)=>new THREE.MeshStandardMaterial({color,roughness:.86,metalness});
const m={rock:mat(0x64696b),wall:mat(0x5b5f61),roof:mat(0x2f383e),wood:mat(0x6b5340),leaves:mat(0x35533b),trunk:mat(0x4c3d2b),road:mat(0x44484a),glass:mat(0x425b64,.2),loot:mat(0xa98b58),locked:mat(0x7e4240),open:mat(0x558a76),dino:mat(0x76905b),hostile:mat(0x934845),boat:mat(0x714b32)};
const graphics=createGraphics(renderer,scene,camera,sun,hemi,CITIES);
Object.assign(m,{wall:graphics.concrete,rock:graphics.rock,road:graphics.road,wood:graphics.wood,glass:graphics.glass});
const box=(w,h,d,material)=>new THREE.Mesh(new THREE.BoxGeometry(w,h,d),material);
const cylinder=(r1,r2,h,material)=>new THREE.Mesh(new THREE.CylinderGeometry(r1,r2,h,7),material);
function meshBox(parent,x,y,z,w,h,d,material){const q=box(w,h,d,material);q.position.set(x,y,z);q.castShadow=!matchMedia("(pointer:coarse)").matches;q.receiveShadow=true;parent.add(q);return q}
let saved;try{saved=JSON.parse(localStorage.getItem(STORAGE)||"null")}catch{}
let state=normalizeState(saved);state.equipment={head:null,torso:"shirt",vest:null,legs:"jeans",feet:"boots",back:null,...saved?.equipment};
state.illness=saved?.illness||null;state.infection=Number(saved?.infection)||0;state.temperature=Number(saved?.temperature)||37;
state.tamed=Array.isArray(saved?.tamed)?saved.tamed:[];state.dinoTrust=saved?.dinoTrust||{};
state.mounted=saved?.mounted||null;state.weapon=saved?.weapon||"pistol";state.underground=null;
state.inventory={...state.inventory,...saved?.inventory};
state.hunted=Array.isArray(saved?.hunted)?saved.hunted:[];
state.mapPins=Array.isArray(saved?.mapPins)?saved.mapPins.slice(0,120):[];
state.dinoEffects=saved?.dinoEffects||{};
state.ecologyStarterKit=Boolean(saved?.ecologyStarterKit);
if(!state.ecologyStarterKit){
 for(const [id,qty] of Object.entries({fishing_rod:1,tranq_dart:8,kibble_herbivore:3,kibble_carnivore:3,cooked_fish:2,medicine:1}))state.inventory[id]=(state.inventory[id]||0)+qty;
 state.equipment.back||="bag";
 state.ecologyStarterKit=true;
}
state.inventoryStacks=Array.isArray(saved?.inventoryStacks)?saved.inventoryStacks:[];
state.inventorySequence=Number(saved?.inventorySequence)||0;
state.groundDrops=Array.isArray(saved?.groundDrops)?saved.groundDrops:[];
state.quickbar=Array.isArray(saved?.quickbar)?saved.quickbar:undefined;
state.inventoryMigration=!!saved?.inventoryMigration;
if(!state.inventoryMigration){state.inventory.pistol=Math.max(1,state.inventory.pistol||0);state.inventoryMigration=true;syncInventory(state);const weapon=state.inventoryStacks.find(t=>t.id===state.weapon);if(weapon)takeInHands(state,weapon.uid)}
syncInventory(state);
for(const key of ['vehicles','vehicleSequence','activeVehicle','vehicleView','thirdPerson','companion','npcs','cash','bank','bankHistory','adminCreatures','xmlOverrides','groundDrops','lootTimers','eventTimers','worldEvents','godMode','configSpawnInitialized','adminLog','runtimeLogs','editorObjects','beachJourney','beachCarCreated','constructionSequence','materialNodes','diving','oxygen'])if(saved?.[key]!==undefined)state[key]=saved[key];
if(!saved){startBeachJourney(state);syncInventory(state);}
state.construction=validateConstruction(saved?.construction);state.playerFeet=Number.isFinite(saved?.playerFeet)?saved.playerFeet:heightAt(state.position.x,state.position.z);
window.addEventListener('error',event=>{state.runtimeLogs??=[];state.runtimeLogs.push(String(event.message));state.runtimeLogs=state.runtimeLogs.slice(-50)});
let worldRuntime,buildings,mapEditor,constructionWorld,constructionUI;
function walkHeight(x,z){const base=buildings?.floorAt(x,z)??groundHeight(x,z,heightAt),floor=constructionWorld?.floorAt(x,z,state.playerFeet??base);return floor!==null&&floor!==undefined&&(floor>=.5||state.diving)?Math.max(base,floor):base;}
let tranquilizerMode=false,fishingCooldown=0,forageCooldown=0;
const keys=new Set(),chunks=new Map(),zombies=[],dinos=[],wildlife=[],resources=[],siteObjects=new Map();
const dynamic=new THREE.Group();outside.add(dynamic);
let started=false,paused=false,isPointer=false,yaw=Number(state.yaw)||0,pitch=0,lastTime=performance.now(),hudTime=0,chunkTime=0,notificationTimeout=0,shootCooldown=0,currentlySprinting=false;
let boatMesh=null,interiorEntrance=null,interiorTreasure=null,headlamp=false,underwaterNotice=false;
let controlsTouch=false,touchYaw=0,touchPitch=0;
const touchState={w:false,a:false,s:false,d:false};
let controller=null,previousPadButtons=[],controllerMove={x:0,y:0},controllerLook={x:0,y:0},controllerSprint=false,controllerFire=false,controllerFireLast=false,controllerMenuAt=0,controllerMenuAxis=0,controllerId="";
const water=new THREE.Mesh(new THREE.PlaneGeometry(WORLD_HALF*2.5,WORLD_HALF*2.5),graphics.water);
water.rotation.x=-Math.PI/2;water.position.y=.5;outside.add(water);
function notice(message){
 const toast=$("toast");toast.textContent=message;toast.classList.remove("hidden");
 clearTimeout(notificationTimeout);notificationTimeout=setTimeout(()=>toast.classList.add("hidden"),3200);
}
function save(){try{
 if(network?.connected)return; // Never write multiplayer state into the solo save.
 state.yaw=yaw;
 for(const d of dinos)state.dinoEffects[d.id]={torpor:d.torpor||0,unconscious:!!d.unconscious,unconsciousTime:d.unconsciousTime||0,tameProgress:d.tameProgress||0};
 localStorage.setItem(STORAGE,JSON.stringify(state))
}catch{notice("Sauvegarde locale saturée")}}
setInterval(()=>{if(started)save()},12000);
window.addEventListener("pagehide",save);
function terrainColor(biome,height){
 if(height<0)return [0.35,.36,.3];
 const colors={plage:[.70,.63,.43],prairie:[.28,.42,.29],"forêt":[.18,.31,.23],jungle:[.08,.30,.19],"hautes-terres":[.33,.35,.30],montagne:[.40,.39,.35],neiges:[.82,.84,.83]};
 return colors[biome]||[.28,.38,.27];
}
const chunkSolids=new Map();
function makeTerrain(cx,cz){
 const solids=[];chunkSolids.set(cx+","+cz,solids);
 const group=new THREE.Group();group.position.set(cx*CHUNK_SIZE,0,cz*CHUNK_SIZE);
 const verts=32,geo=new THREE.PlaneGeometry(CHUNK_SIZE,CHUNK_SIZE,verts,verts);geo.rotateX(-Math.PI/2);
 const arr=geo.attributes.position,colors=[];
 for(let i=0;i<arr.count;i++){
  const x=arr.getX(i)+group.position.x,z=arr.getZ(i)+group.position.z;
  const h=heightAt(x,z);arr.setY(i,h);
  const c=terrainColor(biomeAt(x,z),h);colors.push(...c);
 }
 geo.setAttribute("color",new THREE.Float32BufferAttribute(colors,3));
 geo.computeVertexNormals();const mesh=new THREE.Mesh(geo,graphics.terrain);mesh.receiveShadow=true;group.add(mesh);
 // Buildings are generated deterministically inside the cities, not just decorative labels.
 for(const city of CITIES){
  if(Math.hypot(city.x-group.position.x,city.z-group.position.z)>city.radius+CHUNK_SIZE)continue;
  const minX=Math.floor((group.position.x-CHUNK_SIZE/2)/76),maxX=Math.ceil((group.position.x+CHUNK_SIZE/2)/76);
  const minZ=Math.floor((group.position.z-CHUNK_SIZE/2)/76),maxZ=Math.ceil((group.position.z+CHUNK_SIZE/2)/76);
  for(let gx=minX;gx<=maxX;gx++)for(let gz=minZ;gz<=maxZ;gz++){
   const x=gx*76+14,z=gz*76+14;
   if(x<group.position.x-CHUNK_SIZE/2||x>=group.position.x+CHUNK_SIZE/2||z<group.position.z-CHUNK_SIZE/2||z>=group.position.z+CHUNK_SIZE/2)continue;
   if(Math.hypot(x-city.x,z-city.z)>city.radius||hash2(gx,gz)<1-city.density)continue;
   if(reserveBuilding(x,z,buildings?.objects())||reserveBeach(x,z))continue;
   const y=heightAt(x,z);if(y<2)continue;
   const width=25+hash2(gx+7,gz)*25,depth=25+hash2(gx,gz+8)*23;
   if(Math.abs(x)<width/2+3&&Math.abs(z-180)<depth/2+3)continue;
   const height=9+Math.pow(hash2(gx+3,gz+3),1.65)*(city.id==="helion"?112:70);
   solids.push({x,z,width,depth});
   graphics.building(group,x-group.position.x,y,z-group.position.z,width,height,depth,Math.floor(hash2(gx,gz,993)*4),Math.hypot(x-state.position.x,z-state.position.z)<220);
   if(hash2(gx,gz,123)>.48&&Math.hypot(x-state.position.x,z-state.position.z)<220&&(state.vehicles||[]).filter(v=>v.parkedKey).length<8&&!(state.vehicles||[]).some(v=>v.parkedKey===gx+','+gz)){
    const result=spawnVehicle(state,'car',x-width/2-5,z,heightAt);if(result.ok)result.vehicle.parkedKey=gx+','+gz;
   }
  }
 }
 // Batched vegetation: a few draw calls per streamed sector.
 const tx=Math.floor(group.position.x/65),tz=Math.floor(group.position.z/65),trees=[],grassPoints=[];
 for(let i=0;i<54;i++){
  const sx=group.position.x-CHUNK_SIZE/2+hash2(tx*11+i,tz*7)*CHUNK_SIZE;
  const sz=group.position.z-CHUNK_SIZE/2+hash2(tx*13,tz*3+i)*CHUNK_SIZE;
  const h=heightAt(sx,sz),biome=biomeAt(sx,sz);
  if(h<3||h>420||!["forêt","prairie","hautes-terres","jungle"].includes(biome))continue;
  if(CITIES.some(c=>Math.hypot(c.x-sx,c.z-sz)<c.radius+35))continue;
  trees.push({x:sx-group.position.x,y:h,z:sz-group.position.z,size:13+hash2(i,tx)*14});
 }
 graphics.forest(group,trees);
 for(let i=0;i<(matchMedia("(pointer:coarse)").matches?90:340);i++){
  const sx=group.position.x-CHUNK_SIZE/2+hash2(cx*91+i,cz*19)*CHUNK_SIZE;
  const sz=group.position.z-CHUNK_SIZE/2+hash2(cx*7,cz*97+i)*CHUNK_SIZE;
  const h=heightAt(sx,sz);if(h<3||h>440)continue;
  if(CITIES.some(c=>Math.hypot(c.x-sx,c.z-sz)<c.radius))continue;
  grassPoints.push({x:sx-group.position.x,y:h,z:sz-group.position.z});
 }
 graphics.groundCover(group,grassPoints);
 for(const site of SITES){
  if(site.x<group.position.x-CHUNK_SIZE/2||site.x>=group.position.x+CHUNK_SIZE/2||site.z<group.position.z-CHUNK_SIZE/2||site.z>=group.position.z+CHUNK_SIZE/2)continue;
  if(state.collected.includes(site.id)&&["key","container"].includes(site.type))continue;
  const y=Math.max(2,heightAt(site.x,site.z));
  const material=site.required&&!state.unlocked.includes(site.id)?m.locked:site.type==="key"?m.loot:m.rock;
  let marker;
  if(site.type==="metro"||site.type==="catacomb"){
   marker=meshBox(group,site.x-group.position.x,y+.6,site.z-group.position.z,11,1,11,m.road);
   meshBox(group,site.x-group.position.x,y+3.5,site.z-group.position.z-5,10,6,1,m.wall);
  }else if(site.type==="boat"){
   marker=meshBox(group,site.x-group.position.x,Math.max(y,0)+1,site.z-group.position.z,12,2,5,m.boat);
   meshBox(group,site.x-group.position.x-1,Math.max(y,0)+4,site.z-group.position.z,1,5,1,m.wood);
  }else if(site.type==="village"){
   for(let n=0;n<5;n++){const dx=(n-2)*16,dy=heightAt(site.x+dx,site.z+8);solids.push({x:site.x+dx,z:site.z+8,width:12,depth:10});meshBox(group,site.x+dx-group.position.x,dy+4,site.z+8-group.position.z,12,8,10,m.wood)}
   marker=meshBox(group,site.x-group.position.x,y+2,site.z-group.position.z,4,4,4,m.open);
  }else{
   marker=meshBox(group,site.x-group.position.x,y+2,site.z-group.position.z,site.type==="bunker"?16:5,4,site.type==="bunker"?13:5,material);
   if(site.type==="bunker")meshBox(group,site.x-group.position.x,y+4.4,site.z-group.position.z+5,6,3,.5,m.locked);
  }
  siteObjects.set(site.id,marker);
 }
 if(hash2(cx,cz,884)>.57){
  const x=group.position.x+(hash2(cx,cz,12)-.5)*180,z=group.position.z+(hash2(cx,cz,48)-.5)*180,h=heightAt(x,z);
  if(h>5&&!CITIES.some(c=>Math.hypot(x-c.x,z-c.z)<c.radius)){
   const id="dino-"+cx+"-"+cz,variant=Math.floor(hash2(cx,cz,133)*DINO_TYPES.length),type=DINO_TYPES[variant].id;
   const mesh=createDino(group,x-group.position.x,h,z-group.position.z,type);
   const previous=state.tamed.find(p=>p.id===id);
   const effects=state.dinoEffects[id]||{};dinos.push({id,type,x,z,mesh,chunk:cx+","+cz,trust:state.dinoTrust[id]||0,tamed:!!previous,torpor:effects.torpor||0,unconscious:!!effects.unconscious,unconsciousTime:effects.unconsciousTime||0,tameProgress:effects.tameProgress||0});
  }
 }
 // Shoreline crocodiles, offshore sharks and land wildlife spawn deterministically.
 for(const animal of wildlifeSpawn(cx,cz,{chunkSize:CHUNK_SIZE,hash:hash2,heightAt,biomeAt},2)){
  if(state.hunted.includes(animal.id))continue;
  if(animal.type!=="shark"&&CITIES.some(c=>Math.hypot(animal.x-c.x,animal.z-c.z)<c.radius*.75))continue;
  const positionY=animal.type==="shark"?Math.min(-1,Math.max(-5,heightAt(animal.x,animal.z)+2)):Math.max(0,heightAt(animal.x,animal.z));
  const mesh=createWildAnimal(group,animal.type,animal.x-group.position.x,positionY,animal.z-group.position.z);
  wildlife.push({...animal,mesh,chunk:cx+","+cz,alive:true,attackCooldown:0});
 }
 if(hash2(cx,cz,444)>.78){
  const x=group.position.x+(hash2(cx,cz,102)-.5)*220,z=group.position.z+(hash2(cx,cz,98)-.5)*220,h=heightAt(x,z);
  if(h>3){const bad=meshBox(group,x-group.position.x,h+1.7,z-group.position.z,1.25,3.4,1.3,m.hostile);
   zombies.push({x,z,mesh:bad,chunk:cx+","+cz,hp:55,id:"z-"+cx+"-"+cz,alive:true,cooldown:0})}
 }
 return group;
}
function createDino(group,lx,h,lz,type){
 const col={stegosaur:0x7d9870,raptor:0x97734b,triceratops:0x799387,bront:0x75818c}[type]||0x81936a;
 const material=mat(col),root=new THREE.Group();
 const factor=type==="bront"?2.7:type==="raptor"?.7:1.25;
 const body=new THREE.Mesh(new THREE.SphereGeometry(2.7*factor,8,7),material);body.scale.set(1,.56,.65);body.position.y=2.1*factor;root.add(body);
 for(const xx of [-1.7,1.7])for(const zz of [-.9,.9])meshBox(root,xx*factor,.8*factor,zz*factor,.5*factor,1.6*factor,.5*factor,material);
 const neck=meshBox(root,2.4*factor,2.8*factor,0,2.0*factor,1.05*factor,.86*factor,material);
 const head=meshBox(root,3.6*factor,3.1*factor,0,1.5*factor,.85*factor,1.1*factor,material);
 if(type==="stegosaur")for(let n=0;n<5;n++){const cone=new THREE.Mesh(new THREE.ConeGeometry(.6*factor,1.7*factor,4),mat(0x9d8a55));cone.position.set((n-2)*1.0*factor,3.35*factor,0);root.add(cone)}
 const tail=new THREE.Mesh(new THREE.ConeGeometry(.8*factor,4*factor,5),material);tail.position.set(-3.9*factor,2.0*factor,0);tail.rotation.z=-Math.PI/2;root.add(tail);
 root.position.set(lx,h,lz);group.add(root);return root;
}
function createWildAnimal(group,type,x,y,z){
 const def=WILDLIFE[type],root=new THREE.Group(),shark=type==="shark",croc=type==="crocodile";
 const material=mat(shark?0x557884:croc?0x546844:type==="deer"?0xa07e57:type==="bird"?0x977e5d:type==="jaguar"?0x93754a:0x676450);
 const radius=shark?2.7:croc?2.4:type==="deer"?1.35:1.1;
 const body=new THREE.Mesh(new THREE.SphereGeometry(radius,9,7),material);body.scale.set(shark?1.5:1,shark?.3:croc?.3:.65,shark?.55:1);body.position.y=shark?0:croc?.7:1.8;root.add(body);
 if(croc||shark){
  meshBox(root,radius*1.3,croc?.5:0,0,radius,1,radius*.7,material);
  const tail=new THREE.Mesh(new THREE.ConeGeometry(radius*.45,radius*3,6),material);
  tail.rotation.z=Math.PI/2;tail.position.x=-radius*1.8;root.add(tail);
  if(shark){const fin=new THREE.Mesh(new THREE.ConeGeometry(.9,2.2,3),material);fin.position.y=1.2;root.add(fin)}
 }else{
  for(const xx of [-.8,.8])for(const zz of [-.5,.5])meshBox(root,xx,0.55,zz,.32,1.2,.3,material);
  meshBox(root,1.5,2,0,1,.75,.6,material);
  if(type==="deer"){for(const zz of [-.35,.35]){const antler=cylinder(.07,.13,1.5,m.wood);antler.position.set(1.8,3.2,zz);root.add(antler)}}
 }
 root.position.set(x,y,z);group.add(root);return root;
}
function unloadChunk(id){
 const group=chunks.get(id);if(!group)return;
 outside.remove(group);
 group.traverse(o=>{if(o.geometry)o.geometry.dispose();if(o.material&&!o.material.userData.shared&&o.material!==m.wall&&o.material!==m.rock&&!Object.values(m).includes(o.material))o.material.dispose()});
 chunks.delete(id);chunkSolids.delete(id);
 for(let i=zombies.length-1;i>=0;i--)if(zombies[i].chunk===id)zombies.splice(i,1);
 for(let i=dinos.length-1;i>=0;i--)if(dinos[i].chunk===id){const d=dinos[i];state.dinoEffects[d.id]={torpor:d.torpor||0,unconscious:!!d.unconscious,unconsciousTime:d.unconsciousTime||0,tameProgress:d.tameProgress||0};dinos.splice(i,1)}
 for(let i=wildlife.length-1;i>=0;i--)if(wildlife[i].chunk===id)wildlife.splice(i,1);
}
function updateChunks(force=false){
 if(state.underground)return;
 const center=mapEditor?.active?camera.position:state.position;
 const ccx=Math.floor(center.x/CHUNK_SIZE),ccz=Math.floor(center.z/CHUNK_SIZE);
 const range=matchMedia("(pointer:coarse)").matches?1:2,wanted=new Set();
 for(let x=ccx-range;x<=ccx+range;x++)for(let z=ccz-range;z<=ccz+range;z++){
  const key=x+","+z;wanted.add(key);if(!chunks.has(key)){const group=makeTerrain(x,z);outside.add(group);chunks.set(key,group)}
 }
 for(const id of [...chunks.keys()])if(!wanted.has(id))unloadChunk(id);
 const nearby={x:ccx,z:ccz};if(state.explored?.indexOf(nearby.x+","+nearby.z)<0){state.explored??=[];state.explored.push(nearby.x+","+nearby.z)}
}
function updateStructures(){
 dynamic.clear();
 for(const build of state.structures||[]){
  const y=heightAt(build.x,build.z),group=new THREE.Group();group.position.set(build.x,y,build.z);dynamic.add(group);
  if(build.type==="shelter"){meshBox(group,0,3,0,9,6,8,m.wood);meshBox(group,0,6.2,0,10,1,9,m.roof)}
  else{const fire=new THREE.Mesh(new THREE.ConeGeometry(1.4,2,8),mat(0xea732d));fire.position.y=1;group.add(fire)}
 }
}
function renderBridge(){
 for(const bridge of BRIDGES){
  const dx=bridge.x2-bridge.x1,dz=bridge.z2-bridge.z1,len=Math.hypot(dx,dz);
  const geometry=new THREE.PlaneGeometry(bridge.width,len,1,40);geometry.rotateX(-Math.PI/2);
  const arr=geometry.attributes.position;
  for(let i=0;i<arr.count;i++){
   const t=(arr.getZ(i)+len/2)/len,side=arr.getX(i);
   const x=bridge.x1+dx*t+side*dz/len,z=bridge.z1+dz*t-side*dx/len;
   arr.setXYZ(i,x,bridgeSurface(bridge.x1+dx*t,bridge.z1+dz*t,heightAt)??8,z);
  }
  geometry.computeVertexNormals();outside.add(new THREE.Mesh(geometry,m.road));
  for(let n=0;n<10;n++){
   const t=n/9,x=bridge.x1+dx*t,z=bridge.z1+dz*t,bottom=heightAt(x,z),top=bridgeSurface(x,z,heightAt)??8;
   if(top>bottom)meshBox(outside,x,(top+bottom)/2,z,3,top-bottom,3,m.wall);
  }
 }
}
renderBridge();
function openInterior(site){
 state.underground=site.underground||"bunker";state.entrySite={id:site.id,x:site.x,z:site.z};
 state.position.x=site.x;state.position.z=site.z+2;
 outside.visible=false;underground.visible=true;underground.clear();
 const floorY=-28;
 meshBox(underground,site.x,floorY-1,site.z-31,23,2,95,m.road);
 for(const side of [-1,1])meshBox(underground,site.x+side*11,floorY+7,site.z-31,2,15,95,m.rock);
 meshBox(underground,site.x,floorY+15,site.z-31,24,2,95,m.rock);
 for(let z=0;z<6;z++){
  const zz=site.z-12-z*13;
  for(const side of [-1,1])meshBox(underground,site.x+side*8,floorY+2.3,zz,3,4,5,m.wall);
  const lamp=new THREE.PointLight(0xe5b87a,2,26);lamp.position.set(site.x,floorY+12,zz);underground.add(lamp);
 }
 interiorEntrance=new THREE.Vector3(site.x,0,site.z+2);
 const relic=meshBox(underground,site.x,floorY+1,site.z-69,4,2,3,m.loot);
 interiorTreasure=relic;
 notice("Zone souterraine : "+site.label+" · E à l'entrée pour ressortir · Cherche le coffre au fond.");
}
function exitInterior(){
 const s=state.entrySite;if(!s)return;
 state.underground=null;state.position.x=s.x;state.position.z=s.z+13;
 state.entrySite=null;outside.visible=true;underground.visible=false;underground.clear();
 interiorEntrance=null;interiorTreasure=null;updateChunks(true);notice("Retour à la surface.");
}
function interaction(){
 if(!started||paused)return;
 if(constructionUI?.active){constructionUI.place();return;}
 if(constructionUI?.doorInteract())return;
 if(worldRuntime?.interact())return;
 if(state.underground){
  if(state.entrySite&&Math.hypot(state.position.x-state.entrySite.x,state.position.z-(state.entrySite.z+2))<7){exitInterior();return}
  if(state.entrySite&&Math.hypot(state.position.x-state.entrySite.x,state.position.z-(state.entrySite.z-69))<9){
   const unique="treasure-"+state.entrySite.id;
   if(state.collected.includes(unique)){notice("Ce coffre a déjà été fouillé.");return}
   state.collected.push(unique);const reward=rewardLoot(state,6+state.collected.length);
   notice("Trésor souterrain : "+reward.message);save();return;
  }
  notice("Explore le tunnel, trouve le coffre et reviens vers l'entrée.");return;
 }
 const nearby=nearestSite(state.position.x,state.position.z,20);
 const dino=dinos.find(d=>Math.hypot(d.x-state.position.x,d.z-state.position.z)<11);
 if(dino&&(!nearby||nearby.distance>10)){
  const result=tameWithKibble(state,dino);state.dinoTrust[dino.id]=dino.trust||0;notice(result.message);save();return;
 }
 if(nearby){
  const site=nearby.site;
  if(site.underground){openInterior(site);return}
  if(site.type==="boat"){
   state.boat=!state.boat;if(state.boat){state.mounted=null;state.position.x=site.x;state.position.z=site.z;notice("Bateau lancé : ZQSD/WASD. E pour débarquer près d'une côte.")}else notice("Bateau quitté.");save();return;
  }
  const result=unlockSite(state,site);notice(result.message);
  if(result.ok){updateChunks(true);save()}return;
 }
 if(state.boat){
  if(heightAt(state.position.x,state.position.z)>-3){state.boat=false;notice("Tu as débarqué sur la côte.");return}
  notice("Approche d'une plage avant de quitter le bateau.");return;
 }
 if(forageCooldown>0){notice("Attends quelques instants avant une nouvelle récolte.");return}
 forageCooldown=2.5;
 const reward=forageSupplies(state,{jungle:biomeAt(state.position.x,state.position.z)==="jungle",roll:hash2(Math.floor(state.position.x+Date.now()/6000),Math.floor(state.position.z),91)});
 notice(reward.message);save();
}
let inventoryUI;
function displayInventory(){
 worldRuntime?.cleanup();
 inventoryUI??=inventoryInterface({state,panel:$("panel"),body:$("panelBody"),title:$("panelTitle"),save,notice,open:openPanel,
  recipes:[
   ...KIBBLE_TIERS.map(id=>({id,label:ITEM_DEFS[id].label,cost:KIBBLE_RECIPES[id]})),
   {id:"saddle",label:"Selle renforcée",cost:{fiber:6,cloth:4}},
   {id:"tranq_dart",label:"3 fléchettes tranquillisantes",cost:{scrap:1,cloth:1,berry:2}},
   {id:"fishing_rod",label:"Canne à pêche",cost:{wood:3,fiber:2}},
   {id:"kibble_herbivore",label:"Croquettes herbivores",cost:{berry:6,egg:1,cooked_fish:1}},
   {id:"kibble_carnivore",label:"Croquettes carnivores",cost:{cooked_meat:2,egg:1,berry:2}}
  ],
  actions:{craft:id=>id==="saddle"?importedCraft(id):craftSurvival(state,id),fish:fishNow,campfire:buildCampfire,"cook-meat":()=>cookNear("raw_meat"),"cook-fish":()=>cookNear("raw_fish"),tranq:toggleTranqMode,site:()=>{paused=false;interaction();paused=true}},
  siteInfo:()=>{const near=nearestSite(state.position.x,state.position.z,20);if(!near)return null;const site=near.site;return {label:site.label,locked:site.required&&!hasItem(state,site.required),collected:state.collected.includes(site.id)}}
 });
 inventoryUI.show();
}
function importedCraft(type){
 if(type!=="saddle")return {ok:false,message:"Recette inconnue"};
 if((state.inventory.fiber||0)<6||(state.inventory.cloth||0)<4)return {ok:false,message:"6 fibres et 4 tissus nécessaires."};
 state.inventory.fiber-=6;state.inventory.cloth-=4;state.inventory.saddle=(state.inventory.saddle||0)+1;return {ok:true,message:"Selle fabriquée."}
}
function nearWater(){
 if(state.boat)return true;
 const {x,z}=state.position;
 return [[0,0],[12,0],[-12,0],[0,12],[0,-12],[18,18],[-18,-18]].some(([dx,dz])=>heightAt(x+dx,z+dz)<7);
}
function fishNow(){
 if(!started||state.underground)return {ok:false,message:"Tu ne peux pas pêcher ici."};
 if(fishingCooldown>0)return {ok:false,message:"Patiente un instant avant de relancer ta ligne."};
 fishingCooldown=5.5;
 const result=fishAt(state,{nearWater:nearWater(),roll:hash2(Math.round(state.position.x+performance.now()/1900),Math.round(state.position.z),33)});
 notice(result.message);save();return result;
}
function buildCampfire(){
 if(state.underground)return {ok:false,message:"Impossible de construire ici."};
 const x=state.position.x-Math.sin(yaw)*5,z=state.position.z-Math.cos(yaw)*5;
 const result=buildStructure(state,"fire",x,z);
 if(result.ok){updateStructures();save()}notice(result.message);return result;
}
function cookNear(raw){
 const isNear=(state.structures||[]).some(b=>b.type==="fire"&&Math.hypot(b.x-state.position.x,b.z-state.position.z)<13);
 const result=cookFood(state,raw,isNear);
 notice(result.message);save();return result;
}
function toggleTranqMode(){
 tranquilizerMode=!tranquilizerMode;
 const result={ok:true,message:tranquilizerMode?"Fléchettes tranquillisantes prêtes · V ou R3 pour changer.":"Arme à feu réactivée."};
 notice(result.message);return result;
}
function openPanel(){constructionUI?.cancel();if(mapEditor?.opened)mapEditor.exit();paused=true;$("panel").classList.remove("hidden");if(document.pointerLockElement)document.exitPointerLock()}
function closePanel(){inventoryUI?.cleanup();worldRuntime?.cleanup();paused=false;$("panel").classList.add("hidden")}
function buildShelter(){if(state.underground)return notice('Construction disponible en surface.');constructionUI.show();}
function reload(){
 const available=state.inventory.ammo||0,need=state.magazine-state.ammo;
 if(need<=0){notice("Chargeur plein.");return}
 if(!available){notice("Pas de munitions.");return}
 const count=Math.min(available,need);state.ammo+=count;state.inventory.ammo-=count;notice("Rechargé : "+count+" cartouches");save()
}
function shoot(){
 if(!started||paused||shootCooldown>0||state.health<=0)return;
 if(constructionUI?.active){constructionUI.place();return;}
 if(!["pistol","rifle"].includes(state.hands)&&!tranquilizerMode){notice("Prends une arme dans tes mains depuis l’inventaire.");return;}
 if(state.underground&&tranquilizerMode){notice("Les fléchettes sont réservées aux animaux en surface.");return}
 if(!tranquilizerMode&&!state.ammo){notice("Chargeur vide : R pour recharger.");return}
 if(tranquilizerMode&&!hasItem(state,"tranq_dart")){notice("Fabrique des fléchettes tranquillisantes dans le sac.");return}
 const origin=camera.position.clone(),direction=new THREE.Vector3();
 camera.getWorldDirection(direction);const forward=new THREE.Vector3(direction.x,0,direction.z).normalize();
 let chosen=null,best=145;
 const consider=(kind,target)=>{
  const delta=new THREE.Vector3(target.x-origin.x,0,target.z-origin.z),distance=delta.length();
  if(distance>=best||distance<.5||delta.normalize().dot(forward)<.986)return;
  chosen={kind,target};best=distance;
 };
 if(tranquilizerMode){for(const d of dinos)if(!d.tamed)consider("dino",d)}
 else{
  for(const z of zombies)if(z.alive)consider("infected",z);
  for(const a of wildlife)if(a.alive)consider("wildlife",a);
  for(const npc of worldRuntime?.hostiles()||[])consider("npc",npc);
 }
 const obstacles=[];scene.traverse(o=>{if(o.isMesh&&o.userData.cameraSolid)obstacles.push(o)});
 const ray=new THREE.Raycaster(origin,direction,0,best);if(ray.intersectObjects(obstacles,false).length)chosen=null;
 shootCooldown=tranquilizerMode?.65:.23;
 if(tranquilizerMode){
  if(!chosen){notice("Vise un dinosaure sauvage pour l'endormir.");return}
  const result=tranquilize(state,chosen.target);
  if(result.ok){state.dinoEffects[chosen.target.id]={torpor:chosen.target.torpor,unconscious:chosen.target.unconscious,unconsciousTime:chosen.target.unconsciousTime,tameProgress:chosen.target.tameProgress||0};save()}
  notice(result.message);return;
 }
 state.ammo--;
 if(chosen?.kind==="infected"){
  const enemy=chosen.target;enemy.hp-=42;
  if(enemy.hp<=0){enemy.alive=false;enemy.mesh.visible=false;state.kills++;state.inventory.scrap=(state.inventory.scrap||0)+1;notice("Infecté neutralisé · pièces récupérées.")}
 }else if(chosen?.kind==="npc"){
  const n=chosen.target;n.hp-=42;if(n.hp<=0){n.alive=false;if(!n.rewarded){n.rewarded=true;state.cash=(state.cash||0)+25}notice("Pillard neutralisé · 25 crédits du jeu.");save()}
 }else if(chosen?.kind==="wildlife"){
  const animal=chosen.target;animal.hp-=50;
  if(animal.hp<=0){
   animal.alive=false;animal.mesh.visible=false;
   const result=huntAnimal(state,animal);
   state.kills++;notice(result.message);save();
  }else notice("Animal blessé : "+WILDLIFE[animal.type].name+".");
 }
 if(state.ammo===0)notice("Chargeur vide · R pour recharger.");
}
function mountNear(){
 if(state.mounted){state.mounted=null;notice("Descente de selle.");return}
 const d=dinos.find(x=>x.tamed&&Math.hypot(x.x-state.position.x,x.z-state.position.z)<12);
 if(!d){notice("Approche d'un dinosaure apprivoisé.");return}
 const result=saddleMount(state,d);notice(result.message);save();
}
function breedNear(){
 const close=dinos.filter(x=>x.tamed&&Math.hypot(x.x-state.position.x,x.z-state.position.z)<22);
 if(close.length<2){notice("Il faut deux dinosaures apprivoisés à proximité.");return}
 const result=breed(state,close[0].id,close[1].id);notice(result.message);save();
}
function mapScreen(){
 inventoryUI?.cleanup();worldRuntime?.cleanup();
 $("panelTitle").textContent="CARTE · ARCHIPELS ET CITÉS";
 const canvas=document.createElement("canvas");canvas.width=850;canvas.height=620;canvas.className="mapCanvas";
 const ctx=canvas.getContext("2d"),W=canvas.width,H=canvas.height;
 ctx.fillStyle="#173b48";ctx.fillRect(0,0,W,H);
 const to=(x,z)=>({x:(x+WORLD_HALF)/(WORLD_HALF*2)*W,y:(z+WORLD_HALF)/(WORLD_HALF*2)*H});
 for(let py=0;py<H;py+=5)for(let px=0;px<W;px+=5){
  const x=px/W*WORLD_HALF*2-WORLD_HALF,z=py/H*WORLD_HALF*2-WORLD_HALF,h=heightAt(x,z);
  ctx.fillStyle=h<0?"#1d5260":h>300?"#d2e0d8":h>135?"#72776b":h<7?"#b0a37e":biomeAt(x,z)==="jungle"?"#146940":"#47694c";ctx.fillRect(px,py,5,5);
 }
 for(const zone of JUNGLE_ZONES){
  const p=to(zone.x,zone.z),radius=zone.radius/(WORLD_HALF*2)*W;
  ctx.beginPath();ctx.arc(p.x,p.y,radius,0,Math.PI*2);
  ctx.fillStyle="#008b5252";ctx.fill();ctx.strokeStyle="#39f09bcc";ctx.lineWidth=1.7;ctx.stroke();
  ctx.font="bold 12px sans-serif";ctx.fillStyle="#a5ffd7";ctx.fillText("🌴 "+zone.name,p.x-radius*.5,p.y-6);
 }
 for(const continent of CONTINENTS){const p=to(continent.cx,continent.cz);ctx.fillStyle="#dce9d2";ctx.font="bold 13px sans-serif";ctx.fillText(continent.name,p.x-40,p.y-14);}
 for(const city of CITIES){const p=to(city.x,city.z);ctx.fillStyle="#ffe1a2";ctx.beginPath();ctx.arc(p.x,p.y,5,0,Math.PI*2);ctx.fill();ctx.font="11px sans-serif";ctx.fillText(city.name,p.x+8,p.y+3)}
 for(const o of RP_SITES){const p=to(o.x,o.z);ctx.fillStyle="#b4f1da";ctx.fillRect(p.x-2,p.y-2,4,4);}
 for(const site of SITES){const p=to(site.x,site.z);ctx.fillStyle=site.type==="bunker"?"#e88f80":site.type==="boat"?"#7fe7e4":"#dfc18b";ctx.fillRect(p.x-2,p.y-2,4,4)}
 for(const [i,pin] of (state.mapPins||[]).entries()){
  const p=to(pin.x,pin.z);ctx.strokeStyle="#101d28";ctx.lineWidth=3;ctx.fillStyle="#f8d064";
  ctx.beginPath();ctx.arc(p.x,p.y,6,0,Math.PI*2);ctx.fill();ctx.stroke();
  ctx.font="bold 11px sans-serif";ctx.fillText("R"+(i+1),p.x+8,p.y+3);
 }
 const player=to(state.position.x,state.position.z);ctx.fillStyle="#ff4d55";ctx.beginPath();ctx.arc(player.x,player.y,6,0,Math.PI*2);ctx.fill();
 $("panelBody").replaceChildren(canvas);
 const area=document.createElement("p");area.textContent="Terres émergées : ≈ "+worldMetrics.dryLandKm2.toFixed(1)+" km² hors mer · Carte : 48 × 48 km";$("panelBody").append(area);
 const p=document.createElement("p");p.textContent="● Rouge : joueur · Jaune : villes · Rouge clair : bunkers · Turquoise : bateaux · 🌴 Vert clair : jungles · R : tes repères persistants. Clique sur la carte pour ajouter un repère, clic droit pour supprimer le plus proche."; $("panelBody").append(p);
 canvas.style.cursor="crosshair";
 canvas.addEventListener("click",event=>{
  const rect=canvas.getBoundingClientRect();
  const x=((event.clientX-rect.left)/rect.width)*WORLD_HALF*2-WORLD_HALF;
  const z=((event.clientY-rect.top)/rect.height)*WORLD_HALF*2-WORLD_HALF;
  if(!Number.isFinite(x)||!Number.isFinite(z))return;
  state.mapPins??=[];if(state.mapPins.length>=120){notice("120 repères maximum.");return}
  state.mapPins.push({x:Math.round(clamp(x,-WORLD_HALF,WORLD_HALF)),z:Math.round(clamp(z,-WORLD_HALF,WORLD_HALF))});
  save();mapScreen();
 });
 canvas.addEventListener("contextmenu",event=>{
  event.preventDefault();const rect=canvas.getBoundingClientRect();
  const x=(event.clientX-rect.left)/rect.width*WORLD_HALF*2-WORLD_HALF;
  const z=(event.clientY-rect.top)/rect.height*WORLD_HALF*2-WORLD_HALF;
  const i=(state.mapPins||[]).findIndex(pin=>Math.hypot(pin.x-x,pin.z-z)<540);
  if(i>=0){state.mapPins.splice(i,1);save();mapScreen()}
 });
 openPanel();
}
function updateHud(dt){
 hudTime+=dt;if(hudTime<.1)return;hudTime=0;
 const meters=[["health",state.health],["stamina",state.stamina],["hunger",state.hunger],["thirst",state.thirst]];
 for(const [id,value]of meters){const bar=$(id+"Bar"),label=$(id+"Value");if(bar)bar.style.width=value+"%";if(label)label.textContent=Math.round(value)}
 const {city,distance}=nearestCity(state.position.x,state.position.z);
 const site=nearestSite(state.position.x,state.position.z,16);
 const closestDino=dinos.find(d=>Math.hypot(d.x-state.position.x,d.z-state.position.z)<12);
 const dist=Math.hypot(state.position.x,state.position.z);
 $("region").textContent=state.underground?"SOUS-SOL : "+state.underground.toUpperCase():(distance<city.radius?city.name:biomeAt(state.position.x,state.position.z).toUpperCase());
 $("coordText").textContent="X "+Math.round(state.position.x)+" · Z "+Math.round(state.position.z)+(state.boat?" · BATEAU":"")+(state.mounted?" · SELLE":"")+(state.diving?" · O₂ "+Math.ceil(state.oxygen??100)+"%":"");
 $("equipmentText").textContent=(tranquilizerMode?"FLÉCHETTES ×"+(state.inventory.tranq_dart||0):(state.weapon==="pistol"?"PISTOLET":"FUSIL")+" · "+state.ammo+" / "+(state.inventory.ammo||0))+" · SAC "+weight(state).toFixed(0)+"/"+capacity(state).toFixed(0)+"KG"+(state.illness?" · MALADE":"");
 const hint=$("interaction");
 let text="";
 if(state.underground)text="E · "+(state.entrySite&&Math.hypot(state.position.x-state.entrySite.x,state.position.z-(state.entrySite.z+2))<7?"REMONTER À LA SURFACE":"EXPLORER / OUVRIR COFFRE");
 else if(site)text="E · "+site.site.label+(site.site.required?" · VERROUILLAGE À CLÉ":"");
 else if(closestDino)text=closestDino.unconscious?"E · Donner des croquettes à "+closestDino.type:"V · Fléchettes pour endormir "+closestDino.type+" · E nourrir une fois endormi";
 else if(state.boat)text="BATEAU · navigue vers les îles sans pont";
 else text="E · Récolter œufs/baies · P Pêcher · G Feu de camp · K Cuisiner · V Fléchettes · M Carte";
 hint.textContent=text;hint.classList.toggle("hidden",!text);
 $("compass").textContent=["N","NE","E","SE","S","SO","O","NO"][Math.round((((-yaw%(Math.PI*2))+Math.PI*2)%(Math.PI*2))/(Math.PI/4))%8];
 $("questTitle").textContent=state.unlocked?.includes("bunker-alpha")?"Au-delà des frontières":"Le mystère du bunker Alpha";
 $("questDesc").textContent=state.unlocked?.includes("bunker-alpha")?"Explore le métro, apprivoise les dinosaures, rejoins les îles.":"Trouve la clé Alpha et ouvre le bunker à l'extérieur d'Hélion.";
 const beach=beachObjective(state);if(beach){$("questTitle").textContent=beach.title;$("questDesc").textContent=beach.description;}
}
function updatePlayer(dt){
 if(paused||!started||state.health<=0)return;
 const forward=(keys.has("KeyW")||keys.has("ArrowUp")||keys.has("KeyZ")||touchState.w?1:0)-(keys.has("KeyS")||keys.has("ArrowDown")||touchState.s?1:0)+controllerMove.y;
 const strafe=(keys.has("KeyD")||keys.has("ArrowRight")||touchState.d?1:0)-(keys.has("KeyA")||keys.has("ArrowLeft")||keys.has("KeyQ")||touchState.a?1:0)+controllerMove.x;
 const driving=worldRuntime?.drive(forward,strafe,dt,keys);
 const vector=movementVector(forward,strafe,yaw),fx=vector.x,fz=vector.z;
 const mag=Math.hypot(fx,fz);
 currentlySprinting=!driving&&(keys.has("ShiftLeft")||keys.has("ShiftRight")||controllerSprint)&&state.stamina>3&&!state.underground&&!state.boat;
 const speed=state.boat?30:state.mounted?16:currentlySprinting?8.4:4.6;
 state.stamina=clamp(state.stamina+(currentlySprinting?-dt*17:dt*10),0,100);
 const nx=clamp(state.position.x+fx*speed*dt,-WORLD_HALF,WORLD_HALF);
 const nz=clamp(state.position.z+fz*speed*dt,-WORLD_HALF,WORLD_HALF);
 if(driving){}
 else if(state.underground){const origin=state.entrySite;if(origin){state.position.x=clamp(nx,origin.x-9,origin.x+9);state.position.z=clamp(nz,origin.z-75,origin.z+8)}}
 else if(state.boat){state.position.x=nx;state.position.z=nz}
 else{
  const solids=[...chunkSolids.values()].flat().concat(buildings?.solids()||[],constructionWorld?.solids(state.playerFeet)||[]);
  for(const build of state.structures||[])if(build.type==="shelter")solids.push({x:build.x,z:build.z,width:9,depth:8});
  state.position=moveWithCollisions(state.position,nx-state.position.x,nz-state.position.z,solids,(x,z,tx,tz)=>Math.abs(walkHeight(tx,tz)-walkHeight(x,z))<5+speed*.3);
 }
 let feet=Math.max(walkHeight(state.position.x,state.position.z),0),eye=1.85;
 if(!driving&&state.diving&&heightAt(state.position.x,state.position.z)<.5&&!state.boat&&!state.underground){
  const bottom=heightAt(state.position.x,state.position.z)+.25;state.swimDepth=clamp((state.swimDepth??-2)+((keys.has('Space')?1:0)-(keys.has('ControlLeft')||keys.has('ControlRight')?1:0))*dt*3,bottom,-.2);
  const deck=constructionWorld.floorAt(state.position.x,state.position.z,state.swimDepth);if(deck!==null&&state.swimDepth<deck+.2)state.swimDepth=deck;
  feet=state.swimDepth;eye=1;state.oxygen=clamp((state.oxygen??100)+(feet+eye<.5?-3:12)*dt,0,100);if(state.oxygen===0)state.health=Math.max(0,state.health-dt*5);
 }else{state.diving=false;state.swimDepth=null;state.oxygen=Math.min(100,(state.oxygen??100)+dt*15);}
 if(!driving)state.playerFeet=feet;
 let y=state.underground?-26.25:state.boat?2.5:feet+eye;
 if(!driving&&!state.diving&&!state.boat&&!state.underground&&walkHeight(state.position.x,state.position.z)<-2&&mag){state.health=clamp(state.health-dt*.12,0,100);if(!underwaterNotice){notice("Eau profonde : cherche un bateau ou une plage.");underwaterNotice=true}}
 else underwaterNotice=false;
 camera.position.set(state.position.x,y,state.position.z);
 camera.rotation.order="YXZ";camera.rotation.set(-pitch,yaw,0);
 if(state.boat){
  if(!boatMesh){boatMesh=meshBox(scene,0,0,0,6,1.2,12,m.boat)}
  boatMesh.visible=true;boatMesh.position.set(state.position.x,1,state.position.z);boatMesh.rotation.y=yaw;
 }else if(boatMesh)boatMesh.visible=false;
 tickSurvival(state,dt,currentlySprinting);survivalTick(state,dt,biomeAt(state.position.x,state.position.z));
 for(const z of zombies){if(!z.alive||state.underground||worldRuntime?.isAirborne())continue;z.cooldown=Math.max(0,z.cooldown-dt);const dx=state.position.x-z.x,dz=state.position.z-z.z,d=Math.hypot(dx,dz);
  if(d<30&&d>2){z.x+=dx/d*dt*2;z.z+=dz/d*dt*2;z.mesh.position.x+=dx/d*dt*2;z.mesh.position.z+=dz/d*dt*2;z.mesh.position.y=heightAt(z.x,z.z)+1.7}
  if(d<2.5&&z.cooldown===0){state.health=clamp(state.health-9*(1-protection(state)/100),0,100);z.cooldown=2;notice("Attaque d'infecté !")}
 }
 for(const d of dinos){
  if(d.tamed)continue;
  tickTorpor(d,dt);
  d.mesh.rotation.z=d.unconscious?-Math.PI/2:0;
 }
 for(const a of wildlife){
  if(!a.alive)continue;
  a.attackCooldown=Math.max(0,(a.attackCooldown||0)-dt);
  const dx=state.position.x-a.x,dz=state.position.z-a.z,distance=Math.hypot(dx,dz);
  const def=WILDLIFE[a.type];
  if(def.hostile&&!state.underground&&!worldRuntime?.isAirborne()&&!state.boat&&distance<22&&distance>2.2){
   const vx=dx/distance*dt*def.speed,vz=dz/distance*dt*def.speed;
   const nx=a.x+vx,nz=a.z+vz,h=heightAt(nx,nz);
   const valid=a.type==="shark"?h<1:a.type==="crocodile"?h<14:h>2;
   if(valid){a.x=nx;a.z=nz;a.mesh.position.x+=vx;a.mesh.position.z+=vz;}
  }
  if(def.hostile&&!state.underground&&!worldRuntime?.isAirborne()&&!state.boat&&distance<3.8&&a.attackCooldown===0){
   state.health=clamp(state.health-(a.type==="shark"?22:a.type==="crocodile"?15:8)*(1-protection(state)/110),0,100);
   a.attackCooldown=2.8;notice("Attaque : "+def.name+" !");
  }
  if(a.type==="shark"&&a.alive)a.mesh.rotation.y+=dt*.5;
 }
 shootCooldown=Math.max(0,shootCooldown-dt);
 fishingCooldown=Math.max(0,fishingCooldown-dt);
 forageCooldown=Math.max(0,forageCooldown-dt);
 if(state.health<=0){$("deathScreen").classList.remove("hidden");paused=true;save();if(document.pointerLockElement)document.exitPointerLock()}
}
function start(lockPointer=true){
 started=true;paused=false;$("startScreen").classList.add("hidden");$("hud").classList.remove("hidden");
 updateStructures();updateChunks(true);notice("Bienvenue dans ANOMALIA PRIMEVAL OUTBOUNDUN");
 if(lockPointer&&!matchMedia("(pointer:coarse)").matches){try{renderer.domElement.requestPointerLock?.()?.catch(()=>{});}catch{}}
}
const network=createMultiplayer({scene,state,heightAt:walkHeight,notice,onDisconnect:()=>menu.show(),onMapChanged:()=>{buildings?.update();for(const id of [...chunks.keys()])unloadChunk(id);updateChunks();}});
const menu=createStartMenu({state,renderer,start,network,openEditor:()=>mapEditor.open(),newGame:()=>{try{localStorage.setItem(STORAGE+'-before-new-game',JSON.stringify(state));localStorage.removeItem(STORAGE);location.reload();}catch{notice('Impossible de conserver la sauvegarde actuelle.')}} ,onMenu:()=>{constructionUI?.cancel();mapEditor?.exit();save();started=false;paused=true;keys.clear();$("hud").classList.add('hidden');$("panel").classList.add('hidden');if(document.pointerLockElement)document.exitPointerLock?.();}});
const menuButton=document.createElement('button');menuButton.id='menuBtn';menuButton.textContent='MENU';menuButton.onclick=()=>menu.show();document.querySelector('.topbuttons').append(menuButton);
$("panelClose").onclick=closePanel;
$("mapBtn").onclick=mapScreen;
$("inventoryBtn").onclick=displayInventory;
$("helpBtn").onclick=()=>{inventoryUI?.cleanup();worldRuntime?.cleanup(); $("panelTitle").textContent="COMMANDES";$("panelBody").innerHTML="<h3>Clavier / souris</h3><p>ZQSD/WASD : déplacer · Souris : regarder · Maj : courir · E : fouiller/nourrir · T : monter · Y : reproduction · B : construction modulaire · J : plongée · R : recharger · I : inventaire · M : carte · F : lampe · C : bateau · clic : tirer · F2 : admin · F3 : groupe · F5 : vues · chiffres : raccourcis</p><h3>Survie, chasse et cuisine</h3><p>P : pêcher près de l’eau · G : feu de camp · K : cuire une viande ou un poisson cru près du feu · V : mode fléchettes tranquillisantes · E : œufs et baies ou nourrir un dinosaure endormi avec les croquettes. Les crocodiles vivent près des berges, les requins au large et les jaguars dans la jungle. Clique sur la carte pour placer un repère.</p><h3>Manette Xbox et PS5 (USB / Bluetooth)</h3><p>"+GAMEPAD_LABELS.xbox+"</p><p>"+GAMEPAD_LABELS.playstation+"</p><p>Dans les menus : stick gauche ou croix directionnelle pour sélectionner, A / ✕ pour valider, B / ○ pour revenir. La prise en charge dépend de la reconnaissance de la manette par le navigateur.</p><p>Les bunkers et les conteneurs nécessitent des clés. Explore les caches avant d'entrer. Les animaux doivent être nourris et sellés.</p>";openPanel() };
$("respawnBtn").onclick=()=>{state.health=65;state.thirst=Math.max(35,state.thirst);state.hunger=Math.max(35,state.hunger);state.position=state.beachJourney?{x:435,z:90}:{x:0,z:180};state.underground=null;outside.visible=true;underground.visible=false;$("deathScreen").classList.add("hidden");paused=false;updateChunks(true);save()};
window.addEventListener("keydown",event=>{
 if(event.target.matches?.("input,textarea,select"))return;
 keys.add(event.code);
 if(["Tab","Space","ArrowUp","ArrowDown","F2","F3","F5"].includes(event.code))event.preventDefault();
 if(!started)return;
 if(event.repeat)return;
 if(!paused&&/^Digit[0-9]$/.test(event.code)){syncInventory(state);const index=(Number(event.code.slice(-1))+9)%10,id=state.quickbar[index],stack=state.inventoryStacks.find(t=>t.id===id);if(stack){const result=takeInHands(state,stack.uid);notice(result.message);save()}return;}
 switch(event.code){
  case "F2":worldRuntime?.show('admin');break;
  case "F3":worldRuntime?.show('companions');break;
  case "F5":worldRuntime?.toggleView();break;
  case "KeyH":$("helpBtn").click();break;
  case "KeyI":$("panel").classList.contains("hidden")?displayInventory():closePanel();break;
  case "KeyM":$("panel").classList.contains("hidden")?mapScreen():closePanel();break;
  case "Escape":constructionUI?.cancel();if(!$("panel").classList.contains("hidden"))closePanel();break;
  case "KeyE":interaction();break;
  case "KeyB":buildShelter();break;
  case "KeyR":if(constructionUI?.active)constructionUI.rotate();else reload();break;
  case "KeyJ":if(heightAt(state.position.x,state.position.z)<.5&&!worldRuntime.vehicle()){state.diving=!state.diving;state.swimDepth=state.diving?-2:null;notice(state.diving?"Plongée : Espace monter · Ctrl descendre · oxygène limité":"Retour vers la surface");}else notice("Approche de l’eau pour plonger.");break;
  case "KeyT":mountNear();break;
  case "KeyY":breedNear();break;
  case "KeyF":headlamp=!headlamp;hemi.intensity=headlamp?2:.95;notice(headlamp?"Lampe activée.":"Lampe désactivée.");break;
  case "KeyP":fishNow();break;
  case "KeyG":buildCampfire();break;
  case "KeyK":cookNear(hasItem(state,"raw_meat")?"raw_meat":"raw_fish");break;
  case "KeyV":toggleTranqMode();break;
  case "KeyC":if(state.boat){state.boat=false;notice("Bateau quitté")}else notice("Trouve un port pour embarquer.");break;
 }
});
window.addEventListener("keyup",event=>keys.delete(event.code));
window.addEventListener("blur",()=>keys.clear());
renderer.domElement.addEventListener("click",()=>{if(!started||paused)return;if(document.pointerLockElement!==renderer.domElement&&!matchMedia("(pointer:coarse)").matches)renderer.domElement.requestPointerLock?.();else shoot()});
document.addEventListener("pointerlockchange",()=>{isPointer=document.pointerLockElement===renderer.domElement});
document.addEventListener("mousemove",event=>{if(!isPointer||paused)return;yaw-=event.movementX*.00225;pitch=clamp(pitch+event.movementY*.00225,-1.43,1.43)});
if(matchMedia("(pointer:coarse)").matches){
 const touch=document.createElement("div");touch.id="mobileControls";touch.style.cssText="position:fixed;z-index:7;bottom:24px;left:9px;right:9px;display:flex;justify-content:space-between;pointer-events:none";
 touch.innerHTML='<div style="display:flex;flex-direction:column;gap:5px;align-items:center"><button data-move="w">▲</button><div><button data-move="a">◀</button><button data-move="s">▼</button><button data-move="d">▶</button></div></div><div style="display:grid;grid-template-columns:repeat(2,auto);gap:5px"><button data-act="e">E</button><button data-act="shoot">TIR</button><button data-act="inventory">SAC</button><button data-act="map">CARTE</button><button data-act="fish">PÊCHE</button><button data-act="tranq">FLÉCH.</button></div>';
 document.body.append(touch);for(const b of touch.querySelectorAll("button"))b.style.cssText="pointer-events:auto;background:#122b33c9;border:1px solid #85b7a3;border-radius:12px;color:white;padding:10px;font-weight:800;touch-action:none;min-width:42px";
 for(const b of touch.querySelectorAll("[data-move]")){const k=b.dataset.move;for(const name of ["pointerdown","pointerenter"])b.addEventListener(name,e=>{e.preventDefault();touchState[k]=true});for(const name of ["pointerup","pointercancel","pointerleave"])b.addEventListener(name,e=>{e.preventDefault();touchState[k]=false})}
 const actions={e:interaction,shoot,inventory:displayInventory,map:mapScreen,fish:fishNow,tranq:toggleTranqMode};
 for(const b of touch.querySelectorAll("[data-act]"))b.onclick=actions[b.dataset.act];
 let sx=0,sy=0;
 renderer.domElement.addEventListener("touchstart",e=>{if(e.touches.length===1){sx=e.touches[0].clientX;sy=e.touches[0].clientY}},{passive:true});
 renderer.domElement.addEventListener("touchmove",e=>{if(e.touches.length!==1||paused)return;const t=e.touches[0];yaw-=(t.clientX-sx)*.005;pitch=clamp(pitch+(t.clientY-sy)*.004,-1.4,1.4);sx=t.clientX;sy=t.clientY},{passive:true});
}
// Read the Web Gamepad API once per render frame. Standard mappings cover Xbox and DualSense.
function controllerActions(action){
 if(action==="accept"){
  if(!started){$("startBtn").click();return}
  if(!$("deathScreen").classList.contains("hidden")){$("respawnBtn").click();return}
  if(paused){const focused=document.activeElement;
   if(focused?.matches?.("#panel button"))focused.click();
   else $("panel").querySelector("button")?.focus();
   return;
  }
  interaction();return;
 }
 if(action==="back"){
  if(paused)closePanel();
  else if(started){if(document.pointerLockElement)document.exitPointerLock?.();$("helpBtn").click()}
  return;
 }
 if(action==="menu"){if(!started){$("startBtn").click();return}if(paused)closePanel();else $("helpBtn").click();return}
 if(!started||state.health<=0)return;
 if(paused){if(action==="inventory"||action==="map")closePanel();return}
 switch(action){
  case "interact":if(controller?.aim)fishNow();else interaction();break;
  case "inventory":displayInventory();break;
  case "map":mapScreen();break;
  case "lamp":headlamp=!headlamp;hemi.intensity=headlamp?2:.95;notice(headlamp?"Lampe activée.":"Lampe désactivée.");break;
  case "reload":reload();break;
  case "mount":mountNear();break;
  case "boat":if(state.boat){state.boat=false;notice("Bateau quitté")}else interaction();break;
  case "breed":breedNear();break;
  case "build":buildShelter();break;
  case "focus":toggleTranqMode();break;
 }
}
function controllerMenuNavigate(direction,now){
 if(now-controllerMenuAt<190)return;
 controllerMenuAt=now;
 const elements=[...$("panel").querySelectorAll("button:not(:disabled),[tabindex='0']")].filter(el=>el.offsetParent!==null);
 if(!elements.length)return;
 const current=elements.indexOf(document.activeElement);
 const next=current<0?0:(current+(direction>0?1:-1)+elements.length)%elements.length;
 elements[next].focus({preventScroll:true});
}
function pollController(dt,now){
 const pad=selectGamepad(()=>navigator.getGamepads?.());
 if(!pad){
  if(controllerId){notice("Manette déconnectée — clavier/souris toujours actifs.");controllerId=""}
  controller=null;previousPadButtons=[];controllerMove.x=controllerMove.y=0;
  controllerLook.x=controllerLook.y=0;controllerSprint=controllerFire=false;controllerFireLast=false;return;
 }
 if(pad.id!==controllerId){controllerId=pad.id;previousPadButtons=[];notice("Manette reconnue : "+(controllerFamily(pad.id)==="playstation"?"PS5 / PlayStation":"Xbox / compatible")+" · Options/Menu pour les commandes.")}
 controller=readGamepad(pad,previousPadButtons);
 if(!controller)return;
 previousPadButtons=controller.buttons;
 controllerMove.x=controller.moveX;controllerMove.y=controller.moveY;
 controllerLook.x=controller.lookX;controllerLook.y=controller.lookY;
 controllerSprint=controller.sprint;
 controllerFire=controller.fire;
 if(started&&!paused&&state.health>0){
  const sensitivity=2.35;
  yaw-=controllerLook.x*sensitivity*dt;
  pitch=clamp(pitch+controllerLook.y*sensitivity*dt,-1.43,1.43);
  if(controller.fire&&!controllerFireLast)shoot();
 }else if(paused){
  const y=controller.moveY;
  const verticalUp=controller.buttons[12],verticalDown=controller.buttons[13];
  if(verticalUp||verticalDown||Math.abs(y)>.55){
   const direction=verticalUp? -1:verticalDown?1:(y>0?-1:1);
   controllerMenuNavigate(direction,now);
  }
 }
 controllerFireLast=controller.fire;
 for(const action of controller.justPressed)controllerActions(action);
}
window.addEventListener("gamepadconnected",event=>{if(!event.gamepad)return;controllerId="";previousPadButtons=[]});
window.addEventListener("gamepaddisconnected",event=>{if(event.gamepad?.id===controllerId)controllerId=""});
window.addEventListener("resize",()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight)});
camera.position.set(state.position.x,heightAt(state.position.x,state.position.z)+1.85,state.position.z);
camera.rotation.order="YXZ";camera.rotation.set(0,yaw,0);
buildings=createBuildings({scene,state,heightAt,materials:{concrete:graphics.concrete,wood:graphics.wood,dark:m.roof}});
constructionWorld=createConstructionWorld({scene,state,heightAt,materials:m});
worldRuntime=createWorldRuntime({state,scene,camera,renderer,heightAt:walkHeight,solids:()=>[...chunkSolids.values()].flat().concat(buildings.solids(),constructionWorld.solids(state.playerFeet)),yaw:()=>yaw,save,notice,panel:$("panel"),body:$("panelBody"),title:$("panelTitle"),open:openPanel,close:closePanel,
 cleanup:()=>{inventoryUI?.cleanup();worldRuntime?.cleanup()},enemies:()=>[...zombies,...wildlife.filter(a=>WILDLIFE[a.type].hostile),...(worldRuntime?.hostiles()||[])],
 spawnDino:(d,created)=>{
  if(dinos.some(n=>n.id===d.id))return;
  const known=state.tamed.find(p=>p.id===d.id);d={...d,tamed:d.tamed||!!known,...state.dinoEffects[d.id]};
  const mesh=createDino(outside,d.x,heightAt(d.x,d.z),d.z,d.type);
  dinos.push({...d,mesh,chunk:"admin",trust:d.tamed?100:0,torpor:0,unconscious:false});
  if(d.tamed&&!state.tamed.some(p=>p.id===d.id))state.tamed.push({id:d.id,type:d.type,name:DINO_TYPES.find(p=>p.id===d.type)?.label||d.type,hasSaddle:true});
 }
});
constructionUI=createConstructionUI({state,scene,camera,heightAt,world:constructionWorld,save,notice,panel:$('panel'),body:$('panelBody'),title:$('panelTitle'),open:openPanel,close:closePanel,cleanup:()=>{inventoryUI?.cleanup();worldRuntime?.cleanup();}});
mapEditor=createMapEditor({state,scene,camera,renderer,buildings,save,notice,network,onChanged:()=>{for(const id of [...chunks.keys()])unloadChunk(id);updateChunks();},setPaused:value=>{paused=value;keys.clear();if(value){constructionUI?.cancel();inventoryUI?.cleanup();worldRuntime?.cleanup();$("panel").classList.add('hidden');}}});
window.addEventListener('keydown',e=>{if(e.code==='F4'&&started&&!e.target.matches?.('input,textarea,select')){e.preventDefault();mapEditor.open();}});
for(const [id,label,handler]of [["editorBtn","ANOMALIA EDITOR · F4",()=>mapEditor.open()],["adminBtn","ADMIN · F2",()=>worldRuntime.show('admin')],["companionBtn","GROUPE · F3",()=>worldRuntime.show('companions')],["viewBtn","VUE · F5",()=>worldRuntime.toggleView()]]){const button=document.createElement('button');button.id=id;button.textContent=label;button.onclick=handler;document.querySelector('.topbuttons').append(button)}
function loop(now){
 requestAnimationFrame(loop);
 const dt=Math.min(.08,Math.max(0,(now-lastTime)/1000));lastTime=now;
 pollController(dt,now);
 if(started){updatePlayer(dt);chunkTime+=dt;if(chunkTime>.35){chunkTime=0;updateChunks()}updateHud(dt)}
 buildings.update();constructionWorld.root.visible=!state.underground;constructionWorld.update();constructionUI.update();
 worldRuntime?.update(dt,now/1000,started&&!paused&&state.health>0);
 if(!mapEditor.active)worldRuntime?.applyCamera(pitch);
 mapEditor.update(dt);
 network.update(dt,yaw,started&&!paused);
 for(const d of dinos)if(state.mounted===d.id){d.x=state.position.x;d.z=state.position.z;d.mesh.position.set(d.x,heightAt(d.x,d.z),d.z);d.mesh.rotation.y=yaw+Math.PI;}
 graphics.update(now/1000);
 renderer.render(scene,camera);
 if(new URLSearchParams(location.search).has("smoke"))window.__ANOMALIA_DIAGNOSTICS={calls:renderer.info.render.calls,triangles:renderer.info.render.triangles,position:{...state.position},started,construction:{count:state.construction.length,active:constructionUI.active,oxygen:state.oxygen,diving:state.diving},network:{connected:network.connected,players:network.count},world:worldRuntime?.debug()};
}
requestAnimationFrame(loop);
