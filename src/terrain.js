import * as THREE from "three";
import {WORLD_HALF_SIZE,CHUNK_SIZE,SEA_LEVEL,START,ISLANDS,POIS,BRIDGES,heightAt,biomeAt,chunkCoordinates,rngAt,nearestPoi} from "./world.js";

// Geometry and materials shared between streamed chunks so the game can continuously travel.
const box=new THREE.BoxGeometry(1,1,1);
const cone=new THREE.ConeGeometry(1,1,6);
const stone=new THREE.DodecahedronGeometry(1,0);
const mats={
 dark:new THREE.MeshStandardMaterial({color:0x24313b,roughness:.83}),
 city:new THREE.MeshStandardMaterial({color:0x4a5155,roughness:.87}),
 city2:new THREE.MeshStandardMaterial({color:0x687079,roughness:.81}),
 steel:new THREE.MeshStandardMaterial({color:0x445764,metalness:.5,roughness:.5}),
 concrete:new THREE.MeshStandardMaterial({color:0x747a76,roughness:.95}),
 roof:new THREE.MeshStandardMaterial({color:0x242c31,roughness:.9}),
 rock:new THREE.MeshStandardMaterial({color:0x757e7d,roughness:1}),
 tree:new THREE.MeshStandardMaterial({color:0x315b41,flatShading:true,roughness:1}),
 tree2:new THREE.MeshStandardMaterial({color:0x496b46,flatShading:true,roughness:1}),
 trunk:new THREE.MeshStandardMaterial({color:0x4f3a2d,roughness:1}),
 wood:new THREE.MeshStandardMaterial({color:0x68503a,roughness:1}),
 glass:new THREE.MeshStandardMaterial({color:0x28485e,metalness:.3,roughness:.27}),
 gold:new THREE.MeshStandardMaterial({color:0xf4cf76,metalness:.75,roughness:.22,emissive:0x6b4b13,emissiveIntensity:.3}),
 red:new THREE.MeshStandardMaterial({color:0x8d4235,roughness:.72}),
 blue:new THREE.MeshStandardMaterial({color:0x285f88,roughness:.66}),
 orange:new THREE.MeshBasicMaterial({color:0xffa856}),
 road:new THREE.MeshStandardMaterial({color:0x454c4c,roughness:1})
};
const geoTrunk=new THREE.CylinderGeometry(.3,.48,1,6);
function cube(parent,x,y,z,sx,sy,sz,mat){const o=new THREE.Mesh(box,mat);o.position.set(x,y,z);o.scale.set(sx,sy,sz);o.receiveShadow=false;parent.add(o);return o;}
function tree(parent,x,z,size=1){
 const y=heightAt(x,z),h=(8+size*8);
 const trunk=new THREE.Mesh(geoTrunk,mats.trunk);trunk.position.set(x,y+h*.3,z);trunk.scale.set(1,h*.6,1);parent.add(trunk);
 const leaves=new THREE.Mesh(cone,rngAt(x,z,212)>.5?mats.tree:mats.tree2);leaves.position.set(x,y+h*.84,z);leaves.scale.set(3+size*2,h*.8,3+size*2);parent.add(leaves);
}
function rock(parent,x,z,scale=1){const y=heightAt(x,z),o=new THREE.Mesh(stone,mats.rock);o.position.set(x,y+scale*.35,z);o.scale.set(scale,scale*.62,scale);o.rotation.y=rngAt(x,z,333)*6.28;parent.add(o);}
function building(parent,x,z,city,seed){
 const y=heightAt(x,z),d=Math.hypot(x-city.x,z-city.z)/city.r;
 if(y<2)return;
 const isCenter=d<.44;
 const h=12+Math.pow(rngAt(x,z,52),1.5)*(isCenter?130:52);
 const w=16+rngAt(x,z,3)*25,dep=w*(.65+rngAt(x,z,45)*.33);
 const m=rngAt(x,z,6)>.5?mats.city:mats.city2;
 cube(parent,x,y+h/2,z,w,h,dep,m);
 cube(parent,x,y+h+1,z,w+1,2,dep+1,mats.roof);
 // Shaded facade bands give each procedural building visual scale.
 if(h>35){for(let i=0;i<Math.min(12,Math.floor(h/10));i++)cube(parent,x,y+6+i*10,z+dep*.51,w*.86,.35,.25,mats.glass);}
 if(h>90)cube(parent,x,y+h+8,z,2,14,2,mats.steel);
}
function addLandmark(parent,poi){
 const terrain=heightAt(poi.x,poi.z),g=new THREE.Group();g.position.set(poi.x,terrain,poi.z);g.userData.poi=poi;
 if(poi.type==="bunker"){
  cube(g,0,4,0,26,8,21,mats.concrete);cube(g,0,8.8,0,29,2,24,mats.roof);
  cube(g,0,4,11,9,7,1,mats.steel);cube(g,0,7.4,11.5,8,1,.7,mats.red);
  cube(g,11,2,0,2,4,10,mats.dark);
 }else if(poi.type==="container"){
  cube(g,0,3.5,0,17,7,7,mats.red);cube(g,8.8,3.5,0,.6,6.5,6,mats.gold);
  for(let i=-7;i<=7;i+=3)cube(g,i,3.5,3.6,.3,6,.3,mats.steel);
 }else if(poi.type==="metro"){
  cube(g,0,3,0,19,5,16,mats.roof);
  cube(g,0,3.1,-8.1,11,5,1,mats.glass);
  cube(g,0,6.3,0,16,1.5,1,mats.blue);
 }else if(poi.type==="catacomb"){
  cube(g,-7,4,0,2,8,5,mats.rock);cube(g,7,4,0,2,8,5,mats.rock);
  cube(g,0,8,0,16,2,5,mats.concrete);cube(g,0,4,0,10,7,1,mats.steel);
 }else if(poi.type==="harbor"){
  cube(g,0,1,0,45,2,16,mats.wood);
  for(let i=-2;i<3;i++)cube(g,i*9,3,-8,1,6,1,mats.steel);
 }else if(poi.type==="hidden-village"||poi.type==="village"){
  for(let i=0;i<5;i++){const a=i*1.3,r=14;const px=Math.cos(a)*r,pz=Math.sin(a)*r;
   cube(g,px,3,pz,10,6,9,mats.wood);cube(g,px,6.7,pz,12,1.5,11,mats.roof);}
 }else if(poi.type==="island"){
  const beacon=new THREE.Mesh(new THREE.CylinderGeometry(1.6,2.5,16,8),mats.concrete);
  beacon.position.y=8;g.add(beacon);
  cube(g,0,17,0,4,2,4,mats.gold);
 }else if(poi.type==="city"){
  cube(g,0,15,0,7,30,7,mats.steel);cube(g,0,32,0,8,5,8,mats.blue);
 }
 parent.add(g);return g;
}
export const KEY_STASHES=[
 {id:"alpha-cache",name:"Cache des survivants : Clé Alpha",x:1020,z:705,item:"key_bunker_alpha"},
 {id:"container-cache",name:"Sac du contrebandier : Clé conteneur",x:900,z:890,item:"key_container"},
 {id:"zero-cache",name:"Cache sous le viaduc : Clé Zéro",x:-6300,z:3570,item:"key_bunker_zero"}
];
export const ENCOUNTER_SITES=[
 {id:"scavenge-0",name:"Caisse de ravitaillement",type:"crate",x:1045,z:740},
 {id:"scavenge-1",name:"Caisse de ravitaillement",type:"crate",x:1215,z:970},
 {id:"scavenge-2",name:"Piles de ferraille",type:"crate",x:-400,z:380}
];
function special(group,site){
 const g=new THREE.Group();g.position.set(site.x,heightAt(site.x,site.z),site.z);g.userData.site=site;
 cube(g,0,1.0,0,3.5,2,3.5,site.item?mats.gold:mats.steel);
 if(site.item){const key=new THREE.Mesh(new THREE.TorusGeometry(1,.2,6,16),mats.gold);key.position.y=3;key.rotation.x=Math.PI/2;g.add(key);}
 group.add(g);return g;
}
function bridge(group,entry){
 const ax=entry.from.x,az=entry.from.z,bx=entry.to.x,bz=entry.to.z;
 const mx=(ax+bx)/2,mz=(az+bz)/2,length=Math.hypot(bx-ax,bz-az);
 const angle=Math.atan2(bx-ax,bz-az);
 const deck=cube(group,mx,12,mz,entry.width,2,length,mats.concrete);deck.rotation.y=angle;
 for(let i=0;i<=Math.max(1,Math.round(length/130));i++){
  const t=i/Math.max(1,Math.round(length/130)),x=ax+(bx-ax)*t,z=az+(bz-az)*t;
  cube(group,x,6,z,4,12,4,mats.steel);
 }
 for(let side of [-1,1]){const rail=cube(group,mx,14,mz,1.2,1.5,length,mats.steel);
 rail.rotation.y=angle;rail.position.x+=Math.cos(angle)*entry.width*.52*side;rail.position.z-=Math.sin(angle)*entry.width*.52*side;}
}
function sampleColor(x,z,y){
 const t=biomeAt(x,z);
 const base=t==="ocean"?[.09,.22,.29]:t==="beach"?[.67,.62,.41]:t==="snow"?[.82,.85,.82]:t==="alpine"?[.48,.51,.48]:t==="forest"?[.22,.35,.23]:t==="dry"?[.48,.44,.26]:[.31,.44,.27];
 const noise=(rngAt(Math.floor(x/35),Math.floor(z/35),5)-.5)*.13;
 return base.map(v=>Math.max(0,v+noise));
}
function createGround(cx,cz){
 const divisions=16;
 const meshGeo=new THREE.PlaneGeometry(CHUNK_SIZE,CHUNK_SIZE,divisions,divisions);
 meshGeo.rotateX(-Math.PI/2);
 const a=meshGeo.attributes.position,cols=[];
 for(let i=0;i<a.count;i++){
  const x=cx+a.getX(i),z=cz+a.getZ(i),y=heightAt(x,z);
  a.setY(i,y);
  cols.push(...sampleColor(x,z,y));
 }
 meshGeo.setAttribute("color",new THREE.Float32BufferAttribute(cols,3));
 meshGeo.computeVertexNormals();
 const ground=new THREE.Mesh(meshGeo,new THREE.MeshLambertMaterial({vertexColors:true}));
 ground.position.set(cx,0,cz);ground.receiveShadow=true;return ground;
}
function createBoat(){
 const g=new THREE.Group();
 cube(g,0,-.5,0,5,2,14,mats.wood);
 cube(g,0,1.0,-3,4,2.4,4,mats.steel);cube(g,0,2.9,-3,3,1.4,3,mats.glass);
 cube(g,-2.4,.7,0,.3,2,12,mats.steel);cube(g,2.4,.7,0,.3,2,12,mats.steel);
 return g;
}
export class TerrainWorld {
 constructor(scene,radius=2){
  this.scene=scene;this.radius=radius;this.root=new THREE.Group();scene.add(this.root);
  this.chunks=new Map();this.lastKey="";this.assets=new THREE.Group();this.root.add(this.assets);
  this.ocean=new THREE.Mesh(new THREE.PlaneGeometry(WORLD_HALF_SIZE*2.08,WORLD_HALF_SIZE*2.08),
    new THREE.MeshPhongMaterial({color:0x24526b,shininess:42,transparent:true,opacity:.79,depthWrite:false}));
  this.ocean.rotation.x=-Math.PI/2;this.ocean.position.y=SEA_LEVEL-.15;this.root.add(this.ocean);
  this.boat=createBoat();this.boat.position.set(15150,1.7,450);this.root.add(this.boat);
  // Bridges are persistent world geometry, not separate levels.
  for(const b of BRIDGES)bridge(this.assets,b);
  this.placed=[];
 }
 createChunk(cx,cz){
  const mx=cx*CHUNK_SIZE,my=cz*CHUNK_SIZE,half=CHUNK_SIZE/2;
  const group=new THREE.Group();group.name="terrain "+cx+","+cz;
  group.add(createGround(mx,my));
  // Cities occupy many chunks and use deterministic lots.
  const cities=POIS.filter(p=>p.type==="city"&&Math.hypot(p.x-mx,p.z-my)<(p.r||800)+CHUNK_SIZE);
  if(cities.length){
   const grid=60;
   for(let ix=Math.floor((mx-half)/grid);ix<=Math.ceil((mx+half)/grid);ix++)
    for(let iz=Math.floor((my-half)/grid);iz<=Math.ceil((my+half)/grid);iz++){
     const x=ix*grid,z=iz*grid;
     if(x<mx-half||x>=mx+half||z<my-half||z>=my+half)continue;
     const city=cities.find(p=>Math.hypot(x-p.x,z-p.z)<p.r);
     if(!city||rngAt(ix,iz,16)<.38)continue;building(group,x,z,city,rngAt(ix,iz,13));
    }
  }else{
   for(let i=0;i<12;i++){
    const x=mx-half+rngAt(cx*101+i,cz*43,11)*CHUNK_SIZE;
    const z=my-half+rngAt(cx*73,cz*89+i,19)*CHUNK_SIZE;
    const biome=biomeAt(x,z);
    if(["forest","grassland","dry"].includes(biome)&&rngAt(cx+i,cz,33)>.28)tree(group,x,z,rngAt(x,z,25));
    else if(["alpine","snow","beach"].includes(biome))rock(group,x,z,2+rngAt(x,z,61)*5);
   }
  }
  for(const poi of POIS){if(Math.abs(poi.x-mx)<half&&Math.abs(poi.z-my)<half)addLandmark(group,poi)}
  for(const stash of [...KEY_STASHES,...ENCOUNTER_SITES]){
   if(Math.abs(stash.x-mx)<half&&Math.abs(stash.z-my)<half)special(group,stash)
  }
  return group;
 }
 update(x,z){
  const {cx,cz}=chunkCoordinates(x,z),next=cx+","+cz;
  if(next===this.lastKey)return;
  this.lastKey=next;
  const keep=new Set();
  for(let dx=-this.radius;dx<=this.radius;dx++)for(let dz=-this.radius;dz<=this.radius;dz++){
   const ix=cx+dx,iz=cz+dz,key=ix+","+iz;keep.add(key);
   if(!this.chunks.has(key)){const g=this.createChunk(ix,iz);this.chunks.set(key,g);this.root.add(g)}
  }
  for(const [key,g]of this.chunks)if(!keep.has(key)){
   this.root.remove(g);
   g.traverse(o=>{if(o.isMesh&&o.geometry!==box&&o.geometry!==cone&&o.geometry!==stone&&o.geometry!==geoTrunk)o.geometry.dispose()});
   this.chunks.delete(key);
  }
 }
 setBoat(x,z,yaw=0){this.boat.position.set(x,1.65,z);this.boat.rotation.y=yaw}
 addBuilt(o){
  const y=heightAt(o.x,o.z),g=new THREE.Group();
  g.position.set(o.x,y,o.z);
  if(o.kind==="shelter"){cube(g,0,2,0,10,4,9,mats.wood);cube(g,0,4.8,0,12,2,11,mats.roof)}
  if(o.kind==="campfire"){for(let i=0;i<6;i++){const a=i*Math.PI/3;rock(g,Math.cos(a)*2,Math.sin(a)*2,.8)}
   cube(g,0,.9,0,.9,2,.9,mats.orange);const light=new THREE.PointLight(0xff9944,4,18);light.position.y=3;g.add(light)}
  this.assets.add(g);this.placed.push(g);
 }
 setVisible(visible){this.root.visible=visible}
}
export function makeUnderground(kind="metro"){
 const root=new THREE.Group(),mat=kind==="metro"?mats.concrete:mats.rock;
 const y=-45;cube(root,0,y-1,0,42,2,320,mat);
 cube(root,-21,y+6,0,2,15,320,mat);cube(root,21,y+6,0,2,15,320,mat);
 cube(root,0,y+13,0,42,2,320,mats.roof);
 for(let z=-150;z<=150;z+=24){
  if(kind==="metro"){
   for(const x of [-9,9])cube(root,x,y+.3,z,1,.5,20,mats.steel);
   for(let dz=-10;dz<=10;dz+=5)cube(root,0,y+.1,z+dz,19,.35,1,mats.wood);
  }else for(const x of [-15,15])cube(root,x,y+1,z,7,2,6,mats.rock);
  const light=new THREE.PointLight(kind==="metro"?0xffcf94:0xff845a,2.1,30);light.position.set(0,y+10,z);root.add(light);
 }
 cube(root,0,y+3,-152,14,7,1,mats.steel);
 cube(root,0,y+2,134,10,4,1,mats.gold);
 cube(root,0,y+1,-116,5,2,5,mats.blue);
 return {root,floorY:y,exitZ:134,cacheZ:-116};
}
