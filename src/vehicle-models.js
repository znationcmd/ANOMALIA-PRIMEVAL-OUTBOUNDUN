import {loadSedan} from "./sedan.js";
import * as THREE from 'three';
export function vehicleModel(type,wreck=false){
 const root=new THREE.Group(),moving=[];let detailed=null,disposed=false,cockpit=false;
 const paint=new THREE.MeshStandardMaterial({color:wreck?0x514238:type==='tank'?0x4a5540:0x546b65,roughness:.82,metalness:.18});
 const rubber=new THREE.MeshStandardMaterial({color:0x1c211e,roughness:1}),metal=new THREE.MeshStandardMaterial({color:0x59615c,roughness:.6,metalness:.6}),glass=new THREE.MeshStandardMaterial({color:0x8cb9c2,transparent:true,opacity:.19,roughness:.2,metalness:.15,depthWrite:false});
 const lamp=new THREE.MeshStandardMaterial({color:0xd8caa2,emissive:0x665b36,emissiveIntensity:.3});
 const part=(geo,x,y,z,mat)=>{const m=new THREE.Mesh(geo,mat);m.position.set(x,y,z);m.castShadow=!wreck;m.receiveShadow=true;root.add(m);return m};
 const box=(x,y,z,w,h,d,mat=paint)=>part(new THREE.BoxGeometry(w,h,d),x,y,z,mat);
 const wheel=(x,y,z,r=.4)=>{const o=part(new THREE.CylinderGeometry(r,r,.25,16),x,y,z,rubber);o.rotation.z=Math.PI/2;moving.push({mesh:o,kind:'wheel'});part(new THREE.CylinderGeometry(r*.5,r*.5,.27,12),x,y,z,metal).rotation.z=Math.PI/2};
 const cabin=(y=1)=>{
  const first=root.children.length;
  for(const x of [-.85,.85])for(const z of [-1,1])box(x,y+.55,z,.08,1.1,.09,metal);
  box(0,y+1.1,0,1.85,.12,2.2);box(0,y+.55,-1.02,1.65,.9,.025,glass);box(0,y+.55,1.02,1.65,.9,.025,glass);
  for(const x of [-.86,.86])box(x,y+.5,0,.025,.85,1.9,glass);
  box(0,y-.1,-.65,1.7,.3,.55,rubber);for(const x of [-.45,.45]){box(x,y-.1,.1,.55,.14,.65,rubber);box(x,y+.2,.4,.55,.6,.13,rubber)}
  const steering=part(new THREE.TorusGeometry(.20,.025,6,24),-.43,y+.28,-.37,rubber);steering.rotation.x=-.35;moving.push({mesh:steering,kind:'steering'});
  const canvas=document.createElement('canvas');canvas.width=256;canvas.height=96;const c=canvas.getContext('2d');c.fillStyle='#121b1d';c.fillRect(0,0,256,96);c.strokeStyle='#a6bfb1';c.fillStyle='#c5d9be';c.lineWidth=3;
  for(const x of [65,180]){c.beginPath();c.arc(x,48,35,0,Math.PI*2);c.stroke();c.beginPath();c.moveTo(x,48);c.lineTo(x+18,24);c.stroke()}c.font='12px monospace';c.fillText('KM/H',45,75);c.fillText('FUEL',164,75);
  const tex=new THREE.CanvasTexture(canvas);tex.colorSpace=THREE.SRGBColorSpace;const material=new THREE.MeshBasicMaterial({map:tex});const panel=part(new THREE.PlaneGeometry(.65,.24),-.25,y+.15,-.43,material);panel.rotation.x=-.35;for(const child of root.children.slice(first))child.userData.cockpitOnly=true;
 };
 if(type==='trainwreck'){
  box(0,1.7,0,3,2.4,8);box(0,3,-2,2.8,1.7,2.6);box(0,3,-3.32,2.2,.8,.03,glass);
  for(const x of [-1.45,1.45])for(const z of [-2.8,-1,1,2.8])wheel(x,.55,z,.5);
  for(let n=1;n<3;n++){const z=n*9;box(n*.5,1.4,z,3,1.6,7);for(const side of [-1.45,1.45])for(const dz of [-2.5,2.5])wheel(n*.5+side,.5,z+dz,.45);box(n*.5,2.4,z,3.1,.2,7.2);}
 }else if(['quad','buggy','snowmobile','dirt_bike','kart','formula1','monster_truck'].includes(type)){
  const bike=type==='dirt_bike',snow=type==='snowmobile',monster=type==='monster_truck',formula=type==='formula1',kart=type==='kart';
  const len=monster?6:formula?5.2:snow?3.1:bike?2.2:kart?1.8:3.2,w=monster?3.7:formula?2.0:bike?.8:kart?1.2:1.8;
  const y=monster?2.8:formula?.45:snow?.55:.8;
  box(0,y,0,w*.85,monster?1.5:.45,len*.8,paint);
  if(!bike&&!snow&&!kart){box(0,y+.55,monster?.2:.4,w*.62,.65,len*.3,glass);}
  if(formula){box(0,.6,-2.1,3.2,.12,.5,metal);box(0,.9,2.0,2.6,.15,.4,metal);}
  if(snow){for(const x of [-.6,.6])box(x,.15,-.7,.15,.15,2.8,metal);box(0,.2,.8,1,.35,1.1,rubber);}
  else for(const x of [-w*.5,w*.5])for(const z of [-len*.35,len*.35])wheel(x,monster?1.15:.35,z,monster?1.1:formula?.37:bike?.37:kart?.25:.48);
  if(bike){box(0,1,0,.45,.2,.75,rubber);box(0,1.2,-.7,.8,.1,.1,metal);}
  if(kart){box(0,.55,.1,.6,.15,.6,rubber);box(0,.8,-.3,.6,.1,.1,metal);}
 }else if(['jetski','zodiac'].includes(type)){
  const zodiac=type==='zodiac',len=zodiac?5.2:3,w=zodiac?2.4:1.25;
  const hull=part(new THREE.CapsuleGeometry(w*.42,len*.5,6,12),0,.15,0,paint);hull.rotation.x=Math.PI/2;
  box(0,.5,0,w*.7,.15,len*.65,metal);box(0,.9,0,w*.35,.7,.8,glass);
  if(zodiac)for(const x of [-w*.5,w*.5])box(x,.4,0,.3,.4,len*.75,rubber);
 }else if(['fighter_jet'].includes(type)){
  const fuselage=part(new THREE.CylinderGeometry(.7,.55,12,16),0,1.6,0,metal);fuselage.rotation.x=Math.PI/2;
  box(0,1.5,1,9,.15,3.4,paint);box(0,2.1,4.5,3,.2,2,metal);box(0,2.7,4.8,.2,2,1.5,metal);
  box(0,2.1,-2,1.1,.65,2.3,glass);
 }else if(['attack_helicopter','transport_helicopter'].includes(type)){
  const transport=type==='transport_helicopter',length=transport?12:8,width=transport?3.4:2.2;
  const fuselage=part(new THREE.CapsuleGeometry(width*.5,length*.45,8,16),0,2,0,paint);fuselage.rotation.x=Math.PI/2;
  box(0,2.8,-length*.25,width*.65,1.1,2,glass);box(0,2.3,length*.6,.5,.6,5,metal);
  for(const x of [-width*.5,width*.5])box(x,.3,0,.12,.12,length*.75,metal);
  if(!transport)for(const x of [-2.2,2.2])box(x,1.9,0,1.7,.2,2.6,metal);
  const rotor=new THREE.Group();root.add(rotor);rotor.position.y=4;
  for(const a of [0,Math.PI/2]){const blade=new THREE.Mesh(new THREE.BoxGeometry(transport?18:14,.08,.28),rubber);blade.rotation.y=a;rotor.add(blade)}
  moving.push({mesh:rotor,kind:'rotor'});
 }else if(type==='motorcycle'){
  wheel(0,.38,-.8,.37);wheel(0,.38,.8,.37);box(0,.7,0,.38,.45,1.2);box(0,1,.25,.5,.16,.7,rubber);box(0,1.2,-.6,.9,.07,.06,metal);box(0,.88,-.87,.35,.32,.13,lamp);
 }else if(type==='tank'){
  box(0,1,0,3.3,1.2,5.8);for(const x of [-1.55,1.55]){box(x,.6,0,.65,1.1,5.4,rubber);for(let z=-2;z<=2;z+=.7)wheel(x,.6,z,.44)}
  box(0,1.95,-.3,2.2,.75,2.8);const barrel=part(new THREE.CylinderGeometry(.10,.13,3.8,12),0,2.02,-3,metal);barrel.rotation.x=Math.PI/2;box(0,2.5,.1,1.3,.18,1.4);cabin(1.5);
 }else if(type==='carrier'){
  box(0,2,0,20,3,82,metal);box(0,3.7,0,18,.5,78,paint);box(6,6,8,5,5,14,paint);box(6,9,8,2.2,2,5,glass);box(-7,4,-12,.4,1,28,metal);
  for(let z=-30;z<=28;z+=12)box(0,4.05,z,1,.06,7,new THREE.MeshBasicMaterial({color:0xd8d4b8}));
  cabin(5.2);
 }else if(type==='warship'){
  const hull=part(new THREE.CylinderGeometry(5,3.5,38,8),0,1,0,paint);hull.rotation.x=Math.PI/2;hull.scale.z=.45;
  box(0,3,1,8,.8,30,metal);box(0,6,5,5,5,10,paint);box(0,9,5,3,2,4,glass);box(0,8,11,.4,8,.4,metal);
  for(const z of [-11,14]){const turret=part(new THREE.CylinderGeometry(2,2.4,1.2,16),0,4,z,metal);const gun=part(new THREE.CylinderGeometry(.18,.22,7,12),0,4,z-4,metal);gun.rotation.x=Math.PI/2;}
  cabin(4.5);
 }else if(type==='submarine'){
  const hull=part(new THREE.CapsuleGeometry(3,24,12,20),0,0,0,paint);hull.rotation.x=Math.PI/2;hull.scale.z=1.15;
  box(0,3,1,2.8,3,7,metal);box(0,6,1,.45,5,.45,metal);box(0,7,-.3,2.5,.25,.25,metal);box(0,0,13,9,.25,2,metal);box(0,0,-12,7,.18,3,metal);
  cabin(2.2);
 }else if(type==='boat'){
  const hull=part(new THREE.CylinderGeometry(1.25,.8,5.7,8),0,.1,0,paint);hull.rotation.x=Math.PI/2;hull.scale.z=.5;
  box(0,.5,0,2.1,.2,4.4);cabin(1.1);box(0,.9,2.5,.5,.7,.4,rubber);
 }else if(type==='helicopter'){
  const body=part(new THREE.SphereGeometry(1,20,14),0,1.2,.5,paint);body.scale.set(1.05,.9,1.7);body.userData.hideInCockpit=true;cabin(.8);
  const tail=part(new THREE.ConeGeometry(.6,5,12),0,1.1,3.9,paint);tail.rotation.x=Math.PI/2;
  box(0,1.6,6,.12,1.8,1.2);for(const x of [-1,1]){box(x,.12,0,.12,.12,4,metal);for(const z of [-.8,.8])box(x,.45,z,.08,.7,.08,metal)}
  const rotor=new THREE.Group();root.add(rotor);rotor.position.y=2.6;for(const a of [0,Math.PI/2]){const blade=new THREE.Mesh(new THREE.BoxGeometry(11,.06,.22),rubber);blade.rotation.y=a;rotor.add(blade)}moving.push({mesh:rotor,kind:'rotor'});
 }else if(type==='airplane'){
  const fuselage=part(new THREE.CylinderGeometry(.65,.55,7.5,18),0,1.15,0,paint);fuselage.rotation.x=Math.PI/2;fuselage.userData.hideInCockpit=true;cabin(.75);
  box(0,1.15,.3,10,.16,1.8);box(0,1.6,3.2,3.8,.1,1);box(0,2.15,3.2,.13,1.6,1.2);
  for(const x of [-1.2,1.2])wheel(x,.35,.5,.3);wheel(0,.35,-2.5,.25);
  const prop=box(0,1.15,-3.85,.12,3,.12,rubber);moving.push({mesh:prop,kind:'propeller'});
 }else{
  const heavy=['truck','transport_truck','heavy_truck','firetruck','armored_van','van','ambulance'].includes(type);
  const suv=['suv','police','gendarmerie'].includes(type);
  const long=type==='heavy_truck'?16:type==='transport_truck'?9:type==='firetruck'?9:type==='ambulance'?6:type==='van'||type==='armored_van'?6:heavy?7.5:suv?5:4.4;
  const wide=heavy?2.6:suv?2.2:1.9;
  box(0,.75,heavy?1:0,wide,.7,long*.82,paint);cabin(1);
  if(heavy){box(0,2.3,2.1,wide,2.2,long*.4,metal);if(type==='heavy_truck')box(0,2.3,7,2.9,2.8,7,paint);}
  if(suv)box(0,1.8,.35,wide*.95,1.1,long*.52,glass);
  if(['police','gendarmerie','firetruck','ambulance'].includes(type)){
   const red=new THREE.MeshStandardMaterial({color:0xd22b32,emissive:0x550005});
   const blue=new THREE.MeshStandardMaterial({color:0x245ee0,emissive:0x001266});
   box(-.42,2.8,-.3,.7,.22,.35,red);box(.42,2.8,-.3,.7,.22,.35,blue);
  }
  for(const x of [-(wide/2),wide/2])for(const z of heavy?[-long*.3,long*.3]:[-long*.3,long*.3])wheel(x,.45,z,heavy?.55:.42);
  if(heavy){box(0,1.25,2.6,wide,.15,3.4);for(const x of [-wide*.48,wide*.48])box(x,1.8,2.6,.12,1.1,3.5)}
  for(const x of [-.65,.65])box(x,.8,-2.23,.35,.22,.08,lamp);
  box(0,.43,-2.3,1.8,.18,.2,rubber);
 }
 if(type==='car')loadSedan().then(source=>{if(disposed)return;detailed=source.clone(true);detailed.rotation.y=Math.PI;const bounds=new THREE.Box3().setFromObject(detailed);detailed.position.y-=bounds.min.y;detailed.traverse(o=>{if(o.userData.wheel)moving.push({mesh:o,kind:'wheel'});if(o.isMesh){o.geometry=o.geometry.clone();o.material=o.material.clone();o.castShadow=!wreck;o.receiveShadow=true;o.userData.cameraSolid=false;}});detailed.userData.asset='sedan-cc0';detailed.visible=!cockpit;root.add(detailed);for(const child of root.children)if(child!==detailed)child.visible=!!child.userData.cockpitOnly&&cockpit;}).catch(e=>console.warn('Sedan model unavailable',e.message));
 if(wreck){root.rotation.z=.25;root.rotation.x=.12;}
 return {root,setCockpit(inside){cockpit=inside;if(detailed){detailed.visible=!inside;for(const child of root.children)if(child!==detailed)child.visible=!!child.userData.cockpitOnly&&inside;}root.traverse(o=>{if(o.userData.hideInCockpit)o.visible=!inside})},update(speed,turn,time){for(const p of moving){if(p.kind==='rotor')p.mesh.rotation.y=time*25;else if(p.kind==='propeller')p.mesh.rotation.z=time*35;else if(p.kind==='wheel')p.mesh.rotation.x+=speed*.02;else if(p.kind==='steering')p.mesh.rotation.z=turn*.4}},dispose(){disposed=true;const materials=new Set();root.traverse(o=>{o.geometry?.dispose();if(o.material)materials.add(o.material)});for(const m of materials){m.map?.dispose();m.dispose()}}};
}
