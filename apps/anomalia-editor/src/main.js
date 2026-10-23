import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { TransformControls } from 'three/addons/controls/TransformControls.js';
import { PRESETS, History, newProject, makeObject, cloneProject, validateProject, makeCSV, addToProject, removeFromProject } from './model.js';
import { createEditorMesh } from './meshes.js';
import './style.css';
import './updates-ui.js';

const $ = s => document.querySelector(s);
const $$ = s => Array.from(document.querySelectorAll(s));
const scene = new THREE.Scene();
scene.background = new THREE.Color('#10202a');
scene.fog = new THREE.Fog('#10202a',115,350);
const stage = $('#viewport');
const camera = new THREE.PerspectiveCamera(58,1,.1,1600);
camera.position.set(25,23,28);
const renderer = new THREE.WebGLRenderer({ antialias:true, alpha:false, powerPreference:'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.shadowMap.enabled=true;
renderer.shadowMap.type=THREE.PCFSoftShadowMap;
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;
stage.prepend(renderer.domElement);
renderer.domElement.classList.add('canvas');
const orbit=new OrbitControls(camera,renderer.domElement);
orbit.enableDamping=true;orbit.dampingFactor=.08;
orbit.target.set(0,0,0);orbit.maxPolarAngle=Math.PI/2-.02;
orbit.maxDistance=350;orbit.minDistance=1;
orbit.mouseButtons={LEFT:THREE.MOUSE.PAN,MIDDLE:THREE.MOUSE.DOLLY,RIGHT:THREE.MOUSE.ROTATE};
orbit.update();
scene.add(new THREE.HemisphereLight('#b1d4ff','#758658',2.2));
const sun = new THREE.DirectionalLight('#fff2d2',3.1);
sun.position.set(-36,65,24);sun.castShadow=true;
sun.shadow.mapSize.set(2048,2048);
sun.shadow.camera.left=-90;sun.shadow.camera.right=90;
sun.shadow.camera.top=90;sun.shadow.camera.bottom=-90;
sun.shadow.bias=-.0002;
scene.add(sun);
const ground=new THREE.Mesh(new THREE.PlaneGeometry(800,800),
  new THREE.MeshStandardMaterial({color:'#49654b',roughness:1}));
ground.rotation.x=-Math.PI/2;ground.position.y=-.07;
ground.receiveShadow=true;scene.add(ground);
const grid=new THREE.GridHelper(800,800,'#8ca58c','#6f826e');
grid.position.y=-.05;grid.material.transparent=true;grid.material.opacity=.23;scene.add(grid);
const objects=new THREE.Group();scene.add(objects);
const raycaster=new THREE.Raycaster();
const cursor=new THREE.Vector2();
const transforms=new TransformControls(camera,renderer.domElement);
const helper=transforms.getHelper();
scene.add(helper);
let history=new History(newProject());
let selectedId=null;
let activeMode='select';
let pendingPreset='house';
let currentCategory='Tous';
let rebuildToken=0;
let saving=null;
const meshed=new Map();
let lastPointer=null;

const toast=(message,error=false)=>{
  const node=$('#toast');node.textContent=message;node.hidden=false;node.classList.toggle('error',error);
  clearTimeout(toast.timeout);toast.timeout=setTimeout(()=>node.hidden=true,4100);
};
const status=(message)=>$('#statusMessage').textContent=message;
function setActiveMode(mode){
  if(!['select','move','rotate','scale','brush'].includes(mode))return;
  activeMode=mode;
  $$('[id$="Tool"]').forEach(b=>b.classList.toggle('selected',b.id===mode+'Tool'));
  $('#modeLabel').textContent=mode==='brush'?'PINCEAU':mode==='select'?'SÉLECTION':mode.toUpperCase();
  if(mode==='select'||mode==='brush')transforms.detach();
  else if(selectedId&&meshed.has(selectedId)){transforms.attach(meshed.get(selectedId));transforms.setMode(mode==='move'?'translate':mode);}
  $('#crosshair').style.display=mode==='brush'?'block':'none';
  status(mode==='brush'?'Clic sur le terrain : peindre avec '+(PRESETS.find(x=>x.id===pendingPreset)?.name||'objet'):'Mode '+mode+' activé');
}
function getObject(id){return history.project.objects.find(o=>o.id===id);}
function applySelection(id) {
  selectedId=getObject(id)?id:null;
  const mesh=selectedId?meshed.get(selectedId):null;
  if(mesh&&['move','rotate','scale'].includes(activeMode)){
    transforms.attach(mesh);transforms.setMode(activeMode==='move'?'translate':activeMode);
  }else transforms.detach();
  renderInspector();
  renderHierarchy();
  if(mesh)status('Sélection : '+mesh.name);
}
function objectFromIntersection(hit){
  let node=hit?.object;
  while(node&&node!==objects){if(node.userData.editorId)return node.userData.editorId;node=node.parent;}
  return null;
}
function snapValue(n){
  if(!$('#snap').checked)return n;
  const step=Number($('#snapSize').value)||1;return Math.round(n/step)*step;
}
function pickGround(event){
  const rect=renderer.domElement.getBoundingClientRect();
  cursor.x=((event.clientX-rect.left)/rect.width)*2-1;
  cursor.y=-((event.clientY-rect.top)/rect.height)*2+1;
  raycaster.setFromCamera(cursor,camera);
  const result=raycaster.intersectObject(ground,false)[0];
  if(!result)return null;
  return {x:snapValue(result.point.x),y:0,z:snapValue(result.point.z)};
}
function pointerHits(event){
  const rect=renderer.domElement.getBoundingClientRect();
  cursor.x=((event.clientX-rect.left)/rect.width)*2-1;
  cursor.y=-((event.clientY-rect.top)/rect.height)*2+1;
  raycaster.setFromCamera(cursor,camera);
  return raycaster.intersectObjects(objects.children,true);
}
async function addPreset(preset,position){
  if(history.project.objects.length>=4000){toast('Limite de 4 000 objets atteinte.',true);return;}
  const object=makeObject(preset,position);
  const next=addToProject(history.project,object);
  if(history.commit(next)){
    const mesh=await createEditorMesh(object);
    objects.add(mesh);meshed.set(object.id,mesh);
    afterCommit();applySelection(object.id);
  }
}
async function addModel(file,position={x:0,y:0,z:0}){
  if(file.size>14*1024*1024)throw new Error('Modèle GLB trop volumineux (maximum 14 Mo).');
  if(!/\.glb$/i.test(file.name))throw new Error('Choisis un vrai fichier .glb.');
  const buffer=await file.arrayBuffer();
  const view=new DataView(buffer);
  if(view.getUint32(0,true)!==0x46546c67)throw new Error('Signature GLB incorrecte.');
  let binary='';const bytes=new Uint8Array(buffer);
  for(let i=0;i<bytes.length;i+=32768)binary+=String.fromCharCode(...bytes.subarray(i,i+32768));
  const asset={filename:file.name.slice(0,140),data:btoa(binary)};
  const item=makeObject('custom-glb',position,asset);
  const mesh=await createEditorMesh(item);
  const next=addToProject(history.project,item);
  if(history.commit(next)){objects.add(mesh);meshed.set(item.id,mesh);afterCommit();applySelection(item.id);}
}
async function rebuild(project) {
  const token=++rebuildToken;
  transforms.detach();
  objects.clear();meshed.clear();
  const errors=[];
  for(const item of project.objects) {
    if(token!==rebuildToken)return;
    try {
      const mesh=await createEditorMesh(item);
      if(token!==rebuildToken){mesh.clear();return;}
      objects.add(mesh);meshed.set(item.id,mesh);
    } catch(e){errors.push(item.name+': '+e.message);}
  }
  applySelection(selectedId);
  renderHierarchy();
  if(errors.length)toast('Certains modèles ne peuvent pas être affichés : '+errors.join(' ; ').slice(0,250),true);
}
function commitCurrent(transformOnly=false) {
  if(!selectedId||!meshed.has(selectedId))return;
  const mesh=meshed.get(selectedId);
  const next=cloneProject(history.project);
  const o=next.objects.find(o=>o.id===selectedId);if(!o)return;
  o.position={x:mesh.position.x,y:mesh.position.y,z:mesh.position.z};
  o.rotation={x:THREE.MathUtils.radToDeg(mesh.rotation.x),y:THREE.MathUtils.radToDeg(mesh.rotation.y),z:THREE.MathUtils.radToDeg(mesh.rotation.z)};
  o.scale={x:mesh.scale.x,y:mesh.scale.y,z:mesh.scale.z};
  try{if(history.commit(next))afterCommit();}catch(e){toast(e.message,true);rebuild(history.project);}
}
transforms.addEventListener('dragging-changed',event=>{
  orbit.enabled=!event.value;
  if(!event.value)commitCurrent(true);
});
transforms.addEventListener('objectChange',()=>renderInspector(true));
renderer.domElement.addEventListener('pointerdown',e=>{lastPointer={x:e.clientX,y:e.clientY,button:e.button};});
renderer.domElement.addEventListener('pointerup',async e=>{
  if(!lastPointer||lastPointer.button!==0||e.button!==0||Math.hypot(e.clientX-lastPointer.x,e.clientY-lastPointer.y)>5)return;
  if(transforms.dragging)return;
  if(activeMode==='brush'){
    const point=pickGround(e);if(!point)return;
    for(let i=0;i<3;i++){
      const offset={x:point.x+(Math.random()-.5)*5,y:0,z:point.z+(Math.random()-.5)*5};
      try{await addPreset(pendingPreset,offset);}catch(err){toast(err.message,true);break;}
    }
    return;
  }
  const hits=pointerHits(e);
  const id=hits.map(objectFromIntersection).find(Boolean);
  applySelection(id||null);
});
renderer.domElement.addEventListener('pointermove',e=>{
  const pos=pickGround(e);
  if(pos)$('#coords').textContent='X '+pos.x.toFixed(1)+' · Y '+pos.y.toFixed(1)+' · Z '+pos.z.toFixed(1);
});
function afterCommit(){
  $('#projectName').value=history.project.name;
  renderHierarchy();renderInspector();updateCount();
  clearTimeout(saving);saving=setTimeout(()=>storeProject(history.project).catch(e=>toast('Sauvegarde locale impossible : '+e.message,true)),650);
}
function updateCount(){const n=history.project.objects.length;$('#count').textContent=n+' objet'+(n>1?'s':'');}
function renderCatalog() {
  const categories=['Tous',...new Set(PRESETS.map(p=>p.category))];
  const bar=$('#categoryBar');bar.replaceChildren();
  for(const category of categories) {
    const btn=document.createElement('button');btn.textContent=category;
    btn.className='category'+(currentCategory===category?' on':'');
    btn.onclick=()=>{currentCategory=category;renderCatalog();};bar.append(btn);
  }
  const search=$('#assetSearch').value.trim().toLowerCase();
  const grid=$('#catalog');grid.replaceChildren();
  const icons={house:'⌂',villa:'◇',apartment:'▥',warehouse:'▣',wall:'▤',road:'═',fence:'☷',tower:'♜',pine:'♠',tree:'♣',rock:'⬟',bush:'❀',car:'▰',truck:'▣',boat:'◒',helicopter:'✣',table:'▦',crate:'▧',barrel:'◉',streetlight:'♧'};
  for(const p of PRESETS.filter(p=>(currentCategory==='Tous'||p.category===currentCategory)&&p.name.toLowerCase().includes(search))){
    const btn=document.createElement('button');btn.className='catalogItem';
    const icon=document.createElement('span');icon.className='catalogIcon';icon.textContent=icons[p.id]||'◈';
    const label=document.createElement('span');label.textContent=p.name;
    btn.append(icon,label);
    btn.onclick=async()=>{pendingPreset=p.id;await addPreset(p.id,{x:snapValue(orbit.target.x),y:0,z:snapValue(orbit.target.z)});};
    grid.append(btn);
  }
}
function renderHierarchy() {
  const list=$('#hierarchy');list.replaceChildren();
  for(const item of history.project.objects){
    const btn=document.createElement('button');btn.className='treeItem'+(selectedId===item.id?' active':'');
    const marker=document.createElement('span');marker.textContent='◈';
    const name=document.createElement('span');name.textContent=item.name;
    btn.append(marker,name);btn.onclick=()=>applySelection(item.id);
    list.append(btn);
  }
}
function renderInspector(live=false) {
  const item=getObject(selectedId);
  $('#inspector').hidden=!item;$('#noSelection').hidden=Boolean(item);
  if(!item)return;
  const mesh=meshed.get(item.id);
  $('#objectName').value=item.name;
  const sources={
    position:mesh?mesh.position:item.position,
    rotation:mesh?{x:THREE.MathUtils.radToDeg(mesh.rotation.x),y:THREE.MathUtils.radToDeg(mesh.rotation.y),z:THREE.MathUtils.radToDeg(mesh.rotation.z)}:item.rotation,
    scale:mesh?mesh.scale:item.scale
  };
  for(const el of $$('#inspector input[data-group]')){
    if(document.activeElement===el&&!live)continue;
    el.value=Number(sources[el.dataset.group][el.dataset.axis]).toFixed(el.dataset.group==='rotation'?1:2);
  }
  $('#meta').textContent='Catégorie : '+(PRESETS.find(p=>p.id===item.preset)?.category||'Import GLB')+'\nID : '+item.id;
}
function changeProperty() {
  const item=getObject(selectedId),mesh=meshed.get(selectedId);
  if(!item||!mesh)return;
  const next=cloneProject(history.project);
  const target=next.objects.find(o=>o.id===selectedId);
  for(const input of $$('#inspector input[data-group]')){
    const value=Number(input.value);
    if(!Number.isFinite(value))return toast('Nombre invalide',true);
    target[input.dataset.group][input.dataset.axis]=value;
  }
  try {
    validateProject(next);
    mesh.position.set(target.position.x,target.position.y,target.position.z);
    mesh.rotation.set(...['x','y','z'].map(k=>THREE.MathUtils.degToRad(target.rotation[k])));
    mesh.scale.set(target.scale.x,target.scale.y,target.scale.z);
    if(history.commit(next))afterCommit();
  }catch(e){toast(e.message,true);renderInspector();}
}
function renameObject() {
  const item=getObject(selectedId);if(!item)return;
  const name=$('#objectName').value.trim().slice(0,90);
  if(!name)return toast('Un nom est nécessaire',true);
  const next=cloneProject(history.project);next.objects.find(o=>o.id===selectedId).name=name;
  if(history.commit(next)){meshed.get(selectedId).name=name;afterCommit();}
}
async function duplicateObject() {
  const item=getObject(selectedId);if(!item)return;
  const clone=cloneProject(item);clone.id=crypto.randomUUID();
  clone.name=(item.name+' copie').slice(0,90);clone.position.x+=2;
  const mesh=await createEditorMesh(clone);
  if(history.commit(addToProject(history.project,clone))){objects.add(mesh);meshed.set(clone.id,mesh);afterCommit();applySelection(clone.id);}
}
function removeSelected(){
  if(!selectedId)return;
  const id=selectedId;
  if(history.commit(removeFromProject(history.project,id))){
    transforms.detach();const mesh=meshed.get(id);objects.remove(mesh);meshed.delete(id);
    selectedId=null;afterCommit();applySelection(null);
  }
}
async function stepHistory(direction) {
  const next=direction==='undo'?history.undo():history.redo();
  if(next){await rebuild(next);afterCommit();}
}
function focusObject() {
  const mesh=meshed.get(selectedId);if(!mesh)return;
  orbit.target.copy(mesh.position);
  camera.position.copy(mesh.position).add(new THREE.Vector3(11,10,13));orbit.update();
}
function download(filename,contents,mime) {
  const blob=new Blob([contents],{type:mime});
  const url=URL.createObjectURL(blob);const link=document.createElement('a');
  link.href=url;link.download=filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1200);
}
function projectName(){return (history.project.name||'carte').replace(/[^a-z0-9_-]/gi,'_').slice(0,50);}
function exportJSON(){
  download(projectName()+'.anomalia.json',JSON.stringify(history.project,null,2),'application/json');
  toast('Scène exportée sur ton appareil.');
}
function exportCSV(){
  download(projectName()+'-placements.csv',makeCSV(history.project),'text/csv;charset=utf-8');
  toast('Fichier CSV exporté : positions, rotations et tailles.');
}
function openDatabase(){
  return new Promise((resolve,reject)=>{
    const req=indexedDB.open('anomalia-editor-private-local',1);
    req.onupgradeneeded=()=>{if(!req.result.objectStoreNames.contains('projects'))req.result.createObjectStore('projects');};
    req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);
  });
}
async function storeProject(project) {
  const db=await openDatabase();
  return new Promise((resolve,reject)=>{
    const tx=db.transaction('projects','readwrite');
    tx.objectStore('projects').put(project,'last-opened');
    tx.oncomplete=()=>{db.close();resolve();};tx.onerror=()=>{db.close();reject(tx.error);};
  });
}
async function restoreProject() {
  const db=await openDatabase();
  return new Promise((resolve,reject)=>{
    const tx=db.transaction('projects','readonly');
    const req=tx.objectStore('projects').get('last-opened');
    req.onsuccess=()=>{db.close();resolve(req.result||null);};req.onerror=()=>{db.close();reject(req.error);};
  });
}
function resize(){
  const w=stage.clientWidth,h=stage.clientHeight;
  if(w<1||h<1)return;
  camera.aspect=w/h;camera.updateProjectionMatrix();
  renderer.setSize(w,h,false);
}
new ResizeObserver(resize).observe(stage);
function animate(){
  requestAnimationFrame(animate);orbit.update();renderer.render(scene,camera);
}
for(const mode of ['select','move','rotate','scale','brush'])$('#'+mode+'Tool').onclick=()=>setActiveMode(mode);
$('#undo').onclick=()=>stepHistory('undo');$('#redo').onclick=()=>stepHistory('redo');
$('#duplicate').onclick=duplicateObject;$('#inspectorDuplicate').onclick=duplicateObject;
$('#delete').onclick=removeSelected;$('#focusObject').onclick=focusObject;
$('#assetSearch').addEventListener('input',renderCatalog);
$('#inspector').addEventListener('change',e=>{if(e.target.matches('input[data-group]'))changeProperty();});
$('#objectName').addEventListener('change',renameObject);
$('#projectName').addEventListener('change',()=>{
  const name=$('#projectName').value.trim().slice(0,80)||'Nouvelle carte';
  const next=cloneProject(history.project);next.name=name;
  if(history.commit(next))afterCommit();
});
$('#saveScene').onclick=async()=>{await storeProject(history.project);toast('Sauvegardé en privé dans ce navigateur.');};
$('#saveAs').onclick=exportJSON;$('#exportScene').onclick=exportJSON;$('#exportCSV').onclick=exportCSV;
$('#newScene').onclick=async()=>{
  if(history.project.objects.length&&!confirm('Créer une nouvelle carte ? Exporte d’abord la carte actuelle si tu veux la conserver.'))return;
  history.reset(newProject());selectedId=null;await rebuild(history.project);afterCommit();
  toast('Nouvelle carte créée.');
};
$('#openScene').onclick=()=>$('#fileOpen').click();
$('#fileOpen').onchange=async e=>{
  const file=e.target.files?.[0];if(!file)return;
  try{
    if(file.size>45*1024*1024)throw new Error('Projet trop volumineux (45 Mo maximum).');
    const parsed=validateProject(JSON.parse(await file.text()));
    history.reset(parsed);selectedId=null;await rebuild(parsed);afterCommit();toast('Projet ouvert : '+parsed.name);
  }catch(err){toast('Fichier invalide : '+err.message,true);}
  e.target.value='';
};
$('#importModel').onclick=()=>$('#fileModel').click();
$('#fileModel').onchange=async e=>{
  const file=e.target.files?.[0];if(!file)return;
  try{await addModel(file,{x:snapValue(orbit.target.x),y:0,z:snapValue(orbit.target.z)});toast('Modèle GLB importé.');}
  catch(err){toast(err.message,true);}
  e.target.value='';
};
window.addEventListener('keydown',e=>{
  if(e.target instanceof HTMLInputElement||e.target instanceof HTMLSelectElement||e.target instanceof HTMLTextAreaElement)return;
  const ctrl=e.ctrlKey||e.metaKey;
  const key=e.key.toLowerCase();
  if(ctrl&&key==='z'){e.preventDefault();stepHistory(e.shiftKey?'redo':'undo');}
  else if(ctrl&&key==='y'){e.preventDefault();stepHistory('redo');}
  else if(ctrl&&key==='d'){e.preventDefault();duplicateObject();}
  else if(ctrl&&key==='s'){e.preventDefault();storeProject(history.project).then(()=>toast('Sauvegarde privée effectuée.'));}
  else if(key==='delete'){removeSelected();}
  else if(key==='q'){setActiveMode('select');}
  else if(key==='w'){setActiveMode('move');}
  else if(key==='e'){setActiveMode('rotate');}
  else if(key==='r'){setActiveMode('scale');}
  else if(key==='b'){setActiveMode('brush');}
  else if(key==='f'){focusObject();}
});
async function start(){
  renderCatalog();resize();animate();
  try{
    const previous=await restoreProject();
    if(previous){
      history.reset(validateProject(previous));
      await rebuild(history.project);
      $('#projectName').value=history.project.name;
      status('Carte privée restaurée depuis cet appareil.');
    } else {
      await addPreset('house',{x:0,y:0,z:0});
      await addPreset('tree',{x:9,y:0,z:3});
      await addPreset('car',{x:-9,y:0,z:3});
      history=new History(history.project);applySelection(null);
      await storeProject(history.project);
      status('Scène de démonstration locale créée : utilise le catalogue pour ajouter des objets.');
    }
    updateCount();
  }catch(e){toast('Stockage privé inaccessible : '+e.message,true);}
}
start();
