import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { clone as cloneSkeleton } from 'three/addons/utils/SkeletonUtils.js';
const linkedModels=new Map();

const mats = {
  wall:new THREE.MeshStandardMaterial({color:'#b5b9be',roughness:.9}),
  roof:new THREE.MeshStandardMaterial({color:'#51474b',roughness:.88}),
  window:new THREE.MeshStandardMaterial({color:'#4d94ba',metalness:.25,roughness:.2}),
  wood:new THREE.MeshStandardMaterial({color:'#795338',roughness:.8}),
  trunk:new THREE.MeshStandardMaterial({color:'#58452e'}),
  leaf:new THREE.MeshStandardMaterial({color:'#3a7544',roughness:1}),
  pine:new THREE.MeshStandardMaterial({color:'#1b5949',roughness:1}),
  stone:new THREE.MeshStandardMaterial({color:'#7d7975',roughness:1}),
  asphalt:new THREE.MeshStandardMaterial({color:'#31343b',roughness:1}),
  white:new THREE.MeshStandardMaterial({color:'#e0d9bc'}),
  blue:new THREE.MeshStandardMaterial({color:'#445a78',metalness:.3,roughness:.45}),
  rubber:new THREE.MeshStandardMaterial({color:'#202025',roughness:1}),
  steel:new THREE.MeshStandardMaterial({color:'#8b929c',metalness:.7,roughness:.35}),
  brick:new THREE.MeshStandardMaterial({color:'#995c4b',roughness:.95})
};
const box = (x,y,z,material) => new THREE.Mesh(new THREE.BoxGeometry(x,y,z),material);
function add(group,mesh,x=0,y=0,z=0,rx=0,ry=0,rz=0) {
  mesh.position.set(x,y,z); mesh.rotation.set(rx,ry,rz);
  mesh.castShadow=true;mesh.receiveShadow=true;group.add(mesh);return mesh;
}
function wheel(group,x,z) {
  const cylinder=new THREE.Mesh(new THREE.CylinderGeometry(.48,.48,.3,12),mats.rubber);
  cylinder.rotation.z=Math.PI/2;add(group,cylinder,x,.48,z);
}
function house(group,villa=false) {
  const size=villa?1.6:1;
  add(group,box(6*size,3.6,5*size,mats.wall),0,1.8,0);
  const roof=add(group,new THREE.Mesh(new THREE.ConeGeometry(5.5*size,2,4),mats.roof),0,4.5,0);
  roof.rotation.y=Math.PI/4;
  add(group,box(1.2,2,.12,mats.wood),0,1,-2.55*size);
  for(const x of [-1.8,1.8]) add(group,box(1,1.1,.1,mats.window),x,2.2,-2.55*size);
  if(villa){add(group,box(3,.3,4,mats.window),5,.25,1.5);add(group,box(2,.2,6,mats.white),0,0,-5);}
}
function tree(group,pine=false,bush=false) {
  if(!bush)add(group,new THREE.Mesh(new THREE.CylinderGeometry(.23,.33,3.2,10),mats.trunk),0,1.6,0);
  if(pine){
    for(let j=0;j<3;j++)add(group,new THREE.Mesh(new THREE.ConeGeometry(2.3-j*.42,3,8),mats.pine),0,3.2+j*1.1,0);
  } else {
    add(group,new THREE.Mesh(new THREE.IcosahedronGeometry(bush?1.6:2.2,1),mats.leaf),0,bush?1.2:4.3,0);
    if(!bush)add(group,new THREE.Mesh(new THREE.IcosahedronGeometry(1.2,1),mats.leaf),1.1,4.6,.5);
  }
}
function car(group,truck=false) {
  const length=truck?9:4.6;
  add(group,box(2.15,.95,length,mats.blue),0,1.08,0);
  add(group,box(2,1.05,truck?2.7:2.7,mats.window),0,1.94,truck?2.3:.2);
  if(truck)add(group,box(2.1,2.2,4.8,mats.steel),0,2,-2);
  for(const z of [-(length/2-.8),length/2-.8])
    for(const x of [-1.05,1.05])wheel(group,x,z);
}
function building(group,type) {
  if(type==='house'||type==='villa')house(group,type==='villa');
  if(type==='apartment'){
    add(group,box(9,16,7,mats.brick),0,8,0);
    for(let y=2.3;y<16;y+=3)for(let x=-3.1;x<=3.1;x+=2.05)
      add(group,box(1.15,1.65,.1,mats.window),x,y,-3.54);
  }
  if(type==='warehouse'){
    add(group,box(15,7,11,mats.wall),0,3.5,0);
    add(group,box(15.4,.45,11.6,mats.roof),0,7.1,0);
    for(const x of [-4,3.5])add(group,box(3.6,4,.1,mats.steel),x,2,-5.57);
  }
  if(type==='tower'){
    add(group,new THREE.Mesh(new THREE.CylinderGeometry(.75,1.3,12,10),mats.stone),0,6,0);
    add(group,box(4,1.4,4,mats.stone),0,12,0);
  }
  if(type==='wall')add(group,box(8,3,.45,mats.stone),0,1.5,0);
  if(type==='road'){
    add(group,box(9,.09,18,mats.asphalt),0,.05,0);
    for(let z=-7;z<=7;z+=4)add(group,box(.15,.01,2,mats.white),0,.11,z);
  }
  if(type==='fence'){
    for(let x=-4;x<=4;x+=2){add(group,box(.16,2.4,.16,mats.steel),x,1.2,0);}
    for(let y of [.7,1.7])add(group,box(8,.1,.15,mats.steel),0,y,0);
  }
  if(type==='pine'||type==='tree'||type==='bush')tree(group,type==='pine',type==='bush');
  if(type==='rock'){
    const mesh=new THREE.Mesh(new THREE.DodecahedronGeometry(1.6,0),mats.stone);
    mesh.scale.set(1.6,.85,1);add(group,mesh,0,1,0);
  }
  if(type==='car'||type==='truck')car(group,type==='truck');
  if(type==='boat'){
    add(group,box(3,.8,8,mats.blue),0,.7,0);
    add(group,box(2,1.6,2,mats.white),0,1.9,-1.1);
    add(group,new THREE.Mesh(new THREE.CylinderGeometry(.08,.08,3,8),mats.steel),0,3.3,0);
  }
  if(type==='helicopter'){
    add(group,new THREE.Mesh(new THREE.SphereGeometry(1.65,14,10),mats.blue),0,2,0);
    add(group,box(.4,.4,6,mats.blue),0,2,3);
    add(group,box(10,.12,.2,mats.rubber),0,3.85,0);
    for(let x of [-1,1])add(group,box(.12,.12,3.2,mats.steel),x,.5,0);
  }
  if(type==='table'){
    add(group,box(2,.18,1.1,mats.wood),0,1.1,0);
    for(let x of [-.8,.8])for(let z of [-.4,.4])add(group,box(.11,1,.11,mats.wood),x,.5,z);
  }
  if(type==='crate')add(group,box(1.2,1.2,1.2,mats.wood),0,.6,0);
  if(type==='barrel')add(group,new THREE.Mesh(new THREE.CylinderGeometry(.55,.55,1.3,12),mats.blue),0,.65,0);
  if(type==='streetlight'){
    add(group,new THREE.Mesh(new THREE.CylinderGeometry(.09,.14,6,8),mats.steel),0,3,0);
    add(group,box(1.7,.15,.12,mats.steel),.8,6,0);
    add(group,box(.65,.12,.45,mats.white),1.45,5.85,0);
  }
}
function decodeBase64(base64) {
  const binary=atob(base64);
  const bytes=new Uint8Array(binary.length);
  for(let i=0;i<binary.length;i++)bytes[i]=binary.charCodeAt(i);
  return bytes.buffer;
}
export async function createEditorMesh(item) {
  const group=new THREE.Group();
  group.userData.editorId=item.id;group.name=item.name;
  if(item.preset==='linked-glb'){
    const api=window.anomaliaDesktop?.gameLibrary;
    if(!api)throw new Error('Ressource liée disponible uniquement dans ANOMALIA Editor Windows.');
    let loaded=linkedModels.get(item.asset.libraryId);
    if(!loaded){
      const payload=await api.read(item.asset.libraryId);
      if(payload.kind!=='glb')throw new Error('Ce fichier lié n’est plus un GLB valide.');
      const data=decodeBase64(payload.data);
      const gltf=await new GLTFLoader().parseAsync(data,'');
      loaded=gltf.scene;
      linkedModels.set(item.asset.libraryId,loaded);
      if(linkedModels.size>16)linkedModels.delete(linkedModels.keys().next().value);
    }
    const copy=cloneSkeleton(loaded);
    group.add(copy);
    copy.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});
  } else if(item.preset==='custom-glb'){
    try {
      const data=decodeBase64(item.asset.data);
      const gltf=await new GLTFLoader().parseAsync(data,'');
      group.add(gltf.scene);
      gltf.scene.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});
    } catch(e){throw new Error('GLB impossible à ouvrir : '+e.message);}
  } else building(group,item.preset);
  group.position.set(item.position.x,item.position.y,item.position.z);
  group.rotation.set(...['x','y','z'].map(k=>THREE.MathUtils.degToRad(item.rotation[k])));
  group.scale.set(item.scale.x,item.scale.y,item.scale.z);
  group.visible=item.visible!==false;
  return group;
}
