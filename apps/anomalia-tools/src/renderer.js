import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import './style.css';
import './updates-ui.js';
import './tools-workspace-fix.css';
import {setupToolsUtilities} from './utilities-ui.js';

const api=window.anomaliaTools;
const $=s=>document.querySelector(s);
const $$=s=>[...document.querySelectorAll(s)];
const MODS=[
  ['workbench','⌘','Workbench','Scripts, configs et éditeur de sources'],
  ['objects','⬡','Object Builder','Importer et inspecter des modèles GLB'],
  ['terrain','▥','Terrain Builder','Heightmaps PNG pour Unreal'],
  ['economy','◇','Central Economy','Tables de butin et quantités'],
  ['textures','▨','Texture Tools','Textures et inspection locale'],
  ['addon','◈','Addon Builder','Archives de mods et manifestes'],
  ['publisher','⬆','Publisher','Exporter tes packages en ZIP']
];
const titles={home:"Vue d'ensemble",...Object.fromEntries(MODS.map(([id,,title])=>[id,title])),workshop:'ANOMALIA Workshop',utilities:'Utilitaires',systemStatus:'Statut des outils',updates:'Mises à jour'};
const SOURCE=new Set(['.js','.ts','.json','.xml','.ini','.cfg','.cpp','.h','.hpp','.cs','.txt','.md','.py','.uproject','.uplugin']);
const TEXTURES=['.png','.jpg','.jpeg','.webp','.tga'];
let projects=[],currentId='',files=[],fileOpen='',economy={items:[]},activeTab='home';
let viewer=null;
let activeUtility='terrainProcessor';
let utilities;
function node(tag,text='',className=''){
  const item=document.createElement(tag);
  if(text)item.textContent=text;
  if(className)item.className=className;
  return item;
}
function msg(message,error=false){
  $('#notice').hidden=false;$('#notice').textContent=message;$('#notice').classList.toggle('error',error);
}
async function safe(operation){
  try{return await operation();}
  catch(err){msg(err?.message||String(err),true);return null;}
}
function requireProject(){
  if(!currentId){msg('Crée ou sélectionne un projet avant de travailler.',true);return false;}
  return true;
}
function setTab(tab){
  if(!(tab in titles))return;
  activeTab=tab;
  $$('.page').forEach(p=>p.hidden=p.id!==tab);
  $$('button[data-tab]').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab));
  $('#pageTitle').textContent=titles[tab];
  if(tab==='workbench')renderFiles();
  if(tab==='objects')renderAssets();
  if(tab==='textures')renderTextures();
  if(tab==='terrain')renderTerrainFiles();
  if(tab==='economy')refreshEconomy();
  if(tab==='addon')nativeStatus();
  if(tab==='workshop')refreshWorkshop();
  if(tab==='home')renderProjects();
  if(tab==='systemStatus')utilities.refreshStatus();
  if(tab==='utilities')utilities.select(activeUtility);
  if(viewer&&tab==='objects')requestAnimationFrame(()=>viewer.resize());
}
function showModal(){$('#modal').hidden=false;$('#newName').focus();}
function hideModal(){$('#modal').hidden=true;}
async function refreshProjects(select=null){
  projects=await api.call('listProjects');
  const picker=$('#activeProject');picker.replaceChildren(new Option('Choisir un projet...',''));
  for(const p of projects)picker.add(new Option(p.name,p.id));
  if(select&&projects.some(p=>p.id===select))currentId=select;
  else if(!projects.some(p=>p.id===currentId))currentId=projects[0]?.id||'';
  picker.value=currentId;
  $('#projectCount').textContent=projects.length+' projet'+(projects.length>1?'s':'');
  $('#overviewProjectTotal').textContent=projects.length;
  $('#sidebarWorkspaceName').textContent=projects.find(p=>p.id===currentId)?.name||'Aucun projet actif';
  renderProjects();
  await refreshFiles();
}
async function refreshFiles(){
  files=currentId?await api.call('listFiles',{projectId:currentId}):[];
  $('#overviewFileTotal').textContent=files.filter(f=>f.type==='file').length;
  $('#sidebarWorkspaceName').textContent=projects.find(p=>p.id===currentId)?.name||'Aucun projet actif';
  renderFiles();renderAssets();renderTextures();renderTerrainFiles();
}
function renderProjects(){
  const panel=$('#projectsList');panel.replaceChildren();
  if(!projects.length){panel.append(node('div','Aucun projet. Utilise « Nouveau projet » pour commencer.','output'));return;}
  for(const p of projects){
    const b=node('button','','projectItem'+(p.id===currentId?' active':''));
    const content=node('div');content.append(node('b',p.name),node('small',p.description||'Projet de mod ANOMALIA privé'));
    b.append(content,node('span',p.id===currentId?'Projet actif':'Ouvrir →'));
    b.onclick=async()=>{currentId=p.id;$('#activeProject').value=p.id;await refreshFiles();renderProjects();msg('Projet sélectionné : '+p.name);};
    panel.append(b);
  }
}
function renderModules(){
  const panel=$('#moduleCards');panel.replaceChildren();
  for(const [id,glyph,title,desc] of MODS){
    const btn=node('button','','moduleCard');
    btn.append(node('span',glyph,'glyph'),node('strong',title),node('p',desc),node('span','Ouvrir l’outil →','jump'));
    btn.onclick=()=>setTab(id);panel.append(btn);
  }
}
function extension(file){return '.'+file.split('.').pop().toLowerCase();}
function isText(file){return SOURCE.has(extension(file));}
function renderFiles(){
  const box=$('#filesList');box.replaceChildren();
  if(!currentId){box.append(node('div','Choisis un projet.','output'));return;}
  for(const file of files){
    const icon=file.type==='folder'?'▣ ':isText(file.path)?'⌘ ':'◈ ';
    const b=node('button',icon+file.path,'fileEntry'+(fileOpen===file.path?' active':''));
    if(file.type==='folder'){b.disabled=true;b.title='Dossier';}
    else if(isText(file.path))b.onclick=()=>openSource(file.path);
    else b.onclick=()=>msg('Choisis ce fichier dans Object Builder ou Texture Tools pour un aperçu.');
    box.append(b);
  }
}
async function openSource(path){
  if(!requireProject())return;
  const res=await safe(()=>api.call('readText',{projectId:currentId,file:path}));
  if(!res)return;
  fileOpen=res.path;$('#fileTitle').textContent=path;$('#sourceEditor').value=res.content;
  renderFiles();setTab('workbench');msg('Fichier chargé : '+path);
}
async function saveSource(){
  if(!requireProject()||!fileOpen){msg('Sélectionne un fichier texte à enregistrer.',true);return;}
  const output=await safe(()=>api.call('writeText',{projectId:currentId,file:fileOpen,content:$('#sourceEditor').value}));
  if(output){msg('Fichier enregistré : '+fileOpen);await refreshFiles();}
}
async function createSource(){
  if(!requireProject())return;
  const path=prompt('Chemin du nouveau fichier, par exemple Source/mon_module.cpp','Source/mon_module.cpp');
  if(!path)return;
  if(!isText(path)){msg('Extension non prise en charge pour un fichier source.',true);return;}
  if(files.some(f=>f.path===path)){msg('Le fichier existe déjà : sélectionne-le dans Workbench.',true);return;}
  const res=await safe(()=>api.call('writeText',{projectId:currentId,file:path,content:'// Nouveau fichier ANOMALIA\n'}));
  if(res){await refreshFiles();await openSource(path);}
}
async function importAssets(){
  if(!requireProject())return;
  const paths=await api.chooseAssets();
  if(!paths?.length)return;
  const result=await safe(()=>api.call('importAssets',{projectId:currentId,paths}));
  if(result){msg(result.length+' ressource(s) importée(s) dans ce projet seulement.');await refreshFiles();}
}
function entryList(container,filter,handler){
  const panel=$(container);panel.replaceChildren();
  if(!currentId){panel.append(node('div','Choisir un projet.','output'));return;}
  let count=0;
  for(const f of files){
    if(f.type!=='file'||!filter(f))continue;
    count++;
    const b=node('button',f.path,'fileEntry');b.onclick=()=>handler(f.path);panel.append(b);
  }
  if(!count)panel.append(node('div','Aucun fichier compatible dans le projet.','output'));
}
function renderAssets(){
  entryList('#modelsList',f=>['.glb','.gltf','.fbx','.obj','.usd'].includes(extension(f.path)),showModel);
}
function renderTextures(){
  entryList('#texturesList',f=>TEXTURES.includes(extension(f.path)),showTexture);
}
function renderTerrainFiles(){
  entryList('#terrainList',f=>f.path.startsWith('Content/Terrain/')&&extension(f.path)==='.png',showTerrain);
}
function createViewer(){
  const mount=$('#modelView');
  const scene=new THREE.Scene();scene.background=new THREE.Color('#161b2a');
  const camera=new THREE.PerspectiveCamera(55,1,.01,1500);camera.position.set(4,3,6);
  const renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'default'});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
  renderer.outputColorSpace=THREE.SRGBColorSpace;
  renderer.toneMapping=THREE.ACESFilmicToneMapping;
  mount.replaceChildren(renderer.domElement);
  scene.add(new THREE.HemisphereLight('#c6d6ff','#535e70',2.4));
  const light=new THREE.DirectionalLight('#ffffff',2.6);light.position.set(4,7,6);scene.add(light);
  const grid=new THREE.GridHelper(20,20,'#65599c','#303748');scene.add(grid);
  const orbit=new OrbitControls(camera,renderer.domElement);
  orbit.enableDamping=true;
  let model=null;
  const resize=()=>{
    const w=mount.clientWidth,h=mount.clientHeight;
    if(w<=0||h<=0)return;
    camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false);
  };
  new ResizeObserver(resize).observe(mount);
  let running=true;
  function animate(){if(!running)return;requestAnimationFrame(animate);if(!document.hidden&&activeTab==='objects'){orbit.update();renderer.render(scene,camera);}}
  animate();
  return {
    resize,
    async render(base64){
      if(model){scene.remove(model);model.traverse(o=>{
        if(o.geometry)o.geometry.dispose();
        if(o.material){const mats=Array.isArray(o.material)?o.material:[o.material];for(const m of mats)m.dispose();}
      });model=null;}
      const str=atob(base64),bytes=new Uint8Array(str.length);
      for(let i=0;i<str.length;i++)bytes[i]=str.charCodeAt(i);
      const gltf=await new GLTFLoader().parseAsync(bytes.buffer,'');
      model=gltf.scene;scene.add(model);
      const bbox=new THREE.Box3().setFromObject(model),size=bbox.getSize(new THREE.Vector3());
      const center=bbox.getCenter(new THREE.Vector3());const longest=Math.max(size.x,size.y,size.z,.1);
      orbit.target.copy(center);
      camera.position.copy(center).add(new THREE.Vector3(longest*1.9,longest*1.2,longest*1.9));
      camera.near=Math.max(.001,longest/1000);camera.far=Math.max(1000,longest*100);
      camera.updateProjectionMatrix();orbit.update();resize();
    }
  };
}
async function showModel(file){
  if(extension(file)!=='.glb'){msg('Aperçu 3D réservé aux fichiers GLB. Pour FBX/OBJ/USD, ouvre le modèle dans Blender ou Unreal.',true);return;}
  const res=await safe(()=>api.call('previewAsset',{projectId:currentId,file}));
  if(!res)return;
  $('#modelTitle').textContent=res.name;
  try{
    if(!viewer)viewer=createViewer();
    await viewer.render(res.data);
    msg('Modèle GLB ouvert dans la vue 3D.');
  }catch(e){msg('Aperçu 3D impossible : '+e.message,true);}
}
async function showTexture(file){
  if(extension(file)==='.tga'){msg('TGA conservé comme source : l’aperçu intégré attend PNG, JPEG ou WebP.',true);return;}
  const res=await safe(()=>api.call('previewAsset',{projectId:currentId,file}));
  if(!res)return;
  $('#textureTitle').textContent=res.name;
  const image=node('img');image.alt='Texture du projet';
  image.src='data:'+res.mime+';base64,'+res.data;
  image.onload=()=>$('#textureMeta').textContent=res.name+' · '+image.naturalWidth+' × '+image.naturalHeight+' px · '+res.mime;
  $('#textureView').replaceChildren(image);
}
async function showTerrain(file){
  const res=await safe(()=>api.call('previewAsset',{projectId:currentId,file}));
  if(!res)return;
  const image=node('img');image.alt='Heightmap terrain';
  image.src='data:'+res.mime+';base64,'+res.data;
  $('#terrainPreview').replaceChildren(image);msg('Heightmap : '+file);
}
async function generateTerrain(e){
  e.preventDefault();if(!requireProject())return;
  const args={projectId:currentId,name:$('#terrainName').value,seed:Number($('#terrainSeed').value),
    resolution:Number($('#terrainRes').value),scaleMeters:Number($('#terrainScale').value),
    octaves:Number($('#terrainOctaves').value)};
  msg('Génération du terrain en cours...');
  const r=await safe(()=>api.call('generateTerrain',args));
  if(r){await refreshFiles();await showTerrain(r.image);msg('Terrain '+r.resolution+' × '+r.resolution+' créé dans Content/Terrain.');}
}
async function refreshEconomy(){
  const panel=$('#lootRows');panel.replaceChildren();
  if(!currentId){panel.append(node('tr','Sélectionne un projet.'));return;}
  const r=await safe(()=>api.call('getEconomy',{projectId:currentId}));
  if(!r)return;
  economy=r;renderEconomy();
}
function renderEconomy(){
  const panel=$('#lootRows');panel.replaceChildren();
  for(const [i,item] of economy.items.entries()){
    const row=node('tr');
    for(const key of ['id','category','min','max','chance']){
      const td=node('td');const input=node('input');input.value=item[key];
      input.type=['min','max','chance'].includes(key)?'number':'text';
      if(input.type==='number'){input.step=key==='chance'?'0.1':'1';input.min='0';input.max=key==='chance'?'100':'100000';}
      input.setAttribute('aria-label',key);
      input.onchange=()=>{economy.items[i][key]=input.type==='number'?Number(input.value):input.value.trim();};
      td.append(input);row.append(td);
    }
    const td=node('td');const deleteBtn=node('button','×');
    deleteBtn.title='Supprimer cette entrée';deleteBtn.onclick=()=>{economy.items.splice(i,1);renderEconomy();};
    td.append(deleteBtn);row.append(td);panel.append(row);
  }
}
async function saveEconomy(){
  if(!requireProject())return;
  $$('#lootRows input').forEach(el=>el.dispatchEvent(new Event('change')));
  const r=await safe(()=>api.call('saveEconomy',{projectId:currentId,economy}));
  if(r){msg('Économie sauvegardée : '+r.count+' entrée(s).');await refreshFiles();}
}
async function packageMod(){
  if(!requireProject())return;
  msg('Création d’une archive de sources sécurisée…');
  const r=await safe(()=>api.call('packageMod',{projectId:currentId}));
  if(r){$('#buildInfo').textContent='Archive créée :\n'+r.path+'\n\n'+r.manifest.assets.length+' fichiers · '+(r.size/1048576).toFixed(2)+' Mo\nManifeste SHA-256 inclus';msg('Archive ZIP créée localement.');await refreshFiles();}
}
function nativeEngineRoot(){return $('#engineRoot')?.value.trim()||'';}
async function nativeStatus(){
  if(!requireProject())return;
  const status=await safe(()=>api.call('getNativeModStatus',{projectId:currentId,engineRoot:nativeEngineRoot()}));
  if(!status)return;
  $('#nativeBuildInfo').textContent='Plugin : '+status.plugin+'\nSources : '+(status.valid?'valides':'incomplètes — '+status.validationError)+'\nUnreal Engine : '+(status.engineFound?'détecté':'introuvable')+'\nMachine Windows : '+(status.supportedHost?'oui':'non')+'\nCompilation possible : '+(status.nativeBuildAvailable?'oui':'non')+'\n'+status.note;
}
async function nativeCreate(){
  if(!requireProject())return;
  const result=await safe(()=>api.call('scaffoldNativeMod',{projectId:currentId}));
  if(!result)return;
  await refreshFiles();await nativeStatus();
  msg('Plugin '+result.plugin+' : '+result.created.length+' nouveau(x) fichier(s). Fichiers existants conservés.');
}
async function nativeBuild(){
  if(!requireProject())return;
  const confirmBuild=confirm('Compiler ce plugin natif C++ avec Unreal Engine sur ce PC ? Un mod inconnu peut contenir du code dangereux.');
  if(!confirmBuild)return;
  $('#nativeBuildInfo').textContent='Compilation UE5 en cours — elle peut durer longtemps…';
  const result=await safe(()=>api.call('buildNativeMod',{projectId:currentId,engineRoot:nativeEngineRoot()}));
  if(!result)return;
  $('#nativeBuildInfo').textContent='Compilation terminée : '+result.plugin+'\nSortie : '+result.output+'\n'+result.log+'\nLe jeu ne charge pas automatiquement ce plugin.';
  msg('Plugin Unreal compilé. Le test de chargement dans ANOMALIA reste à faire.');await refreshFiles();
}

let wsData=null,wsActiveCategory='Tous',wsManagerOnly=false;
const WS_ICONS={'Tous':'✦','Véhicules':'◈','Armes':'⌁','Bâtiments':'▣','Créatures':'◆','Survie':'✺','Cartes':'▤','Vêtements':'▥','Outils':'⚙','Autres':'⬡'};
async function refreshWorkshop(){
  const data=await safe(()=>api.call('listWorkshopMods'));
  if(!data)return;
  wsData=data;
  $('#wsTotal').textContent=data.stats.total;
  $('#wsSubs').textContent=data.stats.subscribed;
  $('#wsPrepared').textContent=data.stats.prepared;
  $('#wsStatus').textContent=data.connection.message;
  renderWsCategories();renderWsCards();renderWsProjects();
}
function renderWsCategories(){
  const panel=$('#wsCategories');panel.replaceChildren();
  for(const name of ['Tous',...wsData.categories]){
    const count=name==='Tous'?wsData.entries.length:wsData.entries.filter(x=>x.category===name).length;
    const b=node('button','','wsCategory'+(wsActiveCategory===name?' active':''));
    b.type='button';b.append(node('span',WS_ICONS[name]||'✦','wsCatIcon'),node('strong',name),node('small',count+' mod'+(count===1?'':'s')));
    b.onclick=()=>{wsActiveCategory=name;renderWsCategories();renderWsCards();};
    panel.append(b);
  }
}
function wsCompare(a,b,sort){
  if(sort==='name')return a.title.localeCompare(b.title,'fr');
  if(sort==='category')return a.category.localeCompare(b.category,'fr')||a.title.localeCompare(b.title,'fr');
  return String(b.updatedAt).localeCompare(String(a.updatedAt));
}
function renderWsCards(){
  const panel=$('#wsModGrid');panel.replaceChildren();
  if(!wsData)return;
  const search=$('#wsSearch').value.trim().toLocaleLowerCase('fr');
  const filter=wsData.entries
    .filter(x=>(wsActiveCategory==='Tous'||x.category===wsActiveCategory)&&(!wsManagerOnly||x.prepared)&&
      (!search||[x.title,x.author,x.description,x.category].some(t=>String(t).toLocaleLowerCase('fr').includes(search))))
    .sort((a,b)=>wsCompare(a,b,$('#wsOrder').value));
  $('#wsVisibleCount').textContent='('+filter.length+')';
  if(!filter.length){
    const empty=node('div','','wsEmpty');
    empty.append(node('strong',wsData.entries.length?'Aucun mod pour ces filtres.':'Aucun mod publié dans ta bibliothèque.'));
    empty.append(node('p',wsData.entries.length?'Modifie les catégories ou la recherche.':'Choisis un projet dans « Mes mods & créations » puis ajoute-le au Workshop. Les fiches représentent uniquement tes vrais projets.'));
    panel.append(empty);return;
  }
  for(const mod of filter){
    const card=node('article','','wsModCard');
    const art=node('div','','wsCardArt');
    art.append(node('span',WS_ICONS[mod.category]||'✦','wsTileGlyph'),node('span',mod.category,'wsLabel'));
    const body=node('div','','wsCardBody');
    const title=node('div','','wsCardHeading');
    title.append(node('h4',mod.title),node('small','v'+mod.version));
    body.append(title,node('p',mod.description||'Création ANOMALIA locale — aucune description disponible.'));
    const chips=node('div','','wsChips');
    for(const label of [mod.compiled?'Plugin UE5 compilé':'Sources du mod',mod.prepared?'Préparé dans la bibliothèque':'Non préparé',mod.active?'Activé localement':'Jeu non chargé']){
      chips.append(node('span',label,'wsChip'));
    }
    body.append(chips);
    const actions=node('div','','wsCardActions');
    const sub=node('button',mod.subscribed?'✓ Abonné':'☆ S’abonner');
    sub.onclick=async()=>{
      const r=await safe(()=>api.call('subscribeWorkshopMod',{projectId:mod.id,value:!mod.subscribed}));
      if(r){msg(r.subscribed?'Abonnement local enregistré.':'Abonnement local annulé.');await refreshWorkshop();}
    };
    const prepare=node('button',mod.compiled?(mod.prepared?'↻ Mettre à jour':'↓ Préparer le mod'):'⚒ Compiler d’abord','wsCrimson');
    prepare.onclick=async()=>{
      currentId=mod.id;$('#activeProject').value=mod.id;await refreshFiles();renderProjects();
      if(!mod.compiled){setTab('addon');msg('Ce mod doit être compilé dans Addon Builder avant son installation locale.',true);return;}
      const r=await safe(()=>api.call('prepareWorkshopMod',{projectId:mod.id}));
      if(r){msg(r.message);await refreshWorkshop();}
    };
    actions.append(prepare,sub);
    if(mod.compiled){
      const host=node('button','CMD Hosting ↗');
      host.title='Exporter un manifeste de configuration pour CMD Hosting (sans installation automatique)';
      host.onclick=async()=>{
        const result=await safe(()=>api.exportHostingManifest(mod.id));
        if(result?.saved)msg(result.note+' · '+result.file);
      };
      actions.append(host);
    }

    if(mod.prepared){
      const toggle=node('button',mod.active?'Désactiver':'Activer');
      toggle.onclick=async()=>{
        const r=await safe(()=>api.call('toggleWorkshopMod',{projectId:mod.id,enabled:!mod.active}));
        if(r){msg(r.note);await refreshWorkshop();}
      };
      actions.append(toggle);
    }
    const edit=node('button','Modifier fiche');
    edit.onclick=()=>openWsPublish(mod.id);
    actions.append(edit);body.append(actions);card.append(art,body);panel.append(card);
  }
}
function renderWsProjects(){
  const box=$('#wsProjects');box.replaceChildren();
  if(!wsData.projects.length){box.append(node('div','Aucun projet : crée un mod depuis le bouton Nouveau projet.','wsMuted'));return;}
  for(const project of wsData.projects){
    const row=node('div','','wsProjectRow');
    row.append(node('span',project.name));
    const published=wsData.entries.some(x=>x.id===project.id);
    const btn=node('button',published?'Modifier fiche':'Ajouter au Workshop',published?'button':'wsCrimson');
    btn.onclick=()=>openWsPublish(project.id);
    row.append(btn);box.append(row);
  }
}
function openWsPublish(projectId=null){
  if(!wsData?.projects?.length){showModal();msg('Crée d’abord ton projet de mod dans ANOMALIA Tools.');return;}
  const picker=$('#wsProjectSelect');picker.replaceChildren();
  for(const project of wsData.projects)picker.add(new Option(project.name,project.id));
  picker.value=projectId&&wsData.projects.some(x=>x.id===projectId)?projectId:(currentId||wsData.projects[0].id);
  if(!picker.value)picker.value=wsData.projects[0].id;
  function populate(){
    const project=wsData.projects.find(x=>x.id===picker.value);
    const existing=wsData.entries.find(x=>x.id===picker.value);
    $('#wsModName').value=existing?.title||project?.name||'';
    $('#wsModCategory').value=existing?.category||'Autres';
    $('#wsModVersion').value=existing?.version||'0.1.0';
    $('#wsModDescription').value=existing?.description||project?.description||'';
  }
  picker.onchange=populate;populate();
  $('#wsPublishPanel').hidden=false;$('#wsModName').focus();
}
async function saveWsPublish(e){
  e.preventDefault();
  const data={projectId:$('#wsProjectSelect').value,title:$('#wsModName').value,
    category:$('#wsModCategory').value,version:$('#wsModVersion').value,
    description:$('#wsModDescription').value};
  const result=await safe(()=>api.call('publishWorkshopMod',data));
  if(result){$('#wsPublishPanel').hidden=true;msg('Mod ajouté à ton Workshop local. Aucune publication sur Internet.');await refreshWorkshop();}
}

async function publish(){
  if(!requireProject())return;
  const r=await safe(()=>api.exportPackage(currentId));
  if(r&&!r.cancelled){
    $('#publishInfo').textContent='Archive exportée :\n'+r.path+'\n\nLe mod n’a pas été publié en ligne.';
    msg('Package exporté sur ton ordinateur.');
  }
}
utilities=setupToolsUtilities({
  api,getProjectId:()=>currentId,getFiles:()=>files,getProjects:()=>projects,
  refreshFiles,showTab:setTab,showModal,notify:msg
});
$('[data-tab]').forEach(b=>b.onclick=()=>{
  if(b.dataset.tab==='utilities'&&b.dataset.utility)activeUtility=b.dataset.utility;
  setTab(b.dataset.tab);
});
$('#newProject').onclick=$('#heroCreate').onclick=showModal;
$('#heroExplore').onclick=()=>setTab('workbench');
$('#cancelModal').onclick=hideModal;
$('#createForm').onsubmit=async e=>{
  e.preventDefault();
  const p=await safe(()=>api.call('createProject',{name:$('#newName').value,description:$('#newDescription').value}));
  if(p){hideModal();await refreshProjects(p.id);setTab('home');msg('Projet privé créé : '+p.name);$('#createForm').reset();}
};
$('#activeProject').onchange=async e=>{
  currentId=e.target.value;fileOpen='';$('#sourceEditor').value='';$('#fileTitle').textContent='Aucun fichier sélectionné';
  await refreshFiles();renderProjects();
};
$('#saveFile').onclick=saveSource;$('#newSource').onclick=createSource;
$('#import3D').onclick=$('#importTexture').onclick=importAssets;
$('#terrainForm').onsubmit=generateTerrain;
$('#addLoot').onclick=()=>{
  if(!requireProject())return;
  economy.items.push({id:'new_item_'+(economy.items.length+1),category:'Divers',min:1,max:5,chance:25});
  renderEconomy();
};
$('#saveEconomy').onclick=saveEconomy;
$('#buildAddon').onclick=packageMod;
$('#createNativeMod').onclick=nativeCreate;
$('#checkNativeMod').onclick=nativeStatus;
$('#buildNativeMod').onclick=nativeBuild;
$('#exportMod').onclick=publish;
$('#wsSearch').oninput=renderWsCards;
$('#wsOrder').onchange=renderWsCards;
$('#wsReload').onclick=refreshWorkshop;
$('#wsCreate').onclick=()=>openWsPublish();
$('#wsManage').onclick=()=>{wsManagerOnly=!wsManagerOnly;$('#wsManage').textContent=wsManagerOnly?'Voir tous les mods ↗':'Gérer mes mods ↗';renderWsCards();};
$('#wsOpenAddon').onclick=()=>{setTab('addon');};
$('#wsPublishForm').onsubmit=saveWsPublish;
$('#wsCancelPublish').onclick=()=>{$('#wsPublishPanel').hidden=true;};

api.onNavigate?.(tab=>{if(tab==='workshop')setTab('workshop');});
window.addEventListener('keydown',e=>{
  if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='s'&&activeTab==='workbench'){e.preventDefault();saveSource();}
});
async function init(){
  renderModules();
  const result=await safe(()=>refreshProjects());
  utilities.refreshSources();
  if(!projects.length){showModal();}
}
init();
