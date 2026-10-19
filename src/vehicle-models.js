import * as THREE from 'three';
export function vehicleModel(type,wreck=false){
 const root=new THREE.Group(),moving=[];
 const paint=new THREE.MeshStandardMaterial({color:wreck?0x514238:type==='tank'?0x4a5540:0x546b65,roughness:.82,metalness:.18});
 const rubber=new THREE.MeshStandardMaterial({color:0x1c211e,roughness:1}),metal=new THREE.MeshStandardMaterial({color:0x59615c,roughness:.6,metalness:.6}),glass=new THREE.MeshStandardMaterial({color:0x8cb9c2,transparent:true,opacity:.19,roughness:.2,metalness:.15,depthWrite:false});
 const lamp=new THREE.MeshStandardMaterial({color:0xd8caa2,emissive:0x665b36,emissiveIntensity:.3});
 const part=(geo,x,y,z,mat)=>{const m=new THREE.Mesh(geo,mat);m.position.set(x,y,z);m.castShadow=!wreck;m.receiveShadow=true;root.add(m);return m};
 const box=(x,y,z,w,h,d,mat=paint)=>part(new THREE.BoxGeometry(w,h,d),x,y,z,mat);
 const wheel=(x,y,z,r=.4)=>{const o=part(new THREE.CylinderGeometry(r,r,.25,16),x,y,z,rubber);o.rotation.z=Math.PI/2;moving.push({mesh:o,kind:'wheel'});part(new THREE.CylinderGeometry(r*.5,r*.5,.27,12),x,y,z,metal).rotation.z=Math.PI/2};
 const cabin=(y=1)=>{
  for(const x of [-.85,.85])for(const z of [-1,1])box(x,y+.55,z,.08,1.1,.09,metal);
  box(0,y+1.1,0,1.85,.12,2.2);box(0,y+.55,-1.02,1.65,.9,.025,glass);box(0,y+.55,1.02,1.65,.9,.025,glass);
  for(const x of [-.86,.86])box(x,y+.5,0,.025,.85,1.9,glass);
  box(0,y-.1,-.65,1.7,.3,.55,rubber);for(const x of [-.45,.45]){box(x,y-.1,.1,.55,.14,.65,rubber);box(x,y+.2,.4,.55,.6,.13,rubber)}
  const steering=part(new THREE.TorusGeometry(.20,.025,6,24),-.43,y+.28,-.37,rubber);steering.rotation.x=-.35;moving.push({mesh:steering,kind:'steering'});
  const canvas=document.createElement('canvas');canvas.width=256;canvas.height=96;const c=canvas.getContext('2d');c.fillStyle='#121b1d';c.fillRect(0,0,256,96);c.strokeStyle='#a6bfb1';c.fillStyle='#c5d9be';c.lineWidth=3;
  for(const x of [65,180]){c.beginPath();c.arc(x,48,35,0,Math.PI*2);c.stroke();c.beginPath();c.moveTo(x,48);c.lineTo(x+18,24);c.stroke()}c.font='12px monospace';c.fillText('KM/H',45,75);c.fillText('FUEL',164,75);
  const tex=new THREE.CanvasTexture(canvas);tex.colorSpace=THREE.SRGBColorSpace;const material=new THREE.MeshBasicMaterial({map:tex});const panel=part(new THREE.PlaneGeometry(.65,.24),-.25,y+.15,-.43,material);panel.rotation.x=-.35;
 };
 if(type==='trainwreck'){
  box(0,1.7,0,3,2.4,8);box(0,3,-2,2.8,1.7,2.6);box(0,3,-3.32,2.2,.8,.03,glass);
  for(const x of [-1.45,1.45])for(const z of [-2.8,-1,1,2.8])wheel(x,.55,z,.5);
  for(let n=1;n<3;n++){const z=n*9;box(n*.5,1.4,z,3,1.6,7);for(const side of [-1.45,1.45])for(const dz of [-2.5,2.5])wheel(n*.5+side,.5,z+dz,.45);box(n*.5,2.4,z,3.1,.2,7.2);}
 }else if(type==='motorcycle'){
  wheel(0,.38,-.8,.37);wheel(0,.38,.8,.37);box(0,.7,0,.38,.45,1.2);box(0,1,.25,.5,.16,.7,rubber);box(0,1.2,-.6,.9,.07,.06,metal);box(0,.88,-.87,.35,.32,.13,lamp);
 }else if(type==='tank'){
  box(0,1,0,3.3,1.2,5.8);for(const x of [-1.55,1.55]){box(x,.6,0,.65,1.1,5.4,rubber);for(let z=-2;z<=2;z+=.7)wheel(x,.6,z,.44)}
  box(0,1.95,-.3,2.2,.75,2.8);const barrel=part(new THREE.CylinderGeometry(.10,.13,3.8,12),0,2.02,-3,metal);barrel.rotation.x=Math.PI/2;box(0,2.5,.1,1.3,.18,1.4);cabin(1.5);
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
  const truck=type==='truck';box(0,.65,truck?1:0,truck?2.5:1.9,.65,truck?6.8:4.4);cabin(1);
  for(const x of [truck?-1.25:-1,truck?1.25:1])for(const z of [truck?-1.2:-1.4,truck?3:1.4])wheel(x,.45,z,truck?.55:.42);
  if(truck){box(0,1.25,2.6,2.5,.15,3.4);for(const x of [-1.22,1.22])box(x,1.8,2.6,.12,1.1,3.5)}
  for(const x of [-.65,.65])box(x,.8,-2.23,.35,.22,.08,lamp);
  box(0,.43,-2.3,1.8,.18,.2,rubber);
 }
 if(wreck){root.rotation.z=.25;root.rotation.x=.12;}
 return {root,setCockpit(inside){root.traverse(o=>{if(o.userData.hideInCockpit)o.visible=!inside})},update(speed,turn,time){for(const p of moving){if(p.kind==='rotor')p.mesh.rotation.y=time*25;else if(p.kind==='propeller')p.mesh.rotation.z=time*35;else if(p.kind==='wheel')p.mesh.rotation.x+=speed*.02;else if(p.kind==='steering')p.mesh.rotation.z=turn*.4}},dispose(){const materials=new Set();root.traverse(o=>{o.geometry?.dispose();if(o.material)materials.add(o.material)});for(const m of materials){m.map?.dispose();m.dispose()}}};
}
