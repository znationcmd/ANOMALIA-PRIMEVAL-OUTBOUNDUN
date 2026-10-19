import * as THREE from 'three';
import {BUILDING_TYPES,RP_SITES,localPoint,transformPoint} from './building-rules.js';
export function createBuildings({scene,state,heightAt,materials}){
 const models=new Map();let solids=[],floors=[],signature='';
 function build(o){
  const d=BUILDING_TYPES[o.type],root=new THREE.Group(),walls=[],ground=Math.max(...[[0,0],[-d.width/2,-d.depth/2],[d.width/2,d.depth/2],[-d.width/2,d.depth/2],[d.width/2,-d.depth/2]].map(([x,z])=>{const p=transformPoint(o,x,z);return heightAt(p.x,p.z)}),o.type==='dock'?1:0)+.25;
  root.position.set(o.x,ground,o.z);root.rotation.y=o.yaw||0;
  const wallMat=new THREE.MeshStandardMaterial({color:d.color,map:materials.concrete.map,roughness:.92}),floorMat=materials.concrete,wood=materials.wood,metal=materials.dark;
  const box=(x,y,z,w,h,depth,mat=wallMat,solid=false)=>{const mesh=new THREE.Mesh(new THREE.BoxGeometry(w,h,depth),mat);mesh.position.set(x,y,z);mesh.castShadow=true;mesh.receiveShadow=true;mesh.userData.cameraSolid=solid;mesh.userData.editorId=o.id;root.add(mesh);if(solid){const p=transformPoint(o,x,z);walls.push({x:p.x,z:p.z,width:w,depth,yaw:o.yaw||0})}return mesh};
  function sign(text,x,y,z,w=8){const c=document.createElement('canvas');c.width=1024;c.height=160;const ctx=c.getContext('2d');ctx.fillStyle='#243a37';ctx.fillRect(0,0,c.width,c.height);ctx.strokeStyle='#adb7a3';ctx.lineWidth=7;ctx.strokeRect(5,5,1014,150);ctx.fillStyle='#e8e9d7';ctx.font='bold 64px system-ui';ctx.textAlign='center';ctx.fillText(text,512,105);const tex=new THREE.CanvasTexture(c);tex.colorSpace=THREE.SRGBColorSpace;const m=new THREE.Mesh(new THREE.PlaneGeometry(w,w*.156),new THREE.MeshBasicMaterial({map:tex}));m.position.set(x,y,z);m.userData.editorId=o.id;root.add(m)}
  const bed=(x,z)=>{box(x,.6,z,2,1,3.5,metal);box(x,1.2,z,1.9,.25,3.3,wood);box(x,1.4,z-1.2,1.6,.25,.6,floorMat)};
  const desk=(x,z)=>{box(x,1.1,z,3,.15,1.4,wood);for(const dx of [-1.2,1.2])box(x+dx,.5,z,.12,1,.8,metal)};
  if(o.type==='helipad'){
   box(0,0,0,d.width,.3,d.depth,floorMat);for(const x of [-3.5,3.5])box(x,.17,0,1,.02,10,wallMat);box(0,.17,0,8,.02,1,wallMat);sign('H',0,.22,0,1);
   const ring=new THREE.Mesh(new THREE.RingGeometry(10,10.4,48),new THREE.MeshBasicMaterial({color:0xd5d4b3,side:THREE.DoubleSide}));ring.rotation.x=-Math.PI/2;ring.position.y=.18;root.add(ring);
  }else if(o.type==='dock'){
   box(0,0,0,d.width,.4,d.depth,wood);for(const x of [-8,8])for(const z of [-12,0,12])box(x,-3,z,.6,6,.6,wood);for(const x of [-9,9])box(x,.55,0,.2,1,d.depth,metal);sign('PORT · EMBARCADÈRE',0,2,d.depth/2+.1,12);
  }else if(['sandbags','barrier','container','watchtower'].includes(o.type)){
   if(o.type==='watchtower'){for(const x of [-2.5,2.5])for(const z of [-2.5,2.5])box(x,3,z,.5,6,.5,wood,true);box(0,6,0,6,.3,6,wood);box(0,8.5,0,7,.3,7,metal);box(0,6.8,-2.8,6,1.2,.3,wood,true)}
   else box(0,o.type==='container'?1.5:.65,0,d.width,o.type==='container'?3:1.3,d.depth,o.type==='sandbags'?wood:wallMat,true);
  }else{
   const w=d.width,h=4.5,depth=d.depth,door=o.type==='firestation'?8:3.5;
   box(0,-.15,0,w,.3,depth,floorMat);box(0,h,0,w+.6,.3,depth+.6,floorMat).userData.cameraSolid=true;
   // Back wall and front wall with a real, unobstructed entrance.
   box(0,h/2,-depth/2,w,h,.45,wallMat,true);
   const wing=(w-door)/2;for(const x of [-1,1])box(x*(door/2+wing/2),h/2,depth/2,wing,h,.45,wallMat,true);
   box(0,3.8,depth/2,door,1.4,.45,wallMat);sign(d.label.toUpperCase(),0,3.7,depth/2+.24,Math.min(15,w*.7));
   // Side windows have open geometry and usable firing positions.
   for(const x of [-w/2,w/2]){box(x,.55,0,.45,1.1,depth,wallMat,true);box(x,3.9,0,.45,1.2,depth,wallMat);for(const z of [-depth/2,0,depth/2])box(x,2.2,z,.45,2.4,1.1,wallMat,true)}
   // Interior side rooms leave a central corridor and door gaps.
   for(const x of [-w*.22,w*.22]){box(x,2.2,-depth*.15,.3,4.2,depth*.53,wallMat,true);box(x,2.2,depth*.38,.3,4.2,depth*.17,wallMat,true)}
   if(o.type==='hospital'){for(const x of [-w*.36,w*.36])for(const z of [-depth*.3,0,depth*.25])bed(x,z);desk(0,-depth*.3);sign('URGENCES',0,2.9,depth/2+.27,5)}
   else if(o.type==='barracks'){for(const x of [-w*.36,w*.36])for(const z of [-depth*.3,0,depth*.3]){bed(x,z);box(x,2.7,z,2,.2,3.5,wood)}desk(0,0)}
   else if(o.type==='police'||o.type==='gendarmerie'){desk(-w*.36,depth*.2);desk(w*.36,depth*.2);for(let x=w*.25;x<w*.43;x+=.6)box(x,2.1,-depth*.15,.08,4,.08,metal,true);box(w*.34,2.1,-depth*.15,w*.2,.1,.1,metal);bed(w*.35,-depth*.3);sign('ACCUEIL',0,2.3,-depth*.4,4)}
   else if(o.type==='firestation'){for(const x of [-w*.36,w*.36])box(x,1.8,-depth*.3,2.2,3.6,2,metal,true);desk(0,-depth*.32);for(const x of [-5,5])box(x,.03,0,.1,.02,depth*.9,wallMat)}
   else if(o.type==='armory'){desk(0,depth*.28);for(const x of [-w*.37,w*.37])for(let z=-depth*.35;z<=0;z+=2){box(x,1.5,z,2,.15,1,metal);box(x,2.2,z,.12,1.2,.18,wood)}}
   else if(o.type==='shop'){desk(0,depth*.25);for(const x of [-w*.36,w*.36])for(const y of [.6,1.5,2.4]){box(x,y,-depth*.15,2,.12,depth*.6,wood);for(let z=-depth*.35;z<depth*.1;z+=2)box(x,y+.3,z,.6,.55,.6,wallMat)}}
   else{bed(-w*.35,-depth*.25);desk(w*.32,0);box(0,.6,depth*.05,2.5,1,1.8,wood)}
   // Low-cost ceiling lighting makes the interior navigable.
   const light=new THREE.PointLight(0xdde5cd,12,Math.max(w,depth),2);light.position.set(0,3.7,0);root.add(light);
  }
  scene.add(root);
  return {root,walls,floor:{...o,y:ground,width:d.width,depth:d.depth},dispose(){const mats=new Set();root.traverse(m=>{m.geometry?.dispose();if(m.material&&!Object.values(materials).includes(m.material))mats.add(m.material)});for(const m of mats){if(m.map&&!Object.values(materials).some(v=>v?.map===m.map))m.map.dispose();m.dispose()}root.removeFromParent()}};
 }
 function update(){const entries=[...RP_SITES,...(state.editorObjects||[])];const next=JSON.stringify(entries);if(signature===next)return;signature=next;for(const model of models.values())model.dispose();models.clear();solids=[];floors=[];for(const o of entries){if(!BUILDING_TYPES[o.type])continue;const model=build(o);models.set(o.id,model);solids.push(...model.walls);if(!['sandbags','barrier','container','watchtower'].includes(o.type))floors.push(model.floor)}}
 function floorAt(x,z){let y=null;for(const floor of floors){const p=localPoint(floor,x,z);if(Math.abs(p.x)<=floor.width/2&&Math.abs(p.z)<=floor.depth/2)y=y===null?floor.y:Math.max(y,floor.y)}return y}
 update();return {update,solids:()=>solids,floorAt,objects:()=>[...RP_SITES,...(state.editorObjects||[])],roots:()=>[...models.values()].map(m=>m.root)};
}
