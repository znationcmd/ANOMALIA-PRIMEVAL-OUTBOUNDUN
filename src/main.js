
import * as THREE from "three";
import {JUNGLE_ZONES,WILDLIFE,wildlifeSpawn,huntAnimal,forageSupplies,fishAt,cookFood,craftSurvival,tranquilize,tickTorpor,tameWithKibble} from "./ecology.js";
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
const box=(w,h,d,material)=>new THREE.Mesh(new THREE.BoxGeometry(w,h,d),material);
const cylinder=(r1,r2,h,material)=>new THREE.Mesh(new THREE.CylinderGeometry(r1,r2,h,7),material);
function meshBox(parent,x,y,z,w,h,d,material){const q=box(w,h,d,material);q.position.set(x,y,z);parent.add(q);return q}
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
let tranquilizerMode=false,fishingCooldown=0,forageCooldown=0;
const keys=new Set(),chunks=new Map(),zombies=[],dinos=[],wildlife=[],resources=[],siteObjects=new Map();
const dynamic=new THREE.Group();outside.add(dynamic);
let started=false,paused=false,isPointer=false,yaw=Number(state.yaw)||0,pitch=0,lastTime=performance.now(),hudTime=0,chunkTime=0,notificationTimeout=0,shootCooldown=0,currentlySprinting=false;
let boatMesh=null,interiorEntrance=null,interiorTreasure=null,headlamp=false,underwaterNotice=false;
let controlsTouch=false,touchYaw=0,touchPitch=0;
const touchState={w:false,a:false,s:false,d:false};
let controller=null,previousPadButtons=[],controllerMove={x:0,y:0},controllerLook={x:0,y:0},controllerSprint=false,controllerFire=false,controllerFireLast=false,controllerMenuAt=0,controllerMenuAxis=0,controllerId="";
const water=new THREE.Mesh(new THREE.PlaneGeometry(WORLD_HALF*2.5,WORLD_HALF*2.5),new THREE.MeshStandardMaterial({color:0x1d667a,roughness:.3,metalness:.05,transparent:true,opacity:.81,depthWrite:false,side:THREE.DoubleSide}));
water.rotation.x=-Math.PI/2;water.position.y=.5;outside.add(water);
function notice(message){
 const toast=$("toast");toast.textContent=message;toast.classList.remove("hidden");
 clearTimeout(notificationTimeout);notificationTimeout=setTimeout(()=>toast.classList.add("hidden"),3200);
}
function save(){try{
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
function makeTerrain(cx,cz){
 const group=new THREE.Group();group.position.set(cx*CHUNK_SIZE,0,cz*CHUNK_SIZE);
 const verts=18,geo=new THREE.PlaneGeometry(CHUNK_SIZE,CHUNK_SIZE,verts,verts);geo.rotateX(-Math.PI/2);
 const arr=geo.attributes.position,colors=[];
 for(let i=0;i<arr.count;i++){
  const x=arr.getX(i)+group.position.x,z=arr.getZ(i)+group.position.z;
  const h=heightAt(x,z);arr.setY(i,h);
  const c=terrainColor(biomeAt(x,z),h);colors.push(...c);
 }
 geo.setAttribute("color",new THREE.Float32BufferAttribute(colors,3));
 geo.computeVertexNormals();const mesh=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({vertexColors:true,roughness:1,side:THREE.DoubleSide}));group.add(mesh);
 // Buildings are generated deterministically inside the cities, not just decorative labels.
 for(const city of CITIES){
  if(Math.hypot(city.x-group.position.x,city.z-group.position.z)>city.radius+CHUNK_SIZE)continue;
  const minX=Math.floor((group.position.x-CHUNK_SIZE/2)/76),maxX=Math.ceil((group.position.x+CHUNK_SIZE/2)/76);
  const minZ=Math.floor((group.position.z-CHUNK_SIZE/2)/76),maxZ=Math.ceil((group.position.z+CHUNK_SIZE/2)/76);
  for(let gx=minX;gx<=maxX;gx++)for(let gz=minZ;gz<=maxZ;gz++){
   const x=gx*76+14,z=gz*76+14;
   if(x<group.position.x-CHUNK_SIZE/2||x>=group.position.x+CHUNK_SIZE/2||z<group.position.z-CHUNK_SIZE/2||z>=group.position.z+CHUNK_SIZE/2)continue;
   if(Math.hypot(x-city.x,z-city.z)>city.radius||hash2(gx,gz)<1-city.density)continue;
   const y=heightAt(x,z);if(y<2)continue;
   const width=25+hash2(gx+7,gz)*25,depth=25+hash2(gx,gz+8)*23;
   const height=9+Math.pow(hash2(gx+3,gz+3),1.65)*(city.id==="helion"?112:70);
   const building=meshBox(group,x-group.position.x,y+height/2,z-group.position.z,width,height,depth,m.wall);
   const roof=meshBox(group,x-group.position.x,y+height+.45,z-group.position.z,width+1,1,depth+1,m.roof);
   if(height>30){
    for(let f=1;f<Math.min(8,height/9);f++){
     const yy=y+f*9;
     meshBox(group,x-group.position.x,y+f*9,z-group.position.z+depth/2+.03,width*.7,1.15,.12,m.glass);
    }
   }
  }
 }
 // Forests and shrubs surrounding the cities; each sector has a bounded draw cost.
 const tx=Math.floor(group.position.x/65),tz=Math.floor(group.position.z/65);
 for(let i=0;i<(biomeAt(group.position.x,group.position.z)==="jungle"?46:26);i++){
  const sx=group.position.x-170+hash2(tx*11+i,tz*7)*340;
  const sz=group.position.z-170+hash2(tx*13,tz*3+i)*340;
  const h=heightAt(sx,sz),biome=biomeAt(sx,sz);
  if(h<3||h>320||!["forêt","prairie","hautes-terres","jungle"].includes(biome))continue;
  if(CITIES.some(c=>Math.hypot(c.x-sx,c.z-sz)<c.radius+90))continue;
  const trunk=cylinder(.7,1.4,8+hash2(i,tx)*6,m.trunk);trunk.position.set(sx-group.position.x,h+5,sz-group.position.z);group.add(trunk);
  const crown=new THREE.Mesh(new THREE.ConeGeometry(5.6,16,7),m.leaves);crown.position.set(sx-group.position.x,h+15,sz-group.position.z);group.add(crown);
 }
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
   for(let n=0;n<5;n++){const dx=(n-2)*16,dy=heightAt(site.x+dx,site.z+8);meshBox(group,site.x+dx-group.position.x,dy+4,site.z+8-group.position.z,12,8,10,m.wood)}
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
 group.traverse(o=>{if(o.geometry)o.geometry.dispose();if(o.material&&o.material!==m.wall&&o.material!==m.rock&&!Object.values(m).includes(o.material))o.material.dispose()});
 chunks.delete(id);
 for(let i=zombies.length-1;i>=0;i--)if(zombies[i].chunk===id)zombies.splice(i,1);
 for(let i=dinos.length-1;i>=0;i--)if(dinos[i].chunk===id){const d=dinos[i];state.dinoEffects[d.id]={torpor:d.torpor||0,unconscious:!!d.unconscious,unconsciousTime:d.unconsciousTime||0,tameProgress:d.tameProgress||0};dinos.splice(i,1)}
 for(let i=wildlife.length-1;i>=0;i--)if(wildlife[i].chunk===id)wildlife.splice(i,1);
}
function updateChunks(force=false){
 if(state.underground)return;
 const ccx=Math.floor(state.position.x/CHUNK_SIZE),ccz=Math.floor(state.position.z/CHUNK_SIZE);
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
 for(const bridge of [{x1:4800,z1:0,x2:5850,z2:0},{x1:-5100,z1:3300,x2:-6000,z2:3600}]){
  const dx=bridge.x2-bridge.x1,dz=bridge.z2-bridge.z1,len=Math.hypot(dx,dz);
  const y=7,deck=meshBox(outside,(bridge.x1+bridge.x2)/2,y,(bridge.z1+bridge.z2)/2,22,2,len,m.road);
  deck.rotation.y=-Math.atan2(dx,dz);
  for(let n=0;n<10;n++){const t=n/9;meshBox(outside,bridge.x1+dx*t,-1,bridge.z1+dz*t,3,16,3,m.wall)}
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
function displayInventory(){
 const html=[],cap=capacity(state),wt=weight(state);
 html.push('<p>Poids : <strong>'+wt.toFixed(1)+' / '+cap.toFixed(1)+' kg</strong> · Chaleur : '+warmth(state)+' · Protection : '+protection(state)+'</p>');
 html.push('<h3>Vêtements équipés</h3><div class="slots">');
 for(const slot of EQUIPMENT_SLOTS){const id=state.equipment[slot],label=ITEM_DEFS[id]?.label||"Vide";html.push('<div class="slot"><b>'+slot.toUpperCase()+'</b> · '+label+' '+(id?'<button data-unequip="'+slot+'">Retirer</button>':'')+'</div>')}
 html.push('</div><h3>Inventaire</h3><div class="grid-inventory">');
 for(const [id,n] of Object.entries(state.inventory).filter(x=>x[1]>0)){const def=ITEM_DEFS[id],name=def?.label||ITEM_NAMES[id]||id;
  let cmd='';if(def?.kind==="clothing")cmd='<button data-equip="'+id+'">Porter</button>';
  else if(["water","food","meat","cooked_meat","cooked_fish","berry","bandage","medicine"].includes(id))cmd='<button data-use="'+id+'">Utiliser</button>';
  html.push('<div class="slot">'+name+' × '+n+' '+cmd+'</div>')}
 html.push('</div><p>Froid et humidité peuvent provoquer des maladies. Cherche des médicaments dans les bunkers.</p>');
 html.push('<p>Maladie : '+(state.illness||"Aucune")+' · Température : '+Number(state.temperature).toFixed(1)+' °C</p>');
 html.push('<h3>Animaux apprivoisés</h3><p>'+(state.tamed.length?state.tamed.map(p=>p.name+" ("+(p.hasSaddle?"sellé":"sans selle")+")").join(", "):"Aucun, nourris les dinosaures avec E.")+'</p>');
 html.push('<button data-craft="saddle">Fabriquer une selle : 6 fibres + 4 tissus</button>');
 html.push('<h3>Chasse, pêche et cuisson</h3>');
 html.push('<p>La chasse donne de la viande crue, des peaux et parfois des œufs. Approche une rive pour pêcher. Un feu de camp est indispensable pour cuire.</p>');
 html.push('<button data-ecology="fish">🎣 Pêcher</button> <button data-ecology="campfire">🔥 Construire un feu de camp</button>');
 html.push('<button data-cook="raw_meat">Cuire la viande</button> <button data-cook="raw_fish">Cuire le poisson</button>');
 html.push('<h3>Apprivoisement des dinosaures</h3><p>Active les fléchettes (V ou R3). Tire pour endormir, puis nourris avec E et des croquettes adaptées.</p>');
 html.push('<button data-ecology="tranq">Mode fléchettes : '+(tranquilizerMode?"ACTIVÉ":"DÉSACTIVÉ")+'</button>');
 html.push('<button data-recipe="tranq_dart">3 fléchettes : ferraille + tissu + 2 baies</button>');
 html.push('<button data-recipe="kibble_herbivore">Croquettes herbivores : 6 baies + 1 œuf + 1 poisson cuit</button>');
 html.push('<button data-recipe="kibble_carnivore">Croquettes carnivores : 2 viandes cuites + 1 œuf + 2 baies</button>');
 html.push('<button data-recipe="fishing_rod">Canne à pêche : 3 bois + 2 fibres</button>');
 $("panelTitle").textContent="INVENTAIRE ET SURVIE";$("panelBody").innerHTML=html.join("");
 $("panelBody").onclick=e=>{
  const b=e.target.closest("button");if(!b)return;let msg="";
  if(b.dataset.equip)msg=equip(state,b.dataset.equip).message;
  if(b.dataset.unequip){const id=state.equipment[b.dataset.unequip];state.equipment[b.dataset.unequip]=null;if(id)state.inventory[id]=(state.inventory[id]||0)+1;msg="Retiré : "+(ITEM_DEFS[id]?.label||id)}
  if(b.dataset.use)msg=consume(state,b.dataset.use).message;
  if(b.dataset.craft){const result=importedCraft(b.dataset.craft);msg=result.message}
  if(b.dataset.cook)msg=cookNear(b.dataset.cook).message;
  if(b.dataset.recipe)msg=craftSurvival(state,b.dataset.recipe).message;
  if(b.dataset.ecology==="fish")msg=fishNow().message;
  if(b.dataset.ecology==="campfire")msg=buildCampfire().message;
  if(b.dataset.ecology==="tranq")msg=toggleTranqMode().message;
  notice(msg);save();displayInventory()
 };
 openPanel();
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
 const x=state.position.x+Math.sin(yaw)*5,z=state.position.z+Math.cos(yaw)*5;
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
function openPanel(){paused=true;$("panel").classList.remove("hidden");if(document.pointerLockElement)document.exitPointerLock()}
function closePanel(){paused=false;$("panel").classList.add("hidden")}
function buildShelter(){
 if(state.underground){notice("Construction impossible sous terre.");return}
 const result=buildStructure(state,"shelter",state.position.x+Math.sin(yaw)*8,state.position.z+Math.cos(yaw)*8);
 notice(result.message);if(result.ok){updateStructures();save()}
}
function reload(){
 const available=state.inventory.ammo||0,need=state.magazine-state.ammo;
 if(need<=0){notice("Chargeur plein.");return}
 if(!available){notice("Pas de munitions.");return}
 const count=Math.min(available,need);state.ammo+=count;state.inventory.ammo-=count;notice("Rechargé : "+count+" cartouches");save()
}
function shoot(){
 if(!started||paused||shootCooldown>0||state.health<=0)return;
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
 }
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
 for(const city of CITIES){const p=to(city.x,city.z);ctx.fillStyle="#ffe1a2";ctx.beginPath();ctx.arc(p.x,p.y,5,0,Math.PI*2);ctx.fill();ctx.font="11px sans-serif";ctx.fillText(city.name,p.x+8,p.y+3)}
 for(const site of SITES){const p=to(site.x,site.z);ctx.fillStyle=site.type==="bunker"?"#e88f80":site.type==="boat"?"#7fe7e4":"#dfc18b";ctx.fillRect(p.x-2,p.y-2,4,4)}
 for(const [i,pin] of (state.mapPins||[]).entries()){
  const p=to(pin.x,pin.z);ctx.strokeStyle="#101d28";ctx.lineWidth=3;ctx.fillStyle="#f8d064";
  ctx.beginPath();ctx.arc(p.x,p.y,6,0,Math.PI*2);ctx.fill();ctx.stroke();
  ctx.font="bold 11px sans-serif";ctx.fillText("R"+(i+1),p.x+8,p.y+3);
 }
 const player=to(state.position.x,state.position.z);ctx.fillStyle="#ff4d55";ctx.beginPath();ctx.arc(player.x,player.y,6,0,Math.PI*2);ctx.fill();
 $("panelBody").replaceChildren(canvas);
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
 $("coordText").textContent="X "+Math.round(state.position.x)+" · Z "+Math.round(state.position.z)+(state.boat?" · BATEAU":"")+(state.mounted?" · SELLE":"");
 $("equipmentText").textContent=(tranquilizerMode?"FLÉCHETTES ×"+(state.inventory.tranq_dart||0):(state.weapon==="pistol"?"PISTOLET":"FUSIL")+" · "+state.ammo+" / "+(state.inventory.ammo||0))+" · SAC "+weight(state).toFixed(0)+"/"+capacity(state).toFixed(0)+"KG"+(state.illness?" · MALADE":"");
 const hint=$("interaction");
 let text="";
 if(state.underground)text="E · "+(state.entrySite&&Math.hypot(state.position.x-state.entrySite.x,state.position.z-(state.entrySite.z+2))<7?"REMONTER À LA SURFACE":"EXPLORER / OUVRIR COFFRE");
 else if(site)text="E · "+site.site.label+(site.site.required?" · VERROUILLAGE À CLÉ":"");
 else if(closestDino)text=closestDino.unconscious?"E · Donner des croquettes à "+closestDino.type:"V · Fléchettes pour endormir "+closestDino.type+" · E nourrir une fois endormi";
 else if(state.boat)text="BATEAU · navigue vers les îles sans pont";
 else text="E · Récolter œufs/baies · P Pêcher · G Feu de camp · K Cuisiner · V Fléchettes · M Carte";
 hint.textContent=text;hint.classList.toggle("hidden",!text);
 $("compass").textContent=["N","NE","E","SE","S","SO","O","NO"][Math.round((((yaw%(Math.PI*2))+Math.PI*2)%(Math.PI*2))/(Math.PI/4))%8];
 $("questTitle").textContent=state.unlocked?.includes("bunker-alpha")?"Au-delà des frontières":"Le mystère du bunker Alpha";
 $("questDesc").textContent=state.unlocked?.includes("bunker-alpha")?"Explore le métro, apprivoise les dinosaures, rejoins les îles.":"Trouve la clé Alpha et ouvre le bunker à l'extérieur d'Hélion.";
}
function updatePlayer(dt){
 if(paused||!started||state.health<=0)return;
 const forward=(keys.has("KeyW")||keys.has("ArrowUp")||keys.has("KeyZ")||touchState.w?1:0)-(keys.has("KeyS")||keys.has("ArrowDown")||touchState.s?1:0)+controllerMove.y;
 const strafe=(keys.has("KeyD")||keys.has("ArrowRight")||touchState.d?1:0)-(keys.has("KeyA")||keys.has("ArrowLeft")||keys.has("KeyQ")||touchState.a?1:0)+controllerMove.x;
 let fx=Math.sin(yaw)*forward+Math.cos(yaw)*strafe,fz=Math.cos(yaw)*forward-Math.sin(yaw)*strafe;
 const mag=Math.hypot(fx,fz);if(mag){fx/=mag;fz/=mag}
 currentlySprinting=(keys.has("ShiftLeft")||keys.has("ShiftRight")||controllerSprint)&&state.stamina>3&&!state.underground&&!state.boat;
 const speed=state.boat?30:state.mounted?16:currentlySprinting?8.4:4.6;
 state.stamina=clamp(state.stamina+(currentlySprinting?-dt*17:dt*10),0,100);
 const nx=clamp(state.position.x+fx*speed*dt,-WORLD_HALF,WORLD_HALF);
 const nz=clamp(state.position.z+fz*speed*dt,-WORLD_HALF,WORLD_HALF);
 if(state.underground){const origin=state.entrySite;if(origin){state.position.x=clamp(nx,origin.x-9,origin.x+9);state.position.z=clamp(nz,origin.z-75,origin.z+8)}}
 else if(state.boat){state.position.x=nx;state.position.z=nz}
 else{
  const current=heightAt(state.position.x,state.position.z),next=heightAt(nx,nz);
  if(next>SEA_LEVEL-1&&Math.abs(next-current)<5+speed*.3){state.position.x=nx;state.position.z=nz}
  else if(next<=SEA_LEVEL-1&&Math.abs(next-current)<6){state.position.x=nx;state.position.z=nz}
 }
 let y=state.underground?-26.25:state.boat?2.5:Math.max(heightAt(state.position.x,state.position.z),0)+1.85;
 if(!state.boat&&!state.underground&&heightAt(state.position.x,state.position.z)<-2&&mag){state.health=clamp(state.health-dt*.12,0,100);if(!underwaterNotice){notice("Eau profonde : cherche un bateau ou une plage.");underwaterNotice=true}}
 else underwaterNotice=false;
 camera.position.set(state.position.x,y,state.position.z);
 camera.rotation.order="YXZ";camera.rotation.set(-pitch,yaw,0);
 if(state.boat){
  if(!boatMesh){boatMesh=meshBox(scene,0,0,0,6,1.2,12,m.boat)}
  boatMesh.visible=true;boatMesh.position.set(state.position.x,1,state.position.z);boatMesh.rotation.y=yaw;
 }else if(boatMesh)boatMesh.visible=false;
 tickSurvival(state,dt,currentlySprinting);survivalTick(state,dt,biomeAt(state.position.x,state.position.z));
 for(const z of zombies){if(!z.alive||state.underground)continue;z.cooldown=Math.max(0,z.cooldown-dt);const dx=state.position.x-z.x,dz=state.position.z-z.z,d=Math.hypot(dx,dz);
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
  if(def.hostile&&!state.underground&&!state.boat&&distance<22&&distance>2.2){
   const vx=dx/distance*dt*def.speed,vz=dz/distance*dt*def.speed;
   const nx=a.x+vx,nz=a.z+vz,h=heightAt(nx,nz);
   const valid=a.type==="shark"?h<1:a.type==="crocodile"?h<14:h>2;
   if(valid){a.x=nx;a.z=nz;a.mesh.position.x+=vx;a.mesh.position.z+=vz;}
  }
  if(def.hostile&&!state.underground&&!state.boat&&distance<3.8&&a.attackCooldown===0){
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
function start(){
 started=true;paused=false;$("startScreen").classList.add("hidden");$("hud").classList.remove("hidden");
 updateStructures();updateChunks(true);notice("Bienvenue dans ANOMALIA PRIMEVAL OUTBOUNDUN");
 if(!matchMedia("(pointer:coarse)").matches)renderer.domElement.requestPointerLock?.();
}
$("startBtn").onclick=start;
$("panelClose").onclick=closePanel;
$("mapBtn").onclick=mapScreen;
$("inventoryBtn").onclick=displayInventory;
$("helpBtn").onclick=()=>{ $("panelTitle").textContent="COMMANDES";$("panelBody").innerHTML="<h3>Clavier / souris</h3><p>ZQSD/WASD : déplacer · Souris : regarder · Maj : courir · E : fouiller/nourrir · T : monter · Y : reproduction · B : construire · R : recharger · I : inventaire · M : carte · F : lampe · C : bateau · clic : tirer</p><h3>Survie, chasse et cuisine</h3><p>P : pêcher près de l’eau · G : feu de camp · K : cuire une viande ou un poisson cru près du feu · V : mode fléchettes tranquillisantes · E : œufs et baies ou nourrir un dinosaure endormi avec les croquettes. Les crocodiles vivent près des berges, les requins au large et les jaguars dans la jungle. Clique sur la carte pour placer un repère.</p><h3>Manette Xbox et PS5 (USB / Bluetooth)</h3><p>"+GAMEPAD_LABELS.xbox+"</p><p>"+GAMEPAD_LABELS.playstation+"</p><p>Dans les menus : stick gauche ou croix directionnelle pour sélectionner, A / ✕ pour valider, B / ○ pour revenir. La prise en charge dépend de la reconnaissance de la manette par le navigateur.</p><p>Les bunkers et les conteneurs nécessitent des clés. Explore les caches avant d'entrer. Les animaux doivent être nourris et sellés.</p>";openPanel() };
$("respawnBtn").onclick=()=>{state.health=65;state.thirst=Math.max(35,state.thirst);state.hunger=Math.max(35,state.hunger);state.position={x:0,z:180};state.underground=null;outside.visible=true;underground.visible=false;$("deathScreen").classList.add("hidden");paused=false;updateChunks(true);save()};
window.addEventListener("keydown",event=>{
 if(event.target.matches?.("input,textarea,select"))return;
 keys.add(event.code);
 if(["Tab","Space","ArrowUp","ArrowDown"].includes(event.code))event.preventDefault();
 if(!started)return;
 if(event.repeat)return;
 switch(event.code){
  case "KeyI":$("panel").classList.contains("hidden")?displayInventory():closePanel();break;
  case "KeyM":$("panel").classList.contains("hidden")?mapScreen():closePanel();break;
  case "Escape":if(!$("panel").classList.contains("hidden"))closePanel();break;
  case "KeyE":interaction();break;
  case "KeyB":buildShelter();break;
  case "KeyR":reload();break;
  case "KeyT":mountNear();break;
  case "KeyY":breedNear();break;
  case "KeyF":headlamp=!headlamp;hemi.intensity=headlamp?3.6:2.3;notice(headlamp?"Lampe activée.":"Lampe désactivée.");break;
  case "KeyP":fishNow();break;
  case "KeyG":buildCampfire();break;
  case "KeyK":cookNear(hasItem(state,"raw_meat")?"raw_meat":"raw_fish");break;
  case "KeyV":toggleTranqMode();break;
  case "KeyC":if(state.boat){state.boat=false;notice("Bateau quitté")}else notice("Trouve un port pour embarquer.");break;
 }
});
window.addEventListener("keyup",event=>keys.delete(event.code));
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
  case "lamp":headlamp=!headlamp;hemi.intensity=headlamp?3.6:2.3;notice(headlamp?"Lampe activée.":"Lampe désactivée.");break;
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
function loop(now){
 requestAnimationFrame(loop);
 const dt=Math.min(.08,Math.max(0,(now-lastTime)/1000));lastTime=now;
 pollController(dt,now);
 if(started){updatePlayer(dt);chunkTime+=dt;if(chunkTime>.35){chunkTime=0;updateChunks()}updateHud(dt)}
 renderer.render(scene,camera);
}
requestAnimationFrame(loop);
