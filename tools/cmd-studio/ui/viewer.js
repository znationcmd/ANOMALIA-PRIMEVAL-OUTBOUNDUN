'use strict';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

// Genuine local GLB and texture viewer: this does not create fake 3D assets.
const mount=document.getElementById('modelViewport');
const fallback=document.getElementById('previewFallback');
let renderer=null,scene=null,camera=null,controls=null,display=null,mixer=null,clock=null;
let ground=null,grid=null,originalRadius=3,materialTexture=null;
let currentRequest=0;
function bootstrap(){
  if(renderer)return;
  try {
    renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,powerPreference:'default'});
  }catch(e){throw new Error('WebGL indisponible sur cet ordinateur : '+e.message);}
  renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,1.8));
  renderer.outputColorSpace=THREE.SRGBColorSpace;
  renderer.toneMapping=THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure=1.1;
  renderer.shadowMap.enabled=true;
  renderer.shadowMap.type=THREE.PCFSoftShadowMap;
  renderer.domElement.setAttribute('aria-label','Prévisualisation 3D interactive du fichier local');
  mount.append(renderer.domElement);
  scene=new THREE.Scene();
  scene.background=new THREE.Color('#1c3047');
  scene.fog=new THREE.Fog('#1c3047',35,100);
  camera=new THREE.PerspectiveCamera(40,1,.015,300);
  camera.position.set(4,3,5.5);
  controls=new OrbitControls(camera,renderer.domElement);
  controls.enableDamping=true;
  controls.dampingFactor=.07;
  controls.minDistance=.5;
  controls.maxDistance=55;
  const pmrem=new THREE.PMREMGenerator(renderer);
  const env=pmrem.fromScene(new RoomEnvironment(),.04);
  scene.environment=env.texture;
  scene.add(new THREE.HemisphereLight('#e0eeff','#435268',2.2));
  const key=new THREE.DirectionalLight('#fff0db',3.2);
  key.position.set(-5,9,7);
  key.castShadow=true;
  key.shadow.mapSize.set(1024,1024);
  key.shadow.camera.near=.3;
  key.shadow.camera.far=50;
  key.shadow.camera.left=-12;key.shadow.camera.right=12;
  key.shadow.camera.top=12;key.shadow.camera.bottom=-12;
  key.shadow.bias=-.00015;
  scene.add(key);
  const fill=new THREE.DirectionalLight('#a3bdff',1.6);
  fill.position.set(5,4,-6);scene.add(fill);
  ground=new THREE.Mesh(new THREE.PlaneGeometry(200,200),new THREE.MeshStandardMaterial({
    color:'#24374a',metalness:.05,roughness:.93
  }));
  ground.rotation.x=-Math.PI/2;
  ground.receiveShadow=true;
  scene.add(ground);
  grid=new THREE.GridHelper(14,14,'#6481ac','#324964');
  grid.material.transparent=true;
  grid.material.opacity=.35;
  scene.add(grid);
  clock=new THREE.Clock();
  new ResizeObserver(()=>resize()).observe(mount);
  animate();
}
function resize(){
  if(!renderer)return;
  const w=mount.clientWidth,h=mount.clientHeight;
  if(!w||!h)return;
  camera.aspect=w/h;
  camera.updateProjectionMatrix();
  renderer.setSize(w,h,false);
}
function animate(){
  requestAnimationFrame(animate);
  if(!renderer||document.hidden||document.querySelector('#assets')?.hidden)return;
  if(mixer)mixer.update(Math.min(.05,clock.getDelta()));
  else clock.getDelta();
  controls.update();
  renderer.render(scene,camera);
}
function freeOld(){
  if(!display)return;
  scene.remove(display);
  display.traverse(node=>{
    if(node.isMesh){
      node.geometry?.dispose();
      const materials=Array.isArray(node.material)?node.material:[node.material];
      for(const mat of materials)if(mat){
        for(const key of ['map','normalMap','roughnessMap','metalnessMap','emissiveMap','aoMap','alphaMap'])mat[key]?.dispose();
        mat.dispose();
      }
    }
  });
  if(materialTexture){materialTexture.dispose();materialTexture=null;}
  display=null;mixer=null;
}
function frame(object){
  let bounds=new THREE.Box3().setFromObject(object);
  if(bounds.isEmpty())throw new Error('Le fichier ne contient aucun objet 3D visible.');
  const center=bounds.getCenter(new THREE.Vector3());
  const size=bounds.getSize(new THREE.Vector3());
  const largest=Math.max(size.x,size.y,size.z,.001);
  if(!Number.isFinite(largest)||largest<=.00001)throw new Error('Dimensions invalides dans ce modèle.');
  // Normalise uniquement la mise en scène de prévisualisation ; le fichier original est inchangé.
  const scale=Math.min(25,5/largest);
  object.scale.multiplyScalar(scale);
  bounds=new THREE.Box3().setFromObject(object);
  const center2=bounds.getCenter(new THREE.Vector3());
  object.position.sub(center2);
  object.position.y+=bounds.getSize(new THREE.Vector3()).y/2;
  bounds=new THREE.Box3().setFromObject(object);
  const radius=Math.max(.7,bounds.getSize(new THREE.Vector3()).length()/2);
  originalRadius=radius;
  const yBase=bounds.min.y;
  ground.position.y=yBase-.06;
  grid.position.y=yBase-.045;
  reset();
}
function reset(){
  if(!controls||!camera)return;
  const r=Math.max(1.9,originalRadius);
  controls.target.set(0,r*.30,0);
  camera.position.set(r*1.25,r*.98,r*1.6);
  camera.near=Math.max(.001,r/200);
  camera.far=Math.max(100,r*100);
  camera.updateProjectionMatrix();
  controls.update();
  resize();
}
function binaryBuffer(b64){
  if(b64.length>36*1024*1024)throw new Error('Aperçu trop volumineux.');
  const ascii=atob(b64),data=new Uint8Array(ascii.length);
  for(let i=0;i<ascii.length;i++)data[i]=ascii.charCodeAt(i);
  return data.buffer;
}
function countTriangles(root){
  let sum=0;
  root.traverse(obj=>{
    if(!obj.isMesh)return;
    const g=obj.geometry;
    if(!g)return;
    sum+=Math.floor((g.index?.count||g.attributes.position?.count||0)/3)*(obj.count||1);
  });
  return sum;
}
async function show(resource){
  const token=++currentRequest;
  bootstrap();
  if(!resource||!resource.data||!resource.format)throw Error('Ressource locale invalide.');
  const ext=resource.format.toLowerCase();
  if(!['glb','png','jpg','jpeg'].includes(ext))throw Error('Prévisualisation disponible pour GLB et images PNG/JPEG.');
  let incoming,animations=[];
  if(ext==='glb'){
    const buf=binaryBuffer(resource.data);
    if(new DataView(buf).getUint32(0,true)!==0x46546c67)throw Error('Le fichier n’est pas un GLB valide.');
    const gltf=await new GLTFLoader().parseAsync(buf,'');
    incoming=gltf.scene;
    animations=gltf.animations||[];
    incoming.traverse(obj=>{
      if(obj.isMesh){
        obj.castShadow=true;obj.receiveShadow=true;
        // Metallic, roughness and textures are taken from the actual model.
      }
    });
  }else{
    const mime=ext==='png'?'image/png':'image/jpeg';
    const texture=await new THREE.TextureLoader().loadAsync('data:'+mime+';base64,'+resource.data);
    texture.colorSpace=THREE.SRGBColorSpace;
    materialTexture=texture;
    const aspect=texture.image.width/Math.max(1,texture.image.height);
    incoming=new THREE.Mesh(new THREE.PlaneGeometry(4.3*aspect,4.3),new THREE.MeshStandardMaterial({
      map:texture,side:THREE.DoubleSide,metalness:0,roughness:.75
    }));
    incoming.castShadow=true;
  }
  if(token!==currentRequest){incoming?.traverse(o=>o.geometry?.dispose());return {triangles:null};}
  const count=ext==='glb'?countTriangles(incoming):null;
  freeOld();
  display=incoming;scene.add(display);
  frame(display);
  if(animations.length){
    mixer=new THREE.AnimationMixer(display);
    const action=mixer.clipAction(animations[0]);
    action.play();
  }
  fallback.style.display='none';
  resize();
  renderer.render(scene,camera);
  return {triangles:count};
}
window.CMDStudioViewer={show,resize,reset};
